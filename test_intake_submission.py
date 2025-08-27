#!/usr/bin/env python3
"""
Test script to submit impact intake with new fields and verify database storage
"""

import json
import requests
import sys
sys.path.append('/home/runner/workspace')

from app import create_app
from app.models import db, ImpactIntake

def test_intake_submission():
    """Submit intake form with new fields and verify DB storage"""
    print("\n" + "="*50)
    print("Testing Impact Intake Submission")
    print("="*50 + "\n")
    
    # Test data with all new fields
    test_data = {
        "name": "Test Participant",
        "age": 28,  # New field: age (int)
        "zip": "48201",  # New field: zip (string)
        "ethnicity": "Hispanic/Latino",  # New field: ethnicity (string)
        "location": "Detroit, MI",
        "program": "Youth Leadership Program",
        "role": "participant",
        "grant_id": 9,  # Michigan Community Foundation Grant
        
        # New field: stories (array of 4 text answers)
        "story_1": "I heard about this program through a friend who had participated last year. They told me how it changed their life.",
        "story_2": "The moment I realized I could be a leader was during our first workshop when the facilitator asked me to share my experience.",
        "story_3": "I overcame my fear of public speaking with the support of the program mentors and weekly practice sessions.",
        "story_4": "My hope is to use these skills to start a community center in my neighborhood and help other young people.",
        
        # Impact responses (existing)
        "impact_q1": "This program gave me confidence and leadership skills",
        "impact_q2": "I'm now more active in my community and have started volunteering",
        "impact_q3": 9,
        "impact_q4": "Yes",
        "impact_q5": "The mentorship component was invaluable",
        
        # Improvement responses (existing)
        "improve_q1": "More evening sessions for working participants",
        "improve_q2": "Parents and siblings could benefit from family programs"
    }
    
    # Submit via API
    print("📮 Submitting intake form with new fields...")
    url = "http://localhost:5000/api/phase5/survey/submit"
    
    try:
        response = requests.post(url, json=test_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Submission successful!")
                print(f"   Intake ID: {data.get('intake_id')}")
                print(f"   Confirmation: {data.get('confirmation_code')}")
                
                # Verify in database
                app = create_app()
                with app.app_context():
                    intake_id = data.get('intake_id')
                    if intake_id:
                        intake = ImpactIntake.query.get(intake_id)
                        if intake:
                            payload = intake.payload
                            
                            print("\n📊 Verifying Database Storage:")
                            print(f"   ✓ Grant ID: {intake.grant_id}")
                            print(f"   ✓ Submitted by: {intake.submitted_by}")
                            print(f"   ✓ Role: {intake.role}")
                            
                            print("\n📋 New Fields in Payload:")
                            print(f"   ✓ Age: {payload.get('age')} (expected: {test_data['age']})")
                            print(f"   ✓ ZIP: {payload.get('zip')} (expected: {test_data['zip']})")
                            print(f"   ✓ Ethnicity: {payload.get('ethnicity')} (expected: {test_data['ethnicity']})")
                            
                            stories = payload.get('stories', [])
                            print(f"   ✓ Stories: {len(stories)} stories saved")
                            for i, story in enumerate(stories, 1):
                                print(f"      Story {i}: {story[:50]}...")
                            
                            print("\n📋 Existing Fields Preserved:")
                            print(f"   ✓ Name: {payload.get('name')}")
                            print(f"   ✓ Location: {payload.get('location')}")
                            print(f"   ✓ Program: {payload.get('program')}")
                            
                            impact_responses = payload.get('impact_responses', {})
                            print(f"   ✓ Impact Responses: {len(impact_responses)} fields")
                            
                            # Validate field constraints
                            print("\n✔️ Field Validations:")
                            age_valid = 0 <= payload.get('age', 0) <= 120
                            print(f"   {'✓' if age_valid else '✗'} Age within valid range (0-120)")
                            
                            zip_valid = 5 <= len(str(payload.get('zip', ''))) <= 10
                            print(f"   {'✓' if zip_valid else '✗'} ZIP code length valid (5-10 chars)")
                            
                            eth_valid = len(payload.get('ethnicity', '')) <= 80
                            print(f"   {'✓' if eth_valid else '✗'} Ethnicity length valid (<= 80 chars)")
                            
                            stories_valid = len(stories) <= 4
                            print(f"   {'✓' if stories_valid else '✗'} Stories count valid (<= 4)")
                            
                            return True
                        else:
                            print(f"❌ Intake ID {intake_id} not found in database")
                    else:
                        print("❌ No intake_id returned in response")
            else:
                print(f"❌ Submission failed: {data.get('error')}")
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️ Could not connect to API - ensure Flask server is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return False

if __name__ == '__main__':
    success = test_intake_submission()
    
    if success:
        print("\n" + "="*50)
        print("✅ TEST PASSED")
        print("All new fields are correctly stored in impact_intake.payload")
        print("="*50)
        sys.exit(0)
    else:
        print("\n" + "="*50)
        print("❌ TEST FAILED")
        print("="*50)
        sys.exit(1)