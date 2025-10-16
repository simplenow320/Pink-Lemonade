"""
Cache Service for Performance Optimization
Implements in-memory caching with TTL for frequently accessed data
Enhanced with template caching for Smart Tools Hybrid System
"""
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Callable
from functools import wraps
import hashlib
import json
import logging
import time

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
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'sets': self._stats['sets'],
            'evictions': self._stats['evictions'],
            'hit_rate': f"{hit_rate:.1f}%",
            'size': len(self._cache),
            'memory_kb': len(str(self._cache)) / 1024
        }
    
    # Organization-specific caching methods
    def cache_org_context(self, org_id: int, context: Dict[str, Any], ttl: int = 3600) -> None:
        """Cache organization context for Smart Tools"""
        key = self._make_key('org_context', org_id)
        self.set(key, context, ttl)
    
    def get_org_context(self, org_id: int) -> Optional[Dict[str, Any]]:
        """Get cached organization context"""
        key = self._make_key('org_context', org_id)
        return self.get(key)
    
    def cache_grant_data(self, org_id: int, grant_data: list, ttl: int = 1800) -> None:
        """Cache grant data for organization"""
        key = self._make_key('grant_data', org_id)
        self.set(key, grant_data, ttl)
    
    def get_grant_data(self, org_id: int) -> Optional[list]:
        """Get cached grant data"""
        key = self._make_key('grant_data', org_id)
        return self.get(key)
    
    def cached(self, ttl_seconds: int = 300, key_prefix: str = None):
        """Decorator for caching function results"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                prefix = key_prefix or func.__name__
                cache_key = self._make_key(prefix, *args, **kwargs)
                
                # Check cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {prefix}")
                    return cached_result
                
                # Call function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl_seconds)
                logger.debug(f"Cached result for {prefix}")
                return result
            
            return wrapper
        return decorator


class TemplateCache:
    """Specialized cache for template components and filled templates"""
    
    def __init__(self):
        self.component_cache: Dict[str, Dict[str, str]] = {}
        self.template_cache: Dict[str, str] = {}
        self.last_used: Dict[str, float] = {}
        self.usage_count: Dict[str, int] = {}
    
    def cache_component(self, component_type: str, component_id: str, content: str) -> None:
        """Cache a reusable component"""
        if component_type not in self.component_cache:
            self.component_cache[component_type] = {}
        
        self.component_cache[component_type][component_id] = content
        self.last_used[f"{component_type}:{component_id}"] = time.time()
        
        # Track usage count
        usage_key = f"{component_type}:{component_id}"
        self.usage_count[usage_key] = self.usage_count.get(usage_key, 0) + 1
    
    def get_component(self, component_type: str, component_id: str) -> Optional[str]:
        """Get cached component"""
        if component_type in self.component_cache:
            if component_id in self.component_cache[component_type]:
                self.last_used[f"{component_type}:{component_id}"] = time.time()
                usage_key = f"{component_type}:{component_id}"
                self.usage_count[usage_key] = self.usage_count.get(usage_key, 0) + 1
                return self.component_cache[component_type][component_id]
        return None
    
    def cache_filled_template(self, template_key: str, filled_content: str) -> None:
        """Cache a filled template for reuse"""
        self.template_cache[template_key] = filled_content
        self.last_used[f"template:{template_key}"] = time.time()
        self.usage_count[f"template:{template_key}"] = self.usage_count.get(f"template:{template_key}", 0) + 1
    
    def get_filled_template(self, template_key: str) -> Optional[str]:
        """Get cached filled template"""
        if template_key in self.template_cache:
            self.last_used[f"template:{template_key}"] = time.time()
            self.usage_count[f"template:{template_key}"] = self.usage_count.get(f"template:{template_key}", 0) + 1
            return self.template_cache[template_key]
        return None
    
    def get_most_used(self, limit: int = 10) -> Dict[str, int]:
        """Get most frequently used components"""
        sorted_items = sorted(
            self.usage_count.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {item[0]: item[1] for item in sorted_items[:limit]}
    
    def get_recently_used(self, limit: int = 10) -> Dict[str, float]:
        """Get most recently used components"""
        sorted_items = sorted(
            self.last_used.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            item[0]: time.time() - item[1]
            for item in sorted_items[:limit]
        }
    
    def cleanup_old(self, max_age_seconds: int = 86400) -> int:
        """Remove components not used in max_age_seconds (default 24 hours)"""
        current_time = time.time()
        removed_count = 0
        
        # Find old items
        old_items = [
            key for key, last_time in self.last_used.items()
            if current_time - last_time > max_age_seconds
        ]
        
        # Remove them
        for item_key in old_items:
            if item_key.startswith('template:'):
                template_key = item_key.replace('template:', '')
                if template_key in self.template_cache:
                    del self.template_cache[template_key]
                    removed_count += 1
            else:
                try:
                    component_type, component_id = item_key.split(':', 1)
                    if component_type in self.component_cache:
                        if component_id in self.component_cache[component_type]:
                            del self.component_cache[component_type][component_id]
                            removed_count += 1
                except ValueError:
                    continue
            
            del self.last_used[item_key]
            if item_key in self.usage_count:
                del self.usage_count[item_key]
        
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get template cache statistics"""
        total_components = sum(len(comps) for comps in self.component_cache.values())
        total_templates = len(self.template_cache)
        total_usage = sum(self.usage_count.values())
        
        return {
            'total_components': total_components,
            'total_templates': total_templates,
            'total_usage': total_usage,
            'component_types': list(self.component_cache.keys()),
            'most_used': self.get_most_used(5),
            'memory_estimate_kb': (
                len(str(self.component_cache)) + 
                len(str(self.template_cache))
            ) / 1024
        }


# Global cache instances
cache = CacheService()  # General purpose cache
template_cache = TemplateCache()  # Template-specific cache

# Helper function for Smart Tools caching
def cache_smart_tool_result(tool: str, org_id: int, params: Dict, result: Any, ttl: int = 1800) -> None:
    """Cache Smart Tool generation result"""
    key = cache._make_key(f"smart_tool:{tool}", org_id=org_id, **params)
    cache.set(key, result, ttl)

def get_cached_smart_tool_result(tool: str, org_id: int, params: Dict) -> Optional[Any]:
    """Get cached Smart Tool generation result"""
    key = cache._make_key(f"smart_tool:{tool}", org_id=org_id, **params)
    return cache.get(key)