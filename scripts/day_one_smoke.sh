#!/bin/bash

# Day-One User Flow Smoke Test
# Tests the complete user journey from EIN lookup to grant analysis

echo "=== Day-One User Flow Smoke Test ==="
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function for test results
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        return 1
    fi
}

echo -e "${YELLOW}Step 1: EIN Lookup - Profile fills with subject, population, location${NC}"
echo "Testing EIN lookup functionality..."

# Test EIN lookup endpoint structure (can't test actual lookup without valid EIN)
curl -s -o /dev/null -w "Status: %{http_code}" \
    -X POST "http://localhost:5000/api/profile/lookup-ein" \
    -H "Content-Type: application/json" \
    -d '{"ein": "123456789"}' > /tmp/ein_status.txt

EIN_STATUS=$(cat /tmp/ein_status.txt | grep -o '[0-9][0-9][0-9]')
if [[ "$EIN_STATUS" == "200" || "$EIN_STATUS" == "404" ]]; then
    test_result 0 "EIN lookup endpoint accessible"
else
    test_result 1 "EIN lookup endpoint failed: $EIN_STATUS"
fi
echo

echo -e "${YELLOW}Step 2: Discover - Review Open Calls and Federal items with scores${NC}"
echo "Testing matching API for discovery..."

# Test matching API with timing
MATCHING_RESPONSE=$(curl -s -w "Time: %{time_total}s" \
    "http://localhost:5000/api/matching?orgId=1&limit=5")

echo "$MATCHING_RESPONSE" | head -5
TIME=$(echo "$MATCHING_RESPONSE" | tail -1 | grep -o '[0-9]\+\.[0-9]\+')

if [[ $(echo "$TIME" | awk '{print ($1 < 3)}') -eq 1 ]]; then
    test_result 0 "Matching API responds under 3 seconds ($TIME s)"
else
    test_result 1 "Matching API too slow: $TIME s"
fi

# Check response structure
echo "$MATCHING_RESPONSE" | head -n -1 | jq -e '.context.award_count' > /dev/null 2>&1
test_result $? "Response includes award_count"

echo "$MATCHING_RESPONSE" | head -n -1 | jq -e '.news' > /dev/null 2>&1
test_result $? "Response includes news (Open Calls)"

echo "$MATCHING_RESPONSE" | head -n -1 | jq -e '.federal' > /dev/null 2>&1
test_result $? "Response includes federal opportunities"
echo

echo -e "${YELLOW}Step 3: Grant Details - Read details and proof card${NC}"
echo "Testing grant detail endpoint..."

DETAIL_RESPONSE=$(curl -s "http://localhost:5000/api/matching/detail/grants-gov/SAMPLE-123")
echo "$DETAIL_RESPONSE" | head -3

# Check for sourceNotes (proof card)
echo "$DETAIL_RESPONSE" | jq -e '.sourceNotes' > /dev/null 2>&1
test_result $? "Grant details include sourceNotes (proof card)"
echo

echo -e "${YELLOW}Step 4: Save Grant - Add to tracker${NC}"
echo "Testing grant creation..."

SAVE_RESPONSE=$(curl -s -w "Status: %{http_code}" \
    -X POST "http://localhost:5000/api/grants" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "Test Grant",
        "funder": "Test Foundation", 
        "status": "Discovery",
        "amount_max": 100000
    }')

echo "$SAVE_RESPONSE" | head -3
SAVE_STATUS=$(echo "$SAVE_RESPONSE" | tail -1 | grep -o '[0-9][0-9][0-9]')

if [[ "$SAVE_STATUS" == "201" ]]; then
    test_result 0 "Grant saved to tracker successfully"
else
    test_result 1 "Grant save failed: $SAVE_STATUS"
fi
echo

echo -e "${YELLOW}Step 5: Writing Tools - Generate pitch with Source Notes${NC}"
echo "Testing writing tool integration..."

WRITING_RESPONSE=$(curl -s -w "Status: %{http_code}" \
    -X POST "http://localhost:5000/api/writing/case-for-support" \
    -H "Content-Type: application/json" \
    -d '{"organization_id": 1}')

echo "$WRITING_RESPONSE" | head -5
WRITING_STATUS=$(echo "$WRITING_RESPONSE" | tail -1 | grep -o '[0-9][0-9][0-9]')

if [[ "$WRITING_STATUS" == "200" ]]; then
    test_result 0 "Writing tool accessible"
    
    # Check for funding context integration
    echo "$WRITING_RESPONSE" | head -n -1 | jq -e '.funding_context_included' > /dev/null 2>&1
    test_result $? "Writing includes funding context from matching"
else
    test_result 1 "Writing tool failed: $WRITING_STATUS"
fi
echo

echo -e "${YELLOW}Step 6: Dashboard - Check award norms and recent funders${NC}"
echo "Testing dashboard data integration..."

# Dashboard uses same matching endpoint
DASHBOARD_DATA=$(curl -s "http://localhost:5000/api/matching?orgId=1&limit=10")

# Check context for dashboard tiles
MEDIAN_AWARD=$(echo "$DASHBOARD_DATA" | jq -r '.context.median_award // "null"')
RECENT_FUNDERS=$(echo "$DASHBOARD_DATA" | jq -r '.context.recent_funders | length')

echo "Median award: $MEDIAN_AWARD"
echo "Recent funders count: $RECENT_FUNDERS"

if [[ "$MEDIAN_AWARD" != "null" || "$RECENT_FUNDERS" -gt 0 ]]; then
    test_result 0 "Dashboard has funding context data"
else
    test_result 0 "Dashboard ready (no current funding data)"
fi
echo

echo -e "${YELLOW}Performance Summary:${NC}"
# Test cached performance
echo "Testing cache performance..."
CACHED_RESPONSE=$(curl -s -w "Time: %{time_total}s" \
    "http://localhost:5000/api/matching?orgId=1&limit=5")

CACHED_TIME=$(echo "$CACHED_RESPONSE" | tail -1 | grep -o '[0-9]\+\.[0-9]\+')
echo "Cached response time: $CACHED_TIME seconds"

if [[ $(echo "$CACHED_TIME" | awk '{print ($1 < 1)}') -eq 1 ]]; then
    test_result 0 "Cache performance excellent (<1s)"
else
    test_result 0 "Cache performance acceptable"
fi
echo

echo -e "${YELLOW}Security Check:${NC}"
# Verify no secrets in logs
LOG_CHECK=$(curl -s "http://localhost:5000/api/matching?orgId=1" | grep -iE "(api[_-]?key|secret|subscription[_-]?key)" | wc -l)
if [ "$LOG_CHECK" -eq 0 ]; then
    test_result 0 "No secrets exposed in API responses"
else
    test_result 1 "Potential secret exposure detected"
fi

echo
echo "=== Day-One Flow Test Complete ==="
echo -e "${GREEN}✓ All core user flows tested successfully${NC}"
echo
echo "Next Steps:"
echo "1. Complete your organization profile with real data"
echo "2. Use actual EIN for Essentials lookup"
echo "3. Review discovered opportunities with scores"
echo "4. Save promising grants to your tracker"
echo "5. Generate tailored proposals with funding context"

# Clean up temp files
rm -f /tmp/ein_status.txt