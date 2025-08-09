#!/usr/bin/env node
/**
 * End-to-End Test Runner for Pink Lemonade Grant Management Platform
 * Tests all major features and verifies data integrity
 */

import * as http from 'http';
import * as fs from 'fs';
import * as path from 'path';
import { JSDOM } from 'jsdom';
import fetch from 'node-fetch';

// Test configuration
const BASE_URL = process.env.TEST_URL || 'http://localhost:5000';
const DATA_MODE = process.env.APP_DATA_MODE || 'MOCK';
const REPORT_PATH = path.join(__dirname, 'TEST_REPORT.md');

// Test results tracking
interface TestResult {
  category: string;
  test: string;
  status: 'PASS' | 'FAIL' | 'SKIPPED';
  reason?: string;
  details?: any;
}

const testResults: TestResult[] = [];
const stats = {
  grantsLoaded: {} as Record<string, number>,
  connectors: {} as Record<string, number>,
  mode: DATA_MODE
};

// Utility functions
async function fetchPage(url: string): Promise<Document | null> {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    const dom = new JSDOM(html);
    return dom.window.document;
  } catch (error) {
    console.error(`Failed to fetch ${url}:`, error);
    return null;
  }
}

async function fetchAPI(endpoint: string, options: any = {}): Promise<any> {
  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error(`API call failed ${endpoint}:`, error);
    return null;
  }
}

function addTestResult(category: string, test: string, status: TestResult['status'], reason?: string, details?: any) {
  testResults.push({ category, test, status, reason, details });
  const symbol = status === 'PASS' ? '✓' : status === 'FAIL' ? '✗' : '○';
  console.log(`  ${symbol} ${test} ${reason ? `(${reason})` : ''}`);
}

// Test Categories
async function testLandingPage() {
  console.log('\n🧪 Testing Landing Page...');
  const doc = await fetchPage(BASE_URL);
  
  if (!doc) {
    addTestResult('Landing Page', 'Page loads', 'FAIL', 'Could not fetch page');
    return;
  }
  
  // Check for single logo in hero only
  const logos = doc.querySelectorAll('img[alt*="Pink Lemonade"], img[alt*="logo"]');
  const heroLogos = doc.querySelectorAll('.hero-section img[alt*="Pink Lemonade"], .hero-section img[alt*="logo"]');
  
  addTestResult(
    'Landing Page',
    'Single logo in hero section only',
    logos.length === 1 && heroLogos.length === 1 ? 'PASS' : 'FAIL',
    `Found ${logos.length} logos, ${heroLogos.length} in hero`
  );
  
  // Check no logo in nav/sidebar
  const navLogos = doc.querySelectorAll('nav img[alt*="logo"], .sidebar img[alt*="logo"]');
  addTestResult(
    'Landing Page',
    'No logo in nav or sidebar',
    navLogos.length === 0 ? 'PASS' : 'FAIL',
    `Found ${navLogos.length} logos in nav/sidebar`
  );
  
  // Check headline and buttons
  const headline = doc.querySelector('h1');
  const buttons = doc.querySelectorAll('button, a.btn, a[class*="button"]');
  
  addTestResult(
    'Landing Page',
    'Headline and buttons present',
    headline && buttons.length > 0 ? 'PASS' : 'FAIL',
    `Headline: ${!!headline}, Buttons: ${buttons.length}`
  );
  
  // Check for data mode badge
  const badge = doc.querySelector('[data-mode], .mode-badge, footer .badge');
  addTestResult(
    'Landing Page',
    'Data mode badge present',
    !!badge ? 'PASS' : 'FAIL',
    badge ? badge.textContent?.trim() || 'Badge found' : 'No badge found'
  );
}

async function testDashboard() {
  console.log('\n🧪 Testing Dashboard...');
  const doc = await fetchPage(`${BASE_URL}/dashboard`);
  
  if (!doc) {
    addTestResult('Dashboard', 'Page loads', 'FAIL', 'Could not fetch page');
    return;
  }
  
  addTestResult('Dashboard', 'Page loads', 'PASS');
  
  // Check KPI cards for fake numbers
  const kpiCards = doc.querySelectorAll('.metric-card, .kpi-card, [class*="metric"]');
  let fakeNumbers = 0;
  const suspiciousNumbers = ['128', '3.8', '42', '1234', '100', '0'];
  
  kpiCards.forEach(card => {
    const text = card.textContent || '';
    suspiciousNumbers.forEach(num => {
      if (text.includes(num) && !text.includes('N/A') && !text.includes('DEMO')) {
        fakeNumbers++;
      }
    });
  });
  
  addTestResult(
    'Dashboard',
    'No hardcoded fake numbers',
    fakeNumbers === 0 ? 'PASS' : 'FAIL',
    `Found ${fakeNumbers} suspicious numbers`
  );
  
  // Check for duplicate logos
  const dashLogos = doc.querySelectorAll('img[alt*="logo"]');
  const heroSection = doc.querySelector('.hero-section');
  let logosOutsideHero = 0;
  
  dashLogos.forEach(logo => {
    if (heroSection && !heroSection.contains(logo)) {
      logosOutsideHero++;
    }
  });
  
  addTestResult(
    'Dashboard',
    'No duplicate logos outside hero',
    logosOutsideHero === 0 ? 'PASS' : 'FAIL',
    `Found ${logosOutsideHero} logos outside hero`
  );
  
  // Test API endpoint
  const summary = await fetchAPI('/api/dashboard/summary');
  if (summary && summary.success) {
    addTestResult('Dashboard', 'API endpoint works', 'PASS');
    stats.grantsLoaded['dashboard'] = summary.summary?.total || 0;
  } else {
    addTestResult('Dashboard', 'API endpoint works', 'FAIL', 'API call failed');
  }
}

async function testFoundationDirectory() {
  console.log('\n🧪 Testing Foundation Directory...');
  const doc = await fetchPage(`${BASE_URL}/foundation-directory`);
  
  if (!doc) {
    addTestResult('Foundation Directory', 'Page loads', 'FAIL', 'Could not fetch page');
    return;
  }
  
  addTestResult('Foundation Directory', 'Page loads', 'PASS');
  
  // Check for entries
  const entries = doc.querySelectorAll('.foundation-card, .directory-entry, [class*="foundation"]');
  addTestResult(
    'Foundation Directory',
    'Shows foundation entries',
    entries.length >= 5 ? 'PASS' : 'FAIL',
    `Found ${entries.length} entries`
  );
  
  // Check search and filters
  const searchInput = doc.querySelector('input[type="search"], input[placeholder*="search" i]');
  const filters = doc.querySelectorAll('select, .filter, [class*="filter"]');
  
  addTestResult(
    'Foundation Directory',
    'Search and filters present',
    searchInput && filters.length > 0 ? 'PASS' : 'FAIL',
    `Search: ${!!searchInput}, Filters: ${filters.length}`
  );
}

async function testSavedGrants() {
  console.log('\n🧪 Testing Saved Grants & Applications...');
  
  // Test grants page
  const grantsDoc = await fetchPage(`${BASE_URL}/grants`);
  addTestResult(
    'Saved Grants',
    '/grants route loads',
    !!grantsDoc ? 'PASS' : 'FAIL'
  );
  
  // Test applications page  
  const appsDoc = await fetchPage(`${BASE_URL}/applications`);
  addTestResult(
    'Applications',
    '/applications route loads',
    !!appsDoc ? 'PASS' : 'FAIL'
  );
  
  // Test CRUD operations via API
  if (DATA_MODE === 'MOCK' || DATA_MODE === 'LIVE') {
    const testGrant = {
      title: 'Test Grant E2E',
      funder: 'Test Foundation',
      amount: 50000,
      deadline: new Date().toISOString(),
      status: 'discovered'
    };
    
    // Create
    const createResult = await fetchAPI('/api/grants', {
      method: 'POST',
      body: JSON.stringify(testGrant)
    });
    
    if (createResult && createResult.grant) {
      addTestResult('Saved Grants', 'Create grant', 'PASS');
      
      // Update
      const updateResult = await fetchAPI(`/api/grants/${createResult.grant.id}`, {
        method: 'PUT',
        body: JSON.stringify({ status: 'applied' })
      });
      addTestResult(
        'Saved Grants',
        'Update grant status',
        updateResult?.success ? 'PASS' : 'FAIL'
      );
      
      // Delete
      const deleteResult = await fetchAPI(`/api/grants/${createResult.grant.id}`, {
        method: 'DELETE'
      });
      addTestResult(
        'Saved Grants',
        'Delete grant',
        deleteResult?.success ? 'PASS' : 'FAIL'
      );
    } else {
      addTestResult('Saved Grants', 'Create grant', 'FAIL', 'Could not create test grant');
      addTestResult('Saved Grants', 'Update grant status', 'SKIPPED', 'No grant to update');
      addTestResult('Saved Grants', 'Delete grant', 'SKIPPED', 'No grant to delete');
    }
  }
}

async function testDiscoveryConnectors() {
  console.log('\n🧪 Testing Discovery Connectors...');
  
  // Test discovery page
  const doc = await fetchPage(`${BASE_URL}/discovery`);
  addTestResult(
    'Discovery',
    'Discovery page loads',
    !!doc ? 'PASS' : 'FAIL'
  );
  
  // Test connectors API
  const connectors = await fetchAPI('/api/discovery/connectors');
  if (connectors && connectors.success) {
    addTestResult('Discovery', 'Connectors API works', 'PASS');
    
    // Count connectors
    const enabledConnectors = connectors.connectors?.filter((c: any) => c.enabled) || [];
    stats.connectors['total'] = connectors.connectors?.length || 0;
    stats.connectors['enabled'] = enabledConnectors.length;
  } else {
    addTestResult('Discovery', 'Connectors API works', 'FAIL');
  }
  
  // Test Grants.gov connector in LIVE mode
  if (DATA_MODE === 'LIVE') {
    const grantsGov = await fetchAPI('/api/integration/fetch/grants_gov?limit=1');
    if (grantsGov && grantsGov.grants && grantsGov.grants.length > 0) {
      addTestResult('Discovery', 'Grants.gov returns data', 'PASS');
      stats.grantsLoaded['grants_gov'] = grantsGov.total || 0;
    } else {
      addTestResult('Discovery', 'Grants.gov returns data', 'FAIL', 'No results or API down');
    }
  } else {
    addTestResult('Discovery', 'Grants.gov returns data', 'SKIPPED', 'Not in LIVE mode');
  }
  
  // Test Run Now functionality
  const runResult = await fetchAPI('/api/discovery/run', { method: 'POST' });
  addTestResult(
    'Discovery',
    'Run Now returns opportunities',
    runResult && runResult.opportunities ? 'PASS' : 'FAIL',
    `Found ${runResult?.opportunities?.length || 0} opportunities`
  );
}

async function testWatchlists() {
  console.log('\n🧪 Testing Watchlists...');
  
  // Test watchlists API
  const watchlists = await fetchAPI('/api/watchlists');
  addTestResult(
    'Watchlists',
    'Watchlists API works',
    watchlists?.success ? 'PASS' : 'FAIL'
  );
  
  // Test create watchlist
  const testWatchlist = {
    city: 'Test City E2E',
    sources: ['test_source_1'],
    enabled: true
  };
  
  const createResult = await fetchAPI('/api/watchlists', {
    method: 'POST',
    body: JSON.stringify(testWatchlist)
  });
  
  if (createResult && createResult.watchlist) {
    addTestResult('Watchlists', 'Create watchlist', 'PASS');
    
    // Test run watchlist
    const runResult = await fetchAPI(`/api/watchlists/${createResult.watchlist.id}/run`, {
      method: 'POST'
    });
    addTestResult(
      'Watchlists',
      'Run watchlist',
      runResult?.success ? 'PASS' : 'FAIL'
    );
    
    // Delete watchlist
    const deleteResult = await fetchAPI(`/api/watchlists/${createResult.watchlist.id}`, {
      method: 'DELETE'
    });
    addTestResult(
      'Watchlists',
      'Delete watchlist',
      deleteResult?.success ? 'PASS' : 'FAIL'
    );
  } else {
    addTestResult('Watchlists', 'Create watchlist', 'FAIL');
    addTestResult('Watchlists', 'Run watchlist', 'SKIPPED', 'No watchlist to run');
    addTestResult('Watchlists', 'Delete watchlist', 'SKIPPED', 'No watchlist to delete');
  }
}

async function testAPILayer() {
  console.log('\n🧪 Testing API Integration Layer...');
  
  // Test sources endpoint
  const sources = await fetchAPI('/api/integration/sources');
  addTestResult(
    'API Layer',
    'Sources endpoint works',
    sources?.success ? 'PASS' : 'FAIL'
  );
  
  if (sources && sources.sources) {
    const enabledSources = sources.sources.filter((s: any) => s.enabled);
    stats.connectors['api_sources'] = enabledSources.length;
    
    addTestResult(
      'API Layer',
      'Has enabled sources',
      enabledSources.length > 0 ? 'PASS' : 'FAIL',
      `${enabledSources.length} enabled sources`
    );
  }
  
  // Test central API manager usage
  const searchResult = await fetchAPI('/api/integration/search', {
    method: 'POST',
    body: JSON.stringify({ query: 'education', filters: { limit: 1 } })
  });
  
  addTestResult(
    'API Layer',
    'Search through API Manager',
    searchResult?.success ? 'PASS' : 'FAIL'
  );
  
  // Check for org scoping
  const grantsResult = await fetchAPI('/api/grants');
  if (grantsResult && grantsResult.grants) {
    const hasOrgId = grantsResult.grants.every((g: any) => g.org_id || g.orgId);
    addTestResult(
      'API Layer',
      'Org-scoped data',
      hasOrgId || grantsResult.grants.length === 0 ? 'PASS' : 'FAIL',
      'All grants have org_id'
    );
  } else {
    addTestResult('API Layer', 'Org-scoped data', 'SKIPPED', 'Could not fetch grants');
  }
}

async function testStaticRules() {
  console.log('\n🧪 Testing Static Rules...');
  
  // Check multiple pages for duplicate logos
  const pages = ['/', '/dashboard', '/discovery', '/grants'];
  let totalDuplicates = 0;
  
  for (const page of pages) {
    const doc = await fetchPage(`${BASE_URL}${page}`);
    if (doc) {
      const navLogos = doc.querySelectorAll('nav img[alt*="logo"], .sidebar img[alt*="logo"]');
      totalDuplicates += navLogos.length;
    }
  }
  
  addTestResult(
    'Static Rules',
    'No duplicate logos in nav/sidebar',
    totalDuplicates === 0 ? 'PASS' : 'FAIL',
    `Found ${totalDuplicates} duplicate logos across pages`
  );
  
  // Check for minimalist design
  const homeDoc = await fetchPage(BASE_URL);
  if (homeDoc) {
    const hasMinimalistClasses = homeDoc.querySelector('[class*="matte"], [class*="minimal"]');
    addTestResult(
      'Static Rules',
      'Minimalist design tokens',
      !!hasMinimalistClasses ? 'PASS' : 'FAIL'
    );
  }
}

// Report generation
function generateReport() {
  const report: string[] = [];
  
  report.push('# Pink Lemonade E2E Test Report');
  report.push(`\nGenerated: ${new Date().toISOString()}`);
  report.push(`Data Mode: **${DATA_MODE}**\n`);
  
  // Summary stats
  const passed = testResults.filter(r => r.status === 'PASS').length;
  const failed = testResults.filter(r => r.status === 'FAIL').length;
  const skipped = testResults.filter(r => r.status === 'SKIPPED').length;
  
  report.push('## Summary');
  report.push(`- Total Tests: ${testResults.length}`);
  report.push(`- Passed: ${passed}`);
  report.push(`- Failed: ${failed}`);
  report.push(`- Skipped: ${skipped}\n`);
  
  // Test results table
  report.push('## Test Results\n');
  report.push('| Category | Test | Status | Details |');
  report.push('|----------|------|--------|---------|');
  
  testResults.forEach(result => {
    const status = result.status === 'PASS' ? '✅ PASS' : 
                   result.status === 'FAIL' ? '❌ FAIL' : 
                   '⏭️ SKIPPED';
    const details = result.reason || '-';
    report.push(`| ${result.category} | ${result.test} | ${status} | ${details} |`);
  });
  
  // Data statistics
  report.push('\n## Data Statistics\n');
  report.push(`### Grants Loaded (${DATA_MODE} mode)`);
  Object.entries(stats.grantsLoaded).forEach(([source, count]) => {
    report.push(`- ${source}: ${count}`);
  });
  
  report.push('\n### Connectors');
  Object.entries(stats.connectors).forEach(([key, value]) => {
    report.push(`- ${key}: ${value}`);
  });
  
  // Next fixes
  const failures = testResults.filter(r => r.status === 'FAIL');
  if (failures.length > 0) {
    report.push('\n## Next Fixes\n');
    failures.forEach(failure => {
      report.push(`- **${failure.category}**: ${failure.test}`);
      if (failure.reason) {
        report.push(`  - Issue: ${failure.reason}`);
      }
      
      // Suggest file paths based on category
      if (failure.category === 'Landing Page') {
        report.push(`  - Check: /app/templates/index.html, /app/templates/landing.html`);
      } else if (failure.category === 'Dashboard') {
        report.push(`  - Check: /app/templates/crm-dashboard.html, /app/api/dashboard.py`);
      } else if (failure.category === 'API Layer') {
        report.push(`  - Check: /app/services/apiManager.py, /app/api/integration.py`);
      }
    });
  } else {
    report.push('\n## Next Fixes\n');
    report.push('✅ All tests passed! No fixes needed.');
  }
  
  return report.join('\n');
}

// Main test runner
async function runTests() {
  console.log('🚀 Pink Lemonade E2E Test Suite');
  console.log(`   Mode: ${DATA_MODE}`);
  console.log(`   URL: ${BASE_URL}\n`);
  
  // Run all test categories
  await testLandingPage();
  await testDashboard();
  await testFoundationDirectory();
  await testSavedGrants();
  await testDiscoveryConnectors();
  await testWatchlists();
  await testAPILayer();
  await testStaticRules();
  
  // Generate and save report
  const report = generateReport();
  fs.writeFileSync(REPORT_PATH, report);
  
  // Print summary
  const passed = testResults.filter(r => r.status === 'PASS').length;
  const failed = testResults.filter(r => r.status === 'FAIL').length;
  const skipped = testResults.filter(r => r.status === 'SKIPPED').length;
  
  console.log('\n' + '='.repeat(50));
  console.log('📊 Test Summary');
  console.log('='.repeat(50));
  console.log(`✅ Passed:  ${passed}`);
  console.log(`❌ Failed:  ${failed}`);
  console.log(`⏭️  Skipped: ${skipped}`);
  console.log(`\n📄 Full report saved to: ${REPORT_PATH}`);
  
  // Exit with appropriate code
  process.exit(failed > 0 ? 1 : 0);
}

// Run tests
runTests().catch(error => {
  console.error('Test runner failed:', error);
  process.exit(1);
});