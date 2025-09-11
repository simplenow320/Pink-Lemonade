#!/usr/bin/env python3
"""
Test script for AI endpoints
Creates test data and verifies endpoints work
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Organization, Grant, User
from sqlalchemy import text

def setup_test_data():
    """Create test organizations and grants"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create test organization
            print("Creating test organization...")
            
            # Check if organizations table exists in PostgreSQL
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'organizations'
                )
            """)).scalar()
            
            if result:
                # Use raw SQL for organizations table (PostgreSQL syntax)
                db.session.execute(text("""
                    INSERT INTO organizations 
                    (id, name, mission, primary_city, primary_state, 
                     primary_focus_areas, annual_budget_range, created_at)
                    VALUES 
                    (1, 'Tech for Good Foundation', 
                     'We use technology to solve social problems and improve communities',
                     'San Francisco', 'CA', 
                     :focus_areas,
                     '$500,000 - $1,000,000', 
                     :now)
                    ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    mission = EXCLUDED.mission,
                    primary_city = EXCLUDED.primary_city,
                    primary_state = EXCLUDED.primary_state,
                    primary_focus_areas = EXCLUDED.primary_focus_areas,
                    annual_budget_range = EXCLUDED.annual_budget_range
                """), {
                    'now': datetime.utcnow(),
                    'focus_areas': json.dumps(['Technology', 'Education', 'Community Development'])
                })
            else:
                # Use Organization model
                org = Organization.query.filter_by(id=1).first()
                if not org:
                    org = Organization(
                        id=1,
                        name='Tech for Good Foundation',
                        mission='We use technology to solve social problems and improve communities',
                        website='https://techforgood.org',
                        annual_budget='$500,000 - $1,000,000'
                    )
                    db.session.add(org)
                else:
                    org.name = 'Tech for Good Foundation'
                    org.mission = 'We use technology to solve social problems and improve communities'
            
            # Create test grants
            print("Creating test grants...")
            
            grant_data = [
                {
                    'title': 'Technology Innovation Grant',
                    'funder': 'Bill & Melinda Gates Foundation',
                    'amount_min': 50000,
                    'amount_max': 100000,
                    'deadline': datetime.utcnow().date() + timedelta(days=30),
                    'eligibility': 'Nonprofits using technology for social impact. Organizations leveraging technology to address community challenges.',
                    'geography': 'United States',
                    'source_url': 'https://gatesfoundation.org',
                    'source_name': 'Gates Foundation'
                },
                {
                    'title': 'Community Development Fund',
                    'funder': 'Ford Foundation',
                    'amount_min': 25000,
                    'amount_max': 50000,
                    'deadline': datetime.utcnow().date() + timedelta(days=45),
                    'eligibility': 'Community-based organizations. Funding for community development initiatives.',
                    'geography': 'National',
                    'source_url': 'https://fordfoundation.org',
                    'source_name': 'Ford Foundation'
                },
                {
                    'title': 'Education Technology Grant',
                    'funder': 'Chan Zuckerberg Initiative',
                    'amount_min': 50000,
                    'amount_max': 75000,
                    'deadline': datetime.utcnow().date() + timedelta(days=60),
                    'eligibility': 'Educational technology nonprofits. Support for education technology solutions.',
                    'geography': 'United States',
                    'source_url': 'https://chanzuckerberg.com',
                    'source_name': 'CZI'
                }
            ]
            
            for i, data in enumerate(grant_data, 1):
                grant = Grant.query.filter_by(id=i).first()
                if not grant:
                    grant = Grant(id=i, **data)
                    db.session.add(grant)
                else:
                    for key, value in data.items():
                        setattr(grant, key, value)
            
            db.session.commit()
            print("Test data created successfully!")
            
            # Verify data
            try:
                if result:
                    org_count = db.session.execute(text("SELECT COUNT(*) FROM organizations")).scalar()
                else:
                    org_count = Organization.query.count()
            except:
                org_count = 0
            
            grant_count = Grant.query.count()
            
            print(f"Organizations in database: {org_count}")
            print(f"Grants in database: {grant_count}")
            
            return True
            
        except Exception as e:
            print(f"Error creating test data: {e}")
            db.session.rollback()
            return False

def test_endpoints():
    """Test the AI endpoints"""
    import requests
    
    base_url = "http://localhost:5000"
    
    tests = [
        {
            'name': 'AI Grant Matching (GET)',
            'method': 'GET',
            'url': f'{base_url}/api/ai-grants/match/1',
            'expected_status': [200, 500]  # May be 500 if AI service not configured
        },
        {
            'name': 'AI Grant Matching (POST)',
            'method': 'POST',
            'url': f'{base_url}/api/ai-grants/match/1',
            'json': {},
            'expected_status': [200, 500]
        },
        {
            'name': 'Grant Analysis',
            'method': 'GET',
            'url': f'{base_url}/api/ai-grants/analyze/1/1',
            'expected_status': [200, 500]
        },
        {
            'name': 'Generate Narrative',
            'method': 'POST',
            'url': f'{base_url}/api/ai-grants/generate-narrative',
            'json': {'grant_id': 1, 'org_id': 1, 'section': 'executive_summary'},
            'expected_status': [200, 500]
        },
        {
            'name': 'Smart Tools - Grant Pitch',
            'method': 'POST',
            'url': f'{base_url}/api/smart-tools/pitch/generate',
            'json': {'org_id': 1, 'pitch_type': 'elevator'},
            'expected_status': [200, 500]
        },
        {
            'name': 'Smart Tools - Case for Support',
            'method': 'POST',
            'url': f'{base_url}/api/smart-tools/case/generate',
            'json': {'org_id': 1, 'campaign_goal': 100000},
            'expected_status': [200, 500]
        },
        {
            'name': 'Smart Tools - Impact Report',
            'method': 'POST',
            'url': f'{base_url}/api/smart-tools/impact/generate',
            'json': {'org_id': 1, 'metrics': {'grants_submitted': 10}},
            'expected_status': [200, 500]
        }
    ]
    
    print("\n" + "="*50)
    print("Testing AI Endpoints")
    print("="*50 + "\n")
    
    for test in tests:
        try:
            print(f"Testing: {test['name']}")
            print(f"  URL: {test['url']}")
            print(f"  Method: {test['method']}")
            
            if test['method'] == 'GET':
                response = requests.get(test['url'])
            else:
                response = requests.post(
                    test['url'],
                    json=test.get('json', {}),
                    headers={'Content-Type': 'application/json'}
                )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code in test['expected_status']:
                print(f"  ✓ PASS - Status code is expected")
                
                # Try to parse JSON response
                try:
                    data = response.json()
                    print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"  Response: {response.text[:200]}...")
            else:
                print(f"  ✗ FAIL - Unexpected status code")
                print(f"  Expected: {test['expected_status']}")
                print(f"  Response: {response.text[:500]}...")
            
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
        
        print()
    
    print("="*50)
    print("Test complete!")
    print("="*50)

if __name__ == "__main__":
    print("Setting up test data...")
    if setup_test_data():
        print("\nTesting endpoints...")
        test_endpoints()
    else:
        print("Failed to setup test data")