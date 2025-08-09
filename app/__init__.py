import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object("app.config.settings")  # keep your settings module

    CORS(flask_app, supports_credentials=True)
    db.init_app(flask_app)

    # Create tables within app context
    with flask_app.app_context():
        # Import models so they are registered
        import app.models
        
        # Create all tables
        db.create_all()

    # register blueprints - using existing API files
    from app.api.analytics import bp as analytics_bp
    from app.api.dashboard import dashboard_bp
    from app.api.organization import bp as organization_bp
    from app.api.scraper import bp as scraper_bp
    from app.api.opportunities import bp as opportunities_bp
    from app.api.admin import bp as admin_bp
    # from app.api.writing_assistant import bp as writing_bp  # Temporarily disabled due to syntax errors
    
    flask_app.register_blueprint(analytics_bp)
    flask_app.register_blueprint(dashboard_bp)
    flask_app.register_blueprint(organization_bp)
    flask_app.register_blueprint(scraper_bp)
    flask_app.register_blueprint(opportunities_bp)
    flask_app.register_blueprint(admin_bp)
    # app.register_blueprint(writing_bp)  # Temporarily disabled

    # Add template context processor for env_mode
    @flask_app.context_processor
    def inject_env_mode():
        from app.services.mode import is_live
        return {'env_mode': 'LIVE' if is_live() else 'DEMO'}

    # Add basic routes for serving templates
    from flask import render_template
    
    @flask_app.route('/')
    def index():
        return render_template('index.html')
    
    @flask_app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    # Start scheduler only in production
    if os.environ.get('FLASK_ENV') == 'production':
        from app.utils.scheduler import start_scheduler
        start_scheduler()

    # remove any "serve React for all routes" logic until the new React app is ready
    return flask_app
