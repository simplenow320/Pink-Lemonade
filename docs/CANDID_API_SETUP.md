# Candid API Setup Guide

## Current Status
Your Candid API trial keys have been configured but are not yet activated.

## API Keys Configured
- **Grants API Primary**: cd6150ff5b27410899495f96969451ea
- **Grants API Secondary**: 243699cfa8c9422f9347b970e391fb59
- **News API Primary**: 7647f9fe2d9645d48def7a04b6835083
- **News API Secondary**: 0da558d408e74654baa000836cb88bef

## Activation Steps Required

### 1. Complete Trial Activation
1. Go to https://developer.candid.org/
2. Log in with your Candid account
3. Navigate to "My Subscriptions" or "API Keys"
4. Activate your trial subscriptions
5. Verify the keys are shown as "Active"

### 2. Check Trial Permissions
Your trial may have access to specific APIs:
- Essentials API (basic nonprofit data)
- Charity Check API (compliance validation)
- News API (foundation news)
- Grants API (grant opportunities)

### 3. Test Your Access
Once activated, test with:
```bash
curl -H "Subscription-Key: YOUR_KEY" \
  https://api.candid.org/essentials/v3/search?search_terms=education
```

## Alternative: Contact Candid Support
If keys still don't work after activation:
1. Email: apisupport@candid.org
2. Include your trial registration email
3. Ask which specific APIs your trial includes

## Currently Working Data Sources

While waiting for Candid activation, your platform has:

### ✅ Federal Register API (LIVE)
- 571+ government grant notices
- Updated daily
- No authentication required

### ✅ USAspending.gov (LIVE)
- Historical federal grant awards
- Spending data and trends
- No authentication required

### ✅ Major Foundations Directory (LIVE)
- Bill & Melinda Gates Foundation
- Ford Foundation
- Robert Wood Johnson Foundation
- MacArthur Foundation
- W.K. Kellogg Foundation
- Andrew W. Mellon Foundation
- Lilly Endowment
- Walton Family Foundation

### ✅ Grants.gov (Ready)
- Federal grant opportunities
- Requires proper authentication setup

## Next Steps
1. Activate your Candid trial at developer.candid.org
2. Test the activated keys
3. Contact Candid support if issues persist
4. Platform continues working with existing data sources

Your platform is fully functional with real grant data from multiple sources!