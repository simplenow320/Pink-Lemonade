/**
 * Cache Manager for API responses
 * JavaScript port of the CacheManager class from app/services/apiManager.py
 */

import crypto from 'crypto';
import NodeCache from 'node-cache';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('CacheManager');

/**
 * Cache manager for API responses with TTL support
 */
export class CacheManager {
  constructor() {
    // Initialize NodeCache with default TTL of 1 hour
    this.cache = new NodeCache({
      stdTTL: 3600, // 1 hour default
      checkperiod: 120, // Check for expired keys every 2 minutes
      useClones: false // Better performance, but be careful with object mutations
    });

    // Track cache statistics
    this.stats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0
    };

    this.cache.on('set', (key, value) => {
      this.stats.sets++;
      logger.debug(`Cache set: ${key}`);
    });

    this.cache.on('del', (key, value) => {
      this.stats.deletes++;
      logger.debug(`Cache delete: ${key}`);
    });

    this.cache.on('expired', (key, value) => {
      logger.debug(`Cache expired: ${key}`);
    });

    logger.info('CacheManager initialized with NodeCache');
  }

  /**
   * Generate cache key from source and params
   * @param {string} source - API source name
   * @param {Object} params - Request parameters
   * @returns {string} Cache key
   */
  getCacheKey(source, params = {}) {
    const paramStr = JSON.stringify(params, Object.keys(params).sort());
    return crypto.createHash('md5').update(`${source}:${paramStr}`).digest('hex');
  }

  /**
   * Get cached data if available and not expired
   * @param {string} source - API source name
   * @param {Object} params - Request parameters
   * @param {number} maxAgeMinutes - Maximum age in minutes (optional, uses per-key TTL if not provided)
   * @returns {any|null} Cached data or null if not found/expired
   */
  get(source, params = {}, maxAgeMinutes = null) {
    const key = this.getCacheKey(source, params);
    
    try {
      const cachedData = this.cache.get(key);
      
      if (cachedData !== undefined) {
        // Additional age check if maxAgeMinutes is specified
        if (maxAgeMinutes !== null && cachedData.timestamp) {
          const now = Date.now();
          const maxAge = maxAgeMinutes * 60 * 1000; // Convert to milliseconds
          
          if (now - cachedData.timestamp > maxAge) {
            this.cache.del(key);
            this.stats.misses++;
            logger.debug(`Cache expired by age check for ${source}: ${key}`);
            return null;
          }
        }
        
        this.stats.hits++;
        logger.debug(`Cache hit for ${source}: ${key}`);
        return cachedData.data || cachedData; // Handle both wrapped and unwrapped data
      }
      
      this.stats.misses++;
      logger.debug(`Cache miss for ${source}: ${key}`);
      return null;
    } catch (error) {
      logger.error(`Cache get error for ${source}: ${error.message}`);
      this.stats.misses++;
      return null;
    }
  }

  /**
   * Cache data with timestamp and optional TTL
   * @param {string} source - API source name
   * @param {Object} params - Request parameters
   * @param {any} data - Data to cache
   * @param {number} ttlMinutes - Time to live in minutes (optional)
   */
  set(source, params = {}, data, ttlMinutes = null) {
    const key = this.getCacheKey(source, params);
    
    try {
      // Wrap data with timestamp for additional age tracking
      const wrappedData = {
        data: data,
        timestamp: Date.now(),
        source: source,
        params: params
      };

      if (ttlMinutes !== null) {
        const ttlSeconds = ttlMinutes * 60;
        this.cache.set(key, wrappedData, ttlSeconds);
        logger.debug(`Cached data for ${source} with TTL ${ttlMinutes}m: ${key}`);
      } else {
        this.cache.set(key, wrappedData);
        logger.debug(`Cached data for ${source} with default TTL: ${key}`);
      }
    } catch (error) {
      logger.error(`Cache set error for ${source}: ${error.message}`);
    }
  }

  /**
   * Delete cached data for a specific source and params
   * @param {string} source - API source name
   * @param {Object} params - Request parameters
   * @returns {boolean} True if key was deleted
   */
  delete(source, params = {}) {
    const key = this.getCacheKey(source, params);
    const deleted = this.cache.del(key);
    
    if (deleted > 0) {
      logger.debug(`Cache deleted for ${source}: ${key}`);
      return true;
    }
    
    return false;
  }

  /**
   * Clear all cached data for a source (or all data if no source specified)
   * @param {string} source - API source name (optional)
   */
  clear(source = null) {
    if (source) {
      // Clear all keys for a specific source
      const keys = this.cache.keys();
      const sourceKeys = keys.filter(key => {
        const cachedData = this.cache.get(key);
        return cachedData && cachedData.source === source;
      });
      
      this.cache.del(sourceKeys);
      logger.info(`Cleared ${sourceKeys.length} cache entries for ${source}`);
    } else {
      // Clear all cache
      this.cache.flushAll();
      logger.info('Cleared all cache entries');
    }
  }

  /**
   * Get cache statistics
   * @returns {Object} Cache statistics
   */
  getStats() {
    const cacheStats = this.cache.getStats();
    const hitRate = this.stats.hits + this.stats.misses > 0 
      ? (this.stats.hits / (this.stats.hits + this.stats.misses) * 100).toFixed(2)
      : 0;

    return {
      ...this.stats,
      hitRate: `${hitRate}%`,
      keys: cacheStats.keys,
      ksize: cacheStats.ksize,
      vsize: cacheStats.vsize
    };
  }

  /**
   * Get information about all cached entries
   * @returns {Array} Array of cache entry information
   */
  getCacheInfo() {
    const keys = this.cache.keys();
    const info = [];

    for (const key of keys) {
      const cachedData = this.cache.get(key);
      if (cachedData) {
        const ttl = this.cache.getTtl(key);
        info.push({
          key,
          source: cachedData.source,
          timestamp: new Date(cachedData.timestamp).toISOString(),
          ttl: ttl ? new Date(ttl).toISOString() : null,
          size: JSON.stringify(cachedData).length
        });
      }
    }

    return info.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  }

  /**
   * Check if data exists in cache
   * @param {string} source - API source name
   * @param {Object} params - Request parameters
   * @returns {boolean} True if data exists in cache
   */
  has(source, params = {}) {
    const key = this.getCacheKey(source, params);
    return this.cache.has(key);
  }

  /**
   * Get remaining TTL for cached data
   * @param {string} source - API source name
   * @param {Object} params - Request parameters
   * @returns {number|null} Remaining TTL in seconds, or null if not found
   */
  getTtl(source, params = {}) {
    const key = this.getCacheKey(source, params);
    const ttl = this.cache.getTtl(key);
    
    if (ttl) {
      return Math.max(0, Math.floor((ttl - Date.now()) / 1000));
    }
    
    return null;
  }
}

export default CacheManager;