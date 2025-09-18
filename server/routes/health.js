/**
 * Health Check Routes
 * Provides system health and status endpoints
 */

import express from 'express';
import { apiManager } from '../services/apiManager.js';
import { credentialManager } from '../services/credentialManager.js';
import rateLimitingMiddleware from '../middleware/rateLimiting.js';
import { formatHealthResponse } from '../utils/responseFormatter.js';
import { createLogger } from '../utils/logger.js';

const router = express.Router();
const logger = createLogger('HealthRoutes');

/**
 * Basic health check endpoint
 * GET /api/health
 */
router.get('/', rateLimitingMiddleware.healthRateLimit, async (req, res) => {
  try {
    const healthData = {
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      services: {
        api_manager: apiManager ? 'operational' : 'unavailable',
        credential_manager: credentialManager ? 'operational' : 'unavailable',
        cache: 'operational'
      },
      checks: []
    };

    // Add API source health checks
    try {
      const sourceStatus = await apiManager.getApiStatus();
      healthData.services.api_sources = sourceStatus.summary.healthy > 0 ? 'operational' : 'degraded';
      healthData.checks.push({
        name: 'api_sources',
        status: sourceStatus.summary.healthy > 0 ? 'healthy' : 'unhealthy',
        details: sourceStatus.summary
      });
    } catch (error) {
      healthData.services.api_sources = 'unhealthy';
      healthData.checks.push({
        name: 'api_sources',
        status: 'unhealthy',
        error: error.message
      });
    }

    const response = formatHealthResponse(healthData);
    res.json(response);
  } catch (error) {
    logger.error(`Health check error: ${error.message}`);
    const response = formatHealthResponse({
      status: 'unhealthy',
      services: { system: 'unhealthy' },
      checks: [{ name: 'system', status: 'unhealthy', error: error.message }]
    });
    res.status(503).json(response);
  }
});

/**
 * Detailed health check with service statuses
 * GET /api/health/detailed
 */
router.get('/detailed', rateLimitingMiddleware.configRateLimit, async (req, res) => {
  try {
    const healthData = {
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      timestamp: new Date().toISOString(),
      services: {},
      checks: []
    };

    // Check API Manager
    try {
      const sourceStatus = await apiManager.getApiStatus();
      healthData.services.api_manager = {
        status: 'operational',
        sources: sourceStatus
      };
      healthData.checks.push({
        name: 'api_manager',
        status: 'healthy',
        details: `${sourceStatus.summary.healthy} sources healthy`
      });
    } catch (error) {
      healthData.services.api_manager = {
        status: 'error',
        error: error.message
      };
      healthData.checks.push({
        name: 'api_manager',
        status: 'unhealthy',
        error: error.message
      });
    }

    // Check Credential Manager
    try {
      const credStatus = credentialManager.getOverallStatus();
      healthData.services.credential_manager = {
        status: 'operational',
        credentials: credStatus
      };
      healthData.checks.push({
        name: 'credential_manager',
        status: 'healthy',
        details: `${credStatus.available} credentials available`
      });
    } catch (error) {
      healthData.services.credential_manager = {
        status: 'error',
        error: error.message
      };
      healthData.checks.push({
        name: 'credential_manager',
        status: 'unhealthy',
        error: error.message
      });
    }

    const response = formatHealthResponse(healthData);
    const overallStatus = healthData.checks.some(check => check.status === 'unhealthy') ? 503 : 200;
    res.status(overallStatus).json(response);
  } catch (error) {
    logger.error(`Detailed health check error: ${error.message}`);
    const response = formatHealthResponse({
      status: 'error',
      error: error.message,
      timestamp: new Date().toISOString()
    });
    res.status(500).json(response);
  }
});

export default router;