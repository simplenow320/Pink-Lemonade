"""
HTTP Helper Classes for API Key Rotation and Caching
"""
import os
import time
import requests
import logging
from typing import Dict, Any, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class RotatingKeyPool:
    """Rotating key pool for API keys with error handling"""
    
    def __init__(self, env_var_name: str):
        """Initialize with keys from environment variable (comma-separated)"""
        keys_csv = os.environ.get(env_var_name, '')
        self.keys = [k.strip() for k in keys_csv.split(',') if k.strip()]
        self.current_index = 0
        self.env_var_name = env_var_name
        
        if not self.keys:
            raise ValueError(f"No API keys found in environment variable '{env_var_name}'")
    
    def next(self) -> str:
        """Get current key and advance index"""
        if not self.keys:
            raise RuntimeError(f"No API keys available for '{self.env_var_name}'")
        
        key = self.keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key
    
    def on_unauthorized_or_rate_limit(self) -> bool:
        """Advance to next key on 401/429 errors. Returns True if more keys available."""
        if len(self.keys) <= 1:
            return False  # No other keys to try
        
        # We already advanced in next(), so just check if we have alternatives
        return True
    
    def has_keys(self) -> bool:
        """Check if pool has any keys"""
        return len(self.keys) > 0
    
    def key_count(self) -> int:
        """Get total number of keys"""
        return len(self.keys)


class SimpleCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        """Initialize empty cache"""
        self._cache: Dict[Tuple, Tuple[float, Any]] = {}
    
    def _make_key(self, method: str, url: str, params: Optional[Dict] = None) -> Tuple:
        """Create cache key from method, url, and sorted params"""
        if params is None:
            params = {}
        
        # Sort params for consistent cache keys
        frozen_params = tuple(sorted(params.items()))
        return (method.upper(), url, frozen_params)
    
    def get(self, method: str, url: str, params: Optional[Dict] = None) -> Optional[Any]:
        """Get cached data if not expired"""
        key = self._make_key(method, url, params)
        
        if key not in self._cache:
            return None
        
        expires_at, data = self._cache[key]
        current_time = time.time()
        
        if current_time >= expires_at:
            # Expired, remove from cache
            del self._cache[key]
            return None
        
        return data
    
    def set(self, method: str, url: str, data: Any, ttl_seconds: Union[int, float], params: Optional[Dict] = None) -> None:
        """Store data in cache with TTL"""
        key = self._make_key(method, url, params)
        expires_at = time.time() + ttl_seconds
        self._cache[key] = (expires_at, data)
    
    def clear(self) -> None:
        """Clear all cached data"""
        self._cache.clear()
    
    def size(self) -> int:
        """Get number of items in cache"""
        return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed"""
        current_time = time.time()
        expired_keys = [
            key for key, (expires_at, _) in self._cache.items() 
            if current_time >= expires_at
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)


def make_request_with_retry(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    data: Optional[Any] = None,
    timeout: int = 30,
    max_retries: int = 3,
    backoff_factor: float = 1.0
) -> requests.Response:
    """
    Make HTTP request with automatic retry on failure.
    
    Args:
        method: HTTP method ('GET', 'POST', etc.)
        url: Full API URL
        headers: Optional headers dict
        params: Optional query parameters
        json: Optional JSON body for POST/PUT
        data: Optional form data
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        
    Returns:
        requests.Response object
        
    Raises:
        requests.RequestException: If all retries fail
    """
    retry_codes = [429, 500, 502, 503, 504]
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json,
                data=data,
                timeout=timeout
            )
            
            # If successful or non-retryable error, return
            if response.status_code < 400 or response.status_code not in retry_codes:
                return response
            
            # If this was the last attempt, return the response anyway
            if attempt == max_retries:
                logger.warning(f"Max retries ({max_retries}) reached for {method} {url}")
                return response
            
            # Calculate wait time with exponential backoff
            wait_time = backoff_factor * (2 ** attempt)
            logger.info(f"Retrying {method} {url} in {wait_time}s (attempt {attempt + 1}/{max_retries}, status: {response.status_code})")
            time.sleep(wait_time)
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                logger.error(f"Request failed after {max_retries} retries: {method} {url} - {str(e)}")
                raise e
            
            wait_time = backoff_factor * (2 ** attempt)
            logger.info(f"Request exception, retrying {method} {url} in {wait_time}s: {str(e)}")
            time.sleep(wait_time)
    
    # Should never reach here, but just in case
    raise requests.RequestException(f"Failed to complete request after {max_retries} attempts")