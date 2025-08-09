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
        
        # Create all tables
        db.create_all()
    
    # Register blueprints
    from app.api.analytics import bp as analytics_bp
    from app.api.dashboard import dashboard_bp
    from app.api.organization import bp as organization_bp
    from app.api.scraper import bp as scraper_bp
    from app.api.opportunities import bp as opportunities_bp
    from app.api.admin import bp as admin_bp
    from app.api.scrape import bp as scrape_bp
    from app.api.ai_test import bp as ai_test_bp
    
    flask_app.register_blueprint(analytics_bp)
    flask_app.register_blueprint(dashboard_bp)
    flask_app.register_blueprint(organization_bp)
    flask_app.register_blueprint(scraper_bp)
    flask_app.register_blueprint(opportunities_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(scrape_bp, url_prefix='/api/scrape')
    flask_app.register_blueprint(ai_test_bp, url_prefix='/api/ai')
    
    # Add template context processor for env_mode
    @flask_app.context_processor
    def inject_env_mode():
        from app.services.mode import is_live
        return {'env_mode': 'LIVE' if is_live() else 'DEMO'}
    
    # Basic routes
    from flask import render_template
    
    @flask_app.route('/')
    def index():
        return render_template('index.html')
    
    @flask_app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')
    
    @flask_app.route('/opportunities')
    def opportunities():
        return render_template('opportunities.html')
    
    @flask_app.route('/saved')
    def saved():
        return render_template('saved.html')
    
    @flask_app.route('/applications')
    def applications():
        return render_template('applications.html')
    
    @flask_app.route('/settings')
    def settings():
        return render_template('settings.html')
    
    # Start scheduler only in production
    if os.environ.get('FLASK_ENV') == 'production':
        from app.utils.scheduler import start_scheduler
        start_scheduler()
    
    return flask_app