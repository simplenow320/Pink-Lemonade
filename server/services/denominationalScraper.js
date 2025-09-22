/**
 * Denominational Grant Sources Web Scraper
 * Implements ethical scraping with REACTO guidelines
 */

import puppeteer from 'puppeteer';
import * as cheerio from 'cheerio';
import { v4 as uuidv4 } from 'uuid';
import { createLogger } from '../utils/logger.js';
import { CacheManager } from './cacheManager.js';
import { RateLimiter } from './rateLimiter.js';
import fs from 'fs/promises';
import path from 'path';

const logger = createLogger('DenominationalScraper');

export class DenominationalScraper {
  constructor() {
    this.cache = new CacheManager();
    this.rateLimiter = new RateLimiter({
      requestsPerMinute: 10, // Be respectful to foundation sites
      requestsPerHour: 200
    });
    
    // Foundation sources from the uploaded files
    this.sources = [
      {
        name: 'John Templeton Foundation',
        url: 'https://www.templeton.org/grants',
        additionalUrls: [
          'https://www.templeton.org/grants/apply-for-grant',
          'https://www.templeton.org/grants/grant-calendar'
        ],
        tags: ['interfaith', 'science', 'religion'],
        type: 'foundation'
      },
      {
        name: 'Templeton Religion Trust',
        url: 'https://templetonreligiontrust.org',
        tags: ['religion', 'spiritual'],
        type: 'foundation'
      },
      {
        name: 'Templeton World Charity Foundation',
        url: 'https://www.templetonworldcharity.org',
        tags: ['interfaith', 'global'],
        type: 'foundation'
      },
      {
        name: 'Lilly Endowment',
        url: 'https://lillyendowment.org/grants/',
        additionalUrls: [
          'https://lillyendowment.org/open-initiatives/',
          'https://lillyendowment.org/for-grantseekers/guidelines/'
        ],
        tags: ['christian', 'education', 'community'],
        type: 'foundation'
      },
      {
        name: 'The Duke Endowment',
        url: 'https://dukeendowment.org/rural-church/grants',
        tags: ['christian', 'methodist', 'rural'],
        type: 'foundation'
      },
      {
        name: 'ELCA',
        url: 'https://www.elca.org/our-work/grants',
        additionalUrls: [
          'https://www.elca.org/our-work/relief-and-development/elca-world-hunger/get-involved/domestic-hunger-grants'
        ],
        tags: ['lutheran', 'hunger', 'social-justice'],
        type: 'denomination'
      },
      {
        name: 'Presbyterian Church (USA)',
        url: 'https://www.presbyterianmission.org/ministries/1001/',
        additionalUrls: [
          'https://www.presbyterianmission.org/sites/default/files/Seed-Grant-Application.doc',
          'https://www.presbyterianmission.org/wp-content/uploads/Growth-Grant-Application.doc'
        ],
        tags: ['presbyterian', 'new-churches', 'mission'],
        type: 'denomination'
      },
      {
        name: 'The Episcopal Church',
        url: 'https://www.episcopalchurch.org/grants-and-scholarships/',
        additionalUrls: [
          'https://www.episcopalchurch.org/grants-and-scholarships/new-episcopal-community-grants/'
        ],
        tags: ['episcopal', 'anglican', 'community'],
        type: 'denomination'
      },
      {
        name: 'United Methodist Church',
        url: 'https://umcmission.org/work/humanitarian-relief/migration-refugees/mustard-seed-grants',
        additionalUrls: [
          'https://www.umcdiscipleship.org/about/grants-scholarships'
        ],
        tags: ['methodist', 'mission', 'social-justice'],
        type: 'denomination'
      },
      {
        name: 'United Church of Christ',
        url: 'https://www.ucc.org/giving/ways-we-give/scholarships-grants/program-grants/',
        additionalUrls: [
          'https://www.ucc.org/neighbors-in-need-grant-application-2/'
        ],
        tags: ['ucc', 'progressive', 'social-justice'],
        type: 'denomination'
      },
      {
        name: 'Christian Church (Disciples of Christ)',
        url: 'https://disciples.org/resource/nba-mission-ministry-grants/',
        additionalUrls: [
          'https://disciples.org/resource/disciples-women-endowment-fund/'
        ],
        tags: ['disciples', 'mission', 'ministry'],
        type: 'denomination'
      },
      {
        name: 'Lutheran Church Missouri Synod',
        url: 'https://www.lcms.org/serve/grants/development',
        additionalUrls: [
          'https://www.lcms.org/serve/grants/schiebel'
        ],
        tags: ['lutheran', 'lcms', 'development'],
        type: 'denomination'
      },
      {
        name: 'Evangelical Covenant Church',
        url: 'https://covchurch.org/resource/ministry-development-grants/',
        tags: ['covenant', 'evangelical', 'development'],
        type: 'denomination'
      },
      {
        name: 'Interfaith America',
        url: 'https://www.interfaithamerica.org/grants-leadership-awards/',
        tags: ['interfaith', 'leadership', 'diversity'],
        type: 'organization'
      },
      {
        name: 'Pillars Fund',
        url: 'https://www.pillarsfund.org/opportunities/',
        tags: ['muslim', 'social-change', 'justice'],
        type: 'foundation'
      },
      {
        name: 'Catholic Campaign for Human Development',
        url: 'https://www.usccb.org/committees/catholic-campaign-human-development',
        tags: ['catholic', 'human-development', 'poverty'],
        type: 'denomination'
      },
      {
        name: 'Catholic Extension',
        url: 'https://www.catholicextension.org/grants/',
        tags: ['catholic', 'mission', 'rural'],
        type: 'organization'
      },
      {
        name: 'Conrad N. Hilton Foundation',
        url: 'https://www.hiltonfoundation.org/grants',
        tags: ['catholic', 'humanitarian', 'global'],
        type: 'foundation'
      }
    ];
    
    this.browser = null;
    this.scrapingResults = [];
  }

  /**
   * Initialize browser for scraping
   */
  async initBrowser() {
    if (this.browser) return;
    
    this.browser = await puppeteer.launch({
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu'
      ]
    });
    
    logger.info('Browser initialized for denominational scraping');
  }

  /**
   * Close browser
   */
  async closeBrowser() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      logger.info('Browser closed');
    }
  }

  /**
   * Check robots.txt compliance
   */
  async checkRobotsTxt(url) {
    try {
      const baseUrl = new URL(url).origin;
      const robotsUrl = `${baseUrl}/robots.txt`;
      
      const cachedRobots = this.cache.get(`robots:${baseUrl}`);
      if (cachedRobots !== null) {
        return cachedRobots;
      }
      
      const response = await fetch(robotsUrl);
      if (!response.ok) {
        // No robots.txt found, assume scraping is allowed
        this.cache.set(`robots:${baseUrl}`, true, 3600000); // 1 hour cache
        return true;
      }
      
      const robotsText = await response.text();
      
      // Basic robots.txt parsing - look for User-agent: * and Disallow rules
      const lines = robotsText.split('\n');
      let userAgentSection = false;
      let disallowed = false;
      
      for (const line of lines) {
        const trimmedLine = line.trim().toLowerCase();
        if (trimmedLine.startsWith('user-agent:')) {
          userAgentSection = trimmedLine.includes('*') || trimmedLine.includes('bot');
        } else if (userAgentSection && trimmedLine.startsWith('disallow:')) {
          const disallowPath = trimmedLine.split(':')[1].trim();
          if (disallowPath === '/' || url.includes(disallowPath)) {
            disallowed = true;
            break;
          }
        }
      }
      
      const allowed = !disallowed;
      this.cache.set(`robots:${baseUrl}`, allowed, 3600000); // 1 hour cache
      return allowed;
    } catch (error) {
      logger.warn(`Could not check robots.txt for ${url}: ${error.message}`);
      return true; // Assume allowed if we can't check
    }
  }

  /**
   * Extract grant opportunities from a page
   */
  async extractGrantOpportunities(url, html, sourceName, tags) {
    const $ = cheerio.load(html);
    const opportunities = [];
    
    // Generic selectors for grant information
    const selectors = {
      titles: ['h1', 'h2', 'h3', '.title', '.program-title', '.grant-title', '[class*="title"]'],
      descriptions: ['.description', '.summary', '.content', 'p', '[class*="description"]'],
      amounts: ['[class*="amount"]', '[class*="funding"]', '[class*="award"]', 'td', 'span'],
      deadlines: ['[class*="deadline"]', '[class*="date"]', 'time', '[datetime]'],
      links: ['a[href*="application"]', 'a[href*="apply"]', 'a[href*="grant"]', 'a[href*="program"]']
    };
    
    // Look for structured grant information
    const titleElements = $(selectors.titles.join(', ')).filter((i, el) => {
      const text = $(el).text().toLowerCase();
      return text.includes('grant') || text.includes('program') || text.includes('fund') || 
             text.includes('opportunity') || text.includes('initiative') || text.includes('award');
    });
    
    titleElements.each((index, element) => {
      const $title = $(element);
      const titleText = $title.text().trim();
      
      if (titleText.length > 10 && titleText.length < 200) {
        // Look for associated content
        const $container = $title.closest('div, section, article, li').first();
        
        const description = $container.find(selectors.descriptions.join(', '))
          .first().text().trim().substring(0, 500);
        
        // Look for amount information
        const amountText = $container.find(selectors.amounts.join(', '))
          .text().match(/\$[\d,]+(?:\.\d{2})?|\d+[kKmM]?/)?.[0] || '';
        
        // Look for deadline information
        const deadlineText = $container.find(selectors.deadlines.join(', '))
          .text().match(/\d{1,2}\/\d{1,2}\/\d{2,4}|\w+\s+\d{1,2},?\s+\d{4}|due|deadline/i)?.[0] || '';
        
        // Look for application links
        const applicationLink = $container.find(selectors.links.join(', '))
          .first().attr('href');
        
        opportunities.push({
          id: uuidv4(),
          source: sourceName,
          title: titleText,
          description: description || 'No description available',
          eligibility: this.extractEligibility($container),
          tags: tags,
          geography: this.extractGeography($container),
          funding_amount: amountText,
          deadline: deadlineText,
          status: deadlineText.toLowerCase().includes('closed') ? 'closed' : 'open',
          application_url: applicationLink ? new URL(applicationLink, url).href : url,
          source_url: url,
          contact_info: this.extractContactInfo($container),
          last_updated: new Date().toISOString(),
          unique_key: `${sourceName}-${titleText}-${deadlineText}`.replace(/\W+/g, '-').toLowerCase()
        });
      }
    });
    
    return opportunities;
  }

  /**
   * Extract eligibility information
   */
  extractEligibility($container) {
    const eligibilityKeywords = ['eligible', 'qualification', 'requirement', 'criteria', 'must', 'should'];
    
    const eligibilityText = $container.find('*').contents().filter((i, node) => {
      if (node.nodeType === 3) { // Text node
        const text = node.nodeValue.toLowerCase();
        return eligibilityKeywords.some(keyword => text.includes(keyword));
      }
      return false;
    }).get().map(node => node.nodeValue.trim()).join(' ');
    
    return eligibilityText.substring(0, 300) || 'See source for eligibility requirements';
  }

  /**
   * Extract geography information
   */
  extractGeography($container) {
    const geoKeywords = ['national', 'state', 'local', 'regional', 'international', 'usa', 'us', 'america'];
    const text = $container.text().toLowerCase();
    
    for (const keyword of geoKeywords) {
      if (text.includes(keyword)) {
        return keyword;
      }
    }
    
    return 'See source for geographic restrictions';
  }

  /**
   * Extract contact information
   */
  extractContactInfo($container) {
    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;
    const phoneRegex = /\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/;
    
    const text = $container.text();
    const email = text.match(emailRegex)?.[0];
    const phone = text.match(phoneRegex)?.[0];
    
    return {
      email: email || null,
      phone: phone || null
    };
  }

  /**
   * Scrape a single source
   */
  async scrapeSource(source) {
    const { name, url, additionalUrls = [], tags } = source;
    
    try {
      // Check rate limiting
      await this.rateLimiter.waitForSlot();
      
      // Check robots.txt compliance
      const robotsAllowed = await this.checkRobotsTxt(url);
      if (!robotsAllowed) {
        logger.warn(`Robots.txt disallows scraping for ${name} at ${url}`);
        return {
          source: name,
          status: 'skipped',
          reason: 'robots.txt disallows',
          opportunities: []
        };
      }
      
      await this.initBrowser();
      const page = await this.browser.newPage();
      
      // Set user agent to identify as a responsible scraper
      await page.setUserAgent('GrantFlow-Bot/1.0 (Educational/Nonprofit Grant Discovery; contact@grantflow.org)');
      
      // Set viewport
      await page.setViewport({ width: 1200, height: 800 });
      
      const allOpportunities = [];
      const urlsToScrape = [url, ...additionalUrls];
      
      for (const currentUrl of urlsToScrape) {
        try {
          logger.info(`Scraping ${name}: ${currentUrl}`);
          
          // Navigate to page with timeout
          await page.goto(currentUrl, { 
            waitUntil: 'networkidle2',
            timeout: 30000 
          });
          
          // Wait a bit for dynamic content
          await page.waitForTimeout(2000);
          
          // Get page content
          const html = await page.content();
          
          // Extract opportunities
          const opportunities = await this.extractGrantOpportunities(
            currentUrl, html, name, tags
          );
          
          allOpportunities.push(...opportunities);
          
          // Be respectful with delays between pages
          await page.waitForTimeout(3000);
          
        } catch (error) {
          logger.warn(`Error scraping ${currentUrl}: ${error.message}`);
        }
      }
      
      await page.close();
      
      logger.info(`Scraped ${allOpportunities.length} opportunities from ${name}`);
      
      return {
        source: name,
        status: 'success',
        opportunities: allOpportunities,
        scraped_at: new Date().toISOString()
      };
      
    } catch (error) {
      logger.error(`Error scraping ${name}: ${error.message}`);
      return {
        source: name,
        status: 'error',
        reason: error.message,
        opportunities: []
      };
    }
  }

  /**
   * Run scraping for all sources
   */
  async runScrapingCycle() {
    logger.info('Starting denominational grants scraping cycle');
    
    this.scrapingResults = [];
    let totalOpportunities = 0;
    let successfulSources = 0;
    
    try {
      for (const source of this.sources) {
        const result = await this.scrapeSource(source);
        this.scrapingResults.push(result);
        
        if (result.status === 'success') {
          successfulSources++;
          totalOpportunities += result.opportunities.length;
        }
        
        // Delay between sources to be respectful
        await new Promise(resolve => setTimeout(resolve, 10000)); // 10 second delay
      }
      
      // Save results to files
      await this.saveResults();
      
      logger.info(`Scraping cycle complete: ${successfulSources}/${this.sources.length} sources successful, ${totalOpportunities} total opportunities`);
      
      return {
        success: true,
        sourcesProcessed: this.sources.length,
        successfulSources,
        totalOpportunities,
        results: this.scrapingResults
      };
      
    } catch (error) {
      logger.error(`Scraping cycle error: ${error.message}`);
      throw error;
    } finally {
      await this.closeBrowser();
    }
  }

  /**
   * Save scraping results
   */
  async saveResults() {
    try {
      // Ensure data directory exists
      const dataDir = path.join(process.cwd(), 'data', 'scraped');
      await fs.mkdir(dataDir, { recursive: true });
      
      const timestamp = new Date().toISOString().split('T')[0];
      
      // Save detailed results
      const detailedResults = {
        scraping_run: {
          timestamp: new Date().toISOString(),
          total_sources: this.sources.length,
          successful_sources: this.scrapingResults.filter(r => r.status === 'success').length,
          total_opportunities: this.scrapingResults.reduce((sum, r) => sum + r.opportunities.length, 0)
        },
        results: this.scrapingResults
      };
      
      await fs.writeFile(
        path.join(dataDir, `denominational_grants_${timestamp}.json`),
        JSON.stringify(detailedResults, null, 2)
      );
      
      // Save CSV summary
      const opportunities = this.scrapingResults.flatMap(r => r.opportunities);
      if (opportunities.length > 0) {
        const csvHeader = 'source,title,description,funding_amount,deadline,status,application_url,tags\n';
        const csvRows = opportunities.map(opp => 
          [
            opp.source,
            `"${opp.title.replace(/"/g, '""')}"`,
            `"${opp.description.substring(0, 100).replace(/"/g, '""')}"`,
            opp.funding_amount || '',
            opp.deadline || '',
            opp.status || 'open',
            opp.application_url || '',
            `"${opp.tags.join(', ')}"`
          ].join(',')
        ).join('\n');
        
        await fs.writeFile(
          path.join(dataDir, `denominational_grants_${timestamp}.csv`),
          csvHeader + csvRows
        );
      }
      
      logger.info(`Scraping results saved to data/scraped/denominational_grants_${timestamp}.*`);
      
    } catch (error) {
      logger.error(`Error saving scraping results: ${error.message}`);
      throw error;
    }
  }

  /**
   * Get latest scraping results
   */
  getLatestResults() {
    return this.scrapingResults;
  }

  /**
   * Get source configuration
   */
  getSources() {
    return this.sources;
  }
}

export default DenominationalScraper;