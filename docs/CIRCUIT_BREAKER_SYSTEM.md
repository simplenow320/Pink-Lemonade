# Circuit Breaker System Documentation

## Overview

The APIManager includes a robust circuit breaker system that provides resilience and fault tolerance for all external API integrations. The circuit breaker prevents cascading failures, protects against credential-related issues, and ensures graceful degradation when API sources are unavailable.

## Key Features

### ✅ Implemented Features

- **Automatic Failure Detection**: Monitors API calls and detects various failure types (credential, rate limit, general errors)
- **Configurable Thresholds**: Different failure thresholds for credential-required vs public APIs
- **State Management**: Three-state circuit breaker (Closed, Open, Half-Open) with automatic transitions
- **Cooldown Periods**: Configurable cooldown periods before attempting recovery
- **Credential-Safe Logging**: Error sanitization that removes sensitive information from logs
- **Automatic Recovery Testing**: Half-open state allows limited calls to test service recovery
- **Graceful Degradation**: System continues operating with available sources when others fail
- **Real-time Monitoring**: Comprehensive status reporting and statistics tracking
- **Manual Reset Capability**: Administrative ability to manually reset circuit breakers

## How It Works

### Circuit Breaker States

```
┌─────────────────────────────────────────────────────────────────┐
│                    CIRCUIT BREAKER STATES                      │
├─────────────┬─────────────────────────────────────────────────┤
│   CLOSED    │ ✅ Normal operation - all calls allowed         │
│             │ • Tracks failure count                          │
│             │ • Resets failures on success                   │
│             │ • Opens when failure threshold reached          │
├─────────────┼─────────────────────────────────────────────────┤
│    OPEN     │ 🚫 Circuit breaker protecting system            │
│             │ • All calls blocked                             │
│             │ • Waits for cooldown period                     │
│             │ • Transitions to Half-Open after cooldown      │
├─────────────┼─────────────────────────────────────────────────┤
│  HALF-OPEN  │ 🔄 Testing if service has recovered             │
│             │ • Limited test calls allowed                    │
│             │ • Closes on successful test calls              │
│             │ • Opens immediately on any failure             │
└─────────────┴─────────────────────────────────────────────────┘
```

### State Transitions

```mermaid
stateDiagram-v2
    [*] --> Closed
    Closed --> Open : Failure threshold reached
    Open --> HalfOpen : Cooldown period expired
    HalfOpen --> Closed : Test calls successful
    HalfOpen --> Open : Any test call fails
    Open --> Closed : Manual reset
    Closed --> Closed : Successful calls reset failure count
```

### Configuration Parameters

| Parameter | Credential APIs | Public APIs | Description |
|-----------|----------------|-------------|-------------|
| **Failure Threshold** | 3 failures | 5 failures | Number of consecutive failures before opening |
| **Cooldown Period** | 30 minutes | 15 minutes | Time to wait before recovery testing |
| **Test Calls** | 2 calls | 2 calls | Number of test calls in half-open state |

## Error Classification

The system automatically classifies errors into different types:

### Credential Errors (High Priority)
- HTTP 401 Unauthorized
- HTTP 403 Forbidden
- "invalid_grant", "access_denied"
- "invalid_token", "authentication failed"
- "invalid_client", "invalid credentials"

### Rate Limit Errors (Medium Priority)
- HTTP 429 Too Many Requests
- "rate limit", "quota exceeded"
- "throttled", "rate exceeded"

### General Errors (Lower Priority)
- Connection timeouts
- Network errors
- Server errors (500, 502, 503, 504)

## API Usage

### Basic Usage

```python
from app.services.apiManager import APIManager

# Initialize API Manager with circuit breakers
api_manager = APIManager()

# Make API calls - circuit breaker protection is automatic
grants = api_manager.get_grants_from_source('grants_gov', {'query': 'nonprofit'})
```

### Monitoring Circuit Breakers

```python
# Get status for all circuit breakers
all_status = api_manager.get_circuit_breaker_status()

# Get status for specific source
status = api_manager.get_circuit_breaker_status('grants_gov')
print(f"State: {status['state']}")
print(f"Failures: {status['failure_count']}/{status['failure_threshold']}")
print(f"Success Rate: {status['success_rate']:.1f}%")

# Get summary of all circuit breakers
summary = api_manager.get_circuit_breaker_summary()
print(f"Open circuits: {summary['open_circuits']}")
print(f"Overall success rate: {summary['overall_success_rate']:.1f}%")
```

### Manual Management

```python
# Manually reset a circuit breaker
success = api_manager.reset_circuit_breaker('grants_gov')

# Check if a source is available (circuit not open)
circuit_breaker = api_manager.circuit_breakers['grants_gov']
if circuit_breaker.can_execute():
    # Safe to make API call
    grants = api_manager.get_grants_from_source('grants_gov')
```

## Security Features

### Credential-Safe Error Logging

The system automatically sanitizes error messages to prevent credential exposure:

```python
# Original error might contain:
"HTTP 401: Invalid API-KEY sk-1234567890abcdef"

# Sanitized error logged as:
"HTTP 401: Invalid API_KEY=[REDACTED]"
```

**Sanitization Patterns:**
- API keys: `API_KEY=[REDACTED]`
- Bearer tokens: `Bearer [REDACTED]`
- Basic auth: `Basic [REDACTED]`
- URLs with credentials: `https://[USER]:[PASS]@api.example.com`
- Access tokens: `access_token=[REDACTED]`

## Monitoring and Alerting

### Status Response Example

```json
{
  "source": "grants_gov",
  "state": "closed",
  "failure_count": 0,
  "failure_threshold": 5,
  "total_calls": 42,
  "total_failures": 2,
  "success_rate": 95.2,
  "last_failure_time": "2025-09-18T10:30:15.123Z",
  "cooldown_period_minutes": 15.0,
  "is_available": true,
  "state_changes": [
    {
      "timestamp": "2025-09-18T10:30:15.123Z",
      "from_state": "half_open",
      "to_state": "closed",
      "failure_count": 0
    }
  ]
}
```

### Key Metrics to Monitor

1. **Circuit State Distribution**
   - Number of open/closed/half-open circuits
   - Sources with frequent state changes

2. **Failure Rates**
   - Overall system success rate
   - Individual source success rates
   - Failure classification breakdown

3. **Recovery Patterns**
   - Average time circuits stay open
   - Success rate of recovery attempts
   - Manual reset frequency

## Integration with Existing Systems

### Startup Behavior

1. **Credential Detection**: APIConfig detects missing credentials at startup
2. **Source Disabling**: Sources without required credentials are disabled
3. **Circuit Breaker Init**: Circuit breakers are created for all enabled sources
4. **Logging**: Clear logging indicates which sources are available

### Runtime Behavior

1. **Graceful Degradation**: System continues with available sources
2. **Automatic Recovery**: Circuit breakers automatically test recovery
3. **No Data Fabrication**: Always returns empty results on failure (never fake data)
4. **Cache Integration**: Successful responses are cached to reduce API calls

## Best Practices

### For Developers

1. **Always Check Results**: Handle empty result sets gracefully
2. **Monitor Logs**: Watch for circuit breaker state changes
3. **Use Status APIs**: Implement dashboards using circuit breaker status
4. **Handle Degraded State**: Provide user feedback when sources are unavailable

### For Operations

1. **Set Up Monitoring**: Alert on circuit breaker state changes
2. **Regular Health Checks**: Monitor overall system success rates
3. **Credential Management**: Ensure API credentials are valid and current
4. **Manual Intervention**: Use reset capabilities during maintenance

## Configuration Examples

### Standard Configuration (Current)

```python
# Credential-required sources
CircuitBreaker(
    source_name="candid",
    failure_threshold=3,     # Fail fast for auth issues
    cooldown_minutes=30,     # Longer cooldown for credential issues
    half_open_max_calls=2    # Conservative recovery testing
)

# Public APIs
CircuitBreaker(
    source_name="grants_gov",
    failure_threshold=5,     # More tolerant for public APIs
    cooldown_minutes=15,     # Shorter cooldown for general issues
    half_open_max_calls=2    # Conservative recovery testing
)
```

### Custom Configuration Examples

```python
# High-traffic, critical source
CircuitBreaker(
    source_name="critical_api",
    failure_threshold=10,    # Very tolerant
    cooldown_minutes=5,      # Quick recovery
    half_open_max_calls=5    # More thorough testing
)

# Unreliable external service
CircuitBreaker(
    source_name="unreliable_api",
    failure_threshold=2,     # Fail fast
    cooldown_minutes=60,     # Long cooldown
    half_open_max_calls=1    # Minimal testing
)
```

## Testing

### Automated Testing

The system includes comprehensive tests (`test_circuit_breaker.py`):

1. **Initialization Tests**: Verify proper setup
2. **Success Tracking**: Test success recording
3. **Failure Simulation**: Test various failure scenarios
4. **State Transitions**: Verify correct state changes
5. **Error Sanitization**: Test credential safety
6. **Recovery Testing**: Test automatic recovery

### Manual Testing

```bash
# Run comprehensive circuit breaker tests
python test_circuit_breaker.py

# Test specific scenarios
python -c "
from app.services.apiManager import APIManager
api = APIManager()
print(api.get_circuit_breaker_summary())
"
```

## Troubleshooting

### Common Issues

1. **Circuit Breaker Not Opening**
   - Check error classification in `_is_credential_error()` and `_is_rate_limit_error()`
   - Verify failure threshold configuration
   - Check logs for actual vs expected error types

2. **False Positives**
   - Review error classification patterns
   - Adjust failure thresholds if needed
   - Check for network connectivity issues

3. **Slow Recovery**
   - Review cooldown period settings
   - Check if test calls are succeeding
   - Verify API service is actually recovered

### Debug Commands

```python
# Check current state of all circuit breakers
api_manager = APIManager()
for source, status in api_manager.get_circuit_breaker_status().items():
    print(f"{source}: {status['state']} ({status['failure_count']} failures)")

# Force reset problematic circuit breaker
api_manager.reset_circuit_breaker('problematic_source')

# Check detailed failure history
status = api_manager.get_circuit_breaker_status('source_name')
print(f"Recent state changes: {status['state_changes']}")
```

## Future Enhancements

### Potential Improvements

1. **Persistence**: Store circuit breaker state across restarts
2. **Metrics Integration**: Export metrics to monitoring systems
3. **Dynamic Configuration**: Allow runtime parameter changes
4. **Adaptive Thresholds**: Self-adjusting thresholds based on patterns
5. **Bulkhead Pattern**: Isolate different failure types
6. **Circuit Breaker Policies**: Different policies for different error types

### API Endpoints

Consider adding REST endpoints for monitoring:

```
GET /api/circuit-breakers/status      # Get all status
GET /api/circuit-breakers/{source}    # Get specific status
POST /api/circuit-breakers/{source}/reset  # Reset specific circuit
GET /api/circuit-breakers/summary     # Get summary statistics
```

## Conclusion

The circuit breaker system provides robust protection against API failures while maintaining system availability. It automatically handles credential issues, provides graceful degradation, and includes comprehensive monitoring capabilities. The system is designed to fail safely and recover automatically, ensuring the grant discovery platform remains available even when individual API sources encounter problems.

---

**Last Updated**: September 18, 2025  
**Version**: 1.0  
**Status**: ✅ Fully Implemented and Tested