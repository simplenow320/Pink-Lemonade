/**
 * API Configuration for Grant Data Sources
 * Central configuration for all external APIs and data sources
 * JavaScript port of app/config/apiConfig.py
 */

import dotenv from 'dotenv';
import { createLogger } from '../utils/logger.js';

dotenv.config();
const logger = createLogger('APIConfig');

// API Source Configurations
export const API_SOURCES = {
  grants_gov: {
    name: 'Grants.gov',
    enabled: true,
    base_url: 'https://www.grants.gov/grantsws/rest',
    api_key: null, // Public API, no key required
    credential_required: false,
    rate_limit: {
      calls: 100,
      period: 3600 // per hour
    },
    cache_ttl: 60, // minutes
    supports: ['search', 'details'],
    description: 'Federal grant opportunities from US government',
    endpoints: {
      search: '/opportunities/search',
      details: '/opportunity/details/{id}'
    },
    params: {
      status: 'posted',
      sortBy: 'closeDate',
      oppStatuses: 'posted',
      rows: 25
    }
  },

  philanthropy_news: {
    name: 'Philanthropy News Digest',
    enabled: false, // Returns 403 Forbidden - NOT WORKING
    base_url: 'https://philanthropynewsdigest.org/rfps/rss',
    api_key: null,
    credential_required: false,
    rate_limit: {
      calls: 50,
      period: 3600
    },
    cache_ttl: 120,
    supports: ['search'],
    description: 'Foundation grant opportunities and RFPs'
  },

  foundation_directory: {
    name: 'Foundation Directory Online',
    enabled: false, // Requires paid subscription
    base_url: 'https://api.foundationdirectory.org/v1',
    api_key: process.env.FDO_API_KEY,
    credential_required: true,
    rate_limit: {
      calls: 1000,
      period: 86400 // per day
    },
    cache_ttl: 240,
    supports: ['search', 'details', 'funder_profiles'],
    description: 'Comprehensive foundation data (requires subscription)'
  },

  grantwatch: {
    name: 'GrantWatch',
    enabled: false, // Placeholder for future integration
    base_url: 'https://www.grantwatch.com/api',
    api_key: process.env.GRANTWATCH_API_KEY,
    credential_required: true,
    rate_limit: {
      calls: 100,
      period: 3600
    },
    cache_ttl: 60,
    supports: ['search', 'details'],
    description: 'Diverse grant opportunities across sectors'
  },

  candid: {
    name: 'Candid (formerly Foundation Center)',
    enabled: false, // Placeholder for paid API
    base_url: 'https://api.candid.org/v1',
    api_key: process.env.CANDID_API_KEY,
    credential_required: true,
    rate_limit: {
      calls: 5000,
      period: 86400
    },
    cache_ttl: 1440, // 24 hours
    supports: ['search', 'details', 'funder_profiles', 'analytics'],
    description: 'Premium foundation and nonprofit data'
  },

  michigan_portal: {
    name: 'Michigan Open Data Portal',
    enabled: false, // No implementation - returns empty
    base_url: 'https://data.michigan.gov/api',
    api_key: null,
    credential_required: false,
    rate_limit: {
      calls: 100,
      period: 3600
    },
    cache_ttl: 240,
    supports: ['search'],
    description: 'Michigan state and local grants'
  },

  georgia_portal: {
    name: 'Georgia Grants Portal',
    enabled: false, // No implementation - returns empty
    base_url: 'https://georgia.grantplatform.com/api',
    api_key: null,
    credential_required: false,
    rate_limit: {
      calls: 50,
      period: 3600
    },
    cache_ttl: 240,
    supports: ['search'],
    description: 'Georgia state funding opportunities'
  },

  north_carolina_portal: {
    name: 'North Carolina Grants',
    enabled: false,
    base_url: 'https://ncgrants.nc.gov/api',
    api_key: null,
    credential_required: false,
    rate_limit: {
      calls: 50,
      period: 3600
    },
    cache_ttl: 240,
    supports: ['search'],
    description: 'North Carolina state grants'
  },

  south_carolina_portal: {
    name: 'South Carolina Grants',
    enabled: false,
    base_url: 'https://admin.sc.gov/grants/api',
    api_key: null,
    credential_required: false,
    rate_limit: {
      calls: 50,
      period: 3600
    },
    cache_ttl: 240,
    supports: ['search'],
    description: 'South Carolina state grants'
  },

  federal_register: {
    name: 'Federal Register',
    enabled: true,
    base_url: 'https://www.federalregister.gov/api/v1',
    api_key: null, // Public API
    credential_required: false,
    rate_limit: {
      calls: 1000,
      period: 3600
    },
    cache_ttl: 120,
    supports: ['search'],
    description: 'Federal funding notices and NOFOs',
    endpoints: {
      search: '/documents.json'
    },
    params: {
      'fields[]': 'title,html_url,publication_date,abstract',
      per_page: 20,
      order: 'newest'
    }
  },

  govinfo: {
    name: 'GovInfo API',
    enabled: true,
    base_url: 'https://api.govinfo.gov',
    api_key_env: 'GOVINFO_API_KEY',
    api_key: null, // Public API, but supports optional API key
    credential_required: false, // Optional API key for enhanced access
    credential_fallbacks: ['GOVINFO_KEY'],
    auth_type: 'api_key',
    auth_header: 'X-API-Key',
    rate_limit: {
      calls: 1000,
      period: 3600
    },
    cache_ttl: 120,
    supports: ['search'],
    description: 'Government information and documents',
    endpoints: {
      search: '/search'
    },
    params: {
      collection: 'FR', // Federal Register
      format: 'json',
      pageSize: 25,
      offsetMark: '*'
    }
  },

  // New API Sources
  sam_gov_opportunities: {
    name: 'SAM.gov Get Opportunities API',
    enabled: false, // Requires API key
    base_url: 'https://api.sam.gov/opportunities/v2',
    api_key_env: 'SAM_GOV_API_KEY',
    api_key: null,
    auth_type: 'api_key',
    auth_header: 'X-Api-Key',
    credential_required: true,
    credential_fallbacks: ['SAM_API_KEY', 'SAMGOV_KEY'],
    rate_limit: {
      calls: 1000,
      period: 3600 // per hour
    },
    cache_ttl: 30, // minutes
    supports: ['search', 'details'],
    description: 'Federal contract opportunities from SAM.gov',
    endpoints: {
      search: '/search',
      details: '/opportunities/{id}'
    },
    params: {
      limit: 100,
      api_version: 'v2',
      postedFrom: null, // YYYY-MM-DD format
      postedTo: null,
      type: 'o', // opportunities
      ptype: 'k' // procurement type
    },
    error_handling: {
      retry_codes: [429, 502, 503, 504],
      max_retries: 3,
      backoff_factor: 2
    }
  },

  sam_gov_entity: {
    name: 'SAM.gov Entity Management API',
    enabled: false, // Requires API key
    base_url: 'https://api.sam.gov/entity-information/v3',
    api_key_env: 'SAM_GOV_API_KEY',
    api_key: null,
    auth_type: 'api_key',
    auth_header: 'X-Api-Key',
    credential_required: true,
    credential_fallbacks: ['SAM_API_KEY', 'SAMGOV_KEY'],
    rate_limit: {
      calls: 1000,
      period: 3600
    },
    cache_ttl: 240, // 4 hours - entity data changes less frequently
    supports: ['search', 'details', 'entity_profiles'],
    description: 'Entity registration data from SAM.gov',
    endpoints: {
      search: '/entities',
      details: '/entities/{id}'
    },
    params: {
      limit: 100,
      api_version: 'v3',
      includeSections: 'entityRegistration,coreData',
      format: 'json'
    },
    error_handling: {
      retry_codes: [429, 502, 503, 504],
      max_retries: 3,
      backoff_factor: 2
    }
  },

  michigan_socrata: {
    name: 'Michigan.gov Socrata API',
    enabled: false, // Depends on available datasets
    base_url: 'https://data.michigan.gov/api',
    api_key_env: 'MICHIGAN_SOCRATA_API_KEY',
    api_key: null,
    auth_type: 'app_token', // Socrata uses app_token
    auth_header: 'X-App-Token',
    credential_required: false, // Public API but rate limited without token
    credential_fallbacks: ['SOCRATA_APP_TOKEN', 'MICHIGAN_API_KEY'],
    rate_limit: {
      calls: 1000, // With app token
      period: 3600,
      unauthenticated_calls: 100, // Without app token
      unauthenticated_period: 3600
    },
    cache_ttl: 60,
    supports: ['search', 'datasets'],
    description: 'Michigan state open data and grant information',
    endpoints: {
      search: '/views/{dataset_id}.json',
      datasets: '/views.json'
    },
    params: {
      '$limit': 100,
      '$offset': 0,
      '$order': ':updated_at DESC',
      '$query': null // SoQL query
    },
    datasets: {
      grants: process.env.MICHIGAN_GRANTS_DATASET_ID || 'michigan-grants-dataset-id',
      funding: process.env.MICHIGAN_FUNDING_DATASET_ID || 'michigan-funding-dataset-id',
      contracts: process.env.MICHIGAN_CONTRACTS_DATASET_ID || 'michigan-contracts-dataset-id'
    },
    error_handling: {
      retry_codes: [429, 502, 503, 504],
      max_retries: 2,
      backoff_factor: 1.5
    }
  },

  zyte_api: {
    name: 'Zyte API (Web Scraping)',
    enabled: false, // Requires paid subscription
    base_url: 'https://api.zyte.com/v1',
    api_key_env: 'ZYTE_API_KEY',
    api_key: null,
    auth_type: 'basic_auth', // Zyte uses HTTP Basic Auth
    auth_header: 'Authorization',
    credential_required: true,
    credential_fallbacks: ['SCRAPINGHUB_API_KEY', 'ZYTE_KEY'],
    rate_limit: {
      calls: 100, // Conservative limit for scraping
      period: 3600,
      concurrent_requests: 5
    },
    cache_ttl: 1440, // 24 hours for scraped content
    supports: ['scrape', 'extract'],
    description: 'Professional web scraping service for grant websites',
    endpoints: {
      extract: '/extract',
      browser: '/browser'
    },
    params: {
      browserHtml: true,
      screenshot: false,
      actions: null, // List of actions to perform
      geolocation: 'US'
    },
    scraping_targets: {
      foundation_sites: [
        'foundationcenter.org',
        'guidestar.org',
        'philanthropy.com'
      ],
      government_portals: [
        'grants.gov',
        'usaspending.gov'
      ]
    },
    error_handling: {
      retry_codes: [429, 502, 503, 504, 520, 521, 522, 524],
      max_retries: 2,
      backoff_factor: 3
    }
  },

  // Department-specific scraping sources
  hhs_grants: {
    name: 'HHS Grants Scraper',
    enabled: true, // Public data source
    base_url: 'https://www.hhs.gov/grants',
    api_key: null,
    auth_type: null,
    credential_required: false,
    rate_limit: {
      calls: 50,
      period: 3600
    },
    cache_ttl: 240, // 4 hours
    supports: ['scrape', 'rss'],
    description: 'Health and Human Services grant opportunities',
    endpoints: {
      rss: '/grants/rss.xml',
      search: '/grants/search'
    },
    scraping_config: {
      user_agent: 'Mozilla/5.0 (compatible; PinkLemonade/1.0)',
      timeout: 30,
      follow_redirects: true,
      max_pages: 10
    }
  },

  ed_grants: {
    name: 'Department of Education Grants',
    enabled: true,
    base_url: 'https://www.ed.gov/grants',
    api_key: null,
    auth_type: null,
    credential_required: false,
    rate_limit: {
      calls: 50,
      period: 3600
    },
    cache_ttl: 240,
    supports: ['scrape', 'rss'],
    description: 'Department of Education funding opportunities',
    endpoints: {
      rss: '/news/rss.xml',
      search: '/grants'
    },
    scraping_config: {
      user_agent: 'Mozilla/5.0 (compatible; PinkLemonade/1.0)',
      timeout: 30,
      follow_redirects: true,
      max_pages: 5
    }
  },

  nsf_grants: {
    name: 'National Science Foundation',
    enabled: true,
    base_url: 'https://www.nsf.gov/funding',
    api_key: null,
    auth_type: null,
    credential_required: false,
    rate_limit: {
      calls: 100,
      period: 3600
    },
    cache_ttl: 360, // 6 hours
    supports: ['scrape', 'rss'],
    description: 'National Science Foundation research funding',
    endpoints: {
      rss: '/news/news_rss.xml',
      search: '/funding/search'
    },
    scraping_config: {
      user_agent: 'Mozilla/5.0 (compatible; PinkLemonade/1.0)',
      timeout: 30,
      follow_redirects: true,
      max_pages: 8
    }
  }
};

// Search filters configuration
export const SEARCH_FILTERS = {
  categories: [
    'Arts & Culture',
    'Community Development',
    'Education',
    'Environment',
    'Faith-Based',
    'Health & Human Services',
    'Technology & Innovation',
    'Youth Programs'
  ],
  funding_types: [
    'Operating Support',
    'Project/Program',
    'Capital',
    'Capacity Building',
    'General Support',
    'Research'
  ],
  geographic_focus: [
    'National',
    'Regional',
    'State',
    'Local/City',
    'International'
  ],
  organization_types: [
    '501(c)(3)',
    'Faith-Based Organization',
    'Educational Institution',
    'Government Agency',
    'Individual',
    'Small Business'
  ]
};

// Enhanced data standardization mappings for new sources
export const FIELD_MAPPINGS = {
  grants_gov: {
    title: 'opportunityTitle',
    funder: 'agencyName',
    amount_min: 'awardFloor',
    amount_max: 'awardCeiling',
    deadline: 'closeDate',
    description: 'description',
    eligibility: 'eligibilityCategory'
  },
  sam_gov_opportunities: {
    title: 'title',
    funder: 'fullParentPathName',
    amount_min: 'awardFloor',
    amount_max: 'awardCeiling',
    deadline: 'responseDeadLine',
    description: 'description',
    eligibility: 'additionalInfoOnEligibility',
    opportunity_id: 'opportunityId',
    notice_type: 'type'
  },
  sam_gov_entity: {
    entity_name: 'legalBusinessName',
    duns: 'dunsNumber',
    uei: 'ueiSAM',
    cage_code: 'cageCode',
    address: 'physicalAddress',
    registration_date: 'registrationDate',
    expiration_date: 'expirationDate'
  },
  michigan_socrata: {
    title: 'title',
    description: 'description',
    amount: 'amount',
    deadline: 'deadline',
    category: 'category',
    department: 'department'
  },
  zyte_api: {
    extracted_text: 'html',
    title: 'title',
    links: 'links',
    metadata: 'metadata'
  },
  default: {
    title: 'title',
    funder: 'funder',
    amount_min: 'amount_min',
    amount_max: 'amount_max',
    deadline: 'deadline',
    description: 'description',
    eligibility: 'eligibility'
  }
};

/**
 * Enhanced API Configuration Manager with Flexible Credential Management
 */
export class APIConfig {
  constructor() {
    this.sources = { ...API_SOURCES };
    this.filters = { ...SEARCH_FILTERS };
    this.field_mappings = { ...FIELD_MAPPINGS };
    this._loadEnvironmentKeys();
    this._autoEnableSources();
  }

  /**
   * Load API keys from environment variables with fallback support
   */
  _loadEnvironmentKeys() {
    for (const [sourceId, config] of Object.entries(this.sources)) {
      // Try primary environment variable
      const primaryEnv = config.api_key_env || `${sourceId.toUpperCase()}_API_KEY`;
      let apiKey = process.env[primaryEnv];

      // Try fallback environment variables if primary not found
      if (!apiKey && config.credential_fallbacks) {
        for (const fallbackEnv of config.credential_fallbacks) {
          apiKey = process.env[fallbackEnv];
          if (apiKey) {
            logger.info(`Loaded ${sourceId} credentials from fallback: ${fallbackEnv}`);
            break;
          }
        }
      }

      // Set the API key if found
      if (apiKey) {
        config.api_key = apiKey;
        logger.info(`Loaded credentials for ${sourceId}`);
      } else if (config.credential_required) {
        logger.warn(`Missing required credentials for ${sourceId}. Source will be disabled.`);
      }
    }
  }

  /**
   * Automatically enable sources based on credential availability
   */
  _autoEnableSources() {
    for (const [sourceId, config] of Object.entries(this.sources)) {
      // Skip if already explicitly enabled
      if (config.enabled) {
        continue;
      }

      const credentialRequired = config.credential_required || false;
      const hasCredentials = Boolean(config.api_key);

      // Enable if no credentials required OR credentials are available
      if (!credentialRequired || hasCredentials) {
        config.enabled = true;
        logger.info(`Auto-enabled source: ${sourceId}`);
      } else {
        config.enabled = false;
        logger.debug(`Source ${sourceId} disabled due to missing credentials`);
      }
    }
  }

  /**
   * Get configuration for a specific source
   */
  getSourceConfig(sourceId) {
    return this.sources[sourceId] || {};
  }

  /**
   * Get all enabled sources
   */
  getEnabledSources() {
    return Object.fromEntries(
      Object.entries(this.sources).filter(([, config]) => config.enabled)
    );
  }

  /**
   * Check if a source is enabled
   */
  isSourceEnabled(sourceId) {
    return this.sources[sourceId]?.enabled || false;
  }

  /**
   * Get field mapping for a source
   */
  getFieldMapping(sourceId) {
    return this.field_mappings[sourceId] || this.field_mappings.default;
  }

  /**
   * Enable or disable a source
   */
  updateSourceStatus(sourceId, enabled) {
    if (this.sources[sourceId]) {
      this.sources[sourceId].enabled = enabled;
    }
  }

  /**
   * Add or update API key for a source
   */
  addApiKey(sourceId, apiKey) {
    if (this.sources[sourceId]) {
      this.sources[sourceId].api_key = apiKey;
      // Also enable the source if it was disabled
      if (apiKey) {
        this.sources[sourceId].enabled = true;
        logger.info(`Added API key and enabled source: ${sourceId}`);
      }
    }
  }

  /**
   * Get credential status for all sources
   */
  getCredentialStatus() {
    const status = {};
    for (const [sourceId, config] of Object.entries(this.sources)) {
      status[sourceId] = {
        name: config.name || sourceId,
        enabled: config.enabled || false,
        credential_required: config.credential_required || false,
        has_credentials: Boolean(config.api_key),
        primary_env_var: config.api_key_env || `${sourceId.toUpperCase()}_API_KEY`,
        fallback_env_vars: config.credential_fallbacks || [],
        auth_type: config.auth_type,
        description: config.description || ''
      };
    }
    return status;
  }

  /**
   * Check if a source is properly configured and available
   */
  checkSourceHealth(sourceId) {
    if (!this.sources[sourceId]) {
      return { healthy: false, error: 'Source not found' };
    }

    const config = this.sources[sourceId];
    const healthStatus = {
      healthy: true,
      enabled: config.enabled || false,
      errors: [],
      warnings: []
    };

    // Check credentials
    if (config.credential_required && !config.api_key) {
      healthStatus.healthy = false;
      healthStatus.errors.push('Missing required credentials');
    }

    // Check required configuration
    if (!config.base_url) {
      healthStatus.healthy = false;
      healthStatus.errors.push('Missing base URL configuration');
    }

    return healthStatus;
  }

  /**
   * Get all available sources with their basic info
   */
  getAllSources() {
    return Object.fromEntries(
      Object.entries(this.sources).map(([sourceId, config]) => [
        sourceId,
        {
          name: config.name,
          description: config.description,
          enabled: config.enabled,
          credential_required: config.credential_required,
          has_credentials: Boolean(config.api_key)
        }
      ])
    );
  }
}

// Create and export default instance
export const apiConfig = new APIConfig();
export default apiConfig;