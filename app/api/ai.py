from flask import Blueprint, request, jsonify
from app.models.organization import Organization
from app.models.grant import Grant
from app.models.narrative import Narrative
from app import db
from app.services.ai_service import (
    analyze_grant_match, 
    generate_grant_narrative,
    extract_grant_info,
    extract_grant_info_from_url,
    openai
)
from sqlalchemy.exc import SQLAlchemyError
import logging
import os
from datetime import datetime

bp = Blueprint('ai', __name__, url_prefix='/api/ai')

@bp.route('/status', methods=['GET'])
def get_api_status():
    """Get the status of the OpenAI API configuration"""
    return jsonify({
        "api_key_configured": openai is not None,
        "message": "OpenAI API key is properly configured" if openai else "OpenAI API key is not configured"
    })

@bp.route('/match', methods=['POST'])
def match_grant():
    """Match a grant to the organization profile"""
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
        
        # Call the AI service to analyze the match
        match_result = analyze_grant_match(grant.to_dict(), org.to_dict())
        
        # Update the grant with the match score
        grant.match_score = match_result['score']
        grant.match_explanation = match_result['explanation']
        db.session.commit()
        
        return jsonify(match_result)
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error matching grant: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error matching grant: {str(e)}")
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
def extract_from_text():
    """Extract grant information from text"""
    try:
        data = request.json
        text = data.get('text')
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        # Call the AI service to extract information
        grant_info = extract_grant_info(text)
        
        return jsonify(grant_info)
    
    except Exception as e:
        logging.error(f"Error extracting grant info: {str(e)}")
        return jsonify({"error": "Failed to extract grant information"}), 500

@bp.route('/extract-from-url', methods=['POST'])
def extract_from_url():
    """Extract grant information from a URL"""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({"error": "URL is required"}), 400
        
        # Call the AI service to extract information from URL
        grant_info = extract_grant_info_from_url(url)
        
        return jsonify(grant_info)
    
    except Exception as e:
        logging.error(f"Error extracting grant info from URL: {str(e)}")
        return jsonify({"error": "Failed to extract grant information from URL"}), 500
