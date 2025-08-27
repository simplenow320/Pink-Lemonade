#!/usr/bin/env python
"""Detailed test of Candid API responses"""
import json
import sys
import requests
import os
sys.path.insert(0, '/home/runner/workspace')

def test_direct_api_call():
    """Test direct API calls to understand what's happening"""
    print("Testing Direct API Calls")
    print("=" * 50)
    
    # Test News API directly
    print("\n1. Testing News API directly:")
    news_key = os.environ.get('CANDID_NEWS_KEYS', 'dea86cce366d452a87b9b3a2e5eadbae')
    print(f"   Using API key: {news_key[:10]}...{news_key[-5:]}")
    
    try:
        response = requests.get(
            "https://api.candid.org/news/v1/articles",
            params={
                'search_terms': 'grant',
                'page_size': 1,
                'page': 1
            },
            headers={
                'Accept': 'application/json',
                'Subscription-Key': news_key
            },
            timeout=10
        )
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            print(f"   Data preview: {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"   Error Response: {response.text[:500]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test Grants API directly
    print("\n2. Testing Grants API directly:")
    grants_key = os.environ.get('CANDID_GRANTS_KEYS', '9178555867b84c8fbe9a828a77eaf953')
    print(f"   Using API key: {grants_key[:10]}...{grants_key[-5:]}")
    
    try:
        response = requests.get(
            "https://api.candid.org/grants/v1/transactions",
            params={
                'page': 1,
                'per_page': 1
            },
            headers={
                'Accept': 'application/json',
                'Subscription-Key': grants_key
            },
            timeout=10
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            if 'data' in data:
                print(f"   Data type: {type(data['data'])}")
                if isinstance(data['data'], dict):
                    print(f"   Data keys: {list(data['data'].keys())}")
            print(f"   Data preview: {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"   Error Response: {response.text[:500]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test Essentials API directly
    print("\n3. Testing Essentials API directly:")
    essentials_key = os.environ.get('CANDID_ESSENTIALS_KEY', '8b0f054101a24cd79a2f445632ec9ac2')
    print(f"   Using API key: {essentials_key[:10]}...{essentials_key[-5:]}")
    
    try:
        response = requests.get(
            "https://api.candid.org/essentials/v1/organizations",
            params={
                'search_terms': 'Gates Foundation',
                'page': 1,
                'page_size': 1
            },
            headers={
                'Accept': 'application/json',
                'Subscription-Key': essentials_key
            },
            timeout=10
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            print(f"   Data preview: {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"   Error Response: {response.text[:500]}")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    test_direct_api_call()