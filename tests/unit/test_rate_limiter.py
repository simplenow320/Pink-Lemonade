"""
Unit tests for RateLimiter functionality
Tests rate limiting behavior for different API sources
"""

import pytest
import time
from unittest.mock import patch

from app.services.apiManager import RateLimiter


class TestRateLimiter:
    """Test RateLimiter class functionality"""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes correctly"""
        rl = RateLimiter()
        assert rl.calls == {}
    
    def test_first_call_allowed(self):
        """Test first call to a source is allowed"""
        rl = RateLimiter()
        
        result = rl.check_rate_limit("test_source", max_calls=10, period_seconds=60)
        assert result is True
        assert "test_source" in rl.calls
        assert len(rl.calls["test_source"]) == 1
    
    def test_calls_within_limit_allowed(self):
        """Test calls within rate limit are allowed"""
        rl = RateLimiter()
        
        # Make calls within limit
        for i in range(5):
            result = rl.check_rate_limit("test_source", max_calls=10, period_seconds=60)
            assert result is True
        
        assert len(rl.calls["test_source"]) == 5
    
    def test_calls_exceeding_limit_blocked(self):
        """Test calls exceeding rate limit are blocked"""
        rl = RateLimiter()
        
        # Make calls up to limit
        for i in range(3):
            result = rl.check_rate_limit("test_source", max_calls=3, period_seconds=60)
            assert result is True
        
        # Next call should be blocked
        result = rl.check_rate_limit("test_source", max_calls=3, period_seconds=60)
        assert result is False
        
        # Should still have only 3 calls recorded (blocked call not added)
        assert len(rl.calls["test_source"]) == 3
    
    def test_old_calls_cleaned_up(self):
        """Test old calls are cleaned up after period expires"""
        rl = RateLimiter()
        
        # Mock time to control when calls are made
        with patch('time.time') as mock_time:
            # Initial time
            mock_time.return_value = 1000.0
            
            # Make calls
            for i in range(3):
                result = rl.check_rate_limit("test_source", max_calls=3, period_seconds=60)
                assert result is True
            
            # Move time forward past the period
            mock_time.return_value = 1070.0  # 70 seconds later
            
            # Should allow new call (old calls cleaned up)
            result = rl.check_rate_limit("test_source", max_calls=3, period_seconds=60)
            assert result is True
            
            # Should have only 1 call now (old ones cleaned up)
            assert len(rl.calls["test_source"]) == 1
    
    def test_partial_cleanup_of_old_calls(self):
        """Test partial cleanup when some calls are old and some are recent"""
        rl = RateLimiter()
        
        with patch('time.time') as mock_time:
            # Make some calls at time 1000
            mock_time.return_value = 1000.0
            for i in range(2):
                rl.check_rate_limit("test_source", max_calls=5, period_seconds=60)
            
            # Make more calls at time 1030 (within period)
            mock_time.return_value = 1030.0
            for i in range(2):
                rl.check_rate_limit("test_source", max_calls=5, period_seconds=60)
            
            # Check at time 1070 (old calls should be cleaned)
            mock_time.return_value = 1070.0
            result = rl.check_rate_limit("test_source", max_calls=5, period_seconds=60)
            
            assert result is True
            # Should have 2 recent calls + 1 new call = 3 total
            assert len(rl.calls["test_source"]) == 3
    
    def test_different_sources_tracked_separately(self):
        """Test different sources have separate rate limit tracking"""
        rl = RateLimiter()
        
        # Make calls to different sources
        for i in range(3):
            result1 = rl.check_rate_limit("source1", max_calls=3, period_seconds=60)
            result2 = rl.check_rate_limit("source2", max_calls=3, period_seconds=60)
            assert result1 is True
            assert result2 is True
        
        assert len(rl.calls["source1"]) == 3
        assert len(rl.calls["source2"]) == 3
        
        # Each source should be at its limit
        result1 = rl.check_rate_limit("source1", max_calls=3, period_seconds=60)
        result2 = rl.check_rate_limit("source2", max_calls=3, period_seconds=60)
        assert result1 is False
        assert result2 is False
    
    def test_different_rate_limits_per_source(self):
        """Test different sources can have different rate limits"""
        rl = RateLimiter()
        
        # Source1 has higher limit
        for i in range(5):
            result = rl.check_rate_limit("high_limit_source", max_calls=10, period_seconds=60)
            assert result is True
        
        # Source2 has lower limit
        for i in range(2):
            result = rl.check_rate_limit("low_limit_source", max_calls=2, period_seconds=60)
            assert result is True
        
        # High limit source should still allow calls
        result = rl.check_rate_limit("high_limit_source", max_calls=10, period_seconds=60)
        assert result is True
        
        # Low limit source should be blocked
        result = rl.check_rate_limit("low_limit_source", max_calls=2, period_seconds=60)
        assert result is False
    
    def test_zero_max_calls_blocks_all(self):
        """Test setting max_calls to 0 blocks all requests"""
        rl = RateLimiter()
        
        result = rl.check_rate_limit("blocked_source", max_calls=0, period_seconds=60)
        assert result is False
        assert len(rl.calls.get("blocked_source", [])) == 0
    
    def test_very_short_period(self):
        """Test rate limiting with very short periods"""
        rl = RateLimiter()
        
        # Make calls with 1-second period
        for i in range(2):
            result = rl.check_rate_limit("fast_source", max_calls=2, period_seconds=1)
            assert result is True
        
        # Should be blocked
        result = rl.check_rate_limit("fast_source", max_calls=2, period_seconds=1)
        assert result is False
        
        # Wait for period to expire
        time.sleep(1.1)
        
        # Should be allowed again
        result = rl.check_rate_limit("fast_source", max_calls=2, period_seconds=1)
        assert result is True
    
    def test_concurrent_access_simulation(self):
        """Test behavior that simulates concurrent access patterns"""
        rl = RateLimiter()
        
        # Simulate rapid sequential calls (like concurrent requests)
        results = []
        for i in range(10):
            result = rl.check_rate_limit("busy_source", max_calls=5, period_seconds=60)
            results.append(result)
        
        # First 5 should be True, rest False
        assert results[:5] == [True] * 5
        assert results[5:] == [False] * 5
    
    @pytest.mark.parametrize("max_calls,period,expected_allowed", [
        (1, 60, 1),     # Very restrictive
        (10, 60, 10),   # Moderate
        (100, 60, 100), # High limit
        (1000, 1, 1000), # High calls, short period
    ])
    def test_various_rate_limit_configurations(self, max_calls, period, expected_allowed):
        """Test various rate limit configurations"""
        rl = RateLimiter()
        
        allowed_count = 0
        for i in range(max_calls + 5):  # Try more than limit
            if rl.check_rate_limit("test_source", max_calls=max_calls, period_seconds=period):
                allowed_count += 1
        
        assert allowed_count == expected_allowed
    
    def test_edge_case_exactly_at_limit(self):
        """Test edge case when exactly at rate limit"""
        rl = RateLimiter()
        
        # Make exactly limit number of calls
        for i in range(5):
            result = rl.check_rate_limit("edge_source", max_calls=5, period_seconds=60)
            assert result is True
        
        # Next call should be blocked
        result = rl.check_rate_limit("edge_source", max_calls=5, period_seconds=60)
        assert result is False
        
        # Verify call count is exactly at limit
        assert len(rl.calls["edge_source"]) == 5
    
    def test_rate_limit_with_real_time_progression(self):
        """Test rate limiting with actual time progression"""
        rl = RateLimiter()
        
        # Use very short period for testing
        period = 0.1  # 100ms
        
        # Make calls up to limit
        for i in range(3):
            result = rl.check_rate_limit("time_test", max_calls=3, period_seconds=period)
            assert result is True
        
        # Should be blocked
        result = rl.check_rate_limit("time_test", max_calls=3, period_seconds=period)
        assert result is False
        
        # Wait for period to expire
        time.sleep(period + 0.01)
        
        # Should be allowed again
        result = rl.check_rate_limit("time_test", max_calls=3, period_seconds=period)
        assert result is True
    
    def test_memory_efficiency_with_many_sources(self):
        """Test memory efficiency when tracking many sources"""
        rl = RateLimiter()
        
        # Create many sources
        for i in range(100):
            source_name = f"source_{i}"
            result = rl.check_rate_limit(source_name, max_calls=1, period_seconds=60)
            assert result is True
        
        # Should have 100 sources tracked
        assert len(rl.calls) == 100
        
        # Each source should have 1 call
        for source_name, calls in rl.calls.items():
            assert len(calls) == 1
    
    def test_cleanup_efficiency(self):
        """Test that cleanup doesn't affect performance significantly"""
        rl = RateLimiter()
        
        with patch('time.time') as mock_time:
            # Add many old calls
            mock_time.return_value = 1000.0
            for i in range(50):
                rl.check_rate_limit("cleanup_test", max_calls=100, period_seconds=60)
            
            # Move time forward
            mock_time.return_value = 1070.0
            
            # New call should trigger cleanup
            result = rl.check_rate_limit("cleanup_test", max_calls=100, period_seconds=60)
            assert result is True
            
            # Should have only 1 call left (all old ones cleaned up)
            assert len(rl.calls["cleanup_test"]) == 1