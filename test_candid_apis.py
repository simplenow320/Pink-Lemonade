#!/usr/bin/env python3
"""
CRITICAL CANDID API ACTIVATION TEST
Tests all three premium Candid APIs with real keys to verify enterprise-level data access
"""
import os
import sys
import json
from datetime import datetime

# Add app to path for imports
sys.path.insert(0, 'app')

from services.candid_essentials import CandidEssentialsClient, get_candid_client
from services.candid_client import NewsClient, GrantsClient
from services.candid_news_client import CandidNewsClient
from services.candid_grants_client import CandidGrantsClient

def test_candid_essentials():
    """Test Candid Essentials API - Organization lookup capability"""
    print("\n" + "="*60)
    print("🔥 TESTING CANDID ESSENTIALS API (Premium Organization Data)")
    print("="*60)
    
    try:
        # Test environment variable
        api_key = os.environ.get('CANDID_ESSENTIALS_KEY')
        if not api_key:
            print("❌ CANDID_ESSENTIALS_KEY not found in environment")
            return False
        
        print(f"✅ API Key loaded: {api_key[:8]}...{api_key[-4:]}")
        
        # Initialize client
        client = CandidEssentialsClient()
        
        # Test 1: Search by organization name (real foundation)
        print("\n📍 Testing organization name search...")
        result = client.search_by_name("Gates Foundation", limit=3)
        
        if result:
            print("✅ REAL DATA RETRIEVED from Candid Essentials!")
            org_data = result.get('organization', {})
            print(f"   Organization: {org_data.get('organization_name', 'N/A')}")
            print(f"   EIN: {org_data.get('ein', 'N/A')}")
            print(f"   Website: {org_data.get('website_url', 'N/A')}")
            
            # Extract tokens to show data richness
            tokens = client.extract_tokens(result)
            print(f"   PCS Subject Codes: {len(tokens.get('pcs_subject_codes', []))}")
            print(f"   PCS Population Codes: {len(tokens.get('pcs_population_codes', []))}")
            print(f"   Locations: {tokens.get('locations', [])}")
            return True
        else:
            print("❌ No data returned - API may be inactive or quota exhausted")
            return False
            
    except Exception as e:
        print(f"❌ Candid Essentials API Error: {str(e)}")
        return False

def test_candid_news():
    """Test Candid News API - Foundation and grant news"""
    print("\n" + "="*60)
    print("🔥 TESTING CANDID NEWS API (Premium Foundation News)")
    print("="*60)
    
    try:
        # Test environment variable
        api_key = os.environ.get('CANDID_NEWS_KEYS')
        if not api_key:
            print("❌ CANDID_NEWS_KEYS not found in environment")
            return False
        
        print(f"✅ API Key loaded: {api_key[:8]}...{api_key[-4:]}")
        
        # Test with both client implementations
        print("\n📍 Testing news search with NewsClient...")
        news_client = NewsClient()
        results = news_client.search("foundation grant", page=1, size=5)
        
        if results and len(results) > 0:
            print(f"✅ REAL NEWS DATA RETRIEVED: {len(results)} articles!")
            for i, article in enumerate(results[:3], 1):
                print(f"   {i}. {article.get('title', 'No title')[:60]}...")
                print(f"      Source: {article.get('site_name', 'N/A')}")
                print(f"      Date: {article.get('publication_date', 'N/A')}")
            return True
        else:
            print("❌ No news data returned")
            return False
            
    except Exception as e:
        print(f"❌ Candid News API Error: {str(e)}")
        return False

def test_candid_grants():
    """Test Candid Grants API - Historical grant data"""
    print("\n" + "="*60)
    print("🔥 TESTING CANDID GRANTS API (Premium Historical Grants)")
    print("="*60)
    
    try:
        # Test environment variable
        api_key = os.environ.get('CANDID_GRANTS_KEYS')
        if not api_key:
            print("❌ CANDID_GRANTS_KEYS not found in environment")
            return False
        
        print(f"✅ API Key loaded: {api_key[:8]}...{api_key[-4:]}")
        
        # Test with GrantsClient
        print("\n📍 Testing grants summary...")
        grants_client = CandidGrantsClient()
        summary = grants_client.get_summary()
        
        if summary and isinstance(summary, dict):
            print("✅ REAL GRANTS SUMMARY RETRIEVED!")
            print(f"   Total Foundations: {summary.get('number_of_foundations', 'N/A'):,}")
            print(f"   Total Grants: {summary.get('number_of_grants', 'N/A'):,}")
            print(f"   Total Grant Value: ${summary.get('value_of_grants', 0)/1e9:.1f}B")
            
            # Test grant search
            print("\n📍 Testing grants search...")
            grant_opportunities = grants_client.search_grants(keyword="education", limit=3)
            
            if grant_opportunities:
                print(f"✅ FOUNDATION OPPORTUNITIES: {len(grant_opportunities)} found!")
                for i, grant in enumerate(grant_opportunities[:3], 1):
                    print(f"   {i}. {grant.get('title', 'No title')}")
                    print(f"      Funder: {grant.get('funder', 'N/A')}")
                    print(f"      Amount: ${grant.get('amount_min', 0):,} - ${grant.get('amount_max', 0):,}")
            
            return True
        else:
            print("❌ No grants summary data returned")
            return False
            
    except Exception as e:
        print(f"❌ Candid Grants API Error: {str(e)}")
        return False

def run_premium_activation_test():
    """Run comprehensive test of all three premium Candid APIs"""
    print("🚀" * 20)
    print("PREMIUM CANDID API ACTIVATION TEST")
    print("User has invested hundreds of dollars in enterprise access")
    print("Testing all three APIs for real data retrieval...")
    print("🚀" * 20)
    
    # Disable demo mode to ensure real API calls
    os.environ['DEMO_MODE'] = 'false'
    os.environ['CANDID_ENABLED'] = 'true'
    
    # Test all three APIs
    essentials_success = test_candid_essentials()
    news_success = test_candid_news()
    grants_success = test_candid_grants()
    
    # Summary report
    print("\n" + "="*60)
    print("🎯 PREMIUM API ACTIVATION SUMMARY")
    print("="*60)
    
    total_apis = 3
    successful_apis = sum([essentials_success, news_success, grants_success])
    
    print(f"✅ Candid Essentials API: {'ACTIVE' if essentials_success else 'FAILED'}")
    print(f"✅ Candid News API: {'ACTIVE' if news_success else 'FAILED'}")  
    print(f"✅ Candid Grants API: {'ACTIVE' if grants_success else 'FAILED'}")
    
    print(f"\n🔥 ACTIVATION STATUS: {successful_apis}/{total_apis} APIs ACTIVE")
    
    if successful_apis == total_apis:
        print("🎉 PREMIUM SYSTEM FULLY ACTIVATED!")
        print("✅ All Candid APIs pulling real foundation data")
        print("✅ Ready for 70-source scraper execution")
        print("✅ Enterprise-level ROI confirmed")
        return True
    elif successful_apis > 0:
        print("⚠️  PARTIAL ACTIVATION - Some APIs working")
        print("🔧 Investigate failed APIs for full activation")
        return False
    else:
        print("❌ ACTIVATION FAILED - No APIs responding")
        print("🚨 Check API keys and network connectivity")
        return False

if __name__ == "__main__":
    success = run_premium_activation_test()
    
    if success:
        print("\n🚀 READY FOR NEXT STEP: Execute 70-source foundation scraper!")
        print("   Command: cd server && node run_complete_scrape.js")
    else:
        print("\n🔧 Fix API issues before proceeding to scraper execution")
    
    sys.exit(0 if success else 1)