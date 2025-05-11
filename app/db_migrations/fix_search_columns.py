"""
Fix migration for search reporting columns in the Grant and ScraperHistory tables
"""

import logging
from sqlalchemy import MetaData, Table, Column, String, Integer, JSON
from sqlalchemy.sql import text

from app import db

# Configure logging
logger = logging.getLogger(__name__)

def run_migration():
    """
    Fix the search query and discovery method columns in the Grant table
    and search reporting columns in the ScraperHistory table using a safer approach
    """
    logger.info("Starting fix migration for search reporting columns")
    
    try:
        # Use direct SQL with commit to ensure changes are persisted
        with db.engine.begin() as conn:
            # First check if the columns exist in the grants table
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='grants' AND column_name='search_query'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE grants ADD COLUMN search_query VARCHAR(255)"))
                logger.info("Added search_query column to grants table")
            
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='grants' AND column_name='discovery_method'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE grants ADD COLUMN discovery_method VARCHAR(50)"))
                logger.info("Added discovery_method column to grants table")
            
            # Now check for columns in the scraper_history table
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_history' AND column_name='sites_searched_estimate'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_history ADD COLUMN sites_searched_estimate INTEGER DEFAULT 0"))
                logger.info("Added sites_searched_estimate column to scraper_history table")
            
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_history' AND column_name='total_queries_attempted'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_history ADD COLUMN total_queries_attempted INTEGER DEFAULT 0"))
                logger.info("Added total_queries_attempted column to scraper_history table")
            
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_history' AND column_name='successful_queries'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_history ADD COLUMN successful_queries INTEGER DEFAULT 0"))
                logger.info("Added successful_queries column to scraper_history table")
            
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_history' AND column_name='search_keywords_used'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_history ADD COLUMN search_keywords_used JSONB DEFAULT '[]'::jsonb"))
                logger.info("Added search_keywords_used column to scraper_history table")
        
        # Refresh schema metadata
        db.metadata.clear()
        db.metadata.reflect(bind=db.engine)
        
        logger.info("Fix migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during fix migration: {str(e)}")
        return False