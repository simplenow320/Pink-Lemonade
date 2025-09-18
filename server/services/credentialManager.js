/**
 * Comprehensive Credential Management System for Environment Variables
 * Handles API credentials with proper validation, fallback handling, and status reporting
 * JavaScript port of app/services/credential_manager.py
 */

import { createLogger } from '../utils/logger.js';

const logger = createLogger('CredentialManager');

// Credential Status Enum
export const CredentialStatus = {
  AVAILABLE: 'available',
  MISSING: 'missing',
  INVALID: 'invalid',
  DEPRECATED: 'deprecated'
};

// Credential Priority Enum
export const CredentialPriority = {
  CRITICAL: 'critical',    // Essential for core functionality
  HIGH: 'high',           // Important for main features
  MEDIUM: 'medium',       // Nice to have features
  LOW: 'low'             // Optional/experimental features
};

/**
 * Configuration for a specific credential
 */
class CredentialConfig {
  constructor({
    name,
    envVar,
    fallbackVars = [],
    priority,
    description,
    serviceName,
    validationPattern = null,
    minLength = null,
    requiredPrefix = null,
    setupUrl = null
  }) {
    this.name = name;
    this.envVar = envVar;
    this.fallbackVars = fallbackVars;
    this.priority = priority;
    this.description = description;
    this.serviceName = serviceName;
    this.validationPattern = validationPattern;
    this.minLength = minLength;
    this.requiredPrefix = requiredPrefix;
    this.setupUrl = setupUrl;
  }
}

/**
 * Manages all API credentials with validation and status reporting
 */
export class CredentialManager {
  constructor() {
    this.credentials = this._initializeCredentialConfigs();
    this.statusCache = {};
    this.lastCheck = null;
    logger.info(`Initialized CredentialManager with ${Object.keys(this.credentials).length} credential configurations`);
  }

  /**
   * Initialize all credential configurations
   */
  _initializeCredentialConfigs() {
    return {
      // AI Services - Critical Priority
      openai_api_key: new CredentialConfig({
        name: "OpenAI API Key",
        envVar: "OPENAI_API_KEY",
        fallbackVars: ["OPENAI_KEY", "AI_API_KEY"],
        priority: CredentialPriority.CRITICAL,
        description: "OpenAI GPT API for AI-powered grant matching and writing assistance",
        serviceName: "OpenAI GPT",
        validationPattern: /^sk-[A-Za-z0-9]{48,}$/,
        minLength: 48,
        requiredPrefix: "sk-",
        setupUrl: "https://platform.openai.com/api-keys"
      }),

      // Government APIs - High Priority
      sam_gov_api_key: new CredentialConfig({
        name: "SAM.gov API Key",
        envVar: "SAM_GOV_API_KEY",
        fallbackVars: ["SAM_API_KEY", "SAMGOV_KEY", "SAM_GOV_TOKEN"],
        priority: CredentialPriority.HIGH,
        description: "SAM.gov API for federal contract opportunities and entity data",
        serviceName: "SAM.gov",
        minLength: 32,
        setupUrl: "https://api.sam.gov/getting-started"
      }),

      grants_gov_api_key: new CredentialConfig({
        name: "Grants.gov API Key",
        envVar: "GRANTS_GOV_API_KEY",
        fallbackVars: ["GRANTS_API_KEY", "GRANTSGOW_KEY"],
        priority: CredentialPriority.MEDIUM,
        description: "Grants.gov API for federal grant opportunities (optional - has public endpoints)",
        serviceName: "Grants.gov",
        minLength: 16,
        setupUrl: "https://www.grants.gov/api"
      }),

      // Commercial APIs - High Priority
      candid_api_key: new CredentialConfig({
        name: "Candid API Key",
        envVar: "CANDID_API_KEY",
        fallbackVars: ["CANDID_KEY", "FOUNDATION_CENTER_KEY"],
        priority: CredentialPriority.HIGH,
        description: "Candid (formerly Foundation Center) API for foundation data",
        serviceName: "Candid Foundation Data",
        minLength: 20,
        setupUrl: "https://candid.org/about/products-services/apis"
      }),

      candid_news_key: new CredentialConfig({
        name: "Candid News API Key",
        envVar: "CANDID_NEWS_KEY",
        fallbackVars: ["CANDID_NEWS_KEYS", "PND_API_KEY"],
        priority: CredentialPriority.MEDIUM,
        description: "Candid News API for philanthropy news and RFPs",
        serviceName: "Candid News",
        minLength: 16,
        setupUrl: "https://candid.org/about/products-services/apis"
      }),

      candid_grants_key: new CredentialConfig({
        name: "Candid Grants API Key",
        envVar: "CANDID_GRANTS_KEY",
        fallbackVars: ["CANDID_GRANTS_KEYS"],
        priority: CredentialPriority.MEDIUM,
        description: "Candid Grants API for grant opportunity data",
        serviceName: "Candid Grants",
        minLength: 16,
        setupUrl: "https://candid.org/about/products-services/apis"
      }),

      zyte_api_key: new CredentialConfig({
        name: "Zyte API Key",
        envVar: "ZYTE_API_KEY",
        fallbackVars: ["SCRAPINGHUB_API_KEY", "ZYTE_KEY"],
        priority: CredentialPriority.MEDIUM,
        description: "Zyte API for professional web scraping of grant websites",
        serviceName: "Zyte Web Scraping",
        minLength: 32,
        setupUrl: "https://www.zyte.com/api/"
      }),

      // Foundation Directory APIs
      fdo_api_key: new CredentialConfig({
        name: "Foundation Directory Online API Key",
        envVar: "FDO_API_KEY",
        fallbackVars: ["FOUNDATION_DIRECTORY_KEY", "FDO_KEY"],
        priority: CredentialPriority.MEDIUM,
        description: "Foundation Directory Online API for comprehensive foundation data",
        serviceName: "Foundation Directory",
        minLength: 20,
        setupUrl: "https://fdo.foundationcenter.org/"
      }),

      grantwatch_api_key: new CredentialConfig({
        name: "GrantWatch API Key",
        envVar: "GRANTWATCH_API_KEY",
        fallbackVars: ["GRANTWATCH_KEY"],
        priority: CredentialPriority.LOW,
        description: "GrantWatch API for diverse grant opportunities",
        serviceName: "GrantWatch",
        minLength: 16,
        setupUrl: "https://www.grantwatch.com/api"
      }),

      // Communication Services - High Priority
      sendgrid_api_key: new CredentialConfig({
        name: "SendGrid API Key",
        envVar: "SENDGRID_API_KEY",
        fallbackVars: ["SENDGRID_KEY", "EMAIL_API_KEY"],
        priority: CredentialPriority.HIGH,
        description: "SendGrid API for email notifications and communications",
        serviceName: "SendGrid Email",
        validationPattern: /^SG\.[A-Za-z0-9_-]{43,}$/,
        requiredPrefix: "SG.",
        minLength: 43,
        setupUrl: "https://sendgrid.com/docs/ui/account-and-settings/api-keys/"
      }),

      // Open Data APIs - Low Priority (often public)
      michigan_socrata_key: new CredentialConfig({
        name: "Michigan Socrata API Key",
        envVar: "MICHIGAN_SOCRATA_API_KEY",
        fallbackVars: ["SOCRATA_APP_TOKEN", "MICHIGAN_API_KEY"],
        priority: CredentialPriority.LOW,
        description: "Michigan.gov Socrata API for state grant data",
        serviceName: "Michigan Open Data",
        minLength: 16,
        setupUrl: "https://dev.socrata.com/foundry/"
      }),

      // System Credentials - Critical Priority
      session_secret: new CredentialConfig({
        name: "Session Secret Key",
        envVar: "SESSION_SECRET",
        fallbackVars: ["SECRET_KEY", "FLASK_SECRET_KEY"],
        priority: CredentialPriority.CRITICAL,
        description: "Express session security key for user authentication",
        serviceName: "Express Sessions",
        minLength: 24,
        setupUrl: null
      }),

      jwt_secret: new CredentialConfig({
        name: "JWT Secret Key",
        envVar: "JWT_SECRET",
        fallbackVars: ["JWT_SECRET_KEY", "TOKEN_SECRET"],
        priority: CredentialPriority.CRITICAL,
        description: "JWT token signing secret for authentication",
        serviceName: "JWT Authentication",
        minLength: 32,
        setupUrl: null
      })
    };
  }

  /**
   * Get a credential value with fallback support
   */
  getCredential(credentialId) {
    if (!this.credentials[credentialId]) {
      logger.warn(`Unknown credential ID: ${credentialId}`);
      return null;
    }

    const config = this.credentials[credentialId];

    // Try primary environment variable
    let value = process.env[config.envVar];
    if (value && value.trim()) {
      return value.trim();
    }

    // Try fallback variables
    for (const fallbackVar of config.fallbackVars) {
      value = process.env[fallbackVar];
      if (value && value.trim()) {
        logger.info(`Using fallback ${fallbackVar} for ${credentialId}`);
        return value.trim();
      }
    }

    return null;
  }

  /**
   * Validate a specific credential
   */
  validateCredential(credentialId, value = null) {
    if (!this.credentials[credentialId]) {
      return [CredentialStatus.INVALID, `Unknown credential: ${credentialId}`];
    }

    const config = this.credentials[credentialId];

    if (value === null) {
      value = this.getCredential(credentialId);
    }

    if (!value) {
      return [CredentialStatus.MISSING, `${config.name} is not set`];
    }

    // Check minimum length
    if (config.minLength && value.length < config.minLength) {
      return [CredentialStatus.INVALID, `${config.name} is too short (minimum ${config.minLength} characters)`];
    }

    // Check required prefix
    if (config.requiredPrefix && !value.startsWith(config.requiredPrefix)) {
      return [CredentialStatus.INVALID, `${config.name} must start with '${config.requiredPrefix}'`];
    }

    // Check validation pattern
    if (config.validationPattern) {
      if (!config.validationPattern.test(value)) {
        return [CredentialStatus.INVALID, `${config.name} format is invalid`];
      }
    }

    return [CredentialStatus.AVAILABLE, `${config.name} is valid`];
  }

  /**
   * Check status of all credentials
   */
  checkAllCredentials() {
    const results = {};

    for (const [credentialId, config] of Object.entries(this.credentials)) {
      const [status, message] = this.validateCredential(credentialId);
      const value = this.getCredential(credentialId);

      results[credentialId] = {
        name: config.name,
        status: status,
        message: message,
        priority: config.priority,
        serviceName: config.serviceName,
        hasValue: Boolean(value),
        maskedValue: value && value.length > 12 
          ? `${value.slice(0, 8)}...${value.slice(-4)}` 
          : value ? "***" : null,
        setupUrl: config.setupUrl,
        envVar: config.envVar,
        fallbackVars: config.fallbackVars,
        description: config.description
      };
    }

    this.statusCache = results;
    this.lastCheck = new Date();
    return results;
  }

  /**
   * Get list of missing credentials, optionally filtered by priority
   */
  getMissingCredentials(priorityFilter = null) {
    const allStatus = this.checkAllCredentials();
    const missing = [];

    for (const [credentialId, statusInfo] of Object.entries(allStatus)) {
      if (statusInfo.status === CredentialStatus.MISSING) {
        if (priorityFilter === null || statusInfo.priority === priorityFilter) {
          missing.push({
            credentialId,
            ...statusInfo
          });
        }
      }
    }

    return missing;
  }

  /**
   * Get critical missing credentials that should be requested first
   */
  getCriticalMissingCredentials() {
    return this.getMissingCredentials(CredentialPriority.CRITICAL);
  }

  /**
   * Get high priority missing credentials
   */
  getHighPriorityMissingCredentials() {
    const critical = this.getMissingCredentials(CredentialPriority.CRITICAL);
    const high = this.getMissingCredentials(CredentialPriority.HIGH);
    return [...critical, ...high];
  }

  /**
   * Generate a comprehensive service status report
   */
  getServiceStatusReport() {
    const allStatus = this.checkAllCredentials();

    // Group by priority
    const byPriority = {
      critical: [],
      high: [],
      medium: [],
      low: []
    };

    // Count statuses
    const statusCounts = {
      available: 0,
      missing: 0,
      invalid: 0
    };

    const enabledServices = [];
    const disabledServices = [];

    for (const [credentialId, info] of Object.entries(allStatus)) {
      byPriority[info.priority].push(info);

      if (statusCounts[info.status] !== undefined) {
        statusCounts[info.status]++;
      }

      if (info.status === 'available') {
        enabledServices.push(info.serviceName);
      } else {
        disabledServices.push({
          service: info.serviceName,
          reason: info.message,
          setupUrl: info.setupUrl
        });
      }
    }

    return {
      summary: {
        totalCredentials: Object.keys(allStatus).length,
        available: statusCounts.available,
        missing: statusCounts.missing,
        invalid: statusCounts.invalid,
        lastCheck: this.lastCheck?.toISOString() || null
      },
      byPriority,
      enabledServices,
      disabledServices,
      nextSteps: this._generateNextSteps(allStatus)
    };
  }

  /**
   * Generate actionable next steps based on credential status
   */
  _generateNextSteps(allStatus) {
    const steps = [];

    const criticalMissing = Object.values(allStatus).filter(
      info => info.priority === 'critical' && info.status === 'missing'
    );
    const highMissing = Object.values(allStatus).filter(
      info => info.priority === 'high' && info.status === 'missing'
    );

    if (criticalMissing.length > 0) {
      steps.push(`🚨 CRITICAL: Set up ${criticalMissing.length} critical credential(s) for core functionality`);
      for (const cred of criticalMissing) {
        steps.push(`   - Configure ${cred.name} (${cred.envVar})`);
      }
    }

    if (highMissing.length > 0) {
      steps.push(`⚠️  HIGH PRIORITY: Configure ${highMissing.length} important credential(s) for main features`);
      for (const cred of highMissing) {
        if (cred.setupUrl) {
          steps.push(`   - Get ${cred.name}: ${cred.setupUrl}`);
        } else {
          steps.push(`   - Configure ${cred.name} (${cred.envVar})`);
        }
      }
    }

    if (criticalMissing.length === 0 && highMissing.length === 0) {
      steps.push("✅ All critical and high-priority credentials are configured!");
    }

    return steps;
  }

  /**
   * Update API source configurations with current credential status
   */
  updateApiConfig(apiSources) {
    const updatedSources = {};

    for (const [sourceId, sourceConfig] of Object.entries(apiSources)) {
      const updatedConfig = { ...sourceConfig };

      // Map API source to credential
      const credentialMapping = {
        sam_gov_opportunities: 'sam_gov_api_key',
        sam_gov_entity: 'sam_gov_api_key',
        candid: 'candid_api_key',
        candid_news: 'candid_news_key',
        candid_grants: 'candid_grants_key',
        foundation_directory: 'fdo_api_key',
        grantwatch: 'grantwatch_api_key',
        michigan_socrata: 'michigan_socrata_key',
        zyte_api: 'zyte_api_key'
      };

      if (credentialMapping[sourceId]) {
        const credentialId = credentialMapping[sourceId];
        const credentialValue = this.getCredential(credentialId);
        const [status] = this.validateCredential(credentialId, credentialValue);

        // Update configuration
        updatedConfig.api_key = credentialValue;
        updatedConfig.enabled = status === CredentialStatus.AVAILABLE;
        updatedConfig.credential_status = status;

        logger.info(`Updated ${sourceId}: enabled=${updatedConfig.enabled}, status=${status}`);
      }

      updatedSources[sourceId] = updatedConfig;
    }

    return updatedSources;
  }

  /**
   * Get credential information formatted for environment setup
   */
  getCredentialsForSetup() {
    const highPriorityMissing = this.getHighPriorityMissingCredentials();

    return highPriorityMissing.map(cred => ({
      key: cred.envVar,
      description: `${cred.name}: ${cred.description}`,
      url: cred.setupUrl || `Set up ${cred.serviceName} API access`
    }));
  }
}

// Global instance
export const credentialManager = new CredentialManager();

/**
 * Get the global credential manager instance
 */
export function getCredentialManager() {
  return credentialManager;
}

export default credentialManager;