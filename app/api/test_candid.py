"""
Simple Candid API test endpoint
"""
from flask import Blueprint, jsonify, request
from app.services.candid_essentials import get_candid_client
import logging

logger = logging.getLogger(__name__)

test_candid_bp = Blueprint('test_candid', __name__)

@test_candid_bp.route('/api/test-candid', methods=['GET'])
def test_candid_connection():
    """Test Candid API connection with your new keys"""
    try:
        client = get_candid_client()
        
        # Test with a simple, well-known EIN
        test_ein = "13-1623877"  # United Way Worldwide
        
        logger.info(f"Testing Candid API with EIN: {test_ein}")
        result = client.search_by_ein(test_ein, limit=1)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Candid API connection successful!',
                'test_ein': test_ein,
                'org_found': True,
                'org_name': result.get('organization', {}).get('name', 'Organization found'),
                'api_working': True
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Candid API connected but no results found',
                'test_ein': test_ein,
                'org_found': False,
                'api_working': True
            })
            
    except Exception as e:
        logger.error(f"Candid API test failed: {e}")
        return jsonify({
            'success': False,
            'message': f'Candid API test failed: {str(e)}',
            'api_working': False
        }), 500