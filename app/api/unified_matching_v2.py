"""
Unified Matching API V2 - Consolidated and Reliable
Single endpoint for grant discovery, persistence, and AI scoring
"""
from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
import logging

from app.services.grant_discovery_service_v2 import GrantDiscoveryServiceV2

logger = logging.getLogger(__name__)

unified_v2_bp = Blueprint('unified_matching_v2', __name__)


@unified_v2_bp.route('/api/matching/discover/<int:org_id>', methods=['GET'])
@cross_origin()
def discover_grants(org_id: int):
    """
    Primary endpoint for grant discovery and matching
    
    Features:
    - Discovers from multiple sources (Candid, Grants.gov, foundations)
    - Persists to database with deduplication
    - Applies AI scoring when available
    - Returns cached data if recent
    - Handles failures gracefully
    
    Query params:
    - limit: Max grants to return (default 50)
    - refresh: Force refresh even if cached data exists (default false)
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # Validate limit
        if limit < 1:
            limit = 1
        elif limit > 100:
            limit = 100
        
        # Use the consolidated discovery service
        service = GrantDiscoveryServiceV2()
        results = service.discover_and_persist(
            org_id=org_id,
            limit=limit,
            force_refresh=refresh
        )
        
        # Add metadata for frontend
        results['endpoint'] = 'v2/discover'
        results['features'] = [
            'multi_source_discovery',
            'database_persistence', 
            'ai_scoring',
            'smart_caching',
            'error_resilience'
        ]
        
        # Return appropriate status code
        if results.get('success'):
            return jsonify(results), 200
        else:
            # Still return results (may have cached data) but with error status
            return jsonify(results), 207  # 207 Multi-Status indicates partial success
            
    except Exception as e:
        logger.error(f"Error in discover_grants for org {org_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'grants': [],
            'discovery_stats': {}
        }), 500


@unified_v2_bp.route('/api/matching/grants/<int:org_id>', methods=['GET'])
@cross_origin()
def get_persisted_grants(org_id: int):
    """
    Get persisted grants for an organization (for Smart Tools and display)
    
    Query params:
    - limit: Max grants to return (default 100)
    - min_score: Minimum match score filter (optional)
    """
    try:
        from app.models import Grant
        from app import db
        
        limit = request.args.get('limit', 100, type=int)
        min_score = request.args.get('min_score', type=int)
        
        # Build query
        query = Grant.query.filter_by(org_id=org_id)
        
        # Apply score filter if provided
        if min_score is not None:
            query = query.filter(Grant.match_score >= min_score)
        
        # Order by score and date
        grants = query.order_by(
            Grant.match_score.desc().nullsfirst(),
            Grant.created_at.desc()
        ).limit(limit).all()
        
        return jsonify({
            'success': True,
            'grants': [g.to_dict() for g in grants],
            'total': len(grants),
            'filters_applied': {
                'min_score': min_score
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting grants for org {org_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'grants': []
        }), 500


@unified_v2_bp.route('/api/matching/smart-tools/<int:org_id>', methods=['GET'])
@cross_origin()
def get_grants_for_smart_tools(org_id: int):
    """
    Get grants specifically formatted for Smart Tools usage
    Ensures all necessary fields are present
    """
    try:
        service = GrantDiscoveryServiceV2()
        grants = service.get_grants_for_smart_tools(org_id, limit=100)
        
        return jsonify({
            'success': True,
            'organization_id': org_id,
            'grants': grants,
            'total': len(grants),
            'purpose': 'smart_tools_integration'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting grants for smart tools: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'grants': []
        }), 500


@unified_v2_bp.route('/api/matching/stats/<int:org_id>', methods=['GET'])
@cross_origin()
def get_discovery_stats(org_id: int):
    """
    Get discovery and matching statistics for an organization
    """
    try:
        from app import db
        from app.models import Grant
        from datetime import datetime, timedelta
        
        # Calculate various statistics
        total_grants = Grant.query.filter_by(org_id=org_id).count()
        
        # Recent discoveries (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_grants = Grant.query.filter(
            Grant.org_id == org_id,
            Grant.created_at >= week_ago
        ).count()
        
        # High matches
        high_matches = Grant.query.filter(
            Grant.org_id == org_id,
            Grant.match_score >= 4
        ).count()
        
        # By source
        sources = db.session.query(
            Grant.source_name,
            db.func.count(Grant.id)
        ).filter_by(org_id=org_id).group_by(Grant.source_name).all()
        
        source_breakdown = {source: count for source, count in sources}
        
        # By status
        statuses = db.session.query(
            Grant.status,
            db.func.count(Grant.id)
        ).filter_by(org_id=org_id).group_by(Grant.status).all()
        
        status_breakdown = {status: count for status, count in statuses}
        
        return jsonify({
            'success': True,
            'stats': {
                'total_grants': total_grants,
                'recent_discoveries': recent_grants,
                'high_matches': high_matches,
                'by_source': source_breakdown,
                'by_status': status_breakdown,
                'calculated_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting stats for org {org_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'stats': {}
        }), 500


@unified_v2_bp.route('/api/matching/test/<int:org_id>', methods=['GET'])
@cross_origin()
def test_discovery_pipeline(org_id: int):
    """
    Test endpoint to verify the complete discovery pipeline
    """
    try:
        results = {
            'organization_id': org_id,
            'tests': {},
            'success': True
        }
        
        # Test 1: Organization exists
        from app.models import Organization
        org = Organization.query.get(org_id)
        results['tests']['organization_exists'] = org is not None
        if org:
            results['organization_name'] = org.name
        
        # Test 2: Can generate tokens
        try:
            from app.services.org_tokens import get_org_tokens
            tokens = get_org_tokens(org_id)
            results['tests']['token_generation'] = True
            results['tokens_sample'] = {
                'keywords': tokens.get('keywords', [])[:3],
                'has_pcs_codes': bool(tokens.get('pcs_subject_codes')),
                'has_locations': bool(tokens.get('locations'))
            }
        except Exception as e:
            results['tests']['token_generation'] = False
            results['tests']['token_error'] = str(e)
        
        # Test 3: Discovery service works
        try:
            service = GrantDiscoveryServiceV2()
            discovery_results = service.discover_and_persist(org_id, limit=5, force_refresh=True)
            results['tests']['discovery_service'] = discovery_results.get('success', False)
            results['discovery_summary'] = discovery_results.get('discovery_stats', {})
        except Exception as e:
            results['tests']['discovery_service'] = False
            results['tests']['discovery_error'] = str(e)
        
        # Test 4: Grants persisted
        from app.models import Grant
        grant_count = Grant.query.filter_by(org_id=org_id).count()
        results['tests']['grants_persisted'] = grant_count > 0
        results['total_grants_in_db'] = grant_count
        
        # Test 5: AI scoring available
        try:
            from app.services.ai_grant_matcher import AIGrantMatcher
            ai_matcher = AIGrantMatcher()
            results['tests']['ai_scoring_available'] = True
        except:
            results['tests']['ai_scoring_available'] = False
        
        # Overall success
        results['success'] = all(
            results['tests'].get(key, False) 
            for key in ['organization_exists', 'token_generation', 'discovery_service', 'grants_persisted']
        )
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Error in test pipeline: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'tests': {}
        }), 500