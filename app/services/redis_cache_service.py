"""
Redis Cache Service - Production Implementation
High-performance caching layer for API responses and data optimization
"""

import logging
import json
import os
from datetime import timedelta
from typing import Dict, List, Any, Optional, Union
import hashlib
import pickle

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - using memory cache fallback")

class RedisCacheService:
    """Production Redis caching service with fallback"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.cache_prefix = os.getenv('CACHE_PREFIX', 'pinklemonade:')
        self.default_ttl = int(os.getenv('CACHE_DEFAULT_TTL', 3600))  # 1 hour
        
        # Initialize Redis connection
        self.redis_client = None
        self.memory_cache = {}  # Fallback memory cache
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed, using memory cache: {e}")
                self.redis_client = None
        
        self.is_redis_enabled = self.redis_client is not None
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache
        """
        try:
            cache_key = self._get_cache_key(key)
            
            if self.is_redis_enabled:
                value = self.redis_client.get(cache_key)
                if value is not None:
                    return self._deserialize_value(value)
            else:
                # Memory cache fallback
                if cache_key in self.memory_cache:
                    entry = self.memory_cache[cache_key]
                    if not self._is_expired(entry):
                        return entry['value']
                    else:
                        del self.memory_cache[cache_key]
            
            return default
            
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with optional TTL
        """
        try:
            cache_key = self._get_cache_key(key)
            ttl = ttl or self.default_ttl
            
            if self.is_redis_enabled:
                serialized_value = self._serialize_value(value)
                self.redis_client.setex(cache_key, ttl, serialized_value)
            else:
                # Memory cache fallback
                import time
                self.memory_cache[cache_key] = {
                    'value': value,
                    'expires_at': time.time() + ttl
                }
                # Clean up expired entries periodically
                self._cleanup_memory_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache
        """
        try:
            cache_key = self._get_cache_key(key)
            
            if self.is_redis_enabled:
                self.redis_client.delete(cache_key)
            else:
                # Memory cache fallback
                self.memory_cache.pop(cache_key, None)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern
        """
        try:
            cache_pattern = self._get_cache_key(pattern)
            deleted_count = 0
            
            if self.is_redis_enabled:
                keys = self.redis_client.keys(cache_pattern)
                if keys:
                    deleted_count = self.redis_client.delete(*keys)
            else:
                # Memory cache fallback
                keys_to_delete = [key for key in self.memory_cache.keys() if pattern in key]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                deleted_count = len(keys_to_delete)
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache clear pattern failed for {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        """
        try:
            cache_key = self._get_cache_key(key)
            
            if self.is_redis_enabled:
                return bool(self.redis_client.exists(cache_key))
            else:
                # Memory cache fallback
                if cache_key in self.memory_cache:
                    entry = self.memory_cache[cache_key]
                    if not self._is_expired(entry):
                        return True
                    else:
                        del self.memory_cache[cache_key]
                return False
            
        except Exception as e:
            logger.error(f"Cache exists check failed for key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        Get TTL for key (-1 if no expiration, -2 if key doesn't exist)
        """
        try:
            cache_key = self._get_cache_key(key)
            
            if self.is_redis_enabled:
                return self.redis_client.ttl(cache_key)
            else:
                # Memory cache fallback
                if cache_key in self.memory_cache:
                    entry = self.memory_cache[cache_key]
                    import time
                    remaining = entry['expires_at'] - time.time()
                    return int(remaining) if remaining > 0 else -2
                return -2
            
        except Exception as e:
            logger.error(f"Cache TTL check failed for key {key}: {e}")
            return -2
    
    def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment numeric value in cache
        """
        try:
            cache_key = self._get_cache_key(key)
            
            if self.is_redis_enabled:
                return self.redis_client.incrby(cache_key, amount)
            else:
                # Memory cache fallback
                current_value = self.get(key, 0)
                new_value = int(current_value) + amount
                self.set(key, new_value)
                return new_value
            
        except Exception as e:
            logger.error(f"Cache increment failed for key {key}: {e}")
            return 0
    
    def cache_api_response(self, endpoint: str, params: Dict, response_data: Any, ttl: int = 300) -> bool:
        """
        Cache API response with endpoint and parameters as key
        """
        try:
            # Create cache key from endpoint and parameters
            cache_key = self._create_api_cache_key(endpoint, params)
            return self.set(cache_key, response_data, ttl)
            
        except Exception as e:
            logger.error(f"API response caching failed: {e}")
            return False
    
    def get_cached_api_response(self, endpoint: str, params: Dict) -> Any:
        """
        Get cached API response
        """
        try:
            cache_key = self._create_api_cache_key(endpoint, params)
            return self.get(cache_key)
            
        except Exception as e:
            logger.error(f"API response cache retrieval failed: {e}")
            return None
    
    def cache_grant_search(self, search_params: Dict, results: List[Dict], ttl: int = 1800) -> bool:
        """
        Cache grant search results (30 minutes default)
        """
        try:
            cache_key = f"grant_search:{self._hash_dict(search_params)}"
            return self.set(cache_key, results, ttl)
            
        except Exception as e:
            logger.error(f"Grant search caching failed: {e}")
            return False
    
    def get_cached_grant_search(self, search_params: Dict) -> Optional[List[Dict]]:
        """
        Get cached grant search results
        """
        try:
            cache_key = f"grant_search:{self._hash_dict(search_params)}"
            return self.get(cache_key)
            
        except Exception as e:
            logger.error(f"Grant search cache retrieval failed: {e}")
            return None
    
    def cache_ai_analysis(self, grant_id: str, org_id: str, analysis_result: Dict, ttl: int = 7200) -> bool:
        """
        Cache AI analysis results (2 hours default)
        """
        try:
            cache_key = f"ai_analysis:{grant_id}:{org_id}"
            return self.set(cache_key, analysis_result, ttl)
            
        except Exception as e:
            logger.error(f"AI analysis caching failed: {e}")
            return False
    
    def get_cached_ai_analysis(self, grant_id: str, org_id: str) -> Optional[Dict]:
        """
        Get cached AI analysis results
        """
        try:
            cache_key = f"ai_analysis:{grant_id}:{org_id}"
            return self.get(cache_key)
            
        except Exception as e:
            logger.error(f"AI analysis cache retrieval failed: {e}")
            return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics and health info
        """
        try:
            stats = {
                'cache_type': 'redis' if self.is_redis_enabled else 'memory',
                'redis_available': REDIS_AVAILABLE,
                'redis_connected': self.is_redis_enabled,
                'default_ttl': self.default_ttl,
                'cache_prefix': self.cache_prefix
            }
            
            if self.is_redis_enabled:
                info = self.redis_client.info()
                stats.update({
                    'redis_version': info.get('redis_version'),
                    'used_memory_mb': round(info.get('used_memory', 0) / (1024 * 1024), 2),
                    'connected_clients': info.get('connected_clients'),
                    'total_commands_processed': info.get('total_commands_processed'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                })
                
                # Calculate hit ratio
                hits = stats['keyspace_hits']
                misses = stats['keyspace_misses']
                if hits + misses > 0:
                    stats['hit_ratio'] = round(hits / (hits + misses) * 100, 2)
                else:
                    stats['hit_ratio'] = 0
            else:
                stats.update({
                    'memory_cache_keys': len(self.memory_cache),
                    'memory_cache_size_estimate_kb': len(str(self.memory_cache)) / 1024
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'error': str(e)}
    
    def flush_cache(self) -> bool:
        """
        Flush all cache data
        """
        try:
            if self.is_redis_enabled:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
            
            logger.info("Cache flushed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Cache flush failed: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform cache health check
        """
        try:
            health = {
                'cache_available': False,
                'cache_type': 'memory',
                'response_time_ms': 0,
                'test_operations': {
                    'set': False,
                    'get': False,
                    'delete': False
                }
            }
            
            import time
            start_time = time.time()
            
            # Test basic operations
            test_key = 'health_check_test'
            test_value = {'timestamp': time.time(), 'test': True}
            
            # Test SET
            health['test_operations']['set'] = self.set(test_key, test_value, 60)
            
            # Test GET
            retrieved_value = self.get(test_key)
            health['test_operations']['get'] = retrieved_value == test_value
            
            # Test DELETE
            health['test_operations']['delete'] = self.delete(test_key)
            
            # Calculate response time
            health['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            # Overall health
            health['cache_available'] = all(health['test_operations'].values())
            health['cache_type'] = 'redis' if self.is_redis_enabled else 'memory'
            
            if self.is_redis_enabled:
                # Additional Redis-specific checks
                info = self.redis_client.info()
                health['redis_info'] = {
                    'version': info.get('redis_version'),
                    'uptime_seconds': info.get('uptime_in_seconds'),
                    'used_memory_mb': round(info.get('used_memory', 0) / (1024 * 1024), 2)
                }
            
            return health
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                'cache_available': False,
                'error': str(e),
                'cache_type': 'memory'
            }
    
    def _get_cache_key(self, key: str) -> str:
        """Generate cache key with prefix"""
        return f"{self.cache_prefix}{key}"
    
    def _create_api_cache_key(self, endpoint: str, params: Dict) -> str:
        """Create cache key for API endpoint with parameters"""
        params_hash = self._hash_dict(params)
        return f"api:{endpoint}:{params_hash}"
    
    def _hash_dict(self, data: Dict) -> str:
        """Create hash from dictionary for cache key"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for Redis storage"""
        try:
            if isinstance(value, (dict, list)):
                return json.dumps(value, default=str)
            else:
                return str(value)
        except Exception:
            # Fallback to pickle for complex objects
            return pickle.dumps(value).hex()
    
    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from Redis"""
        try:
            # Try JSON first
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            try:
                # Try pickle fallback
                return pickle.loads(bytes.fromhex(value))
            except Exception:
                # Return as string if all else fails
                return value
    
    def _is_expired(self, entry: Dict) -> bool:
        """Check if memory cache entry is expired"""
        import time
        return time.time() > entry.get('expires_at', 0)
    
    def _cleanup_memory_cache(self):
        """Clean up expired entries from memory cache"""
        import time
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if current_time > entry.get('expires_at', 0)
        ]
        for key in expired_keys:
            del self.memory_cache[key]

# Global cache instance
cache_service = RedisCacheService()