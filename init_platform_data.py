#!/usr/bin/env python
"""Initialize platform with essential data for testing"""

import os
import sys
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Organization, Grant

def init_data():
    """Initialize database with essential test data"""
    app = create_app()
    
    with app.app_context():
        # Clear existing data
        print("Clearing existing test data...")
        db.drop_all()
        db.create_all()
        
        # Create test organization
        print("Creating test organization...")
        org = Organization()
        org.name = "Hope Community Center"
        org.mission = "Empowering urban communities through education, job training, and family support services"
        org.description = "A faith-based nonprofit serving Detroit's inner city for over 20 years"
        org.website = "https://hopecommunity.org"
        org.ein = "12-3456789"
        org.address = "123 Main St, Detroit, MI 48201"
        org.phone = "(313) 555-0100"
        org.annual_budget = 500000
        org.staff_size = 15
        org.year_founded = 2003
        org.focus_areas = ["Education", "Youth Development", "Community Development", "Family Services"]
        org.keywords = ["urban ministry", "after-school programs", "job training", "food pantry"]
        org.tax_status = "501c3"
        db.session.add(org)
        db.session.commit()
        
        # Create test user
        print("Creating test user...")
        user = User()
        user.email = "admin@hopecommunity.org"
        user.username = "admin"
        user.set_password("Test123!")
        user.first_name = "Sarah"
        user.last_name = "Johnson"
        user.org_name = "Hope Community Center"
        user.org_id = str(org.id)
        user.role = "admin"
        user.is_active = True
        user.is_verified = True
        user.verified_at = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
        
        # Create sample grants
        print("Creating sample grants...")
        grants_data = [
            {
                "title": "Youth Development Initiative Grant",
                "funder": "William Davidson Foundation",
                "amount": 75000,
                "deadline": datetime.utcnow() + timedelta(days=45),
                "description": "Supporting programs that help youth develop life skills and achieve academic success",
                "eligibility": "501(c)(3) organizations serving youth in Michigan",
                "focus_area": "Youth Development",
                "source_url": "https://example.com/youth-grant",
                "status": "discovery"
            },
            {
                "title": "Community Impact Grant",
                "funder": "Kresge Foundation",
                "amount": 100000,
                "deadline": datetime.utcnow() + timedelta(days=60),
                "description": "Funding for community-based organizations addressing urban challenges",
                "eligibility": "Nonprofits in Detroit with proven community impact",
                "focus_area": "Community Development",
                "source_url": "https://example.com/community-grant",
                "status": "researching"
            },
            {
                "title": "Education Excellence Fund",
                "funder": "Skillman Foundation",
                "amount": 50000,
                "deadline": datetime.utcnow() + timedelta(days=30),
                "description": "Supporting innovative education programs in Detroit",
                "eligibility": "Organizations providing educational services to underserved youth",
                "focus_area": "Education",
                "source_url": "https://example.com/education-grant",
                "status": "writing"
            }
        ]
        
        for grant_data in grants_data:
            grant = Grant()
            grant.title = grant_data["title"]
            grant.funder = grant_data["funder"]
            grant.amount = grant_data["amount"]
            grant.deadline = grant_data["deadline"]
            grant.description = grant_data["description"]
            grant.eligibility = grant_data["eligibility"]
            grant.focus_area = grant_data["focus_area"]
            grant.source_url = grant_data["source_url"]
            grant.status = grant_data["status"]
            grant.organization_id = org.id
            grant.created_by = user.id
            grant.match_score = 85
            db.session.add(grant)
        
        db.session.commit()
        
        print("\n✅ Platform data initialized successfully!")
        print(f"  - Organization: {org.name}")
        print(f"  - User: {user.email} / Test123!")
        print(f"  - Grants: {len(grants_data)} sample grants created")
        print(f"  - Database: PostgreSQL connected")
        
        return True

if __name__ == "__main__":
    try:
        init_data()
    except Exception as e:
        print(f"Error initializing data: {e}")
        sys.exit(1)