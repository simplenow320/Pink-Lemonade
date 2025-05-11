"""
Migration to add search reporting columns to the Grant and ScraperHistory tables
"""

import logging
from sqlalchemy import Column, String, Integer, JSON, text
from sqlalchemy.exc import OperationalError

from app import db

# Configure logging
logger = logging.getLogger(__name__)

def run_migration():
    """
    Add search query and discovery method columns to the Grant table
    and search reporting columns to the ScraperHistory table
    """
    logger.info("Starting migration to add search reporting columns")
    
    # Add columns to the Grant table
    try:
        # Check if search_query column exists
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='grants' AND column_name='search_query'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE grants ADD COLUMN search_query VARCHAR(255)"))
                logger.info("Added search_query column to grants table")
            else:
                logger.info("search_query column already exists, skipping")
        
        # Check if discovery_method column exists
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='grants' AND column_name='discovery_method'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE grants ADD COLUMN discovery_method VARCHAR(50)"))
                logger.info("Added discovery_method column to grants table")
            else:
                logger.info("discovery_method column already exists, skipping")
                
        # Add columns to ScraperHistory table
        
        # sites_searched_estimate
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_history' AND column_name='sites_searched_estimate'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_history ADD COLUMN sites_searched_estimate INTEGER DEFAULT 0"))
                logger.info("Added sites_searched_estimate column to scraper_history table")
            else:
                logger.info("sites_searched_estimate column already exists, skipping")
        
        # total_queries_attempted
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_history' AND column_name='total_queries_attempted'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_history ADD COLUMN total_queries_attempted INTEGER DEFAULT 0"))
                logger.info("Added total_queries_attempted column to scraper_history table")
            else:
                logger.info("total_queries_attempted column already exists, skipping")
        
        # successful_queries
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_history' AND column_name='successful_queries'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_history ADD COLUMN successful_queries INTEGER DEFAULT 0"))
                logger.info("Added successful_queries column to scraper_history table")
            else:
                logger.info("successful_queries column already exists, skipping")
        
        # search_keywords_used (JSON column)
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scraper_history' AND column_name='search_keywords_used'"))
            if result.rowcount == 0:
                conn.execute(text("ALTER TABLE scraper_history ADD COLUMN search_keywords_used JSONB DEFAULT '[]'::jsonb"))
                logger.info("Added search_keywords_used column to scraper_history table")
            else:
                logger.info("search_keywords_used column already exists, skipping")
                
        logger.info("Migration completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False