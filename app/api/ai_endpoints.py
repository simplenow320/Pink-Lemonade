"""
AI API Endpoints for Grant Management
Handles matching, extraction, and narrative generation
"""

from flask import Blueprint, request, jsonify
from app.models.organization import Organization
from app.models.grant import Grant
from app.models.narrative import Narrative
from app import db
from app.services.ai_service import ai_service
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

bp = Blueprint('ai_endpoints', __name__, url_prefix='/api/ai')

@bp.route('/status', methods=['GET'])
def get_ai_status():
    """Check if AI service is enabled"""
    return jsonify({
        "enabled": ai_service.is_enabled(),
        "message": "AI features enabled" if ai_service.is_enabled() else "No API key configured - Add your OpenAI API key in Settings"
    })

@bp.route('/match', methods=['POST'])
def match_grant():
    """
    Match a grant with organization profile
    Request body: { grant_id: int, org_id: int (optional) }
    """
    try:
        data = request.json
        grant_id = data.get('grant_id')
        org_id = data.get('org_id', 1)  # Default to first org
        
        if not grant_id:
            return jsonify({"error": "grant_id required"}), 400
        
        # Get grant and org from database
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({"error": "Grant not found"}), 404
            
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({"error": "Organization not found"}), 404
        
        # Perform matching
        score, reason = ai_service.match_grant(org.to_dict(), grant.to_dict())
        
        if score is None:
            return jsonify({
                "fit_score": None,
                "fit_reason": None,
                "message": "AI features disabled - Add OpenAI API key in Settings"
            })
        
        # Update grant with match score
        grant.match_score = score
        grant.match_reason = reason
        db.session.commit()
        
        return jsonify({
            "fit_score": score,
            "fit_reason": reason,
            "grant_id": grant_id
        })
        
    except Exception as e:
        logger.error(f"Error in match_grant: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/explain-match', methods=['POST'])
def explain_match():
    """Get detailed explanation for grant match"""
    try:
        data = request.json
        grant_id = data.get('grant_id')
        org_id = data.get('org_id', 1)
        
        grant = Grant.query.get(grant_id)
        org = Organization.query.get(org_id)
        
        if not grant or not org:
            return jsonify({"error": "Grant or organization not found"}), 404
        
        explanation = ai_service.explain_match(org.to_dict(), grant.to_dict())
        
        if not explanation:
            return jsonify({
                "explanation": "AI features disabled - Add OpenAI API key in Settings"
            })
        
        return jsonify({"explanation": explanation})
        
    except Exception as e:
        logger.error(f"Error in explain_match: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/extract', methods=['POST'])
def extract_grant():
    """
    Extract grant information from URL or text
    Request body: { url: string OR text: string, org_id: int (optional) }
    """
    try:
        data = request.json
        url = data.get('url')
        text = data.get('text')
        org_id = data.get('org_id', 1)
        
        if not url and not text:
            return jsonify({"error": "Either url or text required"}), 400
        
        # Fetch content if URL provided
        if url:
            try:
                response = requests.get(url, timeout=30)
                text = response.text
            except Exception as e:
                return jsonify({"error": f"Failed to fetch URL: {e}"}), 400
        
        # Extract grant information
        grant_data = ai_service.extract_grant_from_text(text, url)
        
        if not grant_data:
            return jsonify({
                "error": "AI extraction disabled - Add OpenAI API key in Settings"
            }), 400
        
        # Save as new grant if extraction successful
        grant = Grant(
            title=grant_data['title'],
            funder=grant_data['funder'],
            description=grant_data.get('description', ''),
            amount_min=grant_data.get('amount_min', 0),
            amount_max=grant_data.get('amount_max', 0),
            due_date=grant_data.get('deadline'),
            focus_areas=grant_data.get('focus_areas', ''),
            geography=grant_data.get('geography', ''),
            link=grant_data.get('link', ''),
            contact_name=grant_data.get('contact_name', ''),
            contact_email=grant_data.get('contact_email', ''),
            contact_phone=grant_data.get('contact_phone', ''),
            source_name='AI Extraction',
            discovered_at=datetime.now(),
            org_id=org_id,
            status='prospect'
        )
        
        db.session.add(grant)
        db.session.commit()
        
        return jsonify({
            "grant": grant.to_dict(),
            "message": "Grant extracted and saved successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in extract_grant: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/narrative', methods=['POST'])
def generate_narrative():
    """
    Generate narrative sections for a grant
    Request body: { grant_id: int, sections: [string], org_id: int (optional) }
    """
    try:
        data = request.json
        grant_id = data.get('grant_id')
        sections = data.get('sections', ['need', 'program', 'outcomes', 'budget_rationale'])
        org_id = data.get('org_id', 1)
        
        if not grant_id:
            return jsonify({"error": "grant_id required"}), 400
        
        # Get grant and org
        grant = Grant.query.get(grant_id)
        org = Organization.query.get(org_id)
        
        if not grant or not org:
            return jsonify({"error": "Grant or organization not found"}), 404
        
        # Generate narrative
        narrative_data = ai_service.generate_narrative(
            grant.to_dict(),
            org.to_dict(),
            sections
        )
        
        if not narrative_data:
            return jsonify({
                "error": "AI narrative generation disabled - Add OpenAI API key in Settings"
            }), 400
        
        # Check for existing narrative (versioning)
        existing = Narrative.query.filter_by(grant_id=grant_id).first()
        version = 1
        
        if existing:
            # Create new version instead of overwriting
            version = (existing.version or 1) + 1
            
        # Save narrative
        narrative = Narrative(
            grant_id=grant_id,
            org_id=org_id,
            content=narrative_data,
            version=version,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(narrative)
        db.session.commit()
        
        return jsonify({
            "narrative": {
                "id": narrative.id,
                "grant_id": grant_id,
                "sections": narrative_data.get('sections', {}),
                "version": version,
                "created_at": narrative.created_at.isoformat()
            },
            "message": f"Narrative version {version} generated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in generate_narrative: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/batch-match', methods=['POST'])
def batch_match_grants():
    """Match multiple grants at once"""
    try:
        data = request.json
        grant_ids = data.get('grant_ids', [])
        org_id = data.get('org_id', 1)
        
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({"error": "Organization not found"}), 404
        
        results = []
        for grant_id in grant_ids:
            grant = Grant.query.get(grant_id)
            if grant:
                score, reason = ai_service.match_grant(org.to_dict(), grant.to_dict())
                if score:
                    grant.match_score = score
                    grant.match_reason = reason
                    results.append({
                        "grant_id": grant_id,
                        "fit_score": score,
                        "fit_reason": reason
                    })
                else:
                    results.append({
                        "grant_id": grant_id,
                        "fit_score": None,
                        "fit_reason": "AI disabled"
                    })
        
        db.session.commit()
        
        return jsonify({
            "results": results,
            "message": f"Matched {len(results)} grants"
        })
        
    except Exception as e:
        logger.error(f"Error in batch_match: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500