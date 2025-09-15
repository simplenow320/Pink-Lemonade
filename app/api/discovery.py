"""Grant Discovery API endpoints"""
from flask import Blueprint, jsonify, request, session
from app.models import Organization
from app.services.grant_discovery_service import GrantDiscoveryService
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('discovery', __name__, url_prefix='/api/grants')

@bp.route('/discover/<int:org_id>', methods=['GET'])
def discover_grants_for_organization(org_id):
    """Discover and score grants for a specific organization"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        
        # Verify organization exists
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({
                'error': 'Organization not found',
                'message': f'No organization found with ID {org_id}'
            }), 404
        
        # Initialize discovery service
        discovery_service = GrantDiscoveryService()
        
        # Run complete discovery pipeline
        result = discovery_service.discover_and_persist(org_id, limit=limit)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'organization': result['organization'],
                'discovery_stats': result['discovery_stats'],
                'grants': result['top_matches'],
                'timestamp': result['timestamp'],
                'total_found': len(result['top_matches'])
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Discovery failed'),
                'organization': org.name
            }), 500
        
    except Exception as e:
        logger.error(f"Error in grant discovery for org {org_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Grant discovery failed'
        }), 500


@bp.route('/discover/me', methods=['GET'])
def discover_grants_for_current_user():
    """Discover and score grants for the current logged-in user's organization"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'error': 'Not authenticated',
                'message': 'Please log in to discover grants'
            }), 401
        
        # Get user's organization
        org = Organization.query.filter_by(user_id=user_id).first()
        if not org:
            return jsonify({
                'error': 'No organization profile found',
                'message': 'Please complete your organization profile first'
            }), 404
        
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        
        # Initialize discovery service
        discovery_service = GrantDiscoveryService()
        
        # Run complete discovery pipeline
        result = discovery_service.discover_and_persist(org.id, limit=limit)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'organization': result['organization'],
                'discovery_stats': result['discovery_stats'],
                'grants': result['top_matches'],
                'timestamp': result['timestamp'],
                'total_found': len(result['top_matches'])
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Discovery failed'),
                'organization': org.name
            }), 500
        
    except Exception as e:
        logger.error(f"Error in grant discovery for current user: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Grant discovery failed'
        }), 500


@bp.route('/run', methods=['POST'])
def run_discovery():
    """Legacy run grant discovery process - now redirects to discover/me"""
    return discover_grants_for_current_user()

@bp.route('/status', methods=['GET'])
def get_discovery_status():
    """Get discovery status"""
    return jsonify({"status": "active", "endpoints_available": ["/discover/<org_id>", "/discover/me"]})