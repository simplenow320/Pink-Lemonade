"""
Migration to add user authentication tables
"""

import logging
from sqlalchemy import text
from app import db

logger = logging.getLogger(__name__)

def run_migration():
    """Add user authentication tables"""
    try:
        logger.info("Starting migration to add user authentication tables")
        
        # Create users table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(120) UNIQUE NOT NULL,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(256) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                org_id VARCHAR(100),
                role VARCHAR(50) DEFAULT 'member',
                is_active BOOLEAN DEFAULT TRUE,
                is_verified BOOLEAN DEFAULT FALSE,
                verification_token VARCHAR(100) UNIQUE,
                reset_token VARCHAR(100) UNIQUE,
                reset_token_expiry TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                phone VARCHAR(20),
                timezone VARCHAR(50) DEFAULT 'America/New_York',
                notification_preferences TEXT
            )
        """))
        logger.info("Created users table")
        
        # Create user_invites table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS user_invites (
                id SERIAL PRIMARY KEY,
                email VARCHAR(120) NOT NULL,
                org_id VARCHAR(100) NOT NULL,
                role VARCHAR(50) DEFAULT 'member',
                invited_by INTEGER,
                invite_token VARCHAR(100) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                accepted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invited_by) REFERENCES users(id)
            )
        """))
        logger.info("Created user_invites table")
        
        # Create indexes for better performance
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_invites_token ON user_invites(invite_token)"))
        
        db.session.commit()
        logger.info("Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.session.rollback()
        return False