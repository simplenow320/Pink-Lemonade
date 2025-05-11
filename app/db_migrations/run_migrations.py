"""
Database Migration Runner

This script runs all defined migrations in order.
"""

import logging
import importlib
from flask import current_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of migration modules to run, in order
MIGRATIONS = [
    'app.db_migrations.add_analytics_columns',
    'app.db_migrations.add_search_columns',
]

def run_migrations():
    """
    Run all database migrations
    
    Returns:
        bool: True if all migrations succeed, False otherwise
    """
    logger.info("Starting database migrations...")
    
    success = True
    
    for migration_module in MIGRATIONS:
        try:
            logger.info(f"Running migration: {migration_module}")
            
            # Import the migration module
            module = importlib.import_module(migration_module)
            
            # Run the migration
            result = module.run_migration()
            
            if result:
                logger.info(f"Migration {migration_module} completed successfully")
            else:
                logger.error(f"Migration {migration_module} failed")
                success = False
                
        except Exception as e:
            logger.error(f"Error running migration {migration_module}: {str(e)}")
            success = False
    
    if success:
        logger.info("All migrations completed successfully")
    else:
        logger.error("Some migrations failed")
    
    return success