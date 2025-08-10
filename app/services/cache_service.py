"""
Cache Service for Performance Optimization
Implements in-memory caching with TTL for frequently accessed data
"""
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments"""
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self._cache:
            entry = self._cache[key]
            if entry['expires_at'] > datetime.now():
                self._stats['hits'] += 1
                return entry['value']
            else:
                # Expired, remove it
                del self._cache[key]
                self._stats['evictions'] += 1
        
        self._stats['misses'] += 1
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in cache with TTL"""
        self._cache[key] = {
            'value': value,
            'expires_at': datetime.now() + timedelta(seconds=ttl_seconds),
            'created_at': datetime.now()
        }
        self._stats['sets'] += 1
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry['expires_at'] <= now
        ]
        
        for key in expired_keys:
            del self._cache[key]
            self._stats['evictions'] += 1
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self._stats,
            'size': len(self._cache),
            'hit_rate': round(hit_rate, 2)
        }
    
    # Decorator for caching function results
    def cached(self, ttl_seconds: int = 300, key_prefix: str = None):
        """Decorator to cache function results"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                prefix = key_prefix or f"{func.__module__}.{func.__name__}"
                cache_key = self._make_key(prefix, *args, **kwargs)
                
                # Check cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for {prefix}")
                    return cached_value
                
                # Call function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl_seconds)
                logger.debug(f"Cached result for {prefix}")
                return result
            
            return wrapper
        return decorator

# Singleton instance
cache = CacheService()

# Specific cache utilities for common operations
class GrantCache:
    """Specialized cache for grant-related data"""
    
    @staticmethod
    def cache_grant_search(org_id: int, query: str, filters: dict, results: list):
        """Cache grant search results"""
        key = cache._make_key('grant_search', org_id, query, **filters)
        cache.set(key, results, ttl_seconds=600)  # 10 minutes
    
    @staticmethod
    def get_grant_search(org_id: int, query: str, filters: dict):
        """Get cached grant search results"""
        key = cache._make_key('grant_search', org_id, query, **filters)
        return cache.get(key)
    
    @staticmethod
    def cache_grant_stats(org_id: int, stats: dict):
        """Cache grant statistics"""
        key = f"grant_stats_{org_id}"
        cache.set(key, stats, ttl_seconds=1800)  # 30 minutes
    
    @staticmethod
    def get_grant_stats(org_id: int):
        """Get cached grant statistics"""
        key = f"grant_stats_{org_id}"
        return cache.get(key)
    
    @staticmethod
    def invalidate_grant_cache(org_id: int):
        """Invalidate all grant-related cache for an org"""
        # Clear stats
        cache.delete(f"grant_stats_{org_id}")
        # Clear searches (would need to track keys for full implementation)
        logger.info(f"Invalidated grant cache for org {org_id}")

class AICache:
    """Specialized cache for AI responses"""
    
    @staticmethod
    def cache_ai_response(prompt_hash: str, response: dict):
        """Cache AI response with longer TTL"""
        key = f"ai_response_{prompt_hash}"
        cache.set(key, response, ttl_seconds=3600)  # 1 hour
    
    @staticmethod
    def get_ai_response(prompt_hash: str):
        """Get cached AI response"""
        key = f"ai_response_{prompt_hash}"
        return cache.get(key)
    
    @staticmethod
    def hash_prompt(prompt: str) -> str:
        """Generate hash for prompt"""
        return hashlib.md5(prompt.encode()).hexdigest()