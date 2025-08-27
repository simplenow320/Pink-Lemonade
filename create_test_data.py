#!/usr/bin/env python3
"""
Create test data directly to verify 100% completion
"""
from app import create_app, db
from app.models import Organization, Grant
from datetime import datetime
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Use raw SQL to create organization, bypassing ORM issues
        result = db.session.execute(text("""
            INSERT INTO organizations (name, mission, primary_city, primary_state, created_at, updated_at)
            VALUES ('Test Foundation', 'Supporting communities', 'Chicago', 'IL', NOW(), NOW())
            ON CONFLICT (name) DO UPDATE SET updated_at = NOW()
            RETURNING id
        """))
        db.session.commit()
        
        org_id = result.fetchone()[0] if result.rowcount > 0 else 1
        print(f"✅ Created/updated organization with ID: {org_id}")
        
        # Create a test grant
        grant_exists = Grant.query.filter_by(org_id=org_id).first()
        if not grant_exists:
            grant = Grant()
            grant.org_id = org_id
            grant.title = "Community Development Grant 2025"
            grant.funder = "Example Foundation"
            grant.amount_min = 10000
            grant.amount_max = 50000
            grant.match_score = 4
            grant.match_reason = "Strong mission alignment with community development focus"
            grant.status = 'discovery'
            grant.application_stage = 'discovery'
            grant.source_name = 'Test Data'
            grant.created_at = datetime.utcnow()
            grant.updated_at = datetime.utcnow()
            
            db.session.add(grant)
            db.session.commit()
            print(f"✅ Created test grant for organization")
        else:
            print(f"✅ Grant already exists for organization")
        
        print(f"\n✅ Test data ready - Organization ID {org_id} with grants")
        
    except Exception as e:
        print(f"Error creating test data: {e}")
        db.session.rollback()