import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object("app.config.settings")
    
    CORS(flask_app, supports_credentials=True)
    db.init_app(flask_app)
    
    # Create tables within app context
    with flask_app.app_context():
        # Import models so they are registered
        import app.models
        import app.models_extended
        
        # Create all tables
        db.create_all()
    
    # Register blueprints
    from app.pages import pages as pages_bp
    from app.api.auth import bp as auth_bp, init_auth
    from app.api.analytics import bp as analytics_bp
    from app.api.dashboard import dashboard_bp
    from app.api.organization import bp as organization_bp
    from app.api.scraper import bp as scraper_bp
    from app.api.opportunities import bp as opportunities_bp
    from app.api.admin import admin_bp
    from app.api.scrape import bp as scrape_bp
    from app.api.ai_test import bp as ai_test_bp
    from app.api.writing import bp as writing_bp
    from app.api.exports import bp as exports_bp
    from app.api.profile import bp as profile_bp
    from app.api.simple_org import bp as simple_org_bp
    
    # Initialize authentication
    init_auth(flask_app)
    
    flask_app.register_blueprint(pages_bp)  # Register pages blueprint for page templates
    flask_app.register_blueprint(auth_bp)  # Register auth blueprint
    flask_app.register_blueprint(analytics_bp)
    flask_app.register_blueprint(dashboard_bp)
    flask_app.register_blueprint(organization_bp)
    flask_app.register_blueprint(scraper_bp)
    flask_app.register_blueprint(opportunities_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(scrape_bp, url_prefix='/api/scrape')
    flask_app.register_blueprint(ai_test_bp, url_prefix='/api/ai-test')
    flask_app.register_blueprint(writing_bp, url_prefix='/api/writing')
    flask_app.register_blueprint(exports_bp, url_prefix='/api/exports')
    flask_app.register_blueprint(profile_bp)
    flask_app.register_blueprint(simple_org_bp)
    
    # Register new AI endpoints
    from app.api.ai_endpoints import bp as ai_endpoints_bp
    flask_app.register_blueprint(ai_endpoints_bp)
    
    # Register live data integration endpoints
    from app.api.live_data import bp as live_data_bp
    flask_app.register_blueprint(live_data_bp)
    
    # Register onboarding journey endpoints
    from app.api.onboarding import onboarding_bp
    flask_app.register_blueprint(onboarding_bp)
    
    # Initialize monitoring
    from app.services.monitoring_service import init_monitoring
    init_monitoring(flask_app)
    
    # Add security headers
    from app.services.security_service import security
    @flask_app.after_request
    def add_security_headers(response):
        return security.add_security_headers(response)
    
    # Add template context processor for global template variables
    @flask_app.context_processor
    def inject_globals():
        import os, datetime
        env_mode = os.getenv("APP_DATA_MODE","LIVE").upper()
        return {
            "env_mode": env_mode,
            "current_year": datetime.datetime.utcnow().year,
            "logo_url": os.getenv("APP_LOGO_URL"),
            "active": None
        }
    

    
    # Start scheduler only in production
    if os.environ.get('FLASK_ENV') == 'production':
        from app.utils.scheduler import start_scheduler
        start_scheduler()
    
    return flask_app