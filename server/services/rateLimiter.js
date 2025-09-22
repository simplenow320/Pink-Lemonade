/**
 * Rate Limiter for API calls
 * JavaScript port of the RateLimiter class from app/services/apiManager.py
 */

import { createLogger } from '../utils/logger.js';

const logger = createLogger('RateLimiter');

/**
 * Simple rate limiter for API calls
 */
export class RateLimiter {
  constructor(options = {}) {
    this.calls = new Map();
    this.requestsPerMinute = options.requestsPerMinute || 10;
    this.requestsPerHour = options.requestsPerHour || 200;
  }

  /**
   * Wait for available slot based on rate limits
   */
  async waitForSlot() {
    const now = Date.now();
    const sourceName = 'default';
    
    if (!this.calls.has(sourceName)) {
      this.calls.set(sourceName, []);
    }

    const sourceCalls = this.calls.get(sourceName);
    
    // Clean old calls (older than 1 hour)
    const cutoffTime = now - (60 * 60 * 1000);
    const recentCalls = sourceCalls.filter(callTime => callTime > cutoffTime);
    this.calls.set(sourceName, recentCalls);
    
    // Check minute-based rate limit
    const minuteAgo = now - (60 * 1000);
    const recentMinuteCalls = recentCalls.filter(callTime => callTime > minuteAgo);
    
    if (recentMinuteCalls.length >= this.requestsPerMinute) {
      const oldestRecentCall = Math.min(...recentMinuteCalls);
      const waitTime = (oldestRecentCall + (60 * 1000)) - now;
      if (waitTime > 0) {
        logger.info(`Rate limit reached, waiting ${waitTime}ms`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
    
    // Record this request
    recentCalls.push(now);
    this.calls.set(sourceName, recentCalls);
    
    // Add minimum delay between requests (6 seconds for respectful scraping)
    await new Promise(resolve => setTimeout(resolve, 6000));
  }

  /**
   * Check if we can make another API call
   * @param {string} sourceName - Name of the API source
   * @param {number} maxCalls - Maximum number of calls allowed
   * @param {number} periodSeconds - Time period in seconds
   * @returns {boolean} True if call is allowed, false if rate limited
   */
  checkRateLimit(sourceName, maxCalls, periodSeconds) {
    const now = Date.now();
    
    if (!this.calls.has(sourceName)) {
      this.calls.set(sourceName, []);
    }

    const sourceCalls = this.calls.get(sourceName);

    // Clean old calls
    const cutoffTime = now - (periodSeconds * 1000);
    const recentCalls = sourceCalls.filter(callTime => callTime > cutoffTime);
    this.calls.set(sourceName, recentCalls);

    if (recentCalls.length >= maxCalls) {
      logger.warn(`Rate limit exceeded for ${sourceName}: ${recentCalls.length}/${maxCalls} calls in ${periodSeconds}s`);
      return false;
    }

    recentCalls.push(now);
    this.calls.set(sourceName, recentCalls);
    return true;
  }

  /**
   * Get current call count for a source
   * @param {string} sourceName - Name of the API source
   * @param {number} periodSeconds - Time period in seconds to check
   * @returns {number} Number of calls made in the period
   */
  getCurrentCallCount(sourceName, periodSeconds) {
    if (!this.calls.has(sourceName)) {
      return 0;
    }

    const now = Date.now();
    const cutoffTime = now - (periodSeconds * 1000);
    const sourceCalls = this.calls.get(sourceName);
    
    return sourceCalls.filter(callTime => callTime > cutoffTime).length;
  }

  /**
   * Reset rate limits for a specific source
   * @param {string} sourceName - Name of the API source
   */
  reset(sourceName) {
    if (sourceName) {
      this.calls.delete(sourceName);
      logger.info(`Rate limit reset for ${sourceName}`);
    } else {
      this.calls.clear();
      logger.info('All rate limits reset');
    }
  }

  /**
   * Get rate limit status for all sources
   * @returns {Object} Rate limit status by source
   */
  getStatus() {
    const status = {};
    const now = Date.now();

    for (const [sourceName, callTimes] of this.calls.entries()) {
      // Show calls in last hour
      const lastHourCalls = callTimes.filter(time => now - time < 3600000);
      const lastMinuteCalls = callTimes.filter(time => now - time < 60000);

      status[sourceName] = {
        callsLastHour: lastHourCalls.length,
        callsLastMinute: lastMinuteCalls.length,
        totalCalls: callTimes.length,
        lastCallTime: callTimes.length > 0 ? new Date(Math.max(...callTimes)).toISOString() : null
      };
    }

    return status;
  }
}

export default RateLimiter;