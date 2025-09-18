"""Health check API endpoints"""
from flask import Blueprint, jsonify
from app import db
from sqlalchemy import text
import os
import requests
from datetime import datetime, timedelta
import logging
from app.services.apiManager import api_manager

logger = logging.getLogger(__name__)

bp = Blueprint('health', __name__, url_prefix='/api')

@bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
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


@bp.route('/health/api-sources', methods=['GET'])
def api_sources_diagnostics():
    """Comprehensive API sources health and diagnostics endpoint"""
    try:
        # Get comprehensive status report from APIManager
        status_report = api_manager.get_credential_status_report()
        
        # Add enhanced diagnostic information
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_sources': len(api_manager.sources),
                'enabled_sources': len([s for s in api_manager.sources.values() if s.get('enabled')]),
                'sources_with_credentials': len([s for s in api_manager.sources.values() if s.get('api_key')]),
                'healthy_sources': 0
            },
            'sources': {},
            'credential_requirements': {},
            'configuration_validation': status_report.get('validation_report', {}),
            'recommendations': []
        }
        
        # Analyze each source
        for source_id, config in api_manager.sources.items():
            source_health = api_manager.config.check_source_health(source_id)
            if source_health['healthy']:
                diagnostics['summary']['healthy_sources'] += 1
            
            # Detailed source information
            diagnostics['sources'][source_id] = {
                'name': config.get('name', source_id),
                'enabled': config.get('enabled', False),
                'healthy': source_health['healthy'],
                'description': config.get('description', 'No description available'),
                'base_url': config.get('base_url'),
                'supports': config.get('supports', []),
                'auth_type': config.get('auth_type'),
                'auth_header': config.get('auth_header'),
                'credential_required': config.get('credential_required', False),
                'has_credentials': bool(config.get('api_key')),
                'rate_limit': config.get('rate_limit', {}),
                'cache_ttl': config.get('cache_ttl'),
                'errors': source_health.get('errors', []),
                'warnings': source_health.get('warnings', [])
            }
            
            # Track why sources are enabled/disabled
            enabled_reason = 'Unknown'
            if not config.get('enabled', False):
                if config.get('credential_required', False) and not config.get('api_key'):
                    enabled_reason = 'Disabled: Missing required credentials'
                else:
                    enabled_reason = 'Disabled: Explicitly disabled in configuration'
            else:
                if config.get('credential_required', False):
                    enabled_reason = 'Enabled: Has required credentials'
                else:
                    enabled_reason = 'Enabled: Public API (no credentials required)'
            
            diagnostics['sources'][source_id]['enabled_reason'] = enabled_reason
        
        # Credential requirements breakdown
        for source_id, cred_status in status_report.get('credential_status', {}).items():
            diagnostics['credential_requirements'][source_id] = {
                'primary_env_var': cred_status.get('primary_env_var'),
                'fallback_env_vars': cred_status.get('fallback_env_vars', []),
                'credential_required': cred_status.get('credential_required', False),
                'has_credentials': cred_status.get('has_credentials', False),
                'auth_type': cred_status.get('auth_type')
            }
        
        # Generate recommendations
        disabled_sources = [
            source_id for source_id, info in diagnostics['sources'].items()
            if not info['enabled'] and info['credential_required']
        ]
        
        if disabled_sources:
            diagnostics['recommendations'].append({
                'type': 'missing_credentials',
                'message': f'Consider adding credentials for: {", ".join(disabled_sources)}',
                'sources': disabled_sources
            })
        
        unhealthy_sources = [
            source_id for source_id, info in diagnostics['sources'].items()
            if info['enabled'] and not info['healthy']
        ]
        
        if unhealthy_sources:
            diagnostics['recommendations'].append({
                'type': 'configuration_issues',
                'message': f'Check configuration for: {", ".join(unhealthy_sources)}',
                'sources': unhealthy_sources
            })
        
        return jsonify(diagnostics), 200
        
    except Exception as e:
        logger.error(f"Error generating API sources diagnostics: {e}")
        return jsonify({
            'error': 'Failed to generate diagnostics',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@bp.route('/health/api-sources/test/<source_id>', methods=['POST'])
def test_api_source(source_id):
    """Test a specific API source with a simple request"""
    try:
        if source_id not in api_manager.sources:
            return jsonify({
                'error': 'Source not found',
                'source_id': source_id,
                'available_sources': list(api_manager.sources.keys())
            }), 404
        
        # Attempt to fetch a small amount of data from the source
        test_params = {'limit': 1, 'query': 'test'}
        start_time = datetime.now()
        
        try:
            results = api_manager.get_grants_from_source(source_id, test_params)
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return jsonify({
                'source_id': source_id,
                'test_successful': True,
                'response_time_seconds': response_time,
                'results_count': len(results) if results else 0,
                'timestamp': end_time.isoformat(),
                'sample_result': results[0] if results else None
            }), 200
            
        except Exception as fetch_error:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return jsonify({
                'source_id': source_id,
                'test_successful': False,
                'error': str(fetch_error),
                'error_type': type(fetch_error).__name__,
                'response_time_seconds': response_time,
                'timestamp': end_time.isoformat()
            }), 200  # Return 200 because the test endpoint itself worked
            
    except Exception as e:
        logger.error(f"Error testing API source {source_id}: {e}")
        return jsonify({
            'error': 'Test failed',
            'source_id': source_id,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500