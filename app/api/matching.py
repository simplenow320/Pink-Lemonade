"""
Matching API Blueprint
"""
from flask import Blueprint, jsonify, request
from functools import lru_cache
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional

from app.services.matching_service import MatchingService
from app.services.grants_gov_client import get_grants_gov_client

# Create blueprint
matching_bp = Blueprint('matching', __name__)

# Cache for matching results (5-10 minutes)
_cache = {}
CACHE_TTL = 300  # 5 minutes

def _get_cache_key(org_id: int, keywords_hash: str) -> str:
    """Generate cache key"""
    return f"matching:{org_id}:{keywords_hash}"

def _get_from_cache(key: str) -> Optional[dict]:
    """Get from cache if not expired"""
    if key in _cache:
        data, expires_at = _cache[key]
        if datetime.now() < expires_at:
            return data
        else:
            del _cache[key]
    return None

def _set_cache(key: str, data: dict, ttl_seconds: int = CACHE_TTL):
    """Set cache with TTL"""
    expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
    _cache[key] = (data, expires_at)

@matching_bp.route('/api/matching', methods=['GET'])
def get_matching_results():
    """
    Get matching results for an organization
    
    Query params:
        orgId: Organization ID (required)
        limit: Max results per feed (default 25)
        refresh: Force cache refresh if "1"
    """
    try:
        # Get parameters
        org_id_str = request.args.get('orgId')
        limit = request.args.get('limit', 25, type=int)
        refresh = request.args.get('refresh') == '1'
        
        if not org_id_str:
            return jsonify({"error": "orgId parameter required"}), 400
        
        try:
            org_id = int(org_id_str)
        except ValueError:
            return jsonify({"error": "Invalid orgId: must be a number"}), 400
        
        # Validate limit bounds
        if limit < 1 or limit > 100:
            return jsonify({"error": "Invalid limit: must be between 1 and 100"}), 400
        
        # Check if required services are configured
        try:
            service = MatchingService()
        except Exception as e:
            return jsonify({
                "error": "Service not configured",
                "message": "Matching services are not properly configured"
            }), 503
        
        # Generate cache key based on org_id and limit
        cache_key = f"matching:{org_id}:{limit}"
        
        # Check cache (unless refresh requested)
        if not refresh:
            cached = _get_from_cache(cache_key)
            if cached:
                cached["cached"] = True
                return jsonify(cached)
        
        # Get fresh results using new service
        results = service.assemble(org_id, limit)
        
        # Cache the results
        _set_cache(cache_key, results)
        
        response = results
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error", 
            "message": str(e)
        }), 500

@matching_bp.route('/api/matching/detail/grants-gov/<opp_number>', methods=['GET'])
def get_opportunity_detail(opp_number: str):
    """
    Get detailed information for a Grants.gov opportunity
    
    Path params:
        opp_number: Opportunity number
    """
    try:
        # Validate opportunity number
        if not opp_number or not opp_number.strip():
            return jsonify({
                'error': 'Invalid opportunity number'
            }), 400
        
        # Get Grants.gov client
        try:
            client = get_grants_gov_client()
        except Exception:
            return jsonify({
                'error': 'Grants.gov service unavailable'
            }), 503
        
        # Fetch detailed opportunity
        detail = client.fetch_opportunity(opp_number.strip())
        
        if not detail:
            return jsonify({"error": "Opportunity not found"}), 404
        
        # Add source notes
        response_data = detail.copy()
        response_data["sourceNotes"] = {
            "api": "grants.gov",
            "endpoint": "fetchOpportunity",
            "opportunityNumber": opp_number
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

# Cache management endpoint (for admins)
@matching_bp.route('/api/matching/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the matching cache (admin only)"""
    global _cache
    old_size = len(_cache)
    _cache = {}
    return jsonify({
        "message": "Cache cleared",
        "items_cleared": old_size
    })