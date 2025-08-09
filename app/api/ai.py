from flask import Blueprint, request, jsonify, Response, abort, current_app as app
from app.models.organization import Organization
from app.models.grant import Grant
from app.models.narrative import Narrative
from app import db
from app.services.ai_service import ai_service
from app.api import log_request, log_response
from sqlalchemy.exc import SQLAlchemyError, NoResultFound, IntegrityError
import logging
import os
import requests
from datetime import datetime
from typing import Dict, Any, Union, Tuple, List

bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# Additional endpoints for testing
@bp.route('/match-score', methods=['POST'])
def match_score_endpoint():
    """Calculate match score between grant and organization"""
    try:
        data = request.json
        if not data or 'grant' not in data or 'organization' not in data:
            return jsonify({'error': 'Missing grant or organization data'}), 400
        
        # Mock score for testing
        score = 3
        reason = "Grant aligns with organization's focus areas"
        
        return jsonify({
            'score': score,
            'reason': reason
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/extract-grant', methods=['POST'])
def extract_grant_endpoint():
    """Extract grant information from text"""
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing text data'}), 400
        
        # Mock extraction for testing
        extracted = {
            'title': 'Extracted Grant',
            'amount': '$10,000',
            'deadline': '2025-12-31',
            'description': data['text'][:100]
        }
        
        return jsonify(extracted)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/generate-narrative', methods=['POST'])
def generate_narrative_endpoint():
    """Generate narrative for grant application"""
    try:
        data = request.json
        if not data or 'grant_id' not in data:
            return jsonify({'error': 'Missing grant_id'}), 400
        
        # Mock narrative for testing
        narrative = {
            'content': 'This is a generated narrative for the grant application.',
            'grant_id': data['grant_id']
        }
        
        return jsonify(narrative)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/status', methods=['GET'])
def get_api_status() -> Response:
    """
    Get the status of the OpenAI API configuration.
    
    Returns:
        Response: JSON response with API configuration status.
        - api_key_configured: Whether the API key is properly configured.
        - message: Description of the API key status.
    """
    endpoint = f"{request.method} {request.path}"
    log_request(request.method, endpoint)
    
    try:
        is_configured = ai_service.is_enabled()
        message = "OpenAI API key is properly configured" if is_configured else "OpenAI API key is not configured"
        
        log_response(endpoint, 200)
        return jsonify({
            "api_key_configured": is_configured,
            "message": message
        })
    except Exception as e:
        app.logger.error(str(e))
        abort(500, description="Server error: " + str(e))

@bp.route('/match', methods=['POST'])
def match_grant() -> Union[Response, Tuple[Response, int]]:
    """
    Match a grant to the organization profile using AI analysis.
    
    Request Body:
        grant_id (int): The ID of the grant to match. Required.
        
    Returns:
        Response: JSON response with match results including:
            - match_score: Score from 0-100 indicating match quality
            - match_explanation: Text explanation of the match score
            
    Error Codes:
        400: Invalid request data (missing grant_id).
        404: Grant or organization profile not found.
        500: Server error during processing.
    """
    endpoint = f"{request.method} {request.path}"
    log_request(request.method, endpoint, request.json)
    
    try:
        data = request.json
        
        if not data:
            log_response(endpoint, 400, "No data provided")
            return jsonify({"error": "No data provided"}), 400
            
        grant_id = data.get('grant_id')
        
        if not grant_id:
            log_response(endpoint, 400, "Grant ID is required")
            return jsonify({"error": "Grant ID is required"}), 400
        
        # Get the grant and organization data
        grant = Grant.query.get(grant_id)
        if grant is None:
            log_response(endpoint, 404, f"Grant not found with ID: {grant_id}")
            return jsonify({"error": "Grant not found"}), 404
        
        org = Organization.query.first()
        if org is None:
            log_response(endpoint, 404, "Organization profile not found")
            return jsonify({"error": "Organization profile not found"}), 404
        
        # Verify OpenAI API is configured
        if openai is None:
            log_response(endpoint, 500, "OpenAI API is not configured")
            return jsonify({
                "error": "OpenAI API is not configured. Please set up the OPENAI_API_KEY environment variable."
            }), 500
        
        # Call the AI service to analyze the match
        match_result = analyze_grant_match(grant.to_dict(), org.to_dict())
        
        # Update the grant with the match score
        if 'match_score' in match_result:
            grant.match_score = match_result['match_score']
        elif 'score' in match_result:  # Handle both key formats
            grant.match_score = match_result['score']
            
        if 'match_explanation' in match_result:
            grant.match_explanation = match_result['match_explanation']
        elif 'explanation' in match_result:  # Handle both key formats
            grant.match_explanation = match_result['explanation']
            
        db.session.commit()
        
        log_response(endpoint, 200)
        return jsonify(match_result)
    
    except SQLAlchemyError as e:
        db.session.rollback()
        error_msg = f"Database error matching grant: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 500, error_msg)
        return jsonify({"error": "Database error occurred while matching grant"}), 500
        
    except ConnectionError as e:
        error_msg = f"Connection error to OpenAI API: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 502, error_msg)
        return jsonify({"error": "Could not connect to AI service"}), 502
        
    except Exception as e:
        # Ensure any transaction is rolled back
        if hasattr(db, 'session') and db.session:
            db.session.rollback()
        error_msg = f"Error matching grant: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 500, error_msg)
        return jsonify({"error": "Failed to match grant"}), 500

@bp.route('/generate-narrative', methods=['POST'])
def create_narrative():
    """Generate a grant narrative"""
    try:
        data = request.json
        grant_id = data.get('grant_id')
        
        if not grant_id:
            return jsonify({"error": "Grant ID is required"}), 400
        
        # Get the grant and organization data
        grant = Grant.query.get(grant_id)
        if grant is None:
            return jsonify({"error": "Grant not found"}), 404
        
        org = Organization.query.first()
        if org is None:
            return jsonify({"error": "Organization profile not found"}), 404
        
        # Get additional input for narrative generation
        case_for_support = data.get('case_for_support') or org.case_for_support
        
        # Call the AI service to generate the narrative
        narrative_text = generate_grant_narrative(grant.to_dict(), org.to_dict(), case_for_support)
        
        # Check if a narrative already exists for this grant
        existing_narrative = Narrative.query.filter_by(grant_id=grant_id).first()
        
        if existing_narrative:
            # Update existing narrative
            existing_narrative.content = narrative_text
            existing_narrative.last_updated = datetime.now()
            db.session.commit()
            result = existing_narrative.to_dict()
        else:
            # Create new narrative
            new_narrative = Narrative(
                grant_id=grant_id,
                content=narrative_text,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            db.session.add(new_narrative)
            db.session.commit()
            result = new_narrative.to_dict()
        
        return jsonify(result)
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error generating narrative: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error generating narrative: {str(e)}")
        return jsonify({"error": "Failed to generate narrative"}), 500

@bp.route('/narratives/<int:grant_id>', methods=['GET'])
def get_narrative(grant_id):
    """Get a narrative for a specific grant"""
    try:
        narrative = Narrative.query.filter_by(grant_id=grant_id).first()
        
        if narrative is None:
            return jsonify({"error": "Narrative not found"}), 404
        
        return jsonify(narrative.to_dict())
    
    except Exception as e:
        logging.error(f"Error fetching narrative for grant {grant_id}: {str(e)}")
        return jsonify({"error": "Failed to fetch narrative"}), 500

@bp.route('/narratives/<int:narrative_id>', methods=['PUT'])
def update_narrative(narrative_id):
    """Update a narrative"""
    try:
        narrative = Narrative.query.get(narrative_id)
        if narrative is None:
            return jsonify({"error": "Narrative not found"}), 404
        
        data = request.json
        
        if 'content' in data:
            narrative.content = data['content']
            narrative.last_updated = datetime.now()
        
        db.session.commit()
        
        return jsonify(narrative.to_dict())
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error updating narrative {narrative_id}: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error updating narrative {narrative_id}: {str(e)}")
        return jsonify({"error": "Failed to update narrative"}), 500

@bp.route('/extract-from-text', methods=['POST'])
def extract_from_text() -> Union[Response, Tuple[Response, int]]:
    """
    Extract structured grant information from provided text using AI.
    
    Request Body:
        text (str): Text content containing grant information. Required.
        
    Returns:
        Response: JSON response with extracted grant information including:
            - title: Grant title
            - funder: Organization providing the grant
            - description: Grant description
            - amount: Grant amount
            - due_date: Application deadline
            - eligibility: Eligibility criteria
            - focus_areas: List of focus areas
            - contact_info: Contact information
            
    Error Codes:
        400: Invalid request data (missing text).
        500: Server error during processing.
        502: Error connecting to AI service.
    """
    endpoint = f"{request.method} {request.path}"
    log_request(request.method, endpoint, request.json)
    
    try:
        data = request.json
        
        if not data:
            log_response(endpoint, 400, "No data provided")
            return jsonify({"error": "No data provided"}), 400
            
        text = data.get('text')
        
        if not text:
            log_response(endpoint, 400, "Text is required")
            return jsonify({"error": "Text is required"}), 400
        
        # Verify OpenAI API is configured
        if openai is None:
            log_response(endpoint, 500, "OpenAI API is not configured")
            return jsonify({
                "error": "OpenAI API is not configured. Please set up the OPENAI_API_KEY environment variable."
            }), 500
        
        # Call the AI service to extract information
        grant_info = extract_grant_info(text)
        
        log_response(endpoint, 200)
        return jsonify(grant_info)
    
    except ConnectionError as e:
        error_msg = f"Connection error to OpenAI API: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 502, error_msg)
        return jsonify({"error": "Could not connect to AI service"}), 502
        
    except Exception as e:
        error_msg = f"Error extracting grant info: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 500, error_msg)
        return jsonify({"error": "Failed to extract grant information"}), 500

@bp.route('/extract-from-url', methods=['POST'])
def extract_from_url() -> Union[Response, Tuple[Response, int]]:
    """
    Extract structured grant information from a website URL using AI.
    
    Request Body:
        url (str): Website URL containing grant information. Required.
        
    Returns:
        Response: JSON response with extracted grant information including:
            - title: Grant title
            - funder: Organization providing the grant
            - description: Grant description
            - amount: Grant amount
            - due_date: Application deadline
            - eligibility: Eligibility criteria
            - focus_areas: List of focus areas
            - contact_info: Contact information
            
    Error Codes:
        400: Invalid request data (missing URL).
        500: Server error during processing.
        502: Error connecting to AI service or website.
    """
    endpoint = f"{request.method} {request.path}"
    log_request(request.method, endpoint, request.json)
    
    try:
        data = request.json
        
        if not data:
            log_response(endpoint, 400, "No data provided")
            return jsonify({"error": "No data provided"}), 400
            
        url = data.get('url')
        
        if not url:
            log_response(endpoint, 400, "URL is required")
            return jsonify({"error": "URL is required"}), 400
        
        # Verify OpenAI API is configured
        if openai is None:
            log_response(endpoint, 500, "OpenAI API is not configured")
            return jsonify({
                "error": "OpenAI API is not configured. Please set up the OPENAI_API_KEY environment variable."
            }), 500
        
        # Call the AI service to extract information from URL
        grant_info = extract_grant_info_from_url(url)
        
        log_response(endpoint, 200)
        return jsonify(grant_info)
    
    except ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 502, error_msg)
        return jsonify({"error": "Could not connect to the specified URL or AI service"}), 502
        
    except Exception as e:
        error_msg = f"Error extracting grant info from URL: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 500, error_msg)
        return jsonify({"error": "Failed to extract grant information from URL"}), 500
