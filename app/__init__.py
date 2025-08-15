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
        import app.models_templates

        
        # Create all tables
        db.create_all()
    
    # Register blueprints
    from app.pages import pages as pages_bp
    from app.api.auth import bp as auth_bp, init_auth
    from app.api.analytics import analytics_bp
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
    
    # Register organizations API for profile retrieval
    from app.api.organizations import bp as organizations_bp
    flask_app.register_blueprint(organizations_bp)
    
    # Register grant intelligence endpoints
    from app.api.grant_intelligence import intelligence_api
    flask_app.register_blueprint(intelligence_api)
    
    # Register grant analysis endpoints
    from app.api.grant_analysis import bp as grant_analysis_bp
    flask_app.register_blueprint(grant_analysis_bp)
    
    # Register new AI endpoints
    from app.api.ai_endpoints import bp as ai_endpoints_bp
    flask_app.register_blueprint(ai_endpoints_bp)
    
    # Register advanced AI matching endpoints
    from app.api.ai_matching import bp as ai_matching_bp
    flask_app.register_blueprint(ai_matching_bp)
    
    # Register AI optimization endpoints (Phase 1)
    try:
        from app.api.ai_optimization import ai_optimization_bp
        flask_app.register_blueprint(ai_optimization_bp)
    except ImportError:
        pass  # AI optimization not available yet
    
    # Register subscription management endpoints (Phase 2)
    try:
        from app.api.subscription import subscription_bp
        flask_app.register_blueprint(subscription_bp)
    except ImportError:
        pass  # Subscription management not available yet
    
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
    
    # Register AI grants endpoints with REACTO
    try:
        from app.api.ai_grants import ai_grants_bp
        flask_app.register_blueprint(ai_grants_bp, url_prefix='/api/ai-grants')
    except ImportError as e:
        print(f"AI grants blueprint not available: {e}")
    
    # Register Workflow Management endpoints
    try:
        from app.api.workflow import workflow_bp
        flask_app.register_blueprint(workflow_bp)
    except ImportError as e:
        print(f"Workflow blueprint not available: {e}")
    
    # Register Smart Tools endpoints (Phase 4)
    try:
        from app.api.smart_tools import smart_tools_bp
        flask_app.register_blueprint(smart_tools_bp)
    except ImportError as e:
        print(f"Smart Tools blueprint not available: {e}")
    
    # Register health check endpoints
    from app.api.health import bp as health_bp
    flask_app.register_blueprint(health_bp)
    
    # Register Smart Tools endpoints
    from app.api.smart_tools import bp as smart_tools_bp
    flask_app.register_blueprint(smart_tools_bp)
    
    # Register live data integration endpoints
    from app.api.live_data import bp as live_data_bp
    flask_app.register_blueprint(live_data_bp)
    
    # Register real grants API endpoints  
    from app.api.real_grants import real_grants_bp
    flask_app.register_blueprint(real_grants_bp)
    
    from app.api.live_grants import live_grants_bp
    flask_app.register_blueprint(live_grants_bp)
    
    # Register onboarding journey endpoints
    from app.api.onboarding import onboarding_bp
    flask_app.register_blueprint(onboarding_bp)
    
    # Register Phase 0 Smart Onboarding endpoints
    from app.api.phase0_onboarding import phase0_bp
    flask_app.register_blueprint(phase0_bp)
    
    # Register Phase 1 World-Class Matching endpoints
    from app.api.phase1_matching import phase1_bp
    flask_app.register_blueprint(phase1_bp)
    
    # Register Phase 2 Application Workflow endpoints
    from app.api.phase2_workflow import phase2_bp
    flask_app.register_blueprint(phase2_bp)
    
    # Register Phase 3 Analytics endpoints
    from app.api.phase3_analytics import phase3_bp
    flask_app.register_blueprint(phase3_bp)
    
    # Register Phase 4 AI Writer endpoints
    from app.api.phase4_writer import phase4_bp
    flask_app.register_blueprint(phase4_bp)
    
    # Register Phase 5 Impact Reporting endpoints
    from app.api.phase5_reporting import phase5_bp
    flask_app.register_blueprint(phase5_bp)
    
    # Register Payment API endpoints (Phase 3 of 100% Completion Plan)
    from app.api.payment import payment_bp
    flask_app.register_blueprint(payment_bp, url_prefix='/api/payment')
    
    # Register Smart Templates API endpoints (Phase 5 of 100% Completion Plan)
    from app.api.templates import templates_bp
    flask_app.register_blueprint(templates_bp)
    
    # Register Governance & Compliance API endpoints (Phase 6)
    from app.api.governance import governance_bp
    flask_app.register_blueprint(governance_bp, url_prefix='/api/governance')
    

    
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
    
    # Register Email Invitations blueprint for SendGrid integration
    from app.api.email_invitations import bp as email_invitations_bp
    flask_app.register_blueprint(email_invitations_bp)
    
    # Register new feature blueprints
    from app.api.grant_matching import bp as grant_matching_bp
    flask_app.register_blueprint(grant_matching_bp)
    
    from app.api.document_uploads import bp as document_uploads_bp
    flask_app.register_blueprint(document_uploads_bp)
    
    from app.api.team_collaboration import bp as team_collaboration_bp
    flask_app.register_blueprint(team_collaboration_bp)
    
    from app.api.email_notifications import bp as email_notifications_bp
    flask_app.register_blueprint(email_notifications_bp)
    
    # Register Candid API integration endpoints
    try:
        from app.api.candid import bp as candid_bp
        flask_app.register_blueprint(candid_bp)
    except ImportError:
        pass  # Candid API not yet available
    
    # Register Matching API endpoints
    from app.api.matching import matching_bp
    flask_app.register_blueprint(matching_bp)
    
    # Register Platform Stats API endpoints
    from app.api.platform_stats import bp as platform_stats_bp
    flask_app.register_blueprint(platform_stats_bp)
    
    # Register Opportunities API endpoints
    try:
        from app.api.opportunities import bp as opportunities_bp
        flask_app.register_blueprint(opportunities_bp)
    except ValueError:
        # Blueprint already registered
        pass
    
    # Register Demo Opportunities API
    from app.api.demo_opportunities import bp as demo_opportunities_bp
    flask_app.register_blueprint(demo_opportunities_bp)
    
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
    
    # Add specific route for /reports to redirect to /smart-tools
    @flask_app.route('/reports')
    def reports_redirect():
        from flask import redirect
        return redirect('/smart-tools')
    
    # Start scheduler only in production
    if os.environ.get('FLASK_ENV') == 'production':
        from app.utils.scheduler import start_scheduler
        start_scheduler()
    
    return flask_app