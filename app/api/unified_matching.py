"""
Unified Matching API - Single Source of Truth
Replaces multiple confusing endpoints with one powerful endpoint
"""
from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
import logging

from app.services.grant_discovery_service import GrantDiscoveryService
from app.services.simple_discovery import SimpleDiscoveryService
from app.services.ai_learning_system import AILearningSystem

logger = logging.getLogger(__name__)

unified_bp = Blueprint('unified_matching', __name__)


@unified_bp.route('/api/matching/unified/<int:org_id>', methods=['GET'])
@cross_origin()
def get_unified_matches(org_id: int):
    """
    Single endpoint for complete grant matching pipeline:
    1. Discovers grants from all sources
    2. Persists to database
    3. Applies AI scoring with REACTO
    4. Returns personalized, ranked results
    
    This replaces:
    - /api/matching (no persistence)
    - /api/ai-grants/match (database only)
    - /api/opportunities (display only)
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        refresh = request.args.get('refresh', 'true').lower() == 'true'
        
        # Try simple discovery first (avoids field issues)
        try:
            simple_service = SimpleDiscoveryService()
            results = simple_service.discover_for_org(org_id)
        except Exception as e:
            # Fallback to full discovery service
            discovery_service = GrantDiscoveryService()
            results = discovery_service.discover_and_persist(org_id, limit=limit)
        
        if results.get('success'):
            # Add metadata for frontend
            results['endpoint_version'] = '2.0'
            results['features'] = [
                'real_time_discovery',
                'database_persistence',
                'reacto_ai_scoring',
                'deduplication',
                'unified_response'
            ]
            
            return jsonify(results), 200
        else:
            return jsonify({
                'success': False,
                'error': results.get('error', 'Discovery failed')
            }), 500
            
    except Exception as e:
        logger.error(f"Error in unified matching for org {org_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@unified_bp.route('/api/matching/save-interaction', methods=['POST'])
@cross_origin()
def save_grant_interaction():
    """
    Track user interactions with grants to improve future matching
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        grant_id = data.get('grant_id')
        action = data.get('action')  # 'saved', 'applied', 'dismissed'
        
        if not all([user_id, grant_id, action]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        # Record interaction for learning
        learning_system = AILearningSystem()
        success = learning_system.record_user_decision(user_id, grant_id, action)
        
        return jsonify({
            'success': success,
            'message': f'Interaction recorded: {action}' if success else 'Failed to record',
            'learning_applied': success
        }), 200
        
    except Exception as e:
        logger.error(f"Error saving interaction: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@unified_bp.route('/api/matching/refresh-all', methods=['POST'])
@cross_origin()
def refresh_all_organizations():
    """
    Admin endpoint to refresh grants for all organizations
    Used by background job scheduler
    """
    try:
        # Check for admin token (implement proper auth in production)
        admin_token = request.headers.get('X-Admin-Token')
        if admin_token != 'admin-secret-token':  # Replace with proper auth
            return jsonify({'error': 'Unauthorized'}), 401
        
        discovery_service = GrantDiscoveryService()
        results = discovery_service.refresh_all_organizations()
        
        return jsonify({
            'success': True,
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error in refresh all: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@unified_bp.route('/api/matching/stats/<int:org_id>', methods=['GET'])
@cross_origin()
def get_matching_stats(org_id: int):
    """
    Get matching statistics for an organization
    """
    try:
        from app import db
        from app.models import Grant
        from datetime import datetime, timedelta
        
        # Get stats for last 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        total_grants = Grant.query.filter_by(org_id=org_id).count()
        recent_grants = Grant.query.filter(
            Grant.org_id == org_id,
            Grant.created_at >= cutoff_date
        ).count()
        
        high_matches = Grant.query.filter(
            Grant.org_id == org_id,
            Grant.match_score >= 4
        ).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_grants': total_grants,
                'recent_discoveries': recent_grants,
                'high_matches': high_matches,
                'last_refresh': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500