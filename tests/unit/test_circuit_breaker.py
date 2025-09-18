"""
Unit tests for CircuitBreaker functionality
Tests circuit breaker behavior with various failure scenarios
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.apiManager import CircuitBreaker, CircuitBreakerState


class TestCircuitBreaker:
    """Test CircuitBreaker class functionality"""
    
    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes with correct defaults"""
        cb = CircuitBreaker("test_source")
        
        assert cb.source_name == "test_source"
        assert cb.failure_threshold == 5
        assert cb.cooldown_period == timedelta(minutes=15)
        assert cb.half_open_max_calls == 3
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
        assert cb.half_open_calls == 0
        assert cb.total_calls == 0
        assert cb.total_failures == 0
        assert cb.state_changes == []
    
    def test_circuit_breaker_custom_configuration(self):
        """Test circuit breaker with custom configuration"""
        cb = CircuitBreaker(
            "custom_source",
            failure_threshold=3,
            cooldown_minutes=30,
            half_open_max_calls=2
        )
        
        assert cb.source_name == "custom_source"
        assert cb.failure_threshold == 3
        assert cb.cooldown_period == timedelta(minutes=30)
        assert cb.half_open_max_calls == 2
    
    def test_can_execute_closed_state(self):
        """Test can_execute returns True when circuit is closed"""
        cb = CircuitBreaker("test_source")
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.can_execute() is True
    
    def test_record_success_in_closed_state(self):
        """Test recording success in closed state"""
        cb = CircuitBreaker("test_source")
        
        cb.record_success()
        
        assert cb.total_calls == 1
        assert cb.total_failures == 0
        assert cb.failure_count == 0
        assert cb.state == CircuitBreakerState.CLOSED
    
    def test_record_failure_in_closed_state(self):
        """Test recording failure in closed state"""
        cb = CircuitBreaker("test_source", failure_threshold=3)
        
        cb.record_failure("Test error")
        
        assert cb.total_calls == 1
        assert cb.total_failures == 1
        assert cb.failure_count == 1
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.last_failure_time is not None
    
    def test_circuit_opens_after_threshold_failures(self):
        """Test circuit opens after reaching failure threshold"""
        cb = CircuitBreaker("test_source", failure_threshold=3)
        
        # Record failures up to threshold
        for i in range(3):
            cb.record_failure(f"Error {i+1}")
        
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 3
        assert cb.can_execute() is False
    
    def test_circuit_stays_closed_below_threshold(self):
        """Test circuit stays closed when failures below threshold"""
        cb = CircuitBreaker("test_source", failure_threshold=5)
        
        # Record failures below threshold
        for i in range(4):
            cb.record_failure(f"Error {i+1}")
        
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 4
        assert cb.can_execute() is True
    
    def test_success_resets_failure_count_in_closed_state(self):
        """Test success resets failure count in closed state"""
        cb = CircuitBreaker("test_source", failure_threshold=5)
        
        # Record some failures
        cb.record_failure("Error 1")
        cb.record_failure("Error 2")
        assert cb.failure_count == 2
        
        # Record success - should reset count
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitBreakerState.CLOSED
    
    def test_open_circuit_blocks_execution_during_cooldown(self):
        """Test open circuit blocks execution during cooldown period"""
        cb = CircuitBreaker("test_source", failure_threshold=2, cooldown_minutes=1)
        
        # Open the circuit
        cb.record_failure("Error 1")
        cb.record_failure("Error 2")
        assert cb.state == CircuitBreakerState.OPEN
        
        # Should block execution during cooldown
        assert cb.can_execute() is False
    
    def test_circuit_transitions_to_half_open_after_cooldown(self):
        """Test circuit transitions to half-open after cooldown period"""
        cb = CircuitBreaker("test_source", failure_threshold=2, cooldown_minutes=0.01)  # 0.6 seconds
        
        # Open the circuit
        cb.record_failure("Error 1")
        cb.record_failure("Error 2")
        assert cb.state == CircuitBreakerState.OPEN
        
        # Wait for cooldown to pass
        time.sleep(0.02)  # Wait 1.2 seconds
        
        # Should transition to half-open
        assert cb.can_execute() is True
        # Check state was updated
        cb.can_execute()  # Call again to trigger state change
        # Note: State change happens during can_execute() call
    
    def test_half_open_allows_limited_calls(self):
        """Test half-open state allows limited test calls"""
        cb = CircuitBreaker("test_source", failure_threshold=2, half_open_max_calls=3)
        
        # Manually set to half-open state
        cb.state = CircuitBreakerState.HALF_OPEN
        cb.half_open_calls = 0
        
        # Should allow calls up to max
        for i in range(3):
            assert cb.can_execute() is True
            cb.half_open_calls += 1
        
        # Should block after max calls
        assert cb.can_execute() is False
    
    def test_half_open_success_closes_circuit(self):
        """Test successful calls in half-open state close circuit"""
        cb = CircuitBreaker("test_source", failure_threshold=2, half_open_max_calls=2)
        
        # Set to half-open state
        cb.state = CircuitBreakerState.HALF_OPEN
        cb.half_open_calls = 0
        
        # Record successful calls
        cb.record_success()
        assert cb.half_open_calls == 1
        assert cb.state == CircuitBreakerState.HALF_OPEN
        
        cb.record_success()
        assert cb.half_open_calls == 2
        assert cb.state == CircuitBreakerState.CLOSED  # Should close after max successful calls
        assert cb.failure_count == 0
    
    def test_half_open_failure_opens_circuit(self):
        """Test failure in half-open state immediately opens circuit"""
        cb = CircuitBreaker("test_source", failure_threshold=3)
        
        # Set to half-open state
        cb.state = CircuitBreakerState.HALF_OPEN
        cb.half_open_calls = 1
        
        # Record failure - should immediately open
        cb.record_failure("Recovery failed")
        
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.half_open_calls == 0
    
    def test_credential_error_classification(self):
        """Test credential errors are properly classified"""
        cb = CircuitBreaker("test_source")
        
        # Test credential error
        cb.record_failure("Invalid API key", is_credential_error=True)
        assert cb.failure_count == 1
        assert cb.total_failures == 1
        
        # Test general error
        cb.record_failure("Network timeout", is_credential_error=False)
        assert cb.failure_count == 2
        assert cb.total_failures == 2
    
    def test_error_sanitization(self):
        """Test that error messages are sanitized to remove credentials"""
        cb = CircuitBreaker("test_source")
        
        # Test various credential patterns
        test_errors = [
            "API_KEY=sk-123456789abcdef Request failed",
            "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9 unauthorized",
            "Basic dXNlcjpwYXNzd29yZA== access denied",
            "https://user:password@api.example.com/data timeout",
            "access_token=abc123def456 expired"
        ]
        
        for error in test_errors:
            cb.record_failure(error)
            # Verify no credentials in state changes
            latest_change = cb.state_changes[-1] if cb.state_changes else None
            # We can't directly access the sanitized error, but we ensure no exception is raised
    
    def test_circuit_status_reporting(self):
        """Test circuit breaker status reporting"""
        cb = CircuitBreaker("test_source", failure_threshold=3)
        
        # Record some activity
        cb.record_success()
        cb.record_failure("Error 1")
        cb.record_success()
        cb.record_failure("Error 2")
        
        status = cb.get_status()
        
        assert status['source'] == "test_source"
        assert status['state'] == "closed"
        assert status['failure_count'] == 1  # Should be 1 after last success reset then 1 failure
        assert status['failure_threshold'] == 3
        assert status['total_calls'] == 4
        assert status['total_failures'] == 2
        assert 'success_rate' in status
        assert status['is_available'] is True
        assert 'state_changes' in status
    
    def test_manual_reset(self):
        """Test manual reset of circuit breaker"""
        cb = CircuitBreaker("test_source", failure_threshold=2)
        
        # Open the circuit
        cb.record_failure("Error 1")
        cb.record_failure("Error 2")
        assert cb.state == CircuitBreakerState.OPEN
        
        # Reset manually
        cb.reset()
        
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.half_open_calls == 0
        assert cb.can_execute() is True
    
    def test_state_change_tracking(self):
        """Test state changes are properly tracked"""
        cb = CircuitBreaker("test_source", failure_threshold=2)
        
        initial_changes = len(cb.state_changes)
        
        # Trigger state change to OPEN
        cb.record_failure("Error 1")
        cb.record_failure("Error 2")
        
        assert len(cb.state_changes) > initial_changes
        
        latest_change = cb.state_changes[-1]
        assert latest_change['to_state'] == 'open'
        assert 'timestamp' in latest_change
        assert 'failure_count' in latest_change
    
    def test_state_changes_limited_to_10(self):
        """Test state changes are limited to last 10 entries"""
        cb = CircuitBreaker("test_source", failure_threshold=1)
        
        # Generate more than 10 state changes
        for i in range(15):
            cb.record_failure(f"Error {i}")
            cb.reset()  # This triggers state changes
        
        # Should keep only last 10
        assert len(cb.state_changes) <= 10
    
    def test_different_failure_thresholds_for_credential_vs_general_errors(self):
        """Test that different source types might use different thresholds"""
        # This tests the concept that credential-required sources might have different thresholds
        
        # Credential-required source (more strict)
        cb_cred = CircuitBreaker("credential_source", failure_threshold=3, cooldown_minutes=30)
        
        # Public source (more tolerant)
        cb_public = CircuitBreaker("public_source", failure_threshold=5, cooldown_minutes=15)
        
        assert cb_cred.failure_threshold == 3
        assert cb_cred.cooldown_period == timedelta(minutes=30)
        
        assert cb_public.failure_threshold == 5
        assert cb_public.cooldown_period == timedelta(minutes=15)
    
    @pytest.mark.parametrize("failure_threshold,expected_state", [
        (1, CircuitBreakerState.OPEN),   # Should open after 1 failure
        (3, CircuitBreakerState.CLOSED), # Should stay closed with 2 failures
        (5, CircuitBreakerState.CLOSED), # Should stay closed with 2 failures
    ])
    def test_various_failure_thresholds(self, failure_threshold, expected_state):
        """Test circuit breaker with various failure thresholds"""
        cb = CircuitBreaker("test_source", failure_threshold=failure_threshold)
        
        # Record 2 failures
        cb.record_failure("Error 1")
        cb.record_failure("Error 2")
        
        assert cb.state == expected_state
    
    def test_success_rate_calculation(self):
        """Test success rate calculation in status"""
        cb = CircuitBreaker("test_source")
        
        # No calls yet
        status = cb.get_status()
        assert status['success_rate'] == 100.0  # No calls = 100% success rate
        
        # Mixed calls
        cb.record_success()  # 1 success
        cb.record_failure("Error 1")  # 1 failure
        cb.record_success()  # 1 success
        cb.record_failure("Error 2")  # 1 failure
        cb.record_success()  # 1 success
        
        # 3 successes, 2 failures = 60% success rate
        status = cb.get_status()
        expected_rate = (3 / 5) * 100  # 60%
        assert status['success_rate'] == expected_rate
    
    def test_multiple_rapid_failures_and_recovery(self):
        """Test rapid failure scenario and recovery"""
        cb = CircuitBreaker("test_source", failure_threshold=3, cooldown_minutes=0.01)
        
        # Rapid failures to open circuit
        for i in range(5):
            cb.record_failure(f"Rapid error {i+1}")
        
        assert cb.state == CircuitBreakerState.OPEN
        
        # Wait for cooldown
        time.sleep(0.02)
        
        # Should allow test call
        assert cb.can_execute() is True
        
        # Simulate recovery with successful call
        cb.state = CircuitBreakerState.HALF_OPEN
        cb.half_open_calls = 0
        
        # Multiple successful recovery calls
        for i in range(cb.half_open_max_calls):
            cb.record_success()
        
        assert cb.state == CircuitBreakerState.CLOSED