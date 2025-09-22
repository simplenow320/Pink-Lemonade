#!/usr/bin/env node
/**
 * Test the Enhanced Complete Grant Scraper with selected sources
 */

import EnhancedCompleteScraper from './run_complete_scrape_v2.js';
import { createLogger } from './utils/logger.js';

const logger = createLogger('ScraperTest');

async function testSelectedSources() {
  console.log('🧪 Testing Enhanced Scraper with Selected Sources');
  console.log('=' .repeat(60));
  
  const scraper = new EnhancedCompleteScraper();
  
  // Test with a small selection of diverse sources
  const testSources = [
    { 
      name: 'John Templeton Foundation', 
      url: 'https://www.templeton.org/grants',
      fallbackUrls: ['https://www.templeton.org/funding-areas'],
      type: 'faith_based',
      selectors: ['.funding-area', '.grant-opportunity']
    },
    { 
      name: 'Google.org', 
      url: 'https://www.google.org/our-work/',
      fallbackUrls: ['https://www.google.org/'],
      type: 'corporate_grant'
    },
    { 
      name: 'Knight Foundation', 
      url: 'https://knightfoundation.org/grants/',
      fallbackUrls: ['https://knightfoundation.org/apply/'],
      type: 'major_foundation'
    },
    { 
      name: 'The Kresge Foundation', 
      url: 'https://kresge.org/our-work/',
      fallbackUrls: ['https://kresge.org/opportunities/'],
      type: 'regional_foundation'
    },
    { 
      name: 'Mozilla Foundation', 
      url: 'https://foundation.mozilla.org/en/what-we-fund/',
      fallbackUrls: ['https://foundation.mozilla.org/en/initiatives/'],
      type: 'tech_philanthropy'
    }
  ];
  
  const results = [];
  let totalGrants = 0;
  let successCount = 0;
  
  for (const source of testSources) {
    console.log(`\n🔍 Testing ${source.name}...`);
    
    try {
      const result = await scraper.scrapeSource(source);
      results.push(result);
      
      if (result.status === 'success') {
        successCount++;
        totalGrants += result.count;
        console.log(`  ✅ SUCCESS: Found ${result.count} grants`);
        
        // Show first grant as example
        if (result.opportunities && result.opportunities.length > 0) {
          const firstGrant = result.opportunities[0];
          console.log(`  📋 Example Grant:`);
          console.log(`     Title: ${firstGrant.title.substring(0, 60)}...`);
          console.log(`     Funder: ${firstGrant.funder}`);
          console.log(`     Link: ${firstGrant.link}`);
          if (firstGrant.deadline) {
            console.log(`     Deadline: ${firstGrant.deadline}`);
          }
          if (firstGrant.amount_max) {
            console.log(`     Amount: $${firstGrant.amount_max.toLocaleString()}`);
          }
          console.log(`     Confidence: ${firstGrant.ai_enhanced_data.confidence}%`);
        }
      } else {
        console.log(`  ⚠️  NO GRANTS FOUND`);
      }
      
    } catch (error) {
      console.log(`  ❌ ERROR: ${error.message}`);
      results.push({
        source: source.name,
        status: 'error',
        error: error.message
      });
    }
    
    // Small delay between sources
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  // Generate test report
  console.log('\n' + '=' .repeat(60));
  console.log('📊 TEST RESULTS SUMMARY');
  console.log('=' .repeat(60));
  console.log(`✅ Successful Sources: ${successCount}/${testSources.length}`);
  console.log(`📋 Total Grants Found: ${totalGrants}`);
  console.log(`📈 Average Grants per Success: ${successCount > 0 ? Math.round(totalGrants / successCount) : 0}`);
  
  console.log('\n📝 SOURCE BREAKDOWN:');
  for (const result of results) {
    const status = result.status === 'success' ? '✅' : '❌';
    const count = result.count || 0;
    console.log(`  ${status} ${result.source}: ${count} grants`);
  }
  
  return {
    success: successCount > 0,
    results,
    stats: {
      tested: testSources.length,
      successful: successCount,
      failed: testSources.length - successCount,
      totalGrants
    }
  };
}

// Run the test
if (import.meta.url === `file://${process.argv[1]}`) {
  testSelectedSources()
    .then(report => {
      if (report.success) {
        console.log('\n✅ Test completed successfully!');
        console.log('The enhanced scraper is working properly.');
      } else {
        console.log('\n⚠️  Test completed with issues.');
        console.log('Some sources may need additional work.');
      }
      process.exit(report.success ? 0 : 1);
    })
    .catch(error => {
      console.error('\n❌ Test failed:', error.message);
      process.exit(1);
    });
}

export default testSelectedSources;