"""
Migration to add profile fields to Organization table
"""

import logging
from sqlalchemy import text
from app import db

logger = logging.getLogger(__name__)

def run_migration():
    """Add profile fields to Organization table"""
    try:
        logger.info("Starting migration to add profile fields to Organization table")
        
        # Check and add documents column (JSON text field)
        try:
            result = db.session.execute(text("SELECT documents FROM organizations LIMIT 1"))
            logger.info("documents column already exists, skipping")
        except:
            db.session.execute(text("ALTER TABLE organizations ADD COLUMN documents TEXT"))
            logger.info("Added documents column")
            db.session.commit()
        
        # Check and add location column
        try:
            result = db.session.execute(text("SELECT location FROM organizations LIMIT 1"))
            logger.info("location column already exists, skipping")
        except:
            db.session.execute(text("ALTER TABLE organizations ADD COLUMN location VARCHAR(255)"))
            logger.info("Added location column")
            db.session.commit()
        
        # Check and add annual_budget column
        try:
            result = db.session.execute(text("SELECT annual_budget FROM organizations LIMIT 1"))
            logger.info("annual_budget column already exists, skipping")
        except:
            db.session.execute(text("ALTER TABLE organizations ADD COLUMN annual_budget VARCHAR(100)"))
            logger.info("Added annual_budget column")
            db.session.commit()
        
        # Check and add ein column
        try:
            result = db.session.execute(text("SELECT ein FROM organizations LIMIT 1"))
            logger.info("ein column already exists, skipping")
        except:
            db.session.execute(text("ALTER TABLE organizations ADD COLUMN ein VARCHAR(20)"))
            logger.info("Added ein column")
            db.session.commit()
        
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.session.rollback()
        return False