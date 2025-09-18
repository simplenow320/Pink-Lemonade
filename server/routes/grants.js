/**
 * Grants API Routes
 * Handles grant search, details, and discovery endpoints
 */

import express from 'express';
import { apiManager } from '../services/apiManager.js';
import authenticationMiddleware from '../middleware/authentication.js';
import rateLimitingMiddleware from '../middleware/rateLimiting.js';
import validationMiddleware from '../middleware/validation.js';
import { 
  formatSearchResponse, 
  formatGrantDetailsResponse,
  formatSuccessResponse,
  extractPaginationParams,
  extractRequestInfo 
} from '../utils/responseFormatter.js';
import { createLogger } from '../utils/logger.js';

const router = express.Router();
const logger = createLogger('GrantsRoutes');

/**
 * Search grants across all sources
 * GET /api/grants/search
 */
router.get('/search',
  rateLimitingMiddleware.searchRateLimit,
  authenticationMiddleware.optionalAuth,
  validationMiddleware.validateGrantSearch,
  async (req, res) => {
    try {
      const { query, source, status, location, amount_min, amount_max, deadline_after, deadline_before } = req.query;
      const { page, limit, offset } = extractPaginationParams(req.query);
      const requestInfo = extractRequestInfo(req);
      
      // Build search parameters
      const searchParams = {
        query: query || '',
        filters: {}
      };
      
      if (status) searchParams.filters.status = status;
      if (location) searchParams.filters.location = location;
      if (amount_min) searchParams.filters.amount_min = parseInt(amount_min);
      if (amount_max) searchParams.filters.amount_max = parseInt(amount_max);
      if (deadline_after) searchParams.filters.deadline_after = deadline_after;
      if (deadline_before) searchParams.filters.deadline_before = deadline_before;
      
      // Add pagination to search params
      searchParams.pagination = { page, limit, offset };
      
      let grants = [];
      let totalResults = 0;
      
      if (source) {
        // Search specific source
        logger.info(`Searching source ${source} for "${query || 'all grants'}"`);
        grants = await apiManager.getGrantsFromSource(source, searchParams);
        totalResults = grants.length;
      } else {
        // Search all sources
        logger.info(`Searching all sources for "${query || 'all grants'}"`);
        const searchResult = await apiManager.searchOpportunities(query, searchParams.filters);
        grants = searchResult.grants || [];
        totalResults = searchResult.total || grants.length;
      }
      
      // Apply pagination to results if not handled by source
      const startIndex = offset;
      const endIndex = startIndex + limit;
      const paginatedGrants = grants.slice(startIndex, endIndex);
      
      const response = formatSearchResponse(paginatedGrants, {
        pagination: {
          page,
          limit,
          total: totalResults,
          hasMore: endIndex < totalResults
        },
        metadata: {
          searchQuery: query,
          source: source || 'all_sources',
          filtersApplied: Object.keys(searchParams.filters).length > 0,
          responseTime: `${Date.now() - req.startTime}ms`
        },
        requestInfo
      });
      
      res.json(response);
    } catch (error) {
      logger.error(`Grant search error: ${error.message}`);
      res.status(500).json({
        success: false,
        error: 'Grant search failed',
        details: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

/**
 * Get grant details by ID from a specific source
 * GET /api/grants/:sourceId/:grantId
 */
router.get('/:sourceId/:grantId',
  rateLimitingMiddleware.detailsRateLimit,
  authenticationMiddleware.optionalAuth,
  validationMiddleware.validateGrantDetails,
  async (req, res) => {
    try {
      const { sourceId, grantId } = req.params;
      const requestInfo = extractRequestInfo(req);
      
      logger.info(`Fetching grant details: ${grantId} from ${sourceId}`);
      
      // Get grant details from specific source
      const grantDetails = await apiManager.getGrantDetails(sourceId, grantId);
      
      if (!grantDetails) {
        return res.status(404).json({
          success: false,
          error: 'Grant not found',
          message: `Grant '${grantId}' not found in source '${sourceId}'`,
          timestamp: new Date().toISOString()
        });
      }
      
      const response = formatGrantDetailsResponse(grantDetails, {
        metadata: {
          sourceId,
          grantId,
          fetchedAt: new Date().toISOString(),
          responseTime: `${Date.now() - req.startTime}ms`
        },
        requestInfo
      });
      
      res.json(response);
    } catch (error) {
      logger.error(`Grant details error: ${error.message}`);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve grant details',
        details: error.message,
        sourceId: req.params.sourceId,
        grantId: req.params.grantId,
        timestamp: new Date().toISOString()
      });
    }
  }
);

/**
 * Discovery endpoint - find grants matching organization profile
 * POST /api/grants/discover
 */
router.post('/discover',
  rateLimitingMiddleware.discoveryRateLimit,
  authenticationMiddleware.optionalAuth,
  validationMiddleware.validateJsonPayload,
  async (req, res) => {
    try {
      const { organizationProfile, preferences, filters } = req.body;
      const { page, limit, offset } = extractPaginationParams(req.query);
      const requestInfo = extractRequestInfo(req);
      
      logger.info(`Grant discovery for organization: ${organizationProfile?.name || 'Unknown'}`);
      
      // Use API manager's discovery capabilities
      const discoveryResult = await apiManager.discoverGrants({
        profile: organizationProfile,
        preferences,
        filters,
        pagination: { page, limit, offset }
      });
      
      const response = formatSearchResponse(discoveryResult.grants, {
        pagination: {
          page,
          limit,
          total: discoveryResult.total || discoveryResult.grants.length,
          hasMore: discoveryResult.hasMore || false
        },
        metadata: {
          discoveryType: 'profile_based',
          matchingAlgorithm: discoveryResult.algorithm || 'standard',
          organizationName: organizationProfile?.name,
          filtersApplied: filters ? Object.keys(filters).length : 0,
          confidence: discoveryResult.confidence || null,
          responseTime: `${Date.now() - req.startTime}ms`
        },
        requestInfo
      });
      
      res.json(response);
    } catch (error) {
      logger.error(`Grant discovery error: ${error.message}`);
      res.status(500).json({
        success: false,
        error: 'Grant discovery failed',
        details: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

/**
 * Get recent grants from all sources
 * GET /api/grants/recent
 */
router.get('/recent',
  rateLimitingMiddleware.searchRateLimit,
  authenticationMiddleware.optionalAuth,
  async (req, res) => {
    try {
      const { days = 7, source } = req.query;
      const { page, limit } = extractPaginationParams(req.query);
      const requestInfo = extractRequestInfo(req);
      
      logger.info(`Fetching recent grants from last ${days} days`);
      
      // Calculate date filter
      const dateThreshold = new Date();
      dateThreshold.setDate(dateThreshold.getDate() - parseInt(days));
      
      const searchParams = {
        filters: {
          deadline_after: dateThreshold.toISOString().split('T')[0]
        },
        sortBy: 'date',
        sortOrder: 'desc',
        pagination: { page, limit }
      };
      
      let grants = [];
      
      if (source) {
        grants = await apiManager.getGrantsFromSource(source, searchParams);
      } else {
        const searchResult = await apiManager.searchOpportunities('', searchParams.filters);
        grants = searchResult.grants || [];
      }
      
      const response = formatSearchResponse(grants, {
        pagination: {
          page,
          limit,
          total: grants.length,
          hasMore: false
        },
        metadata: {
          queryType: 'recent_grants',
          daysPast: days,
          source: source || 'all_sources',
          dateThreshold: dateThreshold.toISOString(),
          responseTime: `${Date.now() - req.startTime}ms`
        },
        requestInfo
      });
      
      res.json(response);
    } catch (error) {
      logger.error(`Recent grants error: ${error.message}`);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve recent grants',
        details: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

export default router;