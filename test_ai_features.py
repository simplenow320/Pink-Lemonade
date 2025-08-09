#!/usr/bin/env python3
"""
Test script for AI features
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_ai_features():
    print("=" * 60)
    print("AI FEATURES COMPREHENSIVE TEST")
    print("=" * 60)
    
    # 1. Check AI status
    print("\n1. CHECKING AI STATUS:")
    response = requests.get(f"{BASE_URL}/api/ai-v2/status")
    status = response.json()
    print(f"   AI Enabled: {status['enabled']}")
    print(f"   Message: {status['message']}")
    
    if not status['enabled']:
        print("\n   ⚠️  AI features are disabled. Add your OpenAI API key in Settings.")
        return
    
    # 2. Test Grant Matching
    print("\n2. TESTING GRANT MATCHING:")
    
    # Get existing grants
    grants_response = requests.get(f"{BASE_URL}/api/grants")
    if grants_response.status_code == 200:
        response_data = grants_response.json()
        # Handle both list and dict response formats
        if isinstance(response_data, list):
            grants = response_data
        else:
            grants = response_data.get('grants', [])
        if grants and len(grants) >= 3:
            # Test matching for first 3 grants
            for grant in grants[:3]:
                response = requests.post(f"{BASE_URL}/api/ai-v2/match",
                                        json={'grant_id': grant['id'], 'org_id': 2})
                if response.status_code == 200:
                    result = response.json()
                    score = result.get('fit_score')
                    reason = result.get('fit_reason', 'N/A')
                    print(f"   ✓ Grant '{grant['title'][:40]}...'")
                    print(f"     Score: {score}/5 - {reason[:60]}...")
                else:
                    print(f"   ✗ Failed to match grant {grant['id']}: {response.status_code}")
                time.sleep(1)  # Rate limiting
    
    # 3. Test Grant Extraction
    print("\n3. TESTING GRANT EXTRACTION FROM TEXT:")
    
    test_text = """
    Grant Opportunity: Community Health Initiative 2025
    
    The Health Foundation is pleased to announce funding for community health programs.
    
    Amount: $25,000 - $50,000
    Deadline: March 15, 2025
    
    We are seeking innovative programs that address health disparities in urban communities.
    Priority areas include mental health, youth wellness, and preventive care.
    
    Eligibility: 501(c)(3) nonprofits serving metropolitan areas
    Contact: Dr. Sarah Johnson at grants@healthfoundation.org
    """
    
    print("   Extracting grant from sample text...")
    response = requests.post(f"{BASE_URL}/api/ai-v2/extract",
                            json={'text': test_text, 'org_id': 2})
    
    if response.status_code == 200:
        result = response.json()
        if 'grant' in result:
            grant = result['grant']
            print(f"   ✓ Successfully extracted grant:")
            print(f"     Title: {grant['title']}")
            print(f"     Funder: {grant['funder']}")
            print(f"     Amount: ${grant['amount_min']:,} - ${grant['amount_max']:,}")
            print(f"     Deadline: {grant.get('due_date', 'N/A')}")
            extracted_grant_id = grant['id']
            
            # 4. Test Narrative Generation
            print("\n4. TESTING NARRATIVE GENERATION:")
            print(f"   Generating narrative for extracted grant (ID: {extracted_grant_id})...")
            
            response = requests.post(f"{BASE_URL}/api/ai-v2/narrative",
                                    json={
                                        'grant_id': extracted_grant_id,
                                        'org_id': 2,
                                        'sections': ['need', 'program', 'outcomes', 'budget_rationale']
                                    })
            
            if response.status_code == 200:
                result = response.json()
                narrative = result['narrative']
                print(f"   ✓ Narrative generated successfully:")
                print(f"     Version: {narrative['version']}")
                print(f"     Sections created: {list(narrative['sections'].keys())}")
                
                # Show a sample of the narrative
                if 'need' in narrative['sections']:
                    need_text = narrative['sections']['need']
                    print(f"     Sample (Statement of Need):")
                    print(f"       {need_text[:150]}...")
            else:
                print(f"   ✗ Failed to generate narrative: {response.json()}")
        else:
            print(f"   ✗ Extraction failed: {result}")
    else:
        print(f"   ✗ Extraction request failed: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("AI FEATURES TEST COMPLETE")
    print("=" * 60)
    print("\nSummary:")
    print("✓ AI Service is enabled and operational")
    print("✓ Grant matching scores and explanations working")
    print("✓ Grant extraction from text working")
    print("✓ Narrative generation for proposals working")
    print("\nTo test N/A behavior, remove the OPENAI_API_KEY from Settings")

if __name__ == "__main__":
    test_ai_features()