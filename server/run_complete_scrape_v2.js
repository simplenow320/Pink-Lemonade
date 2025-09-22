#!/usr/bin/env node
/**
 * Enhanced Complete Grant Scraper v2
 * Improved version with better error handling, retry logic, and smarter grant extraction
 */

import fetch from 'node-fetch';
import * as cheerio from 'cheerio';
import { databasePersistence } from './services/databasePersistence.js';
import { createLogger } from './utils/logger.js';
import fs from 'fs/promises';
import crypto from 'crypto';

const logger = createLogger('EnhancedCompleteScraper');

class EnhancedCompleteScraper {
  constructor() {
    this.userAgents = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15',
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ];
    
    this.timeout = 20000; // 20 seconds
    this.retryAttempts = 3;
    this.retryDelay = 2000; // 2 seconds
    this.delayBetweenRequests = 3000; // 3 seconds - respectful but faster
    this.maxGrantsPerSource = 20; // Increase max grants
    this.maxLinksToCheck = 15; // Check more links per source
    
    // Enhanced grant keywords for better detection
    this.grantKeywords = [
      'grant', 'grants', 'funding', 'funds', 'award', 'awards', 'scholarship', 
      'fellowship', 'opportunity', 'opportunities', 'application', 'apply',
      'deadline', 'proposal', 'rfp', 'request for proposal', 'support',
      'initiative', 'program', 'foundation', 'endowment', 'contribution',
      'donation', 'subsidy', 'sponsorship', 'financial assistance',
      'call for proposals', 'open call', 'funding cycle', 'grant cycle',
      'eligibility', 'guidelines', 'criteria', 'submission'
    ];
    
    this.negativeKeywords = [
      'login', 'sign in', 'password', 'privacy', 'cookie', 'terms of service',
      'newsletter', 'subscribe', 'donate now', 'give now', 'volunteer',
      'careers', 'jobs', 'employment', 'contact us', 'about us', 'history',
      'board', 'staff', 'team', 'annual report', 'financial statement',
      'twitter', 'facebook', 'instagram', 'linkedin', 'youtube'
    ];
    
    this.resultsCache = new Map();
    this.statistics = {
      totalSources: 0,
      successfulSources: 0,
      failedSources: 0,
      totalGrants: 0,
      sourcesWithGrants: 0,
      errors: []
    };
  }

  /**
   * Load enhanced foundation sources with verified URLs and fallbacks
   */
  async loadEnhancedFoundationSources() {
    return [
      // Tech/AI Philanthropy - VERIFIED WORKING URLS
      { 
        name: 'Patrick J. McGovern Foundation', 
        url: 'https://www.mcgovern.org/grants/',
        fallbackUrls: ['https://www.mcgovern.org/our-grants/', 'https://www.mcgovern.org'],
        type: 'tech_philanthropy',
        selectors: ['.grant-item', '.funding-opportunity', 'article']
      },
      { 
        name: 'Schmidt Futures', 
        url: 'https://www.schmidtfutures.com/our-work/',
        fallbackUrls: ['https://www.schmidtfutures.com/our-method/', 'https://www.schmidtfutures.com'],
        type: 'tech_philanthropy'
      },
      { 
        name: 'Ford Foundation', 
        url: 'https://www.fordfoundation.org/our-work-around-the-world/',
        fallbackUrls: ['https://www.fordfoundation.org/work/our-grants/', 'https://www.fordfoundation.org'],
        type: 'tech_philanthropy'
      },
      { 
        name: 'Mozilla Foundation', 
        url: 'https://foundation.mozilla.org/en/what-we-fund/',
        fallbackUrls: ['https://foundation.mozilla.org/en/initiatives/', 'https://www.mozilla.org/en-US/grants/'],
        type: 'tech_philanthropy'
      },
      { 
        name: 'Omidyar Network', 
        url: 'https://omidyar.com/our-work/',
        fallbackUrls: ['https://omidyar.com/', 'https://www.omidyar.com/responsible-technology/'],
        type: 'tech_philanthropy'
      },
      
      // Corporate Tech Grants - VERIFIED WORKING URLS
      { 
        name: 'AWS IMAGINE Grant', 
        url: 'https://aws.amazon.com/government-education/nonprofits/aws-imagine-grant/',
        fallbackUrls: ['https://aws.amazon.com/government-education/nonprofits/', 'https://aws.amazon.com/grants/'],
        type: 'corporate_grant'
      },
      { 
        name: 'Google.org', 
        url: 'https://www.google.org/our-work/',
        fallbackUrls: ['https://www.google.org/', 'https://ai.google/social-good/'],
        type: 'corporate_grant'
      },
      { 
        name: 'Microsoft Philanthropies', 
        url: 'https://www.microsoft.com/en-us/nonprofits',
        fallbackUrls: ['https://www.microsoft.com/en-us/ai/ai-for-good', 'https://www.microsoft.com/en-us/ai/ai-for-accessibility'],
        type: 'corporate_grant'
      },
      { 
        name: 'Salesforce.org', 
        url: 'https://www.salesforce.org/nonprofit/',
        fallbackUrls: ['https://www.salesforce.org/grants/', 'https://www.salesforce.org/'],
        type: 'corporate_grant'
      },
      { 
        name: 'Cisco Foundation', 
        url: 'https://www.cisco.com/c/en/us/about/csr/community/nonprofits.html',
        fallbackUrls: ['https://www.cisco.com/c/en/us/about/csr.html'],
        type: 'corporate_grant'
      },
      
      // Regional Foundations - Michigan - VERIFIED WORKING URLS
      { 
        name: 'Grand Rapids Community Foundation', 
        url: 'https://www.grfoundation.org/nonprofits',
        fallbackUrls: ['https://www.grfoundation.org/receive/nonprofits', 'https://www.grfoundation.org/'],
        type: 'regional_foundation'
      },
      { 
        name: 'Community Foundation for Southeast Michigan', 
        url: 'https://cfsem.org/nonprofit-center/grant-opportunities/',
        fallbackUrls: ['https://cfsem.org/initiative/grants/', 'https://cfsem.org/'],
        type: 'regional_foundation'
      },
      { 
        name: 'The Kresge Foundation', 
        url: 'https://kresge.org/our-work/',
        fallbackUrls: ['https://kresge.org/opportunities/', 'https://kresge.org/'],
        type: 'regional_foundation'
      },
      { 
        name: 'W.K. Kellogg Foundation', 
        url: 'https://www.wkkf.org/grants',
        fallbackUrls: ['https://www.wkkf.org/what-we-do', 'https://www.wkkf.org/'],
        type: 'regional_foundation'
      },
      { 
        name: 'Ralph C. Wilson Jr. Foundation', 
        url: 'https://www.rcwjrf.org/grants-initiatives/',
        fallbackUrls: ['https://www.rcwjrf.org/', 'https://www.ralphcwilsonjrfoundation.org/'],
        type: 'regional_foundation'
      },
      
      // Regional Foundations - Georgia - VERIFIED WORKING URLS
      { 
        name: 'Community Foundation for Greater Atlanta', 
        url: 'https://cfgreateratlanta.org/nonprofits/available-grants/',
        fallbackUrls: ['https://cfgreateratlanta.org/nonprofits/', 'https://cfgreateratlanta.org/'],
        type: 'regional_foundation'
      },
      { 
        name: 'Arthur M. Blank Family Foundation', 
        url: 'https://blankfoundation.org/our-giving/',
        fallbackUrls: ['https://blankfoundation.org/', 'https://www.blankfamilyofbusinesses.com/blank-family-foundation/'],
        type: 'regional_foundation'
      },
      { 
        name: 'The Coca-Cola Foundation', 
        url: 'https://www.coca-colacompany.com/shared-future/coca-cola-foundation',
        fallbackUrls: ['https://www.coca-colacompany.com/social-impact', 'https://www.coca-colacompany.com/'],
        type: 'regional_foundation'
      },
      { 
        name: 'Robert W. Woodruff Foundation', 
        url: 'https://woodruff.org/grants/',
        fallbackUrls: ['https://woodruff.org/grantmaking/', 'https://woodruff.org/'],
        type: 'regional_foundation'
      },
      { 
        name: 'The UPS Foundation', 
        url: 'https://about.ups.com/us/en/social-impact/the-ups-foundation.html',
        fallbackUrls: ['https://about.ups.com/us/en/social-impact.html', 'https://www.ups.com/foundation'],
        type: 'regional_foundation'
      },
      
      // Faith-based Foundations - VERIFIED WORKING URLS
      { 
        name: 'John Templeton Foundation', 
        url: 'https://www.templeton.org/grants',
        fallbackUrls: ['https://www.templeton.org/funding-areas', 'https://www.templeton.org/'],
        type: 'faith_based',
        selectors: ['.funding-area', '.grant-opportunity', '.grant-program']
      },
      { 
        name: 'Lilly Endowment', 
        url: 'https://lillyendowment.org/our-work/',
        fallbackUrls: ['https://lillyendowment.org/grant-opportunities/', 'https://lillyendowment.org/'],
        type: 'faith_based'
      },
      { 
        name: 'Conrad N. Hilton Foundation', 
        url: 'https://www.hiltonfoundation.org/grantmaking',
        fallbackUrls: ['https://www.hiltonfoundation.org/priorities', 'https://www.hiltonfoundation.org/'],
        type: 'faith_based'
      },
      { 
        name: 'The Duke Endowment', 
        url: 'https://www.dukeendowment.org/our-work/grants',
        fallbackUrls: ['https://www.dukeendowment.org/grantmaking', 'https://www.dukeendowment.org/'],
        type: 'faith_based'
      },
      { 
        name: 'Trinity Church Wall Street', 
        url: 'https://www.trinitywallstreet.org/grants',
        fallbackUrls: ['https://www.trinitywallstreet.org/social-justice/grants', 'https://www.trinitywallstreet.org/'],
        type: 'faith_based'
      },
      
      // Additional High-Value Foundations - VERIFIED WORKING URLS
      { 
        name: 'Bill & Melinda Gates Foundation', 
        url: 'https://www.gatesfoundation.org/about/how-we-work/grants-database',
        fallbackUrls: ['https://www.gatesfoundation.org/ideas/grants-funding', 'https://www.gatesfoundation.org/'],
        type: 'major_foundation'
      },
      { 
        name: 'MacArthur Foundation', 
        url: 'https://www.macfound.org/programs/',
        fallbackUrls: ['https://www.macfound.org/info-grantseekers/', 'https://www.macfound.org/'],
        type: 'major_foundation'
      },
      { 
        name: 'Andrew W. Mellon Foundation', 
        url: 'https://mellon.org/grants/',
        fallbackUrls: ['https://mellon.org/programs/', 'https://mellon.org/'],
        type: 'major_foundation'
      },
      { 
        name: 'Knight Foundation', 
        url: 'https://knightfoundation.org/grants/',
        fallbackUrls: ['https://knightfoundation.org/apply/', 'https://knightfoundation.org/'],
        type: 'major_foundation'
      },
      { 
        name: 'Robert Wood Johnson Foundation', 
        url: 'https://www.rwjf.org/en/grants.html',
        fallbackUrls: ['https://www.rwjf.org/en/how-we-work/grants-explorer.html', 'https://www.rwjf.org/'],
        type: 'major_foundation'
      }
    ];
  }

  /**
   * Fetch URL with retry logic and better error handling
   */
  async fetchWithRetry(url, attempt = 1) {
    const userAgent = this.userAgents[Math.floor(Math.random() * this.userAgents.length)];
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);
      
      const response = await fetch(url, {
        headers: {
          'User-Agent': userAgent,
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.5',
          'Accept-Encoding': 'gzip, deflate',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        },
        signal: controller.signal,
        redirect: 'follow',
        compress: true
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`Page not found (404): ${url}`);
        }
        if (response.status === 403 || response.status === 429) {
          // Rate limited or forbidden - wait longer before retry
          await new Promise(resolve => setTimeout(resolve, this.retryDelay * 2));
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('text/html')) {
        logger.warn(`Non-HTML content at ${url}: ${contentType}`);
        return null;
      }
      
      return await response.text();
      
    } catch (error) {
      if (attempt < this.retryAttempts) {
        logger.warn(`Attempt ${attempt} failed for ${url}: ${error.message}. Retrying...`);
        await new Promise(resolve => setTimeout(resolve, this.retryDelay * attempt));
        return this.fetchWithRetry(url, attempt + 1);
      }
      
      logger.error(`All attempts failed for ${url}: ${error.message}`);
      throw error;
    }
  }

  /**
   * Enhanced grant extraction with smarter patterns
   */
  extractGrantsFromHTML($, source, url) {
    const grants = [];
    const baseUrl = new URL(url).origin;
    const foundItems = new Set();
    
    // Custom selectors for specific sources
    const customSelectors = source.selectors || [];
    
    // Comprehensive list of selectors to try
    const selectors = [
      ...customSelectors,
      // Direct grant links
      'a[href*="grant"]',
      'a[href*="funding"]',
      'a[href*="opportunity"]',
      'a[href*="application"]',
      'a[href*="apply"]',
      'a[href*="rfp"]',
      'a[href*="proposal"]',
      
      // Class-based selectors
      '.grant-item',
      '.grant-listing',
      '.funding-opportunity',
      '.grant-program',
      '.opportunity-card',
      '.funding-area',
      '[class*="grant"]',
      '[class*="funding"]',
      '[class*="opportunity"]',
      
      // Content sections
      'article',
      '.post',
      '.entry',
      '.content-item',
      '.list-item',
      
      // Table rows (some sites list grants in tables)
      'tr:has(td)',
      
      // List items
      'li:has(a)',
      'ul li',
      'ol li',
      
      // Divs with relevant content
      'div:has(h3)',
      'div:has(h4)',
      'section:has(h2)'
    ];
    
    // Try each selector
    for (const selector of selectors) {
      try {
        $(selector).each((i, element) => {
          if (i >= this.maxLinksToCheck || grants.length >= this.maxGrantsPerSource) return false;
          
          const $el = $(element);
          const text = $el.text().trim();
          const html = $el.html();
          
          // Skip if too short or too long
          if (text.length < 10 || text.length > 2000) return;
          
          // Check if it contains grant-related content
          if (!this.isLikelyGrantContent(text)) return;
          
          // Extract title and link
          let title = '';
          let link = '';
          
          // Try to find a link within the element
          const $link = $el.find('a').first();
          if ($link.length > 0) {
            title = $link.text().trim() || text.substring(0, 200);
            link = $link.attr('href');
          } else if ($el.is('a')) {
            title = text.substring(0, 200);
            link = $el.attr('href');
          } else {
            // No direct link, use the page URL
            title = text.substring(0, 200);
            link = url;
          }
          
          if (!title || !link) return;
          
          // Normalize the link
          if (link && !link.startsWith('http')) {
            if (link.startsWith('//')) {
              link = 'https:' + link;
            } else if (link.startsWith('/')) {
              link = baseUrl + link;
            } else {
              link = baseUrl + '/' + link;
            }
          }
          
          // Create unique identifier
          const uniqueId = `${title}-${link}`;
          if (foundItems.has(uniqueId)) return;
          foundItems.add(uniqueId);
          
          // Extract grant details
          const grant = this.createGrantFromElement($el, title, link, source, $);
          if (grant) {
            grants.push(grant);
          }
        });
        
        // If we found grants with this selector, we might not need to try others
        if (grants.length >= 5) break;
        
      } catch (error) {
        logger.warn(`Error with selector ${selector}: ${error.message}`);
      }
    }
    
    // Also look for grant information in meta tags and structured data
    const structuredGrants = this.extractFromStructuredData($);
    grants.push(...structuredGrants.filter(g => !foundItems.has(`${g.title}-${g.link}`)));
    
    return grants.slice(0, this.maxGrantsPerSource);
  }

  /**
   * Check if text is likely grant-related content
   */
  isLikelyGrantContent(text) {
    const lowerText = text.toLowerCase();
    
    // Must contain at least one grant keyword
    const hasGrantKeyword = this.grantKeywords.some(keyword => 
      lowerText.includes(keyword.toLowerCase())
    );
    
    // Must not contain too many negative keywords
    const negativeCount = this.negativeKeywords.filter(keyword => 
      lowerText.includes(keyword.toLowerCase())
    ).length;
    
    // Special patterns that indicate grant content
    const hasSpecialPattern = /\$[\d,]+|deadline|application|eligib|submit|award|fund/i.test(text);
    
    return (hasGrantKeyword || hasSpecialPattern) && negativeCount < 2;
  }

  /**
   * Create grant object from extracted element
   */
  createGrantFromElement($el, title, link, source, $) {
    const text = $el.text();
    const parentText = $el.parent().text() || '';
    const contextText = text + ' ' + parentText;
    
    // Clean and truncate title
    title = title.replace(/\s+/g, ' ').replace(/^[•\-\*\s]+/, '').trim();
    if (title.length > 300) {
      title = title.substring(0, 297) + '...';
    }
    
    // Extract description
    let description = '';
    const $nextP = $el.next('p');
    const $parentP = $el.closest('div').find('p').first();
    
    if ($nextP.length > 0) {
      description = $nextP.text().trim();
    } else if ($parentP.length > 0) {
      description = $parentP.text().trim();
    } else {
      description = contextText.substring(0, 500);
    }
    
    // Extract deadline
    const deadline = this.extractDeadline(contextText);
    
    // Extract amount
    const amount = this.extractAmount(contextText);
    
    // Extract eligibility
    const eligibility = this.extractEligibility(contextText);
    
    // Generate external ID
    const externalId = this.generateExternalId(source.name, title, link);
    
    return {
      title,
      funder: source.name,
      source_name: source.type,
      source_url: source.url,
      link,
      amount_min: amount.min,
      amount_max: amount.max,
      deadline,
      geography: this.extractGeography(source.name, contextText),
      eligibility,
      description: description.substring(0, 1000),
      requirements: this.extractRequirements(contextText),
      external_id: externalId,
      contact_info: this.extractContactInfo(contextText),
      ai_enhanced_data: {
        source_type: source.type,
        confidence: this.calculateConfidence(contextText),
        keywords: this.extractKeywords(contextText),
        scraped_date: new Date().toISOString()
      },
      scrape_metadata: {
        scraped_at: new Date().toISOString(),
        method: 'enhanced_complete_scrape_v2',
        source_url: link,
        selector_type: $el.prop('tagName').toLowerCase()
      }
    };
  }

  /**
   * Extract grants from structured data (JSON-LD, microdata)
   */
  extractFromStructuredData($) {
    const grants = [];
    
    // Look for JSON-LD structured data
    $('script[type="application/ld+json"]').each((i, elem) => {
      try {
        const data = JSON.parse($(elem).html());
        if (data && (data['@type'] === 'Grant' || data['@type'] === 'FundingOpportunity')) {
          grants.push({
            title: data.name || data.title,
            description: data.description,
            link: data.url || '',
            deadline: data.applicationDeadline,
            amount_min: data.amount?.minValue,
            amount_max: data.amount?.maxValue
          });
        }
      } catch (e) {
        // Invalid JSON, skip
      }
    });
    
    return grants;
  }

  /**
   * Extract deadline with enhanced patterns
   */
  extractDeadline(text) {
    const patterns = [
      // Standard date formats
      /deadline[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})/i,
      /due[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})/i,
      /submit by[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})/i,
      /closes?[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})/i,
      /(\d{1,2}\/\d{1,2}\/\d{2,4})/,
      /(\d{4}-\d{2}-\d{2})/,
      
      // Relative dates
      /deadline[:\s]+(.*?)(?:\.|,|;|$)/i,
      /applications? due[:\s]+(.*?)(?:\.|,|;|$)/i,
      
      // Rolling/ongoing
      /(rolling|ongoing|continuous|open)/i
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        const dateStr = match[1];
        
        // Handle rolling/ongoing
        if (/rolling|ongoing|continuous|open/i.test(dateStr)) {
          return 'Rolling';
        }
        
        // Try to parse as date
        const date = new Date(dateStr);
        if (!isNaN(date.getTime())) {
          return date.toISOString().split('T')[0];
        }
        
        return dateStr;
      }
    }
    
    return null;
  }

  /**
   * Extract amount with better pattern matching
   */
  extractAmount(text) {
    const patterns = [
      /\$([0-9,]+)(?:\s*(?:K|k|thousand))?/g,
      /\$([0-9,]+)(?:\s*(?:M|m|million))?/g,
      /up to \$([0-9,]+)/gi,
      /awards? (?:of|up to|ranging from) \$([0-9,]+)/gi,
      /\$([0-9,]+)\s*(?:to|-)\s*\$([0-9,]+)/g
    ];
    
    let minAmount = null;
    let maxAmount = null;
    
    for (const pattern of patterns) {
      const matches = [...text.matchAll(pattern)];
      for (const match of matches) {
        const amount1 = this.parseAmount(match[1]);
        const amount2 = match[2] ? this.parseAmount(match[2]) : null;
        
        if (amount2) {
          // Range found
          minAmount = Math.min(minAmount || amount1, amount1);
          maxAmount = Math.max(maxAmount || amount2, amount2);
        } else {
          // Single amount
          maxAmount = Math.max(maxAmount || amount1, amount1);
        }
      }
    }
    
    return { min: minAmount, max: maxAmount };
  }

  /**
   * Parse amount string to number
   */
  parseAmount(amountStr) {
    if (!amountStr) return null;
    
    // Remove commas and convert
    let amount = parseFloat(amountStr.replace(/,/g, ''));
    
    // Handle K/M suffixes
    if (/k|thousand/i.test(amountStr)) {
      amount *= 1000;
    } else if (/m|million/i.test(amountStr)) {
      amount *= 1000000;
    }
    
    return amount;
  }

  /**
   * Extract geography/location information
   */
  extractGeography(sourceName, text) {
    // Check source name for regional info
    const regionPatterns = {
      'Michigan': ['michigan', 'detroit', 'grand rapids'],
      'Georgia': ['georgia', 'atlanta'],
      'North Carolina': ['north carolina', 'charlotte', 'raleigh'],
      'National': ['national', 'nationwide', 'united states', 'usa'],
      'Global': ['global', 'international', 'worldwide']
    };
    
    for (const [region, patterns] of Object.entries(regionPatterns)) {
      const combinedText = (sourceName + ' ' + text).toLowerCase();
      if (patterns.some(p => combinedText.includes(p))) {
        return region;
      }
    }
    
    return 'Various';
  }

  /**
   * Extract eligibility information
   */
  extractEligibility(text) {
    const patterns = [
      /eligib(?:le|ility)[:\s]+([^.;]+)/i,
      /who (?:can|may) apply[:\s]+([^.;]+)/i,
      /open to[:\s]+([^.;]+)/i,
      /for[:\s]+(nonprofit|501c3|faith-based|religious|churches?)(?:[^.;]{0,100})/i
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        return match[1].trim().substring(0, 500);
      }
    }
    
    // Default based on source type
    if (text.toLowerCase().includes('nonprofit') || text.toLowerCase().includes('501c3')) {
      return '501(c)(3) nonprofits';
    }
    if (text.toLowerCase().includes('faith') || text.toLowerCase().includes('church')) {
      return 'Faith-based organizations';
    }
    
    return 'Various nonprofit organizations';
  }

  /**
   * Extract requirements
   */
  extractRequirements(text) {
    const patterns = [
      /requirements?[:\s]+([^.;]+)/i,
      /must[:\s]+([^.;]+)/i,
      /application materials?[:\s]+([^.;]+)/i,
      /submit[:\s]+([^.;]+)/i
    ];
    
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        return match[1].trim().substring(0, 500);
      }
    }
    
    return null;
  }

  /**
   * Extract contact information
   */
  extractContactInfo(text) {
    const contact = {};
    
    // Email
    const emailMatch = text.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
    if (emailMatch) {
      contact.email = emailMatch[1];
    }
    
    // Phone
    const phoneMatch = text.match(/(\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})/);
    if (phoneMatch) {
      contact.phone = phoneMatch[1];
    }
    
    return contact;
  }

  /**
   * Calculate confidence score for the extracted grant
   */
  calculateConfidence(text) {
    let score = 0;
    const lowerText = text.toLowerCase();
    
    // Check for key indicators
    if (lowerText.includes('grant')) score += 20;
    if (lowerText.includes('funding')) score += 15;
    if (lowerText.includes('application')) score += 15;
    if (lowerText.includes('deadline')) score += 20;
    if (/\$[\d,]+/.test(text)) score += 15;
    if (lowerText.includes('eligib')) score += 10;
    if (lowerText.includes('nonprofit') || lowerText.includes('501c3')) score += 5;
    
    return Math.min(100, score);
  }

  /**
   * Extract relevant keywords
   */
  extractKeywords(text) {
    const keywords = [];
    const lowerText = text.toLowerCase();
    
    const relevantTerms = [
      'technology', 'ai', 'innovation', 'education', 'community', 
      'youth', 'arts', 'culture', 'health', 'environment', 
      'social justice', 'equity', 'capacity building', 'research'
    ];
    
    for (const term of relevantTerms) {
      if (lowerText.includes(term)) {
        keywords.push(term);
      }
    }
    
    return keywords;
  }

  /**
   * Generate unique external ID
   */
  generateExternalId(sourceName, title, link) {
    const hash = crypto
      .createHash('md5')
      .update(`${sourceName}-${title}-${link}`)
      .digest('hex')
      .substring(0, 8);
    
    return `${sourceName.toLowerCase().replace(/\s+/g, '-')}-${hash}`;
  }

  /**
   * Main scraping method for a single source
   */
  async scrapeSource(source) {
    console.log(`\n🔍 Scraping ${source.name} (${source.type})...`);
    
    const opportunities = [];
    const urlsToTry = [source.url, ...(source.fallbackUrls || [])];
    let lastError = null;
    
    for (const url of urlsToTry) {
      if (!url || url.trim() === '') continue;
      
      try {
        // Check cache first
        if (this.resultsCache.has(url)) {
          console.log(`  📦 Using cached results for ${url}`);
          opportunities.push(...this.resultsCache.get(url));
          break;
        }
        
        // Respect rate limiting
        await new Promise(resolve => setTimeout(resolve, this.delayBetweenRequests));
        
        // Fetch the page
        console.log(`  🌐 Fetching ${url}...`);
        const html = await this.fetchWithRetry(url);
        
        if (!html) {
          console.log(`  ⚠️  No HTML content from ${url}`);
          continue;
        }
        
        // Parse the HTML
        const $ = cheerio.load(html);
        
        // Extract grants
        const grants = this.extractGrantsFromHTML($, source, url);
        
        if (grants.length > 0) {
          console.log(`  ✅ Found ${grants.length} opportunities from ${url}`);
          opportunities.push(...grants);
          
          // Cache successful results
          this.resultsCache.set(url, grants);
          
          break; // Success, no need to try fallback URLs
        } else {
          console.log(`  ⚠️  No grants found at ${url}`);
        }
        
      } catch (error) {
        lastError = error;
        console.log(`  ❌ Error with ${url}: ${error.message}`);
      }
    }
    
    // Update statistics
    if (opportunities.length > 0) {
      this.statistics.successfulSources++;
      this.statistics.sourcesWithGrants++;
      this.statistics.totalGrants += opportunities.length;
    } else {
      this.statistics.failedSources++;
      if (lastError) {
        this.statistics.errors.push({
          source: source.name,
          error: lastError.message
        });
      }
    }
    
    return {
      source: source.name,
      type: source.type,
      url: source.url,
      status: opportunities.length > 0 ? 'success' : 'no_grants',
      count: opportunities.length,
      opportunities
    };
  }

  /**
   * Run the complete scraping process
   */
  async runCompleteScrape() {
    console.log('🚀 Starting Enhanced Complete Grant Scraper v2');
    console.log('=' .repeat(60));
    
    const startTime = Date.now();
    const runId = `scrape-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    try {
      // Create scrape run record
      await databasePersistence.createScrapeRun(runId, {
        version: 'enhanced_v2',
        started_at: new Date().toISOString()
      });
      
      // Load foundation sources
      const sources = await this.loadEnhancedFoundationSources();
      this.statistics.totalSources = sources.length;
      
      console.log(`\n📋 Loaded ${sources.length} foundation sources`);
      console.log('=' .repeat(60));
      
      const allResults = [];
      const allGrants = [];
      
      // Process each source
      for (let i = 0; i < sources.length; i++) {
        const source = sources[i];
        console.log(`\n[${i + 1}/${sources.length}] Processing ${source.name}`);
        
        const result = await this.scrapeSource(source);
        allResults.push(result);
        
        if (result.opportunities && result.opportunities.length > 0) {
          allGrants.push(...result.opportunities);
          
          // Store grants in database periodically
          if (allGrants.length >= 50) {
            await databasePersistence.storeScrapedGrants(allGrants, runId);
            allGrants.length = 0; // Clear array
          }
        }
        
        // Update scrape run progress
        await databasePersistence.updateScrapeRun(runId, {
          status: 'running',
          sourcesProcessed: i + 1,
          successfulSources: this.statistics.successfulSources,
          totalOpportunities: this.statistics.totalGrants
        });
      }
      
      // Store any remaining grants
      if (allGrants.length > 0) {
        await databasePersistence.storeScrapedGrants(allGrants, runId);
      }
      
      // Mark scrape as completed
      await databasePersistence.updateScrapeRun(runId, {
        status: 'completed',
        sourcesProcessed: sources.length,
        successfulSources: this.statistics.successfulSources,
        totalOpportunities: this.statistics.totalGrants,
        errors: this.statistics.errors,
        completedAt: new Date()
      });
      
      // Generate summary report
      const duration = Math.round((Date.now() - startTime) / 1000);
      const report = this.generateReport(allResults, duration);
      
      // Save report to file
      await fs.writeFile(
        `./scrape_report_${runId}.json`,
        JSON.stringify(report, null, 2)
      );
      
      console.log('\n' + '=' .repeat(60));
      console.log('📊 SCRAPING COMPLETE - SUMMARY REPORT');
      console.log('=' .repeat(60));
      console.log(report.summary);
      
      return report;
      
    } catch (error) {
      logger.error(`Scraping failed: ${error.message}`);
      
      // Update scrape run as failed
      await databasePersistence.updateScrapeRun(runId, {
        status: 'failed',
        errors: [{ message: error.message, stack: error.stack }],
        completedAt: new Date()
      });
      
      throw error;
    }
  }

  /**
   * Generate detailed report
   */
  generateReport(results, duration) {
    const successfulSources = results.filter(r => r.status === 'success');
    const failedSources = results.filter(r => r.status !== 'success');
    
    // Group by type
    const byType = {};
    for (const result of results) {
      if (!byType[result.type]) {
        byType[result.type] = { sources: 0, grants: 0, successful: 0 };
      }
      byType[result.type].sources++;
      if (result.status === 'success') {
        byType[result.type].successful++;
        byType[result.type].grants += result.count;
      }
    }
    
    const summary = `
📈 Total Sources Processed: ${this.statistics.totalSources}
✅ Successful Sources: ${this.statistics.successfulSources} (${Math.round(this.statistics.successfulSources / this.statistics.totalSources * 100)}%)
❌ Failed Sources: ${this.statistics.failedSources}
🎯 Sources with Grants: ${this.statistics.sourcesWithGrants}
📋 Total Grants Found: ${this.statistics.totalGrants}
⏱️  Duration: ${duration} seconds
🚀 Average Grants per Successful Source: ${Math.round(this.statistics.totalGrants / (this.statistics.sourcesWithGrants || 1))}

BY SOURCE TYPE:
${Object.entries(byType).map(([type, stats]) => 
  `  ${type}: ${stats.successful}/${stats.sources} sources (${stats.grants} grants)`
).join('\n')}

TOP PERFORMING SOURCES:
${successfulSources
  .sort((a, b) => b.count - a.count)
  .slice(0, 10)
  .map((r, i) => `  ${i + 1}. ${r.source}: ${r.count} grants`)
  .join('\n')}

FAILED SOURCES:
${failedSources
  .slice(0, 10)
  .map(r => `  - ${r.source}`)
  .join('\n')}
${failedSources.length > 10 ? `  ... and ${failedSources.length - 10} more` : ''}
`;
    
    return {
      runId: `scrape-${Date.now()}`,
      timestamp: new Date().toISOString(),
      duration,
      statistics: this.statistics,
      summary,
      results,
      successfulSources: successfulSources.map(r => ({
        name: r.source,
        type: r.type,
        count: r.count,
        url: r.url
      })),
      failedSources: failedSources.map(r => ({
        name: r.source,
        type: r.type,
        url: r.url
      }))
    };
  }
}

// Run the scraper if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const scraper = new EnhancedCompleteScraper();
  
  scraper.runCompleteScrape()
    .then(report => {
      console.log('\n✅ Scraping completed successfully!');
      console.log(`📄 Report saved to: scrape_report_${report.runId}.json`);
      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ Scraping failed:', error.message);
      process.exit(1);
    });
}

export default EnhancedCompleteScraper;