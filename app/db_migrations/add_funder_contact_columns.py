"""
Migration to add contact information columns to the ScraperSource table
"""

import logging
from sqlalchemy.sql import text

from app import db

# Configure logging
logger = logging.getLogger(__name__)

def run_migration():
    """
    Add contact information columns to the ScraperSource table
    """
    logger.info("Starting migration to add contact information columns to ScraperSource table")
    
    try:
        # Use direct SQL with commit to ensure changes are persisted
        with db.engine.begin() as conn:
            # Add location column if it doesn't exist
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_sources' AND column_name='location'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_sources ADD COLUMN location VARCHAR(100)"))
                logger.info("Added location column to scraper_sources table")
            else:
                logger.info("location column already exists, skipping")
            
            # Add phone column if it doesn't exist
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_sources' AND column_name='phone'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_sources ADD COLUMN phone VARCHAR(50)"))
                logger.info("Added phone column to scraper_sources table")
            else:
                logger.info("phone column already exists, skipping")
                
            # Add contact_email column if it doesn't exist
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_sources' AND column_name='contact_email'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_sources ADD COLUMN contact_email VARCHAR(100)"))
                logger.info("Added contact_email column to scraper_sources table")
            else:
                logger.info("contact_email column already exists, skipping")
                
            # Add contact_name column if it doesn't exist
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_sources' AND column_name='contact_name'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_sources ADD COLUMN contact_name VARCHAR(100)"))
                logger.info("Added contact_name column to scraper_sources table")
            else:
                logger.info("contact_name column already exists, skipping")
                
            # Add match_score column if it doesn't exist
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_sources' AND column_name='match_score'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_sources ADD COLUMN match_score INTEGER DEFAULT 0"))
                logger.info("Added match_score column to scraper_sources table")
            else:
                logger.info("match_score column already exists, skipping")
                
            # Add best_fit_initiatives column if it doesn't exist (JSON type)
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_sources' AND column_name='best_fit_initiatives'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_sources ADD COLUMN best_fit_initiatives JSONB DEFAULT '[]'::jsonb"))
                logger.info("Added best_fit_initiatives column to scraper_sources table")
            else:
                logger.info("best_fit_initiatives column already exists, skipping")
                
            # Add grant_programs column if it doesn't exist (JSON type)
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_sources' AND column_name='grant_programs'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_sources ADD COLUMN grant_programs JSONB DEFAULT '[]'::jsonb"))
                logger.info("Added grant_programs column to scraper_sources table")
            else:
                logger.info("grant_programs column already exists, skipping")
        
        # Refresh schema metadata
        db.metadata.clear()
        db.metadata.reflect(bind=db.engine)
        
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False