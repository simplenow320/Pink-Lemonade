/**
 * Authentication Middleware Framework
 * Provides flexible authentication for different types of endpoints
 */

import jwt from 'jsonwebtoken';
import { createLogger } from '../utils/logger.js';
import { credentialManager } from '../services/credentialManager.js';

const logger = createLogger('AuthenticationMiddleware');

/**
 * Authentication levels enum
 */
export const AuthLevel = {
  NONE: 'none',           // Public endpoints
  API_KEY: 'api_key',     // API key required
  JWT: 'jwt',             // JWT token required
  ADMIN: 'admin',         // Admin-level access
  OPTIONAL: 'optional'    // Auth optional, but user context provided if available
};

/**
 * Extract API key from request headers
 */
function extractApiKey(req) {
  return req.headers['x-api-key'] || 
         req.headers['authorization']?.replace('Bearer ', '') ||
         req.query.api_key;
}

/**
 * Extract JWT token from request headers
 */
function extractJwtToken(req) {
  const authHeader = req.headers['authorization'];
  if (authHeader && authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }
  return null;
}

/**
 * Validate API key (if API key authentication is implemented)
 */
function validateApiKey(apiKey) {
  // This would typically check against a database or configuration
  // For now, we'll check against environment variables
  const validKeys = [
    process.env.API_KEY,
    process.env.INTERNAL_API_KEY,
    process.env.ADMIN_API_KEY
  ].filter(Boolean);
  
  return validKeys.includes(apiKey);
}

/**
 * Validate and decode JWT token
 */
function validateJwtToken(token) {
  try {
    const secret = process.env.JWT_SECRET;
    
    // Fail-fast if JWT_SECRET is not configured
    if (!secret) {
      throw new Error('JWT_SECRET environment variable is required but not configured');
    }
    
    const decoded = jwt.verify(token, secret);
    
    // Check token expiration
    if (decoded.exp && Date.now() >= decoded.exp * 1000) {
      throw new Error('Token expired');
    }
    
    return { valid: true, payload: decoded };
  } catch (error) {
    return { valid: false, error: error.message };
  }
}

/**
 * Rate limiting based on user/API key
 */
export const userBasedRateLimit = (req, res, next) => {
  // Get user identifier
  const userId = req.user?.id || req.user?.sub || req.apiKey || req.ip;
  
  // Add user context to request for rate limiting
  req.rateLimitKey = `user:${userId}`;
  
  next();
};

/**
 * API Key authentication middleware
 */
export const requireApiKey = (req, res, next) => {
  const apiKey = extractApiKey(req);
  
  if (!apiKey) {
    logger.warn(`API key missing for ${req.method} ${req.path} from ${req.ip}`);
    return res.status(401).json({
      success: false,
      error: 'API key required',
      message: 'Please provide a valid API key in the X-API-Key header or Authorization header',
      timestamp: new Date().toISOString()
    });
  }
  
  if (!validateApiKey(apiKey)) {
    logger.warn(`Invalid API key attempt for ${req.method} ${req.path} from ${req.ip}`);
    return res.status(401).json({
      success: false,
      error: 'Invalid API key',
      message: 'The provided API key is not valid',
      timestamp: new Date().toISOString()
    });
  }
  
  // Add API key to request context
  req.apiKey = apiKey;
  req.authLevel = AuthLevel.API_KEY;
  
  logger.debug(`API key authenticated for ${req.method} ${req.path}`);
  next();
};

/**
 * JWT authentication middleware
 */
export const requireJwt = (req, res, next) => {
  const token = extractJwtToken(req);
  
  if (!token) {
    logger.warn(`JWT token missing for ${req.method} ${req.path} from ${req.ip}`);
    return res.status(401).json({
      success: false,
      error: 'Authentication required',
      message: 'Please provide a valid JWT token in the Authorization header',
      timestamp: new Date().toISOString()
    });
  }
  
  const validation = validateJwtToken(token);
  if (!validation.valid) {
    logger.warn(`Invalid JWT token for ${req.method} ${req.path} from ${req.ip}: ${validation.error}`);
    return res.status(401).json({
      success: false,
      error: 'Invalid token',
      message: 'The provided token is invalid or expired',
      timestamp: new Date().toISOString()
    });
  }
  
  // Add user context to request
  req.user = validation.payload;
  req.authLevel = AuthLevel.JWT;
  
  logger.debug(`JWT authenticated for ${req.method} ${req.path}, user: ${req.user.sub || req.user.id}`);
  next();
};

/**
 * Admin authentication middleware
 */
export const requireAdmin = [requireJwt, (req, res, next) => {
  if (!req.user.roles?.includes('admin') && !req.user.admin) {
    logger.warn(`Admin access denied for ${req.method} ${req.path}, user: ${req.user.sub || req.user.id}`);
    return res.status(403).json({
      success: false,
      error: 'Admin access required',
      message: 'This endpoint requires administrator privileges',
      timestamp: new Date().toISOString()
    });
  }
  
  req.authLevel = AuthLevel.ADMIN;
  logger.debug(`Admin authenticated for ${req.method} ${req.path}, user: ${req.user.sub || req.user.id}`);
  next();
}];

/**
 * Optional authentication middleware - doesn't require auth but provides context if available
 */
export const optionalAuth = (req, res, next) => {
  const token = extractJwtToken(req);
  const apiKey = extractApiKey(req);
  
  if (token) {
    const validation = validateJwtToken(token);
    if (validation.valid) {
      req.user = validation.payload;
      req.authLevel = AuthLevel.JWT;
      logger.debug(`Optional JWT authenticated for ${req.method} ${req.path}`);
    }
  } else if (apiKey && validateApiKey(apiKey)) {
    req.apiKey = apiKey;
    req.authLevel = AuthLevel.API_KEY;
    logger.debug(`Optional API key authenticated for ${req.method} ${req.path}`);
  }
  
  if (!req.authLevel) {
    req.authLevel = AuthLevel.NONE;
  }
  
  next();
};

/**
 * Flexible authentication factory
 * @param {string} level - Authentication level required
 * @param {Object} options - Additional options
 */
export const authenticate = (level = AuthLevel.NONE, options = {}) => {
  switch (level) {
    case AuthLevel.API_KEY:
      return requireApiKey;
    case AuthLevel.JWT:
      return requireJwt;
    case AuthLevel.ADMIN:
      return requireAdmin;
    case AuthLevel.OPTIONAL:
      return optionalAuth;
    case AuthLevel.NONE:
    default:
      return (req, res, next) => {
        req.authLevel = AuthLevel.NONE;
        next();
      };
  }
};

/**
 * Check if user has specific permission
 */
export const requirePermission = (permission) => (req, res, next) => {
  if (req.authLevel === AuthLevel.NONE) {
    return res.status(401).json({
      success: false,
      error: 'Authentication required',
      message: 'This endpoint requires authentication',
      timestamp: new Date().toISOString()
    });
  }
  
  // Admin users have all permissions
  if (req.authLevel === AuthLevel.ADMIN || req.user?.admin) {
    return next();
  }
  
  // Check user permissions
  if (req.user?.permissions?.includes(permission)) {
    return next();
  }
  
  logger.warn(`Permission denied: ${permission} for ${req.method} ${req.path}, user: ${req.user?.sub || req.user?.id || 'anonymous'}`);
  return res.status(403).json({
    success: false,
    error: 'Permission denied',
    message: `This endpoint requires the '${permission}' permission`,
    timestamp: new Date().toISOString()
  });
};

/**
 * Rate limiting based on authentication level
 */
export const authBasedRateLimit = (req, res, next) => {
  let rateLimitConfig = { calls: 100, period: 3600 }; // Default: 100/hour
  
  switch (req.authLevel) {
    case AuthLevel.ADMIN:
      rateLimitConfig = { calls: 10000, period: 3600 }; // 10,000/hour
      break;
    case AuthLevel.JWT:
      rateLimitConfig = { calls: 1000, period: 3600 }; // 1,000/hour
      break;
    case AuthLevel.API_KEY:
      rateLimitConfig = { calls: 500, period: 3600 }; // 500/hour
      break;
    case AuthLevel.NONE:
    default:
      rateLimitConfig = { calls: 100, period: 3600 }; // 100/hour
      break;
  }
  
  req.rateLimitConfig = rateLimitConfig;
  next();
};

/**
 * Security headers based on authentication
 */
export const authSecurityHeaders = (req, res, next) => {
  // Add security headers based on auth level
  if (req.authLevel !== AuthLevel.NONE) {
    res.setHeader('X-Auth-Level', req.authLevel);
    
    if (req.user?.id) {
      res.setHeader('X-User-ID', req.user.id);
    }
  }
  
  next();
};

export default {
  AuthLevel,
  authenticate,
  requireApiKey,
  requireJwt,
  requireAdmin,
  optionalAuth,
  requirePermission,
  userBasedRateLimit,
  authBasedRateLimit,
  authSecurityHeaders
};