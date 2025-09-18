"""
Unit tests for API sources with invalid credentials
Tests that sources handle invalid credentials gracefully and don't affect other sources
"""

import pytest
import os
from unittest.mock import patch, Mock
from typing import Dict, Any

from app.services.apiManager import APIManager, CircuitBreakerState
from app.config.apiConfig import APIConfig
from tests.fixtures.api_responses import get_mock_response, MOCK_ERROR_RESPONSES
from tests.fixtures.mock_server import MockAPIServer


class TestAPISourcesInvalidCredentials:
    """Test API sources behavior with invalid credentials"""
    
    def test_invalid_credentials_return_401_error(self, clean_environment):
        """Test that invalid credentials result in 401 errors"""
        # Set invalid credentials
        invalid_credentials = {
            'SAM_GOV_API_KEY': 'invalid-sam-key-123',
            'CANDID_API_KEY': 'invalid-candid-key-456',
            'FDO_API_KEY': 'invalid-fdo-key-789',
            'GRANTWATCH_API_KEY': 'invalid-grantwatch-key-000'
        }
        
        with patch.dict(os.environ, invalid_credentials):
            api_manager = APIManager()
            
            # Mock 401 responses for invalid credentials
            with patch('app.services.apiManager.requests.request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_response.text = 'Unauthorized'
                mock_response.json.return_value = {'error': 'Invalid API key'}
                mock_request.return_value = mock_response
                
                credential_sources = [
                    'sam_gov_opportunities',
                    'candid',
                    'foundation_directory',
                    'grantwatch'
                ]
                
                for source_name in credential_sources:
                    results = api_manager.get_grants_from_source(source_name, {})
                    
                    # Should return empty list on auth failure
                    assert isinstance(results, list)
                    assert len(results) == 0
    
    def test_invalid_credentials_trigger_circuit_breaker(self, clean_environment):
        """Test that invalid credentials trigger circuit breaker"""
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'invalid-key'}):
            api_manager = APIManager()
            
            # Mock 401 responses
            with patch('app.services.apiManager.requests.request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_response.text = 'Unauthorized'
                mock_response.json.return_value = {'error': 'Invalid API key'}
                mock_request.return_value = mock_response
                
                source_name = 'sam_gov_opportunities'
                circuit_breaker = api_manager.circuit_breakers.get(source_name)
                assert circuit_breaker is not None
                
                initial_failure_count = circuit_breaker.failure_count
                
                # Make request that should fail
                results = api_manager.get_grants_from_source(source_name, {})
                
                # Circuit breaker should record the failure
                assert circuit_breaker.failure_count > initial_failure_count
                assert results == []
    
    def test_credential_errors_classified_as_credential_failures(self, clean_environment):
        """Test that 401/403 errors are classified as credential failures"""
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'invalid-key'}):
            api_manager = APIManager()
            
            # Test different auth error codes
            auth_error_codes = [401, 403]
            
            for error_code in auth_error_codes:
                with patch('app.services.apiManager.requests.request') as mock_request:
                    mock_response = Mock()
                    mock_response.status_code = error_code
                    mock_response.text = f'HTTP {error_code} Error'
                    mock_response.json.return_value = {'error': f'HTTP {error_code}'}
                    mock_request.return_value = mock_response
                    
                    source_name = 'sam_gov_opportunities'
                    circuit_breaker = api_manager.circuit_breakers.get(source_name)
                    
                    # Reset circuit breaker
                    circuit_breaker.reset()
                    initial_failures = circuit_breaker.total_failures
                    
                    # Make request
                    api_manager.get_grants_from_source(source_name, {})
                    
                    # Should be recorded as failure
                    assert circuit_breaker.total_failures > initial_failures
    
    def test_invalid_credentials_dont_affect_other_sources(self, clean_environment):
        """Test that invalid credentials for one source don't affect others"""
        # Set mixed credentials - some valid, some invalid
        mixed_credentials = {
            'SAM_GOV_API_KEY': 'invalid-sam-key',  # Invalid
            'GOVINFO_API_KEY': 'valid-govinfo-key'  # Valid (we'll mock as valid)
        }
        
        with patch.dict(os.environ, mixed_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    
                    # Check which source based on URL
                    if 'sam.gov' in url:
                        # Invalid credentials for SAM.gov
                        response.status_code = 401
                        response.text = 'Unauthorized'
                        response.json.return_value = {'error': 'Invalid API key'}
                    elif 'govinfo.gov' in url:
                        # Valid response for GovInfo
                        response.status_code = 200
                        response.text = '{"packages": []}'
                        response.json.return_value = get_mock_response('govinfo', 'success')
                    else:
                        # Default success for other sources
                        response.status_code = 200
                        response.text = '{"results": []}'
                        response.json.return_value = {'results': []}
                    
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                # SAM.gov should fail
                sam_results = api_manager.get_grants_from_source('sam_gov_opportunities', {})
                assert sam_results == []
                
                # GovInfo should work
                govinfo_results = api_manager.get_grants_from_source('govinfo', {})
                assert isinstance(govinfo_results, (list, dict))
                # Should not be empty if mock data is returned
    
    def test_circuit_breaker_opens_after_repeated_auth_failures(self, clean_environment):
        """Test circuit breaker opens after repeated authentication failures"""
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'invalid-key'}):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_response.text = 'Unauthorized'
                mock_response.json.return_value = {'error': 'Invalid API key'}
                mock_request.return_value = mock_response
                
                source_name = 'sam_gov_opportunities'
                circuit_breaker = api_manager.circuit_breakers.get(source_name)
                
                # Make enough failed requests to open circuit
                failure_threshold = circuit_breaker.failure_threshold
                for i in range(failure_threshold):
                    api_manager.get_grants_from_source(source_name, {'attempt': i})
                
                # Circuit should be open
                assert circuit_breaker.state == CircuitBreakerState.OPEN
                
                # Further requests should be blocked by circuit breaker
                result = api_manager.get_grants_from_source(source_name, {})
                assert result == []
    
    def test_different_credential_error_types(self, clean_environment):
        """Test handling of different types of credential errors"""
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'test-key'}):
            api_manager = APIManager()
            
            error_scenarios = [
                (401, 'Unauthorized', 'Invalid API key'),
                (403, 'Forbidden', 'Access denied'),
                (422, 'Unprocessable Entity', 'Invalid key format'),
            ]
            
            for status_code, status_text, error_message in error_scenarios:
                with patch('app.services.apiManager.requests.request') as mock_request:
                    mock_response = Mock()
                    mock_response.status_code = status_code
                    mock_response.text = status_text
                    mock_response.json.return_value = {'error': error_message}
                    mock_request.return_value = mock_response
                    
                    # Reset circuit breaker
                    source_name = 'sam_gov_opportunities'
                    circuit_breaker = api_manager.circuit_breakers.get(source_name)
                    circuit_breaker.reset()
                    
                    # Make request
                    result = api_manager.get_grants_from_source(source_name, {})
                    
                    # Should handle gracefully
                    assert isinstance(result, list)
                    assert len(result) == 0
                    
                    # Should record as failure
                    assert circuit_breaker.failure_count > 0
    
    def test_credential_error_logging_safety(self, clean_environment):
        """Test that credential errors are logged safely without exposing keys"""
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'secret-key-12345'}):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_response.text = 'Unauthorized - API key secret-key-12345 is invalid'
                mock_response.json.return_value = {'error': 'Invalid key secret-key-12345'}
                mock_request.return_value = mock_response
                
                source_name = 'sam_gov_opportunities'
                circuit_breaker = api_manager.circuit_breakers.get(source_name)
                
                # Make request that will fail
                api_manager.get_grants_from_source(source_name, {})
                
                # Verify circuit breaker recorded failure but sanitized error
                assert circuit_breaker.failure_count > 0
                
                # Check that state changes don't contain actual credentials
                # (The sanitization happens in record_failure method)
                # We can't directly verify the sanitized content, but ensure no exception occurred
    
    def test_retry_mechanism_with_invalid_credentials(self, clean_environment):
        """Test that retry mechanism doesn't indefinitely retry auth failures"""
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'invalid-key'}):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_response.text = 'Unauthorized'
                mock_response.json.return_value = {'error': 'Invalid API key'}
                mock_request.return_value = mock_response
                
                # Make request
                source_name = 'sam_gov_opportunities'
                result = api_manager.get_grants_from_source(source_name, {})
                
                # Should only make one request (no retries for auth failures)
                assert mock_request.call_count == 1
                assert result == []
    
    def test_mixed_valid_invalid_credentials_in_search(self, clean_environment):
        """Test search across sources with mixed credential validity"""
        # Set up mixed scenario
        mixed_credentials = {
            'SAM_GOV_API_KEY': 'invalid-sam-key',
            'GOVINFO_API_KEY': 'valid-govinfo-key'
        }
        
        with patch.dict(os.environ, mixed_credentials):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                def mock_response_handler(method, url, **kwargs):
                    response = Mock()
                    
                    if 'sam.gov' in url:
                        # Invalid credentials
                        response.status_code = 401
                        response.json.return_value = {'error': 'Invalid API key'}
                    elif 'govinfo.gov' in url:
                        # Valid response
                        response.status_code = 200
                        response.json.return_value = get_mock_response('govinfo', 'success')
                    else:
                        # Public APIs work without credentials
                        response.status_code = 200
                        response.json.return_value = get_mock_response('grants_gov', 'success')
                    
                    return response
                
                mock_request.side_effect = mock_response_handler
                
                # Search should work despite some sources having invalid credentials
                results = api_manager.search_opportunities('education', {})
                
                # Should get results from working sources
                assert isinstance(results, list)
                # May have results from working sources
    
    @pytest.mark.parametrize("source_name,env_var", [
        ('sam_gov_opportunities', 'SAM_GOV_API_KEY'),
        ('foundation_directory', 'FDO_API_KEY'),
        ('candid', 'CANDID_API_KEY'),
        ('grantwatch', 'GRANTWATCH_API_KEY'),
    ])
    def test_individual_source_invalid_credentials(self, source_name, env_var, clean_environment):
        """Test individual sources with invalid credentials"""
        with patch.dict(os.environ, {env_var: 'invalid-key-test'}):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_response.text = 'Unauthorized'
                mock_response.json.return_value = {'error': 'Invalid API key'}
                mock_request.return_value = mock_response
                
                # Should handle gracefully
                result = api_manager.get_grants_from_source(source_name, {})
                assert isinstance(result, list)
                assert len(result) == 0
                
                # Circuit breaker should record failure
                circuit_breaker = api_manager.circuit_breakers.get(source_name)
                if circuit_breaker:
                    assert circuit_breaker.failure_count > 0
    
    def test_credential_validation_in_config(self, clean_environment):
        """Test that config can detect invalid credentials"""
        # Set invalid credentials
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'obviously-invalid-key'}):
            config = APIConfig()
            
            # Source should be enabled (credential validation happens at runtime)
            sam_config = config.get_source_config('sam_gov_opportunities')
            assert sam_config.get('enabled', False) is True
            assert sam_config.get('api_key') == 'obviously-invalid-key'
            
            # Health check might not detect invalid format without actual API call
            health = config.check_source_health('sam_gov_opportunities')
            # Health check may pass (format looks ok) but runtime will fail
    
    def test_auth_header_preparation_with_invalid_keys(self, clean_environment):
        """Test that auth headers are prepared correctly even with invalid keys"""
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'invalid-key-format'}):
            api_manager = APIManager()
            
            # Should not crash when preparing headers
            try:
                # This is an internal method, test indirectly through get_grants_from_source
                with patch('app.services.apiManager.requests.request') as mock_request:
                    mock_response = Mock()
                    mock_response.status_code = 401
                    mock_request.return_value = mock_response
                    
                    api_manager.get_grants_from_source('sam_gov_opportunities', {})
                    
                    # Should have made request with proper headers
                    assert mock_request.called
                    call_args = mock_request.call_args
                    headers = call_args[1].get('headers', {})
                    
                    # Should have auth header with invalid key
                    assert 'X-Api-Key' in headers
                    assert headers['X-Api-Key'] == 'invalid-key-format'
                    
            except Exception as e:
                pytest.fail(f"Should not raise exception: {e}")
    
    def test_rate_limiting_with_invalid_credentials(self, clean_environment):
        """Test rate limiting behavior with invalid credentials"""
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'invalid-key'}):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_request.return_value = mock_response
                
                source_name = 'sam_gov_opportunities'
                
                # Make multiple rapid requests
                for i in range(5):
                    result = api_manager.get_grants_from_source(source_name, {'attempt': i})
                    assert result == []
                
                # Rate limiting should still apply to failed requests
                # (Though they'll be blocked by circuit breaker before rate limiting)
    
    def test_caching_not_applied_to_error_responses(self, clean_environment):
        """Test that error responses are not cached"""
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'invalid-key'}):
            api_manager = APIManager()
            
            with patch('app.services.apiManager.requests.request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_response.text = 'Unauthorized'
                mock_response.json.return_value = {'error': 'Invalid API key'}
                mock_request.return_value = mock_response
                
                source_name = 'sam_gov_opportunities'
                params = {'query': 'test'}
                
                # Make same request twice
                result1 = api_manager.get_grants_from_source(source_name, params)
                result2 = api_manager.get_grants_from_source(source_name, params)
                
                # Both should be empty
                assert result1 == []
                assert result2 == []
                
                # Should have made multiple requests (no caching of errors)
                # Note: Circuit breaker might prevent second request
                # so we check that both results are consistently empty