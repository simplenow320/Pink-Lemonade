/**
 * Test Script for API Clients
 * Tests all implemented Node.js API clients
 */

import { apiManager } from './services/apiManager.js';
import { createLogger } from './utils/logger.js';

const logger = createLogger('APITest');

/**
 * Test all API clients
 */
async function testAllClients() {
  logger.info('Starting API client tests...');
  
  // Get enabled sources
  const enabledSources = apiManager.getEnabledSources();
  logger.info(`Testing ${Object.keys(enabledSources).length} enabled sources`);
  
  const results = {};
  
  for (const [sourceName, config] of Object.entries(enabledSources)) {
    logger.info(`\n=== Testing ${config.name} (${sourceName}) ===`);
    
    try {
      const startTime = Date.now();
      
      // Test with basic search parameters
      const grants = await apiManager.getGrantsFromSource(sourceName, {
        query: 'education',
        limit: 5
      });
      
      const duration = Date.now() - startTime;
      
      results[sourceName] = {
        name: config.name,
        success: true,
        grants_count: grants ? grants.length : 0,
        duration: `${duration}ms`,
        sample_grant: grants && grants.length > 0 ? {
          id: grants[0].id,
          title: grants[0].title?.substring(0, 100) + '...',
          funder: grants[0].funder,
          source: grants[0].source
        } : null
      };
      
      logger.info(`✅ ${config.name}: Found ${grants.length} grants in ${duration}ms`);
      
    } catch (error) {
      results[sourceName] = {
        name: config.name,
        success: false,
        error: error.message,
        error_type: error.constructor.name
      };
      
      logger.error(`❌ ${config.name}: ${error.message}`);
    }
  }
  
  // Print summary
  logger.info('\n=== TEST SUMMARY ===');
  const successful = Object.values(results).filter(r => r.success).length;
  const total = Object.keys(results).length;
  
  logger.info(`Successful: ${successful}/${total} sources`);
  
  if (successful > 0) {
    logger.info('\n✅ Working sources:');
    Object.entries(results)
      .filter(([, result]) => result.success)
      .forEach(([sourceName, result]) => {
        logger.info(`  - ${result.name}: ${result.grants_count} grants (${result.duration})`);
      });
  }
  
  const failed = Object.values(results).filter(r => !r.success);
  if (failed.length > 0) {
    logger.info('\n❌ Failed sources:');
    failed.forEach(result => {
      logger.info(`  - ${result.name}: ${result.error}`);
    });
  }
  
  return results;
}

/**
 * Test circuit breaker functionality
 */
async function testCircuitBreaker() {
  logger.info('\n=== Testing Circuit Breaker ===');
  
  const summary = apiManager.getCircuitBreakerSummary();
  logger.info(`Circuit breaker summary: ${summary.totalSources} sources, ${summary.openCircuits} open, ${summary.closedCircuits} closed`);
  
  if (summary.openCircuits > 0) {
    logger.warn(`Open circuits: ${summary.sourcesByState.open.join(', ')}`);
  }
  
  return summary;
}

/**
 * Test RSS parsing functionality
 */
async function testRSSFeed() {
  logger.info('\n=== Testing RSS Feed Parsing ===');
  
  try {
    // Test with one of the RSS sources
    const grants = await apiManager.getGrantsFromSource('nsf_grants', {
      limit: 3,
      keywords: ['funding', 'research']
    });
    
    logger.info(`✅ RSS Parsing: Found ${grants.length} grants from NSF RSS feed`);
    
    if (grants.length > 0) {
      logger.info(`Sample grant: ${grants[0].title} from ${grants[0].funder}`);
    }
    
    return { success: true, grants_count: grants.length };
  } catch (error) {
    logger.error(`❌ RSS Parsing failed: ${error.message}`);
    return { success: false, error: error.message };
  }
}

/**
 * Test data transformation
 */
function testDataTransformation() {
  logger.info('\n=== Testing Data Transformation ===');
  
  // Test standardized grant object creation
  const mockGrantData = {
    opportunityId: 'TEST-123',
    opportunityTitle: 'Test Education Grant',
    agencyName: 'Department of Education',
    description: 'A test grant for education programs',
    awardCeiling: 50000,
    closeDate: '2024-12-31'
  };
  
  try {
    const standardGrant = apiManager._transformGrantsGovData({ grants: [mockGrantData] });
    
    if (standardGrant && standardGrant.length > 0) {
      const grant = standardGrant[0];
      logger.info(`✅ Data Transformation: Created standardized grant`);
      logger.info(`  - ID: ${grant.id}`);
      logger.info(`  - Title: ${grant.title}`);
      logger.info(`  - Funder: ${grant.funder}`);
      logger.info(`  - Source: ${grant.source}`);
      
      return { success: true, grant };
    } else {
      throw new Error('No grants returned from transformation');
    }
  } catch (error) {
    logger.error(`❌ Data Transformation failed: ${error.message}`);
    return { success: false, error: error.message };
  }
}

/**
 * Main test function
 */
async function runTests() {
  try {
    logger.info('🧪 Starting comprehensive API client testing...\n');
    
    // Test basic configuration
    logger.info('API Manager initialized successfully');
    logger.info(`Cache manager: ${apiManager.cache ? 'Active' : 'Inactive'}`);
    logger.info(`Rate limiter: ${apiManager.rateLimiter ? 'Active' : 'Inactive'}`);
    
    // Run all tests
    const clientResults = await testAllClients();
    const circuitBreakerSummary = await testCircuitBreaker();
    const rssResults = await testRSSFeed();
    const transformationResults = testDataTransformation();
    
    // Final summary
    logger.info('\n🎉 ALL TESTS COMPLETED');
    logger.info('==========================================');
    
    const testResults = {
      client_tests: clientResults,
      circuit_breaker: circuitBreakerSummary,
      rss_parsing: rssResults,
      data_transformation: transformationResults,
      timestamp: new Date().toISOString()
    };
    
    return testResults;
    
  } catch (error) {
    logger.error(`Test suite failed: ${error.message}`);
    throw error;
  }
}

// Run tests if this script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runTests()
    .then(results => {
      console.log('\n✅ Test suite completed successfully');
      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ Test suite failed:', error.message);
      process.exit(1);
    });
}

export { runTests, testAllClients, testCircuitBreaker, testRSSFeed, testDataTransformation };