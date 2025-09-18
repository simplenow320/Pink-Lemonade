/**
 * Comprehensive Input Validation Middleware
 * Uses express-validator for request parameter validation
 */

import { body, param, query, validationResult } from 'express-validator';
import { createLogger } from '../utils/logger.js';
import xss from 'xss';

const logger = createLogger('ValidationMiddleware');

/**
 * Handle validation errors and return standardized error responses
 */
export const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    logger.warn(`Validation failed for ${req.method} ${req.path}`, {
      errors: errors.array(),
      ip: req.ip
    });

    return res.status(400).json({
      success: false,
      error: 'Validation failed',
      details: errors.array().map(err => ({
        field: err.path || err.param,
        message: err.msg,
        value: typeof err.value === 'string' ? xss(err.value) : err.value
      })),
      timestamp: new Date().toISOString()
    });
  }
  next();
};

/**
 * Validation rules for grant search endpoint
 */
export const validateGrantSearch = [
  query('query')
    .notEmpty()
    .withMessage('Search query is required')
    .isLength({ min: 2, max: 500 })
    .withMessage('Query must be between 2 and 500 characters')
    .trim()
    .escape(),
  
  query('page')
    .optional()
    .isInt({ min: 1, max: 1000 })
    .withMessage('Page must be a positive integer between 1 and 1000')
    .toInt(),
  
  query('limit')
    .optional()
    .isInt({ min: 1, max: 100 })
    .withMessage('Limit must be between 1 and 100')
    .toInt(),
  
  query('filters')
    .optional()
    .custom((value) => {
      if (typeof value === 'string') {
        try {
          const parsed = JSON.parse(value);
          if (typeof parsed !== 'object' || Array.isArray(parsed)) {
            throw new Error('Filters must be a valid JSON object');
          }
          return true;
        } catch (error) {
          throw new Error('Invalid JSON format for filters');
        }
      }
      return true;
    }),
  
  query('sortBy')
    .optional()
    .isIn(['relevance', 'date', 'deadline', 'amount', 'title'])
    .withMessage('SortBy must be one of: relevance, date, deadline, amount, title'),
  
  query('sortOrder')
    .optional()
    .isIn(['asc', 'desc'])
    .withMessage('SortOrder must be either asc or desc'),
  
  handleValidationErrors
];

/**
 * Validation rules for source-specific grant requests
 */
export const validateGrantsBySource = [
  param('sourceId')
    .notEmpty()
    .withMessage('Source ID is required')
    .isLength({ min: 1, max: 100 })
    .withMessage('Source ID must be between 1 and 100 characters')
    .matches(/^[a-zA-Z0-9_-]+$/)
    .withMessage('Source ID can only contain letters, numbers, hyphens, and underscores')
    .trim(),
  
  query('page')
    .optional()
    .isInt({ min: 1, max: 1000 })
    .withMessage('Page must be a positive integer between 1 and 1000')
    .toInt(),
  
  query('limit')
    .optional()
    .isInt({ min: 1, max: 100 })
    .withMessage('Limit must be between 1 and 100')
    .toInt(),
  
  query('query')
    .optional()
    .isLength({ max: 500 })
    .withMessage('Query must be less than 500 characters')
    .trim()
    .escape(),
  
  handleValidationErrors
];

/**
 * Validation rules for grant details endpoint
 */
export const validateGrantDetails = [
  param('grantId')
    .notEmpty()
    .withMessage('Grant ID is required')
    .isLength({ min: 1, max: 200 })
    .withMessage('Grant ID must be between 1 and 200 characters')
    .trim(),
  
  query('source')
    .optional()
    .isLength({ min: 1, max: 100 })
    .withMessage('Source must be between 1 and 100 characters')
    .matches(/^[a-zA-Z0-9_-]+$/)
    .withMessage('Source can only contain letters, numbers, hyphens, and underscores')
    .trim(),
  
  query('includeMetadata')
    .optional()
    .isBoolean()
    .withMessage('includeMetadata must be a boolean')
    .toBoolean(),
  
  handleValidationErrors
];

/**
 * Validation rules for source status endpoint
 */
export const validateSourceStatus = [
  query('source')
    .optional()
    .isLength({ min: 1, max: 100 })
    .withMessage('Source must be between 1 and 100 characters')
    .matches(/^[a-zA-Z0-9_-]+$/)
    .withMessage('Source can only contain letters, numbers, hyphens, and underscores')
    .trim(),
  
  query('includeHealth')
    .optional()
    .isBoolean()
    .withMessage('includeHealth must be a boolean')
    .toBoolean(),
  
  query('includeMetrics')
    .optional()
    .isBoolean()
    .withMessage('includeMetrics must be a boolean')
    .toBoolean(),
  
  handleValidationErrors
];

/**
 * Validation rules for circuit breaker reset endpoint
 */
export const validateCircuitBreakerReset = [
  param('sourceName')
    .notEmpty()
    .withMessage('Source name is required')
    .isLength({ min: 1, max: 100 })
    .withMessage('Source name must be between 1 and 100 characters')
    .matches(/^[a-zA-Z0-9_-]+$/)
    .withMessage('Source name can only contain letters, numbers, hyphens, and underscores')
    .trim(),
  
  handleValidationErrors
];

/**
 * Generic pagination validation
 */
export const validatePagination = [
  query('page')
    .optional()
    .isInt({ min: 1, max: 1000 })
    .withMessage('Page must be a positive integer between 1 and 1000')
    .toInt(),
  
  query('limit')
    .optional()
    .isInt({ min: 1, max: 100 })
    .withMessage('Limit must be between 1 and 100')
    .toInt(),
  
  handleValidationErrors
];

/**
 * Validate request contains valid JSON when Content-Type is application/json
 */
export const validateJsonPayload = (req, res, next) => {
  if (req.is('application/json')) {
    if (req.body === undefined) {
      return res.status(400).json({
        success: false,
        error: 'Invalid JSON payload',
        message: 'Request body is required when Content-Type is application/json',
        timestamp: new Date().toISOString()
      });
    }
    
    // Check if body is empty object when JSON is expected
    if (req.method !== 'GET' && Object.keys(req.body).length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Empty JSON payload',
        message: 'Request body cannot be empty for this endpoint',
        timestamp: new Date().toISOString()
      });
    }
  }
  
  next();
};

/**
 * Sanitize request parameters to prevent XSS attacks
 */
export const sanitizeInput = (req, res, next) => {
  // Sanitize query parameters
  if (req.query) {
    for (const [key, value] of Object.entries(req.query)) {
      if (typeof value === 'string') {
        req.query[key] = xss(value.trim());
      }
    }
  }
  
  // Sanitize URL parameters
  if (req.params) {
    for (const [key, value] of Object.entries(req.params)) {
      if (typeof value === 'string') {
        req.params[key] = xss(value.trim());
      }
    }
  }
  
  // Sanitize body (for POST/PUT requests)
  if (req.body && typeof req.body === 'object') {
    req.body = sanitizeObject(req.body);
  }
  
  next();
};

/**
 * Recursively sanitize object properties
 */
function sanitizeObject(obj) {
  if (Array.isArray(obj)) {
    return obj.map(item => 
      typeof item === 'string' ? xss(item) : 
      typeof item === 'object' ? sanitizeObject(item) : item
    );
  }
  
  if (obj && typeof obj === 'object') {
    const sanitized = {};
    for (const [key, value] of Object.entries(obj)) {
      if (typeof value === 'string') {
        sanitized[key] = xss(value);
      } else if (typeof value === 'object') {
        sanitized[key] = sanitizeObject(value);
      } else {
        sanitized[key] = value;
      }
    }
    return sanitized;
  }
  
  return obj;
}

/**
 * Rate limit validation - check if rate limit headers are present
 */
export const checkRateLimit = (req, res, next) => {
  const rateLimitRemaining = res.getHeader('X-RateLimit-Remaining');
  const rateLimitReset = res.getHeader('X-RateLimit-Reset');
  
  if (rateLimitRemaining !== undefined) {
    logger.debug(`Rate limit remaining: ${rateLimitRemaining} for IP: ${req.ip}`);
    
    if (parseInt(rateLimitRemaining) < 5) {
      logger.warn(`Low rate limit remaining (${rateLimitRemaining}) for IP: ${req.ip}`);
    }
  }
  
  next();
};

export default {
  handleValidationErrors,
  validateGrantSearch,
  validateGrantsBySource,
  validateGrantDetails,
  validateSourceStatus,
  validateCircuitBreakerReset,
  validatePagination,
  validateJsonPayload,
  sanitizeInput,
  checkRateLimit
};