from flask import Blueprint, jsonify, request
from app import db
from app.services.ai_service import ai_service
from app.services.ai_optimizer_service import AIOptimizerService
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('ai', __name__)

# Initialize services
optimizer = AIOptimizerService()

@bp.route('/match', methods=['POST'])
def get_match_score():
    """Get AI match score for a grant"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        grant_data = data.get('grant', {})
        org_data = data.get('organization', {})
        
        if not grant_data or not org_data:
            return jsonify({"error": "Both 'grant' and 'organization' data required"}), 400
        
        # Use sophisticated AI service for matching
        score, reason = ai_service.match_grant(org_data, grant_data)
        result = {
            "match_score": score,
            "reason": reason,
            "success": True
        }
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"AI match error: {str(e)}")
        return jsonify({"error": "AI matching failed", "details": str(e)}), 500

@bp.route('/extract', methods=['POST'])
def extract_grant_info():
    """Extract grant information from text/URL"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        text = data.get('text', '')
        url = data.get('url', '')
        
        if not text and not url:
            return jsonify({"error": "Either 'text' or 'url' required"}), 400
        
        # Use AI service for text analysis
        result = ai_service.extract_grant_info(text or url)
        if result:
            return jsonify(result)
        else:
            return jsonify({"error": "Failed to extract grant information"}), 500
        
    except Exception as e:
        logger.error(f"Grant extraction error: {str(e)}")
        return jsonify({"error": "Grant extraction failed", "details": str(e)}), 500

@bp.route('/generate', methods=['POST'])
def generate_narrative():
    """Generate grant narrative"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        section_type = data.get('section_type', 'executive_summary')
        org_data = data.get('organization', {})
        grant_data = data.get('grant', {})
        
        if not org_data:
            return jsonify({"error": "Organization data required"}), 400
        
        # Use AI service for narrative generation
        narrative = ai_service.generate_grant_narrative(
            org_profile=org_data,
            grant=grant_data,
            section=section_type
        )
        if narrative:
            result = {
                "narrative": narrative,
                "section_type": section_type,
                "success": True
            }
            return jsonify(result)
        else:
            return jsonify({"error": "Failed to generate narrative"}), 500
        
    except Exception as e:
        logger.error(f"Narrative generation error: {str(e)}")
        return jsonify({"error": "Narrative generation failed", "details": str(e)}), 500