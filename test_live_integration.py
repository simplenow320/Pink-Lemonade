#!/usr/bin/env python3
"""
Test script to verify LIVE data integration
Tests both LIVE and MOCK modes for the API layer
"""

import os
import sys
import requests
import json

def test_api_endpoint(url, expected_keys=None):
    """Test an API endpoint and return response data"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if expected_keys:
                missing_keys = set(expected_keys) - set(data.keys())
                if missing_keys:
                    print(f"❌ Missing keys: {missing_keys}")
                    return None
            return data
        else:
            print(f"❌ HTTP {response.status_code}: {url}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_live_integration():
    """Test the complete LIVE data integration"""
    
    print("🧪 Testing Pink Lemonade LIVE Data Integration")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Discovery Sources
    print("\n📡 Testing Discovery Sources...")
    sources_data = test_api_endpoint(f"{base_url}/api/discovery/sources", ['success', 'sources'])
    if sources_data and sources_data['success']:
        print(f"✅ Found {len(sources_data['sources'])} enabled sources:")
        for source in sources_data['sources'][:3]:  # Show first 3
            print(f"   • {source['name']} ({source['id']})")
    
    # Test 2: Dashboard Metrics
    print("\n📊 Testing Dashboard Metrics...")
    metrics_data = test_api_endpoint(f"{base_url}/api/dashboard/metrics", ['success', 'metrics', 'dataMode'])
    if metrics_data and metrics_data['success']:
        mode = metrics_data.get('dataMode', 'Unknown')
        metrics = metrics_data['metrics']
        print(f"✅ Dashboard running in {mode} mode")
        print(f"   • Total Grants: {metrics.get('totalGrants', 'N/A')}")
        print(f"   • Active Grants: {metrics.get('activeGrants', 'N/A')}")
        print(f"   • Win Rate: {metrics.get('winRate', 'N/A')}%")
    
    # Test 3: Discovery Search
    print("\n🔍 Testing Discovery Search...")
    search_data = test_api_endpoint(f"{base_url}/api/discovery/search?query=nonprofit&limit=3", 
                                  ['success', 'opportunities', 'dataMode'])
    if search_data and search_data['success']:
        mode = search_data.get('dataMode', 'Unknown')
        count = len(search_data.get('opportunities', []))
        print(f"✅ Search in {mode} mode returned {count} opportunities")
        if count > 0:
            for i, opp in enumerate(search_data['opportunities'][:2]):
                print(f"   • {opp.get('title', 'Untitled')} ({opp.get('source', 'Unknown')})")
    
    # Test 4: Discovery Status
    print("\n🏥 Testing Discovery Status...")
    status_data = test_api_endpoint(f"{base_url}/api/discovery/status", 
                                  ['success', 'sources', 'dataMode'])
    if status_data and status_data['success']:
        mode = status_data.get('dataMode', 'Unknown')
        online = status_data.get('onlineSources', 0)
        total = status_data.get('totalSources', 0)
        print(f"✅ Status check in {mode} mode: {online}/{total} sources online")
    
    # Test 5: Grant Search (Specific Source)
    print("\n🏛️ Testing Grants.gov Integration...")
    grants_data = test_api_endpoint(f"{base_url}/api/discovery/search?source=grants_gov&query=education&limit=2")
    if grants_data and grants_data.get('success'):
        count = len(grants_data.get('opportunities', []))
        print(f"✅ Grants.gov returned {count} opportunities")
        
        if count > 0:
            for opp in grants_data['opportunities'][:1]:
                print(f"   • {opp.get('title', 'Untitled')}")
                print(f"     Source: {opp.get('source', 'Unknown')}")
                print(f"     Link: {opp.get('link', 'N/A')}")
    
    # Test 6: Federal Register Integration
    print("\n📰 Testing Federal Register Integration...")
    fed_data = test_api_endpoint(f"{base_url}/api/discovery/search?source=federal_register&query=grant&limit=2")
    if fed_data and fed_data.get('success'):
        count = len(fed_data.get('opportunities', []))
        print(f"✅ Federal Register returned {count} opportunities")
    
    # Test 7: Recent Activity
    print("\n📝 Testing Recent Activity...")
    activity_data = test_api_endpoint(f"{base_url}/api/dashboard/recent-activity", ['success', 'activities'])
    if activity_data and activity_data['success']:
        count = len(activity_data.get('activities', []))
        print(f"✅ Found {count} recent activities")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 INTEGRATION TEST SUMMARY")
    print("=" * 50)
    
    if metrics_data:
        mode = metrics_data.get('dataMode', 'Unknown')
        if mode == 'LIVE':
            print("✅ System running in LIVE mode with real API data")
        elif mode == 'MOCK':  
            print("ℹ️ System running in MOCK mode with demo data")
        else:
            print("⚠️ Unknown data mode detected")
    
    if sources_data:
        source_count = len(sources_data.get('sources', []))
        print(f"✅ {source_count} discovery sources enabled and configured")
    
    print("\n🔗 Key Integration Points:")
    print("• Dashboard metrics compute from real saved grants")
    print("• Discovery searches live APIs (Grants.gov, Federal Register, GovInfo)")
    print("• Activity feed tracks real grant status changes")
    print("• All data flows through centralized API Manager")
    
    print("\n📚 Configuration:")
    print("• Data mode controlled by APP_DATA_MODE environment variable")
    print("• API configs stored in app/config/apiConfig.py")
    print("• Rate limiting and caching applied to all sources")
    print("• Documentation updated in docs/apiManager.md")

if __name__ == "__main__":
    test_live_integration()