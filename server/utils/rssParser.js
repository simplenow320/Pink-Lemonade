/**
 * RSS Feed Parser Utility
 * Handles parsing of RSS/XML feeds from government agencies and other sources
 */

import axios from 'axios';
import { XMLParser } from 'fast-xml-parser';
import { createLogger } from './logger.js';
import { createStandardizedGrant, retryWithBackoff } from './apiUtils.js';

const logger = createLogger('RSSParser');

/**
 * RSS Feed Parser for grant opportunities
 */
export class RSSParser {
  constructor() {
    // Configure XML parser options
    this.xmlParserOptions = {
      ignoreAttributes: false,
      attributeNamePrefix: '@_',
      ignoreNameSpace: false,
      allowBooleanAttributes: true,
      parseNodeValue: true,
      parseAttributeValue: true,
      trimValues: true,
      cdataTagName: '__cdata',
      cdataPositionChar: '\\c',
      processEntities: true,
      htmlEntities: true
    };
    
    this.parser = new XMLParser(this.xmlParserOptions);
    
    // Common RSS field mappings
    this.rssFieldMappings = {
      title: ['title', 'name'],
      description: ['description', 'summary', 'content', 'content:encoded'],
      link: ['link', 'url', 'guid'],
      publishedDate: ['pubDate', 'published', 'dc:date', 'date'],
      category: ['category', 'dc:subject'],
      author: ['author', 'dc:creator']
    };
  }

  /**
   * Parse RSS feed from URL
   * @param {string} feedUrl - RSS feed URL
   * @param {string} source - Source identifier
   * @param {Object} options - Parsing options
   * @returns {Promise<Array>} Array of standardized grant objects
   */
  async parseRSSFeed(feedUrl, source, options = {}) {
    const {
      maxRetries = 3,
      timeout = 30000,
      customFieldMappings = {},
      filterKeywords = [],
      maxItems = 100
    } = options;

    try {
      logger.info(`Fetching RSS feed from ${feedUrl}`);
      
      const response = await retryWithBackoff(
        () => axios.get(feedUrl, {
          timeout,
          headers: {
            'User-Agent': 'Mozilla/5.0 (compatible; PinkLemonade/1.0)',
            'Accept': 'application/rss+xml, application/xml, text/xml'
          }
        }),
        maxRetries
      );

      const xmlData = response.data;
      logger.debug(`Retrieved ${xmlData.length} bytes of XML data from ${feedUrl}`);

      return await this.parseXMLContent(xmlData, source, {
        customFieldMappings,
        filterKeywords,
        maxItems
      });

    } catch (error) {
      logger.error(`Failed to parse RSS feed ${feedUrl}: ${error.message}`);
      throw error;
    }
  }

  /**
   * Parse XML content directly
   * @param {string} xmlContent - XML content string
   * @param {string} source - Source identifier
   * @param {Object} options - Parsing options
   * @returns {Promise<Array>} Array of standardized grant objects
   */
  async parseXMLContent(xmlContent, source, options = {}) {
    const {
      customFieldMappings = {},
      filterKeywords = [],
      maxItems = 100
    } = options;

    try {
      const jsonObj = this.parser.parse(xmlContent);
      logger.debug('XML parsed to JSON successfully');

      // Extract items from different RSS/Atom formats
      const items = this._extractItemsFromFeed(jsonObj);
      logger.info(`Found ${items.length} items in RSS feed`);

      if (!items.length) {
        logger.warn('No items found in RSS feed');
        return [];
      }

      // Convert items to standardized grants
      const grants = [];
      const fieldMappings = { ...this.rssFieldMappings, ...customFieldMappings };

      for (const item of items.slice(0, maxItems)) {
        try {
          // Apply keyword filtering if specified
          if (filterKeywords.length > 0 && !this._matchesKeywords(item, filterKeywords)) {
            continue;
          }

          const standardGrant = this._convertRSSItemToGrant(item, source, fieldMappings);
          if (standardGrant && standardGrant.title) {
            grants.push(standardGrant);
          }
        } catch (itemError) {
          logger.warn(`Failed to process RSS item: ${itemError.message}`);
        }
      }

      logger.info(`Converted ${grants.length} RSS items to standardized grants`);
      return grants;

    } catch (error) {
      logger.error(`Failed to parse XML content: ${error.message}`);
      throw error;
    }
  }

  /**
   * Extract items array from various RSS/Atom feed formats
   * @param {Object} feedData - Parsed JSON feed data
   * @returns {Array} Array of feed items
   */
  _extractItemsFromFeed(feedData) {
    // Try different feed formats
    const possiblePaths = [
      'rss.channel.item',      // RSS 2.0
      'rdf:RDF.item',          // RSS 1.0
      'feed.entry',            // Atom
      'channel.item',          // Direct channel
      'items.item',            // Some custom formats
      'feed.item'              // Alternative Atom
    ];

    for (const path of possiblePaths) {
      const items = this._getNestedValue(feedData, path);
      if (items) {
        // Ensure we return an array
        return Array.isArray(items) ? items : [items];
      }
    }

    logger.warn('No items found in feed structure');
    return [];
  }

  /**
   * Convert RSS item to standardized grant object
   * @param {Object} item - RSS item
   * @param {string} source - Source identifier
   * @param {Object} fieldMappings - Field mapping configuration
   * @returns {Object} Standardized grant object
   */
  _convertRSSItemToGrant(item, source, fieldMappings) {
    // Extract core RSS fields
    const title = this._extractFieldValue(item, fieldMappings.title);
    const description = this._extractFieldValue(item, fieldMappings.description);
    const link = this._extractFieldValue(item, fieldMappings.link);
    const publishedDate = this._extractFieldValue(item, fieldMappings.publishedDate);
    const category = this._extractFieldValue(item, fieldMappings.category);

    // Generate ID from title and link
    const id = this._generateIdFromRSSItem(item, title, link);

    // Create standardized grant object
    const grant = createStandardizedGrant({
      id,
      title: this._cleanText(title),
      description: this._cleanText(description),
      url: link,
      category,
      publishedDate,
      source_item: item // Keep original for reference
    }, source);

    // Set specific RSS metadata
    grant.posted_date = this._parseDate(publishedDate);
    grant.funder = this._inferFunderFromSource(source);
    grant.source_type = 'rss';

    return grant;
  }

  /**
   * Extract field value using multiple possible field names
   * @param {Object} item - RSS item
   * @param {Array} fieldNames - Possible field names
   * @returns {string|null} Extracted value
   */
  _extractFieldValue(item, fieldNames) {
    for (const fieldName of fieldNames) {
      const value = this._getNestedValue(item, fieldName);
      if (value !== null && value !== undefined) {
        // Handle CDATA sections
        if (typeof value === 'object' && value.__cdata) {
          return value.__cdata;
        }
        return String(value);
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
  _getNestedValue(obj, path) {
    if (!obj || !path) return null;
    
    return path.split('.').reduce((current, key) => {
      return (current && current[key] !== undefined) ? current[key] : null;
    }, obj);
  }

  /**
   * Generate unique ID from RSS item
   * @param {Object} item - RSS item
   * @param {string} title - Item title
   * @param {string} link - Item link
   * @returns {string} Generated ID
   */
  _generateIdFromRSSItem(item, title, link) {
    // Try to find existing GUID first
    const guid = this._extractFieldValue(item, ['guid', 'id']);
    if (guid) {
      return guid;
    }

    // Generate ID from link if available
    if (link) {
      const url = new URL(link);
      const pathParts = url.pathname.split('/').filter(p => p);
      if (pathParts.length > 0) {
        return pathParts[pathParts.length - 1];
      }
    }

    // Generate ID from title
    if (title) {
      return title.toLowerCase()
        .replace(/[^a-z0-9\s]/g, '')
        .replace(/\s+/g, '-')
        .substring(0, 50);
    }

    // Fallback to timestamp
    return `rss-${Date.now()}`;
  }

  /**
   * Clean text content (remove HTML tags, extra whitespace)
   * @param {string} text - Raw text
   * @returns {string} Cleaned text
   */
  _cleanText(text) {
    if (!text) return null;

    return text
      .replace(/<[^>]*>/g, '') // Remove HTML tags
      .replace(/&[a-z]+;/gi, ' ') // Remove HTML entities
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim();
  }

  /**
   * Parse date from RSS item
   * @param {string} dateStr - Date string
   * @returns {string|null} ISO date string or null
   */
  _parseDate(dateStr) {
    if (!dateStr) return null;

    try {
      const date = new Date(dateStr);
      return isNaN(date.getTime()) ? null : date.toISOString();
    } catch (error) {
      logger.debug(`Failed to parse RSS date: ${dateStr}`);
      return null;
    }
  }

  /**
   * Infer funder name from source identifier
   * @param {string} source - Source identifier
   * @returns {string} Inferred funder name
   */
  _inferFunderFromSource(source) {
    const funderMap = {
      'hhs_grants': 'Department of Health and Human Services',
      'ed_grants': 'Department of Education',
      'nsf_grants': 'National Science Foundation',
      'federal_register': 'Federal Register',
      'govinfo': 'U.S. Government Publishing Office'
    };

    return funderMap[source] || source.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  /**
   * Check if RSS item matches filter keywords
   * @param {Object} item - RSS item
   * @param {Array} keywords - Filter keywords
   * @returns {boolean} True if matches
   */
  _matchesKeywords(item, keywords) {
    if (!keywords.length) return true;

    const searchText = [
      this._extractFieldValue(item, this.rssFieldMappings.title),
      this._extractFieldValue(item, this.rssFieldMappings.description),
      this._extractFieldValue(item, this.rssFieldMappings.category)
    ].filter(Boolean).join(' ').toLowerCase();

    return keywords.some(keyword => 
      searchText.includes(keyword.toLowerCase())
    );
  }
}

// Export singleton instance
export const rssParser = new RSSParser();
export default rssParser;