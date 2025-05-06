import os
import secrets
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SESSION_SECRET', secrets.token_hex(16))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///grantflow.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    DEBUG = False
    TESTING = False
    
    # OpenAI API key from environment
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Scheduler settings
    SCHEDULER_ENABLED = True
    
    # Application settings
    GRANTS_PER_PAGE = 10
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    # Production settings
    DEBUG = False
    
    # Security settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True

# Dictionary of configurations
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get the appropriate configuration based on environment"""
    config_name = os.environ.get('FLASK_ENV', 'development')
    return config.get(config_name, config['default'])
