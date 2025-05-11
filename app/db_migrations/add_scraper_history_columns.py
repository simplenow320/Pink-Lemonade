"""
Add additional columns to ScraperHistory table

This migration adds new columns to the ScraperHistory table for better tracking
of web search progress and results.
"""

import logging
import sqlalchemy as sa
from sqlalchemy.sql import text
from app import db

# Configure logging
logger = logging.getLogger(__name__)

def run_migration():
    """
    Run the migration to add web search tracking columns to ScraperHistory table
    """
    logger.info("Starting migration to add web search tracking columns to ScraperHistory table")
    
    with db.engine.connect() as connection:
        # Check for web_search_performed column
        if not column_exists(connection, 'scraper_history', 'web_search_performed'):
            logger.info("Adding web_search_performed column to scraper_history")
            connection.execute(text(
                "ALTER TABLE scraper_history ADD COLUMN web_search_performed BOOLEAN DEFAULT FALSE"
            ))
        else:
            logger.info("web_search_performed column already exists, skipping")
            
        # Check for web_search_status column
        if not column_exists(connection, 'scraper_history', 'web_search_status'):
            logger.info("Adding web_search_status column to scraper_history")
            connection.execute(text(
                "ALTER TABLE scraper_history ADD COLUMN web_search_status VARCHAR(50)"
            ))
        else:
            logger.info("web_search_status column already exists, skipping")
            
        # Check for sites_searched column
        if not column_exists(connection, 'scraper_history', 'sites_searched'):
            logger.info("Adding sites_searched column to scraper_history")
            connection.execute(text(
                "ALTER TABLE scraper_history ADD COLUMN sites_searched INTEGER DEFAULT 0"
            ))
        else:
            logger.info("sites_searched column already exists, skipping")
            
        # Check for queries_attempted column
        if not column_exists(connection, 'scraper_history', 'queries_attempted'):
            logger.info("Adding queries_attempted column to scraper_history")
            connection.execute(text(
                "ALTER TABLE scraper_history ADD COLUMN queries_attempted INTEGER DEFAULT 0"
            ))
        else:
            logger.info("queries_attempted column already exists, skipping")
            
    logger.info("Migration completed successfully")
    return True

def column_exists(connection, table_name, column_name):
    """
    Check if a column exists in a table
    
    Args:
        connection: SQLAlchemy connection
        table_name: Name of the table
        column_name: Name of the column
        
    Returns:
        bool: True if the column exists, False otherwise
    """
    inspector = sa.inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns