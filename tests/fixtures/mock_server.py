"""
Mock HTTP server utilities for API testing
"""

import json
import time
from unittest.mock import Mock, patch
from typing import Dict, Any, Optional, Callable
from urllib.parse import urlparse, parse_qs

from .api_responses import get_mock_response, SOURCE_MOCK_RESPONSES, MOCK_ERROR_RESPONSES

class MockAPIServer:
    """
    Mock HTTP server that simulates various API behaviors for testing
    """
    
    def __init__(self):
        self.call_count = {}
        self.rate_limits = {}
        self.failure_modes = {}
        self.response_delays = {}
        self.custom_responses = {}
        
    def reset(self):
        """Reset all counters and configurations"""
        self.call_count.clear()
        self.rate_limits.clear()
        self.failure_modes.clear()
        self.response_delays.clear()
        self.custom_responses.clear()
    
    def set_rate_limit(self, source: str, max_calls: int, period_seconds: int):
        """Configure rate limiting for a source"""
        self.rate_limits[source] = {
            'max_calls': max_calls,
            'period': period_seconds,
            'calls': [],
            'blocked_until': None
        }
    
    def set_failure_mode(self, source: str, failure_type: str, failure_rate: float = 1.0):
        """Configure failure behavior for a source"""
        self.failure_modes[source] = {
            'type': failure_type,
            'rate': failure_rate,
            'count': 0
        }
    
    def set_response_delay(self, source: str, delay_seconds: float):
        """Configure response delay for a source"""
        self.response_delays[source] = delay_seconds
    
    def set_custom_response(self, source: str, response_data: Dict[str, Any]):
        """Set custom response for a source"""
        self.custom_responses[source] = response_data
    
    def mock_request(self, method: str, url: str, **kwargs) -> Mock:
        """
        Mock HTTP request that simulates various API behaviors
        """
        # Extract source from URL
        source = self._identify_source_from_url(url)
        
        # Track call count
        self.call_count[source] = self.call_count.get(source, 0) + 1
        
        # Simulate response delay if configured
        if source in self.response_delays:
            time.sleep(self.response_delays[source])
        
        # Check rate limiting
        if self._is_rate_limited(source):
            return self._create_mock_response(429, MOCK_ERROR_RESPONSES["429_rate_limit"])
        
        # Check failure modes
        if self._should_fail(source):
            failure_config = self.failure_modes[source]
            return self._create_mock_response(
                MOCK_ERROR_RESPONSES[failure_config['type']]['status_code'],
                MOCK_ERROR_RESPONSES[failure_config['type']]
            )
        
        # Check for custom response
        if source in self.custom_responses:
            return self._create_mock_response(200, {
                'content': self.custom_responses[source],
                'headers': {'Content-Type': 'application/json'}
            })
        
        # Check authentication
        auth_result = self._check_authentication(source, kwargs)
        if auth_result:
            return auth_result
        
        # Return success response
        response_data = get_mock_response(source, "success")
        return self._create_mock_response(200, {
            'content': response_data,
            'headers': {'Content-Type': 'application/json'}
        })
    
    def _identify_source_from_url(self, url: str) -> str:
        """Identify API source from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        source_mappings = {
            'grants.gov': 'grants_gov',
            'federalregister.gov': 'federal_register',
            'api.sam.gov': 'sam_gov_opportunities',
            'api.govinfo.gov': 'govinfo',
            'api.foundationdirectory.org': 'foundation_directory',
            'api.candid.org': 'candid',
            'grantwatch.com': 'grantwatch',
            'data.michigan.gov': 'michigan_socrata',
            'api.zyte.com': 'zyte_api'
        }
        
        for domain_key, source_name in source_mappings.items():
            if domain_key in domain:
                return source_name
        
        return 'unknown'
    
    def _is_rate_limited(self, source: str) -> bool:
        """Check if source is rate limited"""
        if source not in self.rate_limits:
            return False
        
        config = self.rate_limits[source]
        now = time.time()
        
        # Clean old calls
        config['calls'] = [call_time for call_time in config['calls'] 
                          if now - call_time < config['period']]
        
        # Check if blocked
        if config.get('blocked_until') and now < config['blocked_until']:
            return True
        
        # Check rate limit
        if len(config['calls']) >= config['max_calls']:
            config['blocked_until'] = now + config['period']
            return True
        
        config['calls'].append(now)
        return False
    
    def _should_fail(self, source: str) -> bool:
        """Check if request should fail based on failure mode"""
        if source not in self.failure_modes:
            return False
        
        config = self.failure_modes[source]
        config['count'] += 1
        
        # Simple probability-based failure
        import random
        return random.random() < config['rate']
    
    def _check_authentication(self, source: str, request_kwargs: Dict[str, Any]) -> Optional[Mock]:
        """Check authentication for the request"""
        headers = request_kwargs.get('headers', {})
        
        # Check for missing required auth
        auth_required_sources = [
            'sam_gov_opportunities', 'sam_gov_entity', 'foundation_directory',
            'grantwatch', 'candid', 'zyte_api'
        ]
        
        if source in auth_required_sources:
            auth_header_map = {
                'sam_gov_opportunities': 'X-Api-Key',
                'sam_gov_entity': 'X-Api-Key',
                'foundation_directory': 'Authorization',
                'candid': 'Authorization',
                'grantwatch': 'Authorization',
                'zyte_api': 'Authorization',
                'michigan_socrata': 'X-App-Token'
            }
            
            required_header = auth_header_map.get(source)
            if required_header and required_header not in headers:
                return self._create_mock_response(401, MOCK_ERROR_RESPONSES["401_unauthorized"])
            
            # Check for invalid auth tokens
            auth_value = headers.get(required_header, '')
            if auth_value and auth_value.startswith('invalid'):
                return self._create_mock_response(401, MOCK_ERROR_RESPONSES["401_unauthorized"])
        
        return None
    
    def _create_mock_response(self, status_code: int, config: Dict[str, Any]) -> Mock:
        """Create a mock response object"""
        response = Mock()
        response.status_code = status_code
        response.headers = config.get('headers', {})
        
        content = config.get('content', {})
        if isinstance(content, dict):
            response.text = json.dumps(content)
            response.json.return_value = content
        else:
            response.text = str(content)
            response.json.side_effect = json.JSONDecodeError("No JSON", "", 0)
        
        return response
    
    def get_call_count(self, source: str) -> int:
        """Get number of calls made to a source"""
        return self.call_count.get(source, 0)
    
    def get_total_calls(self) -> int:
        """Get total number of calls across all sources"""
        return sum(self.call_count.values())

class CircuitBreakerTestHelper:
    """Helper for testing circuit breaker functionality"""
    
    @staticmethod
    def trigger_failures(api_manager, source: str, failure_count: int, error_type: str = "500_server_error"):
        """Trigger a specific number of failures for a source"""
        with patch('app.services.apiManager.requests.request') as mock_request:
            error_config = MOCK_ERROR_RESPONSES[error_type]
            mock_response = Mock()
            mock_response.status_code = error_config['status_code']
            mock_response.text = json.dumps(error_config['content'])
            mock_response.json.return_value = error_config['content']
            mock_request.return_value = mock_response
            
            for _ in range(failure_count):
                api_manager.get_grants_from_source(source, {})
    
    @staticmethod
    def verify_circuit_state(api_manager, source: str, expected_state: str):
        """Verify circuit breaker is in expected state"""
        circuit_breaker = api_manager.circuit_breakers.get(source)
        assert circuit_breaker is not None, f"Circuit breaker not found for {source}"
        assert circuit_breaker.state.value == expected_state, \
            f"Expected {expected_state}, got {circuit_breaker.state.value}"
    
    @staticmethod
    def get_circuit_status(api_manager, source: str) -> Dict[str, Any]:
        """Get circuit breaker status for a source"""
        circuit_breaker = api_manager.circuit_breakers.get(source)
        return circuit_breaker.get_status() if circuit_breaker else {}

class RateLimitTestHelper:
    """Helper for testing rate limiting functionality"""
    
    @staticmethod
    def exhaust_rate_limit(api_manager, source: str, max_calls: int):
        """Make enough calls to exhaust rate limit"""
        with patch('app.services.apiManager.requests.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = get_mock_response(source, "success")
            mock_request.return_value = mock_response
            
            results = []
            for i in range(max_calls + 2):  # Exceed limit by 2
                result = api_manager.get_grants_from_source(source, {'call': i})
                results.append(len(result))
            
            return results
    
    @staticmethod
    def verify_rate_limit_headers(response_headers: Dict[str, str]):
        """Verify rate limit headers are present"""
        expected_headers = ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset']
        for header in expected_headers:
            assert header in response_headers, f"Missing rate limit header: {header}"

class CacheTestHelper:
    """Helper for testing cache functionality"""
    
    @staticmethod
    def verify_cache_hit(api_manager, source: str, params: Dict[str, Any]):
        """Verify that subsequent identical requests hit cache"""
        with patch('app.services.apiManager.requests.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = get_mock_response(source, "success")
            mock_request.return_value = mock_response
            
            # First call should hit the API
            api_manager.get_grants_from_source(source, params)
            first_call_count = mock_request.call_count
            
            # Second call should hit cache
            api_manager.get_grants_from_source(source, params)
            second_call_count = mock_request.call_count
            
            # Should be same call count (cached)
            assert first_call_count == second_call_count, "Cache miss when hit expected"
    
    @staticmethod
    def verify_cache_miss(api_manager, source: str, params1: Dict[str, Any], params2: Dict[str, Any]):
        """Verify that different requests don't hit cache"""
        with patch('app.services.apiManager.requests.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = get_mock_response(source, "success")
            mock_request.return_value = mock_response
            
            # First call
            api_manager.get_grants_from_source(source, params1)
            first_call_count = mock_request.call_count
            
            # Second call with different params
            api_manager.get_grants_from_source(source, params2)
            second_call_count = mock_request.call_count
            
            # Should be different call counts (cache miss)
            assert second_call_count > first_call_count, "Cache hit when miss expected"