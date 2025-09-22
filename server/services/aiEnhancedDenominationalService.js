/**
 * AI-Enhanced Denominational Service
 * Integrates AI processing with denominational grant data
 * Based on the Python REACTO system architecture
 */

import { createLogger } from '../utils/logger.js';
import { CacheManager } from './cacheManager.js';
import { ScheduledScraper } from './scheduledScraper.js';

const logger = createLogger('AIEnhancedDenominational');

export class AIEnhancedDenominationalService {
  constructor() {
    this.cache = new CacheManager();
    this.scheduledScraper = new ScheduledScraper();
    
    // AI matching weights for denominational grants
    this.matchingWeights = {
      denominationMatch: 0.3,        // Perfect denomination match
      faithTraditionMatch: 0.25,     // Broader faith tradition match
      missionAlignment: 0.2,         // Mission/purpose alignment
      geographicMatch: 0.15,         // Geographic eligibility
      fundingAmountMatch: 0.1        // Funding amount compatibility
    };
    
    // Faith tradition mappings for better matching
    this.faithTraditions = {
      'christian': ['catholic', 'protestant', 'orthodox', 'evangelical', 'baptist', 'methodist', 'presbyterian', 'episcopal', 'lutheran', 'pentecostal'],
      'catholic': ['roman-catholic', 'catholic', 'orthodox'],
      'protestant': ['baptist', 'methodist', 'presbyterian', 'episcopal', 'lutheran', 'evangelical', 'reformed', 'congregational'],
      'interfaith': ['ecumenical', 'multi-faith', 'interfaith', 'interreligious'],
      'progressive': ['progressive', 'liberal', 'inclusive', 'social-justice'],
      'evangelical': ['evangelical', 'conservative', 'fundamentalist', 'born-again']
    };
  }

  /**
   * Enhanced grant matching with AI-like scoring
   * Based on the Python REACTO system but adapted for JavaScript
   */
  async matchGrantsForOrganization(organizationProfile, options = {}) {
    try {
      const { 
        limit = 20, 
        minScore = 2.0, 
        includeExplanation = true,
        prioritizeDenominational = true 
      } = options;
      
      // Get latest denominational grant data
      const latestResults = await this.scheduledScraper.getLatestResults();
      
      if (!latestResults) {
        logger.warn('No denominational grant data available for matching');
        return {
          success: false,
          message: 'No denominational grant data available',
          matches: []
        };
      }
      
      // Extract all opportunities
      const allOpportunities = latestResults.results
        .filter(result => result.status === 'success' && result.opportunities)
        .flatMap(result => result.opportunities);
      
      logger.info(`Matching ${allOpportunities.length} denominational grants against organization profile`);
      
      // Score each opportunity
      const scoredGrants = [];
      
      for (const grant of allOpportunities) {
        const match = this.calculateMatchScore(organizationProfile, grant);
        
        if (match.score >= minScore) {
          const enhancedGrant = {
            ...grant,
            match_score: match.score,
            match_percentage: Math.round(match.score * 20), // Convert 0-5 to 0-100
            match_verdict: this.getMatchVerdict(match.score),
            match_reason: match.explanation,
            key_alignments: match.alignments,
            potential_challenges: match.challenges,
            next_steps: match.nextSteps,
            denominational_priority: match.denominationalPriority,
            confidence_level: match.confidence
          };
          
          scoredGrants.push(enhancedGrant);
        }
      }
      
      // Sort by score and denominational priority
      scoredGrants.sort((a, b) => {
        if (prioritizeDenominational && a.denominational_priority !== b.denominational_priority) {
          return b.denominational_priority - a.denominational_priority;
        }
        return b.match_score - a.match_score;
      });
      
      const topMatches = scoredGrants.slice(0, limit);
      
      logger.info(`Found ${topMatches.length} high-quality denominational grant matches (score >= ${minScore})`);
      
      return {
        success: true,
        matches: topMatches,
        metadata: {
          totalEvaluated: allOpportunities.length,
          qualifyingMatches: scoredGrants.length,
          averageScore: scoredGrants.length > 0 ? 
            (scoredGrants.reduce((sum, g) => sum + g.match_score, 0) / scoredGrants.length).toFixed(2) : 0,
          denominationalSources: latestResults.sourcesProcessed || 0,
          lastDataUpdate: latestResults.scraping_run?.timestamp,
          matchingAlgorithm: 'ai_enhanced_denominational_v1'
        }
      };
      
    } catch (error) {
      logger.error(`Error in AI-enhanced denominational matching: ${error.message}`);
      throw error;
    }
  }

  /**
   * Calculate match score using weighted criteria
   */
  calculateMatchScore(organizationProfile, grant) {
    const scores = {
      denomination: 0,
      faithTradition: 0,
      mission: 0,
      geographic: 0,
      fundingAmount: 0
    };
    
    const alignments = [];
    const challenges = [];
    let denominationalPriority = 0;
    
    // 1. Denomination/Faith Matching
    if (organizationProfile.denomination) {
      const orgDenom = organizationProfile.denomination.toLowerCase();
      const grantTags = grant.tags || [];
      
      // Direct denomination match
      if (grantTags.some(tag => tag.toLowerCase().includes(orgDenom))) {
        scores.denomination = 5;
        alignments.push(`Direct ${organizationProfile.denomination} denomination match`);
        denominationalPriority = 3;
      } else {
        // Faith tradition matching
        for (const [tradition, denominations] of Object.entries(this.faithTraditions)) {
          if (denominations.includes(orgDenom)) {
            const traditionMatch = grantTags.some(tag => 
              denominations.includes(tag.toLowerCase()) || tag.toLowerCase().includes(tradition)
            );
            if (traditionMatch) {
              scores.faithTradition = 4;
              alignments.push(`Compatible faith tradition (${tradition})`);
              denominationalPriority = 2;
              break;
            }
          }
        }
      }
    }
    
    // 2. Mission/Focus Area Alignment
    if (organizationProfile.focusAreas && organizationProfile.missionStatement) {
      const orgMission = (organizationProfile.missionStatement + ' ' + organizationProfile.focusAreas.join(' ')).toLowerCase();
      const grantDescription = (grant.title + ' ' + grant.description).toLowerCase();
      
      // Look for mission keywords
      const missionKeywords = this.extractMissionKeywords(orgMission);
      const grantKeywords = this.extractMissionKeywords(grantDescription);
      
      const commonKeywords = missionKeywords.filter(keyword => 
        grantKeywords.includes(keyword)
      );
      
      if (commonKeywords.length > 0) {
        scores.mission = Math.min(5, 2 + commonKeywords.length);
        alignments.push(`Mission alignment: ${commonKeywords.join(', ')}`);
      }
    }
    
    // 3. Geographic Eligibility
    if (organizationProfile.location) {
      const orgLocation = organizationProfile.location.toLowerCase();
      const grantGeography = grant.geography?.toLowerCase() || '';
      const grantDescription = grant.description.toLowerCase();
      
      if (grantGeography.includes('national') || grantDescription.includes('nationwide')) {
        scores.geographic = 5;
        alignments.push('National eligibility');
      } else if (grantGeography.includes(orgLocation) || grantDescription.includes(orgLocation)) {
        scores.geographic = 4;
        alignments.push(`Local/regional eligibility (${organizationProfile.location})`);
      } else if (grantGeography.includes('usa') || grantGeography.includes('america')) {
        scores.geographic = 3;
        alignments.push('US-wide eligibility');
      }
    }
    
    // 4. Funding Amount Compatibility
    if (organizationProfile.annualBudget && grant.funding_amount) {
      const grantAmount = this.extractFundingAmount(grant.funding_amount);
      const orgBudget = parseInt(organizationProfile.annualBudget);
      
      if (grantAmount > 0) {
        if (grantAmount <= orgBudget * 0.5) {
          scores.fundingAmount = 5;
          alignments.push(`Funding amount well within capacity ($${grantAmount.toLocaleString()})`);
        } else if (grantAmount <= orgBudget) {
          scores.fundingAmount = 4;
          alignments.push(`Funding amount manageable ($${grantAmount.toLocaleString()})`);
        } else if (grantAmount <= orgBudget * 2) {
          scores.fundingAmount = 2;
          challenges.push(`Large funding amount may require capacity building ($${grantAmount.toLocaleString()})`);
        }
      }
    }
    
    // Calculate weighted final score
    const finalScore = 
      (scores.denomination * this.matchingWeights.denominationMatch) +
      (scores.faithTradition * this.matchingWeights.faithTraditionMatch) +
      (scores.mission * this.matchingWeights.missionAlignment) +
      (scores.geographic * this.matchingWeights.geographicMatch) +
      (scores.fundingAmount * this.matchingWeights.fundingAmountMatch);
    
    // Add challenges for common issues
    if (scores.denomination === 0 && scores.faithTradition === 0) {
      challenges.push('No clear denominational alignment - verify eligibility requirements');
    }
    
    if (scores.geographic < 3) {
      challenges.push('Geographic restrictions may apply - check eligibility carefully');
    }
    
    // Generate next steps
    const nextSteps = this.generateNextSteps(grant, scores, organizationProfile);
    
    // Calculate confidence based on data quality
    const confidence = this.calculateConfidence(grant, scores);
    
    const explanation = this.generateExplanation(finalScore, alignments, challenges);
    
    return {
      score: Math.round(finalScore * 100) / 100, // Round to 2 decimal places
      explanation,
      alignments: alignments.slice(0, 5), // Top 5 alignments
      challenges: challenges.slice(0, 3), // Top 3 challenges
      nextSteps,
      denominationalPriority,
      confidence,
      breakdown: {
        denomination: scores.denomination,
        faithTradition: scores.faithTradition,
        mission: scores.mission,
        geographic: scores.geographic,
        fundingAmount: scores.fundingAmount
      }
    };
  }

  /**
   * Extract mission keywords for matching
   */
  extractMissionKeywords(text) {
    const keywords = [
      'youth', 'children', 'education', 'community', 'outreach', 'ministry', 'service',
      'social justice', 'poverty', 'homeless', 'hunger', 'health', 'elderly', 'seniors',
      'mission', 'evangelism', 'discipleship', 'worship', 'spiritual', 'faith',
      'urban', 'rural', 'immigrant', 'refugee', 'multicultural', 'diversity',
      'arts', 'music', 'culture', 'environment', 'sustainability', 'technology'
    ];
    
    return keywords.filter(keyword => text.includes(keyword));
  }

  /**
   * Extract funding amount from text
   */
  extractFundingAmount(text) {
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
   * Generate contextual next steps
   */
  generateNextSteps(grant, scores, organizationProfile) {
    const steps = [];
    
    steps.push('Review full grant guidelines on the foundation website');
    
    if (scores.denomination > 0 || scores.faithTradition > 0) {
      steps.push('Highlight denominational connection in application');
    }
    
    if (grant.contact_info?.email) {
      steps.push('Contact program officer for pre-application discussion');
    }
    
    if (scores.mission > 3) {
      steps.push('Emphasize mission alignment in proposal narrative');
    }
    
    if (grant.deadline && grant.deadline !== 'rolling') {
      steps.push(`Prepare application materials before ${grant.deadline} deadline`);
    }
    
    return steps;
  }

  /**
   * Calculate confidence level based on data quality
   */
  calculateConfidence(grant, scores) {
    let confidence = 0.5; // Base confidence
    
    // Increase confidence for complete data
    if (grant.description && grant.description.length > 100) confidence += 0.1;
    if (grant.funding_amount) confidence += 0.1;
    if (grant.eligibility && grant.eligibility.length > 50) confidence += 0.1;
    if (grant.contact_info?.email) confidence += 0.1;
    if (grant.application_url) confidence += 0.1;
    
    // Adjust based on match quality
    const avgScore = Object.values(scores).reduce((a, b) => a + b, 0) / Object.values(scores).length;
    if (avgScore > 3) confidence += 0.1;
    
    return Math.min(1.0, Math.round(confidence * 100) / 100);
  }

  /**
   * Generate human-readable explanation
   */
  generateExplanation(score, alignments, challenges) {
    let explanation = '';
    
    if (score >= 4.0) {
      explanation = 'Excellent match with strong denominational and mission alignment.';
    } else if (score >= 3.0) {
      explanation = 'Good match with solid alignment in key areas.';
    } else if (score >= 2.0) {
      explanation = 'Moderate match worth exploring further.';
    } else {
      explanation = 'Lower match - review requirements carefully.';
    }
    
    if (alignments.length > 0) {
      explanation += ` Key strengths: ${alignments[0]}.`;
    }
    
    if (challenges.length > 0) {
      explanation += ` Consider: ${challenges[0]}.`;
    }
    
    return explanation;
  }

  /**
   * Get match verdict based on score
   */
  getMatchVerdict(score) {
    if (score >= 4.0) return 'Highly Recommended';
    if (score >= 3.0) return 'Recommended';
    if (score >= 2.5) return 'Consider Applying';
    if (score >= 2.0) return 'Worth Exploring';
    return 'Low Priority';
  }

  /**
   * Get enhanced grant data with AI analysis
   */
  async getEnhancedGrantData(grantId, organizationProfile) {
    try {
      const latestResults = await this.scheduledScraper.getLatestResults();
      
      if (!latestResults) {
        throw new Error('No denominational grant data available');
      }
      
      // Find the specific grant
      const allOpportunities = latestResults.results
        .filter(result => result.status === 'success' && result.opportunities)
        .flatMap(result => result.opportunities);
      
      const grant = allOpportunities.find(g => g.id === grantId);
      
      if (!grant) {
        throw new Error(`Grant with ID ${grantId} not found`);
      }
      
      // Calculate match for this specific grant
      const match = this.calculateMatchScore(organizationProfile, grant);
      
      return {
        ...grant,
        aiAnalysis: {
          matchScore: match.score,
          matchPercentage: Math.round(match.score * 20),
          verdict: this.getMatchVerdict(match.score),
          explanation: match.explanation,
          alignments: match.alignments,
          challenges: match.challenges,
          nextSteps: match.nextSteps,
          confidence: match.confidence,
          breakdown: match.breakdown
        }
      };
      
    } catch (error) {
      logger.error(`Error getting enhanced grant data: ${error.message}`);
      throw error;
    }
  }
}

export default AIEnhancedDenominationalService;