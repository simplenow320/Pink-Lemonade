import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with a custom model class
db = SQLAlchemy(model_class=Base)

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Enable CORS
    CORS(app)
    
    # Configure the app
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SESSION_SECRET", "dev"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///grantflow.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
    )
    
    # Use ProxyFix for proper URL generation when behind proxies
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions with the app
    db.init_app(app)

    with app.app_context():
        # Import models
        from app.models import grant, organization, scraper, narrative, analytics
        
        # Create all tables in the database
        db.create_all()
        
        # Run database migrations
        from app.db_migrations.run_migrations import run_migrations
        run_migrations()
        
        # Import and register blueprints
        from app.api import grants, organization, scraper, ai, analytics
        app.register_blueprint(grants.bp)
        app.register_blueprint(organization.bp)
        app.register_blueprint(scraper.bp)
        app.register_blueprint(ai.bp)
        app.register_blueprint(analytics.bp)
        
        # Import and register main routes
        from app import routes
        app.register_blueprint(routes.bp)
        
        # Initialize the scheduler for automated scraping
        if not app.config.get('TESTING', False):
            from app.utils.scheduler import initialize_scheduler
            initialize_scheduler()

    return app
