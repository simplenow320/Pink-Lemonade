import os

# Database
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///grantflow.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Security
SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Session Configuration
SESSION_TYPE = "filesystem"
SESSION_PERMANENT = False
PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
SESSION_COOKIE_NAME = "grantflow_session"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Demo Mode Configuration
DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"
SCHEDULER_ENABLED = not DEMO_MODE  # Disable scheduler in demo mode

# Data sources in demo mode (only free APIs)
USE_CANDID_APIS = not DEMO_MODE  # Disable paid Candid APIs in demo mode
USE_FREE_GOVERNMENT_APIS = True  # Always enable free APIs