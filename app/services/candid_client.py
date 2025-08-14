"""
Candid API Client with Key Rotation and Caching
"""
import os
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import urllib.request
import urllib.parse
import urllib.error
from functools import wraps

class SimpleCache:
    """Simple in-memory cache with TTL"""
    def __init__(self):
        self.cache = {}
        self.ttl = 300  # 5 minutes default TTL
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            data, expiry = self.cache[key]
            if datetime.now() < expiry:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        expiry = datetime.now() + timedelta(seconds=ttl or self.ttl)
        self.cache[key] = (value, expiry)
    
    def clear_expired(self):
        now = datetime.now()
        expired = [k for k, (_, exp) in self.cache.items() if exp < now]
        for k in expired:
            del self.cache[k]

class KeyRotator:
    """Round-robin key rotation with fallback on errors"""
    def __init__(self, keys: List[str]):
        self.keys = keys
        self.current_index = 0
        self.failed_keys = set()
        self.failure_timestamps = {}
        self.retry_after = 3600  # Retry failed keys after 1 hour
    
    def get_next_key(self) -> Optional[str]:
        """Get next available key using round-robin"""
        if not self.keys:
            return None
        
        # Clean up old failures (retry after 1 hour)
        now = time.time()
        for key in list(self.failed_keys):
            if key in self.failure_timestamps:
                if now - self.failure_timestamps[key] > self.retry_after:
                    self.failed_keys.remove(key)
                    del self.failure_timestamps[key]
        
        # Find next working key
        attempts = 0
        while attempts < len(self.keys):
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
            
            if key not in self.failed_keys:
                return key
            attempts += 1
        
        # If all keys failed, try the oldest failed one
        if self.failed_keys:
            oldest_key = min(self.failure_timestamps, key=self.failure_timestamps.get)
            return oldest_key
        
        return None
    
    def mark_failed(self, key: str):
        """Mark a key as failed"""
        self.failed_keys.add(key)
        self.failure_timestamps[key] = time.time()

class CandidClient:
    """Candid API Client with caching and key rotation"""
    
    BASE_URL_GRANTS = "https://api.candid.org/grants/v1"
    BASE_URL_NEWS = "https://philanthropynewsdigest.org/api/v1"
    
    def __init__(self):
        # Load and parse API keys
        grants_keys = os.environ.get('CANDID_GRANTS_KEYS', '').split(',')
        news_keys = os.environ.get('CANDID_NEWS_KEYS', '').split(',')
        
        self.grants_keys = [k.strip() for k in grants_keys if k.strip()]
        self.news_keys = [k.strip() for k in news_keys if k.strip()]
        
        # Initialize rotators and cache
        self.grants_rotator = KeyRotator(self.grants_keys)
        self.news_rotator = KeyRotator(self.news_keys)
        self.cache = SimpleCache()
    
    def _make_request(self, url: str, api_key: str, rotator: KeyRotator) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'User-Agent': 'PinkLemonade/1.0'
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code in [401, 429]:  # Unauthorized or Rate Limited
                rotator.mark_failed(api_key)
            raise
        except Exception as e:
            # Log error but don't expose details
            print(f"Request failed: {type(e).__name__}")
            raise
        
        return None
    
    def _cached_request(self, cache_key: str, url: str, rotator: KeyRotator) -> Optional[Dict]:
        """Make cached request with key rotation"""
        # Check cache first
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Try request with key rotation
        last_error = None
        attempts = min(3, len(rotator.keys))  # Try up to 3 keys
        
        for _ in range(attempts):
            api_key = rotator.get_next_key()
            if not api_key:
                break
            
            try:
                result = self._make_request(url, api_key, rotator)
                if result:
                    self.cache.set(cache_key, result)
                    return result
            except Exception as e:
                last_error = e
                continue
        
        if last_error:
            raise last_error
        return None
    
    def search_grants(self, query: str, limit: int = 10) -> Dict:
        """Search Candid grants database"""
        if not self.grants_keys:
            return {"error": "No Candid grants API keys configured", "grants": []}
        
        # Build cache key
        cache_key = f"grants:{hashlib.md5(f'{query}:{limit}'.encode()).hexdigest()}"
        
        # Build URL
        params = urllib.parse.urlencode({
            'q': query,
            'limit': limit,
            'format': 'json'
        })
        url = f"{self.BASE_URL_GRANTS}/search?{params}"
        
        try:
            result = self._cached_request(cache_key, url, self.grants_rotator)
            return result or {"grants": []}
        except Exception as e:
            return {"error": f"Failed to fetch grants: {str(e)}", "grants": []}
    
    def search_news(self, query: str, limit: int = 10) -> Dict:
        """Search Candid philanthropy news"""
        if not self.news_keys:
            return {"error": "No Candid news API keys configured", "articles": []}
        
        # Build cache key
        cache_key = f"news:{hashlib.md5(f'{query}:{limit}'.encode()).hexdigest()}"
        
        # Build URL
        params = urllib.parse.urlencode({
            'q': query,
            'limit': limit,
            'format': 'json'
        })
        url = f"{self.BASE_URL_NEWS}/news?{params}"
        
        try:
            result = self._cached_request(cache_key, url, self.news_rotator)
            return result or {"articles": []}
        except Exception as e:
            return {"error": f"Failed to fetch news: {str(e)}", "articles": []}
    
    def get_foundation_profile(self, ein: str) -> Dict:
        """Get foundation profile by EIN"""
        if not self.grants_keys:
            return {"error": "No Candid grants API keys configured"}
        
        # Build cache key
        cache_key = f"foundation:{ein}"
        
        # Build URL
        url = f"{self.BASE_URL_GRANTS}/foundations/{ein}"
        
        try:
            result = self._cached_request(cache_key, url, self.grants_rotator)
            return result or {"error": "Foundation not found"}
        except Exception as e:
            return {"error": f"Failed to fetch foundation: {str(e)}"}
    
    def test_connection(self) -> Dict:
        """Test API connections without exposing keys"""
        status = {
            "grants_api": {
                "configured": bool(self.grants_keys),
                "key_count": len(self.grants_keys),
                "status": "not_tested"
            },
            "news_api": {
                "configured": bool(self.news_keys),
                "key_count": len(self.news_keys),
                "status": "not_tested"
            }
        }
        
        # Test grants API
        if self.grants_keys:
            try:
                result = self.search_grants("education", limit=1)
                status["grants_api"]["status"] = "error" if "error" in result else "connected"
            except:
                status["grants_api"]["status"] = "error"
        
        # Test news API
        if self.news_keys:
            try:
                result = self.search_news("nonprofit", limit=1)
                status["news_api"]["status"] = "error" if "error" in result else "connected"
            except:
                status["news_api"]["status"] = "error"
        
        return status

# Singleton instance
_client = None

def get_candid_client() -> CandidClient:
    """Get singleton Candid client instance"""
    global _client
    if _client is None:
        _client = CandidClient()
    return _client