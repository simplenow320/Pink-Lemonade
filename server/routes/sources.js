/**
 * API Sources Routes
 * Handles source status and configuration endpoints
 */

import express from 'express';
import { apiManager } from '../services/apiManager.js';
import { credentialManager } from '../services/credentialManager.js';
import authenticationMiddleware from '../middleware/authentication.js';
import rateLimitingMiddleware from '../middleware/rateLimiting.js';
import validationMiddleware from '../middleware/validation.js';
import { formatSourceStatusResponse, formatSuccessResponse } from '../utils/responseFormatter.js';
import { createLogger } from '../utils/logger.js';

const router = express.Router();
const logger = createLogger('SourcesRoutes');

/**
 * Get status of all API sources
 * GET /api/sources/status
 */
router.get('/status',
  rateLimitingMiddleware.configRateLimit,
  authenticationMiddleware.optionalAuth,
  validationMiddleware.validateSourceStatus,
  async (req, res) => {
    try {
      const { source, includeHealth, includeMetrics } = req.query;
      
      // Get basic API status
      const apiStatus = await apiManager.getApiStatus();
      
      // Get detailed source information
      const sources = [];
      const enabledSources = apiManager.getEnabledSources();
      
      for (const [sourceId, sourceConfig] of Object.entries(enabledSources)) {
        if (source && source !== sourceId) continue;
        
        const sourceInfo = {
          id: sourceId,
          name: sourceConfig.name,
          enabled: sourceConfig.enabled,
          health: 'unknown',
          credentialRequired: sourceConfig.credential_required,
          credentialStatus: 'unknown',
          rateLimitInfo: {
            calls: sourceConfig.rate_limit?.calls || 0,
            period: sourceConfig.rate_limit?.period || 3600
          }
        };
        
        // Check circuit breaker status
        const circuitStatus = apiManager.getCircuitBreakerStatus(sourceId);
        if (circuitStatus) {
          sourceInfo.circuitBreaker = {
            state: circuitStatus.state,
            failureCount: circuitStatus.failureCount,
            lastFailure: circuitStatus.lastFailure
          };
          sourceInfo.health = circuitStatus.state === 'closed' ? 'healthy' : 'unhealthy';
        }
        
        // Check credential status if required
        if (sourceConfig.credential_required && includeHealth) {
          try {
            const credStatus = credentialManager.checkCredential(sourceConfig.api_key_env || `${sourceId}_api_key`);
            sourceInfo.credentialStatus = credStatus.status;
          } catch (error) {
            sourceInfo.credentialStatus = 'error';
          }
        }
        
        // Add performance metrics if requested
        if (includeMetrics) {
          sourceInfo.metrics = {
            totalCalls: circuitStatus?.totalCalls || 0,
            totalFailures: circuitStatus?.totalFailures || 0,
            successRate: circuitStatus?.totalCalls > 0 
              ? ((circuitStatus.totalCalls - circuitStatus.totalFailures) / circuitStatus.totalCalls * 100).toFixed(2)
              : 'N/A'
          };
        }
        
        sources.push(sourceInfo);
      }
      
      const response = formatSourceStatusResponse(sources, {
        summary: apiStatus.summary,
        total: sources.length,
        healthy: sources.filter(s => s.health === 'healthy').length,
        unhealthy: sources.filter(s => s.health === 'unhealthy').length
      });
      
      res.json(response);
    } catch (error) {
      logger.error(`Sources status error: ${error.message}`);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve sources status',
        details: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

/**
 * Get configuration for a specific source
 * GET /api/sources/:sourceId/config
 */
router.get('/:sourceId/config',
  rateLimitingMiddleware.configRateLimit,
  authenticationMiddleware.optionalAuth,
  async (req, res) => {
    try {
      const { sourceId } = req.params;
      const enabledSources = apiManager.getEnabledSources();
      
      if (!enabledSources[sourceId]) {
        return res.status(404).json({
          success: false,
          error: 'Source not found',
          message: `API source '${sourceId}' is not available or enabled`,
          timestamp: new Date().toISOString()
        });
      }
      
      const sourceConfig = enabledSources[sourceId];
      
      // Filter sensitive information
      const safeConfig = {
        id: sourceId,
        name: sourceConfig.name,
        enabled: sourceConfig.enabled,
        description: sourceConfig.description,
        supports: sourceConfig.supports,
        baseUrl: sourceConfig.base_url,
        credentialRequired: sourceConfig.credential_required,
        rateLimit: sourceConfig.rate_limit,
        cacheSettings: {
          ttl: sourceConfig.cache_ttl
        }
      };
      
      const response = formatSuccessResponse(safeConfig, {
        metadata: {
          sourceId,
          configType: 'safe_config'
        }
      });
      
      res.json(response);
    } catch (error) {
      logger.error(`Source config error for ${req.params.sourceId}: ${error.message}`);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve source configuration',
        details: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

/**
 * Test connectivity to a specific source
 * POST /api/sources/:sourceId/test
 */
router.post('/:sourceId/test',
  rateLimitingMiddleware.testRateLimit,
  authenticationMiddleware.optionalAuth,
  async (req, res) => {
    try {
      const { sourceId } = req.params;
      const enabledSources = apiManager.getEnabledSources();
      
      if (!enabledSources[sourceId]) {
        return res.status(404).json({
          success: false,
          error: 'Source not found',
          message: `API source '${sourceId}' is not available or enabled`,
          timestamp: new Date().toISOString()
        });
      }
      
      // Test the source with a simple query
      const testResult = await apiManager.testSourceConnectivity(sourceId);
      
      const response = formatSuccessResponse(testResult, {
        metadata: {
          sourceId,
          testType: 'connectivity_test',
          timestamp: new Date().toISOString()
        }
      });
      
      res.json(response);
    } catch (error) {
      logger.error(`Source test error for ${req.params.sourceId}: ${error.message}`);
      res.status(500).json({
        success: false,
        error: 'Source connectivity test failed',
        details: error.message,
        sourceId: req.params.sourceId,
        timestamp: new Date().toISOString()
      });
    }
  }
);

export default router;