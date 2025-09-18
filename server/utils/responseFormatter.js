/**
 * Standardized Response Formatter with Pagination Support
 * Provides consistent JSON response format across all API endpoints
 */

import { createLogger } from './logger.js';

const logger = createLogger('ResponseFormatter');

/**
 * Standard success response format
 */
export const formatSuccessResponse = (data, options = {}) => {
  const response = {
    success: true,
    data,
    timestamp: new Date().toISOString()
  };

  // Add metadata if provided
  if (options.metadata) {
    response.metadata = {
      ...options.metadata,
      responseTime: options.responseTime || null,
      source: options.source || null
    };
  }

  // Add pagination if provided
  if (options.pagination) {
    response.pagination = {
      page: options.pagination.page || 1,
      limit: options.pagination.limit || 25,
      total: options.pagination.total || (Array.isArray(data) ? data.length : 0),
      totalPages: Math.ceil((options.pagination.total || 0) / (options.pagination.limit || 25)),
      hasMore: options.pagination.hasMore || false
    };
    
    // Add count for backwards compatibility
    response.count = Array.isArray(data) ? data.length : 0;
  } else {
    // Add simple count if no pagination
    response.count = Array.isArray(data) ? data.length : undefined;
  }

  // Add request information if provided
  if (options.requestInfo) {
    response.request = {
      method: options.requestInfo.method,
      endpoint: options.requestInfo.endpoint,
      params: options.requestInfo.params || {}
    };
  }

  return response;
};

/**
 * Standard error response format
 */
export const formatErrorResponse = (error, statusCode = 500, options = {}) => {
  const response = {
    success: false,
    error: options.userMessage || getDefaultErrorMessage(statusCode),
    timestamp: new Date().toISOString()
  };

  // Add error code if provided
  if (options.errorCode) {
    response.errorCode = options.errorCode;
  }

  // Add details in development mode
  if (process.env.NODE_ENV !== 'production' && options.includeDetails) {
    response.details = {
      message: error.message,
      stack: error.stack?.split('\n').slice(0, 5), // Limit stack trace
      type: error.constructor.name
    };
  }

  // Add retry information if applicable
  if (options.retryable) {
    response.retry = {
      retryable: true,
      retryAfter: options.retryAfter || null,
      maxRetries: options.maxRetries || null
    };
  }

  // Add validation errors if present
  if (options.validationErrors) {
    response.validationErrors = options.validationErrors;
  }

  return response;
};

/**
 * Get default error message based on status code
 */
function getDefaultErrorMessage(statusCode) {
  const messages = {
    400: 'Bad Request - Invalid input parameters',
    401: 'Unauthorized - Authentication required',
    403: 'Forbidden - Insufficient permissions',
    404: 'Not Found - Resource not found',
    409: 'Conflict - Resource already exists',
    422: 'Unprocessable Entity - Invalid request data',
    429: 'Too Many Requests - Rate limit exceeded',
    500: 'Internal Server Error - Something went wrong',
    502: 'Bad Gateway - External service unavailable',
    503: 'Service Unavailable - Temporary service interruption',
    504: 'Gateway Timeout - External service timeout'
  };
  
  return messages[statusCode] || 'An error occurred';
}

/**
 * Format paginated response with metadata
 */
export const formatPaginatedResponse = (data, pagination, options = {}) => {
  const formattedPagination = {
    page: parseInt(pagination.page) || 1,
    limit: parseInt(pagination.limit) || 25,
    total: pagination.total || 0,
    totalPages: Math.ceil((pagination.total || 0) / (parseInt(pagination.limit) || 25)),
    hasMore: false
  };

  // Calculate hasMore
  formattedPagination.hasMore = formattedPagination.page < formattedPagination.totalPages;

  return formatSuccessResponse(data, {
    ...options,
    pagination: formattedPagination
  });
};

/**
 * Format API source status response
 */
export const formatSourceStatusResponse = (sources, options = {}) => {
  const summary = {
    totalSources: sources.length,
    enabledSources: sources.filter(s => s.enabled).length,
    disabledSources: sources.filter(s => !s.enabled).length,
    healthySources: sources.filter(s => s.health === 'healthy').length,
    unhealthySources: sources.filter(s => s.health !== 'healthy').length
  };

  return formatSuccessResponse(sources, {
    ...options,
    metadata: {
      summary,
      lastUpdated: new Date().toISOString(),
      ...options.metadata
    }
  });
};

/**
 * Format search results with source information
 */
export const formatSearchResponse = (results, searchQuery, options = {}) => {
  const metadata = {
    query: searchQuery,
    searchTime: options.searchTime || null,
    sourcesQueried: options.sourcesQueried || [],
    totalSources: options.totalSources || 0,
    successfulSources: options.successfulSources || 0,
    failedSources: options.failedSources || 0,
    ...options.metadata
  };

  return formatSuccessResponse(results, {
    ...options,
    metadata
  });
};

/**
 * Format grant details response
 */
export const formatGrantDetailsResponse = (grant, options = {}) => {
  if (!grant) {
    return formatErrorResponse(
      new Error('Grant not found'),
      404,
      { userMessage: 'The requested grant could not be found' }
    );
  }

  const metadata = {
    source: options.source || null,
    fetchedAt: new Date().toISOString(),
    includedFields: grant ? Object.keys(grant).length : 0,
    ...options.metadata
  };

  return formatSuccessResponse(grant, {
    ...options,
    metadata
  });
};

/**
 * Format health check response
 */
export const formatHealthResponse = (healthData) => {
  const overallStatus = determineOverallHealth(healthData);
  
  return {
    status: overallStatus,
    timestamp: new Date().toISOString(),
    version: healthData.version || '1.0.0',
    environment: healthData.environment || 'development',
    uptime: healthData.uptime || process.uptime(),
    services: healthData.services || {},
    system: {
      memory: healthData.memory || process.memoryUsage(),
      nodeVersion: process.version,
      platform: process.platform
    },
    checks: healthData.checks || []
  };
};

/**
 * Determine overall health status
 */
function determineOverallHealth(healthData) {
  if (!healthData.services) return 'healthy';
  
  const services = Object.values(healthData.services);
  const hasUnhealthy = services.some(status => 
    status === 'unhealthy' || status === 'failed' || status === 'error'
  );
  
  const hasDegraded = services.some(status => 
    status === 'degraded' || status === 'warning'
  );
  
  if (hasUnhealthy) return 'unhealthy';
  if (hasDegraded) return 'degraded';
  return 'healthy';
}

/**
 * Extract pagination parameters from request
 */
export const extractPaginationParams = (req, defaults = {}) => {
  const page = parseInt(req.query.page) || defaults.page || 1;
  const limit = parseInt(req.query.limit) || defaults.limit || 25;
  
  // Ensure reasonable bounds
  const boundedPage = Math.max(1, Math.min(page, 1000));
  const boundedLimit = Math.max(1, Math.min(limit, 100));
  
  return {
    page: boundedPage,
    limit: boundedLimit,
    offset: (boundedPage - 1) * boundedLimit
  };
};

/**
 * Apply pagination to array data
 */
export const paginateArray = (data, pagination) => {
  const { page, limit, offset } = pagination;
  const total = data.length;
  const paginatedData = data.slice(offset, offset + limit);
  
  return {
    data: paginatedData,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
      hasMore: (page * limit) < total
    }
  };
};

/**
 * Response timing middleware
 */
export const responseTimingMiddleware = (req, res, next) => {
  req.startTime = Date.now();
  
  const originalJson = res.json;
  res.json = function(obj) {
    // Add response time to successful responses
    if (obj && obj.success !== false && req.startTime) {
      const responseTime = Date.now() - req.startTime;
      
      if (obj.metadata) {
        obj.metadata.responseTime = `${responseTime}ms`;
      } else if (obj.success) {
        obj.responseTime = `${responseTime}ms`;
      }
    }
    
    return originalJson.call(this, obj);
  };
  
  next();
};

/**
 * Request information extraction
 */
export const extractRequestInfo = (req) => ({
  method: req.method,
  endpoint: req.originalUrl,
  params: {
    query: req.query,
    params: req.params
  },
  userAgent: req.get('User-Agent'),
  ip: req.ip,
  timestamp: new Date().toISOString()
});

export default {
  formatSuccessResponse,
  formatErrorResponse,
  formatPaginatedResponse,
  formatSourceStatusResponse,
  formatSearchResponse,
  formatGrantDetailsResponse,
  formatHealthResponse,
  extractPaginationParams,
  paginateArray,
  responseTimingMiddleware,
  extractRequestInfo
};