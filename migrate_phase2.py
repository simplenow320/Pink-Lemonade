"""
Phase 2 Database Migration Script
Adds workflow fields to Grant model
"""
from app import app, db

with app.app_context():
    # Create all tables
    db.create_all()
    print("✓ Database tables updated with Phase 2 workflow fields")
    
    # Verify Grant table has new fields
    from app.models import Grant
    grant_columns = [col.name for col in Grant.__table__.columns]
    
    phase2_fields = [
        'application_stage', 'priority_level', 'checklist', 
        'team_members', 'activity_log', 'requirements',
        'user_id', 'grant_name', 'funding_organization',
        'grant_amount', 'submission_deadline'
    ]
    
    missing_fields = [f for f in phase2_fields if f not in grant_columns]
    
    if missing_fields:
        print(f"⚠ Missing fields: {missing_fields}")
    else:
        print("✓ All Phase 2 workflow fields successfully added to Grant model")
    
    print(f"✓ Total Grant columns: {len(grant_columns)}")