/**
 * Request Sanitization Middleware
 * Prevents XSS, injection attacks, and malicious input
 */

import mongoSanitize from 'express-mongo-sanitize';
import xss from 'xss';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('SanitizationMiddleware');

/**
 * Configure XSS protection with custom options
 */
const xssOptions = {
  whiteList: {
    // Allow minimal HTML tags that might be needed for grant descriptions
    em: [],
    strong: [],
    b: [],
    i: [],
    p: [],
    br: [],
    ul: [],
    ol: [],
    li: []
  },
  stripIgnoreTag: true,
  stripIgnoreTagBody: ['script', 'style'],
  css: false,
  allowCommentTag: false
};

/**
 * Advanced XSS protection middleware
 */
export const xssProtection = (req, res, next) => {
  try {
    // Sanitize query parameters
    if (req.query && typeof req.query === 'object') {
      req.query = sanitizeObject(req.query);
    }

    // Sanitize URL parameters
    if (req.params && typeof req.params === 'object') {
      req.params = sanitizeObject(req.params);
    }

    // Sanitize request body
    if (req.body && typeof req.body === 'object') {
      req.body = sanitizeObject(req.body);
    }

    // Sanitize headers that might contain user input
    const dangerousHeaders = ['x-forwarded-for', 'user-agent', 'referer', 'origin'];
    dangerousHeaders.forEach(header => {
      if (req.headers[header] && typeof req.headers[header] === 'string') {
        req.headers[header] = xss(req.headers[header], xssOptions);
      }
    });

    next();
  } catch (error) {
    logger.error(`XSS protection error: ${error.message}`);
    next(); // Continue processing even if sanitization fails
  }
};

/**
 * MongoDB injection protection
 */
export const mongoSanitization = mongoSanitize({
  replaceWith: '_', // Replace $ and . with underscore
  onSanitize: ({ req, key }) => {
    logger.warn(`MongoDB injection attempt detected from ${req.ip}: key=${key}`, {
      url: req.originalUrl,
      method: req.method,
      userAgent: req.get('User-Agent')
    });
  }
});

/**
 * SQL injection protection for query strings
 */
export const sqlInjectionProtection = (req, res, next) => {
  const suspiciousPatterns = [
    /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)\b)/gi,
    /(\b(OR|AND)\b\s*\d+\s*=\s*\d+)/gi,
    /(;|\||&&|--|\/\*|\*\/)/gi,
    /('|(\\'))|(((\\');?)+)/gi,
    /<script[\s\S]*?>[\s\S]*?<\/script>/gi
  ];

  const checkValue = (value, path = '') => {
    if (typeof value === 'string') {
      for (const pattern of suspiciousPatterns) {
        if (pattern.test(value)) {
          logger.warn(`SQL injection attempt detected from ${req.ip}`, {
            path,
            value: value.substring(0, 100),
            url: req.originalUrl,
            method: req.method,
            userAgent: req.get('User-Agent')
          });
          
          return res.status(400).json({
            success: false,
            error: 'Invalid input detected',
            message: 'Request contains potentially malicious content',
            timestamp: new Date().toISOString()
          });
        }
      }
    } else if (typeof value === 'object' && value !== null) {
      for (const [key, val] of Object.entries(value)) {
        const result = checkValue(val, `${path}.${key}`);
        if (result) return result;
      }
    }
  };

  // Check query parameters
  const queryResult = checkValue(req.query, 'query');
  if (queryResult) return queryResult;

  // Check URL parameters  
  const paramsResult = checkValue(req.params, 'params');
  if (paramsResult) return paramsResult;

  // Check request body
  const bodyResult = checkValue(req.body, 'body');
  if (bodyResult) return bodyResult;

  next();
};

/**
 * File upload protection (if needed for document uploads)
 */
export const fileUploadSanitization = (req, res, next) => {
  if (req.files || req.file) {
    const files = req.files || [req.file];
    const allowedMimes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'image/jpeg',
      'image/png'
    ];
    
    const maxFileSize = 10 * 1024 * 1024; // 10MB

    for (const file of files) {
      if (!allowedMimes.includes(file.mimetype)) {
        logger.warn(`Rejected file upload with invalid MIME type: ${file.mimetype} from ${req.ip}`);
        return res.status(400).json({
          success: false,
          error: 'Invalid file type',
          message: 'Only PDF, DOC, DOCX, TXT, and image files are allowed',
          timestamp: new Date().toISOString()
        });
      }

      if (file.size > maxFileSize) {
        logger.warn(`Rejected file upload exceeding size limit: ${file.size} bytes from ${req.ip}`);
        return res.status(400).json({
          success: false,
          error: 'File too large',
          message: 'File size must not exceed 10MB',
          timestamp: new Date().toISOString()
        });
      }

      // Sanitize filename
      file.originalname = sanitizeFilename(file.originalname);
    }
  }
  
  next();
};

/**
 * Content-Type validation
 */
export const contentTypeValidation = (req, res, next) => {
  const allowedContentTypes = [
    'application/json',
    'application/x-www-form-urlencoded',
    'multipart/form-data',
    'text/plain'
  ];

  if (req.method !== 'GET' && req.method !== 'DELETE') {
    const contentType = req.get('content-type');
    if (contentType) {
      const baseContentType = contentType.split(';')[0];
      if (!allowedContentTypes.some(allowed => baseContentType === allowed)) {
        logger.warn(`Rejected request with invalid Content-Type: ${contentType} from ${req.ip}`);
        return res.status(415).json({
          success: false,
          error: 'Unsupported Media Type',
          message: 'Content-Type not supported',
          timestamp: new Date().toISOString()
        });
      }
    }
  }
  
  next();
};

/**
 * Request size limiting
 */
export const requestSizeLimit = (limit = '10mb') => (req, res, next) => {
  const contentLength = parseInt(req.get('content-length') || '0');
  const maxSize = parseSize(limit);
  
  if (contentLength > maxSize) {
    logger.warn(`Rejected request exceeding size limit: ${contentLength} bytes from ${req.ip}`);
    return res.status(413).json({
      success: false,
      error: 'Payload Too Large',
      message: `Request size exceeds ${limit} limit`,
      timestamp: new Date().toISOString()
    });
  }
  
  next();
};

/**
 * Recursively sanitize object
 */
function sanitizeObject(obj) {
  if (Array.isArray(obj)) {
    return obj.map(item => {
      if (typeof item === 'string') {
        return xss(item, xssOptions);
      } else if (typeof item === 'object' && item !== null) {
        return sanitizeObject(item);
      }
      return item;
    });
  }

  if (obj && typeof obj === 'object' && obj !== null) {
    const sanitized = {};
    for (const [key, value] of Object.entries(obj)) {
      const sanitizedKey = xss(key, xssOptions);
      
      if (typeof value === 'string') {
        sanitized[sanitizedKey] = xss(value, xssOptions);
      } else if (typeof value === 'object' && value !== null) {
        sanitized[sanitizedKey] = sanitizeObject(value);
      } else {
        sanitized[sanitizedKey] = value;
      }
    }
    return sanitized;
  }

  return obj;
}

/**
 * Sanitize filename for uploads
 */
function sanitizeFilename(filename) {
  return filename
    .replace(/[^a-zA-Z0-9._-]/g, '_') // Replace invalid characters
    .replace(/\.+/g, '.') // Replace multiple dots
    .replace(/^\.+/, '') // Remove leading dots
    .substring(0, 255); // Limit length
}

/**
 * Parse size string to bytes
 */
function parseSize(size) {
  if (typeof size === 'number') return size;
  
  const units = {
    b: 1,
    kb: 1024,
    mb: 1024 * 1024,
    gb: 1024 * 1024 * 1024
  };
  
  const match = size.toLowerCase().match(/^(\d+(?:\.\d+)?)(b|kb|mb|gb)?$/);
  if (!match) return 0;
  
  const value = parseFloat(match[1]);
  const unit = match[2] || 'b';
  
  return value * units[unit];
}

export default {
  xssProtection,
  mongoSanitization,
  sqlInjectionProtection,
  fileUploadSanitization,
  contentTypeValidation,
  requestSizeLimit
};