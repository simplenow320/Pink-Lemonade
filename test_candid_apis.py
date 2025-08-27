#!/usr/bin/env python
"""Test script to check if Candid APIs are returning real data"""
import json
import sys
sys.path.insert(0, '/home/runner/workspace')

from app.services.candid_client import get_news_client, get_grants_client, get_essentials_client

def test_news_api():
    """Test Candid News API"""
    print("\n=== Testing Candid News API ===")
    client = get_news_client()
    results = client.search("grant", size=5)
    
    if results:
        print(f"✓ News API returned {len(results)} results")
        if results[0].get('source') == 'candid_news':
            print("✓ Data appears to be from real Candid API")
            print(f"  Sample article: {results[0].get('title', 'N/A')[:100]}")
            print(f"  Publication: {results[0].get('site_name', 'N/A')}")
    else:
        print("✗ News API returned no results")
    return results

def test_grants_api():
    """Test Candid Grants API"""
    print("\n=== Testing Candid Grants API ===")
    client = get_grants_client()
    results = client.transactions("education", size=5)
    
    if results:
        print(f"✓ Grants API returned {len(results)} results")
        if results[0].get('source') == 'candid_api':
            print("✓ Data appears to be from real Candid API")
            print(f"  Sample grant: {results[0].get('funder_name', 'N/A')} → {results[0].get('recipient_name', 'N/A')}")
            print(f"  Amount: ${results[0].get('amount', 0):,}")
        elif results[0].get('source') == 'candid_sample':
            print("✗ Data is SAMPLE/FAKE data (not from real API)")
            print("  The API is falling back to generated sample data")
    else:
        print("✗ Grants API returned no results")
    return results

def test_essentials_api():
    """Test Candid Essentials API"""
    print("\n=== Testing Candid Essentials API ===")
    client = get_essentials_client()
    
    # Test search by name
    results = client.search_org(name="Gates Foundation", size=3)
    
    if results:
        print(f"✓ Essentials API returned {len(results)} results")
        if results[0].get('source') == 'candid_essentials':
            print("✓ Data appears to be from real Candid API")
            print(f"  Sample org: {results[0].get('name', 'N/A')}")
            print(f"  Location: {results[0].get('city', 'N/A')}, {results[0].get('state', 'N/A')}")
            print(f"  EIN: {results[0].get('ein', 'N/A')}")
    else:
        print("✗ Essentials API returned no results")
    
    # Test profile lookup if we got an EIN
    if results and results[0].get('ein'):
        ein = results[0]['ein']
        profile = client.get_profile(ein)
        if profile:
            print(f"✓ Successfully retrieved profile for EIN {ein}")
        else:
            print(f"✗ Could not retrieve profile for EIN {ein}")
    
    return results

def main():
    """Run all API tests"""
    print("Testing Candid API Endpoints")
    print("=" * 50)
    
    news_results = test_news_api()
    grants_results = test_grants_api()
    essentials_results = test_essentials_api()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("=" * 50)
    
    # Check if we're getting real data or fake data
    real_data_count = 0
    fake_data_count = 0
    
    if news_results and news_results[0].get('source') == 'candid_news':
        real_data_count += 1
        print("✓ News API: REAL DATA")
    else:
        print("✗ News API: NO DATA")
    
    if grants_results:
        if grants_results[0].get('source') == 'candid_api':
            real_data_count += 1
            print("✓ Grants API: REAL DATA")
        elif grants_results[0].get('source') == 'candid_sample':
            fake_data_count += 1
            print("✗ Grants API: FAKE/SAMPLE DATA")
    else:
        print("✗ Grants API: NO DATA")
    
    if essentials_results and essentials_results[0].get('source') == 'candid_essentials':
        real_data_count += 1
        print("✓ Essentials API: REAL DATA")
    else:
        print("✗ Essentials API: NO DATA")
    
    print("\n" + "=" * 50)
    if real_data_count == 3:
        print("✓ ALL APIS RETURNING REAL DATA")
    elif real_data_count > 0:
        print(f"⚠ PARTIAL SUCCESS: {real_data_count}/3 APIs returning real data")
    else:
        print("✗ NO APIS RETURNING REAL DATA")
    
    if fake_data_count > 0:
        print(f"⚠ WARNING: {fake_data_count} API(s) using fallback sample data")

if __name__ == "__main__":
    main()