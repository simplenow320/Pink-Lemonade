"""
Add Phase 0 tables and columns
"""
from app import db
from sqlalchemy import text

def upgrade():
    """Add Phase 0 related columns and tables"""
    
    # Add custom_fields column to organizations table
    with db.engine.connect() as conn:
        # Check if column exists first
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='organizations' AND column_name='custom_fields'
        """))
        
        if not result.fetchone():
            conn.execute(text("ALTER TABLE organizations ADD COLUMN custom_fields JSON"))
            conn.commit()
            print("Added custom_fields column to organizations")
        
        # Create LovedGrant table if it doesn't exist
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name='loved_grants'
        """))
        
        if not result.fetchone():
            conn.execute(text("""
                CREATE TABLE loved_grants (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    grant_id INTEGER REFERENCES grants(id),
                    opportunity_data JSON,
                    status VARCHAR(50) DEFAULT 'interested',
                    notes TEXT,
                    loved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reminder_date TIMESTAMP,
                    progress_percentage INTEGER DEFAULT 0
                )
            """))
            conn.commit()
            print("Created loved_grants table")

def downgrade():
    """Remove Phase 0 related columns and tables"""
    with db.engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS loved_grants"))
        conn.execute(text("ALTER TABLE organizations DROP COLUMN IF EXISTS custom_fields"))
        conn.commit()

if __name__ == "__main__":
    upgrade()
    print("Phase 0 migration completed successfully")