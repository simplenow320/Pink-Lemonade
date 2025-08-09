"""
Migration to add org_id field to the Grant table
"""

from sqlalchemy import inspect, text
import logging

logger = logging.getLogger(__name__)

def run_migration(db=None):
    """Add org_id field to the Grant table for organization scoping"""
    from app import db as app_db
    if db is None:
        db = app_db
    
    logger.info("Starting migration to add org_id field to Grant table")
    
    try:
        # Check if the column already exists
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('grants')]
        
        if 'org_id' not in columns:
            logger.info("Adding org_id column to grants table")
            with db.engine.begin() as connection:
                connection.execute(text("""
                    ALTER TABLE grants
                    ADD COLUMN org_id VARCHAR(100);
                """))
            logger.info("org_id column added successfully")
        else:
            logger.info("org_id column already exists, skipping")
        
        logger.info("Migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False