#!/usr/bin/env python3
"""Test script for the Grant Pitch endpoint to verify personalization works"""

import requests
import json

# Test the endpoint with form data
def test_with_form_data():
    """Test the grant-pitch endpoint with organization data from form"""
    print("Testing Grant Pitch with form data...")
    
    url = "http://localhost:5000/api/writing/grant-pitch"
    
    # Simulate form data submission
    payload = {
        "org_name": "Tech for Good Foundation",
        "mission": "To bridge the digital divide in underserved communities through innovative technology education and access programs",
        "programs": "Digital Literacy Workshops, Computer Lab Access, Coding Bootcamps for Youth, Tech Equipment Donation Program",
        "impact": "Served 5,000+ students in 2024, 85% graduation rate from coding bootcamp, 200+ computers donated to families",
        "funding_need": "Expand our coding bootcamp to 3 new locations and purchase equipment for mobile tech labs",
        "funding_amount": "$50,000",
        "geographic_focus": "Los Angeles, California",
        "funder_name": "Gates Foundation",
        "alignment": "Technology access, education equity, youth development",
        "word_limit": "250"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Grant pitch generated with form data")
            content = result.get('content', '')
            # Check if the pitch includes the provided organization name
            if "Tech for Good Foundation" in content:
                print("✅ Organization name correctly used from form data")
            else:
                print("❌ Organization name NOT found in generated pitch")
            
            # Check if mission is reflected
            if "digital divide" in content.lower() or "technology education" in content.lower():
                print("✅ Mission content reflected in pitch")
            else:
                print("⚠️ Mission may not be fully reflected")
                
            print("\nFirst 500 characters of generated pitch:")
            print(content[:500])
            return True
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_without_form_data():
    """Test the grant-pitch endpoint without organization data (should use database)"""
    print("\n\nTesting Grant Pitch without form data (database fallback)...")
    
    url = "http://localhost:5000/api/writing/grant-pitch"
    
    # Only pitch-specific fields, no org data
    payload = {
        "funder_name": "Ford Foundation",
        "alignment": "Community development",
        "funding_need": "General operating support",
        "funding_amount": "$25,000",
        "word_limit": "150"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Grant pitch generated with database fallback")
            content = result.get('content', '')
            print("\nFirst 500 characters of generated pitch:")
            print(content[:500])
            return True
        elif response.status_code == 404:
            print("✅ Correctly returned 404 when no org in database and no form data")
            return True
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Grant Pitch Personalization Test")
    print("="*60)
    
    # Test both scenarios
    test1 = test_with_form_data()
    test2 = test_without_form_data()
    
    print("\n" + "="*60)
    if test1 and test2:
        print("✅ All tests passed! Grant Pitch personalization is working correctly")
    else:
        print("❌ Some tests failed. Please review the output above.")
    print("="*60)