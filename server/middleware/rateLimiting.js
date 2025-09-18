/**
 * Enhanced Rate Limiting Middleware
 * Provides endpoint-specific and user-based rate limiting
 */

import rateLimit from 'express-rate-limit';
import slowDown from 'express-slow-down';
import { createLogger } from '../utils/logger.js';
import { AuthLevel } from './authentication.js';

const logger = createLogger('RateLimitingMiddleware');

/**
 * Rate limit configurations for different endpoint types
 */
const rateLimitConfigs = {
  // Health check endpoints - very lenient
  health: {
    windowMs: 1 * 60 * 1000, // 1 minute
    max: 100, // 100 requests per minute
    message: {
      success: false,
      error: 'Rate limit exceeded',
      message: 'Too many health check requests. Please try again in a minute.',
      retryAfter: '1 minute'
    }
  },
  
  // Search endpoints - moderate limiting
  search: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 200, // 200 requests per 15 minutes
    message: {
      success: false,
      error: 'Search rate limit exceeded',
      message: 'Too many search requests. Please try again in a few minutes.',
      retryAfter: '15 minutes'
    }
  },
  
  // Data retrieval endpoints - stricter
  data: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // 100 requests per 15 minutes
    message: {
      success: false,
      error: 'Data access rate limit exceeded',
      message: 'Too many data requests. Please try again in a few minutes.',
      retryAfter: '15 minutes'
    }
  },
  
  // Admin endpoints - very strict
  admin: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 50, // 50 requests per 15 minutes
    message: {
      success: false,
      error: 'Admin rate limit exceeded',
      message: 'Too many admin requests. Please try again later.',
      retryAfter: '15 minutes'
    }
  },
  
  // Configuration endpoints - moderate
  config: {
    windowMs: 5 * 60 * 1000, // 5 minutes
    max: 50, // 50 requests per 5 minutes
    message: {
      success: false,
      error: 'Configuration access rate limit exceeded',
      message: 'Too many configuration requests. Please try again in a few minutes.',
      retryAfter: '5 minutes'
    }
  },
  
  // Default fallback
  default: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // 100 requests per 15 minutes
    message: {
      success: false,
      error: 'Rate limit exceeded',
      message: 'Too many requests. Please try again later.',
      retryAfter: '15 minutes'
    }
  }
};

/**
 * Slow down configurations - progressively slow down requests as limits approach
 */
const slowDownConfigs = {
  search: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    delayAfter: 50, // Start slowing down after 50 requests
    delayMs: 100, // Add 100ms delay per request
    maxDelayMs: 5000, // Max 5 second delay
    skipFailedRequests: true
  },
  
  data: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    delayAfter: 30, // Start slowing down after 30 requests
    delayMs: 200, // Add 200ms delay per request
    maxDelayMs: 10000, // Max 10 second delay
    skipFailedRequests: true
  }
};

/**
 * Create key generator based on user authentication with IPv6 support
 */
const createKeyGenerator = (includeAuth = true) => (req) => {
  // Use the built-in IP handling from express-rate-limit for IPv6 compatibility
  const baseKey = req.ip;
  
  if (!includeAuth) return baseKey;
  
  // Use user ID if authenticated
  if (req.user?.id) {
    return `user:${req.user.id}`;
  }
  
  // Use API key if present  
  if (req.apiKey) {
    return `apikey:${req.apiKey.substring(0, 8)}`;
  }
  
  // Use IP for unauthenticated requests - let express-rate-limit handle IPv6
  return baseKey;
};

/**
 * Skip rate limiting for certain conditions
 */
const createSkipFunction = (options = {}) => (req) => {
  // Skip for admin users if configured
  if (options.skipAdmin && req.authLevel === AuthLevel.ADMIN) {
    return true;
  }
  
  // Skip for internal IP addresses if configured
  if (options.skipInternal) {
    const ip = req.ip;
    const internalRanges = [
      '127.0.0.1',
      '::1',
      '10.0.0.0/8',
      '192.168.0.0/16',
      '172.16.0.0/12'
    ];
    
    if (internalRanges.some(range => ip.includes(range.split('/')[0]))) {
      return true;
    }
  }
  
  return false;
};

/**
 * Enhanced rate limiting with logging
 */
const createRateLimit = (config, options = {}) => {
  const rateLimitConfig = {
    ...config,
    skip: createSkipFunction(options),
    standardHeaders: true,
    legacyHeaders: false,
    handler: (req, res) => {
      const identifier = req.user?.id || req.apiKey?.substring(0, 8) || req.ip;
      
      // Log rate limit exceeded
      logger.warn(`Rate limit exceeded for ${identifier} on ${req.method} ${req.path}`, {
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        authLevel: req.authLevel,
        method: req.method,
        path: req.path
      });
      
      res.status(429).json({
        ...config.message,
        timestamp: new Date().toISOString(),
        resetTime: new Date(Date.now() + config.windowMs).toISOString()
      });
    }
  };
  
  return rateLimit(rateLimitConfig);
};

/**
 * Create slow down middleware
 */
const createSlowDown = (config) => {
  return slowDown({
    ...config,
    // Fix express-slow-down v2 delayMs behavior
    delayMs: () => config.delayMs,
    validate: { delayMs: false }, // Disable warning
    // Don't use custom keyGenerator for IPv6 compatibility
    skipSuccessfulRequests: false,
    skipFailedRequests: false
  });
};

/**
 * Adaptive rate limiting based on authentication level
 */
export const adaptiveRateLimit = (baseConfig) => (req, res, next) => {
  let config = { ...baseConfig };
  
  // Adjust limits based on authentication level
  switch (req.authLevel) {
    case AuthLevel.ADMIN:
      config.max = Math.floor(config.max * 10); // 10x higher limit
      break;
    case AuthLevel.JWT:
      config.max = Math.floor(config.max * 3); // 3x higher limit
      break;
    case AuthLevel.API_KEY:
      config.max = Math.floor(config.max * 2); // 2x higher limit
      break;
    case AuthLevel.NONE:
    default:
      // Use base config
      break;
  }
  
  const limiter = createRateLimit(config, { includeAuth: true });
  return limiter(req, res, next);
};

/**
 * Pre-configured rate limiters for different endpoint types
 */
export const healthRateLimit = createRateLimit(rateLimitConfigs.health, {
  skipAdmin: true,
  skipInternal: true
});

export const searchRateLimit = createRateLimit(rateLimitConfigs.search, {
  skipAdmin: true
});

export const dataRateLimit = createRateLimit(rateLimitConfigs.data, {
  skipAdmin: true
});

export const adminRateLimit = createRateLimit(rateLimitConfigs.admin);

export const configRateLimit = createRateLimit(rateLimitConfigs.config, {
  skipAdmin: true
});

export const defaultRateLimit = createRateLimit(rateLimitConfigs.default);

/**
 * Pre-configured slow down middleware
 */
export const searchSlowDown = createSlowDown(slowDownConfigs.search);
export const dataSlowDown = createSlowDown(slowDownConfigs.data);

/**
 * Combined middleware factory for common patterns
 */
export const createEndpointLimiter = (type, options = {}) => {
  const middleware = [];
  
  // Add slow down if configured
  if (type === 'search') {
    middleware.push(searchSlowDown);
  } else if (type === 'data') {
    middleware.push(dataSlowDown);
  }
  
  // Add rate limiting
  switch (type) {
    case 'health':
      middleware.push(healthRateLimit);
      break;
    case 'search':
      middleware.push(searchRateLimit);
      break;
    case 'data':
      middleware.push(dataRateLimit);
      break;
    case 'admin':
      middleware.push(adminRateLimit);
      break;
    case 'config':
      middleware.push(configRateLimit);
      break;
    default:
      middleware.push(defaultRateLimit);
      break;
  }
  
  return middleware;
};

/**
 * Global rate limiting middleware
 */
export const globalRateLimit = createRateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000, // 1000 requests per 15 minutes per IP
  message: {
    success: false,
    error: 'Global rate limit exceeded',
    message: 'Too many requests from this IP. Please try again later.',
    retryAfter: '15 minutes'
  }
}, {
  skipAdmin: true,
  skipInternal: true
});

export const testRateLimit = createRateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 10, // 10 tests per minute
  message: {
    success: false,
    error: 'Test rate limit exceeded',
    message: 'Too many test requests. Please try again in a minute.',
    retryAfter: '1 minute'
  }
});

export const detailsRateLimit = createRateLimit({
  windowMs: 5 * 60 * 1000, // 5 minutes  
  max: 50, // 50 detail requests per 5 minutes
  message: {
    success: false,
    error: 'Details rate limit exceeded',
    message: 'Too many detail requests. Please try again in a few minutes.',
    retryAfter: '5 minutes'
  }
});

export const discoveryRateLimit = createRateLimit({
  windowMs: 10 * 60 * 1000, // 10 minutes
  max: 20, // 20 discovery requests per 10 minutes
  message: {
    success: false,
    error: 'Discovery rate limit exceeded', 
    message: 'Too many discovery requests. Please try again in a few minutes.',
    retryAfter: '10 minutes'
  }
});

export default {
  adaptiveRateLimit,
  healthRateLimit,
  searchRateLimit,
  dataRateLimit,
  adminRateLimit,
  configRateLimit,
  testRateLimit,
  detailsRateLimit,
  discoveryRateLimit,
  defaultRateLimit,
  searchSlowDown,
  dataSlowDown,
  createEndpointLimiter,
  globalRateLimit
};