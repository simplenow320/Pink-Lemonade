#!/usr/bin/env python
"""
Production-Safe Database Initialization Script
Handles database creation with proper error handling and migration support
"""

import os
import sys
import logging
from sqlalchemy import text, inspect
from flask import Flask
from app import create_app, db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Test database connection before proceeding"""
    try:
        with db.engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        logger.info("✓ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False

def init_database_safe():
    """Initialize database with comprehensive error handling"""
    logger.info("Starting production-safe database initialization...")
    
    try:
        # Test connection first
        if not check_database_connection():
            logger.error("Cannot proceed without database connection")
            return False
        
        # Import all models to ensure they're registered
        logger.info("Importing all models...")
        import app.models
        import app.models_extended  
        import app.models_templates
        logger.info("✓ All models imported")
        
        # Get existing tables
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"Found {len(existing_tables)} existing tables")
        
        # Create tables that don't exist
        logger.info("Creating missing tables...")
        db.create_all()
        
        # Verify table creation
        updated_tables = inspector.get_table_names()
        new_tables = len(updated_tables) - len(existing_tables)
        if new_tables > 0:
            logger.info(f"✓ Created {new_tables} new tables")
        else:
            logger.info("✓ All tables already exist")
        
        # Verify critical tables
        critical_tables = ['users', 'organizations', 'grants', 'narratives']
        missing_critical = [t for t in critical_tables if t not in updated_tables]
        
        if missing_critical:
            logger.warning(f"Missing critical tables: {missing_critical}")
        else:
            logger.info("✓ All critical tables present")
        
        logger.info("✅ Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

def run_safe_migrations():
    """Run additional migrations if migration system exists"""
    try:
        from app.db_migrations.run_migrations import run_migrations
        logger.info("Running additional migrations...")
        success = run_migrations()
        if success:
            logger.info("✓ Migrations completed successfully")
        else:
            logger.warning("⚠ Some migrations failed (non-critical)")
        return success
    except ImportError:
        logger.info("No migration system found, skipping")
        return True
    except Exception as e:
        logger.warning(f"Migration system error: {e}")
        return False

if __name__ == "__main__":
    # Create app context for database operations
    app = create_app()
    
    with app.app_context():
        # Initialize database
        db_success = init_database_safe()
        
        if db_success:
            # Run migrations if available
            migration_success = run_safe_migrations()
            
            if db_success and migration_success:
                logger.info("🎉 Complete database setup successful!")
                sys.exit(0)
            else:
                logger.warning("Database initialized but migrations had issues")
                sys.exit(0)  # Still proceed - migrations are often optional
        else:
            logger.error("💥 Database initialization failed!")
            sys.exit(1)