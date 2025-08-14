"""
Matching API Blueprint
"""
from flask import Blueprint, jsonify, request
from functools import lru_cache
import hashlib
import json
from datetime import datetime, timedelta

from app.services import matching_service
from app.services.grants_gov_client import get_grants_gov_client

# Create blueprint
matching_bp = Blueprint('matching', __name__)

# Cache for matching results (5-10 minutes)
_cache = {}
CACHE_TTL = 300  # 5 minutes

def _get_cache_key(org_id: int, keywords_hash: str) -> str:
    """Generate cache key"""
    return f"matching:{org_id}:{keywords_hash}"

def _get_from_cache(key: str) -> dict:
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
        org_id = request.args.get('orgId', type=int)
        limit = request.args.get('limit', 25, type=int)
        refresh = request.args.get('refresh') == '1'
        
        if not org_id:
            return jsonify({"error": "orgId parameter required"}), 400
        
        # Build tokens
        tokens = matching_service.build_tokens(org_id)
        
        # Generate cache key
        keywords_str = json.dumps(sorted(tokens.get("keywords", [])))
        keywords_hash = hashlib.md5(keywords_str.encode()).hexdigest()[:8]
        cache_key = _get_cache_key(org_id, keywords_hash)
        
        # Check cache (unless refresh requested)
        if not refresh:
            cached = _get_from_cache(cache_key)
            if cached:
                # Apply limit to cached results
                result = {
                    "federal": cached["federal"][:limit],
                    "news": cached["news"][:limit],
                    "context": cached["context"]
                }
                result["cached"] = True
                return jsonify(result)
        
        # Get fresh results
        results = matching_service.assemble_results(tokens)
        
        # Cache the full results
        _set_cache(cache_key, results)
        
        # Add source notes to federal items
        for item in results["federal"]:
            item["sourceNotes"] = {
                "api": "grants.gov",
                "endpoint": "search2",
                "keyword": " ".join(tokens.get("keywords", [])[:3])
            }
        
        # Add source notes to news items
        base_query = 'RFP OR "grant opportunity" OR "call for proposals"'
        for item in results["news"]:
            item["sourceNotes"] = {
                "api": "candid.news",
                "query": f"{base_query} AND {' OR '.join(tokens.get('keywords', [])[:3])}"
            }
        
        # Add source notes to context
        if results["context"]:
            topic = tokens.get("keywords", [""])[0] if tokens.get("keywords") else ""
            geo = tokens.get("geo", "")
            results["context"]["sourceNotes"] = {
                "api": "candid.grants",
                "endpoint": "transactions",
                "query": f"{topic} AND {geo}" if topic and geo else topic or geo
            }
        
        # Apply limit
        response = {
            "federal": results["federal"][:limit],
            "news": results["news"][:limit],
            "context": results["context"]
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@matching_bp.route('/api/matching/detail/grants-gov/<opp_number>', methods=['GET'])
def get_opportunity_detail(opp_number: str):
    """
    Get detailed information for a Grants.gov opportunity
    
    Path params:
        opp_number: Opportunity number
    """
    try:
        client = get_grants_gov_client()
        
        # Fetch detailed opportunity
        detail = client.fetch_opportunity(opp_number)
        
        if not detail:
            return jsonify({"error": "Opportunity not found"}), 404
        
        # Add source notes
        detail["sourceNotes"] = {
            "api": "grants.gov",
            "endpoint": "fetchOpportunity",
            "opportunityNumber": opp_number
        }
        
        return jsonify(detail)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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