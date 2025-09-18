"""
Unified API & Data Integration Manager
Handles all external API calls and data source integrations
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
import time
import hashlib
from flask import current_app
from app.config.apiConfig import APIConfig, API_SOURCES
from app.services.mode import is_live
import base64
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failed - blocking calls
    HALF_OPEN = "half_open" # Testing if service recovered

class CircuitBreaker:
    """
    Robust Circuit Breaker implementation for API source resilience
    
    Features:
    - Configurable failure threshold and cooldown periods
    - Automatic recovery testing
    - Credential-safe error logging
    - Graceful degradation
    """
    
    def __init__(self, source_name: str, failure_threshold: int = 5, 
                 cooldown_minutes: int = 15, half_open_max_calls: int = 3):
        """
        Initialize circuit breaker for a source
        
        Args:
            source_name: Name of the API source
            failure_threshold: Number of failures before opening circuit
            cooldown_minutes: Minutes to wait before attempting recovery
            half_open_max_calls: Max calls to allow in half-open state for testing
        """
        self.source_name = source_name
        self.failure_threshold = failure_threshold
        self.cooldown_period = timedelta(minutes=cooldown_minutes)
        self.half_open_max_calls = half_open_max_calls
        
        # State tracking
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        
        # Statistics
        self.total_calls = 0
        self.total_failures = 0
        self.state_changes = []
        
        logger.info(f"Circuit breaker initialized for {source_name} - "
                   f"threshold: {failure_threshold}, cooldown: {cooldown_minutes}min")
    
    def can_execute(self) -> bool:
        """Check if calls to the source are allowed"""
        now = datetime.now()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if cooldown period has passed
            if (self.last_failure_time and 
                now - self.last_failure_time >= self.cooldown_period):
                self._transition_to_half_open()
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Allow limited calls for testing recovery
            return self.half_open_calls < self.half_open_max_calls
        
        return False
    
    def record_success(self):
        """Record a successful call"""
        self.total_calls += 1
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
            # If we've made enough successful test calls, close the circuit
            if self.half_open_calls >= self.half_open_max_calls:
                self._transition_to_closed()
                logger.info(f"Circuit breaker for {self.source_name} recovered - "
                           f"closing circuit after {self.half_open_calls} successful test calls")
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self, error: str, is_credential_error: bool = False):
        """Record a failed call"""
        self.total_calls += 1
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        # Log error safely without exposing credentials
        safe_error = self._sanitize_error(error)
        error_type = "credential" if is_credential_error else "general"
        
        logger.warning(f"Circuit breaker for {self.source_name} recorded {error_type} failure "
                      f"({self.failure_count}/{self.failure_threshold}): {safe_error}")
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            # Any failure in half-open state opens circuit immediately
            self._transition_to_open()
            logger.warning(f"Circuit breaker for {self.source_name} failed recovery test - opening circuit")
        elif self.state == CircuitBreakerState.CLOSED:
            # Check if we've hit failure threshold
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()
                logger.error(f"Circuit breaker for {self.source_name} opened due to "
                           f"{self.failure_count} consecutive failures")
    
    def _transition_to_open(self):
        """Transition to open state"""
        old_state = self.state
        self.state = CircuitBreakerState.OPEN
        self.half_open_calls = 0
        self._record_state_change(old_state, self.state)
    
    def _transition_to_half_open(self):
        """Transition to half-open state"""
        old_state = self.state
        self.state = CircuitBreakerState.HALF_OPEN
        self.half_open_calls = 0
        self._record_state_change(old_state, self.state)
        logger.info(f"Circuit breaker for {self.source_name} entering half-open state for recovery test")
    
    def _transition_to_closed(self):
        """Transition to closed state"""
        old_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.half_open_calls = 0
        self._record_state_change(old_state, self.state)
    
    def _record_state_change(self, from_state: CircuitBreakerState, to_state: CircuitBreakerState):
        """Record state change for monitoring"""
        change = {
            'timestamp': datetime.now().isoformat(),
            'from_state': from_state.value,
            'to_state': to_state.value,
            'failure_count': self.failure_count
        }
        self.state_changes.append(change)
        
        # Keep only last 10 state changes
        if len(self.state_changes) > 10:
            self.state_changes = self.state_changes[-10:]
    
    def _sanitize_error(self, error: str) -> str:
        """Remove potential credentials from error messages"""
        import re
        
        sanitized = str(error)
        
        # Remove API keys (various formats)
        sanitized = re.sub(r'[aA][pP][iI][-_]?[kK][eE][yY][-_:=\s]+[A-Za-z0-9+/]{16,}', 
                          'API_KEY=[REDACTED]', sanitized)
        
        # Remove bearer tokens
        sanitized = re.sub(r'[bB]earer\s+[A-Za-z0-9+/._-]{16,}', 
                          'Bearer [REDACTED]', sanitized)
        
        # Remove basic auth
        sanitized = re.sub(r'[bB]asic\s+[A-Za-z0-9+/=]{16,}', 
                          'Basic [REDACTED]', sanitized)
        
        # Remove URLs with embedded credentials
        sanitized = re.sub(r'https?://[^:]+:[^@]+@', 
                          'https://[USER]:[PASS]@', sanitized)
        
        # Remove access tokens
        sanitized = re.sub(r'access[-_]?token[-_:=\s]+[A-Za-z0-9+/._-]{16,}', 
                          'access_token=[REDACTED]', sanitized)
        
        return sanitized
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            'source': self.source_name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'total_calls': self.total_calls,
            'total_failures': self.total_failures,
            'success_rate': (self.total_calls - self.total_failures) / max(self.total_calls, 1) * 100,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'cooldown_period_minutes': self.cooldown_period.total_seconds() / 60,
            'is_available': self.can_execute(),
            'state_changes': self.state_changes[-5:] if self.state_changes else []  # Last 5 changes
        }
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        old_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.half_open_calls = 0
        self._record_state_change(old_state, self.state)
        logger.info(f"Circuit breaker for {self.source_name} manually reset to closed state")

class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self):
        self.calls = {}
    
    def check_rate_limit(self, source_name: str, max_calls: int, period_seconds: int) -> bool:
        """Check if we can make another API call"""
        now = time.time()
        if source_name not in self.calls:
            self.calls[source_name] = []
        
        # Clean old calls
        self.calls[source_name] = [
            call_time for call_time in self.calls[source_name] 
            if now - call_time < period_seconds
        ]
        
        if len(self.calls[source_name]) >= max_calls:
            return False
        
        self.calls[source_name].append(now)
        return True

class CacheManager:
    """Simple cache manager for API responses"""
    def __init__(self):
        self.cache = {}
    
    def get_cache_key(self, source: str, params: dict) -> str:
        """Generate cache key from source and params"""
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(f"{source}:{param_str}".encode()).hexdigest()
    
    def get(self, source: str, params: dict, max_age_minutes: int = 60) -> Optional[Any]:
        """Get cached data if available and not expired"""
        key = self.get_cache_key(source, params)
        if key in self.cache:
            cached_data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(minutes=max_age_minutes):
                logger.info(f"Cache hit for {source}")
                return cached_data
        return None
    
    def set(self, source: str, params: dict, data: Any):
        """Cache data with timestamp"""
        key = self.get_cache_key(source, params)
        self.cache[key] = (data, datetime.now())
        logger.info(f"Cached data for {source}")

class APIManager:
    """Enhanced Central API Manager for all grant data sources"""
    
    def __init__(self):
        self.config = APIConfig()
        self.rate_limiter = RateLimiter()
        self.cache = CacheManager()
        self.circuit_breakers = {}  # Circuit breakers for each source
        self.sources = self._initialize_sources()
        self._initialize_circuit_breakers()
        logger.info(f"Initialized APIManager with {len(self.sources)} enabled sources and circuit breakers")
    
    def _initialize_sources(self) -> Dict:
        """Initialize all API sources from enhanced config"""
        sources = {}
        enabled_sources = self.config.get_enabled_sources()
        for source_id, source_config in enabled_sources.items():
            sources[source_id] = source_config
            auth_status = "with credentials" if source_config.get('api_key') else "public"
            logger.info(f"Initialized source: {source_id} ({auth_status})")
        return sources
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for all sources"""
        for source_id in self.sources:
            # Configure circuit breaker parameters based on source type
            source_config = self.sources[source_id]
            
            # Use more strict settings for credential-required sources
            if source_config.get('credential_required', False):
                failure_threshold = 3  # Fail faster for auth issues
                cooldown_minutes = 30  # Longer cooldown for credential issues
            else:
                failure_threshold = 5  # More tolerant for public APIs
                cooldown_minutes = 15  # Shorter cooldown for general issues
            
            self.circuit_breakers[source_id] = CircuitBreaker(
                source_name=source_id,
                failure_threshold=failure_threshold,
                cooldown_minutes=cooldown_minutes,
                half_open_max_calls=2  # Conservative recovery testing
            )
            
        logger.info(f"Initialized circuit breakers for {len(self.circuit_breakers)} sources")
    
    def get_grants_from_source(self, source_name: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Fetch grants from a specific source with circuit breaker protection
        Returns list of standardized grant objects
        """
        params = params or {}
        
        # Check if source is enabled
        if source_name not in self.sources:
            logger.warning(f"Source {source_name} not found or disabled")
            return []
        
        # Check circuit breaker - don't proceed if circuit is open
        circuit_breaker = self.circuit_breakers.get(source_name)
        if circuit_breaker and not circuit_breaker.can_execute():
            logger.info(f"Circuit breaker for {source_name} is {circuit_breaker.state.value} - skipping call")
            return []
        
        # Check cache first
        cached_data = self.cache.get(source_name, params)
        if cached_data:
            return cached_data
        
        # Check rate limit
        source_config = self.sources[source_name]
        rate_limit = source_config.get('rate_limit', {'calls': 10, 'period': 60})
        if not self.rate_limiter.check_rate_limit(
            source_name, 
            rate_limit['calls'], 
            rate_limit['period']
        ):
            logger.warning(f"Rate limit exceeded for {source_name}")
            return []  # Return empty when rate limited
        
        # Route to appropriate fetcher with enhanced circuit breaker error handling
        try:
            grants = self._dispatch_to_fetcher(source_name, params)
            
            # Record success in circuit breaker
            if circuit_breaker:
                circuit_breaker.record_success()
            
            if not grants:
                logger.info(f"No data returned from {source_name}")
            else:
                # Cache successful response
                self.cache.set(source_name, params, grants)
            
            return grants
            
        except Exception as e:
            # Record failure in circuit breaker with error classification
            is_credential_error = self._is_credential_error(e)
            is_rate_limit_error = self._is_rate_limit_error(e)
            
            if circuit_breaker:
                circuit_breaker.record_failure(str(e), is_credential_error)
            
            # Log errors based on type and mode
            if is_credential_error:
                logger.warning(f"Authentication failed for {source_name} - circuit breaker updated")
            elif is_rate_limit_error:
                logger.warning(f"Rate limit exceeded for {source_name}")
            else:
                if is_live():
                    logger.error(f"LIVE MODE: Error fetching from {source_name} - circuit breaker updated")
                    logger.error(f"GUIDANCE: {source_name} API is unavailable. Check credentials and API status.")
                else:
                    logger.warning(f"DEMO MODE: Error simulated for {source_name}")
                    
            return []  # Return empty on error, never fake data
    
    def get_enabled_sources(self) -> Dict[str, Dict]:
        """Get all enabled sources with their configurations"""
        return self.sources
    
    def search_grants(self, source_name: str, params: Optional[Dict] = None) -> List[Dict]:
        """Search grants from a specific source - alias for get_grants_from_source"""
        return self.get_grants_from_source(source_name, params)
    
    def _get_current_timestamp(self) -> str:
        """Get current ISO timestamp"""
        return datetime.now().isoformat()
    
    def search_opportunities(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Search for grant opportunities across all enabled sources
        """
        filters = filters or {}
        all_grants = []
        
        # Search each enabled source
        for source_name in self.sources:
            params = {
                'query': query,
                **filters
            }
            grants = self.get_grants_from_source(source_name, params)
            all_grants.extend(grants)
        
        # Deduplicate and sort by relevance
        seen = set()
        unique_grants = []
        for grant in all_grants:
            grant_id = f"{grant.get('title', '')}:{grant.get('funder', '')}"
            if grant_id not in seen:
                seen.add(grant_id)
                unique_grants.append(grant)
        
        return unique_grants
    
    def fetch_grant_details(self, grant_id: str, source: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch detailed information about a specific grant
        """
        if source and source in self.sources:
            params = {'grant_id': grant_id}
            grants = self.get_grants_from_source(source, params)
            if grants:
                return grants[0]
        
        # Try all sources if source not specified
        for source_name in self.sources:
            params = {'grant_id': grant_id}
            grants = self.get_grants_from_source(source_name, params)
            if grants:
                return grants[0]
        
        return None
    
    def get_watchlist_updates(self, watchlist_id: str, last_check: Optional[datetime] = None) -> List[Dict]:
        """
        Get new grant opportunities for a watchlist since last check
        """
        # This would integrate with the existing watchlist system
        # For now, return recent grants
        all_grants = []
        for source_name in self.sources:
            params = {
                'since': last_check.isoformat() if last_check else None,
                'watchlist_id': watchlist_id
            }
            grants = self.get_grants_from_source(source_name, params)
            all_grants.extend(grants)
        
        return all_grants
    
    def _dispatch_to_fetcher(self, source_name: str, params: Dict) -> List[Dict]:
        """Dispatch to appropriate fetcher method based on source name"""
        # Existing sources
        if source_name == 'grants_gov':
            return self._fetch_grants_gov(params)
        elif source_name == 'federal_register':
            return self._fetch_federal_register(params)
        elif source_name == 'govinfo':
            return self._fetch_govinfo(params)
        elif source_name == 'philanthropy_news':
            return self._fetch_philanthropy_news(params)
        elif source_name == 'foundation_directory':
            return self._fetch_foundation_directory(params)
        elif source_name == 'grantwatch':
            return self._fetch_grantwatch(params)
        elif source_name == 'michigan_portal':
            return self._fetch_michigan_portal(params)
        elif source_name == 'georgia_portal':
            return self._fetch_georgia_portal(params)
        # New API sources
        elif source_name == 'sam_gov_opportunities':
            return self._fetch_sam_gov_opportunities(params)
        elif source_name == 'sam_gov_entity':
            return self._fetch_sam_gov_entity(params)
        elif source_name == 'michigan_socrata':
            return self._fetch_michigan_socrata(params)
        elif source_name == 'zyte_api':
            return self._fetch_zyte_api(params)
        elif source_name == 'hhs_grants':
            return self._fetch_hhs_grants(params)
        elif source_name == 'ed_grants':
            return self._fetch_ed_grants(params)
        elif source_name == 'nsf_grants':
            return self._fetch_nsf_grants(params)
        else:
            logger.warning(f"Unknown source: {source_name}")
            return []  # No data for unknown sources
    
    def _is_credential_error(self, error: Exception) -> bool:
        """Check if error is related to credentials/authentication"""
        error_str = str(error).lower()
        error_indicators = [
            "401", "403", "unauthorized", "forbidden", "invalid_grant",
            "access_denied", "invalid_token", "authentication failed",
            "invalid_client", "invalid credentials", "api key"
        ]
        return any(indicator in error_str for indicator in error_indicators)
    
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is related to rate limiting"""
        error_str = str(error).lower()
        rate_limit_indicators = [
            "429", "rate limit", "too many requests", "quota exceeded",
            "throttled", "rate exceeded"
        ]
        return any(indicator in error_str for indicator in rate_limit_indicators)
    
    def get_circuit_breaker_status(self, source_name: Optional[str] = None) -> Dict[str, Any]:
        """Get circuit breaker status for one or all sources"""
        if source_name:
            circuit_breaker = self.circuit_breakers.get(source_name)
            if circuit_breaker:
                return circuit_breaker.get_status()
            return {'error': f'No circuit breaker found for source: {source_name}'}
        
        # Return status for all sources
        return {
            source_name: breaker.get_status() 
            for source_name, breaker in self.circuit_breakers.items()
        }
    
    def reset_circuit_breaker(self, source_name: str) -> bool:
        """Manually reset a circuit breaker"""
        circuit_breaker = self.circuit_breakers.get(source_name)
        if circuit_breaker:
            circuit_breaker.reset()
            logger.info(f"Circuit breaker for {source_name} manually reset")
            return True
        logger.warning(f"No circuit breaker found for source: {source_name}")
        return False
    
    def get_circuit_breaker_summary(self) -> Dict[str, Any]:
        """Get summary of all circuit breaker states"""
        summary = {
            'total_sources': len(self.circuit_breakers),
            'open_circuits': 0,
            'half_open_circuits': 0,
            'closed_circuits': 0,
            'sources_by_state': {
                'open': [],
                'half_open': [],
                'closed': []
            },
            'total_failures': 0,
            'total_calls': 0
        }
        
        for source_name, breaker in self.circuit_breakers.items():
            status = breaker.get_status()
            state = status['state']
            
            if state == 'open':
                summary['open_circuits'] += 1
                summary['sources_by_state']['open'].append(source_name)
            elif state == 'half_open':
                summary['half_open_circuits'] += 1
                summary['sources_by_state']['half_open'].append(source_name)
            else:
                summary['closed_circuits'] += 1
                summary['sources_by_state']['closed'].append(source_name)
            
            summary['total_failures'] += status['total_failures']
            summary['total_calls'] += status['total_calls']
        
        if summary['total_calls'] > 0:
            summary['overall_success_rate'] = (
                (summary['total_calls'] - summary['total_failures']) / 
                summary['total_calls'] * 100
            )
        else:
            summary['overall_success_rate'] = 100.0
        
        return summary
    
    def _prepare_authenticated_request(self, source_name: str, url: str, method: str = 'GET', 
                                     data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """Prepare an authenticated request based on source configuration"""
        source_config = self.sources.get(source_name, {})
        
        headers = {
            'User-Agent': 'PinkLemonade/1.0 Grant Discovery Platform',
            'Accept': 'application/json',
            'Content-Type': 'application/json' if data else None
        }
        
        # Remove None values
        headers = {k: v for k, v in headers.items() if v is not None}
        
        # Add authentication based on auth_type
        auth_type = source_config.get('auth_type')
        api_key = source_config.get('api_key')
        
        if auth_type == 'api_key' and api_key:
            auth_header = source_config.get('auth_header', 'X-Api-Key')
            headers[auth_header] = api_key
        elif auth_type == 'basic_auth' and api_key:
            # For basic auth, api_key should be in format "username:password"
            encoded_credentials = base64.b64encode(api_key.encode()).decode()
            headers['Authorization'] = f'Basic {encoded_credentials}'
        elif auth_type == 'bearer' and api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        elif auth_type == 'app_token' and api_key:
            auth_header = source_config.get('auth_header', 'X-App-Token')
            headers[auth_header] = api_key
        
        return {
            'url': url,
            'method': method,
            'headers': headers,
            'json': data if data else None,
            'params': params,
            'timeout': 30
        }
    
    def _make_request_with_retry(self, source_name: str, request_config: Dict) -> requests.Response:
        """Make HTTP request with retry logic based on source configuration"""
        source_config = self.sources.get(source_name, {})
        error_config = source_config.get('error_handling', {})
        
        max_retries = error_config.get('max_retries', 1)
        backoff_factor = error_config.get('backoff_factor', 1)
        retry_codes = error_config.get('retry_codes', [429, 502, 503, 504])
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.request(**request_config)
                
                # If successful or non-retryable error, return
                if response.status_code == 200 or response.status_code not in retry_codes:
                    return response
                
                # If this was the last attempt, return the response anyway
                if attempt == max_retries:
                    return response
                
                # Wait before retrying
                wait_time = backoff_factor * (2 ** attempt)
                logger.info(f"Retrying {source_name} in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries:
                    raise e
                wait_time = backoff_factor * (2 ** attempt)
                logger.info(f"Request failed, retrying {source_name} in {wait_time}s: {e}")
                time.sleep(wait_time)
        
        # This shouldn't be reached, but just in case
        raise Exception(f"Max retries exceeded for {source_name}")
    
    def _standardize_grant(self, raw_data: Dict, source_name: str = 'default') -> Dict:
        """Standardize grant data using field mappings"""
        field_mapping = self.config.get_field_mapping(source_name)
        
        standardized = {
            'title': self._safe_get(raw_data, field_mapping.get('title', 'title')),
            'funder': self._safe_get(raw_data, field_mapping.get('funder', 'funder')),
            'amount_min': self._safe_get(raw_data, field_mapping.get('amount_min', 'amount_min')),
            'amount_max': self._safe_get(raw_data, field_mapping.get('amount_max', 'amount_max')),
            'deadline': self._safe_get(raw_data, field_mapping.get('deadline', 'deadline')),
            'description': self._safe_get(raw_data, field_mapping.get('description', 'description')),
            'eligibility': self._safe_get(raw_data, field_mapping.get('eligibility', 'eligibility')),
            'source': source_name,
            'source_data': raw_data,  # Keep original for debugging
            'last_updated': datetime.now().isoformat()
        }
        
        # Clean up None values
        return {k: v for k, v in standardized.items() if v is not None}
    
    def _safe_get(self, data: Dict, key: str) -> Any:
        """Safely get value from nested dictionary using dot notation"""
        if not key or not isinstance(data, dict):
            return None
        
        keys = key.split('.')
        value = data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def get_source_health_status(self) -> Dict[str, Dict]:
        """Get health status for all configured sources"""
        health_status = {}
        for source_id in self.config.sources.keys():
            health_status[source_id] = self.config.check_source_health(source_id)
        return health_status
    
    def get_credential_status_report(self) -> Dict[str, Any]:
        """Get comprehensive credential status report"""
        return {
            'credential_status': self.config.get_credential_status(),
            'validation_report': self.config.validate_configuration(),
            'health_status': self.get_source_health_status()
        }
    
        """
        Fetch grants from Grants.gov API
        Uses the v2 search API which is publicly available
        """
        try:
            # Using the correct endpoint
            search_url = "https://www.grants.gov/search/"
            
            # Build POST payload for v2 API
            payload = {
                "startRecordNum": 0,
                "keyword": params.get('query', 'nonprofit'),
                "oppStatuses": "forecasted|posted",  # Open opportunities
                "sortBy": "openDate|desc",
                "rows": params.get('limit', 25)
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "PinkLemonade/1.0"
            }
            
            # Make POST request to search endpoint
            response = requests.post(
                search_url,
                json=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                grants = []
                
                for opp in data.get('opportunities', []):
                    grant = self._standardize_grant({
                        'title': opp.get('title'),
                        'funder': opp.get('agency'),
                        'amount_min': opp.get('awardFloor'),
                        'amount_max': opp.get('awardCeiling'),
                        'deadline': opp.get('closeDate'),
                        'description': opp.get('description'),
                        'link': f"https://grants.gov/search-results-detail/{opp.get('id')}",
                        'source': 'Grants.gov',
                        'source_id': opp.get('id')
                    })
                    grants.append(grant)
                
                return grants
                
        except Exception as e:
            logger.error(f"Error fetching from Grants.gov: {e}")
        
        return []
    
    def _fetch_philanthropy_news(self, params: Dict) -> List[Dict]:
        """
        Fetch grants from Philanthropy News Digest RSS
        """
        try:
            # Note: feedparser dependency not available - using alternative approach
            base_url = self.sources['philanthropy_news']['base_url']
            
            # Simple RSS parsing without feedparser
            response = requests.get(base_url, timeout=10)
            if response.status_code == 200:
                # Basic RSS parsing - extract title and link from XML
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                grants = []
                items = root.findall('.//item')[:params.get('limit', 25)]
                
                for item in items:
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    pub_date = item.find('pubDate')
                    
                    grant = self._standardize_grant({
                        'title': title.text if title is not None else 'Grant Opportunity',
                        'description': description.text if description is not None else '',
                        'link': link.text if link is not None else '',
                        'deadline': pub_date.text if pub_date is not None else '',
                        'source': 'Philanthropy News Digest'
                    })
                    grants.append(grant)
                
                return grants
            else:
                logger.warning(f"Failed to fetch RSS feed: {response.status_code}")
                return []
            
        except Exception as e:
            logger.error(f"Error fetching from Philanthropy News: {e}")
        
        return []
    
    def _fetch_foundation_directory(self, params: Dict) -> List[Dict]:
        """
        Fetch from Foundation Directory Online (placeholder for paid API)
        """
        # This requires API credentials
        logger.warning("Foundation Directory API requires paid subscription")
        return []  # No data without API key
    
    def _fetch_grantwatch(self, params: Dict) -> List[Dict]:
        """
        Fetch from GrantWatch free listings
        """
        # GrantWatch requires subscription for API
        logger.warning("GrantWatch API requires paid subscription")
        return []  # No data without API key
    
    def _fetch_michigan_portal(self, params: Dict) -> List[Dict]:
        """
        Fetch from Michigan state portal
        """
        # Implementation would depend on available Michigan open data APIs
        logger.info("Michigan portal: No public API available yet")
        return []  # No data source configured
    
    def _fetch_georgia_portal(self, params: Dict) -> List[Dict]:
        """
        Fetch from Georgia state portal
        """
        # Implementation would depend on available Georgia open data APIs
        logger.info("Georgia portal: No public API available yet")
        return []  # No data source configured
    
    def _fetch_federal_register(self, params: Dict) -> List[Dict]:
        """
        Fetch REAL grant notices from Federal Register API
        This API is confirmed working and returns actual government grant notices
        """
        try:
            # Using the actual working endpoint
            base_url = "https://www.federalregister.gov/api/v1"
            
            # Search for grant-related documents
            query_params = {
                'conditions[term]': params.get('query', 'grant opportunity funding'),
                'conditions[type][]': 'NOTICE',  # Focus on funding notices
                'per_page': params.get('limit', 20),
                'order': 'newest'
            }
            
            response = requests.get(
                f"{base_url}/documents",
                params=query_params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                grants = []
                
                for doc in data.get('results', []):
                    grant = self._standardize_grant({
                        'title': doc.get('title'),
                        'description': doc.get('abstract'),
                        'link': doc.get('html_url'),
                        'deadline': doc.get('publication_date'),
                        'source': 'Federal Register',
                        'source_id': doc.get('document_number')
                    })
                    grants.append(grant)
                
                return grants
                
        except Exception as e:
            logger.error(f"Error fetching from Federal Register: {e}")
        
        return []
    
    def _fetch_govinfo(self, params: Dict) -> List[Dict]:
        """
        Fetch grants from GovInfo API
        """
        try:
            base_url = self.sources['govinfo']['base_url']
            
            # Build query parameters for GovInfo
            query_params = {
                'query': params.get('query', 'grant funding opportunity'),
                'collection': 'FR',  # Federal Register
                'format': 'json',
                'pageSize': params.get('limit', 25),
                'offsetMark': '*'
            }
            
            response = requests.get(
                f"{base_url}/search",
                params=query_params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                grants = []
                
                for item in data.get('packages', []):
                    grant = self._standardize_grant({
                        'title': item.get('title'),
                        'description': item.get('summary'),
                        'link': item.get('packageLink'),
                        'deadline': item.get('dateIssued'),
                        'source': 'GovInfo',
                        'source_id': item.get('packageId')
                    })
                    grants.append(grant)
                
                return grants
                
        except Exception as e:
            logger.error(f"Error fetching from GovInfo: {e}")
        
        return []
    
    
    # Existing Source Fetchers (restored)
    def _fetch_grants_gov(self, params: Dict) -> List[Dict]:
        """Fetch grants from Grants.gov API"""
        try:
            search_url = "https://www.grants.gov/search/"
            
            payload = {
                "startRecordNum": 0,
                "keyword": params.get('query', 'nonprofit'),
                "oppStatuses": "forecasted|posted",
                "sortBy": "openDate|desc",
                "rows": params.get('limit', 25)
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "PinkLemonade/1.0"
            }
            
            response = requests.post(search_url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                grants = []
                
                for opp in data.get('opportunities', []):
                    grant = self._standardize_grant(opp, 'grants_gov')
                    grants.append(grant)
                
                return grants
        except Exception as e:
            logger.error(f"Error fetching from Grants.gov: {e}")
        
        return []
    
    # New API Source Fetchers
    def _fetch_sam_gov_opportunities(self, params: Dict) -> List[Dict]:
        """Fetch opportunities from SAM.gov API"""
        source_config = self.sources.get('sam_gov_opportunities', {})
        if not source_config.get('api_key'):
            logger.warning("SAM.gov API key not available")
            return []
        
        try:
            base_url = source_config['base_url']
            endpoint = source_config['endpoints']['search']
            url = f"{base_url}{endpoint}"
            
            query_params = {
                'limit': params.get('limit', 100),
                'api_version': 'v2',
                'keyword': params.get('query', ''),
                'postedFrom': params.get('posted_from'),
                'postedTo': params.get('posted_to')
            }
            
            # Remove None values
            query_params = {k: v for k, v in query_params.items() if v is not None}
            
            request_config = self._prepare_authenticated_request(
                'sam_gov_opportunities', url, 'GET', params=query_params
            )
            
            response = self._make_request_with_retry('sam_gov_opportunities', request_config)
            
            if response.status_code == 200:
                data = response.json()
                grants = []
                for opp in data.get('opportunitiesData', []):
                    grant = self._standardize_grant(opp, 'sam_gov_opportunities')
                    grants.append(grant)
                return grants
            else:
                logger.error(f"SAM.gov API returned {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching from SAM.gov opportunities: {e}")
            return []
    
    def _fetch_sam_gov_entity(self, params: Dict) -> List[Dict]:
        """Fetch entity data from SAM.gov Entity Management API"""
        source_config = self.sources.get('sam_gov_entity', {})
        if not source_config.get('api_key'):
            logger.warning("SAM.gov Entity API key not available")
            return []
        
        try:
            base_url = source_config['base_url']
            endpoint = source_config['endpoints']['search']
            url = f"{base_url}{endpoint}"
            
            query_params = {
                'limit': params.get('limit', 100),
                'api_version': 'v3',
                'includeSections': 'entityRegistration,coreData',
                'format': 'json'
            }
            
            request_config = self._prepare_authenticated_request(
                'sam_gov_entity', url, 'GET', params=query_params
            )
            
            response = self._make_request_with_retry('sam_gov_entity', request_config)
            
            if response.status_code == 200:
                data = response.json()
                entities = []
                for entity in data.get('entityData', []):
                    standardized = self._standardize_grant(entity, 'sam_gov_entity')
                    entities.append(standardized)
                return entities
            else:
                logger.error(f"SAM.gov Entity API returned {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching from SAM.gov entity: {e}")
            return []
    
    def _fetch_michigan_socrata(self, params: Dict) -> List[Dict]:
        """Fetch data from Michigan Socrata API"""
        source_config = self.sources.get('michigan_socrata', {})
        
        try:
            base_url = source_config['base_url']
            # For now, use a generic endpoint - would need specific dataset IDs
            url = f"{base_url}/views.json"
            
            query_params = {
                '$limit': params.get('limit', 100),
                '$offset': params.get('offset', 0),
                '$order': ':updated_at DESC'
            }
            
            # Add query if provided
            if params.get('query'):
                query_params['$q'] = params['query']
            
            request_config = self._prepare_authenticated_request(
                'michigan_socrata', url, 'GET', params=query_params
            )
            
            response = self._make_request_with_retry('michigan_socrata', request_config)
            
            if response.status_code == 200:
                data = response.json()
                grants = []
                # Process Socrata dataset metadata
                for dataset in data:
                    if 'grant' in dataset.get('name', '').lower() or 'funding' in dataset.get('description', '').lower():
                        grant = self._standardize_grant(dataset, 'michigan_socrata')
                        grants.append(grant)
                return grants
            else:
                logger.error(f"Michigan Socrata API returned {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching from Michigan Socrata: {e}")
            return []
    
    def _fetch_zyte_api(self, params: Dict) -> List[Dict]:
        """Use Zyte API for web scraping grant websites"""
        source_config = self.sources.get('zyte_api', {})
        if not source_config.get('api_key'):
            logger.warning("Zyte API key not available")
            return []
        
        try:
            target_urls = params.get('urls', [])
            if not target_urls:
                # Use default scraping targets from config
                targets = source_config.get('scraping_targets', {})
                target_urls = targets.get('foundation_sites', []) + targets.get('government_portals', [])
            
            grants = []
            for url in target_urls[:5]:  # Limit to 5 URLs to avoid rate limits
                try:
                    scrape_data = self._scrape_with_zyte(url, source_config)
                    if scrape_data:
                        grant = self._standardize_grant(scrape_data, 'zyte_api')
                        grants.append(grant)
                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {e}")
                    continue
            
            return grants
            
        except Exception as e:
            logger.error(f"Error with Zyte API: {e}")
            return []
    
    def _scrape_with_zyte(self, target_url: str, config: Dict) -> Optional[Dict]:
        """Scrape a single URL using Zyte API"""
        try:
            base_url = config['base_url']
            endpoint = config['endpoints']['extract']
            url = f"{base_url}{endpoint}"
            
            scrape_params = {
                'url': target_url,
                'browserHtml': True,
                'screenshot': False,
                'geolocation': 'US'
            }
            
            request_config = self._prepare_authenticated_request(
                'zyte_api', url, 'POST', data=scrape_params
            )
            
            response = self._make_request_with_retry('zyte_api', request_config)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Zyte scraping failed for {target_url}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping {target_url} with Zyte: {e}")
            return None
    
    def _fetch_hhs_grants(self, params: Dict) -> List[Dict]:
        """Scrape HHS grants website"""
        source_config = self.sources.get('hhs_grants', {})
        
        try:
            # Try RSS feed first
            rss_url = f"{source_config['base_url']}{source_config['endpoints']['rss']}"
            
            response = requests.get(rss_url, timeout=30, headers={
                'User-Agent': source_config['scraping_config']['user_agent']
            })
            
            if response.status_code == 200:
                grants = self._parse_rss_feed(response.content, 'hhs_grants')
                return grants[:params.get('limit', 25)]
            else:
                logger.warning(f"HHS RSS feed unavailable: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching HHS grants: {e}")
            return []
    
    def _fetch_ed_grants(self, params: Dict) -> List[Dict]:
        """Scrape Department of Education grants"""
        source_config = self.sources.get('ed_grants', {})
        
        try:
            # Try RSS feed first
            rss_url = f"{source_config['base_url']}{source_config['endpoints']['rss']}"
            
            response = requests.get(rss_url, timeout=30, headers={
                'User-Agent': source_config['scraping_config']['user_agent']
            })
            
            if response.status_code == 200:
                grants = self._parse_rss_feed(response.content, 'ed_grants')
                return grants[:params.get('limit', 25)]
            else:
                logger.warning(f"Education RSS feed unavailable: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching Education grants: {e}")
            return []
    
    def _fetch_nsf_grants(self, params: Dict) -> List[Dict]:
        """Scrape NSF grants website"""
        source_config = self.sources.get('nsf_grants', {})
        
        try:
            # Try RSS feed first
            rss_url = f"{source_config['base_url']}{source_config['endpoints']['rss']}"
            
            response = requests.get(rss_url, timeout=30, headers={
                'User-Agent': source_config['scraping_config']['user_agent']
            })
            
            if response.status_code == 200:
                grants = self._parse_rss_feed(response.content, 'nsf_grants')
                return grants[:params.get('limit', 25)]
            else:
                logger.warning(f"NSF RSS feed unavailable: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching NSF grants: {e}")
            return []
    
    def _parse_rss_feed(self, content: bytes, source_name: str) -> List[Dict]:
        """Parse RSS feed content into grant objects"""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            
            grants = []
            items = root.findall('.//item')
            
            for item in items:
                title = item.find('title')
                link = item.find('link')
                description = item.find('description')
                pub_date = item.find('pubDate')
                
                raw_data = {
                    'title': title.text if title is not None else 'Grant Opportunity',
                    'description': description.text if description is not None else '',
                    'link': link.text if link is not None else '',
                    'publication_date': pub_date.text if pub_date is not None else '',
                    'source': source_name
                }
                
                grant = self._standardize_grant(raw_data, source_name)
                grants.append(grant)
            
            return grants
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed for {source_name}: {e}")
            return []
    
    def _generate_id(self, grant: Dict) -> str:
        """Generate unique ID for grant"""
        unique_str = f"{grant.get('title', '')}:{grant.get('funder', '')}:{grant.get('source', '')}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:12]
    
    def _handle_no_data(self, source_name: str) -> List[Dict]:
        """
        Handle cases where no real data is available
        """
        if is_live():
            logger.warning(f"LIVE MODE: No real data available from {source_name}.")
            logger.warning("GUIDANCE: API keys, credentials, or configuration may be needed. Check source settings and try again.")
        else:
            logger.info(f"DEMO MODE: No data simulation for {source_name}")
        return []  # Return empty list - never fake data

# Singleton instance
api_manager = APIManager()

# Convenience functions for direct import
def get_grants_from_source(source_name: str, params: Optional[Dict] = None) -> List[Dict]:
    """Fetch grants from a specific source"""
    return api_manager.get_grants_from_source(source_name, params)

def search_opportunities(query: str, filters: Optional[Dict] = None) -> List[Dict]:
    """Search for opportunities across all sources"""
    return api_manager.search_opportunities(query, filters)

def fetch_grant_details(grant_id: str, source: Optional[str] = None) -> Optional[Dict]:
    """Fetch detailed grant information"""
    return api_manager.fetch_grant_details(grant_id, source)

def get_watchlist_updates(watchlist_id: str, last_check: Optional[datetime] = None) -> List[Dict]:
    """Get watchlist updates"""
    return api_manager.get_watchlist_updates(watchlist_id, last_check)