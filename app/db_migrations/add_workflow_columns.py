"""
Migration to add workflow-related columns to Grant table
"""

import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

def run(db):
    """Add attachments and reminders columns to Grant table"""
    logger.info("Starting migration to add workflow columns to Grant table")
    
    try:
        # Check if attachments column exists
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='grants' AND column_name='attachments'
        """))
        
        if not result.fetchone():
            logger.info("Adding attachments column")
            db.session.execute(text("""
                ALTER TABLE grants 
                ADD COLUMN attachments JSON
            """))
            db.session.commit()
            logger.info("attachments column added successfully")
        else:
            logger.info("attachments column already exists, skipping")
        
        # Check if reminders column exists
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='grants' AND column_name='reminders'
        """))
        
        if not result.fetchone():
            logger.info("Adding reminders column")
            db.session.execute(text("""
                ALTER TABLE grants 
                ADD COLUMN reminders JSON
            """))
            db.session.commit()
            logger.info("reminders column added successfully")
        else:
            logger.info("reminders column already exists, skipping")
            
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        db.session.rollback()
        raise