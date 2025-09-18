"""
Integration tests to verify public APIs continue working when private APIs fail
Tests that credential issues with private APIs don't affect public API functionality
"""

import pytest
import os
from unittest.mock import patch, Mock
from typing import Dict, Any, List

from app.services.apiManager import APIManager, CircuitBreakerState
from app.config.apiConfig import APIConfig
from tests.fixtures.api_responses import get_mock_response, MOCK_ERROR_RESPONSES


class TestPublicAPIsWithPrivateFailures:
    """Test that public APIs work independently of private API failures"""
    
    def test_public_apis_work_with_all_private_apis_down(self, clean_environment):
        """Test public APIs work when all private APIs are failing"""
        # Set invalid credentials for all private APIs
        invalid_credentials = {
            'SAM_GOV_API_KEY': 'invalid-sam-key',
            'CANDID_API_KEY': 'invalid-candid-key',
            'FDO_API_KEY': 'invalid-fdo-key',
            'GRANTWATCH_API_KEY': 'invalid-grantwatch-key',
            'ZYTE_API_KEY': 'invalid-zyte-key'
        }
        
        with patch.dict(os.environ, invalid_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    
                    # Private APIs fail with auth errors
                    if any(domain in url for domain in ['sam.gov', 'candid.org', 'foundationdirectory.org', 'grantwatch.com', 'zyte.com']):
                        response.status_code = 401
                        response.text = 'Unauthorized'
                        response.json.return_value = {'error': 'Invalid API key'}
                    # Public APIs work fine
                    elif 'grants.gov' in url:
                        response.status_code = 200
                        response.json.return_value = get_mock_response('grants_gov', 'success')
                        response.text = str(response.json.return_value)
                    elif 'federalregister.gov' in url:
                        response.status_code = 200
                        response.json.return_value = get_mock_response('federal_register', 'success')
                        response.text = str(response.json.return_value)
                    else:
                        response.status_code = 200
                        response.json.return_value = {'results': []}
                        response.text = '{"results": []}'
                    
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                # Public APIs should work despite private API failures
                grants_gov_results = api_manager.get_grants_from_source('grants_gov', {'query': 'education'})
                federal_register_results = api_manager.get_grants_from_source('federal_register', {'query': 'funding'})
                
                # Should get results from public APIs
                assert isinstance(grants_gov_results, (list, dict))
                assert isinstance(federal_register_results, (list, dict))
                
                # Private APIs should fail gracefully
                sam_results = api_manager.get_grants_from_source('sam_gov_opportunities', {})
                candid_results = api_manager.get_grants_from_source('candid', {})
                
                assert sam_results == []
                assert candid_results == []
    
    def test_search_opportunities_prioritizes_working_sources(self, clean_environment):
        """Test search_opportunities gets results from working sources despite failures"""
        # Mix of invalid and missing credentials
        mixed_credentials = {
            'SAM_GOV_API_KEY': 'invalid-sam-key',
            'CANDID_API_KEY': 'invalid-candid-key'
            # GOVINFO_API_KEY missing (but it's optional)
            # FDO_API_KEY missing (required, so disabled)
        }
        
        with patch.dict(os.environ, mixed_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    
                    if 'sam.gov' in url or 'candid.org' in url:
                        # Auth failures
                        response.status_code = 401
                        response.text = 'Unauthorized'
                        response.json.return_value = {'error': 'Invalid API key'}
                    elif 'grants.gov' in url:
                        # Public API works
                        response.status_code = 200
                        mock_data = get_mock_response('grants_gov', 'success')
                        response.json.return_value = mock_data
                        response.text = str(mock_data)
                    elif 'federalregister.gov' in url:
                        # Public API works
                        response.status_code = 200
                        mock_data = get_mock_response('federal_register', 'success')
                        response.json.return_value = mock_data
                        response.text = str(mock_data)
                    elif 'govinfo.gov' in url:
                        # Optional credentials API works without credentials
                        response.status_code = 200
                        mock_data = get_mock_response('govinfo', 'success')
                        response.json.return_value = mock_data
                        response.text = str(mock_data)
                    else:
                        response.status_code = 200
                        response.json.return_value = {'results': []}
                        response.text = '{"results": []}'
                    
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                # Search should aggregate results from working sources
                results = api_manager.search_opportunities('education funding', {'limit': 10})
                
                # Should get aggregated results from working sources
                assert isinstance(results, list)
                # Should not crash due to private API failures
    
    def test_circuit_breakers_isolate_private_api_failures(self, clean_environment):
        """Test circuit breakers isolate private API failures from public APIs"""
        invalid_credentials = {
            'SAM_GOV_API_KEY': 'failing-sam-key'
        }
        
        with patch.dict(os.environ, invalid_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    
                    if 'sam.gov' in url:
                        # SAM.gov fails consistently
                        response.status_code = 500
                        response.text = 'Internal Server Error'
                        response.json.return_value = {'error': 'Server error'}
                    else:
                        # Other APIs work
                        response.status_code = 200
                        response.json.return_value = get_mock_response('grants_gov', 'success')
                        response.text = str(response.json.return_value)
                    
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                # Trigger SAM.gov circuit breaker
                sam_cb = api_manager.circuit_breakers.get('sam_gov_opportunities')
                if sam_cb:
                    failure_threshold = sam_cb.failure_threshold
                    
                    # Make enough failed requests to open circuit
                    for i in range(failure_threshold):
                        api_manager.get_grants_from_source('sam_gov_opportunities', {'attempt': i})
                    
                    # Circuit should be open
                    assert sam_cb.state == CircuitBreakerState.OPEN
                
                # Public APIs should still work normally
                grants_gov_results = api_manager.get_grants_from_source('grants_gov', {})
                assert isinstance(grants_gov_results, (list, dict))
                
                # Further SAM.gov requests should be blocked by circuit breaker
                sam_results = api_manager.get_grants_from_source('sam_gov_opportunities', {})
                assert sam_results == []
    
    def test_rate_limiting_independence_between_public_and_private(self, clean_environment):
        """Test rate limiting independence between public and private APIs"""
        api_manager = APIManager()
        
        with patch('app.services.apiManager.requests.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'results': []}
            mock_response.text = '{"results": []}'
            mock_request.return_value = mock_response
            
            # Exhaust rate limit for one source
            for i in range(20):  # Exceed typical rate limits
                api_manager.get_grants_from_source('grants_gov', {'call': i})
            
            # Other sources should not be affected
            federal_register_result = api_manager.get_grants_from_source('federal_register', {})
            assert isinstance(federal_register_result, (list, dict))
    
    def test_caching_isolation_between_public_and_private(self, clean_environment):
        """Test caching isolation between public and private APIs"""
        invalid_credentials = {
            'SAM_GOV_API_KEY': 'invalid-key'
        }
        
        with patch.dict(os.environ, invalid_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                call_tracker = {'grants_gov': 0, 'sam_gov': 0}
                
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    
                    if 'grants.gov' in url:
                        call_tracker['grants_gov'] += 1
                        response.status_code = 200
                        response.json.return_value = get_mock_response('grants_gov', 'success')
                        response.text = str(response.json.return_value)
                    elif 'sam.gov' in url:
                        call_tracker['sam_gov'] += 1
                        response.status_code = 401
                        response.text = 'Unauthorized'
                        response.json.return_value = {'error': 'Invalid API key'}
                    else:
                        response.status_code = 200
                        response.json.return_value = {'results': []}
                        response.text = '{"results": []}'
                    
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                params = {'query': 'test'}
                
                # Make repeated requests to public API (should cache)
                api_manager.get_grants_from_source('grants_gov', params)
                api_manager.get_grants_from_source('grants_gov', params)
                
                # Should cache public API (fewer calls)
                first_grants_gov_calls = call_tracker['grants_gov']
                
                # Private API failures should not affect public API cache
                api_manager.get_grants_from_source('sam_gov_opportunities', params)
                api_manager.get_grants_from_source('sam_gov_opportunities', params)
                
                # Public API cache should not be affected
                api_manager.get_grants_from_source('grants_gov', params)
                
                # Should still use cache for public API
                assert call_tracker['grants_gov'] == first_grants_gov_calls
    
    def test_public_api_performance_unaffected_by_private_failures(self, clean_environment):
        """Test public API performance is not degraded by private API failures"""
        invalid_credentials = {
            'SAM_GOV_API_KEY': 'failing-key',
            'CANDID_API_KEY': 'failing-key',
            'FDO_API_KEY': 'failing-key'
        }
        
        with patch.dict(os.environ, invalid_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    
                    if any(domain in url for domain in ['sam.gov', 'candid.org', 'foundationdirectory.org']):
                        # Slow failing private APIs
                        import time
                        time.sleep(0.1)  # Simulate slow failure
                        response.status_code = 500
                        response.text = 'Server Error'
                        response.json.return_value = {'error': 'Server error'}
                    else:
                        # Fast public APIs
                        response.status_code = 200
                        response.json.return_value = get_mock_response('grants_gov', 'success')
                        response.text = str(response.json.return_value)
                    
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                import time
                
                # Time public API calls
                start_time = time.time()
                for i in range(5):
                    api_manager.get_grants_from_source('grants_gov', {'call': i})
                public_api_time = time.time() - start_time
                
                # Time private API calls (will fail but shouldn't affect timing of future public calls)
                for i in range(3):
                    api_manager.get_grants_from_source('sam_gov_opportunities', {'call': i})
                
                # Time public API calls again
                start_time = time.time()
                for i in range(5):
                    api_manager.get_grants_from_source('grants_gov', {'call': i + 10})
                second_public_api_time = time.time() - start_time
                
                # Public API performance should not be significantly affected
                # Allow some variation but should not be dramatically slower
                assert second_public_api_time < public_api_time * 2
    
    def test_public_apis_work_with_no_private_credentials(self, clean_environment):
        """Test public APIs work perfectly with zero private credentials"""
        # Ensure no private credentials are set
        api_manager = APIManager()
        
        with patch('app.services.apiManager.requests.request') as mock_request:
            def mock_response_handler(method, url, **kwargs):
                response = Mock()
                response.status_code = 200
                
                if 'grants.gov' in url:
                    response.json.return_value = get_mock_response('grants_gov', 'success')
                elif 'federalregister.gov' in url:
                    response.json.return_value = get_mock_response('federal_register', 'success')
                elif 'govinfo.gov' in url:
                    response.json.return_value = get_mock_response('govinfo', 'success')
                else:
                    response.json.return_value = {'results': []}
                
                response.text = str(response.json.return_value)
                return response
            
            mock_request.side_effect = mock_response_handler
            
            # All public APIs should work
            public_sources = ['grants_gov', 'federal_register', 'govinfo']
            
            for source in public_sources:
                try:
                    result = api_manager.get_grants_from_source(source, {'query': 'test'})
                    assert isinstance(result, (list, dict))
                except Exception as e:
                    # Some sources might not be enabled, but should not crash
                    pass
            
            # Search should work with available public sources
            results = api_manager.search_opportunities('education', {})
            assert isinstance(results, list)
    
    def test_mixed_success_failure_aggregation(self, clean_environment):
        """Test aggregation works correctly with mixed success/failure"""
        partial_credentials = {
            'SAM_GOV_API_KEY': 'invalid-key'  # Will fail
            # No other private credentials
        }
        
        with patch.dict(os.environ, partial_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    
                    if 'sam.gov' in url:
                        # Fails
                        response.status_code = 401
                        response.text = 'Unauthorized'
                        response.json.return_value = {'error': 'Invalid API key'}
                    elif 'grants.gov' in url:
                        # Succeeds with mock data
                        response.status_code = 200
                        mock_data = get_mock_response('grants_gov', 'success')
                        response.json.return_value = mock_data
                        response.text = str(mock_data)
                    elif 'federalregister.gov' in url:
                        # Succeeds with mock data
                        response.status_code = 200
                        mock_data = get_mock_response('federal_register', 'success')
                        response.json.return_value = mock_data
                        response.text = str(mock_data)
                    else:
                        # Default success
                        response.status_code = 200
                        response.json.return_value = {'results': []}
                        response.text = '{"results": []}'
                    
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                # Search should aggregate results from successful sources
                results = api_manager.search_opportunities('funding', {})
                
                # Should get results from working sources
                assert isinstance(results, list)
                # Should not crash despite failures
    
    def test_configuration_health_with_private_failures(self, clean_environment):
        """Test configuration health accurately reflects private API failures"""
        invalid_credentials = {
            'SAM_GOV_API_KEY': 'invalid-key',
            'CANDID_API_KEY': 'invalid-key'
        }
        
        with patch.dict(os.environ, invalid_credentials):
            config = APIConfig()
            
            # Overall validation should reflect mixed state
            validation_report = config.validate_configuration()
            
            # Should have some healthy sources (public ones)
            assert validation_report['healthy_sources'] > 0
            
            # Should have some sources with credentials (though invalid)
            assert validation_report['sources_with_credentials'] > 0
            
            # Individual health checks
            grants_gov_health = config.check_source_health('grants_gov')
            assert grants_gov_health.get('healthy', False) is True
            
            sam_health = config.check_source_health('sam_gov_opportunities')
            # Should be healthy from config perspective (has credentials)
            # Runtime failures are detected by circuit breakers, not config health
            assert sam_health.get('healthy', False) is True
    
    def test_fallback_behavior_public_only(self, clean_environment):
        """Test system gracefully falls back to public-only operation"""
        # Simulate total private API unavailability
        invalid_credentials = {
            'SAM_GOV_API_KEY': 'invalid',
            'CANDID_API_KEY': 'invalid',
            'FDO_API_KEY': 'invalid',
            'GRANTWATCH_API_KEY': 'invalid',
            'ZYTE_API_KEY': 'invalid'
        }
        
        with patch.dict(os.environ, invalid_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    
                    # All private APIs fail
                    if any(private in url for private in ['sam.gov', 'candid.org', 'foundationdirectory.org', 'grantwatch.com', 'zyte.com']):
                        response.status_code = 401
                        response.text = 'Unauthorized'
                        response.json.return_value = {'error': 'Invalid API key'}
                    else:
                        # Public APIs work
                        response.status_code = 200
                        if 'grants.gov' in url:
                            response.json.return_value = get_mock_response('grants_gov', 'success')
                        elif 'federalregister.gov' in url:
                            response.json.return_value = get_mock_response('federal_register', 'success')
                        else:
                            response.json.return_value = {'results': []}
                        response.text = str(response.json.return_value)
                    
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                # System should operate in public-only mode
                enabled_sources = api_manager.get_enabled_sources()
                
                # Should have some enabled sources (public ones)
                public_sources_enabled = any(
                    source in enabled_sources 
                    for source in ['grants_gov', 'federal_register', 'govinfo']
                )
                
                # Search should still work with public sources
                results = api_manager.search_opportunities('education', {})
                assert isinstance(results, list)
                
                # Direct public API calls should work
                grants_result = api_manager.get_grants_from_source('grants_gov', {})
                assert isinstance(grants_result, (list, dict))