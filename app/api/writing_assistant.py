"""
Writing Assistant API Endpoints for GrantFlow

This module provides API endpoints for the AI-powered writing assistant.
"""

import logging
from flask import Blueprint, jsonify, request, abort, current_app as app

from app import db
from app.models.grant import Grant
from app.models.organization import Organization
from app.services.writing_assistant_service import (
    generate_section_content,
    improve_section_content,
    generate_section_outline,
    SECTION_TYPES
)
from app.api import log_request, log_response

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('writing_assistant', __name__, url_prefix='/api/writing-assistant')


@bp.route('/sections', methods=['GET'])
def get_section_types():
    """
    Get available section types for the writing assistant
    
    Returns:
        Response: JSON response with available section types and descriptions.
    """
    log_request('GET', '/api/writing-assistant/sections')
    
    try:
        result = {
            "success": True,
            "sections": {
                section_type: description
                for section_type, description in SECTION_TYPES.items()
            }
        }
        
        log_response('/api/writing-assistant/sections', 200)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting section types: {str(e)}")
        log_response('/api/writing-assistant/sections', 500, str(e))
        return jsonify({"success": False, "error": "Failed to get section types"}), 500


@bp.route('/generate', methods=['POST'])
def generate_section():
    """
    Generate content for a specific section of a grant proposal
    
    Request Body:
        section_type (str): Type of proposal section
        grant_id (int): ID of the grant
        additional_inputs (dict, optional): Additional user inputs specific to the section
        
    Returns:
        Response: JSON response with generated content and writing tips.
    """
    log_request('POST', '/api/writing-assistant/generate', request.json)
    
    try:
        data = request.json
        
        # Validate request data
        if not data or 'section_type' not in data or 'grant_id' not in data:
            log_response('/api/writing-assistant/generate', 400, "Missing required fields")
            return jsonify({
                "success": False,
                "error": "Missing required fields: section_type, grant_id"
            }), 400
        
        section_type = data['section_type']
        grant_id = data['grant_id']
        additional_inputs = data.get('additional_inputs', {})
        
        # Get grant and organization information
        grant = Grant.query.get(grant_id)
        if not grant:
            log_response('/api/writing-assistant/generate', 404, "Grant not found")
            return jsonify({"success": False, "error": "Grant not found"}), 404
        
        organization = Organization.query.first()  # Assuming single organization for now
        if not organization:
            log_response('/api/writing-assistant/generate', 404, "Organization not found")
            return jsonify({"success": False, "error": "Organization profile not found"}), 404
        
        # Prepare grant info
        grant_info = {
            'title': grant.title,
            'funder': grant.funder,
            'amount': grant.amount,
            'description': grant.description,
            'focus_areas': grant.focus_areas or [],
            'eligibility': grant.eligibility
        }
        
        # Prepare organization info
        org_info = organization.to_dict()
        
        # Generate content
        result = generate_section_content(section_type, grant_info, org_info, additional_inputs)
        
        status_code = 200 if result.get('success', False) else 400
        log_response('/api/writing-assistant/generate', status_code, None if result.get('success', False) else result.get('error'))
        
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error generating section content: {str(e)}")
        log_response('/api/writing-assistant/generate', 500, str(e))
        return jsonify({"success": False, "error": "Failed to generate content"}), 500


@bp.route('/improve', methods=['POST'])
def improve_section():
    """
    Improve existing content based on user feedback
    
    Request Body:
        section_type (str): Type of proposal section
        content (str): Current section content
        feedback (str): User feedback for improvements
        
    Returns:
        Response: JSON response with improved content.
    """
    log_request('POST', '/api/writing-assistant/improve', request.json)
    
    try:
        data = request.json
        
        # Validate request data
        if not data or 'section_type' not in data or 'content' not in data or 'feedback' not in data:
            log_response('/api/writing-assistant/improve', 400, "Missing required fields")
            return jsonify({
                "success": False,
                "error": "Missing required fields: section_type, content, feedback"
            }), 400
        
        section_type = data['section_type']
        current_content = data['content']
        feedback = data['feedback']
        
        # Improve content
        result = improve_section_content(section_type, current_content, feedback)
        
        status_code = 200 if result.get('success', False) else 400
        log_response('/api/writing-assistant/improve', status_code, None if result.get('success', False) else result.get('error'))
        
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error improving section content: {str(e)}")
        log_response('/api/writing-assistant/improve', 500, str(e))
        return jsonify({"success": False, "error": "Failed to improve content"}), 500


@bp.route('/outline', methods=['POST'])
def create_section_outline():
    """
    Generate an outline/structure for a specific proposal section
    
    Request Body:
        section_type (str): Type of proposal section
        grant_id (int): ID of the grant
        
    Returns:
        Response: JSON response with section outline.
    """
    log_request('POST', '/api/writing-assistant/outline', request.json)
    
    try:
        data = request.json
        
        # Validate request data
        if not data or 'section_type' not in data or 'grant_id' not in data:
            log_response('/api/writing-assistant/outline', 400, "Missing required fields")
            return jsonify({
                "success": False,
                "error": "Missing required fields: section_type, grant_id"
            }), 400
        
        section_type = data['section_type']
        grant_id = data['grant_id']
        
        # Get grant and organization information
        grant = Grant.query.get(grant_id)
        if not grant:
            log_response('/api/writing-assistant/outline', 404, "Grant not found")
            return jsonify({"success": False, "error": "Grant not found"}), 404
        
        organization = Organization.query.first()  # Assuming single organization for now
        if not organization:
            log_response('/api/writing-assistant/outline', 404, "Organization not found")
            return jsonify({"success": False, "error": "Organization profile not found"}), 404
        
        # Prepare grant info
        grant_info = {
            'title': grant.title,
            'funder': grant.funder,
            'amount': grant.amount,
            'focus_areas': grant.focus_areas or []
        }
        
        # Prepare organization info
        org_info = {
            'name': organization.name,
            'mission': organization.mission
        }
        
        # Generate outline
        result = generate_section_outline(section_type, grant_info, org_info)
        
        status_code = 200 if result.get('success', False) else 400
        log_response('/api/writing-assistant/outline', status_code, None if result.get('success', False) else result.get('error'))
        
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error generating section outline: {str(e)}")
        log_response('/api/writing-assistant/outline', 500, str(e))
        return jsonify({"success": False, "error": "Failed to generate outline"}), 500