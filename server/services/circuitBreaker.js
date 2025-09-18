/**
 * Circuit Breaker Implementation for API Source Resilience
 * JavaScript port of the CircuitBreaker class from app/services/apiManager.py
 */

import { createLogger } from '../utils/logger.js';

const logger = createLogger('CircuitBreaker');

// Circuit Breaker States
export const CircuitBreakerState = {
  CLOSED: 'closed',      // Normal operation
  OPEN: 'open',          // Failed - blocking calls
  HALF_OPEN: 'half_open' // Testing if service recovered
};

/**
 * Robust Circuit Breaker implementation for API source resilience
 * 
 * Features:
 * - Configurable failure threshold and cooldown periods
 * - Automatic recovery testing
 * - Credential-safe error logging
 * - Graceful degradation
 */
export class CircuitBreaker {
  /**
   * Initialize circuit breaker for a source
   * 
   * @param {string} sourceName - Name of the API source
   * @param {number} failureThreshold - Number of failures before opening circuit
   * @param {number} cooldownMinutes - Minutes to wait before attempting recovery
   * @param {number} halfOpenMaxCalls - Max calls to allow in half-open state for testing
   */
  constructor(sourceName, failureThreshold = 5, cooldownMinutes = 15, halfOpenMaxCalls = 3) {
    this.sourceName = sourceName;
    this.failureThreshold = failureThreshold;
    this.cooldownPeriod = cooldownMinutes * 60 * 1000; // Convert to milliseconds
    this.halfOpenMaxCalls = halfOpenMaxCalls;

    // State tracking
    this.state = CircuitBreakerState.CLOSED;
    this.failureCount = 0;
    this.lastFailureTime = null;
    this.halfOpenCalls = 0;

    // Statistics
    this.totalCalls = 0;
    this.totalFailures = 0;
    this.stateChanges = [];

    logger.info(`Circuit breaker initialized for ${sourceName} - ` +
      `threshold: ${failureThreshold}, cooldown: ${cooldownMinutes}min`);
  }

  /**
   * Check if calls to the source are allowed
   */
  canExecute() {
    const now = new Date();

    if (this.state === CircuitBreakerState.CLOSED) {
      return true;
    } else if (this.state === CircuitBreakerState.OPEN) {
      // Check if cooldown period has passed
      if (this.lastFailureTime && 
          now.getTime() - this.lastFailureTime.getTime() >= this.cooldownPeriod) {
        this._transitionToHalfOpen();
        return true;
      }
      return false;
    } else if (this.state === CircuitBreakerState.HALF_OPEN) {
      // Allow limited calls for testing recovery
      return this.halfOpenCalls < this.halfOpenMaxCalls;
    }

    return false;
  }

  /**
   * Record a successful call
   */
  recordSuccess() {
    this.totalCalls++;

    if (this.state === CircuitBreakerState.HALF_OPEN) {
      this.halfOpenCalls++;
      // If we've made enough successful test calls, close the circuit
      if (this.halfOpenCalls >= this.halfOpenMaxCalls) {
        this._transitionToClosed();
        logger.info(`Circuit breaker for ${this.sourceName} recovered - ` +
          `closing circuit after ${this.halfOpenCalls} successful test calls`);
      }
    } else if (this.state === CircuitBreakerState.CLOSED) {
      // Reset failure count on success
      this.failureCount = 0;
    }
  }

  /**
   * Record a failed call
   */
  recordFailure(error, isCredentialError = false) {
    this.totalCalls++;
    this.totalFailures++;
    this.failureCount++;
    this.lastFailureTime = new Date();

    // Log error safely without exposing credentials
    const safeError = this._sanitizeError(error);
    const errorType = isCredentialError ? "credential" : "general";

    logger.warn(`Circuit breaker for ${this.sourceName} recorded ${errorType} failure ` +
      `(${this.failureCount}/${this.failureThreshold}): ${safeError}`);

    if (this.state === CircuitBreakerState.HALF_OPEN) {
      // Any failure in half-open state opens circuit immediately
      this._transitionToOpen();
      logger.warn(`Circuit breaker for ${this.sourceName} failed recovery test - opening circuit`);
    } else if (this.state === CircuitBreakerState.CLOSED) {
      // Check if we've hit failure threshold
      if (this.failureCount >= this.failureThreshold) {
        this._transitionToOpen();
        logger.error(`Circuit breaker for ${this.sourceName} opened due to ` +
          `${this.failureCount} consecutive failures`);
      }
    }
  }

  /**
   * Transition to open state
   */
  _transitionToOpen() {
    const oldState = this.state;
    this.state = CircuitBreakerState.OPEN;
    this.halfOpenCalls = 0;
    this._recordStateChange(oldState, this.state);
  }

  /**
   * Transition to half-open state
   */
  _transitionToHalfOpen() {
    const oldState = this.state;
    this.state = CircuitBreakerState.HALF_OPEN;
    this.halfOpenCalls = 0;
    this._recordStateChange(oldState, this.state);
    logger.info(`Circuit breaker for ${this.sourceName} entering half-open state for recovery test`);
  }

  /**
   * Transition to closed state
   */
  _transitionToClosed() {
    const oldState = this.state;
    this.state = CircuitBreakerState.CLOSED;
    this.failureCount = 0;
    this.halfOpenCalls = 0;
    this._recordStateChange(oldState, this.state);
  }

  /**
   * Record state change for monitoring
   */
  _recordStateChange(fromState, toState) {
    const change = {
      timestamp: new Date().toISOString(),
      fromState: fromState,
      toState: toState,
      failureCount: this.failureCount
    };
    this.stateChanges.push(change);

    // Keep only last 10 state changes
    if (this.stateChanges.length > 10) {
      this.stateChanges = this.stateChanges.slice(-10);
    }
  }

  /**
   * Remove potential credentials from error messages
   */
  _sanitizeError(error) {
    let sanitized = String(error);

    // Remove API keys (various formats)
    sanitized = sanitized.replace(
      /[aA][pP][iI][-_]?[kK][eE][yY][-_:=\s]+[A-Za-z0-9+/]{16,}/g,
      'API_KEY=[REDACTED]'
    );

    // Remove bearer tokens
    sanitized = sanitized.replace(
      /[bB]earer\s+[A-Za-z0-9+/._-]{16,}/g,
      'Bearer [REDACTED]'
    );

    // Remove basic auth
    sanitized = sanitized.replace(
      /[bB]asic\s+[A-Za-z0-9+/=]{16,}/g,
      'Basic [REDACTED]'
    );

    // Remove URLs with embedded credentials
    sanitized = sanitized.replace(
      /https?:\/\/[^:]+:[^@]+@/g,
      'https://[USER]:[PASS]@'
    );

    // Remove access tokens
    sanitized = sanitized.replace(
      /access[-_]?token[-_:=\s]+[A-Za-z0-9+/._-]{16,}/g,
      'access_token=[REDACTED]'
    );

    return sanitized;
  }

  /**
   * Get current circuit breaker status
   */
  getStatus() {
    const successRate = this.totalCalls > 0 
      ? (this.totalCalls - this.totalFailures) / this.totalCalls * 100 
      : 100;

    return {
      source: this.sourceName,
      state: this.state,
      failureCount: this.failureCount,
      failureThreshold: this.failureThreshold,
      totalCalls: this.totalCalls,
      totalFailures: this.totalFailures,
      successRate: successRate,
      lastFailureTime: this.lastFailureTime?.toISOString() || null,
      cooldownPeriodMinutes: this.cooldownPeriod / (60 * 1000),
      isAvailable: this.canExecute(),
      stateChanges: this.stateChanges.slice(-5) // Last 5 changes
    };
  }

  /**
   * Manually reset circuit breaker to closed state
   */
  reset() {
    const oldState = this.state;
    this.state = CircuitBreakerState.CLOSED;
    this.failureCount = 0;
    this.halfOpenCalls = 0;
    this._recordStateChange(oldState, this.state);
    logger.info(`Circuit breaker for ${this.sourceName} manually reset to closed state`);
  }
}

export default CircuitBreaker;