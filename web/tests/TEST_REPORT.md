# Pink Lemonade E2E Test Report

Generated: 2025-08-09T12:57:24.603Z
Data Mode: **LIVE**

## Summary
- Total Tests: 30
- Passed: 19
- Failed: 8
- Skipped: 3

## Test Results

| Category | Test | Status | Details |
|----------|------|--------|---------|
| Landing Page | Single logo in hero section only | ✅ PASS | Found 1 logos, 1 in hero |
| Landing Page | No logo in nav or sidebar | ✅ PASS | Found 0 logos in nav/sidebar |
| Landing Page | Headline and buttons present | ✅ PASS | Headline: true, Buttons: 1 |
| Landing Page | Data mode badge present | ❌ FAIL | No badge found |
| Dashboard | Page loads | ✅ PASS | - |
| Dashboard | No hardcoded fake numbers | ❌ FAIL | Found 8 suspicious numbers |
| Dashboard | No duplicate logos outside hero | ✅ PASS | Found 0 logos outside hero |
| Dashboard | API endpoint works | ✅ PASS | - |
| Foundation Directory | Page loads | ✅ PASS | - |
| Foundation Directory | Shows foundation entries | ❌ FAIL | Found 0 entries |
| Foundation Directory | Search and filters present | ✅ PASS | Search: true, Filters: 4 |
| Saved Grants | /grants route loads | ✅ PASS | - |
| Applications | /applications route loads | ✅ PASS | - |
| Saved Grants | Create grant | ❌ FAIL | Could not create test grant |
| Saved Grants | Update grant status | ⏭️ SKIPPED | No grant to update |
| Saved Grants | Delete grant | ⏭️ SKIPPED | No grant to delete |
| Discovery | Discovery page loads | ✅ PASS | - |
| Discovery | Connectors API works | ❌ FAIL | - |
| Discovery | Grants.gov returns data | ❌ FAIL | No results or API down |
| Discovery | Run Now returns opportunities | ❌ FAIL | Found 0 opportunities |
| Watchlists | Watchlists API works | ✅ PASS | - |
| Watchlists | Create watchlist | ✅ PASS | - |
| Watchlists | Run watchlist | ✅ PASS | - |
| Watchlists | Delete watchlist | ✅ PASS | - |
| API Layer | Sources endpoint works | ✅ PASS | - |
| API Layer | Has enabled sources | ✅ PASS | 6 enabled sources |
| API Layer | Search through API Manager | ✅ PASS | - |
| API Layer | Org-scoped data | ⏭️ SKIPPED | Could not fetch grants |
| Static Rules | No duplicate logos in nav/sidebar | ✅ PASS | Found 0 duplicate logos across pages |
| Static Rules | Minimalist design tokens | ❌ FAIL | - |

## Data Statistics

### Grants Loaded (LIVE mode)
- dashboard: 0

### Connectors
- api_sources: 6

## Next Fixes

- **Landing Page**: Data mode badge present
  - Issue: No badge found
  - Check: /app/templates/index.html, /app/templates/landing.html
- **Dashboard**: No hardcoded fake numbers
  - Issue: Found 8 suspicious numbers
  - Check: /app/templates/crm-dashboard.html, /app/api/dashboard.py
- **Foundation Directory**: Shows foundation entries
  - Issue: Found 0 entries
- **Saved Grants**: Create grant
  - Issue: Could not create test grant
- **Discovery**: Connectors API works
- **Discovery**: Grants.gov returns data
  - Issue: No results or API down
- **Discovery**: Run Now returns opportunities
  - Issue: Found 0 opportunities
- **Static Rules**: Minimalist design tokens