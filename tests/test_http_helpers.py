"""
Unit tests for HTTP helper classes
"""
import os
import time
import unittest
from unittest.mock import patch
from app.services.http_helpers import RotatingKeyPool, SimpleCache


class TestRotatingKeyPool(unittest.TestCase):
    """Test RotatingKeyPool functionality"""
    
    def test_init_with_single_key(self):
        """Test initialization with single key"""
        with patch.dict(os.environ, {'TEST_KEYS': 'key1'}):
            pool = RotatingKeyPool('TEST_KEYS')
            self.assertEqual(pool.key_count(), 1)
            self.assertTrue(pool.has_keys())
    
    def test_init_with_multiple_keys(self):
        """Test initialization with multiple comma-separated keys"""
        with patch.dict(os.environ, {'TEST_KEYS': 'key1,key2,key3'}):
            pool = RotatingKeyPool('TEST_KEYS')
            self.assertEqual(pool.key_count(), 3)
            self.assertTrue(pool.has_keys())
    
    def test_init_with_spaces(self):
        """Test initialization handles spaces in key list"""
        with patch.dict(os.environ, {'TEST_KEYS': ' key1 , key2 , key3 '}):
            pool = RotatingKeyPool('TEST_KEYS')
            self.assertEqual(pool.key_count(), 3)
    
    def test_init_with_no_keys(self):
        """Test initialization with no keys raises error"""
        with patch.dict(os.environ, {'TEST_KEYS': ''}):
            with self.assertRaises(ValueError) as cm:
                RotatingKeyPool('TEST_KEYS')
            self.assertIn("No API keys found", str(cm.exception))
    
    def test_init_with_missing_env_var(self):
        """Test initialization with missing environment variable"""
        # Ensure env var doesn't exist
        if 'NONEXISTENT_KEYS' in os.environ:
            del os.environ['NONEXISTENT_KEYS']
        
        with self.assertRaises(ValueError) as cm:
            RotatingKeyPool('NONEXISTENT_KEYS')
        self.assertIn("No API keys found", str(cm.exception))
    
    def test_next_rotation(self):
        """Test key rotation works correctly"""
        with patch.dict(os.environ, {'TEST_KEYS': 'key1,key2,key3'}):
            pool = RotatingKeyPool('TEST_KEYS')
            
            # First rotation cycle
            self.assertEqual(pool.next(), 'key1')
            self.assertEqual(pool.next(), 'key2')
            self.assertEqual(pool.next(), 'key3')
            
            # Should wrap around
            self.assertEqual(pool.next(), 'key1')
            self.assertEqual(pool.next(), 'key2')
    
    def test_next_with_single_key(self):
        """Test next() with single key always returns same key"""
        with patch.dict(os.environ, {'TEST_KEYS': 'onlykey'}):
            pool = RotatingKeyPool('TEST_KEYS')
            
            self.assertEqual(pool.next(), 'onlykey')
            self.assertEqual(pool.next(), 'onlykey')
            self.assertEqual(pool.next(), 'onlykey')
    
    def test_on_unauthorized_or_rate_limit_multiple_keys(self):
        """Test error handling with multiple keys"""
        with patch.dict(os.environ, {'TEST_KEYS': 'key1,key2,key3'}):
            pool = RotatingKeyPool('TEST_KEYS')
            
            # Should return True when other keys are available
            self.assertTrue(pool.on_unauthorized_or_rate_limit())
    
    def test_on_unauthorized_or_rate_limit_single_key(self):
        """Test error handling with single key"""
        with patch.dict(os.environ, {'TEST_KEYS': 'onlykey'}):
            pool = RotatingKeyPool('TEST_KEYS')
            
            # Should return False when no alternatives
            self.assertFalse(pool.on_unauthorized_or_rate_limit())
    
    def test_retry_scenario(self):
        """Test typical retry scenario with multiple keys"""
        with patch.dict(os.environ, {'TEST_KEYS': 'key1,key2,key3'}):
            pool = RotatingKeyPool('TEST_KEYS')
            
            # First request fails, try next key
            first_key = pool.next()  # key1
            self.assertEqual(first_key, 'key1')
            
            # Simulate 401/429 error
            can_retry = pool.on_unauthorized_or_rate_limit()
            self.assertTrue(can_retry)
            
            # Next key should be different
            second_key = pool.next()  # key2 
            self.assertEqual(second_key, 'key2')
            self.assertNotEqual(first_key, second_key)


class TestSimpleCache(unittest.TestCase):
    """Test SimpleCache functionality"""
    
    def setUp(self):
        """Set up test cache"""
        self.cache = SimpleCache()
    
    def test_cache_miss(self):
        """Test cache miss returns None"""
        result = self.cache.get('GET', 'http://api.example.com/data')
        self.assertIsNone(result)
    
    def test_cache_hit(self):
        """Test cache hit returns stored data"""
        test_data = {'result': 'success'}
        self.cache.set('GET', 'http://api.example.com/data', test_data, ttl_seconds=60)
        
        result = self.cache.get('GET', 'http://api.example.com/data')
        self.assertEqual(result, test_data)
    
    def test_cache_expiration(self):
        """Test cache expiration removes data"""
        test_data = {'result': 'success'}
        # Set with very short TTL
        self.cache.set('GET', 'http://api.example.com/data', test_data, ttl_seconds=0.1)
        
        # Should be available immediately
        result = self.cache.get('GET', 'http://api.example.com/data')
        self.assertEqual(result, test_data)
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be expired and return None
        result = self.cache.get('GET', 'http://api.example.com/data')
        self.assertIsNone(result)
    
    def test_cache_with_params(self):
        """Test cache works with parameters"""
        params1 = {'page': 1, 'limit': 10}
        params2 = {'page': 2, 'limit': 10}
        
        data1 = {'page': 1, 'results': ['a', 'b']}
        data2 = {'page': 2, 'results': ['c', 'd']}
        
        # Store data with different params
        self.cache.set('GET', 'http://api.example.com/data', data1, 60, params1)
        self.cache.set('GET', 'http://api.example.com/data', data2, 60, params2)
        
        # Should get correct data for each param set
        result1 = self.cache.get('GET', 'http://api.example.com/data', params1)
        result2 = self.cache.get('GET', 'http://api.example.com/data', params2)
        
        self.assertEqual(result1, data1)
        self.assertEqual(result2, data2)
    
    def test_cache_key_normalization(self):
        """Test cache keys are normalized consistently"""
        params_ordered = {'a': 1, 'b': 2}
        params_unordered = {'b': 2, 'a': 1}
        
        test_data = {'result': 'success'}
        
        # Store with one param order
        self.cache.set('GET', 'http://api.example.com/data', test_data, 60, params_ordered)
        
        # Should get same data with different param order
        result = self.cache.get('GET', 'http://api.example.com/data', params_unordered)
        self.assertEqual(result, test_data)
    
    def test_method_case_normalization(self):
        """Test HTTP method case is normalized"""
        test_data = {'result': 'success'}
        
        # Store with lowercase method
        self.cache.set('get', 'http://api.example.com/data', test_data, 60)
        
        # Should get same data with uppercase method
        result = self.cache.get('GET', 'http://api.example.com/data')
        self.assertEqual(result, test_data)
    
    def test_cache_clear(self):
        """Test cache clear removes all data"""
        self.cache.set('GET', 'http://api.example.com/data1', {'data': 1}, 60)
        self.cache.set('POST', 'http://api.example.com/data2', {'data': 2}, 60)
        
        self.assertEqual(self.cache.size(), 2)
        
        self.cache.clear()
        self.assertEqual(self.cache.size(), 0)
        
        result = self.cache.get('GET', 'http://api.example.com/data1')
        self.assertIsNone(result)
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries"""
        # Add entries with different TTLs
        self.cache.set('GET', 'http://api.example.com/data1', {'data': 1}, 0.1)
        self.cache.set('GET', 'http://api.example.com/data2', {'data': 2}, 60)
        
        self.assertEqual(self.cache.size(), 2)
        
        # Wait for first entry to expire
        time.sleep(0.2)
        
        # Cleanup expired entries
        removed_count = self.cache.cleanup_expired()
        self.assertEqual(removed_count, 1)
        self.assertEqual(self.cache.size(), 1)
        
        # Non-expired entry should still be there
        result = self.cache.get('GET', 'http://api.example.com/data2')
        self.assertEqual(result, {'data': 2})


if __name__ == '__main__':
    unittest.main()