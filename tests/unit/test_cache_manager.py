"""
Unit tests for CacheManager functionality
Tests caching behavior for API responses
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch

from app.services.apiManager import CacheManager


class TestCacheManager:
    """Test CacheManager class functionality"""
    
    def test_cache_manager_initialization(self):
        """Test cache manager initializes correctly"""
        cm = CacheManager()
        assert cm.cache == {}
    
    def test_cache_key_generation(self):
        """Test cache key generation from source and params"""
        cm = CacheManager()
        
        # Same source and params should generate same key
        key1 = cm.get_cache_key("test_source", {"param1": "value1", "param2": "value2"})
        key2 = cm.get_cache_key("test_source", {"param1": "value1", "param2": "value2"})
        assert key1 == key2
        
        # Different params should generate different keys
        key3 = cm.get_cache_key("test_source", {"param1": "different", "param2": "value2"})
        assert key1 != key3
        
        # Different source should generate different keys
        key4 = cm.get_cache_key("different_source", {"param1": "value1", "param2": "value2"})
        assert key1 != key4
    
    def test_cache_key_param_order_independence(self):
        """Test cache key is independent of parameter order"""
        cm = CacheManager()
        
        key1 = cm.get_cache_key("test_source", {"a": 1, "b": 2, "c": 3})
        key2 = cm.get_cache_key("test_source", {"c": 3, "a": 1, "b": 2})
        key3 = cm.get_cache_key("test_source", {"b": 2, "c": 3, "a": 1})
        
        assert key1 == key2 == key3
    
    def test_cache_set_and_get_basic(self):
        """Test basic cache set and get operations"""
        cm = CacheManager()
        
        test_data = {"result": "test_value", "count": 42}
        params = {"query": "test"}
        
        # Set data in cache
        cm.set("test_source", params, test_data)
        
        # Get data from cache
        cached_data = cm.get("test_source", params)
        assert cached_data == test_data
    
    def test_cache_miss_returns_none(self):
        """Test cache miss returns None"""
        cm = CacheManager()
        
        # Try to get non-existent data
        cached_data = cm.get("nonexistent_source", {"param": "value"})
        assert cached_data is None
    
    def test_cache_expiration(self):
        """Test cache expiration after max_age"""
        cm = CacheManager()
        
        test_data = {"result": "test_value"}
        params = {"query": "test"}
        
        with patch('app.services.apiManager.datetime') as mock_datetime:
            # Set initial time
            initial_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = initial_time
            
            # Set data in cache
            cm.set("test_source", params, test_data)
            
            # Get data immediately (should hit)
            cached_data = cm.get("test_source", params, max_age_minutes=60)
            assert cached_data == test_data
            
            # Move time forward past expiration
            expired_time = initial_time + timedelta(minutes=61)
            mock_datetime.now.return_value = expired_time
            
            # Get data after expiration (should miss)
            cached_data = cm.get("test_source", params, max_age_minutes=60)
            assert cached_data is None
    
    def test_cache_within_expiration_time(self):
        """Test cache hit within expiration time"""
        cm = CacheManager()
        
        test_data = {"result": "test_value"}
        params = {"query": "test"}
        
        with patch('app.services.apiManager.datetime') as mock_datetime:
            # Set initial time
            initial_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = initial_time
            
            # Set data in cache
            cm.set("test_source", params, test_data)
            
            # Move time forward but within expiration
            later_time = initial_time + timedelta(minutes=30)
            mock_datetime.now.return_value = later_time
            
            # Get data (should still hit)
            cached_data = cm.get("test_source", params, max_age_minutes=60)
            assert cached_data == test_data
    
    def test_different_max_age_values(self):
        """Test different max_age values affect expiration"""
        cm = CacheManager()
        
        test_data = {"result": "test_value"}
        params = {"query": "test"}
        
        with patch('app.services.apiManager.datetime') as mock_datetime:
            # Set initial time
            initial_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = initial_time
            
            # Set data in cache
            cm.set("test_source", params, test_data)
            
            # Move time forward 30 minutes
            later_time = initial_time + timedelta(minutes=30)
            mock_datetime.now.return_value = later_time
            
            # Get with long max_age (should hit)
            cached_data = cm.get("test_source", params, max_age_minutes=60)
            assert cached_data == test_data
            
            # Get with short max_age (should miss)
            cached_data = cm.get("test_source", params, max_age_minutes=15)
            assert cached_data is None
    
    def test_cache_different_sources_isolated(self):
        """Test different sources have isolated cache entries"""
        cm = CacheManager()
        
        params = {"query": "test"}
        data1 = {"source": "source1"}
        data2 = {"source": "source2"}
        
        # Set data for different sources
        cm.set("source1", params, data1)
        cm.set("source2", params, data2)
        
        # Get data for each source
        cached_data1 = cm.get("source1", params)
        cached_data2 = cm.get("source2", params)
        
        assert cached_data1 == data1
        assert cached_data2 == data2
        assert cached_data1 != cached_data2
    
    def test_cache_different_params_isolated(self):
        """Test different parameters have isolated cache entries"""
        cm = CacheManager()
        
        source = "test_source"
        params1 = {"query": "test1"}
        params2 = {"query": "test2"}
        data1 = {"result": "result1"}
        data2 = {"result": "result2"}
        
        # Set data for different params
        cm.set(source, params1, data1)
        cm.set(source, params2, data2)
        
        # Get data for each param set
        cached_data1 = cm.get(source, params1)
        cached_data2 = cm.get(source, params2)
        
        assert cached_data1 == data1
        assert cached_data2 == data2
        assert cached_data1 != cached_data2
    
    def test_cache_overwrite_same_key(self):
        """Test cache overwrites data for same key"""
        cm = CacheManager()
        
        source = "test_source"
        params = {"query": "test"}
        original_data = {"result": "original"}
        new_data = {"result": "updated"}
        
        # Set original data
        cm.set(source, params, original_data)
        cached_data = cm.get(source, params)
        assert cached_data == original_data
        
        # Overwrite with new data
        cm.set(source, params, new_data)
        cached_data = cm.get(source, params)
        assert cached_data == new_data
        assert cached_data != original_data
    
    def test_cache_complex_data_types(self):
        """Test caching complex data types"""
        cm = CacheManager()
        
        complex_data = {
            "grants": [
                {"id": 1, "title": "Grant 1", "tags": ["education", "youth"]},
                {"id": 2, "title": "Grant 2", "tags": ["health", "community"]}
            ],
            "metadata": {
                "total": 2,
                "page": 1,
                "timestamp": "2025-01-01T12:00:00Z"
            },
            "nested": {
                "level1": {
                    "level2": {
                        "value": "deep_value"
                    }
                }
            }
        }
        
        params = {"query": "complex"}
        
        # Set and get complex data
        cm.set("test_source", params, complex_data)
        cached_data = cm.get("test_source", params)
        
        assert cached_data == complex_data
        assert cached_data["grants"][0]["tags"] == ["education", "youth"]
        assert cached_data["nested"]["level1"]["level2"]["value"] == "deep_value"
    
    def test_cache_none_values(self):
        """Test caching None values"""
        cm = CacheManager()
        
        params = {"query": "test"}
        
        # Set None value
        cm.set("test_source", params, None)
        cached_data = cm.get("test_source", params)
        
        assert cached_data is None
        
        # Ensure it's actually cached (not a cache miss)
        key = cm.get_cache_key("test_source", params)
        assert key in cm.cache
    
    def test_cache_empty_collections(self):
        """Test caching empty collections"""
        cm = CacheManager()
        
        empty_data_types = [
            [],  # empty list
            {},  # empty dict
            "",  # empty string
            set(),  # empty set (will be converted in serialization)
        ]
        
        for i, empty_data in enumerate(empty_data_types):
            params = {"query": f"empty_{i}"}
            
            cm.set("test_source", params, empty_data)
            cached_data = cm.get("test_source", params)
            
            assert cached_data == empty_data
    
    def test_cache_key_hash_consistency(self):
        """Test cache key hash consistency across multiple generations"""
        cm = CacheManager()
        
        params = {"query": "test", "limit": 10, "sort": "date"}
        
        # Generate key multiple times
        keys = [cm.get_cache_key("test_source", params) for _ in range(10)]
        
        # All keys should be identical
        assert all(key == keys[0] for key in keys)
        
        # Keys should be strings
        assert all(isinstance(key, str) for key in keys)
        
        # Keys should be reasonable length (MD5 hash = 32 chars)
        assert all(len(key) == 32 for key in keys)
    
    def test_cache_param_types_handled(self):
        """Test cache handles different parameter value types"""
        cm = CacheManager()
        
        param_sets = [
            {"string": "value", "int": 123, "float": 45.67},
            {"bool": True, "none": None, "list": [1, 2, 3]},
            {"dict": {"nested": "value"}, "tuple": (1, 2, 3)},
        ]
        
        for i, params in enumerate(param_sets):
            data = {"test": f"data_{i}"}
            
            # Should not raise exceptions
            cm.set("test_source", params, data)
            cached_data = cm.get("test_source", params)
            
            assert cached_data == data
    
    @pytest.mark.parametrize("max_age_minutes", [1, 30, 60, 120, 1440])
    def test_various_expiration_times(self, max_age_minutes):
        """Test various cache expiration times"""
        cm = CacheManager()
        
        test_data = {"result": f"data_for_{max_age_minutes}_minutes"}
        params = {"query": "test"}
        
        with patch('app.services.apiManager.datetime') as mock_datetime:
            # Set initial time
            initial_time = datetime(2025, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = initial_time
            
            # Set data in cache
            cm.set("test_source", params, test_data)
            
            # Move time forward to just before expiration
            almost_expired_time = initial_time + timedelta(minutes=max_age_minutes - 1)
            mock_datetime.now.return_value = almost_expired_time
            
            # Should still be cached
            cached_data = cm.get("test_source", params, max_age_minutes=max_age_minutes)
            assert cached_data == test_data
            
            # Move time forward past expiration
            expired_time = initial_time + timedelta(minutes=max_age_minutes + 1)
            mock_datetime.now.return_value = expired_time
            
            # Should be expired
            cached_data = cm.get("test_source", params, max_age_minutes=max_age_minutes)
            assert cached_data is None
    
    def test_cache_performance_with_many_entries(self):
        """Test cache performance doesn't degrade with many entries"""
        cm = CacheManager()
        
        # Add many cache entries
        for i in range(1000):
            source = f"source_{i % 10}"  # 10 different sources
            params = {"query": f"query_{i}"}
            data = {"result": f"data_{i}"}
            
            cm.set(source, params, data)
        
        # Verify cache has entries
        assert len(cm.cache) == 1000
        
        # Test retrieval performance (should be fast)
        start_time = time.time()
        for i in range(100):
            params = {"query": f"query_{i}"}
            cached_data = cm.get(f"source_{i % 10}", params)
            assert cached_data is not None
        
        elapsed_time = time.time() - start_time
        # Should complete quickly (less than 1 second for 100 retrievals)
        assert elapsed_time < 1.0