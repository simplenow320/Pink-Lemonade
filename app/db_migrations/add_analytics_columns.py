"""
Database migration script to add analytics columns to the Grant table
"""

import logging
from app import db
from sqlalchemy import text

logger = logging.getLogger(__name__)

def run_migration():
    """
    Add date_submitted and date_decision columns to the Grant table
    """
    try:
        logger.info("Starting migration to add analytics columns to Grant table")
        
        # Check if the columns already exist
        conn = db.engine.connect()
        
        # Check for date_submitted column
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'grants' 
            AND column_name = 'date_submitted'
        """))
        count = result.scalar()
        date_submitted_exists = count is not None and count > 0
        
        # Check for date_decision column
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'grants' 
            AND column_name = 'date_decision'
        """))
        count = result.scalar()
        date_decision_exists = count is not None and count > 0
        
        # Add date_submitted column if it doesn't exist
        if not date_submitted_exists:
            logger.info("Adding date_submitted column to Grant table")
            conn.execute(text("""
                ALTER TABLE grants 
                ADD COLUMN date_submitted DATE
            """))
        else:
            logger.info("date_submitted column already exists, skipping")
        
        # Add date_decision column if it doesn't exist
        if not date_decision_exists:
            logger.info("Adding date_decision column to Grant table")
            conn.execute(text("""
                ALTER TABLE grants 
                ADD COLUMN date_decision DATE
            """))
        else:
            logger.info("date_decision column already exists, skipping")
        
        # Commit the transaction
        conn.commit()
        
        logger.info("Migration completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False