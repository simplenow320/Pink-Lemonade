# Pink Lemonade Demo Configuration Guide

## Overview
This guide explains how to configure Pink Lemonade in **Demo Mode** to show real grant opportunities to potential buyers without consuming paid API quotas.

## Demo Mode Features

✅ **Real Grant Data** - Uses free government APIs (Federal Register, Grants.gov)  
✅ **Zero API Costs** - No paid API calls to Candid News/Grants APIs  
✅ **Quota Safe** - Background scheduler disabled to prevent automatic API calls  
✅ **Production Ready** - Same codebase, different configuration  

## Environment Variables

### Enable Demo Mode
```bash
# Set this to enable demo mode
DEMO_MODE=true
```

### When Demo Mode is Enabled
- ✅ Background scheduler **automatically disabled**
- ✅ Candid APIs **not called** (prevents 403 quota errors)  
- ✅ Only **free government APIs** used
- ✅ Real grant opportunities from Federal Register and Grants.gov
- ✅ Manual refresh buttons still work for demonstrations

### When Demo Mode is Disabled (Production)
```bash
DEMO_MODE=false  # or omit entirely
```
- ✅ Full Candid API integration enabled
- ✅ Background scheduler runs every 6 hours
- ✅ Complete grant discovery pipeline active

## Free Data Sources in Demo Mode

### 1. Federal Register API (100% Free)
- **Source**: Federal government grant notices
- **Cost**: FREE (no API key required)
- **Quota**: Unlimited
- **Data**: Recent federal grant opportunities and notices

### 2. Grants.gov GSA Search API (100% Free)
- **Source**: Active federal grant opportunities
- **Cost**: FREE (uses public GSA Search API)
- **Quota**: Unlimited
- **Data**: Live federal grant opportunities from Grants.gov

## Configuration Files Updated

### `app/config/settings.py`
```python
# Demo Mode Configuration
DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"
SCHEDULER_ENABLED = not DEMO_MODE  # Disable scheduler in demo mode

# Data sources in demo mode (only free APIs)
USE_CANDID_APIS = not DEMO_MODE  # Disable paid Candid APIs in demo mode
USE_FREE_GOVERNMENT_APIS = True  # Always enable free APIs
```

### `app/config.py`
```python
# Demo Mode Configuration
DEMO_MODE = os.environ.get('DEMO_MODE', 'false').lower() == 'true'

# Scheduler settings - disabled in demo mode
SCHEDULER_ENABLED = not DEMO_MODE

# API Configuration - disable paid APIs in demo mode
USE_CANDID_APIS = not DEMO_MODE
USE_FREE_GOVERNMENT_APIS = True
```

## New Demo-Safe Service

### `app/services/demo_safe_matching_service.py`
- **Purpose**: Provides grant matching using only free government APIs
- **Features**: 
  - Real grant opportunities from Federal Register
  - Live federal grants from Grants.gov GSA Search API
  - Intelligent scoring and ranking
  - Zero cost operation

## Quick Setup for Demo

### 1. Enable Demo Mode
```bash
export DEMO_MODE=true
```

### 2. Restart Application
```bash
# Restart the application to pick up new configuration
```

### 3. Verify Demo Mode
Check the application logs for:
```
🎯 DEMO MODE - background scheduler disabled to prevent API quota exhaustion
💡 Use manual refresh buttons for demo purposes
```

## API Endpoints in Demo Mode

When `DEMO_MODE=true`, the following endpoints automatically use free APIs only:

- `/api/matching/*` - Uses demo-safe matching service
- `/api/discovery/*` - Uses free government data sources
- Manual refresh buttons - Work with free APIs only

## Monitoring Demo Mode

### Application Logs
- Demo mode status clearly indicated in startup logs
- API calls show "FREE" cost indicators
- No Candid API quota warnings

### Grant Data Quality
- **Federal Register**: Latest federal grant notices and RFPs
- **Grants.gov**: Active federal grant opportunities
- **Scoring**: Intelligent matching based on organization profile
- **Freshness**: Data updated manually via refresh buttons

## Benefits for Sales Demos

1. **Real Data**: Show actual federal grant opportunities
2. **Zero Risk**: No API quota exhaustion possible
3. **Cost Effective**: Unlimited demos without API costs
4. **Professional**: Same UI/UX as production version
5. **Live Updates**: Manual refresh shows fresh data on demand

## Reverting to Production Mode

```bash
# Disable demo mode
export DEMO_MODE=false
# or
unset DEMO_MODE

# Restart application
```

The application will automatically:
- Re-enable background scheduler
- Activate Candid API integrations
- Resume full grant discovery pipeline

## Troubleshooting

### Problem: Still seeing Candid API errors
**Solution**: Ensure `DEMO_MODE=true` is set and application restarted

### Problem: No grant data showing
**Solution**: Use manual refresh buttons to fetch from government APIs

### Problem: Demo mode not detected
**Solution**: Check environment variable is set correctly:
```bash
echo $DEMO_MODE  # Should output: true
```

## Summary

Demo Mode provides a **bulletproof demonstration environment** where potential buyers can see real grant opportunities without any risk of API quota exhaustion or additional costs.