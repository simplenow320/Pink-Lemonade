#!/usr/bin/env python
"""Migration to create impact_intake table and indexes"""

from main import app
from app import db
from app.models import ImpactIntake
from sqlalchemy import text, inspect

def migrate_up():
    """Create impact_intake table and indexes"""
    with app.app_context():
        # Create the table using SQLAlchemy
        db.create_all()
        print("✓ Created/updated database tables")
        
        # Add indexes using raw SQL
        try:
            # Basic indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_impact_intake_grant_id 
                ON impact_intake (grant_id);
            """))
            print("✓ Created grant_id index")
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_impact_intake_created_at 
                ON impact_intake (created_at);
            """))
            print("✓ Created created_at index")
            
            # Expression indexes for JSONB fields (PostgreSQL specific)
            try:
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_impact_intake_payload_zip 
                    ON impact_intake ((payload->>'zip'));
                """))
                print("✓ Created payload->zip index")
                
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_impact_intake_payload_ethnicity 
                    ON impact_intake ((payload->>'ethnicity'));
                """))
                print("✓ Created payload->ethnicity index")
            except Exception as e:
                print(f"⚠ Could not create expression indexes (may not be supported): {e}")
            
            # Add role constraint
            try:
                db.session.execute(text("""
                    ALTER TABLE impact_intake 
                    ADD CONSTRAINT check_role_values 
                    CHECK (role IN ('staff', 'board', 'participant', 'other') OR role IS NULL);
                """))
                print("✓ Added role constraint")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("✓ Role constraint already exists")
                else:
                    print(f"⚠ Could not add role constraint: {e}")
            
            db.session.commit()
            print("✓ Migration UP complete")
            
            # Verify table structure
            inspector = inspect(db.engine)
            if 'impact_intake' in inspector.get_table_names():
                columns = inspector.get_columns('impact_intake')
                print(f"\n✓ Table 'impact_intake' has {len(columns)} columns:")
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
                
                indexes = inspector.get_indexes('impact_intake')
                print(f"\n✓ Table 'impact_intake' has {len(indexes)} indexes:")
                for idx in indexes:
                    print(f"  - {idx['name']}")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Migration failed: {e}")
            raise

def migrate_down():
    """Drop impact_intake table and indexes"""
    with app.app_context():
        try:
            # Drop indexes first
            db.session.execute(text("DROP INDEX IF EXISTS idx_impact_intake_grant_id CASCADE;"))
            db.session.execute(text("DROP INDEX IF EXISTS idx_impact_intake_created_at CASCADE;"))
            db.session.execute(text("DROP INDEX IF EXISTS idx_impact_intake_payload_zip CASCADE;"))
            db.session.execute(text("DROP INDEX IF EXISTS idx_impact_intake_payload_ethnicity CASCADE;"))
            print("✓ Dropped indexes")
            
            # Drop table
            db.session.execute(text("DROP TABLE IF EXISTS impact_intake CASCADE;"))
            print("✓ Dropped table impact_intake")
            
            db.session.commit()
            print("✓ Migration DOWN complete")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Rollback failed: {e}")
            raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        print("Running migration DOWN...")
        migrate_down()
    else:
        print("Running migration UP...")
        migrate_up()