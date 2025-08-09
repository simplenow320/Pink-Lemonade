"""
Writing Assistant API Endpoints for GrantFlow

This module provides API endpoints for the AI-powered writing assistant.
"""

import logging
from flask import Blueprint, jsonify, request, abort, current_app as app

from app import db
from app.models import Grant, Organization
from app.services.writing_assistant_service import (
    generate_section_content,
    improve_section_content,
    generate_section_outline,
    SECTION_TYPES
)
# Removed unused imports

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('writing_assistant', __name__, url_prefix='/api/writing-assistant')

@bp.route('/templates', methods=['GET'])
def get_templates():
    """Get available writing templates"""
    try:
        templates = [
            {'id': 'brief', 'name': 'Brief Narrative', 'description': 'Short grant narrative'},
            {'id': 'detailed', 'name': 'Detailed Narrative', 'description': 'Comprehensive grant narrative'},
            {'id': 'loi', 'name': 'Letter of Intent', 'description': 'Letter of intent template'}
        ]
        return jsonify(templates)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/sections', methods=['GET'])
def get_section_types():
    """
    Get available section types for the writing assistant
    
    Returns:
        Response: JSON response with available section types and descriptions.
    """
    logger.info('GET /api/writing-assistant/sections')
    
    try:
        result = {
            "success": True,
            "sections": {
                section_type: description
                for section_type, description in SECTION_TYPES.items()
            }
        }
        
        logger.info('Success response from /api/writing-assistant/sections')
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting section types: {str(e)}")
        logger.error(f'Error response from /api/writing-assistant/sections: {str(e)}')
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
    logger.info('POST /api/writing-assistant/generate')
    
    try:
        data = request.json
        
        # Validate request data
        if not data or 'section_type' not in data or 'grant_id' not in data:
            logger.error('Error response from /api/writing-assistant/generate: Missing required fields')
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
            logger.info("Request processed")
            return jsonify({"success": False, "error": "Grant not found"}), 404
        
        organization = Organization.query.first()  # Assuming single organization for now
        if not organization:
            logger.info("Request processed")
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
        logger.info("Request processed") else result.get('error'))
        
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error generating section content: {str(e)}")
        logger.info("Request processed"))
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
    logger.info("Request processed")
    
    try:
        data = request.json
        
        # Validate request data
        if not data or 'section_type' not in data or 'content' not in data or 'feedback' not in data:
            logger.info("Request processed")
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
        logger.info("Request processed") else result.get('error'))
        
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error improving section content: {str(e)}")
        logger.info("Request processed"))
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
    logger.info("Request processed")
    
    try:
        data = request.json
        
        # Validate request data
        if not data or 'section_type' not in data or 'grant_id' not in data:
            logger.info("Request processed")
            return jsonify({
                "success": False,
                "error": "Missing required fields: section_type, grant_id"
            }), 400
        
        section_type = data['section_type']
        grant_id = data['grant_id']
        
        # Get grant and organization information
        grant = Grant.query.get(grant_id)
        if not grant:
            logger.info("Request processed")
            return jsonify({"success": False, "error": "Grant not found"}), 404
        
        organization = Organization.query.first()  # Assuming single organization for now
        if not organization:
            logger.info("Request processed")
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
        logger.info("Request processed") else result.get('error'))
        
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error generating section outline: {str(e)}")
        logger.info("Request processed"))
        return jsonify({"success": False, "error": "Failed to generate outline"}), 500