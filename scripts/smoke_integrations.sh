#!/bin/bash

# Integration Smoke Test for Pink Lemonade
# Tests all four data integrations: Candid (Essentials, News, Grants) + Grants.gov

echo "=== Pink Lemonade Integration Smoke Test ==="
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1) Check integration clients and routes
echo -e "${YELLOW}1. Integration Status Check${NC}"
echo "Checking client presence and route availability..."

INTEGRATIONS_RESULT=$(curl -s http://localhost:5000/api/health/integrations)
echo "$INTEGRATIONS_RESULT" | jq '.' 

# Extract status indicators
ESSENTIALS_CLIENT=$(echo "$INTEGRATIONS_RESULT" | jq -r '.candid.essentials_client // false')
NEWS_CLIENT=$(echo "$INTEGRATIONS_RESULT" | jq -r '.candid.news_client // false')
GRANTS_CLIENT=$(echo "$INTEGRATIONS_RESULT" | jq -r '.candid.grants_client // false')
GRANTS_GOV_CLIENT=$(echo "$INTEGRATIONS_RESULT" | jq -r '.grants_gov.client_present // false')
SECRETS_PRESENT=$(echo "$INTEGRATIONS_RESULT" | jq -r '.candid.secrets_present // false')

echo
echo "Client Status:"
echo "  Essentials Client: $ESSENTIALS_CLIENT"
echo "  News Client: $NEWS_CLIENT"
echo "  Grants Client: $GRANTS_CLIENT"
echo "  Grants.gov Client: $GRANTS_GOV_CLIENT"
echo "  Secrets Present: $SECRETS_PRESENT"
echo

# 2) Ping external APIs
echo -e "${YELLOW}2. Live API Ping Test${NC}"
echo "Testing actual API connectivity..."

PING_RESULT=$(curl -s http://localhost:5000/api/health/ping)
echo "$PING_RESULT" | jq '.'

# Extract ping results
ESSENTIALS_OK=$(echo "$PING_RESULT" | jq -r '.candid.essentials.ok // false')
NEWS_OK=$(echo "$PING_RESULT" | jq -r '.candid.news.ok // false')
GRANTS_OK=$(echo "$PING_RESULT" | jq -r '.candid.grants.ok // false')
GRANTS_GOV_OK=$(echo "$PING_RESULT" | jq -r '.grants_gov.ok // false')

echo
echo "API Connectivity:"
echo "  Essentials API: $ESSENTIALS_OK"
echo "  News API: $NEWS_OK"
echo "  Grants API: $GRANTS_OK"
echo "  Grants.gov API: $GRANTS_GOV_OK"
echo

# 3) Test matching endpoint with context and lengths
echo -e "${YELLOW}3. Matching Endpoint Test${NC}"
echo "Testing integrated matching functionality..."

MATCHING_RESULT=$(curl -s "http://localhost:5000/api/matching?orgId=1")

if [ $? -eq 0 ]; then
    echo "$MATCHING_RESULT" | jq '.context, (.news|length), (.federal|length)' 2>/dev/null || echo "Matching endpoint returned data (JSON parse issue)"
    
    # Extract counts
    NEWS_COUNT=$(echo "$MATCHING_RESULT" | jq -r '.news | length // 0')
    FEDERAL_COUNT=$(echo "$MATCHING_RESULT" | jq -r '.federal | length // 0')
    AWARD_COUNT=$(echo "$MATCHING_RESULT" | jq -r '.context.award_count // 0')
    
    echo
    echo "Matching Results:"
    echo "  News items: $NEWS_COUNT"
    echo "  Federal opportunities: $FEDERAL_COUNT"
    echo "  Award context count: $AWARD_COUNT"
else
    echo "Matching endpoint failed"
fi

echo

# 4) Test opportunity detail endpoint
echo -e "${YELLOW}4. Opportunity Detail Test${NC}"
echo "Testing grant detail functionality..."

# Try with a sample opportunity number
DETAIL_RESULT=$(curl -s "http://localhost:5000/api/matching/detail/grants-gov/SAMPLE-123")

if [ $? -eq 0 ]; then
    echo "$DETAIL_RESULT" | jq 'keys' 2>/dev/null || echo "Detail endpoint returned data (JSON parse issue)"
    
    # Check for source notes
    HAS_SOURCE_NOTES=$(echo "$DETAIL_RESULT" | jq -r 'has("sourceNotes")')
    echo "Has source notes: $HAS_SOURCE_NOTES"
else
    echo "Detail endpoint failed"
fi

echo

# Summary
echo -e "${YELLOW}=== Integration Test Summary ===${NC}"

# Count successful integrations
SUCCESS_COUNT=0
TOTAL_COUNT=4

if [ "$ESSENTIALS_CLIENT" = "true" ] && [ "$ESSENTIALS_OK" = "true" ]; then
    echo -e "${GREEN}✓ Candid Essentials API: Working${NC}"
    ((SUCCESS_COUNT++))
elif [ "$ESSENTIALS_CLIENT" = "true" ]; then
    echo -e "${YELLOW}⚠ Candid Essentials API: Client present, connectivity issue${NC}"
else
    echo -e "${RED}✗ Candid Essentials API: Not available${NC}"
fi

if [ "$NEWS_CLIENT" = "true" ] && [ "$NEWS_OK" = "true" ]; then
    echo -e "${GREEN}✓ Candid News API: Working${NC}"
    ((SUCCESS_COUNT++))
elif [ "$NEWS_CLIENT" = "true" ]; then
    echo -e "${YELLOW}⚠ Candid News API: Client present, connectivity issue${NC}"
else
    echo -e "${RED}✗ Candid News API: Not available${NC}"
fi

if [ "$GRANTS_CLIENT" = "true" ] && [ "$GRANTS_OK" = "true" ]; then
    echo -e "${GREEN}✓ Candid Grants API: Working${NC}"
    ((SUCCESS_COUNT++))
elif [ "$GRANTS_CLIENT" = "true" ]; then
    echo -e "${YELLOW}⚠ Candid Grants API: Client present, connectivity issue${NC}"
else
    echo -e "${RED}✗ Candid Grants API: Not available${NC}"
fi

if [ "$GRANTS_GOV_CLIENT" = "true" ] && [ "$GRANTS_GOV_OK" = "true" ]; then
    echo -e "${GREEN}✓ Grants.gov API: Working${NC}"
    ((SUCCESS_COUNT++))
elif [ "$GRANTS_GOV_CLIENT" = "true" ]; then
    echo -e "${YELLOW}⚠ Grants.gov API: Client present, connectivity issue${NC}"
else
    echo -e "${RED}✗ Grants.gov API: Not available${NC}"
fi

echo
echo "Overall Status: $SUCCESS_COUNT/$TOTAL_COUNT integrations fully operational"

if [ $SUCCESS_COUNT -eq $TOTAL_COUNT ]; then
    echo -e "${GREEN}🎉 All integrations working perfectly!${NC}"
    exit 0
elif [ $SUCCESS_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠️ Partial integration success - some APIs may need attention${NC}"
    exit 1
else
    echo -e "${RED}❌ No integrations fully working - check configuration${NC}"
    exit 2
fi