/**
 * Integrated Grant Search Service
 * Combines traditional API sources with denominational scraped data
 * Provides unified search and matching across all grant sources
 */

import { createLogger } from '../utils/logger.js';
import { apiManager } from './apiManager.js';
import { AIEnhancedDenominationalService } from './aiEnhancedDenominationalService.js';
import { CacheManager } from './cacheManager.js';

const logger = createLogger('IntegratedGrantSearch');

export class IntegratedGrantSearch {
  constructor() {
    this.cache = new CacheManager();
    this.denominationalService = new AIEnhancedDenominationalService();
    
    // Search result priorities and weights
    this.sourceWeights = {
      'denominational': 1.2,      // Boost denominational matches
      'candid': 1.1,              // High-quality foundation data
      'grants_gov': 1.0,          // Federal opportunities
      'sam_gov': 1.0,             // Government contracts
      'federal_register': 0.9,    // Federal notices
      'foundation_directory': 1.1, // Foundation data
      'default': 1.0
    };
  }

  /**
   * Unified search across all grant sources
   */
  async searchAllSources(searchParams, organizationProfile = null) {
    try {
      const {
        query = '',
        filters = {},
        pagination = { page: 1, limit: 50, offset: 0 },
        includeAIScoring = true,
        prioritizeDenominational = true
      } = searchParams;
      
      logger.info(`Integrated search for "${query}" across all sources`);
      
      // Search traditional API sources
      const apiResults = await this.searchApiSources(query, filters, pagination);
      
      // Search denominational sources
      const denominationalResults = await this.searchDenominationalSources(query, filters, organizationProfile);
      
      // Combine and deduplicate results
      const combinedResults = await this.combineResults(
        apiResults, 
        denominationalResults, 
        organizationProfile,
        { includeAIScoring, prioritizeDenominational }
      );
      
      // Apply final sorting and pagination
      const sortedResults = this.sortResults(combinedResults, prioritizeDenominational);
      const paginatedResults = this.applyPagination(sortedResults, pagination);
      
      return {
        success: true,
        grants: paginatedResults,
        metadata: {
          totalResults: combinedResults.length,
          apiSourceResults: apiResults.total || 0,
          denominationalResults: denominationalResults.length,
          searchQuery: query,
          filtersApplied: Object.keys(filters).length,
          aiScoringEnabled: includeAIScoring,
          denominationalPriority: prioritizeDenominational,
          sources: this.getSourceSummary(combinedResults)
        }
      };
      
    } catch (error) {
      logger.error(`Integrated search error: ${error.message}`);
      throw error;
    }
  }

  /**
   * Search traditional API sources
   */
  async searchApiSources(query, filters, pagination) {
    try {
      // Use existing API manager search
      const searchResult = await apiManager.searchOpportunities(query, {
        ...filters,
        pagination
      });
      
      // Add source metadata to each grant
      const grantsWithSource = (searchResult.grants || []).map(grant => ({
        ...grant,
        source_type: 'api',
        source_category: this.categorizeApiSource(grant.source),
        search_relevance: this.calculateSearchRelevance(grant, query)
      }));
      
      return {
        grants: grantsWithSource,
        total: searchResult.total || grantsWithSource.length
      };
      
    } catch (error) {
      logger.error(`API sources search error: ${error.message}`);
      return { grants: [], total: 0 };
    }
  }

  /**
   * Search denominational sources with AI enhancement
   */
  async searchDenominationalSources(query, filters, organizationProfile) {
    try {
      const latestResults = this.denominationalService.scheduledScraper.getLatestResults();
      
      if (!latestResults) {
        logger.warn('No denominational data available for search');
        return [];
      }
      
      // Extract all opportunities
      let opportunities = latestResults.results
        .filter(result => result.status === 'success' && result.opportunities)
        .flatMap(result => result.opportunities);
      
      // Apply text search
      if (query) {
        const searchTerms = query.toLowerCase().split(' ').filter(term => term.length > 2);
        opportunities = opportunities.filter(opp => {
          const searchableText = `${opp.title} ${opp.description} ${opp.tags?.join(' ')} ${opp.source}`.toLowerCase();
          return searchTerms.some(term => searchableText.includes(term));
        });
      }
      
      // Apply filters
      opportunities = this.applyFilters(opportunities, filters);
      
      // Add AI scoring if organization profile is provided
      if (organizationProfile) {
        opportunities = await this.addAIScoring(opportunities, organizationProfile);
      }
      
      // Add source metadata
      opportunities = opportunities.map(opp => ({
        ...opp,
        source_type: 'denominational',
        source_category: 'faith_based',
        search_relevance: this.calculateSearchRelevance(opp, query),
        denominational_source: true
      }));
      
      return opportunities;
      
    } catch (error) {
      logger.error(`Denominational sources search error: ${error.message}`);
      return [];
    }
  }

  /**
   * Apply filters to opportunities
   */
  applyFilters(opportunities, filters) {
    let filtered = opportunities;
    
    if (filters.source) {
      filtered = filtered.filter(opp => 
        opp.source.toLowerCase().includes(filters.source.toLowerCase())
      );
    }
    
    if (filters.tag) {
      filtered = filtered.filter(opp => 
        opp.tags && opp.tags.some(t => t.toLowerCase().includes(filters.tag.toLowerCase()))
      );
    }
    
    if (filters.status) {
      filtered = filtered.filter(opp => opp.status === filters.status);
    }
    
    if (filters.amount_min) {
      filtered = filtered.filter(opp => {
        const amount = this.extractAmount(opp.funding_amount);
        return amount >= parseInt(filters.amount_min);
      });
    }
    
    if (filters.amount_max) {
      filtered = filtered.filter(opp => {
        const amount = this.extractAmount(opp.funding_amount);
        return amount <= parseInt(filters.amount_max);
      });
    }
    
    if (filters.location) {
      filtered = filtered.filter(opp => {
        const geography = opp.geography?.toLowerCase() || '';
        const description = opp.description?.toLowerCase() || '';
        const location = filters.location.toLowerCase();
        return geography.includes(location) || description.includes(location);
      });
    }
    
    if (filters.deadline_after) {
      const dateThreshold = new Date(filters.deadline_after);
      filtered = filtered.filter(opp => {
        if (!opp.deadline) return true; // Include rolling deadlines
        const deadline = new Date(opp.deadline);
        return deadline >= dateThreshold;
      });
    }
    
    if (filters.deadline_before) {
      const dateThreshold = new Date(filters.deadline_before);
      filtered = filtered.filter(opp => {
        if (!opp.deadline) return false; // Exclude rolling deadlines for before filter
        const deadline = new Date(opp.deadline);
        return deadline <= dateThreshold;
      });
    }
    
    return filtered;
  }

  /**
   * Add AI scoring to opportunities
   */
  async addAIScoring(opportunities, organizationProfile) {
    const scoredOpportunities = [];
    
    for (const opp of opportunities) {
      try {
        const match = this.denominationalService.calculateMatchScore(organizationProfile, opp);
        
        scoredOpportunities.push({
          ...opp,
          match_score: match.score,
          match_percentage: Math.round(match.score * 20),
          match_verdict: this.denominationalService.getMatchVerdict(match.score),
          match_reason: match.explanation,
          key_alignments: match.alignments,
          potential_challenges: match.challenges,
          denominational_priority: match.denominationalPriority,
          ai_confidence: match.confidence
        });
        
      } catch (error) {
        logger.warn(`Error scoring opportunity ${opp.id}: ${error.message}`);
        scoredOpportunities.push({
          ...opp,
          match_score: 0,
          match_reason: 'Scoring unavailable'
        });
      }
    }
    
    return scoredOpportunities;
  }

  /**
   * Combine and deduplicate results from different sources
   */
  async combineResults(apiResults, denominationalResults, organizationProfile, options) {
    const { includeAIScoring, prioritizeDenominational } = options;
    
    let combined = [];
    
    // Add API results
    combined.push(...apiResults.grants);
    
    // Add denominational results
    combined.push(...denominationalResults);
    
    // Deduplicate based on title and source similarity
    combined = this.deduplicateResults(combined);
    
    // Apply source-based weighting
    combined = combined.map(grant => ({
      ...grant,
      weighted_score: this.calculateWeightedScore(grant),
      final_score: grant.match_score || 0
    }));
    
    return combined;
  }

  /**
   * Deduplicate similar grants from different sources
   */
  deduplicateResults(grants) {
    const deduplicated = [];
    const seen = new Set();
    
    for (const grant of grants) {
      // Create a simple fingerprint based on title and source
      const fingerprint = this.createGrantFingerprint(grant);
      
      if (!seen.has(fingerprint)) {
        seen.add(fingerprint);
        deduplicated.push(grant);
      } else {
        // If duplicate, prefer denominational source or higher quality data
        const existingIndex = deduplicated.findIndex(g => 
          this.createGrantFingerprint(g) === fingerprint
        );
        
        if (existingIndex >= 0) {
          const existing = deduplicated[existingIndex];
          if (this.shouldReplaceExisting(existing, grant)) {
            deduplicated[existingIndex] = grant;
          }
        }
      }
    }
    
    return deduplicated;
  }

  /**
   * Create a fingerprint for grant deduplication
   */
  createGrantFingerprint(grant) {
    const title = grant.title?.toLowerCase().replace(/[^\w\s]/g, '').trim() || '';
    const source = grant.source?.toLowerCase() || '';
    
    // Create a simple hash-like string
    const words = title.split(' ').filter(word => word.length > 3).slice(0, 5);
    return `${words.join('_')}_${source.replace(/\s+/g, '_')}`;
  }

  /**
   * Determine if a duplicate grant should replace the existing one
   */
  shouldReplaceExisting(existing, candidate) {
    // Prefer denominational sources
    if (candidate.denominational_source && !existing.denominational_source) {
      return true;
    }
    
    // Prefer grants with AI scoring
    if (candidate.match_score > 0 && (!existing.match_score || existing.match_score === 0)) {
      return true;
    }
    
    // Prefer more complete data
    const existingCompleteness = this.calculateDataCompleteness(existing);
    const candidateCompleteness = this.calculateDataCompleteness(candidate);
    
    return candidateCompleteness > existingCompleteness;
  }

  /**
   * Calculate data completeness score
   */
  calculateDataCompleteness(grant) {
    let score = 0;
    
    if (grant.title && grant.title.length > 10) score += 1;
    if (grant.description && grant.description.length > 50) score += 1;
    if (grant.funding_amount) score += 1;
    if (grant.deadline) score += 1;
    if (grant.eligibility && grant.eligibility.length > 20) score += 1;
    if (grant.application_url) score += 1;
    if (grant.contact_info?.email) score += 1;
    
    return score;
  }

  /**
   * Calculate weighted score based on source quality and type
   */
  calculateWeightedScore(grant) {
    const baseScore = grant.match_score || grant.search_relevance || 1;
    const sourceKey = grant.source?.toLowerCase().replace(/\s+/g, '_') || 'default';
    const weight = this.sourceWeights[sourceKey] || this.sourceWeights.default;
    
    // Additional boost for denominational sources if relevant
    let additionalBoost = 1;
    if (grant.denominational_source && grant.denominational_priority > 0) {
      additionalBoost = 1 + (grant.denominational_priority * 0.1);
    }
    
    return baseScore * weight * additionalBoost;
  }

  /**
   * Sort combined results
   */
  sortResults(results, prioritizeDenominational = true) {
    return results.sort((a, b) => {
      // Primary sort: denominational priority if enabled
      if (prioritizeDenominational) {
        const aPriority = a.denominational_priority || 0;
        const bPriority = b.denominational_priority || 0;
        if (aPriority !== bPriority) {
          return bPriority - aPriority;
        }
      }
      
      // Secondary sort: weighted score
      const aScore = a.weighted_score || a.final_score || 0;
      const bScore = b.weighted_score || b.final_score || 0;
      if (aScore !== bScore) {
        return bScore - aScore;
      }
      
      // Tertiary sort: recency (if available)
      const aDate = new Date(a.last_updated || a.created_at || 0);
      const bDate = new Date(b.last_updated || b.created_at || 0);
      return bDate - aDate;
    });
  }

  /**
   * Apply pagination to results
   */
  applyPagination(results, pagination) {
    const { page = 1, limit = 50 } = pagination;
    const offset = (page - 1) * limit;
    return results.slice(offset, offset + limit);
  }

  /**
   * Calculate search relevance for text matching
   */
  calculateSearchRelevance(grant, query) {
    if (!query) return 1;
    
    const searchTerms = query.toLowerCase().split(' ').filter(term => term.length > 2);
    const title = grant.title?.toLowerCase() || '';
    const description = grant.description?.toLowerCase() || '';
    
    let relevance = 0;
    
    searchTerms.forEach(term => {
      if (title.includes(term)) relevance += 2;
      if (description.includes(term)) relevance += 1;
    });
    
    return Math.min(5, relevance);
  }

  /**
   * Extract funding amount from various formats
   */
  extractAmount(text) {
    if (!text) return 0;
    
    const match = text.match(/\$?([\d,]+(?:\.\d{2})?)/);
    if (match) {
      return parseInt(match[1].replace(/,/g, ''));
    }
    
    // Handle shorthand (5K, 100K, 1M)
    const shorthandMatch = text.match(/(\d+)([kKmM])/);
    if (shorthandMatch) {
      const number = parseInt(shorthandMatch[1]);
      const multiplier = shorthandMatch[2].toLowerCase() === 'k' ? 1000 : 1000000;
      return number * multiplier;
    }
    
    return 0;
  }

  /**
   * Categorize API source type
   */
  categorizeApiSource(source) {
    const sourceName = source?.toLowerCase() || '';
    
    if (sourceName.includes('candid')) return 'foundation_database';
    if (sourceName.includes('grants.gov')) return 'federal_grants';
    if (sourceName.includes('sam.gov')) return 'federal_contracts';
    if (sourceName.includes('federal_register')) return 'federal_notices';
    if (sourceName.includes('foundation')) return 'foundation_direct';
    
    return 'other';
  }

  /**
   * Generate source summary for metadata
   */
  getSourceSummary(results) {
    const summary = {};
    
    results.forEach(grant => {
      const category = grant.source_category || 'other';
      summary[category] = (summary[category] || 0) + 1;
    });
    
    return summary;
  }

  /**
   * Get recommended grants for organization (smart discovery)
   */
  async discoverGrantsForOrganization(organizationProfile, options = {}) {
    try {
      const {
        limit = 20,
        includeExplanations = true,
        minScore = 2.5
      } = options;
      
      logger.info(`Discovering grants for organization: ${organizationProfile.name || 'Unknown'}`);
      
      // Build smart search query based on organization profile
      const smartQuery = this.buildSmartQuery(organizationProfile);
      
      // Build smart filters
      const smartFilters = this.buildSmartFilters(organizationProfile);
      
      // Perform integrated search
      const searchResults = await this.searchAllSources({
        query: smartQuery,
        filters: smartFilters,
        pagination: { page: 1, limit: limit * 2 }, // Get more to filter by score
        includeAIScoring: true,
        prioritizeDenominational: true
      }, organizationProfile);
      
      // Filter by minimum score and return top matches
      const qualifiedGrants = searchResults.grants
        .filter(grant => (grant.match_score || 0) >= minScore)
        .slice(0, limit);
      
      return {
        success: true,
        grants: qualifiedGrants,
        metadata: {
          ...searchResults.metadata,
          discoveryQuery: smartQuery,
          smartFilters: smartFilters,
          organizationName: organizationProfile.name,
          minScoreFilter: minScore,
          qualificationRate: searchResults.grants.length > 0 ? 
            (qualifiedGrants.length / searchResults.grants.length * 100).toFixed(1) + '%' : '0%'
        }
      };
      
    } catch (error) {
      logger.error(`Grant discovery error: ${error.message}`);
      throw error;
    }
  }

  /**
   * Build smart search query from organization profile
   */
  buildSmartQuery(profile) {
    const queryParts = [];
    
    if (profile.focusAreas && profile.focusAreas.length > 0) {
      queryParts.push(...profile.focusAreas.slice(0, 3)); // Top 3 focus areas
    }
    
    if (profile.denomination) {
      queryParts.push(profile.denomination);
    }
    
    if (profile.organizationType) {
      queryParts.push(profile.organizationType);
    }
    
    // Add mission keywords
    if (profile.missionStatement) {
      const missionKeywords = this.denominationalService.extractMissionKeywords(
        profile.missionStatement.toLowerCase()
      );
      queryParts.push(...missionKeywords.slice(0, 2));
    }
    
    return queryParts.join(' ');
  }

  /**
   * Build smart filters from organization profile
   */
  buildSmartFilters(profile) {
    const filters = {};
    
    if (profile.location) {
      filters.location = profile.location;
    }
    
    if (profile.annualBudget) {
      // Set reasonable funding range based on budget
      const budget = parseInt(profile.annualBudget);
      filters.amount_min = Math.floor(budget * 0.05); // 5% of budget minimum
      filters.amount_max = budget * 2; // Up to 2x budget maximum
    }
    
    // Only include open opportunities
    filters.status = 'open';
    
    // Only include future deadlines
    filters.deadline_after = new Date().toISOString().split('T')[0];
    
    return filters;
  }
}

export default IntegratedGrantSearch;