/**
 * Database Persistence Service
 * Provides database persistence for denominational grant scraping results
 * Replaces in-memory CacheManager with durable PostgreSQL storage
 */

import { createLogger } from '../utils/logger.js';
import pkg from 'pg';
const { Pool } = pkg;

const logger = createLogger('DatabasePersistence');

export class DatabasePersistence {
  constructor() {
    this.pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
    });
    
    this.initializeTables();
  }

  /**
   * Initialize database tables for denominational scraping
   */
  async initializeTables() {
    try {
      // Create denominational_scrape_runs table for tracking scrape history
      await this.pool.query(`
        CREATE TABLE IF NOT EXISTS denominational_scrape_runs (
          id SERIAL PRIMARY KEY,
          run_id VARCHAR(255) UNIQUE NOT NULL,
          status VARCHAR(50) NOT NULL DEFAULT 'running',
          started_at TIMESTAMP NOT NULL DEFAULT NOW(),
          completed_at TIMESTAMP NULL,
          sources_processed INTEGER DEFAULT 0,
          successful_sources INTEGER DEFAULT 0,
          total_opportunities INTEGER DEFAULT 0,
          errors JSONB DEFAULT '[]'::JSONB,
          metadata JSONB DEFAULT '{}'::JSONB,
          created_at TIMESTAMP DEFAULT NOW(),
          updated_at TIMESTAMP DEFAULT NOW()
        )
      `);

      // Create denominational_grants table for scraped grant data
      await this.pool.query(`
        CREATE TABLE IF NOT EXISTS denominational_grants (
          id SERIAL PRIMARY KEY,
          external_id VARCHAR(255) UNIQUE,
          title VARCHAR(500) NOT NULL,
          funder VARCHAR(255),
          source_name VARCHAR(255) NOT NULL,
          source_url TEXT,
          link TEXT,
          amount_min DECIMAL(14,2),
          amount_max DECIMAL(14,2),
          deadline DATE,
          geography VARCHAR(255),
          eligibility TEXT,
          description TEXT,
          requirements TEXT,
          contact_info JSONB DEFAULT '{}'::JSONB,
          ai_enhanced_data JSONB DEFAULT '{}'::JSONB,
          scrape_metadata JSONB DEFAULT '{}'::JSONB,
          created_at TIMESTAMP DEFAULT NOW(),
          updated_at TIMESTAMP DEFAULT NOW(),
          scraped_at TIMESTAMP DEFAULT NOW()
        )
      `);

      // Create index for efficient queries
      await this.pool.query(`
        CREATE INDEX IF NOT EXISTS idx_denominational_grants_source 
        ON denominational_grants (source_name)
      `);
      
      await this.pool.query(`
        CREATE INDEX IF NOT EXISTS idx_denominational_grants_deadline 
        ON denominational_grants (deadline)
      `);

      logger.info('Database tables initialized successfully');
    } catch (error) {
      logger.error(`Failed to initialize database tables: ${error.message}`);
      throw error;
    }
  }

  /**
   * Store scraped denominational grants
   */
  async storeScrapedGrants(grants, runId) {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');

      let insertedCount = 0;
      let updatedCount = 0;

      for (const grant of grants) {
        const {
          title, funder, source_name, source_url, link, 
          amount_min, amount_max, deadline, geography,
          eligibility, description, requirements, contact_info,
          ai_enhanced_data, external_id
        } = grant;

        const scrapeMetadata = {
          run_id: runId,
          scraped_at: new Date().toISOString(),
          source_name
        };

        try {
          // Try to update existing grant first (based on external_id or unique combination)
          const updateResult = await client.query(`
            UPDATE denominational_grants 
            SET title = $1, funder = $2, source_url = $3, link = $4,
                amount_min = $5, amount_max = $6, deadline = $7, geography = $8,
                eligibility = $9, description = $10, requirements = $11,
                contact_info = $12, ai_enhanced_data = $13, scrape_metadata = $14,
                updated_at = NOW(), scraped_at = NOW()
            WHERE external_id = $15 OR (title = $1 AND source_name = $2)
            RETURNING id
          `, [
            title, funder, source_url, link, amount_min, amount_max, 
            deadline, geography, eligibility, description, requirements,
            JSON.stringify(contact_info || {}), JSON.stringify(ai_enhanced_data || {}),
            JSON.stringify(scrapeMetadata), external_id
          ]);

          if (updateResult.rowCount === 0) {
            // Insert new grant
            await client.query(`
              INSERT INTO denominational_grants (
                external_id, title, funder, source_name, source_url, link,
                amount_min, amount_max, deadline, geography, eligibility,
                description, requirements, contact_info, ai_enhanced_data,
                scrape_metadata
              ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            `, [
              external_id || `${source_name}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              title, funder, source_name, source_url, link, amount_min, amount_max,
              deadline, geography, eligibility, description, requirements,
              JSON.stringify(contact_info || {}), JSON.stringify(ai_enhanced_data || {}),
              JSON.stringify(scrapeMetadata)
            ]);
            insertedCount++;
          } else {
            updatedCount++;
          }
        } catch (grantError) {
          logger.warn(`Failed to store grant "${title}": ${grantError.message}`);
        }
      }

      await client.query('COMMIT');
      logger.info(`Stored ${insertedCount} new and updated ${updatedCount} existing denominational grants`);
      
      return { insertedCount, updatedCount };
    } catch (error) {
      await client.query('ROLLBACK');
      logger.error(`Failed to store scraped grants: ${error.message}`);
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Create a new scrape run record
   */
  async createScrapeRun(runId, metadata = {}) {
    try {
      const result = await this.pool.query(`
        INSERT INTO denominational_scrape_runs (run_id, status, metadata)
        VALUES ($1, 'running', $2)
        RETURNING *
      `, [runId, JSON.stringify(metadata)]);

      logger.info(`Created scrape run: ${runId}`);
      return result.rows[0];
    } catch (error) {
      logger.error(`Failed to create scrape run: ${error.message}`);
      throw error;
    }
  }

  /**
   * Update scrape run status and results
   */
  async updateScrapeRun(runId, updates) {
    try {
      const {
        status, sourcesProcessed, successfulSources, 
        totalOpportunities, errors, completedAt
      } = updates;

      const result = await this.pool.query(`
        UPDATE denominational_scrape_runs
        SET status = $1, sources_processed = $2, successful_sources = $3,
            total_opportunities = $4, errors = $5, completed_at = $6, 
            updated_at = NOW()
        WHERE run_id = $7
        RETURNING *
      `, [
        status, sourcesProcessed, successfulSources, totalOpportunities,
        JSON.stringify(errors || []), completedAt, runId
      ]);

      if (result.rows.length === 0) {
        throw new Error(`Scrape run not found: ${runId}`);
      }

      return result.rows[0];
    } catch (error) {
      logger.error(`Failed to update scrape run: ${error.message}`);
      throw error;
    }
  }

  /**
   * Get latest denominational grants with pagination and filtering
   */
  async getLatestGrants(options = {}) {
    try {
      const { 
        limit = 50, 
        offset = 0, 
        source = null, 
        deadline_after = null,
        search_term = null
      } = options;

      let whereConditions = [];
      let params = [];
      let paramIndex = 1;

      if (source) {
        whereConditions.push(`source_name = $${paramIndex++}`);
        params.push(source);
      }

      if (deadline_after) {
        whereConditions.push(`deadline >= $${paramIndex++}`);
        params.push(deadline_after);
      }

      if (search_term) {
        whereConditions.push(`(title ILIKE $${paramIndex++} OR funder ILIKE $${paramIndex++})`);
        params.push(`%${search_term}%`, `%${search_term}%`);
        paramIndex++;
      }

      const whereClause = whereConditions.length > 0 
        ? `WHERE ${whereConditions.join(' AND ')}`
        : '';

      const countResult = await this.pool.query(`
        SELECT COUNT(*) as total FROM denominational_grants ${whereClause}
      `, params);

      const grantsResult = await this.pool.query(`
        SELECT * FROM denominational_grants 
        ${whereClause}
        ORDER BY scraped_at DESC, created_at DESC
        LIMIT $${paramIndex++} OFFSET $${paramIndex++}
      `, [...params, limit, offset]);

      return {
        grants: grantsResult.rows,
        total: parseInt(countResult.rows[0].total),
        limit,
        offset
      };
    } catch (error) {
      logger.error(`Failed to get latest grants: ${error.message}`);
      throw error;
    }
  }

  /**
   * Get scrape run history
   */
  async getScrapeRunHistory(limit = 10) {
    try {
      const result = await this.pool.query(`
        SELECT * FROM denominational_scrape_runs
        ORDER BY started_at DESC
        LIMIT $1
      `, [limit]);

      return result.rows;
    } catch (error) {
      logger.error(`Failed to get scrape run history: ${error.message}`);
      throw error;
    }
  }

  /**
   * Get current scraping status
   */
  async getScrapingStatus() {
    try {
      const runningResult = await this.pool.query(`
        SELECT COUNT(*) as count FROM denominational_scrape_runs 
        WHERE status = 'running'
      `);

      const lastRunResult = await this.pool.query(`
        SELECT * FROM denominational_scrape_runs
        ORDER BY started_at DESC
        LIMIT 1
      `);

      const totalGrantsResult = await this.pool.query(`
        SELECT COUNT(*) as count FROM denominational_grants
      `);

      const recentGrantsResult = await this.pool.query(`
        SELECT COUNT(*) as count FROM denominational_grants
        WHERE scraped_at >= NOW() - INTERVAL '7 days'
      `);

      return {
        isRunning: parseInt(runningResult.rows[0].count) > 0,
        lastRun: lastRunResult.rows[0] || null,
        totalGrants: parseInt(totalGrantsResult.rows[0].count),
        recentGrants: parseInt(recentGrantsResult.rows[0].count)
      };
    } catch (error) {
      logger.error(`Failed to get scraping status: ${error.message}`);
      throw error;
    }
  }

  /**
   * Clean up old data
   */
  async cleanupOldData(daysToKeep = 90) {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');

      // Delete old scrape runs
      const oldRunsResult = await client.query(`
        DELETE FROM denominational_scrape_runs 
        WHERE started_at < NOW() - INTERVAL '${daysToKeep} days'
      `);

      // Delete old grants that haven't been updated recently
      const oldGrantsResult = await client.query(`
        DELETE FROM denominational_grants 
        WHERE scraped_at < NOW() - INTERVAL '${daysToKeep} days'
        AND updated_at < NOW() - INTERVAL '${daysToKeep} days'
      `);

      await client.query('COMMIT');

      logger.info(`Cleanup completed: deleted ${oldRunsResult.rowCount} old runs and ${oldGrantsResult.rowCount} old grants`);
      
      return {
        deletedRuns: oldRunsResult.rowCount,
        deletedGrants: oldGrantsResult.rowCount
      };
    } catch (error) {
      await client.query('ROLLBACK');
      logger.error(`Failed to cleanup old data: ${error.message}`);
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Close database connection pool
   */
  async close() {
    await this.pool.end();
    logger.info('Database connection pool closed');
  }
}

export const databasePersistence = new DatabasePersistence();