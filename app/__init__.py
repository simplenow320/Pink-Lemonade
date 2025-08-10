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
    from app.api.scraper import bp as scraper_bp
    from app.api.opportunities import bp as opportunities_bp
    from app.api.admin import admin_bp
    from app.api.scrape import bp as scrape_bp
    from app.api.ai_test import bp as ai_test_bp
    from app.api.writing import bp as writing_bp
    from app.api.exports import bp as exports_bp
    from app.api.profile import bp as profile_bp
    from app.api.simple_org import bp as simple_org_bp
    from app.api.user_settings import bp as user_settings_bp
    from app.api.grants import bp as grants_bp
    
    # Initialize authentication
    init_auth(flask_app)
    
    flask_app.register_blueprint(pages_bp)  # Register pages blueprint for page templates
    flask_app.register_blueprint(auth_bp)  # Register auth blueprint
    flask_app.register_blueprint(analytics_bp)
    flask_app.register_blueprint(dashboard_bp)
    
    # Register new organization API
    try:
        from app.api.organization import bp as organization_bp
        flask_app.register_blueprint(organization_bp, url_prefix='/api/organization')
    except ImportError:
        pass  # Organization API not yet available
    flask_app.register_blueprint(scraper_bp)
    flask_app.register_blueprint(opportunities_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(scrape_bp, url_prefix='/api/scrape')
    flask_app.register_blueprint(ai_test_bp, url_prefix='/api/ai-test')
    flask_app.register_blueprint(writing_bp, url_prefix='/api/writing')
    flask_app.register_blueprint(exports_bp, url_prefix='/api/exports')
    flask_app.register_blueprint(profile_bp)
    flask_app.register_blueprint(simple_org_bp)
    flask_app.register_blueprint(user_settings_bp)
    flask_app.register_blueprint(grants_bp, url_prefix='/api/grants')
    
    # Register grant intelligence endpoints
    from app.api.grant_intelligence import intelligence_api
    flask_app.register_blueprint(intelligence_api)
    
    # Register new AI endpoints
    from app.api.ai_endpoints import bp as ai_endpoints_bp
    flask_app.register_blueprint(ai_endpoints_bp)
    
    # Register advanced AI matching endpoints
    from app.api.ai_matching import bp as ai_matching_bp
    flask_app.register_blueprint(ai_matching_bp)
    
    # Register integration endpoints
    from app.api.integration import bp as integration_bp
    flask_app.register_blueprint(integration_bp)
    
    # Register automated monitoring endpoints
    from app.api.automated_monitoring import bp as monitoring_bp
    flask_app.register_blueprint(monitoring_bp)
    
    # Register notification enhancement endpoints
    from app.api.notification_enhancement import bp as notification_enhancement_bp
    flask_app.register_blueprint(notification_enhancement_bp)
    
    # Register production readiness endpoints
    from app.api.production_readiness import bp as production_bp
    flask_app.register_blueprint(production_bp)
    
    # Register deployment endpoints
    from app.api.deployment import bp as deployment_bp
    flask_app.register_blueprint(deployment_bp)
    
    # Register final completion endpoints
    from app.api.final_completion import bp as final_completion_bp
    flask_app.register_blueprint(final_completion_bp)
    
    # Register live data integration endpoints
    from app.api.live_data import bp as live_data_bp
    flask_app.register_blueprint(live_data_bp)
    
    # Register onboarding journey endpoints
    from app.api.onboarding import onboarding_bp
    flask_app.register_blueprint(onboarding_bp)
    
    # Register Smart Reporting endpoints
    from app.api.smart_reporting import bp as smart_reporting_bp
    flask_app.register_blueprint(smart_reporting_bp)
    
    # Register Smart Reporting Phase 2 blueprint
    from app.api.smart_reporting_phase2 import bp as smart_reporting_phase2_bp
    flask_app.register_blueprint(smart_reporting_phase2_bp)
    
    # Register Smart Reporting Phase 3 blueprint
    from app.api.smart_reporting_phase3 import bp as smart_reporting_phase3_bp
    flask_app.register_blueprint(smart_reporting_phase3_bp)
    
    # Register Smart Reporting Phase 4 blueprint
    from app.api.smart_reporting_phase4 import bp as smart_reporting_phase4_bp
    flask_app.register_blueprint(smart_reporting_phase4_bp)
    
    # Register Smart Reporting Phase 5 blueprint
    from app.api.smart_reporting_phase5 import bp as smart_reporting_phase5_bp
    flask_app.register_blueprint(smart_reporting_phase5_bp)
    
    # Register Smart Reporting Phase 6 blueprint
    from app.api.smart_reporting_phase6 import bp as smart_reporting_phase6_bp
    flask_app.register_blueprint(smart_reporting_phase6_bp)
    
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