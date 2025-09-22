#!/usr/bin/env node
/**
 * Manual scraping test runner - shows live scraping output
 */

import { ScheduledScraper } from './services/scheduledScraper.js';
import { createLogger } from './utils/logger.js';
import fs from 'fs/promises';

const logger = createLogger('ScrapeTest');

async function runManualScrape() {
  console.log('🚀 Starting manual denominational grant scraping...\n');
  
  try {
    const scheduler = new ScheduledScraper();
    
    // Show available sources
    const sources = scheduler.getSources();
    console.log(`📊 Total sources configured: ${sources.length}`);
    console.log('📋 Source types:');
    sources.slice(0, 10).forEach((source, i) => {
      console.log(`  ${i + 1}. ${source.name} (${source.type || 'foundation'})`);
    });
    if (sources.length > 10) {
      console.log(`  ... and ${sources.length - 10} more sources`);
    }
    console.log('\n⏱️  Starting scraping process...\n');
    
    // Initialize and run scraping
    await scheduler.initialize();
    
    console.log('🔄 Running full scraping cycle...\n');
    const startTime = Date.now();
    
    // Run the scraping
    await scheduler.runManualScrape();
    
    const endTime = Date.now();
    const duration = ((endTime - startTime) / 1000).toFixed(2);
    
    console.log(`\n✅ Scraping completed in ${duration} seconds\n`);
    
    // Get and show results
    const results = await scheduler.getLatestResults();
    console.log('📈 SCRAPING RESULTS:');
    console.log(`  📦 Total sources processed: ${results.sourcesProcessed || 0}`);
    console.log(`  ✅ Successful sources: ${results.successfulSources || 0}`);
    console.log(`  🎯 Total opportunities found: ${results.totalOpportunities || 0}`);
    console.log(`  🗓️  Last update: ${results.lastUpdate || 'Unknown'}`);
    console.log(`  💾 Data source: ${results.source || 'cache'}`);
    
    if (results.results && results.results.length > 0) {
      console.log('\n📋 Sample opportunities found:');
      let sampleCount = 0;
      for (const sourceResult of results.results) {
        if (sourceResult.opportunities && sourceResult.opportunities.length > 0) {
          console.log(`\n  📌 ${sourceResult.source} (${sourceResult.opportunities.length} opportunities):`);
          sourceResult.opportunities.slice(0, 3).forEach((opp, i) => {
            console.log(`    ${i + 1}. ${opp.title}`);
            if (opp.organization) console.log(`       Funder: ${opp.organization}`);
            if (opp.deadline) console.log(`       Deadline: ${opp.deadline}`);
            if (opp.amount_min || opp.amount_max) {
              const amountRange = opp.amount_min && opp.amount_max 
                ? `$${opp.amount_min.toLocaleString()} - $${opp.amount_max.toLocaleString()}`
                : opp.amount_min ? `Min: $${opp.amount_min.toLocaleString()}`
                : opp.amount_max ? `Max: $${opp.amount_max.toLocaleString()}`
                : 'Amount: Variable';
              console.log(`       ${amountRange}`);
            }
            sampleCount++;
          });
          if (sampleCount >= 15) break; // Limit sample output
        }
      }
    }
    
    // Show database status
    const status = await scheduler.getStatus();
    console.log('\n💾 DATABASE STATUS:');
    console.log(`  🔄 Last run: ${status.lastRun ? new Date(status.lastRun).toLocaleString() : 'Never'}`);
    console.log(`  📊 Total grants in DB: ${status.runHistory?.length || 0} runs tracked`);
    
    console.log('\n🎉 Scraping test completed successfully!');
    
  } catch (error) {
    console.error('❌ Scraping failed:', error.message);
    console.error(error.stack);
  }
}

// Run the scraping test
runManualScrape().then(() => {
  console.log('\n👋 Scraping test finished. Exiting...');
  process.exit(0);
}).catch((error) => {
  console.error('💥 Fatal error:', error);
  process.exit(1);
});