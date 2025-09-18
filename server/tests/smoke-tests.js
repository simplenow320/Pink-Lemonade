/**
 * Basic Smoke Tests for Express Server
 * Tests key endpoints to ensure the server is working
 */

import axios from 'axios';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('SmokeTests');
const BASE_URL = process.env.SERVER_URL || 'http://localhost:3001';

/**
 * Test configuration
 */
const TESTS = [
  {
    name: 'Health Check',
    method: 'GET',
    url: '/api/health',
    expectedStatus: 200,
    expectedFields: ['success', 'data', 'timestamp']
  },
  {
    name: 'Sources Status',
    method: 'GET', 
    url: '/api/sources/status',
    expectedStatus: 200,
    expectedFields: ['success', 'data', 'timestamp']
  },
  {
    name: 'Grants Search',
    method: 'GET',
    url: '/api/grants/search?query=education',
    expectedStatus: 200,
    expectedFields: ['success', 'data', 'count']
  },
  {
    name: '404 Handler',
    method: 'GET',
    url: '/api/nonexistent',
    expectedStatus: 404,
    expectedFields: ['success', 'error']
  }
];

/**
 * Run individual test
 */
async function runTest(test) {
  try {
    logger.info(`Running test: ${test.name}`);
    
    const config = {
      method: test.method,
      url: `${BASE_URL}${test.url}`,
      timeout: 10000,
      validateStatus: () => true // Don't throw on non-2xx status
    };

    if (test.data) {
      config.data = test.data;
    }

    const response = await axios(config);
    
    // Check status code
    if (response.status !== test.expectedStatus) {
      throw new Error(`Expected status ${test.expectedStatus}, got ${response.status}`);
    }
    
    // Check response fields
    if (test.expectedFields) {
      const data = response.data;
      for (const field of test.expectedFields) {
        if (!(field in data)) {
          throw new Error(`Missing expected field: ${field}`);
        }
      }
    }
    
    logger.info(`✅ ${test.name} - PASSED`);
    return { name: test.name, status: 'PASSED', response: response.data };
    
  } catch (error) {
    logger.error(`❌ ${test.name} - FAILED: ${error.message}`);
    return { 
      name: test.name, 
      status: 'FAILED', 
      error: error.message,
      details: error.response?.data || null
    };
  }
}

/**
 * Run all smoke tests
 */
async function runSmokeTests() {
  logger.info(`🚀 Starting smoke tests against ${BASE_URL}`);
  logger.info(`Running ${TESTS.length} tests...`);
  
  const results = [];
  let passedCount = 0;
  let failedCount = 0;
  
  // Wait a moment for server to be ready
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  for (const test of TESTS) {
    const result = await runTest(test);
    results.push(result);
    
    if (result.status === 'PASSED') {
      passedCount++;
    } else {
      failedCount++;
    }
    
    // Brief pause between tests
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  // Summary
  logger.info(`\n📊 Smoke Test Results:`);
  logger.info(`✅ Passed: ${passedCount}`);
  logger.info(`❌ Failed: ${failedCount}`);
  logger.info(`📋 Total: ${TESTS.length}`);
  
  if (failedCount === 0) {
    logger.info(`🎉 All tests passed! Server is ready.`);
  } else {
    logger.warn(`⚠️  ${failedCount} test(s) failed. Server may have issues.`);
  }
  
  return {
    total: TESTS.length,
    passed: passedCount,
    failed: failedCount,
    results,
    success: failedCount === 0
  };
}

// Export for use as module
export { runSmokeTests, runTest, TESTS };

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runSmokeTests()
    .then((results) => {
      process.exit(results.success ? 0 : 1);
    })
    .catch((error) => {
      logger.error(`Smoke tests failed to run: ${error.message}`);
      process.exit(1);
    });
}