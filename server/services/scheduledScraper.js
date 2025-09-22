/**
 * Scheduled Scraper Service
 * Manages automated scraping cycles for denominational grants
 */

import schedule from 'node-schedule';
import { DenominationalScraper } from './denominationalScraper.js';
import { createLogger } from '../utils/logger.js';
import { CacheManager } from './cacheManager.js';
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

    try {
      this.isRunning = true;
      this.lastRun = new Date();
      logger.info('Starting scheduled denominational grants scraping cycle');

      const startTime = Date.now();
      const results = await this.scraper.runScrapingCycle();
      const duration = Date.now() - startTime;

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

    try {
      this.isRunning = true;
      logger.info(`Starting manual scraping${sourceName ? ` for ${sourceName}` : ''}`);

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

      // Update cache
      this.cache.set('latest_denominational_scrape', results, 86400000);

      return results;

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
   * Get latest scraping results from cache
   */
  getLatestResults() {
    return this.cache.get('latest_denominational_scrape');
  }

  /**
   * Get run history from cache
   */
  getRunHistory() {
    return this.cache.get('denominational_scrape_history') || this.runHistory;
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