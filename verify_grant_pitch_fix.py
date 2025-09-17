#!/usr/bin/env python3
"""Simple verification that Grant Pitch personalization fix is working"""

import requests
import json

print("Verifying Grant Pitch personalization fix...")
print("-" * 60)

# Test with custom organization data
test_data = {
    "org_name": "My Custom Organization",
    "mission": "Our unique mission statement",
    "programs": "Our specific programs",
    "impact": "Our measurable impact",
    "funding_need": "Our funding needs",
    "funder_name": "Test Funder",
    "alignment": "Our alignment areas"
}

url = "http://localhost:5000/api/writing/grant-pitch"

try:
    response = requests.post(url, json=test_data)
    
    if response.status_code == 200:
        result = response.json()
        content = result.get('content', '')
        
        # Check if custom organization name appears in the pitch
        if "My Custom Organization" in content:
            print("✅ SUCCESS: Grant Pitch is using form data!")
            print("   The custom organization name was found in the generated pitch.")
        else:
            print("❌ ISSUE: Custom organization name not found in pitch.")
            print("   The pitch might still be using database defaults.")
        
        # Show a snippet to verify
        print("\nGenerated pitch snippet:")
        print("-" * 40)
        print(content[:400] + "...")
        
    else:
        print(f"⚠️ Server returned status code: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error during test: {e}")

print("-" * 60)
print("Verification complete.")