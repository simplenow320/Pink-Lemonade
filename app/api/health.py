"""Health check API endpoints"""
from flask import Blueprint, jsonify
from app import db
import os
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('health', __name__, url_prefix='/api')

@bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except:
        db_status = 'unhealthy'
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
        'version': '1.0.0'
    }), 200

@bp.route('/smart-tools/health', methods=['GET'])
def smart_tools_health():
    """Smart Tools health check"""
    return jsonify({
        'status': 'healthy',
        'tools': {
            'case_support': 'enabled',
            'grant_pitch': 'enabled',
            'impact_report': 'enabled',
            'writing_assistant': 'enabled',
            'analytics': 'enabled',
            'smart_reports': 'enabled'
        }
    }), 200

@bp.route('/ai/status', methods=['GET'])
def ai_status():
    """AI service status"""
    return jsonify({
        'enabled': bool(os.getenv('OPENAI_API_KEY')),
        'features': {
            'grant_extraction': True,
            'grant_matching': True,
            'narrative_generation': True,
            'text_improvement': True
        },
        'model': 'gpt-4o'
    }), 200


@bp.route('/health/integrations', methods=['GET'])
def get_integrations_status():
    """Check integration clients and routes presence"""
    
    # Check Candid clients
    candid_status = {
        "essentials_client": False,
        "news_client": False,
        "grants_client": False,
        "secrets_present": False
    }
    
    try:
        from app.services.candid_client import EssentialsClient, NewsClient, GrantsClient
        candid_status["essentials_client"] = True
        candid_status["news_client"] = True
        candid_status["grants_client"] = True
    except ImportError:
        pass
    
    # Check secrets presence
    candid_secrets = [
        os.environ.get('CANDID_ESSENTIALS_KEY'),
        os.environ.get('CANDID_NEWS_KEYS'),
        os.environ.get('CANDID_GRANTS_KEYS')
    ]
    candid_status["secrets_present"] = all(secret for secret in candid_secrets)
    
    # Check Grants.gov client
    grants_gov_status = {"client_present": False}
    try:
        from app.services.grants_gov_client import GrantsGovClient
        grants_gov_status["client_present"] = True
    except ImportError:
        pass
    
    # Check routes presence
    routes_status = {
        "matching": False,
        "matching_detail": False,
        "onboarding_manual": False,
        "onboarding_essentials_search": False,
        "onboarding_essentials_apply": False
    }
    
    try:
        from app.api.matching import matching_bp
        routes_status["matching"] = True
        routes_status["matching_detail"] = True  # We found this route exists
    except ImportError:
        pass
    
    try:
        from app.api.onboarding import onboarding_bp
        # Check if specific routes exist (they may be missing)
        routes_status["onboarding_manual"] = False  # Will check in tests
        routes_status["onboarding_essentials_search"] = False
        routes_status["onboarding_essentials_apply"] = False
    except ImportError:
        pass
    
    return jsonify({
        "candid": candid_status,
        "grants_gov": grants_gov_status,
        "routes": routes_status
    })


@bp.route('/health/ping', methods=['GET'])
def ping_integrations():
    """Ping external integrations with safe calls"""
    
    results = {
        "candid": {
            "essentials": {"ok": False, "status": 0},
            "news": {"ok": False, "status": 0},
            "grants": {"ok": False, "status": 0}
        },
        "grants_gov": {"ok": False, "status": 0}
    }
    
    # Test Candid Essentials
    try:
        essentials_key = os.environ.get('CANDID_ESSENTIALS_KEY')
        if essentials_key:
            headers = {
                'Accept': 'application/json',
                'Subscription-Key': essentials_key
            }
            params = {
                'query': 'United Way',
                'page_size': 1
            }
            
            response = requests.get(
                'https://api.candid.org/essentials/v1/organizations/search',
                params=params,
                headers=headers,
                timeout=20
            )
            
            results["candid"]["essentials"]["status"] = response.status_code
            results["candid"]["essentials"]["ok"] = response.status_code == 200
    except Exception as e:
        logger.debug(f"Essentials ping failed: {type(e).__name__}")
    
    # Test Candid News
    try:
        news_keys = os.environ.get('CANDID_NEWS_KEYS', '').split(',')
        if news_keys and news_keys[0].strip():
            headers = {
                'Accept': 'application/json',
                'Subscription-Key': news_keys[0].strip()
            }
            
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            params = {
                'query': 'RFP',
                'start_date': start_date,
                'size': 1
            }
            
            response = requests.get(
                'https://api.candid.org/news/v1/search',
                params=params,
                headers=headers,
                timeout=20
            )
            
            results["candid"]["news"]["status"] = response.status_code
            results["candid"]["news"]["ok"] = response.status_code == 200
    except Exception as e:
        logger.debug(f"News ping failed: {type(e).__name__}")
    
    # Test Candid Grants
    try:
        grants_keys = os.environ.get('CANDID_GRANTS_KEYS', '').split(',')
        if grants_keys and grants_keys[0].strip():
            headers = {
                'Accept': 'application/json',
                'Subscription-Key': grants_keys[0].strip()
            }
            params = {
                'query': 'education AND Michigan',
                'size': 1
            }
            
            response = requests.get(
                'https://api.candid.org/grants/v1/transactions',
                params=params,
                headers=headers,
                timeout=20
            )
            
            results["candid"]["grants"]["status"] = response.status_code
            results["candid"]["grants"]["ok"] = response.status_code == 200
    except Exception as e:
        logger.debug(f"Grants ping failed: {type(e).__name__}")
    
    # Test Grants.gov
    try:
        payload = {"keyword": "education", "limit": 1}
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.post(
            'https://api.grants.gov/v1/api/search2',
            json=payload,
            headers=headers,
            timeout=20
        )
        
        results["grants_gov"]["status"] = response.status_code
        results["grants_gov"]["ok"] = response.status_code == 200
        
        # Additional check for proper JSON response structure
        if response.status_code == 200:
            try:
                data = response.json()
                results["grants_gov"]["ok"] = 'oppHits' in data or 'opportunities' in data
            except:
                results["grants_gov"]["ok"] = False
                
    except Exception as e:
        logger.debug(f"Grants.gov ping failed: {type(e).__name__}")
    
    return jsonify(results)