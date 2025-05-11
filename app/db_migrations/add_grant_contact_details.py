"""
Migration to add enhanced contact and application details to the Grant table
"""

import logging
from sqlalchemy.sql import text

from app import db

# Configure logging
logger = logging.getLogger(__name__)

def run_migration():
    """
    Add enhanced contact and application details to the Grant table
    """
    logger.info("Starting migration to add enhanced contact and application details to Grant table")
    
    try:
        # Use direct SQL with commit to ensure changes are persisted
        with db.engine.begin() as conn:
            # Add contact_name column if it doesn't exist
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='grants' AND column_name='contact_name'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE grants ADD COLUMN contact_name VARCHAR(255)"))
                logger.info("Added contact_name column to grants table")
            else:
                logger.info("contact_name column already exists, skipping")
            
            # Add contact_email column if it doesn't exist
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='grants' AND column_name='contact_email'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE grants ADD COLUMN contact_email VARCHAR(255)"))
                logger.info("Added contact_email column to grants table")
            else:
                logger.info("contact_email column already exists, skipping")
                
            # Add contact_phone column if it doesn't exist
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='grants' AND column_name='contact_phone'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE grants ADD COLUMN contact_phone VARCHAR(100)"))
                logger.info("Added contact_phone column to grants table")
            else:
                logger.info("contact_phone column already exists, skipping")
                
            # Add submission_url column if it doesn't exist
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='grants' AND column_name='submission_url'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE grants ADD COLUMN submission_url VARCHAR(500)"))
                logger.info("Added submission_url column to grants table")
            else:
                logger.info("submission_url column already exists, skipping")
                
            # Add application_process column if it doesn't exist
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='grants' AND column_name='application_process'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE grants ADD COLUMN application_process TEXT"))
                logger.info("Added application_process column to grants table")
            else:
                logger.info("application_process column already exists, skipping")
                
            # Add grant_cycle column if it doesn't exist
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='grants' AND column_name='grant_cycle'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE grants ADD COLUMN grant_cycle VARCHAR(255)"))
                logger.info("Added grant_cycle column to grants table")
            else:
                logger.info("grant_cycle column already exists, skipping")
                
        # Refresh schema metadata
        db.metadata.clear()
        db.metadata.reflect(bind=db.engine)
        
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False