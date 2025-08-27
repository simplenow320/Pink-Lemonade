#!/usr/bin/env python3
"""
Direct test of unified API endpoint
"""
import requests
import json

# Test the unified endpoint directly
url = "http://localhost:5000/api/matching/unified/1"

print("Testing unified matching endpoint...")
try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ SUCCESS! Unified endpoint working")
        print(f"Organization: {data.get('organization')}")
        print(f"Discovery stats: {data.get('discovery_stats')}")
        print(f"Features active: {data.get('features')}")
        print(f"Matches found: {len(data.get('top_matches', []))}")
        
        if data.get('top_matches'):
            print("\nTop match:")
            match = data['top_matches'][0]
            print(f"  Title: {match.get('title')}")
            print(f"  Score: {match.get('match_score')}")
            print(f"  Reason: {match.get('match_reason')}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"Error: {e}")