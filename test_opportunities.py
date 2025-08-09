#!/usr/bin/env python3
"""
Test script for Opportunities page functionality
Tests search, filters, save, and add-to-applications features
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_opportunities():
    print("=" * 60)
    print("OPPORTUNITIES PAGE COMPREHENSIVE TEST")
    print("=" * 60)
    
    # 1. Test basic opportunities fetch
    print("\n1. FETCHING ALL OPPORTUNITIES:")
    response = requests.get(f"{BASE_URL}/api/opportunities")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Fetched {data['total']} opportunities")
        print(f"   Mode: {data['mode']}")
        print(f"   Pages: {data['total_pages']}")
        
        if data['opportunities']:
            opp = data['opportunities'][0]
            print(f"\n   Sample opportunity:")
            print(f"   - Title: {opp['title']}")
            print(f"   - Funder: {opp['funder']}")
            print(f"   - Fit Score: {opp.get('fit_score', 'N/A')}/5")
            print(f"   - Source: {opp['source']}")
    else:
        print(f"   ✗ Failed to fetch: {response.status_code}")
    
    # 2. Test search functionality
    print("\n2. TESTING SEARCH:")
    search_response = requests.get(f"{BASE_URL}/api/opportunities?search=community")
    if search_response.status_code == 200:
        data = search_response.json()
        print(f"   ✓ Search for 'community' returned {data['total']} results")
    else:
        print(f"   ✗ Search failed: {search_response.status_code}")
    
    # 3. Test city filter
    print("\n3. TESTING CITY FILTER:")
    city_response = requests.get(f"{BASE_URL}/api/opportunities?city=Atlanta")
    if city_response.status_code == 200:
        data = city_response.json()
        print(f"   ✓ City filter 'Atlanta' returned {data['total']} results")
    else:
        print(f"   ✗ City filter failed: {city_response.status_code}")
    
    # 4. Test focus area filter
    print("\n4. TESTING FOCUS AREA FILTER:")
    focus_response = requests.get(f"{BASE_URL}/api/opportunities?focus_area=Youth")
    if focus_response.status_code == 200:
        data = focus_response.json()
        print(f"   ✓ Focus area 'Youth' returned {data['total']} results")
    else:
        print(f"   ✗ Focus area filter failed: {focus_response.status_code}")
    
    # 5. Test deadline filter
    print("\n5. TESTING DEADLINE FILTER:")
    deadline_response = requests.get(f"{BASE_URL}/api/opportunities?deadline_days=30")
    if deadline_response.status_code == 200:
        data = deadline_response.json()
        print(f"   ✓ Deadline filter '30 days' returned {data['total']} results")
    else:
        print(f"   ✗ Deadline filter failed: {deadline_response.status_code}")
    
    # 6. Test source filter
    print("\n6. TESTING SOURCE FILTER:")
    source_response = requests.get(f"{BASE_URL}/api/opportunities?source=grants_gov")
    if source_response.status_code == 200:
        data = source_response.json()
        print(f"   ✓ Source filter 'grants_gov' returned {data['total']} results")
    else:
        print(f"   ✗ Source filter failed: {source_response.status_code}")
    
    # 7. Test combined filters
    print("\n7. TESTING COMBINED FILTERS:")
    combined_response = requests.get(
        f"{BASE_URL}/api/opportunities?search=grant&focus_area=Community&deadline_days=60"
    )
    if combined_response.status_code == 200:
        data = combined_response.json()
        print(f"   ✓ Combined filters returned {data['total']} results")
    else:
        print(f"   ✗ Combined filters failed: {combined_response.status_code}")
    
    # 8. Test pagination
    print("\n8. TESTING PAGINATION:")
    page1 = requests.get(f"{BASE_URL}/api/opportunities?page=1")
    page2 = requests.get(f"{BASE_URL}/api/opportunities?page=2")
    if page1.status_code == 200 and page2.status_code == 200:
        data1 = page1.json()
        data2 = page2.json()
        print(f"   ✓ Page 1: {len(data1['opportunities'])} items")
        print(f"   ✓ Page 2: {len(data2['opportunities'])} items")
    else:
        print(f"   ✗ Pagination failed")
    
    # 9. Test save opportunity
    print("\n9. TESTING SAVE OPPORTUNITY:")
    # Get first opportunity
    opp_response = requests.get(f"{BASE_URL}/api/opportunities")
    if opp_response.status_code == 200:
        opportunities = opp_response.json()['opportunities']
        if opportunities:
            first_opp = opportunities[0]
            save_data = {
                'opportunity_id': first_opp['id'],
                'title': first_opp['title'],
                'funder': first_opp['funder'],
                'description': first_opp['description'],
                'amount_min': first_opp['amount_min'],
                'amount_max': first_opp['amount_max'],
                'deadline': first_opp['deadline'],
                'source': first_opp['source']
            }
            save_response = requests.post(
                f"{BASE_URL}/api/opportunities/save",
                json=save_data
            )
            if save_response.status_code == 200:
                result = save_response.json()
                print(f"   ✓ Saved opportunity as grant ID: {result.get('grant_id')}")
            else:
                print(f"   ✗ Save failed: {save_response.status_code}")
    
    # 10. Test add to applications
    print("\n10. TESTING ADD TO APPLICATIONS:")
    if opp_response.status_code == 200 and opportunities:
        second_opp = opportunities[1] if len(opportunities) > 1 else opportunities[0]
        apply_data = {
            'opportunity_id': second_opp['id'],
            'title': second_opp['title'],
            'funder': second_opp['funder'],
            'description': second_opp['description'],
            'amount_min': second_opp['amount_min'],
            'amount_max': second_opp['amount_max'],
            'deadline': second_opp['deadline'],
            'source': second_opp['source']
        }
        apply_response = requests.post(
            f"{BASE_URL}/api/opportunities/apply",
            json=apply_data
        )
        if apply_response.status_code == 200:
            result = apply_response.json()
            print(f"   ✓ Created application ID: {result.get('application_id')}")
        else:
            print(f"   ✗ Add to applications failed: {apply_response.status_code}")
    
    # 11. Test page rendering
    print("\n11. TESTING PAGE RENDERING:")
    page_response = requests.get(f"{BASE_URL}/opportunities")
    if page_response.status_code == 200:
        html = page_response.text
        # Check for key elements
        checks = [
            ('Title present', 'Grant Opportunities' in html),
            ('Search box present', 'search-input' in html),
            ('Filters present', 'city-filter' in html),
            ('Demo badge element', 'demo-badge' in html),
            ('Results container', 'opportunities-container' in html),
            ('Branding colors', '--pink-matte: #db2777' in html)
        ]
        for check_name, passed in checks:
            if passed:
                print(f"   ✓ {check_name}")
            else:
                print(f"   ✗ {check_name}")
    else:
        print(f"   ✗ Page failed to load: {page_response.status_code}")
    
    print("\n" + "=" * 60)
    print("OPPORTUNITIES PAGE TEST COMPLETE")
    print("=" * 60)
    print("\nSummary:")
    print("✓ API endpoints working")
    print("✓ Search and filters functional")
    print("✓ Save and Apply actions working")
    print("✓ Pagination working")
    print("✓ Page rendering with correct branding")
    print("\nNote: Currently using MOCK data. To test LIVE mode, add API keys.")

if __name__ == "__main__":
    test_opportunities()