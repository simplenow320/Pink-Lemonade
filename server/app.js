/**
 * Express Application Server
 * Main entry point for the Node.js/Express backend
 * Provides comprehensive API proxy endpoints with security middleware
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import cookieParser from 'cookie-parser';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import dotenv from 'dotenv';
import fs from 'fs';

// Import our services and configuration
import { createLogger } from './utils/logger.js';
import { apiManager } from './services/apiManager.js';
import { credentialManager } from './services/credentialManager.js';
import { apiConfig } from './config/apiConfig.js';

// Import comprehensive middleware
import validationMiddleware from './middleware/validation.js';
import sanitizationMiddleware from './middleware/sanitization.js';
import authenticationMiddleware from './middleware/authentication.js';
import rateLimitingMiddleware from './middleware/rateLimiting.js';

// Import route handlers
import healthRoutes from './routes/health.js';
import sourcesRoutes from './routes/sources.js';
import grantsRoutes from './routes/grants.js';

// Import response formatting utilities
import {
  formatSuccessResponse,
  formatErrorResponse,
  formatPaginatedResponse,
  formatSourceStatusResponse,
  formatSearchResponse,
  formatGrantDetailsResponse,
  formatHealthResponse,
  extractPaginationParams,
  responseTimingMiddleware,
  extractRequestInfo
} from './utils/responseFormatter.js';

// Load environment variables
dotenv.config();

// Get current file path (ES modules equivalent of __dirname)
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Initialize logger
const logger = createLogger('App');

// Create Express application
const app = express();
const PORT = process.env.PORT || 3001; // Different from frontend port 3000

// Trust proxy if behind reverse proxy (like in production)
if (process.env.NODE_ENV === 'production') {
  app.set('trust proxy', 1);
}

// Create logs directory if it doesn't exist
const logsDir = join(__dirname, 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

/**
 * Security Middleware
 */
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'"],
      fontSrc: ["'self'"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
      frameSrc: ["'none'"],
    },
  },
  crossOriginEmbedderPolicy: false // Allow embedding for development
}));

/**
 * CORS Configuration
 */
const corsOptions = {
  origin: process.env.NODE_ENV === 'production' 
    ? (process.env.FRONTEND_URL ? [process.env.FRONTEND_URL] : false) // Production must set FRONTEND_URL
    : ['http://localhost:3000', 'http://localhost:5000'], // Include Flask dev server
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
  exposedHeaders: ['X-Total-Count', 'X-Page-Count']
};

app.use(cors(corsOptions));

/**
 * Global Security Middleware Setup
 */
// Response timing middleware
app.use(responseTimingMiddleware);

// Request sanitization and XSS protection
app.use(sanitizationMiddleware.xssProtection);
app.use(sanitizationMiddleware.mongoSanitization);
app.use(sanitizationMiddleware.sqlInjectionProtection);
app.use(sanitizationMiddleware.contentTypeValidation);

// Input sanitization
app.use(validationMiddleware.sanitizeInput);

// Global rate limiting
app.use('/api/', rateLimitingMiddleware.globalRateLimit);

/**
 * Body Parsing Middleware
 */
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(cookieParser());

/**
 * Compression Middleware
 */
app.use(compression());

/**
 * Request Logging Middleware
 */
app.use((req, res, next) => {
  const start = Date.now();
  const { method, url, ip } = req;
  
  // Add timing to request for response formatter
  req.startTime = start;
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    const { statusCode } = res;
    
    if (statusCode >= 400) {
      logger.warn(`${method} ${url} - ${statusCode} - ${duration}ms - ${ip}`);
    } else {
      logger.info(`${method} ${url} - ${statusCode} - ${duration}ms - ${ip}`);
    }
  });
  
  next();
});

/**
 * API Routes
 */
app.use('/api/health', healthRoutes);
app.use('/api/sources', sourcesRoutes);
app.use('/api/grants', grantsRoutes);

/**
 * Configuration endpoints for internal use
 */
app.get('/api/config/sources', (req, res) => {
  try {
    const sources = apiConfig.getAllSources();
    res.json({
      success: true,
      data: sources,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error(`Error getting sources: ${error.message}`);
    res.status(500).json({
      success: false,
      error: 'Failed to get sources',
      message: error.message
    });
  }
});

// Get credential status
app.get('/api/config/credentials', (req, res) => {
  try {
    const credentialStatus = credentialManager.checkAllCredentials();
    res.json({
      success: true,
      data: credentialStatus,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error(`Error getting credential status: ${error.message}`);
    res.status(500).json({
      success: false,
      error: 'Failed to get credential status',
      message: error.message
    });
  }
});

// Get circuit breaker status
app.get('/api/config/circuit-breakers', (req, res) => {
  try {
    const { source } = req.query;
    const status = apiManager.getCircuitBreakerStatus(source);
    res.json({
      success: true,
      data: status,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error(`Error getting circuit breaker status: ${error.message}`);
    res.status(500).json({
      success: false,
      error: 'Failed to get circuit breaker status',
      message: error.message
    });
  }
});

// Reset circuit breaker
app.post('/api/config/circuit-breakers/:sourceName/reset', (req, res) => {
  try {
    const { sourceName } = req.params;
    const success = apiManager.resetCircuitBreaker(sourceName);
    
    if (success) {
      res.json({
        success: true,
        message: `Circuit breaker for ${sourceName} has been reset`,
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(404).json({
        success: false,
        error: `Circuit breaker for source '${sourceName}' not found`
      });
    }
  } catch (error) {
    logger.error(`Error resetting circuit breaker for ${req.params.sourceName}: ${error.message}`);
    res.status(500).json({
      success: false,
      error: 'Failed to reset circuit breaker',
      message: error.message
    });
  }
})
/**
 * Enhanced Error Handling Middleware
 */
app.use((err, req, res, next) => {
  const statusCode = err.status || err.statusCode || 500;
  
  // Log error details securely
  logger.error(`Unhandled error on ${req.method} ${req.path}`, {
    error: err.message,
    stack: process.env.NODE_ENV === 'development' ? err.stack : undefined,
    ip: req.ip
  });

  // Determine if error is retryable and user message
  const isRetryable = statusCode >= 500 || statusCode === 429;
  let userMessage = 'An error occurred while processing your request';
  
  if (statusCode === 400) userMessage = 'Invalid request parameters';
  else if (statusCode === 401) userMessage = 'Authentication required';
  else if (statusCode === 403) userMessage = 'Access denied';
  else if (statusCode === 404) userMessage = 'Resource not found';
  else if (statusCode === 429) userMessage = 'Too many requests. Please try again later';
  else if (statusCode >= 500) userMessage = 'Server error. Please try again later';

  const response = formatErrorResponse(err, statusCode, {
    userMessage,
    retryable: isRetryable,
    retryAfter: isRetryable ? '30 seconds' : null,
    includeDetails: process.env.NODE_ENV !== 'production'
  });

  res.status(statusCode).json(response);
});

/**
 * 404 Handler
 */
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Route not found',
    path: req.originalUrl,
    timestamp: new Date().toISOString()
  });
});

/**
 * Graceful Shutdown Handler
 */
const gracefulShutdown = (signal) => {
  logger.info(`Received ${signal}. Shutting down gracefully...`);
  
  server.close(() => {
    logger.info('Server closed. Exiting process.');
    process.exit(0);
  });

  // Force close after 10 seconds
  setTimeout(() => {
    logger.error('Could not close connections in time, forcefully shutting down');
    process.exit(1);
  }, 10000);
};

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

/**
 * Environment Variable Validation on Startup
 */
function validateEnvironment() {
  const requiredEnvVars = [];
  const warnings = [];

  // Check for JWT_SECRET in production
  if (process.env.NODE_ENV === 'production' && !process.env.JWT_SECRET) {
    logger.error('JWT_SECRET environment variable is required in production');
    process.exit(1);
  } else if (!process.env.JWT_SECRET) {
    warnings.push('JWT_SECRET not set - JWT authentication will not work');
  }

  // Log warnings
  if (warnings.length > 0) {
    logger.warn('Environment validation warnings:');
    warnings.forEach(warning => logger.warn(`- ${warning}`));
  }

  logger.info('✅ Environment validation completed');
}

/**
 * Start Server with proper validation
 */
validateEnvironment();

const server = app.listen(PORT, '0.0.0.0', () => {
  logger.info(`🚀 Server running on port ${PORT}`);
  logger.info(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
  logger.info(`🔧 API Manager initialized with ${Object.keys(apiManager.getEnabledSources()).length} sources`);
  
  // Log credential status
  try {
    const credentialReport = credentialManager.getServiceStatusReport();
    logger.info(`🔑 Credentials: ${credentialReport.summary.available}/${credentialReport.summary.totalCredentials} available`);
  } catch (error) {
    logger.warn(`🔑 Could not get credential status: ${error.message}`);
  }
  
  // Log circuit breaker summary
  try {
    const circuitSummary = apiManager.getCircuitBreakerSummary();
    logger.info(`⚡ Circuit Breakers: ${circuitSummary.closedCircuits} closed, ${circuitSummary.openCircuits} open`);
  } catch (error) {
    logger.warn(`⚡ Could not get circuit breaker status: ${error.message}`);
  }

  logger.info('🎯 Server is ready to accept connections');
});

// Handle server startup errors
server.on('error', (error) => {
  if (error.code === 'EADDRINUSE') {
    logger.error(`❌ Port ${PORT} is already in use`);
    process.exit(1);
  } else {
    logger.error(`❌ Server startup error: ${error.message}`);
    process.exit(1);
  }
});

export default app;
      const apiStatus = await apiManager.getApiStatus();
      
      // Get detailed source information
