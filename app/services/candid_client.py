"""
Candid API Client with Key Rotation and Caching
"""
import os
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class RotatingKeyPool:
    """Rotating key pool for API keys"""
    def __init__(self, env_var: str):
        keys_csv = os.environ.get(env_var, '')
        self.keys = [k.strip() for k in keys_csv.split(',') if k.strip()]
        self.current_index = 0
        
    def get_next_key(self) -> Optional[str]:
        """Get next key in rotation"""
        if not self.keys:
            return None
        key = self.keys[self.current_index]
        old_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.keys)
        logger.info(f"Using API key at index {old_index} of {len(self.keys)} total keys")
        return key
    
    def has_keys(self) -> bool:
        """Check if pool has keys"""
        return len(self.keys) > 0

class CandidClient:
    """Candid API Client with caching and key rotation"""
    
    def __init__(self):
        self.grants_pool = RotatingKeyPool('CANDID_GRANTS_KEYS')
        self.news_pool = RotatingKeyPool('CANDID_NEWS_KEYS')
        self.cache = {}  # Simple cache: (url, sorted_params) -> (expires_at, data)
        
    def _cache_key(self, url: str, params: Dict) -> Tuple:
        """Create cache key from URL and sorted params"""
        sorted_params = tuple(sorted(params.items())) if params else ()
        return (url, sorted_params)
    
    def _get_from_cache(self, url: str, params: Dict) -> Optional[Dict]:
        """Get data from cache if not expired"""
        key = self._cache_key(url, params)
        if key in self.cache:
            expires_at, data = self.cache[key]
            if datetime.now() < expires_at:
                logger.info(f"Cache HIT for {url}")
                return data
            else:
                del self.cache[key]
        logger.info(f"Cache MISS for {url}")
        return None
    
    def _set_cache(self, url: str, params: Dict, data: Dict, ttl_seconds: int = 300):
        """Set cache with TTL"""
        key = self._cache_key(url, params)
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        self.cache[key] = (expires_at, data)
    
    def get_json(self, url: str, params: Dict, service: str = "news") -> Dict:
        """Make GET request with key rotation and caching"""
        # Check cache first
        cached = self._get_from_cache(url, params)
        if cached is not None:
            return cached
        
        # Select appropriate key pool
        pool = self.news_pool if service == "news" else self.grants_pool
        if not pool.has_keys():
            return {"error": f"No API keys configured for {service}"}
        
        # Build full URL with params
        if params:
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
        else:
            full_url = url
        
        # Try up to 2 keys with rotation on 401/429
        last_error = None
        attempts = min(2, len(pool.keys))
        
        for _ in range(attempts):
            api_key = pool.get_next_key()
            if not api_key:
                break
                
            headers = {
                'Accept': 'application/json',
                'X-API-KEY': api_key
            }
            
            req = urllib.request.Request(full_url, headers=headers)
            
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    logger.info(f"Candid API {service} endpoint hit: {url}, status: {response.status}")
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        self._set_cache(url, params, data)
                        return data
            except urllib.error.HTTPError as e:
                logger.info(f"Candid API {service} endpoint hit: {url}, status: {e.code}")
                if e.code in [401, 429]:
                    logger.warning(f"Key rotation triggered, status: {e.code}")
                    # Rotate key and retry
                    last_error = e
                    continue
                else:
                    return {"error": f"HTTP {e.code}: {e.reason}"}
            except Exception as e:
                return {"error": str(e)}
        
        # All retries failed
        if last_error:
            return {"error": f"All keys failed: HTTP {last_error.code}"}
        return {"error": "Request failed"}
    
    def search_news(self, query: str, start_date: Optional[str] = None, 
                   region: Optional[str] = None, page: int = 1, size: int = 25) -> Dict:
        """Search Candid news"""
        url = "https://api.candid.org/funding/v1/news"
        params = {
            'query': query,
            'page': page,
            'size': size
        }
        if start_date:
            params['start_date'] = start_date
        if region:
            params['region'] = region
            
        return self.get_json(url, params, service="news")
    
    def search_transactions(self, query: str, page: int = 1, size: int = 25) -> Dict:
        """Search grant transactions"""
        url = "https://api.candid.org/funding/v1/grants"
        params = {
            'query': query,
            'page': page,
            'size': size
        }
        return self.get_json(url, params, service="grants")

# Singleton instance
_client = None

def get_candid_client() -> CandidClient:
    """Get singleton Candid client instance"""
    global _client
    if _client is None:
        _client = CandidClient()
    return _client