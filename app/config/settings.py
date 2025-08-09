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

# OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")