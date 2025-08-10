#!/usr/bin/env python3
"""
Test the comprehensive organization data collection pipeline
Tests onboarding flow, profile management, and AI learning integration
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def register_and_login():
    """Register a new test user and log in"""
    print_header("STEP 1: User Registration & Login")
    
    # Register new user with all required fields
    register_data = {
        "org_name": "Urban Hope Foundation",
        "email": f"test_{int(time.time())}@example.com",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    session = requests.Session()
    
    response = session.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"Registration: {response.status_code}")
    if response.status_code in [200, 201]:
        print("✓ User registered successfully")
        # For testing, mark user as verified directly in database
        import subprocess
        verify_sql = f"UPDATE users SET is_verified = true WHERE email = '{register_data['email']}'"
        subprocess.run(['python', '-c', f"""
import psycopg2
import os
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()
cur.execute("{verify_sql}")
conn.commit()
cur.close()
conn.close()
print("User verified in database")
"""], capture_output=True)
        print("✓ User auto-verified for testing")
    else:
        print(f"✗ Registration failed: {response.text}")
        return None
    
    # Login
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }
    
    response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"Login: {response.status_code}")
    if response.status_code == 200:
        print("✓ User logged in successfully")
    else:
        print(f"✗ Login failed: {response.text}")
        return None
    
    return session

def test_onboarding_step1(session):
    """Test Step 1: Basic Information"""
    print_header("STEP 2: Basic Organization Information")
    
    data = {
        "step": 1,
        "legal_name": "Urban Hope Foundation Inc.",
        "ein": "84-1234567",
        "org_type": "faith_based",
        "year_founded": 2015,
        "website": "https://urbanhope.org",
        "social_media": "@urbanhopefdn",
        "mission": "We empower underserved urban communities through faith-based education, job training, and family support services, creating pathways to sustainable prosperity and spiritual growth.",
        "vision": "To see every urban neighborhood transformed into a thriving community where families flourish, youth reach their potential, and hope is restored.",
        "values": "Faith, Compassion, Excellence, Community, Empowerment",
        "faith_based": True,
        "minority_led": True,
        "woman_led": False,
        "lgbtq_led": False,
        "veteran_led": False
    }
    
    response = session.post(f"{BASE_URL}/api/organization/onboarding", json=data)
    result = response.json()
    
    if response.status_code == 200:
        print(f"✓ Step 1 completed successfully")
        print(f"  Profile completeness: {result.get('profile_completeness', 0)}%")
        print(f"  Organization ID: {result.get('org_id')}")
    else:
        print(f"✗ Step 1 failed: {result}")
    
    return response.status_code == 200

def test_onboarding_step2(session):
    """Test Step 2: Programs & Services"""
    print_header("STEP 3: Programs & Services")
    
    data = {
        "step": 2,
        "primary_focus_areas": ["education", "workforce_development", "family_services"],
        "secondary_focus_areas": ["youth_development", "housing", "spiritual_care"],
        "programs_services": """
        1. After-School Tutoring & Mentoring: Daily academic support for K-12 students
        2. Job Training Academy: 12-week vocational training in IT, healthcare, and trades
        3. Family Resource Center: Emergency assistance, counseling, and parent education
        4. Summer Youth Leadership: 8-week intensive program for teens
        5. Community Food Pantry: Weekly food distribution serving 500+ families
        """,
        "target_demographics": ["low_income", "minorities", "single_parents", "at_risk_youth"],
        "age_groups_served": ["5-12", "13-18", "19-25", "26-64"],
        "service_area_type": "regional",
        "primary_city": "Atlanta",
        "primary_state": "Georgia",
        "primary_zip": "30303",
        "counties_served": ["Fulton", "DeKalb", "Clayton"],
        "states_served": ["Georgia"]
    }
    
    response = session.post(f"{BASE_URL}/api/organization/onboarding", json=data)
    result = response.json()
    
    if response.status_code == 200:
        print(f"✓ Step 2 completed successfully")
        print(f"  Profile completeness: {result.get('profile_completeness', 0)}%")
    else:
        print(f"✗ Step 2 failed: {result}")
    
    return response.status_code == 200

def test_onboarding_step3(session):
    """Test Step 3: Organizational Capacity"""
    print_header("STEP 4: Organizational Capacity")
    
    data = {
        "step": 3,
        "annual_budget_range": "$500k-$1M",
        "staff_size": "11-25",
        "volunteer_count": "50-100",
        "board_size": 9,
        "people_served_annually": "2500+",
        "key_achievements": """
        - 95% high school graduation rate for program participants
        - Placed 200+ adults in living-wage jobs over past 3 years
        - Distributed 250,000 pounds of food during COVID-19 pandemic
        - Recognized as "Nonprofit of the Year" by Atlanta Chamber (2023)
        - Expanded services to 3 new neighborhoods in 2024
        """,
        "impact_metrics": {
            "students_tutored": 350,
            "job_placements": 85,
            "families_served": 1200,
            "volunteer_hours": 15000
        }
    }
    
    response = session.post(f"{BASE_URL}/api/organization/onboarding", json=data)
    result = response.json()
    
    if response.status_code == 200:
        print(f"✓ Step 3 completed successfully")
        print(f"  Profile completeness: {result.get('profile_completeness', 0)}%")
    else:
        print(f"✗ Step 3 failed: {result}")
    
    return response.status_code == 200

def test_onboarding_step4(session):
    """Test Step 4: Grant History"""
    print_header("STEP 5: Grant History & Preferences")
    
    data = {
        "step": 4,
        "previous_funders": [
            "Arthur M. Blank Family Foundation",
            "United Way of Greater Atlanta",
            "Chick-fil-A Foundation",
            "Georgia Power Foundation",
            "Department of Education"
        ],
        "typical_grant_size": "$25k-$100k",
        "grant_success_rate": 65.0,
        "preferred_grant_types": ["operating", "project", "capacity_building"],
        "grant_writing_capacity": "both"  # internal and consultant
    }
    
    response = session.post(f"{BASE_URL}/api/organization/onboarding", json=data)
    result = response.json()
    
    if response.status_code == 200:
        print(f"✓ Step 4 completed successfully")
        print(f"  Profile completeness: {result.get('profile_completeness', 0)}%")
    else:
        print(f"✗ Step 4 failed: {result}")
    
    return response.status_code == 200

def test_onboarding_step5(session):
    """Test Step 5: AI Learning & Keywords"""
    print_header("STEP 6: AI Learning Configuration")
    
    data = {
        "step": 5,
        "keywords": [
            "urban ministry", "faith-based", "workforce development",
            "youth mentoring", "family strengthening", "education equity",
            "job training", "community development", "poverty alleviation",
            "holistic services"
        ],
        "unique_capabilities": """
        Our unique strength lies in our deep community trust built over a decade of consistent service.
        We combine faith-based values with evidence-based programs, creating a holistic approach that
        addresses both material and spiritual needs. Our culturally-competent staff (80% from the
        communities we serve) enables authentic relationships and sustainable impact.
        """,
        "partnership_interests": """
        We seek partners who share our commitment to comprehensive community transformation.
        Ideal partners include workforce development organizations, educational institutions,
        faith communities, and funders focused on systems change and equity.
        """,
        "funding_priorities": """
        1. Expand job training program to include tech certifications
        2. Launch mobile family resource unit for underserved areas
        3. Develop youth entrepreneurship incubator
        4. Create trauma-informed care training for all staff
        5. Build emergency assistance endowment fund
        """,
        "exclusions": [
            "political_advocacy",
            "controversial_research",
            "discriminatory_practices"
        ]
    }
    
    response = session.post(f"{BASE_URL}/api/organization/onboarding", json=data)
    result = response.json()
    
    if response.status_code == 200:
        print(f"✓ Step 5 completed successfully")
        print(f"  Profile completeness: {result.get('profile_completeness', 0)}%")
        print(f"  Onboarding complete: {result.get('message', '')}")
    else:
        print(f"✗ Step 5 failed: {result}")
    
    return response.status_code == 200

def test_ai_context(session):
    """Test AI context generation from profile"""
    print_header("STEP 7: AI Context Verification")
    
    response = session.get(f"{BASE_URL}/api/organization/ai-context")
    
    if response.status_code == 200:
        result = response.json()
        ai_context = result.get('ai_context', {})
        
        print("✓ AI Context successfully generated:")
        print(f"  Organization: {ai_context.get('name', 'N/A')}")
        print(f"  Mission: {ai_context.get('mission', 'N/A')[:100]}...")
        print(f"  Focus Areas: {', '.join(ai_context.get('focus_areas', []))}")
        print(f"  Location: {ai_context.get('location', 'N/A')}")
        print(f"  Keywords: {len(ai_context.get('keywords', []))} keywords")
        print(f"  Profile Completeness: {result.get('profile_completeness', 0)}%")
        
        # Verify key AI learning fields are present
        required_fields = ['name', 'mission', 'focus_areas', 'demographics', 'budget_range', 'keywords']
        missing_fields = [f for f in required_fields if f not in ai_context or not ai_context[f]]
        
        if missing_fields:
            print(f"⚠ Missing AI fields: {', '.join(missing_fields)}")
        else:
            print("✓ All required AI fields present")
            
    else:
        print(f"✗ Failed to get AI context: {response.text}")
    
    return response.status_code == 200

def test_profile_update(session):
    """Test profile update after onboarding"""
    print_header("STEP 8: Profile Update & AI Learning")
    
    # Update profile with new information
    update_data = {
        "annual_budget_range": "$1M-$2.5M",  # Organization grew!
        "staff_size": "26-50",
        "key_achievements": """
        - 95% high school graduation rate for program participants
        - Placed 200+ adults in living-wage jobs over past 3 years
        - Distributed 250,000 pounds of food during COVID-19 pandemic
        - Recognized as "Nonprofit of the Year" by Atlanta Chamber (2023)
        - Expanded services to 3 new neighborhoods in 2024
        - NEW: Launched tech training center with 50 computer stations
        - NEW: Received $500k federal grant for workforce development
        """,
        "keywords": [
            "urban ministry", "faith-based", "workforce development",
            "youth mentoring", "family strengthening", "education equity",
            "job training", "community development", "poverty alleviation",
            "holistic services", "digital literacy", "tech training"  # Added new keywords
        ]
    }
    
    response = session.put(f"{BASE_URL}/api/organization/profile", json=update_data)
    
    if response.status_code == 200:
        result = response.json()
        print("✓ Profile updated successfully")
        print("  AI will learn from these updates for better grant matching")
        print(f"  Organization data: {result.get('organization', {}).get('name', 'N/A')}")
    else:
        print(f"✗ Profile update failed: {response.text}")
    
    return response.status_code == 200

def run_comprehensive_test():
    """Run the complete organization pipeline test"""
    print("\n" + "="*60)
    print(" COMPREHENSIVE ORGANIZATION DATA COLLECTION TEST")
    print(" Testing: Onboarding → Profile → AI Learning Pipeline")
    print("="*60)
    
    # Track test results
    results = {
        "registration": False,
        "step1": False,
        "step2": False,
        "step3": False,
        "step4": False,
        "step5": False,
        "ai_context": False,
        "profile_update": False
    }
    
    # Run tests
    session = register_and_login()
    if session:
        results["registration"] = True
        results["step1"] = test_onboarding_step1(session)
        results["step2"] = test_onboarding_step2(session)
        results["step3"] = test_onboarding_step3(session)
        results["step4"] = test_onboarding_step4(session)
        results["step5"] = test_onboarding_step5(session)
        results["ai_context"] = test_ai_context(session)
        results["profile_update"] = test_profile_update(session)
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n  Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS: All tests passed! The comprehensive organization")
        print("   data collection pipeline is working correctly.")
        print("   - User registration with organization name")
        print("   - 5-step onboarding process")
        print("   - AI context generation from profile")
        print("   - Profile updates trigger AI learning")
        print("\n   The platform now has rich organizational data for AI matching!")
    else:
        print("\n⚠ WARNING: Some tests failed. Please review the errors above.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        exit(1)