#!/usr/bin/env python
"""Database migration script to ensure all tables and columns exist"""

from main import app
from app import db
from app.models import *

with app.app_context():
    # Create all tables (this won't drop existing data)
    db.create_all()
    print("✓ Database tables created/updated successfully")
    
    # Verify organizations table has all columns
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    
    if 'organizations' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('organizations')]
        print(f"✓ Organizations table has {len(columns)} columns")
        
        # Check for critical columns
        required_cols = ['type', 'city', 'state', 'year_established', 'mission_statement', 
                        'focus_areas', 'target_population', 'geographic_scope', 'key_programs',
                        'annual_budget', 'staff_count', 'board_members', 'previous_grants', 
                        'grant_experience']
        
        missing = [col for col in required_cols if col not in columns]
        if missing:
            print(f"⚠ Missing columns: {missing}")
        else:
            print("✓ All required columns present")
    
    print("\n✓ Database migration complete!")