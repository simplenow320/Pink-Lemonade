"""
Cache Service for Performance Optimization
Implements in-memory caching with TTL
"""

from datetime import datetime, timedelta
import logging
import json
import hashlib

logger = logging.getLogger(__name__)

class CacheService:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        self.cache = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
    
    def _make_key(self, namespace, key):
        """Create cache key from namespace and key"""
        if isinstance(key, dict):
            key = json.dumps(key, sort_keys=True)
        return f"{namespace}:{hashlib.md5(str(key).encode()).hexdigest()}"
    
    def get(self, namespace, key):
        """Get value from cache"""
        cache_key = self._make_key(namespace, key)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if datetime.now() < entry['expires']:
                self.stats['hits'] += 1
                logger.debug(f"Cache hit: {cache_key}")
                return entry['value']
            else:
                # Expired, remove it
                del self.cache[cache_key]
                self.stats['evictions'] += 1
        
        self.stats['misses'] += 1
        logger.debug(f"Cache miss: {cache_key}")
        return None
    
    def set(self, namespace, key, value, ttl=300):
        """Set value in cache with TTL in seconds"""
        cache_key = self._make_key(namespace, key)
        
        self.cache[cache_key] = {
            'value': value,
            'expires': datetime.now() + timedelta(seconds=ttl),
            'created': datetime.now()
        }
        
        self.stats['sets'] += 1
        logger.debug(f"Cache set: {cache_key}, TTL: {ttl}s")
        
        # Clean up expired entries periodically
        if self.stats['sets'] % 100 == 0:
            self.cleanup()
    
    def delete(self, namespace, key):
        """Delete value from cache"""
        cache_key = self._make_key(namespace, key)
        
        if cache_key in self.cache:
            del self.cache[cache_key]
            logger.debug(f"Cache delete: {cache_key}")
            return True
        return False
    
    def clear_namespace(self, namespace):
        """Clear all cache entries for a namespace"""
        prefix = f"{namespace}:"
        keys_to_delete = [k for k in self.cache.keys() if k.startswith(prefix)]
        
        for key in keys_to_delete:
            del self.cache[key]
        
        logger.info(f"Cleared {len(keys_to_delete)} entries from namespace: {namespace}")
        return len(keys_to_delete)
    
    def cleanup(self):
        """Remove expired entries"""
        now = datetime.now()
        expired = []
        
        for key, entry in self.cache.items():
            if now >= entry['expires']:
                expired.append(key)
        
        for key in expired:
            del self.cache[key]
            self.stats['evictions'] += 1
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired cache entries")
    
    def get_stats(self):
        """Get cache statistics"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'evictions': self.stats['evictions'],
            'hit_rate': hit_rate,
            'entries': len(self.cache)
        }

# Global cache instance
cache = CacheService()