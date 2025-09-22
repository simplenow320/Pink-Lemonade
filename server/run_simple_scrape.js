#!/usr/bin/env node
/**
 * Simple HTTP-based scraper to get real grant data without Puppeteer
 */

import fetch from 'node-fetch';
import * as cheerio from 'cheerio';
import { databasePersistence } from './services/databasePersistence.js';
import { createLogger } from './utils/logger.js';

const logger = createLogger('SimpleScraper');

async function scrapeRealGrants() {
  console.log('🚀 Starting simple HTTP scraping for real grant data...\n');
  
  const runId = `simple-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  try {
    // Initialize database
    await databasePersistence.initializeTables();
    
    // Create run record
    await databasePersistence.createScrapeRun(runId, {
      type: 'simple_http',
      triggeredAt: new Date().toISOString()
    });
    
    console.log(`📊 Created scrape run: ${runId}\n`);
    
    // Simple sources that don't require complex JS rendering
    const simpleSources = [
      {
        name: 'Federal Register - NOFO Opportunities',
        url: 'https://www.federalregister.gov/documents/search?conditions[agencies][]=health-and-human-services-department&conditions[term]=grant+opportunity',
        type: 'government'
      },
      {
        name: 'NSF Grant Opportunities',
        url: 'https://www.nsf.gov/funding/opportunities.jsp',
        type: 'government'
      },
      {
        name: 'HHS Grants',
        url: 'https://www.hhs.gov/grants/index.html',
        type: 'government'
      }
    ];
    
    let totalOpportunities = 0;
    const results = [];
    
    for (const source of simpleSources) {
      console.log(`🔍 Scraping ${source.name}...`);
      
      try {
        const response = await fetch(source.url, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (compatible; GrantFlow/1.0; +https://grantflow.org/bot)'
          },
          timeout: 15000
        });
        
        if (!response.ok) {
          console.log(`⚠️  ${source.name}: HTTP ${response.status}`);
          continue;
        }
        
        const html = await response.text();
        const $ = cheerio.load(html);
        
        let opportunities = [];
        
        // Parse different grant sites
        if (source.name.includes('Federal Register')) {
          // Federal Register parsing
          $('.document-row').each((i, el) => {
            if (i >= 10) return false; // Limit to 10 per source
            
            const title = $(el).find('.title a').text().trim();
            const link = $(el).find('.title a').attr('href');
            const date = $(el).find('.date').text().trim();
            const description = $(el).find('.summary').text().trim();
            
            if (title && title.toLowerCase().includes('grant')) {
              opportunities.push({
                title: title.substring(0, 500),
                link: link ? `https://www.federalregister.gov${link}` : source.url,
                deadline: date || null,
                description: description.substring(0, 1000),
                funder: 'Federal Government',
                geography: 'United States',
                source_name: source.name,
                source_url: source.url
              });
            }
          });
        } 
        else if (source.name.includes('NSF')) {
          // NSF parsing
          $('table tr').each((i, el) => {
            if (i >= 10 || i === 0) return; // Skip header, limit to 10
            
            const title = $(el).find('td').first().text().trim();
            const link = $(el).find('a').attr('href');
            const deadline = $(el).find('td').eq(1).text().trim();
            
            if (title && title.length > 10) {
              opportunities.push({
                title: title.substring(0, 500),
                link: link ? (link.startsWith('http') ? link : `https://www.nsf.gov${link}`) : source.url,
                deadline: deadline || null,
                description: `NSF funding opportunity: ${title}`,
                funder: 'National Science Foundation',
                geography: 'United States',
                source_name: source.name,
                source_url: source.url
              });
            }
          });
        }
        else {
          // Generic parsing for other sites
          $('a').each((i, el) => {
            if (i >= 15) return false; // Limit to 15 per source
            
            const title = $(el).text().trim();
            const link = $(el).attr('href');
            
            if (title && title.length > 10 && 
                (title.toLowerCase().includes('grant') || 
                 title.toLowerCase().includes('funding') ||
                 title.toLowerCase().includes('opportunity'))) {
              
              opportunities.push({
                title: title.substring(0, 500),
                link: link ? (link.startsWith('http') ? link : `${new URL(source.url).origin}${link}`) : source.url,
                deadline: null,
                description: `Funding opportunity from ${source.name}`,
                funder: source.name.includes('HHS') ? 'Health and Human Services' : 'Government Agency',
                geography: 'United States',
                source_name: source.name,
                source_url: source.url
              });
            }
          });
        }
        
        // Remove duplicates and save to database
        const uniqueOpportunities = opportunities.filter((opp, index, self) => 
          index === self.findIndex(o => o.title === opp.title)
        );
        
        console.log(`  📈 Found ${uniqueOpportunities.length} opportunities`);
        
        // Save each opportunity to database
        for (const opportunity of uniqueOpportunities) {
          try {
            await databasePersistence.saveGrant({
              external_id: `simple-${source.name.replace(/\s+/g, '-').toLowerCase()}-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
              title: opportunity.title,
              funder: opportunity.funder,
              source_name: opportunity.source_name,
              source_url: opportunity.source_url,
              link: opportunity.link,
              amount_min: null,
              amount_max: null,
              deadline: opportunity.deadline,
              geography: opportunity.geography,
              eligibility: 'Varies by program',
              description: opportunity.description,
              requirements: 'See grant details',
              contact_info: {},
              ai_enhanced_data: {},
              scrape_metadata: {
                scraped_at: new Date().toISOString(),
                method: 'simple_http',
                source_type: source.type
              }
            }, runId);
            
            totalOpportunities++;
          } catch (saveError) {
            console.log(`  ⚠️  Error saving opportunity: ${saveError.message}`);
          }
        }
        
        results.push({
          source: source.name,
          status: 'success',
          opportunities: uniqueOpportunities.length
        });
        
        // Wait 3 seconds between sources
        await new Promise(resolve => setTimeout(resolve, 3000));
        
      } catch (sourceError) {
        console.log(`❌ Error scraping ${source.name}: ${sourceError.message}`);
        results.push({
          source: source.name,
          status: 'error',
          error: sourceError.message,
          opportunities: 0
        });
      }
    }
    
    // Update run status
    await databasePersistence.updateScrapeRun(runId, {
      status: 'completed',
      sources_processed: simpleSources.length,
      successful_sources: results.filter(r => r.status === 'success').length,
      total_opportunities: totalOpportunities,
      completed_at: new Date().toISOString()
    });
    
    console.log('\n🎉 SIMPLE SCRAPING COMPLETED!');
    console.log('📊 FINAL RESULTS:');
    console.log(`  🎯 Total opportunities saved: ${totalOpportunities}`);
    console.log(`  ✅ Successful sources: ${results.filter(r => r.status === 'success').length}/${simpleSources.length}`);
    console.log(`  💾 Run ID: ${runId}`);
    
    // Show sample saved data
    if (totalOpportunities > 0) {
      console.log('\n📋 Sample saved opportunities:');
      results.forEach(result => {
        if (result.status === 'success' && result.opportunities > 0) {
          console.log(`  📌 ${result.source}: ${result.opportunities} grants`);
        }
      });
    }
    
    return { success: true, runId, totalOpportunities, results };
    
  } catch (error) {
    console.error('💥 Scraping failed:', error.message);
    
    // Mark run as failed
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

// Run the scraping
scrapeRealGrants().then((result) => {
  if (result.success) {
    console.log('\n✅ Real grant data successfully saved to database!');
  } else {
    console.log('\n❌ Scraping failed:', result.error);
  }
  process.exit(result.success ? 0 : 1);
}).catch((error) => {
  console.error('💥 Fatal error:', error);
  process.exit(1);
});