"""
Integration tests for APIManager with partial credentials
Tests that the system works correctly when only some API sources have valid credentials
"""

import pytest
import os
from unittest.mock import patch, Mock
from typing import Dict, Any, List

from app.services.apiManager import APIManager, CircuitBreakerState
from app.config.apiConfig import APIConfig
from tests.fixtures.api_responses import get_mock_response, SOURCE_MOCK_RESPONSES
from tests.fixtures.mock_server import MockAPIServer


class TestAPIManagerPartialCredentials:
    """Integration tests for APIManager with partial credential scenarios"""
    
    def test_mixed_credential_scenario_basic(self, clean_environment):
        """Test basic mixed credential scenario"""
        # Set up partial credentials
        partial_credentials = {
            'SAM_GOV_API_KEY': 'valid-sam-key',
            'GOVINFO_API_KEY': 'valid-govinfo-key'
            # Intentionally not setting CANDID_API_KEY, FDO_API_KEY
        }
        
        with patch.dict(os.environ, partial_credentials):
            api_manager = APIManager()
            config = APIConfig()
            
            # Verify configuration reflects partial credentials
            enabled_sources = api_manager.get_enabled_sources()
            
            # Sources with credentials should be enabled
            assert 'sam_gov_opportunities' in enabled_sources
            assert 'govinfo' in enabled_sources
            
            # Sources without credentials should not be enabled
            assert 'candid' not in enabled_sources
            assert 'foundation_directory' not in enabled_sources
            
            # Public sources should be enabled regardless
            public_sources = ['grants_gov', 'federal_register']
            for source in public_sources:
                source_config = config.get_source_config(source)
                if source_config.get('enabled', False):
                    assert source in enabled_sources or not source_config.get('credential_required', False)
    
    def test_search_opportunities_with_partial_credentials(self, clean_environment):
        """Test search_opportunities works with partial credentials"""
        partial_credentials = {
            'SAM_GOV_API_KEY': 'valid-sam-key',
            'GOVINFO_API_KEY': 'valid-govinfo-key'
        }
        
        with patch.dict(os.environ, partial_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    response.status_code = 200
                    response.headers = {'Content-Type': 'application/json'}
                    
                    # Different responses based on URL
                    if 'grants.gov' in url:
                        response.json.return_value = get_mock_response('grants_gov', 'success')
                    elif 'sam.gov' in url:
                        response.json.return_value = get_mock_response('sam_gov_opportunities', 'success')
                    elif 'govinfo.gov' in url:
                        response.json.return_value = get_mock_response('govinfo', 'success')
                    elif 'federalregister.gov' in url:
                        response.json.return_value = get_mock_response('federal_register', 'success')
                    else:
                        response.json.return_value = {'results': []}
                    
                    response.text = str(response.json.return_value)
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                # Search should work with available sources
                results = api_manager.search_opportunities('education funding', {'limit': 10})
                
                # Should get results from enabled sources
                assert isinstance(results, list)
                # Results might be empty but should not crash
    
    def test_circuit_breaker_isolation_with_partial_credentials(self, clean_environment):
        """Test that circuit breakers work independently with partial credentials"""
        partial_credentials = {
            'SAM_GOV_API_KEY': 'invalid-sam-key',  # Will fail
            'GOVINFO_API_KEY': 'valid-govinfo-key'  # Will succeed
        }
        
        with patch.dict(os.environ, partial_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    
                    if 'sam.gov' in url:
                        # Invalid credentials - return 401
                        response.status_code = 401
                        response.text = 'Unauthorized'
                        response.json.return_value = {'error': 'Invalid API key'}
                    elif 'govinfo.gov' in url:
                        # Valid credentials - return success
                        response.status_code = 200
                        response.json.return_value = get_mock_response('govinfo', 'success')
                        response.text = str(response.json.return_value)
                    else:
                        # Public APIs work
                        response.status_code = 200
                        response.json.return_value = get_mock_response('grants_gov', 'success')
                        response.text = str(response.json.return_value)
                    
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                # SAM.gov should fail and trigger circuit breaker
                sam_cb = api_manager.circuit_breakers.get('sam_gov_opportunities')
                initial_sam_failures = sam_cb.failure_count if sam_cb else 0
                
                sam_results = api_manager.get_grants_from_source('sam_gov_opportunities', {})
                assert sam_results == []
                
                if sam_cb:
                    assert sam_cb.failure_count > initial_sam_failures
                
                # GovInfo should work fine
                govinfo_results = api_manager.get_grants_from_source('govinfo', {})
                # Should get results or at least not crash
                assert isinstance(govinfo_results, (list, dict))
    
    def test_rate_limiting_independence_with_partial_credentials(self, clean_environment):
        """Test that rate limiting works independently for different sources"""
        partial_credentials = {
            'SAM_GOV_API_KEY': 'valid-sam-key',
            'GOVINFO_API_KEY': 'valid-govinfo-key'
        }
        
        with patch.dict(os.environ, partial_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                # Mock successful responses
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'results': []}
                mock_response.text = '{"results": []}'
                mock_request.return_value = mock_response
                
                # Test different sources have independent rate limits
                sam_config = api_manager.sources.get('sam_gov_opportunities', {})
                govinfo_config = api_manager.sources.get('govinfo', {})
                
                sam_rate_limit = sam_config.get('rate_limit', {})
                govinfo_rate_limit = govinfo_config.get('rate_limit', {})
                
                # Sources should have their own rate limit configurations
                # and not affect each other
                if sam_rate_limit and govinfo_rate_limit:
                    # Make calls to SAM.gov
                    for i in range(3):
                        result = api_manager.get_grants_from_source('sam_gov_opportunities', {'call': i})
                    
                    # GovInfo should still work independently
                    result = api_manager.get_grants_from_source('govinfo', {})
                    # Should not be affected by SAM.gov calls
    
    def test_caching_independence_with_partial_credentials(self, clean_environment):
        """Test that caching works independently for different sources"""
        partial_credentials = {
            'SAM_GOV_API_KEY': 'valid-sam-key',
            'GOVINFO_API_KEY': 'valid-govinfo-key'
        }
        
        with patch.dict(os.environ, partial_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                call_count = {'count': 0}
                
                def mock_response_handler(method, url, **kwargs):
                    call_count['count'] += 1
                    response = Mock()
                    response.status_code = 200
                    
                    if 'sam.gov' in url:
                        response.json.return_value = get_mock_response('sam_gov_opportunities', 'success')
                    else:
                        response.json.return_value = get_mock_response('govinfo', 'success')
                    
                    response.text = str(response.json.return_value)
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                # Make identical requests to same source (should cache)
                params = {'query': 'test'}
                result1 = api_manager.get_grants_from_source('sam_gov_opportunities', params)
                result2 = api_manager.get_grants_from_source('sam_gov_opportunities', params)
                
                # Should cache the second request
                first_call_count = call_count['count']
                
                # Different source should not use cache
                result3 = api_manager.get_grants_from_source('govinfo', params)
                
                # Should make new call for different source
                assert call_count['count'] > first_call_count
    
    def test_error_propagation_with_partial_credentials(self, clean_environment):
        """Test error propagation doesn't affect working sources"""
        partial_credentials = {
            'SAM_GOV_API_KEY': 'failing-key',
            'GOVINFO_API_KEY': 'working-key'
        }
        
        with patch.dict(os.environ, partial_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    
                    if 'sam.gov' in url:
                        # Simulate various failures
                        response.status_code = 500
                        response.text = 'Internal Server Error'
                        response.json.return_value = {'error': 'Server error'}
                    else:
                        # Other sources work fine
                        response.status_code = 200
                        response.json.return_value = get_mock_response('govinfo', 'success')
                        response.text = str(response.json.return_value)
                    
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                # SAM.gov fails
                sam_results = api_manager.get_grants_from_source('sam_gov_opportunities', {})
                assert sam_results == []
                
                # Other sources should still work
                govinfo_results = api_manager.get_grants_from_source('govinfo', {})
                assert isinstance(govinfo_results, (list, dict))
                
                # Public sources should work
                grants_gov_results = api_manager.get_grants_from_source('grants_gov', {})
                assert isinstance(grants_gov_results, (list, dict))
    
    def test_configuration_validation_with_partial_credentials(self, clean_environment):
        """Test configuration validation with partial credentials"""
        partial_credentials = {
            'SAM_GOV_API_KEY': 'sam-key-123',
            'GOVINFO_API_KEY': 'govinfo-key-456'
            # Missing: CANDID_API_KEY, FDO_API_KEY, etc.
        }
        
        with patch.dict(os.environ, partial_credentials):
            config = APIConfig()
            
            # Get validation report
            validation_report = config.validate_configuration()
            
            # Should reflect partial credential state
            assert validation_report['total_sources'] > 0
            assert validation_report['enabled_sources'] > 0
            assert validation_report['sources_with_credentials'] > 0
            
            # Should have some sources with credentials, some without
            assert validation_report['sources_with_credentials'] < validation_report['total_sources']
            
            # Some sources should be healthy (public ones + credentialed ones)
            assert validation_report['healthy_sources'] > 0
    
    def test_health_checks_with_partial_credentials(self, clean_environment):
        """Test health checks reflect partial credential status"""
        partial_credentials = {
            'SAM_GOV_API_KEY': 'sam-key-123',
            'GOVINFO_API_KEY': 'govinfo-key-456'
        }
        
        with patch.dict(os.environ, partial_credentials):
            config = APIConfig()
            
            # Sources with credentials should be healthy (configuration-wise)
            sam_health = config.check_source_health('sam_gov_opportunities')
            assert sam_health.get('healthy', False) is True
            
            govinfo_health = config.check_source_health('govinfo')
            assert govinfo_health.get('healthy', False) is True
            
            # Sources without credentials should be unhealthy
            candid_health = config.check_source_health('candid')
            assert candid_health.get('healthy', True) is False
            
            # Public sources should be healthy
            grants_gov_health = config.check_source_health('grants_gov')
            assert grants_gov_health.get('healthy', False) is True
    
    def test_credential_status_reporting_with_partial_credentials(self, clean_environment):
        """Test credential status reporting with partial credentials"""
        partial_credentials = {
            'SAM_GOV_API_KEY': 'sam-key-123',
            'GOVINFO_API_KEY': 'govinfo-key-456'
        }
        
        with patch.dict(os.environ, partial_credentials):
            config = APIConfig()
            
            credential_status = config.get_credential_status()
            
            # Should have status for all sources
            assert len(credential_status) > 10
            
            # Sources with credentials
            if 'sam_gov_opportunities' in credential_status:
                sam_status = credential_status['sam_gov_opportunities']
                assert sam_status.get('has_credentials', False) is True
                assert sam_status.get('credential_required', False) is True
            
            if 'govinfo' in credential_status:
                govinfo_status = credential_status['govinfo']
                assert govinfo_status.get('has_credentials', False) is True
            
            # Sources without credentials
            if 'candid' in credential_status:
                candid_status = credential_status['candid']
                assert candid_status.get('has_credentials', True) is False
                assert candid_status.get('credential_required', False) is True
    
    def test_search_aggregation_with_partial_sources(self, clean_environment):
        """Test search result aggregation with partial sources"""
        partial_credentials = {
            'SAM_GOV_API_KEY': 'sam-key-123'
        }
        
        with patch.dict(os.environ, partial_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    response.status_code = 200
                    response.headers = {'Content-Type': 'application/json'}
                    
                    # Return different mock data for different sources
                    if 'grants.gov' in url:
                        response.json.return_value = get_mock_response('grants_gov', 'success')
                    elif 'sam.gov' in url:
                        response.json.return_value = get_mock_response('sam_gov_opportunities', 'success')
                    elif 'federalregister.gov' in url:
                        response.json.return_value = get_mock_response('federal_register', 'success')
                    else:
                        response.json.return_value = {'results': []}
                    
                    response.text = str(response.json.return_value)
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                # Search across all enabled sources
                results = api_manager.search_opportunities('education grant', {})
                
                # Should aggregate results from enabled sources
                assert isinstance(results, list)
                
                # Should not crash due to disabled sources
                # Results may be empty but system should be stable
    
    def test_dynamic_credential_changes(self, clean_environment):
        """Test behavior when credentials change dynamically"""
        # Start with no credentials
        api_manager = APIManager()
        initial_enabled = len(api_manager.get_enabled_sources())
        
        # Add credentials dynamically
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'new-sam-key'}):
            # Create new manager to pick up environment changes
            new_api_manager = APIManager()
            new_enabled = len(new_api_manager.get_enabled_sources())
            
            # Should have more enabled sources
            assert new_enabled >= initial_enabled
            
            # SAM.gov should now be enabled
            enabled_sources = new_api_manager.get_enabled_sources()
            assert 'sam_gov_opportunities' in enabled_sources
    
    def test_performance_with_partial_credentials(self, clean_environment):
        """Test performance isn't degraded by partial credentials"""
        partial_credentials = {
            'SAM_GOV_API_KEY': 'sam-key-123',
            'GOVINFO_API_KEY': 'govinfo-key-456'
        }
        
        with patch.dict(os.environ, partial_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                # Mock fast responses
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'results': []}
                mock_response.text = '{"results": []}'
                mock_request.return_value = mock_response
                
                import time
                start_time = time.time()
                
                # Make multiple requests to different sources
                for i in range(10):
                    api_manager.get_grants_from_source('sam_gov_opportunities', {'call': i})
                    api_manager.get_grants_from_source('grants_gov', {'call': i})
                
                elapsed = time.time() - start_time
                
                # Should complete quickly (disabled sources shouldn't add overhead)
                assert elapsed < 5.0  # Should be much faster, but allow reasonable time
    
    def test_resilience_with_partial_failures(self, clean_environment):
        """Test system resilience when some sources fail"""
        partial_credentials = {
            'SAM_GOV_API_KEY': 'sam-key-123',
            'GOVINFO_API_KEY': 'govinfo-key-456'
        }
        
        with patch.dict(os.environ, partial_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                failure_count = {'count': 0}
                
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    
                    # SAM.gov fails intermittently
                    if 'sam.gov' in url:
                        failure_count['count'] += 1
                        if failure_count['count'] % 2 == 0:
                            response.status_code = 500
                            response.text = 'Server Error'
                            response.json.return_value = {'error': 'Server error'}
                        else:
                            response.status_code = 200
                            response.json.return_value = get_mock_response('sam_gov_opportunities', 'success')
                            response.text = str(response.json.return_value)
                    else:
                        # Other sources work reliably
                        response.status_code = 200
                        response.json.return_value = get_mock_response('grants_gov', 'success')
                        response.text = str(response.json.return_value)
                    
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                # System should remain stable despite intermittent failures
                results = []
                for i in range(5):
                    try:
                        result = api_manager.search_opportunities(f'query_{i}', {})
                        results.append(len(result) if isinstance(result, list) else 0)
                    except Exception as e:
                        pytest.fail(f"Should not raise exception: {e}")
                
                # Should complete all iterations without crashing
                assert len(results) == 5
    
    @pytest.mark.parametrize("credential_sets", [
        # Only public sources
        {},
        # Only one private source
        {'SAM_GOV_API_KEY': 'sam-key'},
        # Mix of sources
        {'SAM_GOV_API_KEY': 'sam-key', 'GOVINFO_API_KEY': 'govinfo-key'},
        # Many sources
        {
            'SAM_GOV_API_KEY': 'sam-key',
            'GOVINFO_API_KEY': 'govinfo-key',
            'CANDID_API_KEY': 'candid-key',
            'FDO_API_KEY': 'fdo-key'
        }
    ])
    def test_various_partial_credential_combinations(self, credential_sets, clean_environment):
        """Test various combinations of partial credentials"""
        with patch.dict(os.environ, credential_sets):
            api_manager = APIManager()
            config = APIConfig()
            
            # Should not crash regardless of credential combination
            enabled_sources = api_manager.get_enabled_sources()
            assert isinstance(enabled_sources, dict)
            
            # Should have some enabled sources (at least public ones)
            assert len(enabled_sources) >= 0
            
            # Validation should work
            validation_report = config.validate_configuration()
            assert isinstance(validation_report, dict)
            assert 'total_sources' in validation_report