/**
 * Utility functions for API operations
 * Handles retry logic, data transformation, and standardized grant object creation
 */

import { createLogger } from './logger.js';

const logger = createLogger('APIUtils');

/**
 * Retry an async operation with exponential backoff
 * @param {Function} operation - Async function to retry
 * @param {number} maxRetries - Maximum number of retries
 * @param {number} baseDelay - Base delay in milliseconds
 * @param {number} backoffFactor - Exponential backoff factor
 * @param {Array<number>} retryStatusCodes - HTTP status codes to retry on
 * @returns {Promise} Result of the operation
 */
export async function retryWithBackoff(
  operation,
  maxRetries = 3,
  baseDelay = 1000,
  backoffFactor = 2,
  retryStatusCodes = [429, 502, 503, 504, 520, 521, 522, 524]
) {
  let lastError;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const result = await operation();
      return result;
    } catch (error) {
      lastError = error;
      
      // Don't retry on the last attempt
      if (attempt === maxRetries) {
        break;
      }
      
      // Check if error should be retried
      const shouldRetry = 
        retryStatusCodes.includes(error.response?.status) ||
        error.code === 'ECONNRESET' ||
        error.code === 'ETIMEDOUT' ||
        error.code === 'ENOTFOUND';
      
      if (!shouldRetry) {
        logger.warn(`Non-retryable error on attempt ${attempt + 1}: ${error.message}`);
        throw error;
      }
      
      const delay = baseDelay * Math.pow(backoffFactor, attempt);
      logger.info(`Retrying operation after ${delay}ms (attempt ${attempt + 1}/${maxRetries})`);
      
      // Add jitter to prevent thundering herd
      const jitter = Math.random() * 0.1 * delay;
      await new Promise(resolve => setTimeout(resolve, delay + jitter));
    }
  }
  
  logger.error(`Operation failed after ${maxRetries + 1} attempts`);
  throw lastError;
}

/**
 * Create a standardized grant object from various API response formats
 * @param {Object} rawData - Raw data from API
 * @param {string} source - Source identifier
 * @param {Object} fieldMapping - Field mapping configuration
 * @returns {Object} Standardized grant object
 */
export function createStandardizedGrant(rawData, source, fieldMapping = {}) {
  const standardGrant = {
    // Required fields
    id: extractField(rawData, fieldMapping.id || ['id', 'opportunityId', 'grant_id', 'opportunity_id']),
    title: extractField(rawData, fieldMapping.title || ['title', 'opportunityTitle', 'name', 'grant_title']),
    funder: extractField(rawData, fieldMapping.funder || ['funder', 'agencyName', 'sponsor', 'funding_agency']),
    description: extractField(rawData, fieldMapping.description || ['description', 'synopsis', 'summary', 'abstract']),
    
    // Optional fields with defaults
    amount_min: parseAmount(extractField(rawData, fieldMapping.amount_min || ['awardFloor', 'minimum_award', 'min_amount'])),
    amount_max: parseAmount(extractField(rawData, fieldMapping.amount_max || ['awardCeiling', 'maximum_award', 'max_amount'])),
    deadline: parseDate(extractField(rawData, fieldMapping.deadline || ['closeDate', 'deadline', 'application_deadline', 'due_date'])),
    posted_date: parseDate(extractField(rawData, fieldMapping.posted_date || ['postedDate', 'posted', 'publication_date', 'created_date'])),
    
    // Additional information
    eligibility: extractField(rawData, fieldMapping.eligibility || ['eligibilityCategory', 'eligibility', 'eligible_applicants']),
    category: extractField(rawData, fieldMapping.category || ['category', 'fundingInstrumentType', 'type']),
    geographic_focus: extractField(rawData, fieldMapping.geographic_focus || ['geographic_focus', 'location', 'region']),
    url: extractField(rawData, fieldMapping.url || ['url', 'link', 'opportunityUrl', 'grant_url']),
    
    // Metadata
    source: source,
    raw_data: rawData, // Keep original data for debugging
    created_at: new Date().toISOString(),
    last_updated: new Date().toISOString()
  };
  
  // Clean up empty fields
  Object.keys(standardGrant).forEach(key => {
    if (standardGrant[key] === null || standardGrant[key] === undefined || standardGrant[key] === '') {
      if (!['amount_min', 'amount_max', 'deadline', 'posted_date'].includes(key)) {
        standardGrant[key] = null;
      }
    }
  });
  
  return standardGrant;
}

/**
 * Extract field value from nested object using multiple possible field names
 * @param {Object} data - Source data object
 * @param {Array|string} fieldNames - Possible field names to try
 * @returns {any} Extracted value or null
 */
function extractField(data, fieldNames) {
  if (!data) return null;
  
  const fieldsToTry = Array.isArray(fieldNames) ? fieldNames : [fieldNames];
  
  for (const fieldName of fieldsToTry) {
    // Support nested field access with dot notation
    if (fieldName.includes('.')) {
      const value = getNestedValue(data, fieldName);
      if (value !== null && value !== undefined) {
        return value;
      }
    } else {
      // Direct field access
      if (data.hasOwnProperty(fieldName) && data[fieldName] !== null && data[fieldName] !== undefined) {
        return data[fieldName];
      }
    }
  }
  
  return null;
}

/**
 * Get nested value from object using dot notation
 * @param {Object} obj - Source object
 * @param {string} path - Dot notation path
 * @returns {any} Value or null
 */
function getNestedValue(obj, path) {
  return path.split('.').reduce((current, key) => {
    return (current && current[key] !== undefined) ? current[key] : null;
  }, obj);
}

/**
 * Parse and normalize amount values
 * @param {any} value - Raw amount value
 * @returns {number|null} Parsed amount or null
 */
function parseAmount(value) {
  if (!value) return null;
  
  let cleanValue = value;
  
  // Handle string values
  if (typeof value === 'string') {
    // Remove currency symbols and commas
    cleanValue = value.replace(/[$,\s]/g, '');
    
    // Handle "K" and "M" suffixes
    if (cleanValue.toLowerCase().endsWith('k')) {
      cleanValue = parseFloat(cleanValue.slice(0, -1)) * 1000;
    } else if (cleanValue.toLowerCase().endsWith('m')) {
      cleanValue = parseFloat(cleanValue.slice(0, -1)) * 1000000;
    } else {
      cleanValue = parseFloat(cleanValue);
    }
  }
  
  return isNaN(cleanValue) ? null : cleanValue;
}

/**
 * Parse and normalize date values
 * @param {any} value - Raw date value
 * @returns {string|null} ISO date string or null
 */
function parseDate(value) {
  if (!value) return null;
  
  try {
    const date = new Date(value);
    return isNaN(date.getTime()) ? null : date.toISOString();
  } catch (error) {
    logger.debug(`Failed to parse date: ${value}`);
    return null;
  }
}

/**
 * Validate required fields in standardized grant object
 * @param {Object} grant - Standardized grant object
 * @returns {boolean} True if valid
 */
export function validateGrantObject(grant) {
  const requiredFields = ['id', 'title', 'funder', 'source'];
  
  for (const field of requiredFields) {
    if (!grant[field]) {
      logger.warn(`Missing required field '${field}' in grant object`);
      return false;
    }
  }
  
  return true;
}

/**
 * Create authentication headers for different API types
 * @param {Object} config - API configuration
 * @returns {Object} Headers object
 */
export function createAuthHeaders(config) {
  const headers = {
    'User-Agent': 'PinkLemonade-GrantFinder/1.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  };
  
  if (!config.api_key) {
    return headers;
  }
  
  switch (config.auth_type) {
    case 'api_key':
      headers[config.auth_header || 'X-API-Key'] = config.api_key;
      break;
      
    case 'bearer':
      headers['Authorization'] = `Bearer ${config.api_key}`;
      break;
      
    case 'basic_auth':
      const encoded = Buffer.from(`${config.api_key}:`).toString('base64');
      headers['Authorization'] = `Basic ${encoded}`;
      break;
      
    case 'app_token':
      headers[config.auth_header || 'X-App-Token'] = config.api_key;
      break;
      
    default:
      headers['Authorization'] = config.api_key;
      break;
  }
  
  return headers;
}

/**
 * Build query parameters for API requests
 * @param {Object} baseParams - Base parameters from config
 * @param {Object} additionalParams - Additional parameters
 * @returns {Object} Combined parameters
 */
export function buildQueryParams(baseParams = {}, additionalParams = {}) {
  const params = { ...baseParams };
  
  // Merge additional parameters, handling array values
  Object.entries(additionalParams).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      params[key] = value;
    }
  });
  
  return params;
}

/**
 * Format URL with parameters, handling template replacements
 * @param {string} baseUrl - Base URL
 * @param {string} endpoint - Endpoint path
 * @param {Object} params - Parameters object
 * @param {Object} pathParams - Parameters for URL template replacement
 * @returns {string} Formatted URL
 */
export function formatUrl(baseUrl, endpoint, params = {}, pathParams = {}) {
  let url = `${baseUrl}${endpoint}`;
  
  // Replace path parameters (e.g., /opportunities/{id})
  Object.entries(pathParams).forEach(([key, value]) => {
    url = url.replace(`{${key}}`, encodeURIComponent(value));
  });
  
  return url;
}

/**
 * Sleep for specified milliseconds
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise} Promise that resolves after delay
 */
export function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}