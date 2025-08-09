"""
Add AI matching fields to Grant table
"""

import logging
from sqlalchemy import text
from app import db

logger = logging.getLogger(__name__)

def run_migration():
    """Add match_score and match_reason columns to Grant table"""
    try:
        logger.info("Starting migration to add AI matching fields to Grant table")
        
        # Get the actual table name (might be 'grants' not 'grant')
        from app.models.grant import Grant
        table_name = Grant.__tablename__
        
        # Check if columns exist before adding
        inspector = db.inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        with db.engine.connect() as conn:
            # Add match_score column if it doesn't exist
            if 'match_score' not in existing_columns:
                conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN match_score INTEGER'))
                conn.commit()
                logger.info("Added match_score column")
            else:
                logger.info("match_score column already exists, skipping")
            
            # Add match_reason column if it doesn't exist
            if 'match_reason' not in existing_columns:
                conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN match_reason TEXT'))
                conn.commit()
                logger.info("Added match_reason column")
            else:
                logger.info("match_reason column already exists, skipping")
        
        logger.info("Migration completed successfully")
        return True  # Return True to indicate success
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        raise