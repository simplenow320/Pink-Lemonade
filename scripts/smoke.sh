#!/bin/bash
# Smoke test script for GrantFlow API integrations
# Does not echo secrets

echo "=== GrantFlow API Integration Smoke Tests ==="
echo ""

# Base URL
BASE_URL=${BASE_URL:-"http://localhost:5000"}

echo "1. Testing Grants.gov search for 'youth'..."
curl -s -X POST "https://api.grants.gov/v1/api/search2" \
  -H "Content-Type: application/json" \
  -d '{
    "opportunity_status": "open",
    "keywords": ["youth"],
    "funding_instruments": ["G"],
    "eligibilities": ["25"],
    "page_size": 5
  }' | python -m json.tool 2>/dev/null | head -20
echo ""

echo "2. Testing GrantFlow matching endpoint..."
curl -s "${BASE_URL}/api/matching?orgId=1&limit=10" | python -m json.tool 2>/dev/null | head -30
echo ""

echo "3. Testing Candid News API (requires CANDID_NEWS_KEYS secret)..."
echo "Note: Replace YOUR_API_KEY_HERE with actual key from Replit Secrets"
curl -s "https://api.candid.org/news/v1/search?query=RFP&page=1&page_size=5" \
  -H "Accept: application/json" \
  -H "Subscription-Key: YOUR_API_KEY_HERE" | python -m json.tool 2>/dev/null | head -20
echo ""

echo "4. Testing Candid Grants Transactions API (requires CANDID_GRANTS_KEYS secret)..."
echo "Note: Replace YOUR_API_KEY_HERE with actual key from Replit Secrets"
curl -s "https://api.candid.org/grants/v1/transactions?query=education&state=CA&page=1&page_size=5" \
  -H "Accept: application/json" \
  -H "Subscription-Key: YOUR_API_KEY_HERE" | python -m json.tool 2>/dev/null | head -20
echo ""

echo "=== Smoke tests complete ==="#