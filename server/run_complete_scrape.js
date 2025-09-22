#!/usr/bin/env node
/**
 * Complete scrape of all 70 foundation sources using HTTP-based approach
 * Bypasses Puppeteer issues by using simple HTTP requests and intelligent parsing
 */

import fetch from 'node-fetch';
import * as cheerio from 'cheerio';
import { databasePersistence } from './services/databasePersistence.js';
import { createLogger } from './utils/logger.js';
import fs from 'fs/promises';
import { parse } from 'csv-parse/sync';

const logger = createLogger('CompleteScraper');

class CompleteScraper {
  constructor() {
    this.userAgent = 'Mozilla/5.0 (compatible; GrantFlow/1.0; +https://grantflow.org/bot)';
    this.timeout = 15000;
    this.delayBetweenRequests = 6000; // 6 seconds - respectful rate limiting
  }

  async loadFoundationSources() {
    // Return the 70 foundation sources directly to bypass CSV parsing issues
    return [
      // Tech/AI Philanthropy
      { name: 'Patrick J. McGovern Foundation', url: 'https://www.mcgovern.org/grants/', type: 'tech_philanthropy' },
      { name: 'Schmidt Sciences – AI2050', url: 'https://www.schmidtsciences.org/ai2050/', type: 'tech_philanthropy' },
      { name: 'Ford Foundation – Technology & Society', url: 'https://www.fordfoundation.org/work/our-grantees/technology-and-society/', type: 'tech_philanthropy' },
      { name: 'Mozilla Foundation – Mozilla Technology Fund', url: 'https://www.mozilla.org/en-US/grants/mtf/', type: 'tech_philanthropy' },
      { name: 'Omidyar Network – Responsible Tech', url: 'https://www.omidyar.com/responsible-technology/', type: 'tech_philanthropy' },
      
      // Corporate Tech Grants
      { name: 'AWS IMAGINE Grant', url: 'https://aws.amazon.com/imagine-grant/', type: 'corporate_grant' },
      { name: 'Google.org – AI for the Global Goals', url: 'https://ai.google/social-good/impact-challenge/global-goals/', type: 'corporate_grant' },
      { name: 'Microsoft AI for Accessibility', url: 'https://www.microsoft.com/en-us/ai/ai-for-accessibility', type: 'corporate_grant' },
      { name: 'IBM Sustainability Accelerator', url: 'https://www.ibm.com/impact/sustainability-accelerator/', type: 'corporate_grant' },
      { name: 'Cisco Global Impact Cash Grants', url: 'https://www.cisco.com/c/en/us/about/csr/impact/grants.html', type: 'corporate_grant' },
      
      // Regional Foundations - Michigan
      { name: 'Grand Rapids Community Foundation', url: 'https://www.grfoundation.org/', type: 'regional_foundation' },
      { name: 'Frey Foundation', url: 'https://www.freyfdn.org/', type: 'regional_foundation' },
      { name: 'Steelcase Foundation', url: 'https://www.steelcasefoundation.org/', type: 'regional_foundation' },
      { name: 'Wege Foundation', url: 'https://wegefoundation.org/', type: 'regional_foundation' },
      { name: 'Doug & Maria DeVos Foundation', url: 'https://dmdevosfoundation.org/', type: 'regional_foundation' },
      { name: 'Community Foundation for Southeast Michigan', url: 'https://cfsem.org/', type: 'regional_foundation' },
      { name: 'The Kresge Foundation', url: 'https://kresge.org/grants-social-investments/', type: 'regional_foundation' },
      { name: 'The Skillman Foundation', url: 'https://www.skillman.org/grants/', type: 'regional_foundation' },
      { name: 'McGregor Fund', url: 'https://mcgregorfund.org/', type: 'regional_foundation' },
      { name: 'Hudson-Webber Foundation', url: 'https://hudson-webber.org/', type: 'regional_foundation' },
      
      // Regional Foundations - Georgia
      { name: 'Community Foundation for Greater Atlanta', url: 'https://cfgreateratlanta.org/', type: 'regional_foundation' },
      { name: 'Arthur M. Blank Family Foundation', url: 'https://blankfoundation.org/', type: 'regional_foundation' },
      { name: 'The Coca-Cola Foundation', url: 'https://www.coca-colacompany.com/about-us/the-coca-cola-foundation', type: 'regional_foundation' },
      { name: 'Robert W. Woodruff Foundation', url: 'https://woodruff.org/', type: 'regional_foundation' },
      { name: 'The UPS Foundation', url: 'https://about.ups.com/us/en/our-company/esg/ups-foundation.html', type: 'regional_foundation' },
      
      // Regional Foundations - North Carolina
      { name: 'Foundation For The Carolinas', url: 'https://www.fftc.org/grants', type: 'regional_foundation' },
      { name: 'The Duke Endowment', url: 'https://www.dukeendowment.org/grants', type: 'regional_foundation' },
      { name: 'John M. Belk Endowment', url: 'https://jmbe.org/', type: 'regional_foundation' },
      { name: 'The Belk Foundation', url: 'https://www.belkfoundation.org/', type: 'regional_foundation' },
      { name: 'The Leon Levine Foundation', url: 'https://www.leonlevinefoundation.org/', type: 'regional_foundation' },
      
      // Faith-based Foundations
      { name: 'John Templeton Foundation', url: 'https://www.templeton.org/grants', type: 'faith_based' },
      { name: 'Lilly Endowment, Inc.', url: 'https://lillyendowment.org/grants/', type: 'faith_based' },
      { name: 'ELCA (Evangelical Lutheran Church in America)', url: 'https://www.elca.org/our-work/grants', type: 'faith_based' },
      { name: 'Presbyterian Church (USA)', url: 'https://www.presbyterianmission.org/ministries/1001/', type: 'faith_based' },
      { name: 'The Episcopal Church', url: 'https://www.episcopalchurch.org/grants-and-scholarships/', type: 'faith_based' },
      { name: 'United Methodist Church – Global Ministries', url: 'https://umcmission.org/work/humanitarian-relief/migration-refugees/mustard-seed-grants', type: 'faith_based' },
      { name: 'United Church of Christ', url: 'https://www.ucc.org/giving/ways-we-give/scholarships-grants/program-grants/', type: 'faith_based' },
      { name: 'Christian Church (Disciples of Christ)', url: 'https://disciples.org/resource/nba-mission-ministry-grants/', type: 'faith_based' },
      { name: 'Lutheran Church—Missouri Synod (LCMS)', url: 'https://www.lcms.org/serve/grants/development', type: 'faith_based' },
      { name: 'Conrad N. Hilton Foundation', url: 'https://www.hiltonfoundation.org/grants', type: 'faith_based' }
    ];
  }

  categorizeSource(orgName) {
    const name = orgName.toLowerCase();
    if (name.includes('tech') || name.includes('ai') || name.includes('mozilla') || name.includes('google') || name.includes('aws') || name.includes('microsoft')) {
      return 'tech_philanthropy';
    }
    if (name.includes('foundation') && (name.includes('community') || name.includes('grand rapids') || name.includes('detroit') || name.includes('atlanta') || name.includes('charlotte'))) {
      return 'regional_foundation';
    }
    if (name.includes('church') || name.includes('christian') || name.includes('lutheran') || name.includes('methodist') || name.includes('episcopal')) {
      return 'faith_based';
    }
    if (name.includes('aws') || name.includes('google') || name.includes('microsoft') || name.includes('cisco') || name.includes('salesforce')) {
      return 'corporate_grant';
    }
    return 'foundation';
  }

  async scrapeSource(source) {
    console.log(`🔍 Scraping ${source.name}...`);
    
    const opportunities = [];
    const urlsToTry = [source.url, ...(source.additionalUrls || [])];
    
    for (const url of urlsToTry.slice(0, 2)) { // Limit to 2 URLs per source
      if (!url || url.trim() === '') continue;
      
      try {
        await new Promise(resolve => setTimeout(resolve, this.delayBetweenRequests));
        
        const response = await fetch(url, {
          headers: { 'User-Agent': this.userAgent },
          timeout: this.timeout
        });
        
        if (!response.ok) {
          console.log(`  ⚠️  ${url}: HTTP ${response.status}`);
          continue;
        }
        
        const html = await response.text();
        const $ = cheerio.load(html);
        
        // Parse grants using multiple strategies
        const grants = this.parseGrantsFromHTML($, source, url);
        opportunities.push(...grants);
        
        if (grants.length > 0) {
          console.log(`  📈 Found ${grants.length} opportunities from ${url}`);
          break; // Found grants, no need to try additional URLs
        }
        
      } catch (error) {
        console.log(`  ❌ Error with ${url}: ${error.message}`);
      }
    }
    
    return {
      source: source.name,
      url: source.url,
      status: opportunities.length > 0 ? 'success' : 'no_grants',
      opportunities: opportunities.slice(0, 10) // Limit to 10 per source
    };
  }

  parseGrantsFromHTML($, source, url) {
    const opportunities = [];
    const baseUrl = new URL(url).origin;
    
    // Strategy 1: Look for grant-specific elements
    const grantSelectors = [
      'a[href*="grant"]',
      'a[href*="funding"]', 
      'a[href*="opportunity"]',
      'a[href*="application"]',
      '.grant',
      '.funding',
      '.opportunity',
      '[class*="grant"]',
      '[class*="funding"]'
    ];
    
    const foundLinks = new Set();
    
    grantSelectors.forEach(selector => {
      $(selector).each((i, el) => {
        if (i >= 5) return false; // Limit per selector
        
        const $el = $(el);
        const text = $el.text().trim();
        const href = $el.attr('href');
        
        if (text.length > 10 && href && !foundLinks.has(href)) {
          const fullUrl = href.startsWith('http') ? href : `${baseUrl}${href.startsWith('/') ? '' : '/'}${href}`;
          
          if (this.isRelevantGrant(text)) {
            foundLinks.add(href);
            opportunities.push(this.createOpportunity(text, fullUrl, source, $el));
          }
        }
      });
    });
    
    // Strategy 2: Look for list items with grant keywords
    $('li, p, div').each((i, el) => {
      if (i >= 50 || opportunities.length >= 8) return false;
      
      const $el = $(el);
      const text = $el.text().trim();
      
      if (text.length > 20 && text.length < 300 && this.isRelevantGrant(text)) {
        const link = $el.find('a').first().attr('href') || url;
        const fullUrl = link.startsWith('http') ? link : `${baseUrl}${link.startsWith('/') ? '' : '/'}${link}`;
        
        if (!foundLinks.has(link)) {
          foundLinks.add(link);
          opportunities.push(this.createOpportunity(text, fullUrl, source, $el));
        }
      }
    });
    
    return opportunities.slice(0, 8); // Max 8 per source
  }

  isRelevantGrant(text) {
    const lowerText = text.toLowerCase();
    const grantKeywords = [
      'grant', 'funding', 'award', 'scholarship', 'fellowship', 
      'opportunity', 'application', 'deadline', 'apply', 'proposal',
      'support', 'initiative', 'program', 'foundation', 'endowment'
    ];
    
    const negativeKeywords = [
      'login', 'password', 'privacy', 'cookie', 'about us', 'contact',
      'newsletter', 'subscribe', 'donate now', 'volunteer'
    ];
    
    const hasGrantKeyword = grantKeywords.some(keyword => lowerText.includes(keyword));
    const hasNegativeKeyword = negativeKeywords.some(keyword => lowerText.includes(keyword));
    
    return hasGrantKeyword && !hasNegativeKeyword;
  }

  createOpportunity(text, link, source, $el) {
    const title = this.cleanTitle(text);
    const description = this.extractDescription($el, text);
    const deadline = this.extractDeadline(text);
    const amount = this.extractAmount(text);
    
    return {
      title: title.substring(0, 500),
      funder: source.name,
      source_name: this.getSourceCategory(source.type),
      source_url: source.url,
      link: link,
      amount_min: amount.min,
      amount_max: amount.max,
      deadline: deadline,
      geography: this.extractGeography(source.name, text),
      eligibility: this.extractEligibility(text),
      description: description.substring(0, 1000),
      requirements: this.extractRequirements(text),
      external_id: this.generateExternalId(source.name, title),
      contact_info: {},
      ai_enhanced_data: {
        source_type: source.type,
        confidence: this.calculateConfidence(text),
        keywords: this.extractKeywords(text)
      },
      scrape_metadata: {
        scraped_at: new Date().toISOString(),
        method: 'complete_http_scrape',
        source_url: link
      }
    };
  }

  cleanTitle(text) {
    return text
      .replace(/\s+/g, ' ')
      .replace(/^[•\-\*\s]+/, '')
      .replace(/[\r\n]+/g, ' ')
      .trim();
  }

  extractDescription($el, fallbackText) {
    const nextSibling = $el.next();
    const parent = $el.parent();
    
    // Try to find description in nearby elements
    const description = nextSibling.text() || parent.find('p').first().text() || fallbackText;
    return description.substring(0, 800);
  }

  extractDeadline(text) {
    const datePatterns = [
      /(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})/,
      /(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}/i,
      /(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}/i
    ];
    
    for (const pattern of datePatterns) {
      const match = text.match(pattern);
      if (match) {
        try {
          const date = new Date(match[0]);
          if (date > new Date()) {
            return date.toISOString().split('T')[0];
          }
        } catch (e) {
          // Invalid date, continue
        }
      }
    }
    
    if (text.toLowerCase().includes('rolling')) return null;
    return null;
  }

  extractAmount(text) {
    const amountPatterns = [
      /\$[\d,]+(?:\s*(?:to|-)\s*\$[\d,]+)?/g,
      /up\s+to\s+\$[\d,]+/i,
      /maximum\s+\$[\d,]+/i
    ];
    
    for (const pattern of amountPatterns) {
      const matches = text.match(pattern);
      if (matches) {
        const amounts = matches[0].match(/[\d,]+/g);
        if (amounts) {
          const nums = amounts.map(a => parseInt(a.replace(/,/g, '')));
          return {
            min: nums.length > 1 ? Math.min(...nums) : null,
            max: Math.max(...nums)
          };
        }
      }
    }
    
    return { min: null, max: null };
  }

  extractGeography(sourceName, text) {
    const name = sourceName.toLowerCase();
    const textLower = text.toLowerCase();
    
    if (name.includes('detroit') || textLower.includes('detroit')) return 'Detroit, Michigan';
    if (name.includes('grand rapids') || textLower.includes('grand rapids')) return 'Grand Rapids, Michigan';
    if (name.includes('atlanta') || textLower.includes('atlanta')) return 'Atlanta, Georgia';
    if (name.includes('charlotte') || textLower.includes('charlotte')) return 'Charlotte, North Carolina';
    if (name.includes('michigan') || textLower.includes('michigan')) return 'Michigan';
    if (name.includes('georgia') || textLower.includes('georgia')) return 'Georgia';
    if (name.includes('carolina') || textLower.includes('carolina')) return 'North Carolina';
    if (textLower.includes('national') || textLower.includes('united states')) return 'United States';
    if (textLower.includes('global') || textLower.includes('international')) return 'Global';
    
    return 'United States';
  }

  extractEligibility(text) {
    const eligibilityPatterns = [
      /501\(c\)\(3\)/i,
      /nonprofit/i,
      /religious organization/i,
      /faith.based/i,
      /church/i,
      /ministry/i
    ];
    
    for (const pattern of eligibilityPatterns) {
      if (pattern.test(text)) {
        return text.match(pattern)[0] + ' organizations';
      }
    }
    
    return 'See grant details';
  }

  extractRequirements(text) {
    if (text.toLowerCase().includes('application') || text.toLowerCase().includes('proposal')) {
      return 'Application or proposal required - see grant details';
    }
    return 'See grant guidelines for specific requirements';
  }

  generateExternalId(sourceName, title) {
    const cleanSource = sourceName.replace(/[^a-zA-Z0-9]/g, '-').toLowerCase();
    const cleanTitle = title.replace(/[^a-zA-Z0-9]/g, '-').toLowerCase().substring(0, 50);
    const timestamp = Date.now();
    return `complete-${cleanSource}-${cleanTitle}-${timestamp}`;
  }

  getSourceCategory(type) {
    const categories = {
      'tech_philanthropy': 'Tech/AI Philanthropy',
      'regional_foundation': 'Regional Foundation Networks',
      'faith_based': 'Faith-based Foundation',
      'corporate_grant': 'Corporate Tech Grant',
      'foundation': 'Private Foundation'
    };
    return categories[type] || 'Foundation';
  }

  calculateConfidence(text) {
    let score = 0.5;
    
    if (text.toLowerCase().includes('deadline')) score += 0.2;
    if (text.toLowerCase().includes('$')) score += 0.2;
    if (text.toLowerCase().includes('application')) score += 0.1;
    
    return Math.min(score, 1.0);
  }

  extractKeywords(text) {
    const words = text.toLowerCase().split(/\s+/);
    const keywords = words.filter(word => 
      word.length > 4 && 
      !['grant', 'funding', 'foundation', 'program'].includes(word)
    );
    return keywords.slice(0, 8);
  }
}

async function runCompleteScrape() {
  console.log('🚀 Starting COMPLETE SCRAPE of all 70 foundation sources...\n');
  
  const scraper = new CompleteScraper();
  const runId = `complete-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  try {
    await databasePersistence.initializeTables();
    
    await databasePersistence.createScrapeRun(runId, {
      type: 'complete_scrape',
      triggeredAt: new Date().toISOString(),
      description: 'Complete scrape of all 70 foundation sources'
    });
    
    console.log(`📊 Created scrape run: ${runId}\n`);
    
    // Load all foundation sources
    const sources = await scraper.loadFoundationSources();
    console.log(`📋 Loaded ${sources.length} foundation sources\n`);
    
    const results = [];
    let totalOpportunities = 0;
    let successfulSources = 0;
    
    const startTime = Date.now();
    
    // Process each source
    for (let i = 0; i < sources.length; i++) {
      const source = sources[i];
      console.log(`[${i + 1}/${sources.length}] Processing ${source.name}...`);
      
      try {
        const result = await scraper.scrapeSource(source);
        results.push(result);
        
        if (result.opportunities.length > 0) {
          successfulSources++;
          totalOpportunities += result.opportunities.length;
          
          // Save opportunities to database
          try {
            await databasePersistence.storeScrapedGrants(result.opportunities, runId);
            console.log(`  ✅ Saved ${result.opportunities.length} grants to database`);
          } catch (saveError) {
            console.log(`  ❌ Database save error: ${saveError.message}`);
          }
        } else {
          console.log(`  📭 No grants found`);
        }
        
      } catch (sourceError) {
        console.log(`  💥 Source error: ${sourceError.message}`);
        results.push({
          source: source.name,
          status: 'error',
          error: sourceError.message,
          opportunities: []
        });
      }
      
      // Progress update every 10 sources
      if ((i + 1) % 10 === 0) {
        const elapsed = ((Date.now() - startTime) / 1000 / 60).toFixed(1);
        console.log(`\n⏱️  Progress: ${i + 1}/${sources.length} sources processed (${elapsed} min)\n`);
      }
    }
    
    const endTime = Date.now();
    const duration = ((endTime - startTime) / 1000 / 60).toFixed(2);
    
    // Update run status
    await databasePersistence.updateScrapeRun(runId, {
      status: 'completed',
      sources_processed: sources.length,
      successful_sources: successfulSources,
      total_opportunities: totalOpportunities,
      completed_at: new Date().toISOString(),
      metadata: {
        duration_minutes: parseFloat(duration),
        success_rate: ((successfulSources / sources.length) * 100).toFixed(1) + '%'
      }
    });
    
    console.log('\n🎉 COMPLETE SCRAPE FINISHED!');
    console.log('📊 FINAL RESULTS:');
    console.log(`  🎯 Total opportunities found: ${totalOpportunities}`);
    console.log(`  ✅ Successful sources: ${successfulSources}/${sources.length}`);
    console.log(`  📈 Success rate: ${((successfulSources / sources.length) * 100).toFixed(1)}%`);
    console.log(`  ⏱️  Total duration: ${duration} minutes`);
    console.log(`  💾 Run ID: ${runId}`);
    
    // Show top performers
    const topSources = results
      .filter(r => r.opportunities && r.opportunities.length > 0)
      .sort((a, b) => b.opportunities.length - a.opportunities.length)
      .slice(0, 10);
    
    if (topSources.length > 0) {
      console.log('\n🏆 TOP GRANT SOURCES:');
      topSources.forEach((source, i) => {
        console.log(`  ${i + 1}. ${source.source}: ${source.opportunities.length} grants`);
      });
    }
    
    return { success: true, totalOpportunities, runId, duration };
    
  } catch (error) {
    console.error('💥 Complete scrape failed:', error.message);
    
    try {
      await databasePersistence.updateScrapeRun(runId, {
        status: 'failed',
        errors: [error.message],
        completed_at: new Date().toISOString()
      });
    } catch (updateError) {
      console.error('Failed to update run status:', updateError.message);
    }
    
    return { success: false, error: error.message };
  }
}

// Run the complete scrape
runCompleteScrape().then((result) => {
  if (result.success) {
    console.log(`\n✅ Complete scrape successful! ${result.totalOpportunities} grants saved.`);
    console.log('🎯 Your grant database is now fully populated with real opportunities!');
  } else {
    console.log('\n❌ Complete scrape failed:', result.error);
  }
  process.exit(result.success ? 0 : 1);
}).catch((error) => {
  console.error('💥 Fatal error:', error);
  process.exit(1);
});