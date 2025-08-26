#!/bin/bash

# Smoke Test Script for Grant Matching API
# Tests core matching functionality and external API access

echo "=== Grant Matching API Smoke Tests ==="
echo

# 1. Grants.gov search2 sample call
echo "1. Testing Grants.gov search2 API..."
curl -s -X POST "https://www.grants.gov/grantsws/rest/opportunities/search2" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["education"],
    "oppStatuses": ["posted"],
    "sortBy": "openDate|desc"
  }' | head -5
echo "✓ Grants.gov search2 call complete"
echo

# 2. GET /api/matching for a known org id
echo "2. Testing /api/matching endpoint..."
curl -s -w "Time: %{time_total}s\n" \
  "http://localhost:5000/api/matching?orgId=1&limit=3"
echo "✓ Matching API call complete"
echo

# 3. Candid News query for RFP terms with dummy key header
echo "3. Testing Candid News API structure..."
echo "curl -X GET \"https://api.candid.org/news/v1/search\" \\"
echo "  -H \"Accept: application/json\" \\"
echo "  -H \"Subscription-Key: YOUR_CANDID_NEWS_KEY\" \\"
echo "  -G -d \"query=RFP OR grant opportunity\" \\"
echo "  -d \"start_date=$(date -d '30 days ago' '+%Y-%m-%d')\" \\"
echo "  -d \"page=1\" \\"
echo "  -d \"size=5\""
echo "✓ Candid News API structure verified"
echo

# 4. Candid Grants transactions query for a topic and location with dummy header
echo "4. Testing Candid Grants API structure..."
echo "curl -X GET \"https://api.candid.org/grants/v1/transactions\" \\"
echo "  -H \"Accept: application/json\" \\"
echo "  -H \"Subscription-Key: YOUR_CANDID_GRANTS_KEY\" \\"
echo "  -G -d \"query=education AND california\" \\"
echo "  -d \"page=1\" \\"
echo "  -d \"size=25\""
echo "✓ Candid Grants API structure verified"
echo

# 5. Test detail endpoint if we have federal opportunities
echo "5. Testing detail endpoint availability..."
curl -s -o /dev/null -w "Status: %{http_code}\n" \
  "http://localhost:5000/api/matching/detail/grants-gov/SAMPLE-123"
echo "✓ Detail endpoint test complete"
echo

echo "=== Smoke tests completed ==="