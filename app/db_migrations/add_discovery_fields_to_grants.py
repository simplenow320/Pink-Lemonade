"""
Migration to add discovery-related fields to the Grant table
"""

from sqlalchemy import inspect, text
import logging

logger = logging.getLogger(__name__)

def run_migration(db=None):
    """Add discovery fields to the Grant table"""
    from app import db as app_db
    if db is None:
        db = app_db
    
    logger.info("Starting migration to add discovery fields to Grant table")
    
    try:
        # Check if the columns already exist
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('grants')]
        
        fields_to_add = [
            ('source_name', 'VARCHAR(200)'),
            ('source_url', 'VARCHAR(500)'),
            ('discovered_at', 'TIMESTAMP'),
            ('tags', 'JSON'),
            ('amount_min', 'FLOAT'),
            ('amount_max', 'FLOAT'),
            ('link', 'VARCHAR(500)'),
            ('deadline', 'TIMESTAMP')
        ]
        
        with db.engine.begin() as connection:
            for field_name, field_type in fields_to_add:
                if field_name not in columns:
                    logger.info(f"Adding {field_name} column to grants table")
                    connection.execute(text(f"""
                        ALTER TABLE grants
                        ADD COLUMN {field_name} {field_type};
                    """))
                    logger.info(f"{field_name} column added successfully")
                else:
                    logger.info(f"{field_name} column already exists, skipping")
        
        logger.info("Migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False