"""
Candid API endpoints
"""
from flask import Blueprint, jsonify, request
from app.services.candid_client import get_candid_client

bp = Blueprint('candid', __name__, url_prefix='/api/candid')

@bp.route('/grants/search', methods=['GET'])
def search_grants():
    """Search Candid grants database"""
    client = get_candid_client()
    
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 10)), 50)  # Cap at 50
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    result = client.search_grants(query, limit)
    return jsonify(result)

@bp.route('/news/search', methods=['GET'])
def search_news():
    """Search philanthropy news"""
    client = get_candid_client()
    
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 10)), 50)  # Cap at 50
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    result = client.search_news(query, limit)
    return jsonify(result)

@bp.route('/foundation/<ein>', methods=['GET'])
def get_foundation(ein):
    """Get foundation profile by EIN"""
    client = get_candid_client()
    
    if not ein or not ein.replace('-', '').isdigit():
        return jsonify({"error": "Valid EIN is required"}), 400
    
    result = client.get_foundation_profile(ein)
    return jsonify(result)

@bp.route('/status', methods=['GET'])
def status():
    """Check Candid API status"""
    client = get_candid_client()
    result = client.test_connection()
    return jsonify(result)