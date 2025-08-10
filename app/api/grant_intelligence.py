"""
Grant Intelligence API
Endpoints for AI-powered grant analysis and data extraction
"""
import logging
from flask import Blueprint, jsonify, request

from app.services.grant_intelligence import GrantIntelligenceService
from app.models import Grant

logger = logging.getLogger(__name__)

intelligence_api = Blueprint('grant_intelligence', __name__, url_prefix='/api/grants')

@intelligence_api.route('/<int:grant_id>/intelligence', methods=['POST'])
def analyze_grant(grant_id):
    """
    Trigger AI analysis for a specific grant
    
    POST /api/grants/{grant_id}/intelligence
    """
    try:
        # Get organization context from request if provided
        org_context = request.get_json() if request.is_json else None
        
        service = GrantIntelligenceService()
        result = service.analyze_grant(grant_id, org_context or {})
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Grant intelligence analysis failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}',
            'grant_id': grant_id
        }), 500

@intelligence_api.route('/bulk-intelligence', methods=['POST'])
def bulk_analyze_grants():
    """
    Analyze multiple grants in bulk
    
    POST /api/grants/bulk-intelligence
    Body: {
        "limit": 10,
        "org_context": {...}
    }
    """
    try:
        data = request.get_json() if request.is_json else {}
        limit = data.get('limit', 5)  # Default to 5 grants
        org_context = data.get('org_context')
        
        service = GrantIntelligenceService()
        results = service.bulk_analyze_grants(org_context or {}, limit)
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Bulk grant analysis failed: {str(e)}")
        return jsonify({
            'total_analyzed': 0,
            'successful': 0,
            'failed': 1,
            'error': f'Bulk analysis failed: {str(e)}'
        }), 500

@intelligence_api.route('/<int:grant_id>/intelligence', methods=['GET'])
def get_grant_intelligence(grant_id):
    """
    Get existing intelligence data for a grant
    
    GET /api/grants/{grant_id}/intelligence
    """
    try:
        grant = Grant.query.get_or_404(grant_id)
        
        intelligence_data = {
            'grant_id': grant_id,
            'title': grant.title,
            'funder': grant.funder,
            'contact_info': grant.contact_info,
            'requirements_summary': grant.requirements_summary,
            'application_complexity': grant.application_complexity,
            'ai_summary': grant.ai_summary,
            'last_intelligence_update': grant.last_intelligence_update.isoformat() if grant.last_intelligence_update else None,
            'has_intelligence': bool(grant.ai_summary or grant.contact_info)
        }
        
        return jsonify({
            'success': True,
            'intelligence': intelligence_data
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get grant intelligence: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'grant_id': grant_id
        }), 500

@intelligence_api.route('/intelligence-status', methods=['GET'])
def get_intelligence_status():
    """
    Get overall intelligence status for all grants
    
    GET /api/grants/intelligence-status
    """
    try:
        total_grants = Grant.query.count()
        grants_with_intelligence = Grant.query.filter(
            Grant.ai_summary.isnot(None)
        ).count()
        grants_with_contacts = Grant.query.filter(
            Grant.contact_info.isnot(None)
        ).count()
        grants_needing_analysis = Grant.query.filter(
            Grant.ai_summary.is_(None)
        ).count()
        
        return jsonify({
            'success': True,
            'status': {
                'total_grants': total_grants,
                'analyzed_grants': grants_with_intelligence,
                'grants_with_contacts': grants_with_contacts,
                'pending_analysis': grants_needing_analysis,
                'analysis_coverage': round((grants_with_intelligence / total_grants * 100), 1) if total_grants > 0 else 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get intelligence status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500