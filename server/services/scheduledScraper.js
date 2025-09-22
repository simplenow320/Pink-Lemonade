/**
 * Scheduled Scraper Service
 * Manages automated scraping cycles for denominational grants
 */

import schedule from 'node-schedule';
import { DenominationalScraper } from './denominationalScraper.js';
import { createLogger } from '../utils/logger.js';
import { CacheManager } from './cacheManager.js';
import { databasePersistence } from './databasePersistence.js';
import fs from 'fs/promises';
import path from 'path';

const logger = createLogger('ScheduledScraper');

export class ScheduledScraper {
  constructor() {
    this.scraper = new DenominationalScraper();
    this.cache = new CacheManager();
    this.isRunning = false;
    this.lastRun = null;
    this.nextRun = null;
    this.scheduledJob = null;
    this.runHistory = [];
  }

  /**
   * Initialize scheduled scraping
   * Runs every 3 days as specified in the REACTO prompt
   */
  initialize() {
    try {
      // Schedule to run every 3 days at 2 AM to avoid peak hours
      // Cron pattern: minute hour day-of-month month day-of-week
      // 0 2 */3 * * = At 02:00 AM every 3 days
      this.scheduledJob = schedule.scheduleJob('denominational-scraper', '0 2 */3 * *', async () => {
        await this.runScheduledScrape();
      });

      // Also allow manual runs, but stagger different sources
      // This creates a more distributed load
      this.staggeredJob = schedule.scheduleJob('denominational-staggered', '0 */6 * * *', async () => {
        await this.runStaggeredScrape();
      });

      logger.info('Denominational scraper scheduled: Every 3 days at 2 AM, with 6-hour staggered updates');
      this.nextRun = this.scheduledJob.nextInvocation();
      
    } catch (error) {
      logger.error(`Error initializing scheduler: ${error.message}`);
      throw error;
    }
  }

  /**
   * Run a complete scraping cycle
   */
  async runScheduledScrape() {
    if (this.isRunning) {
      logger.warn('Scraping already in progress, skipping scheduled run');
      return;
    }

    const runId = `scheduled-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    try {
      this.isRunning = true;
      this.lastRun = new Date();
      logger.info('Starting scheduled denominational grants scraping cycle');

      // Create database run record
      await databasePersistence.createScrapeRun(runId, {
        type: 'scheduled',
        triggeredAt: new Date().toISOString()
      });

      const startTime = Date.now();
      const results = await this.scraper.runScrapingCycle();
      const duration = Date.now() - startTime;

      // Process and store results in database
      if (results && results.results && results.results.length > 0) {
        const allGrants = [];
        
        // Extract all grants from all sources
        results.results.forEach(sourceResult => {
          if (sourceResult.opportunities && sourceResult.opportunities.length > 0) {
            sourceResult.opportunities.forEach(opportunity => {
              allGrants.push({
                title: opportunity.title || 'Untitled Grant',
                funder: opportunity.organization || sourceResult.source,
                source_name: sourceResult.source,
                source_url: sourceResult.url,
                link: opportunity.link,
                amount_min: opportunity.amount_min,
                amount_max: opportunity.amount_max,
                deadline: opportunity.deadline,
                geography: opportunity.location || opportunity.geography,
                eligibility: opportunity.eligibility,
                description: opportunity.description,
                requirements: opportunity.requirements,
                contact_info: opportunity.contact || {},
                ai_enhanced_data: opportunity.ai_enhanced || {},
                external_id: this.generateDeterministicId(sourceResult.source, opportunity.title, opportunity.link)
              });
            });
          }
        });

        // Store grants in database
        const { insertedCount, updatedCount } = await databasePersistence.storeScrapedGrants(allGrants, runId);
        
        // Update run record with final stats
        await databasePersistence.updateScrapeRun(runId, {
          status: 'completed',
          sourcesProcessed: results.sourcesProcessed || results.results.length,
          successfulSources: results.successfulSources || results.results.filter(r => r.opportunities && r.opportunities.length > 0).length,
          totalOpportunities: results.totalOpportunities || allGrants.length,
          errors: results.errors || [],
          completedAt: new Date()
        });

        logger.info(`Scheduled scrape completed: ${insertedCount} new, ${updatedCount} updated grants stored in database`);
      } else {
        // No results found
        await databasePersistence.updateScrapeRun(runId, {
          status: 'completed',
          sourcesProcessed: results?.results?.length || 0,
          successfulSources: 0,
          totalOpportunities: 0,
          errors: results?.errors || [],
          completedAt: new Date()
        });
      }

      // Store results in cache for API access
      this.cache.set('latest_denominational_scrape', results, 86400000); // 24 hours

      // Update run history
      const runRecord = {
        timestamp: this.lastRun.toISOString(),
        duration: `${Math.round(duration / 1000)}s`,
        status: 'success',
        sourcesProcessed: results.sourcesProcessed,
        successfulSources: results.successfulSources,
        totalOpportunities: results.totalOpportunities,
        results: results.results.map(r => ({
          source: r.source,
          status: r.status,
          opportunityCount: r.opportunities?.length || 0
        }))
      };

      this.runHistory.unshift(runRecord);
      // Keep last 10 runs
      this.runHistory = this.runHistory.slice(0, 10);

      // Cache run history
      this.cache.set('denominational_scrape_history', this.runHistory, 86400000);

      logger.info(`Scheduled scraping completed in ${Math.round(duration / 1000)}s: ${results.totalOpportunities} opportunities from ${results.successfulSources} sources`);

    } catch (error) {
      logger.error(`Scheduled scraping failed: ${error.message}`);
      
      // Update run record with error in database
      try {
        await databasePersistence.updateScrapeRun(runId, {
          status: 'failed',
          sourcesProcessed: 0,
          successfulSources: 0,
          totalOpportunities: 0,
          errors: [{ message: error.message, timestamp: new Date().toISOString() }],
          completedAt: new Date()
        });
      } catch (dbError) {
        logger.error(`Failed to update failed run in database: ${dbError.message}`);
      }
      
      // Record failed run
      const failedRun = {
        timestamp: new Date().toISOString(),
        status: 'failed',
        error: error.message
      };
      this.runHistory.unshift(failedRun);
      this.runHistory = this.runHistory.slice(0, 10);
      this.cache.set('denominational_scrape_history', this.runHistory, 86400000);
      
    } finally {
      this.isRunning = false;
      this.nextRun = this.scheduledJob?.nextInvocation();
    }
  }

  /**
   * Run staggered scraping (subset of sources to distribute load)
   */
  async runStaggeredScrape() {
    if (this.isRunning) return;

    try {
      const sources = this.scraper.getSources();
      const currentHour = new Date().getHours();
      
      // Divide sources into 4 groups and scrape different group based on time
      const groupSize = Math.ceil(sources.length / 4);
      const groupIndex = Math.floor(currentHour / 6); // 0-3 based on 6-hour intervals
      const startIndex = groupIndex * groupSize;
      const groupSources = sources.slice(startIndex, startIndex + groupSize);

      if (groupSources.length === 0) return;

      logger.info(`Running staggered scrape for group ${groupIndex + 1}: ${groupSources.map(s => s.name).join(', ')}`);

      // Create temporary scraper with subset of sources
      const staggeredScraper = new DenominationalScraper();
      staggeredScraper.sources = groupSources;
      
      const results = await staggeredScraper.runScrapingCycle();
      
      // Merge with existing cached results
      const existingResults = this.cache.get('latest_denominational_scrape') || { results: [] };
      
      // Update only the sources that were just scraped
      const updatedResults = existingResults.results.map(existing => {
        const updated = results.results.find(r => r.source === existing.source);
        return updated || existing;
      });
      
      // Add any new sources
      results.results.forEach(newResult => {
        if (!updatedResults.find(r => r.source === newResult.source)) {
          updatedResults.push(newResult);
        }
      });

      existingResults.results = updatedResults;
      existingResults.lastStaggeredUpdate = new Date().toISOString();
      
      this.cache.set('latest_denominational_scrape', existingResults, 86400000);

    } catch (error) {
      logger.error(`Staggered scraping error: ${error.message}`);
    }
  }

  /**
   * Run manual scraping cycle
   */
  async runManualScrape(sourceName = null) {
    if (this.isRunning) {
      throw new Error('Scraping already in progress');
    }

    const runId = `manual-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    try {
      this.isRunning = true;
      logger.info(`Starting manual scraping${sourceName ? ` for ${sourceName}` : ''}`);

      // Create database run record
      await databasePersistence.createScrapeRun(runId, {
        type: 'manual',
        sourceFilter: sourceName || 'all',
        triggeredAt: new Date().toISOString()
      });

      let results;
      if (sourceName) {
        // Scrape specific source
        const sources = this.scraper.getSources();
        const targetSource = sources.find(s => s.name === sourceName);
        if (!targetSource) {
          throw new Error(`Source '${sourceName}' not found`);
        }

        const tempScraper = new DenominationalScraper();
        tempScraper.sources = [targetSource];
        results = await tempScraper.runScrapingCycle();
      } else {
        // Full scrape
        results = await this.scraper.runScrapingCycle();
      }

      // Process and store results in database
      if (results && results.results && results.results.length > 0) {
        const allGrants = [];
        
        // Extract all grants from all sources
        results.results.forEach(sourceResult => {
          if (sourceResult.opportunities && sourceResult.opportunities.length > 0) {
            sourceResult.opportunities.forEach(opportunity => {
              allGrants.push({
                title: opportunity.title || 'Untitled Grant',
                funder: opportunity.organization || sourceResult.source,
                source_name: sourceResult.source,
                source_url: sourceResult.url,
                link: opportunity.link,
                amount_min: opportunity.amount_min,
                amount_max: opportunity.amount_max,
                deadline: opportunity.deadline,
                geography: opportunity.location || opportunity.geography,
                eligibility: opportunity.eligibility,
                description: opportunity.description,
                requirements: opportunity.requirements,
                contact_info: opportunity.contact || {},
                ai_enhanced_data: opportunity.ai_enhanced || {},
                external_id: this.generateDeterministicId(sourceResult.source, opportunity.title, opportunity.link)
              });
            });
          }
        });

        // Store grants in database
        const { insertedCount, updatedCount } = await databasePersistence.storeScrapedGrants(allGrants, runId);
        
        // Update run record with final stats
        await databasePersistence.updateScrapeRun(runId, {
          status: 'completed',
          sourcesProcessed: results.results.length,
          successfulSources: results.results.filter(r => r.opportunities && r.opportunities.length > 0).length,
          totalOpportunities: allGrants.length,
          errors: results.errors || [],
          completedAt: new Date()
        });

        logger.info(`Manual scrape completed: ${insertedCount} new, ${updatedCount} updated grants stored`);
      } else {
        // No results found
        await databasePersistence.updateScrapeRun(runId, {
          status: 'completed',
          sourcesProcessed: 0,
          successfulSources: 0,
          totalOpportunities: 0,
          errors: results.errors || [],
          completedAt: new Date()
        });
      }

      // Still cache for quick access
      this.cache.set('latest_denominational_scrape', results, 86400000);

      return results;

    } catch (error) {
      logger.error(`Manual scraping failed: ${error.message}`);
      
      // Update run record with error
      try {
        await databasePersistence.updateScrapeRun(runId, {
          status: 'failed',
          sourcesProcessed: 0,
          successfulSources: 0,
          totalOpportunities: 0,
          errors: [{ message: error.message, timestamp: new Date().toISOString() }],
          completedAt: new Date()
        });
      } catch (dbError) {
        logger.error(`Failed to update failed run in database: ${dbError.message}`);
      }
      
      throw error;
    } finally {
      this.isRunning = false;
    }
  }

  /**
   * Get scraping status and statistics
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      lastRun: this.lastRun,
      nextRun: this.nextRun,
      scheduledJobActive: this.scheduledJob?.name || null,
      sourcesConfigured: this.scraper.getSources().length,
      runHistory: this.runHistory.slice(0, 5), // Last 5 runs
      cacheStatus: {
        hasLatestResults: this.cache.get('latest_denominational_scrape') !== null,
        hasRunHistory: this.cache.get('denominational_scrape_history') !== null
      }
    };
  }

  /**
   * Get latest scraping results from database (fallback to cache)
   */
  async getLatestResults(options = {}) {
    try {
      // Always try database first for consistency
      const dbResults = await databasePersistence.getLatestGrants(options);
      
      // Format results to match expected API structure
      if (dbResults && dbResults.grants && dbResults.grants.length > 0) {
        // Transform database format to expected cache format for API compatibility
        const formattedResults = {
          sourcesProcessed: await this.getUniqueSourceCount(),
          successfulSources: await this.getSuccessfulSourceCount(),
          totalOpportunities: dbResults.total,
          lastUpdate: new Date().toISOString(),
          source: 'database',
          results: this.groupGrantsBySource(dbResults.grants),
          pagination: {
            total: dbResults.total,
            limit: dbResults.limit,
            offset: dbResults.offset
          }
        };
        
        // Cache the formatted results for faster subsequent access
        this.cache.set('latest_denominational_scrape', formattedResults, 300000); // 5 minutes
        
        return formattedResults;
      }
    } catch (error) {
      logger.warn(`Failed to get results from database, falling back to cache: ${error.message}`);
    }
    
    // Fallback to cache if database fails or has no results
    const cachedResults = this.cache.get('latest_denominational_scrape');
    if (cachedResults) {
      cachedResults.source = 'cache';
      return cachedResults;
    }
    
    // Return empty results if neither database nor cache have data
    return {
      sourcesProcessed: 0,
      successfulSources: 0,
      totalOpportunities: 0,
      lastUpdate: null,
      source: 'none',
      results: [],
      pagination: { total: 0, limit: options.limit || 50, offset: options.offset || 0 }
    };
  }

  /**
   * Get run history from database (fallback to cache)
   */
  async getRunHistory(limit = 10) {
    try {
      // Try to get from database first
      const dbHistory = await databasePersistence.getScrapeRunHistory(limit);
      if (dbHistory && dbHistory.length > 0) {
        return dbHistory;
      }
    } catch (error) {
      logger.warn(`Failed to get run history from database, falling back to cache: ${error.message}`);
    }
    
    // Fallback to cache and memory
    return this.cache.get('denominational_scrape_history') || this.runHistory;
  }

  /**
   * Generate deterministic ID for grant deduplication
   */
  generateDeterministicId(source, title, link) {
    // Create a deterministic ID based on source, title, and link
    const crypto = require('crypto');
    const key = `${source}||${title || ''}||${link || ''}`.toLowerCase().trim();
    return crypto.createHash('md5').update(key).digest('hex');
  }

  /**
   * Helper: Group database grants by source for API compatibility
   */
  groupGrantsBySource(grants) {
    const sourceMap = {};
    grants.forEach(grant => {
      const sourceName = grant.source_name;
      if (!sourceMap[sourceName]) {
        sourceMap[sourceName] = {
          source: sourceName,
          status: 'success',
          url: grant.source_url,
          opportunities: []
        };
      }
      
      // Transform database format to expected opportunity format
      sourceMap[sourceName].opportunities.push({
        title: grant.title,
        organization: grant.funder,
        link: grant.link,
        amount_min: parseFloat(grant.amount_min) || null,
        amount_max: parseFloat(grant.amount_max) || null,
        deadline: grant.deadline,
        location: grant.geography,
        geography: grant.geography,
        eligibility: grant.eligibility,
        description: grant.description,
        requirements: grant.requirements,
        contact: grant.contact_info,
        ai_enhanced: grant.ai_enhanced_data
      });
    });
    
    return Object.values(sourceMap);
  }

  /**
   * Helper: Get count of unique sources from database
   */
  async getUniqueSourceCount() {
    try {
      const status = await databasePersistence.getScrapingStatus();
      return status.lastRun?.sources_processed || 0;
    } catch (error) {
      return 0;
    }
  }

  /**
   * Helper: Get count of successful sources from database
   */
  async getSuccessfulSourceCount() {
    try {
      const status = await databasePersistence.getScrapingStatus();
      return status.lastRun?.successful_sources || 0;
    } catch (error) {
      return 0;
    }
  }

  /**
   * Get available sources
   */
  getSources() {
    return this.scraper.getSources();
  }

  /**
   * Stop scheduled scraping
   */
  stop() {
    if (this.scheduledJob) {
      this.scheduledJob.cancel();
      logger.info('Denominational scraper schedule stopped');
    }
    if (this.staggeredJob) {
      this.staggeredJob.cancel();
    }
  }

  /**
   * Restart scheduled scraping
   */
  restart() {
    this.stop();
    this.initialize();
    logger.info('Denominational scraper schedule restarted');
  }
}

export default ScheduledScraper;