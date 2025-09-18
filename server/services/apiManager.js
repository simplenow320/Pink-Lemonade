/**
 * Unified API & Data Integration Manager
 * Handles all external API calls and data source integrations
 * JavaScript port of app/services/apiManager.py
 */

import axios from 'axios';
import { APIConfig } from '../config/apiConfig.js';
import { CircuitBreaker } from './circuitBreaker.js';
import { RateLimiter } from './rateLimiter.js';
import { CacheManager } from './cacheManager.js';
import { credentialManager } from './credentialManager.js';
import { createLogger } from '../utils/logger.js';
import { 
  retryWithBackoff, 
  createStandardizedGrant, 
  createAuthHeaders, 
  buildQueryParams, 
  formatUrl,
  validateGrantObject
} from '../utils/apiUtils.js';
import { rssParser } from '../utils/rssParser.js';

const logger = createLogger('APIManager');

/**
 * Enhanced Central API Manager for all grant data sources
 */
export class APIManager {
  constructor() {
    this.config = new APIConfig();
    this.rateLimiter = new RateLimiter();
    this.cache = new CacheManager();
    this.circuitBreakers = new Map(); // Circuit breakers for each source
    this.sources = this._initializeSources();
    this._initializeCircuitBreakers();
    
    // Configure axios defaults
    this._configureAxios();
    
    logger.info(`Initialized APIManager with ${Object.keys(this.sources).length} enabled sources and circuit breakers`);
  }

  /**
   * Configure axios with sensible defaults
   */
  _configureAxios() {
    // Set default timeout
    axios.defaults.timeout = 30000; // 30 seconds
    
    // Add request interceptor for logging
    axios.interceptors.request.use(
      (config) => {
        logger.debug(`Making request to ${config.url}`);
        return config;
      },
      (error) => {
        logger.error(`Request error: ${error.message}`);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    axios.interceptors.response.use(
      (response) => {
        logger.debug(`Received response from ${response.config.url} - Status: ${response.status}`);
        return response;
      },
      (error) => {
        if (error.response) {
          logger.warn(`HTTP error ${error.response.status} from ${error.config?.url}: ${error.response.statusText}`);
        } else if (error.request) {
          logger.error(`Network error for ${error.config?.url}: ${error.message}`);
        } else {
          logger.error(`Request setup error: ${error.message}`);
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Initialize all API sources from enhanced config
   */
  _initializeSources() {
    const sources = {};
    const enabledSources = this.config.getEnabledSources();
    
    for (const [sourceId, sourceConfig] of Object.entries(enabledSources)) {
      sources[sourceId] = sourceConfig;
      const authStatus = sourceConfig.api_key ? "with credentials" : "public";
      logger.info(`Initialized source: ${sourceId} (${authStatus})`);
    }
    
    return sources;
  }

  /**
   * Initialize circuit breakers for all sources
   */
  _initializeCircuitBreakers() {
    for (const sourceId of Object.keys(this.sources)) {
      const sourceConfig = this.sources[sourceId];

      // Use more strict settings for credential-required sources
      let failureThreshold, cooldownMinutes;
      if (sourceConfig.credential_required) {
        failureThreshold = 3;  // Fail faster for auth issues
        cooldownMinutes = 30;  // Longer cooldown for credential issues
      } else {
        failureThreshold = 5;  // More tolerant for public APIs
        cooldownMinutes = 15;  // Shorter cooldown for general issues
      }

      this.circuitBreakers.set(sourceId, new CircuitBreaker(
        sourceId,
        failureThreshold,
        cooldownMinutes,
        2  // Conservative recovery testing
      ));
    }

    logger.info(`Initialized circuit breakers for ${this.circuitBreakers.size} sources`);
  }

  /**
   * Fetch grants from a specific source with circuit breaker protection
   * @param {string} sourceName - Name of the API source
   * @param {Object} params - Request parameters
   * @returns {Promise<Array>} List of standardized grant objects
   */
  async getGrantsFromSource(sourceName, params = {}) {
    // Check if source is enabled
    if (!this.sources[sourceName]) {
      logger.warn(`Source ${sourceName} not found or disabled`);
      return [];
    }

    // Check circuit breaker - don't proceed if circuit is open
    const circuitBreaker = this.circuitBreakers.get(sourceName);
    if (circuitBreaker && !circuitBreaker.canExecute()) {
      logger.info(`Circuit breaker for ${sourceName} is ${circuitBreaker.state} - skipping call`);
      return [];
    }

    // Check cache first
    const cachedData = this.cache.get(sourceName, params);
    if (cachedData) {
      logger.debug(`Returning cached data for ${sourceName}`);
      return cachedData;
    }

    // Check rate limit
    const sourceConfig = this.sources[sourceName];
    const rateLimit = sourceConfig.rate_limit || { calls: 10, period: 60 };
    if (!this.rateLimiter.checkRateLimit(sourceName, rateLimit.calls, rateLimit.period)) {
      logger.warn(`Rate limit exceeded for ${sourceName}`);
      return []; // Return empty when rate limited
    }

    // Route to appropriate fetcher with enhanced circuit breaker error handling
    try {
      const grants = await this._dispatchToFetcher(sourceName, params);

      // Record success in circuit breaker
      if (circuitBreaker) {
        circuitBreaker.recordSuccess();
      }

      if (!grants || grants.length === 0) {
        logger.info(`No data returned from ${sourceName}`);
      } else {
        // Cache successful response
        const cacheTimeout = sourceConfig.cache_ttl || 60;
        this.cache.set(sourceName, params, grants, cacheTimeout);
        logger.info(`Retrieved ${grants.length} grants from ${sourceName}`);
      }

      return grants || [];

    } catch (error) {
      // Record failure in circuit breaker with error classification
      const isCredentialError = this._isCredentialError(error);
      const isRateLimitError = this._isRateLimitError(error);

      if (circuitBreaker) {
        circuitBreaker.recordFailure(error.message, isCredentialError);
      }

      // Log errors based on type
      if (isCredentialError) {
        logger.warn(`Authentication failed for ${sourceName} - circuit breaker updated`);
      } else if (isRateLimitError) {
        logger.warn(`Rate limit exceeded for ${sourceName}`);
      } else {
        logger.error(`Error fetching from ${sourceName}: ${error.message}`);
      }

      return []; // Return empty on error, never fake data
    }
  }

  /**
   * Get all enabled sources with their configurations
   */
  getEnabledSources() {
    return this.sources;
  }

  /**
   * Search grants from a specific source - alias for getGrantsFromSource
   */
  async searchGrants(sourceName, params = {}) {
    return this.getGrantsFromSource(sourceName, params);
  }

  /**
   * Search for grant opportunities across all enabled sources
   * @param {string} query - Search query
   * @param {Object} filters - Additional filters
   * @returns {Promise<Array>} Array of grant opportunities
   */
  async searchOpportunities(query, filters = {}) {
    const allGrants = [];
    const promises = [];

    // Search each enabled source in parallel
    for (const sourceName of Object.keys(this.sources)) {
      const params = { query, ...filters };
      promises.push(
        this.getGrantsFromSource(sourceName, params)
          .then(grants => ({ sourceName, grants }))
          .catch(error => {
            logger.error(`Error searching ${sourceName}: ${error.message}`);
            return { sourceName, grants: [] };
          })
      );
    }

    // Wait for all searches to complete
    const results = await Promise.allSettled(promises);
    
    for (const result of results) {
      if (result.status === 'fulfilled') {
        allGrants.push(...result.value.grants);
      }
    }

    // Deduplicate and sort by relevance
    const seen = new Set();
    const uniqueGrants = [];
    
    for (const grant of allGrants) {
      const grantId = `${grant.title || ''}:${grant.funder || ''}`;
      if (!seen.has(grantId)) {
        seen.add(grantId);
        uniqueGrants.push(grant);
      }
    }

    logger.info(`Found ${uniqueGrants.length} unique grants from ${Object.keys(this.sources).length} sources`);
    return uniqueGrants;
  }

  /**
   * Fetch detailed information about a specific grant
   * @param {string} grantId - Grant identifier
   * @param {string} source - Specific source to search (optional)
   * @returns {Promise<Object|null>} Grant details or null
   */
  async fetchGrantDetails(grantId, source = null) {
    if (source && this.sources[source]) {
      const params = { grant_id: grantId };
      const grants = await this.getGrantsFromSource(source, params);
      return grants.length > 0 ? grants[0] : null;
    }

    // Try all sources if source not specified
    for (const sourceName of Object.keys(this.sources)) {
      try {
        const params = { grant_id: grantId };
        const grants = await this.getGrantsFromSource(sourceName, params);
        if (grants.length > 0) {
          return grants[0];
        }
      } catch (error) {
        logger.debug(`Failed to fetch grant ${grantId} from ${sourceName}: ${error.message}`);
      }
    }

    return null;
  }

  /**
   * Get new grant opportunities for a watchlist since last check
   * @param {string} watchlistId - Watchlist identifier
   * @param {Date} lastCheck - Last check timestamp
   * @returns {Promise<Array>} Array of new grants
   */
  async getWatchlistUpdates(watchlistId, lastCheck = null) {
    const allGrants = [];
    const promises = [];

    for (const sourceName of Object.keys(this.sources)) {
      const params = {
        since: lastCheck ? lastCheck.toISOString() : null,
        watchlist_id: watchlistId
      };
      promises.push(this.getGrantsFromSource(sourceName, params));
    }

    const results = await Promise.allSettled(promises);
    
    for (const result of results) {
      if (result.status === 'fulfilled') {
        allGrants.push(...result.value);
      }
    }

    return allGrants;
  }

  /**
   * Dispatch to appropriate fetcher method based on source name
   * @param {string} sourceName - Name of the API source
   * @param {Object} params - Request parameters
   * @returns {Promise<Array>} Array of grants
   */
  async _dispatchToFetcher(sourceName, params) {
    // Existing sources
    const fetcherMap = {
      grants_gov: () => this._fetchGrantsGov(params),
      federal_register: () => this._fetchFederalRegister(params),
      govinfo: () => this._fetchGovInfo(params),
      philanthropy_news: () => this._fetchPhilanthropyNews(params),
      foundation_directory: () => this._fetchFoundationDirectory(params),
      grantwatch: () => this._fetchGrantWatch(params),
      michigan_portal: () => this._fetchMichiganPortal(params),
      georgia_portal: () => this._fetchGeorgiaPortal(params),
      // New API sources
      sam_gov_opportunities: () => this._fetchSamGovOpportunities(params),
      sam_gov_entity: () => this._fetchSamGovEntity(params),
      michigan_socrata: () => this._fetchMichiganSocrata(params),
      zyte_api: () => this._fetchZyteApi(params),
      hhs_grants: () => this._fetchHhsGrants(params),
      ed_grants: () => this._fetchEdGrants(params),
      nsf_grants: () => this._fetchNsfGrants(params)
    };

    const fetcher = fetcherMap[sourceName];
    if (!fetcher) {
      logger.warn(`Unknown source: ${sourceName}`);
      return [];
    }

    return await fetcher();
  }

  /**
   * Check if error is related to credentials/authentication
   */
  _isCredentialError(error) {
    const errorStr = error.message?.toLowerCase() || '';
    const errorIndicators = [
      '401', '403', 'unauthorized', 'forbidden', 'invalid_grant',
      'access_denied', 'invalid_token', 'authentication failed',
      'invalid_client', 'invalid credentials', 'api key'
    ];
    return errorIndicators.some(indicator => errorStr.includes(indicator));
  }

  /**
   * Check if error is related to rate limiting
   */
  _isRateLimitError(error) {
    const errorStr = error.message?.toLowerCase() || '';
    const rateLimitIndicators = [
      '429', 'rate limit', 'too many requests', 'quota exceeded',
      'throttled', 'rate exceeded'
    ];
    return rateLimitIndicators.some(indicator => errorStr.includes(indicator));
  }

  /**
   * Get circuit breaker status for one or all sources
   */
  getCircuitBreakerStatus(sourceName = null) {
    if (sourceName) {
      const circuitBreaker = this.circuitBreakers.get(sourceName);
      if (circuitBreaker) {
        return circuitBreaker.getStatus();
      }
      return { error: `No circuit breaker found for source: ${sourceName}` };
    }

    // Return status for all sources
    const status = {};
    for (const [name, breaker] of this.circuitBreakers.entries()) {
      status[name] = breaker.getStatus();
    }
    return status;
  }

  /**
   * Manually reset a circuit breaker
   */
  resetCircuitBreaker(sourceName) {
    const circuitBreaker = this.circuitBreakers.get(sourceName);
    if (circuitBreaker) {
      circuitBreaker.reset();
      logger.info(`Circuit breaker for ${sourceName} manually reset`);
      return true;
    }
    logger.warn(`No circuit breaker found for source: ${sourceName}`);
    return false;
  }

  /**
   * Get summary of all circuit breaker states
   */
  getCircuitBreakerSummary() {
    const summary = {
      totalSources: this.circuitBreakers.size,
      openCircuits: 0,
      halfOpenCircuits: 0,
      closedCircuits: 0,
      sourcesByState: {
        open: [],
        half_open: [],
        closed: []
      },
      totalFailures: 0,
      totalCalls: 0
    };

    for (const [sourceName, breaker] of this.circuitBreakers.entries()) {
      const status = breaker.getStatus();
      const state = status.state;

      if (state === 'open') {
        summary.openCircuits++;
        summary.sourcesByState.open.push(sourceName);
      } else if (state === 'half_open') {
        summary.halfOpenCircuits++;
        summary.sourcesByState.half_open.push(sourceName);
      } else {
        summary.closedCircuits++;
        summary.sourcesByState.closed.push(sourceName);
      }

      summary.totalFailures += status.totalFailures;
      summary.totalCalls += status.totalCalls;
    }

    return summary;
  }

  // API Client Implementations
  
  /**
   * Grants.gov API Client
   * Implements search2 and fetchOpportunity endpoints
   */
  async _fetchGrantsGov(params) {
    const sourceConfig = this.sources.grants_gov;
    const baseUrl = sourceConfig.base_url;
    const fieldMapping = this.config.getFieldMapping('grants_gov');
    
    try {
      // Handle both search and detail fetch
      if (params.grant_id || params.opportunityId) {
        return await this._fetchGrantsGovDetails(params, sourceConfig, baseUrl);
      } else {
        return await this._fetchGrantsGovSearch(params, sourceConfig, baseUrl, fieldMapping);
      }
    } catch (error) {
      throw new Error(`Grants.gov API error: ${error.message}`);
    }
  }

  async _fetchGrantsGovSearch(params, sourceConfig, baseUrl, fieldMapping) {
    const endpoint = sourceConfig.endpoints?.search || '/opportunities/search';
    const headers = createAuthHeaders(sourceConfig);
    
    const queryParams = buildQueryParams(sourceConfig.params, {
      keyword: params.query,
      oppStatuses: 'posted|closed',
      sortBy: params.sortBy || 'closeDate',
      rows: params.limit || 25,
      startRecordNum: params.offset || 0
    });

    const operation = async () => {
      const response = await axios.get(`${baseUrl}${endpoint}`, {
        params: queryParams,
        headers,
        timeout: 30000
      });
      return response.data;
    };

    const response = await retryWithBackoff(operation, 3);
    return this._transformGrantsGovData(response, fieldMapping);
  }

  async _fetchGrantsGovDetails(params, sourceConfig, baseUrl) {
    const oppId = params.grant_id || params.opportunityId;
    const endpoint = sourceConfig.endpoints?.details || '/opportunity/details/{id}';
    const url = formatUrl(baseUrl, endpoint, {}, { id: oppId });
    const headers = createAuthHeaders(sourceConfig);

    const operation = async () => {
      const response = await axios.get(url, { headers, timeout: 30000 });
      return response.data;
    };

    const response = await retryWithBackoff(operation, 3);
    const fieldMapping = this.config.getFieldMapping('grants_gov');
    return this._transformGrantsGovData(response, fieldMapping);
  }

  /**
   * SAM.gov Get Opportunities API Client
   */
  async _fetchSamGovOpportunities(params) {
    const sourceConfig = this.sources.sam_gov_opportunities;
    if (!sourceConfig?.api_key) {
      logger.warn('SAM.gov Opportunities API key not available');
      return [];
    }

    const baseUrl = sourceConfig.base_url;
    const endpoint = sourceConfig.endpoints?.search || '/search';
    const headers = createAuthHeaders(sourceConfig);
    const fieldMapping = this.config.getFieldMapping('sam_gov_opportunities');

    const queryParams = buildQueryParams(sourceConfig.params, {
      keyword: params.query,
      limit: params.limit || 100,
      offset: params.offset || 0,
      postedFrom: params.postedFrom,
      postedTo: params.postedTo,
      type: 'o' // opportunities
    });

    try {
      const operation = async () => {
        const response = await axios.get(`${baseUrl}${endpoint}`, {
          params: queryParams,
          headers,
          timeout: 30000
        });
        return response.data;
      };

      const response = await retryWithBackoff(operation, sourceConfig.error_handling?.max_retries || 3);
      return this._transformSamGovOpportunitiesData(response, fieldMapping);
    } catch (error) {
      throw new Error(`SAM.gov Opportunities API error: ${error.message}`);
    }
  }

  /**
   * SAM.gov Entity Management API Client
   */
  async _fetchSamGovEntity(params) {
    const sourceConfig = this.sources.sam_gov_entity;
    if (!sourceConfig?.api_key) {
      logger.warn('SAM.gov Entity API key not available');
      return [];
    }

    const baseUrl = sourceConfig.base_url;
    const endpoint = sourceConfig.endpoints?.search || '/entities';
    const headers = createAuthHeaders(sourceConfig);
    const fieldMapping = this.config.getFieldMapping('sam_gov_entity');

    const queryParams = buildQueryParams(sourceConfig.params, {
      entityName: params.query || params.entityName,
      ueiSAM: params.uei,
      cageCode: params.cage_code,
      limit: params.limit || 100
    });

    try {
      const operation = async () => {
        const response = await axios.get(`${baseUrl}${endpoint}`, {
          params: queryParams,
          headers,
          timeout: 30000
        });
        return response.data;
      };

      const response = await retryWithBackoff(operation, sourceConfig.error_handling?.max_retries || 3);
      return this._transformSamGovEntityData(response, fieldMapping);
    } catch (error) {
      throw new Error(`SAM.gov Entity API error: ${error.message}`);
    }
  }

  /**
   * Federal Register API Client
   */
  async _fetchFederalRegister(params) {
    const sourceConfig = this.sources.federal_register;
    const baseUrl = sourceConfig.base_url;
    const endpoint = sourceConfig.endpoints?.search || '/documents.json';
    const headers = createAuthHeaders(sourceConfig);

    const queryParams = buildQueryParams(sourceConfig.params, {
      conditions: {
        term: params.query || 'grant',
        agencies: params.agencies,
        type: 'NOTICE'
      },
      per_page: params.limit || 20,
      page: params.page || 1
    });

    try {
      const operation = async () => {
        const response = await axios.get(`${baseUrl}${endpoint}`, {
          params: queryParams,
          headers,
          timeout: 30000
        });
        return response.data;
      };

      const response = await retryWithBackoff(operation, 3);
      return this._transformFederalRegisterData(response);
    } catch (error) {
      throw new Error(`Federal Register API error: ${error.message}`);
    }
  }

  /**
   * Michigan.gov Socrata API Client
   */
  async _fetchMichiganSocrata(params) {
    const sourceConfig = this.sources.michigan_socrata;
    const baseUrl = sourceConfig.base_url;
    const headers = createAuthHeaders(sourceConfig);
    
    // Default to grants dataset
    const datasetId = params.dataset_id || sourceConfig.datasets?.grants;
    if (!datasetId) {
      logger.warn('No Michigan Socrata dataset ID configured');
      return [];
    }

    const endpoint = sourceConfig.endpoints?.search || '/views/{dataset_id}.json';
    const url = formatUrl(baseUrl, endpoint, {}, { dataset_id: datasetId });
    
    const queryParams = buildQueryParams(sourceConfig.params, {
      '$limit': params.limit || 100,
      '$offset': params.offset || 0,
      '$q': params.query,
      '$order': params.order || ':updated_at DESC'
    });

    try {
      const operation = async () => {
        const response = await axios.get(url, {
          params: queryParams,
          headers,
          timeout: 30000
        });
        return response.data;
      };

      const response = await retryWithBackoff(operation, sourceConfig.error_handling?.max_retries || 2);
      const fieldMapping = this.config.getFieldMapping('michigan_socrata');
      return this._transformMichiganSocrataData(response, fieldMapping);
    } catch (error) {
      throw new Error(`Michigan Socrata API error: ${error.message}`);
    }
  }

  /**
   * Zyte API Client for Web Scraping
   */
  async _fetchZyteApi(params) {
    const sourceConfig = this.sources.zyte_api;
    if (!sourceConfig?.api_key) {
      logger.warn('Zyte API key not available');
      return [];
    }

    const baseUrl = sourceConfig.base_url;
    const endpoint = sourceConfig.endpoints?.extract || '/extract';
    const headers = createAuthHeaders(sourceConfig);
    headers['Content-Type'] = 'application/json';

    const requestData = {
      url: params.url,
      browserHtml: sourceConfig.params?.browserHtml || true,
      screenshot: sourceConfig.params?.screenshot || false,
      geolocation: sourceConfig.params?.geolocation || 'US',
      actions: params.actions || null
    };

    try {
      const operation = async () => {
        const response = await axios.post(`${baseUrl}${endpoint}`, requestData, {
          headers,
          timeout: 60000 // Longer timeout for scraping
        });
        return response.data;
      };

      const response = await retryWithBackoff(operation, sourceConfig.error_handling?.max_retries || 2);
      return this._transformZyteApiData(response, params);
    } catch (error) {
      throw new Error(`Zyte API error: ${error.message}`);
    }
  }

  /**
   * HHS Grants RSS Scraper
   */
  async _fetchHhsGrants(params) {
    const sourceConfig = this.sources.hhs_grants;
    const baseUrl = sourceConfig.base_url;
    const rssEndpoint = sourceConfig.endpoints?.rss || '/grants/rss.xml';
    const rssUrl = `${baseUrl}${rssEndpoint}`;

    try {
      const filterKeywords = params.keywords || ['grant', 'funding', 'award'];
      const grants = await rssParser.parseRSSFeed(rssUrl, 'hhs_grants', {
        filterKeywords,
        maxItems: params.limit || 50,
        timeout: sourceConfig.scraping_config?.timeout * 1000 || 30000
      });

      logger.info(`Retrieved ${grants.length} grants from HHS RSS feed`);
      return grants;
    } catch (error) {
      throw new Error(`HHS Grants RSS error: ${error.message}`);
    }
  }

  /**
   * Department of Education Grants RSS Scraper
   */
  async _fetchEdGrants(params) {
    const sourceConfig = this.sources.ed_grants;
    const baseUrl = sourceConfig.base_url;
    const rssEndpoint = sourceConfig.endpoints?.rss || '/news/rss.xml';
    const rssUrl = `${baseUrl}${rssEndpoint}`;

    try {
      const filterKeywords = params.keywords || ['grant', 'funding', 'education'];
      const grants = await rssParser.parseRSSFeed(rssUrl, 'ed_grants', {
        filterKeywords,
        maxItems: params.limit || 50,
        timeout: sourceConfig.scraping_config?.timeout * 1000 || 30000
      });

      logger.info(`Retrieved ${grants.length} grants from Education RSS feed`);
      return grants;
    } catch (error) {
      throw new Error(`Education Grants RSS error: ${error.message}`);
    }
  }

  /**
   * NSF Grants RSS Scraper
   */
  async _fetchNsfGrants(params) {
    const sourceConfig = this.sources.nsf_grants;
    const baseUrl = sourceConfig.base_url;
    const rssEndpoint = sourceConfig.endpoints?.rss || '/news/news_rss.xml';
    const rssUrl = `${baseUrl}${rssEndpoint}`;

    try {
      const filterKeywords = params.keywords || ['funding', 'research', 'grant'];
      const grants = await rssParser.parseRSSFeed(rssUrl, 'nsf_grants', {
        filterKeywords,
        maxItems: params.limit || 100,
        timeout: sourceConfig.scraping_config?.timeout * 1000 || 30000
      });

      logger.info(`Retrieved ${grants.length} grants from NSF RSS feed`);
      return grants;
    } catch (error) {
      throw new Error(`NSF Grants RSS error: ${error.message}`);
    }
  }

  /**
   * GovInfo API Client
   */
  async _fetchGovInfo(params) {
    const sourceConfig = this.sources.govinfo;
    const baseUrl = sourceConfig.base_url;
    const endpoint = sourceConfig.endpoints?.search || '/search';
    const headers = createAuthHeaders(sourceConfig);

    const queryParams = buildQueryParams(sourceConfig.params, {
      query: params.query || 'grant',
      collection: params.collection || 'FR',
      pageSize: params.limit || 25,
      offsetMark: params.offsetMark || '*'
    });

    try {
      const operation = async () => {
        const response = await axios.get(`${baseUrl}${endpoint}`, {
          params: queryParams,
          headers,
          timeout: 30000
        });
        return response.data;
      };

      const response = await retryWithBackoff(operation, 3);
      return this._transformGovInfoData(response);
    } catch (error) {
      throw new Error(`GovInfo API error: ${error.message}`);
    }
  }

  /**
   * Foundation Directory Client
   */
  async _fetchFoundationDirectory(params) {
    const sourceConfig = this.sources.foundation_directory;
    if (!sourceConfig?.api_key) {
      logger.warn('Foundation Directory API key not available');
      return [];
    }

    const baseUrl = sourceConfig.base_url;
    const endpoint = '/grants/search';
    const headers = createAuthHeaders(sourceConfig);

    const queryParams = {
      q: params.query,
      limit: params.limit || 100,
      offset: params.offset || 0,
      fields: 'title,description,funder,amount,deadline'
    };

    try {
      const operation = async () => {
        const response = await axios.get(`${baseUrl}${endpoint}`, {
          params: queryParams,
          headers,
          timeout: 30000
        });
        return response.data;
      };

      const response = await retryWithBackoff(operation, 3);
      return this._transformFoundationDirectoryData(response);
    } catch (error) {
      throw new Error(`Foundation Directory API error: ${error.message}`);
    }
  }

  /**
   * GrantWatch Client
   */
  async _fetchGrantWatch(params) {
    const sourceConfig = this.sources.grantwatch;
    if (!sourceConfig?.api_key) {
      logger.warn('GrantWatch API key not available');
      return [];
    }

    const baseUrl = sourceConfig.base_url;
    const endpoint = '/search';
    const headers = createAuthHeaders(sourceConfig);

    const queryParams = {
      keyword: params.query,
      limit: params.limit || 50,
      category: params.category
    };

    try {
      const operation = async () => {
        const response = await axios.get(`${baseUrl}${endpoint}`, {
          params: queryParams,
          headers,
          timeout: 30000
        });
        return response.data;
      };

      const response = await retryWithBackoff(operation, 3);
      return this._transformGrantWatchData(response);
    } catch (error) {
      throw new Error(`GrantWatch API error: ${error.message}`);
    }
  }

  /**
   * Candid API Clients (placeholder - would need specific implementation based on actual API)
   */
  async _fetchCandidNews(params) {
    logger.info('Candid News API implementation placeholder');
    return [];
  }

  async _fetchCandidGrants(params) {
    logger.info('Candid Grants API implementation placeholder');
    return [];
  }

  async _fetchCandidEssentials(params) {
    logger.info('Candid Essentials API implementation placeholder');
    return [];
  }

  /**
   * USAspending.gov Client (placeholder)
   */
  async _fetchUSAspending(params) {
    logger.info('USAspending.gov API implementation placeholder');
    return [];
  }

  /**
   * Placeholder methods for state portals
   */
  async _fetchMichiganPortal(params) {
    logger.debug('Michigan Portal - using Socrata API instead');
    return this._fetchMichiganSocrata(params);
  }

  async _fetchGeorgiaPortal(params) {
    logger.debug('Georgia Portal - placeholder implementation');
    return [];
  }

  async _fetchPhilanthropyNews(params) {
    logger.debug('Philanthropy News - placeholder implementation (403 Forbidden)');
    return [];
  }

  // Data transformation methods
  _transformGrantsGovData(data, fieldMapping) {
    // Handle both single opportunity and search results
    const grants = data.grants || data.opportunityDetails || (Array.isArray(data) ? data : [data]);
    
    if (!grants || grants.length === 0) return [];
    
    return grants.map(grant => {
      const standardGrant = createStandardizedGrant(grant, 'grants_gov', fieldMapping);
      
      // Additional Grants.gov specific fields
      if (grant.cfda) {
        standardGrant.cfda_number = grant.cfda.map(c => c.cfdaNumber).join(', ');
      }
      
      return standardGrant;
    }).filter(grant => validateGrantObject(grant));
  }

  _transformSamGovOpportunitiesData(data, fieldMapping) {
    const opportunities = data.opportunities || data._embedded?.opportunities || data.results || [];
    
    if (!opportunities || opportunities.length === 0) return [];
    
    return opportunities.map(opp => {
      const standardGrant = createStandardizedGrant(opp, 'sam_gov_opportunities', fieldMapping);
      
      // SAM.gov specific fields
      standardGrant.notice_type = opp.type;
      standardGrant.solicitation_number = opp.solicitationNumber;
      standardGrant.set_aside_codes = opp.setAsideCodes;
      
      return standardGrant;
    }).filter(grant => validateGrantObject(grant));
  }

  _transformSamGovEntityData(data, fieldMapping) {
    const entities = data.entities || data._embedded?.entities || data.results || [];
    
    if (!entities || entities.length === 0) return [];
    
    return entities.map(entity => {
      // Transform entity data to grant-like format (this is entity data, not grants)
      return {
        id: entity.ueiSAM || entity.entityRegistration?.ueiSAM,
        title: entity.legalBusinessName || entity.entityRegistration?.legalBusinessName,
        funder: 'SAM.gov Entity Registry',
        description: `Entity: ${entity.legalBusinessName}`,
        source: 'sam_gov_entity',
        entity_type: 'registry',
        uei: entity.ueiSAM,
        duns: entity.dunsNumber,
        cage_code: entity.cageCode,
        registration_date: entity.registrationDate,
        expiration_date: entity.expirationDate,
        created_at: new Date().toISOString()
      };
    });
  }

  _transformFederalRegisterData(data) {
    const documents = data.results || [];
    
    if (!documents || documents.length === 0) return [];
    
    return documents.map(doc => {
      const standardGrant = createStandardizedGrant(doc, 'federal_register', {
        id: 'document_number',
        title: 'title',
        description: 'abstract',
        url: 'html_url',
        posted_date: 'publication_date'
      });
      
      // Federal Register specific fields
      standardGrant.document_type = doc.type;
      standardGrant.agencies = doc.agencies?.map(a => a.name).join(', ');
      
      return standardGrant;
    }).filter(grant => validateGrantObject(grant));
  }

  _transformMichiganSocrataData(data, fieldMapping) {
    // Socrata returns array of objects directly
    const records = Array.isArray(data) ? data : [data];
    
    return records.map(record => {
      const standardGrant = createStandardizedGrant(record, 'michigan_socrata', fieldMapping);
      
      // Michigan specific fields
      standardGrant.state = 'Michigan';
      standardGrant.data_source = 'michigan_open_data';
      
      return standardGrant;
    }).filter(grant => validateGrantObject(grant));
  }

  _transformZyteApiData(data, params) {
    // Zyte API returns scraped content, need to extract grant info
    const html = data.browserHtml || data.html;
    
    if (!html) return [];
    
    // This would need custom parsing based on the target website
    // For now, return basic structure with scraped content
    return [{
      id: `zyte-${Date.now()}`,
      title: `Scraped content from ${params.url}`,
      funder: 'Web Scraping',
      description: 'Content scraped via Zyte API',
      source: 'zyte_api',
      url: params.url,
      scraped_content: html,
      scraped_at: new Date().toISOString(),
      created_at: new Date().toISOString()
    }];
  }

  _transformGovInfoData(data) {
    const documents = data.results || data.packages || [];
    
    if (!documents || documents.length === 0) return [];
    
    return documents.map(doc => {
      const standardGrant = createStandardizedGrant(doc, 'govinfo', {
        id: 'packageId',
        title: 'title',
        description: 'summary',
        posted_date: 'dateIssued'
      });
      
      standardGrant.document_class = doc.docClass;
      standardGrant.collection = doc.collectionName;
      
      return standardGrant;
    }).filter(grant => validateGrantObject(grant));
  }

  _transformFoundationDirectoryData(data) {
    const grants = data.grants || data.results || [];
    
    if (!grants || grants.length === 0) return [];
    
    return grants.map(grant => {
      const standardGrant = createStandardizedGrant(grant, 'foundation_directory');
      
      // Foundation Directory specific fields
      standardGrant.foundation_type = grant.foundation_type;
      standardGrant.geographic_focus = grant.geographic_focus;
      
      return standardGrant;
    }).filter(grant => validateGrantObject(grant));
  }

  _transformGrantWatchData(data) {
    const grants = data.grants || data.opportunities || [];
    
    if (!grants || grants.length === 0) return [];
    
    return grants.map(grant => {
      const standardGrant = createStandardizedGrant(grant, 'grantwatch');
      
      // GrantWatch specific fields
      standardGrant.sectors = grant.sectors;
      standardGrant.organization_types = grant.organization_types;
      
      return standardGrant;
    }).filter(grant => validateGrantObject(grant));
  }

  /**
   * Get comprehensive API status
   */
  getApiStatus() {
    return {
      sources: this.config.getAllSources(),
      circuitBreakers: this.getCircuitBreakerSummary(),
      rateLimits: this.rateLimiter.getStatus(),
      cache: this.cache.getStats(),
      credentials: credentialManager.getServiceStatusReport()
    };
  }
}

// Create and export default instance
export const apiManager = new APIManager();
export default apiManager;