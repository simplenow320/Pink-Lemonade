#!/bin/bash
# Set environment to LIVE mode for testing real data sources
export APP_DATA_MODE=LIVE
echo "Set APP_DATA_MODE to LIVE"

# Test the dashboard metrics in LIVE mode
echo "Testing dashboard metrics in LIVE mode..."
curl -s http://localhost:5000/api/dashboard/metrics | jq '.metrics'

echo ""
echo "Testing discovery search in LIVE mode..."
curl -s http://localhost:5000/api/discovery/search?query=nonprofit&limit=5 | jq '{dataMode, total, opportunities}'

echo ""
echo "Testing discovery sources status..."
curl -s http://localhost:5000/api/discovery/status | jq '{dataMode, onlineSources, totalSources}'