"""
Candid API endpoints - Fixed implementation with proper client usage
"""
from flask import Blueprint, jsonify, request
from app.services.candid_client import get_news_client, get_grants_client, get_essentials_client
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('candid', __name__, url_prefix='/api/candid')

@bp.route('/grants/search', methods=['GET'])
def search_grants():
    """Search Candid grants database using transactions endpoint"""
    try:
        logger.warning(f"FLASK DEBUG: Starting grants search endpoint")
        client = get_grants_client()
        logger.warning(f"FLASK DEBUG: Got client, API key available: {bool(client.api_key)}")
        
        query = request.args.get('q', '')
        location = request.args.get('location', type=int)  # Geoname ID
        page = int(request.args.get('page', 1))
        
        logger.warning(f"FLASK DEBUG: Query: {query}, Location: {location}, Page: {page}")
        
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400
        
        # Use the transactions method with proper parameters
        logger.warning(f"FLASK DEBUG: About to call client.transactions...")
        if location:
            result = client.transactions(query=query, location=location, page=page)
        else:
            result = client.transactions(query=query, page=page)
        
        logger.warning(f"FLASK DEBUG: Got result type: {type(result)}, length: {len(result) if hasattr(result, '__len__') else 'No length'}")
        if result:
            logger.warning(f"FLASK DEBUG: First grant keys: {list(result[0].keys()) if result else 'Empty'}")
        
        # Format response
        if result:
            return jsonify({
                "success": True,
                "data": result,
                "count": len(result),
                "query": query
            })
        else:
            return jsonify({
                "success": True,
                "data": [],
                "count": 0,
                "query": query,
                "message": "No grants found"
            })
            
    except Exception as e:
        logger.error(f"Error searching grants: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to search grants",
            "message": str(e)
        }), 500

@bp.route('/grants/snapshot', methods=['GET'])
def grant_snapshot():
    """Get grant snapshot for topic and geography"""
    try:
        client = get_grants_client()
        
        topic = request.args.get('topic', '')
        geo = request.args.get('geo', '')
        
        if not topic:
            return jsonify({"error": "Topic parameter is required"}), 400
        
        # Use the snapshot_for method
        result = client.snapshot_for(topic=topic, geo=geo)
        
        return jsonify({
            "success": True,
            "data": result,
            "topic": topic,
            "geography": geo
        })
        
    except Exception as e:
        logger.error(f"Error getting snapshot: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get grant snapshot",
            "message": str(e)
        }), 500

@bp.route('/news/search', methods=['GET'])
def search_news():
    """Search philanthropy news"""
    try:
        client = get_news_client()
        
        query = request.args.get('q', '')
        limit = min(int(request.args.get('limit', 25)), 100)  # Cap at 100
        page = int(request.args.get('page', 1))
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400
        
        # Use the actual search method from NewsClient
        result = client.search(
            query=query,
            page=page,
            size=limit,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            "success": True,
            "data": result,
            "count": len(result),
            "query": query
        })
        
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to search news",
            "message": str(e)
        }), 500

@bp.route('/foundation/<ein>', methods=['GET'])
def get_foundation(ein):
    """Get foundation profile by EIN"""
    try:
        client = get_essentials_client()
        
        if not ein or not ein.replace('-', '').isdigit():
            return jsonify({"error": "Valid EIN is required"}), 400
        
        # Use search_org method from EssentialsClient
        result = client.search_org(search_terms=ein)
        
        if result:
            return jsonify({
                "success": True,
                "data": result,
                "ein": ein
            })
        else:
            return jsonify({
                "success": False,
                "message": "Foundation not found",
                "ein": ein
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting foundation: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get foundation profile",
            "message": str(e)
        }), 500

@bp.route('/foundation/search', methods=['GET'])
def search_foundation():
    """Search for foundation by name"""
    try:
        client = get_essentials_client()
        
        name = request.args.get('name', '')
        
        if not name:
            return jsonify({"error": "Name parameter is required"}), 400
        
        # Use search_org method
        result = client.search_org(search_terms=name)
        
        if result:
            return jsonify({
                "success": True,
                "data": result,
                "query": name
            })
        else:
            return jsonify({
                "success": True,
                "data": None,
                "message": "No foundation found",
                "query": name
            })
            
    except Exception as e:
        logger.error(f"Error searching foundation: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to search foundation",
            "message": str(e)
        }), 500

@bp.route('/status', methods=['GET'])
def status():
    """Check Candid API status"""
    try:
        status_report = {
            "grants_api": False,
            "news_api": False,
            "essentials_api": False,
            "overall_status": "degraded"
        }
        
        # Test Grants API
        try:
            grants_client = get_grants_client()
            test_result = grants_client.transactions(query="test", page=1)
            if test_result is not None and len(test_result) > 0:
                status_report["grants_api"] = True
            logger.info(f"Grants API test result: {test_result}")
        except Exception as e:
            logger.error(f"Grants API test failed: {e}")
        
        # Test News API
        try:
            news_client = get_news_client()
            test_result = news_client.search("test", size=1)
            if test_result is not None:
                status_report["news_api"] = True
        except Exception as e:
            logger.debug(f"News API test failed: {e}")
        
        # Test Essentials API
        try:
            essentials_client = get_essentials_client()
            test_result = essentials_client.search_org("Gates Foundation")
            if test_result is not None:
                status_report["essentials_api"] = True
        except Exception as e:
            logger.debug(f"Essentials API test failed: {e}")
        
        # Determine overall status
        apis_working = sum([
            status_report["grants_api"],
            status_report["news_api"],
            status_report["essentials_api"]
        ])
        
        if apis_working == 3:
            status_report["overall_status"] = "operational"
        elif apis_working >= 1:
            status_report["overall_status"] = "partial"
        else:
            status_report["overall_status"] = "offline"
        
        return jsonify({
            "success": True,
            "status": status_report,
            "message": f"{apis_working} of 3 Candid APIs operational"
        })
        
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to check API status",
            "message": str(e)
        }), 500

@bp.route('/test', methods=['GET'])
def test():
    """Quick test endpoint"""
    return jsonify({
        "success": True,
        "message": "Candid API endpoints are available",
        "endpoints": [
            "/api/candid/grants/search?q=education",
            "/api/candid/grants/snapshot?topic=youth&geo=NYC",
            "/api/candid/news/search?q=philanthropy",
            "/api/candid/foundation/{ein}",
            "/api/candid/foundation/search?name=Gates",
            "/api/candid/status"
        ]
    })