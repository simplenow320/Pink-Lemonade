/**
 * Denominational Grants API Routes
 * Provides endpoints for denominational grant scraping and data access
 */

import express from 'express';
import { ScheduledScraper } from '../services/scheduledScraper.js';
import authenticationMiddleware from '../middleware/authentication.js';
import rateLimitingMiddleware from '../middleware/rateLimiting.js';
import validationMiddleware from '../middleware/validation.js';
import { 
  formatSuccessResponse, 
  extractPaginationParams,
  extractRequestInfo 
} from '../utils/responseFormatter.js';
import { createLogger } from '../utils/logger.js';

const router = express.Router();
const logger = createLogger('DenominationalRoutes');

// Initialize scheduled scraper
const scheduledScraper = new ScheduledScraper();
scheduledScraper.initialize();

/**
 * Get denominational grant scraping status
 * GET /api/denominational/status
 */
router.get('/status',
  rateLimitingMiddleware.defaultRateLimit,
  authenticationMiddleware.optionalAuth,
  async (req, res) => {
    try {
      const status = scheduledScraper.getStatus();
      const requestInfo = extractRequestInfo(req);
      
      const response = formatSuccessResponse(status, {
        metadata: {
          endpoint: 'denominational_status',
          responseTime: `${Date.now() - req.startTime}ms`
        },
        requestInfo
      });
      
      res.json(response);
    } catch (error) {
      logger.error(`Status check error: ${error.message}`);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve scraping status',
        details: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

/**
 * Get latest denominational grant results
 * GET /api/denominational/grants
 */
router.get('/grants',
  rateLimitingMiddleware.searchRateLimit,
  authenticationMiddleware.optionalAuth,
  async (req, res) => {
    try {
      const { source, tag, status, limit = 50 } = req.query;
      const { page, limit: paginationLimit, offset } = extractPaginationParams(req.query, parseInt(limit));
      const requestInfo = extractRequestInfo(req);
      
      const latestResults = scheduledScraper.getLatestResults();
      
      if (!latestResults) {
        return res.status(404).json({
          success: false,
          error: 'No denominational grant data available',
          message: 'Scraping may not have completed yet. Check /api/denominational/status',
          timestamp: new Date().toISOString()
        });
      }
      
      // Extract all opportunities from all sources
      let allOpportunities = latestResults.results
        .filter(result => result.status === 'success' && result.opportunities)
        .flatMap(result => result.opportunities);
      
      // Apply filters
      if (source) {
        allOpportunities = allOpportunities.filter(opp => 
          opp.source.toLowerCase().includes(source.toLowerCase())
        );
      }
      
      if (tag) {
        allOpportunities = allOpportunities.filter(opp => 
          opp.tags && opp.tags.some(t => t.toLowerCase().includes(tag.toLowerCase()))
        );
      }
      
      if (status) {
        allOpportunities = allOpportunities.filter(opp => 
          opp.status === status
        );
      }
      
      // Sort by last updated (most recent first)
      allOpportunities.sort((a, b) => 
        new Date(b.last_updated) - new Date(a.last_updated)
      );
      
      // Apply pagination
      const totalResults = allOpportunities.length;
      const paginatedOpportunities = allOpportunities.slice(offset, offset + paginationLimit);
      
      const response = {
        success: true,
        data: paginatedOpportunities,
        pagination: {
          page,
          limit: paginationLimit,
          total: totalResults,
          hasMore: offset + paginationLimit < totalResults
        },
        metadata: {
          endpoint: 'denominational_grants',
          totalSources: latestResults.sourcesProcessed || 0,
          successfulSources: latestResults.successfulSources || 0,
          lastScraped: latestResults.scraping_run?.timestamp || null,
          filtersApplied: { source, tag, status },
          responseTime: `${Date.now() - req.startTime}ms`
        },
        requestInfo
      };
      
      res.json(response);
    } catch (error) {
      logger.error(`Get grants error: ${error.message}`);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve denominational grants',
        details: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

/**
 * Get denominational grant sources configuration
 * GET /api/denominational/sources
 */
router.get('/sources',
  rateLimitingMiddleware.defaultRateLimit,
  authenticationMiddleware.optionalAuth,
  async (req, res) => {
    try {
      const sources = scheduledScraper.getSources();
      const requestInfo = extractRequestInfo(req);
      
      const response = formatSuccessResponse(sources, {
        metadata: {
          endpoint: 'denominational_sources',
          totalSources: sources.length,
          sourceTypes: [...new Set(sources.map(s => s.type))],
          responseTime: `${Date.now() - req.startTime}ms`
        },
        requestInfo
      });
      
      res.json(response);
    } catch (error) {
      logger.error(`Get sources error: ${error.message}`);
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
 * Get scraping run history
 * GET /api/denominational/history
 */
router.get('/history',
  rateLimitingMiddleware.defaultRateLimit,
  authenticationMiddleware.optionalAuth,
  async (req, res) => {
    try {
      const { limit = 10 } = req.query;
      const requestInfo = extractRequestInfo(req);
      
      const history = scheduledScraper.getRunHistory();
      const limitedHistory = history.slice(0, parseInt(limit));
      
      const response = formatSuccessResponse(limitedHistory, {
        metadata: {
          endpoint: 'denominational_history',
          totalRuns: history.length,
          limit: parseInt(limit),
          responseTime: `${Date.now() - req.startTime}ms`
        },
        requestInfo
      });
      
      res.json(response);
    } catch (error) {
      logger.error(`Get history error: ${error.message}`);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve scraping history',
        details: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

/**
 * Manually trigger scraping
 * POST /api/denominational/scrape
 */
router.post('/scrape',
  rateLimitingMiddleware.testRateLimit, // More restrictive for manual runs
  authenticationMiddleware.requireJwt, // Require authentication for manual scraping
  validationMiddleware.validateJsonPayload,
  async (req, res) => {
    try {
      const { source } = req.body;
      const requestInfo = extractRequestInfo(req);
      
      logger.info(`Manual scraping initiated${source ? ` for ${source}` : ''} by ${req.user?.id || 'anonymous'}`);
      
      // Run scraping (this might take a while)
      const results = await scheduledScraper.runManualScrape(source);
      
      const response = formatSuccessResponse(results, {
        metadata: {
          endpoint: 'denominational_manual_scrape',
          triggeredBy: req.user?.id || 'anonymous',
          sourcesScraped: results.sourcesProcessed,
          successfulSources: results.successfulSources,
          totalOpportunities: results.totalOpportunities,
          responseTime: `${Date.now() - req.startTime}ms`
        },
        requestInfo
      });
      
      res.json(response);
    } catch (error) {
      logger.error(`Manual scraping error: ${error.message}`);
      res.status(500).json({
        success: false,
        error: 'Manual scraping failed',
        details: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

/**
 * Search denominational grants
 * GET /api/denominational/search
 */
router.get('/search',
  rateLimitingMiddleware.searchRateLimit,
  authenticationMiddleware.optionalAuth,
  validationMiddleware.validateGrantSearch,
  async (req, res) => {
    try {
      const { q: query, source, tag, amount_min, amount_max } = req.query;
      const { page, limit, offset } = extractPaginationParams(req.query);
      const requestInfo = extractRequestInfo(req);
      
      const latestResults = scheduledScraper.getLatestResults();
      
      if (!latestResults) {
        return res.status(404).json({
          success: false,
          error: 'No denominational grant data available for search',
          timestamp: new Date().toISOString()
        });
      }
      
      // Extract all opportunities
      let opportunities = latestResults.results
        .filter(result => result.status === 'success' && result.opportunities)
        .flatMap(result => result.opportunities);
      
      // Apply text search
      if (query) {
        const searchTerms = query.toLowerCase().split(' ');
        opportunities = opportunities.filter(opp => {
          const searchableText = `${opp.title} ${opp.description} ${opp.tags?.join(' ')} ${opp.source}`.toLowerCase();
          return searchTerms.some(term => searchableText.includes(term));
        });
      }
      
      // Apply filters
      if (source) {
        opportunities = opportunities.filter(opp => 
          opp.source.toLowerCase().includes(source.toLowerCase())
        );
      }
      
      if (tag) {
        opportunities = opportunities.filter(opp => 
          opp.tags && opp.tags.some(t => t.toLowerCase().includes(tag.toLowerCase()))
        );
      }
      
      if (amount_min) {
        opportunities = opportunities.filter(opp => {
          const amount = opp.funding_amount?.match(/\$?([\d,]+)/)?.[1];
          return amount && parseInt(amount.replace(',', '')) >= parseInt(amount_min);
        });
      }
      
      if (amount_max) {
        opportunities = opportunities.filter(opp => {
          const amount = opp.funding_amount?.match(/\$?([\d,]+)/)?.[1];
          return amount && parseInt(amount.replace(',', '')) <= parseInt(amount_max);
        });
      }
      
      // Sort by relevance (basic scoring based on query match)
      if (query) {
        opportunities.sort((a, b) => {
          const aScore = (a.title.toLowerCase().includes(query.toLowerCase()) ? 2 : 0) +
                        (a.description.toLowerCase().includes(query.toLowerCase()) ? 1 : 0);
          const bScore = (b.title.toLowerCase().includes(query.toLowerCase()) ? 2 : 0) +
                        (b.description.toLowerCase().includes(query.toLowerCase()) ? 1 : 0);
          return bScore - aScore;
        });
      }
      
      // Apply pagination
      const totalResults = opportunities.length;
      const paginatedOpportunities = opportunities.slice(offset, offset + limit);
      
      const response = {
        success: true,
        data: paginatedOpportunities,
        pagination: {
          page,
          limit,
          total: totalResults,
          hasMore: offset + limit < totalResults
        },
        metadata: {
          endpoint: 'denominational_search',
          searchQuery: query,
          filtersApplied: { source, tag, amount_min, amount_max },
          responseTime: `${Date.now() - req.startTime}ms`
        },
        requestInfo
      };
      
      res.json(response);
    } catch (error) {
      logger.error(`Search error: ${error.message}`);
      res.status(500).json({
        success: false,
        error: 'Search failed',
        details: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

export default router;