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
    
    # Add template context processor for env_mode and current_year
    @flask_app.context_processor
    def inject_env_mode():
        from app.services.mode import is_live
        from datetime import datetime
        return {
            'env_mode': 'LIVE' if is_live() else 'DEMO',
            'current_year': datetime.now().year
        }
    
    # Basic routes
    from flask import render_template
    
    @flask_app.route('/')
    def index():
        return render_template('index.html')
    
    @flask_app.route('/dashboard')
    def dashboard():
        from datetime import datetime, timedelta
        from app.services.mode import is_live
        
        # Initialize default stats
        stats = {
            'total': 0,
            'due_this_month': 0,
            'avg_fit': None,
            'submitted': 0
        }
        
        # Initialize empty top matches for DEMO mode or when no data available
        top_matches = []
        
        # In LIVE mode, try to get real data from database
        if is_live():
            try:
                from app.models import Grant
                
                # Get total opportunities count
                stats['total'] = Grant.query.count()
                
                # Get opportunities due this month
                now = datetime.now()
                month_end = (now + timedelta(days=30))
                due_this_month = Grant.query.filter(
                    Grant.deadline >= now,
                    Grant.deadline <= month_end
                ).count()
                stats['due_this_month'] = due_this_month
                
                # Get submitted count
                submitted = Grant.query.filter(
                    Grant.status.in_(['submitted', 'awarded', 'declined'])
                ).count()
                stats['submitted'] = submitted
                
                # Get average fit score
                grants_with_fit = Grant.query.filter(Grant.match_score.isnot(None)).all()
                if grants_with_fit:
                    avg_fit = sum(g.match_score for g in grants_with_fit) / len(grants_with_fit)
                    stats['avg_fit'] = f"{avg_fit:.1f}"
                
                # Get top matches (highest fit scores)
                top_grants = Grant.query.filter(
                    Grant.match_score.isnot(None)
                ).order_by(Grant.match_score.desc()).limit(5).all()
                
                for grant in top_grants:
                    top_matches.append({
                        'title': grant.title,
                        'funder': grant.funder,
                        'fit': grant.match_score,
                        'deadline': grant.deadline.strftime('%b %d, %Y') if grant.deadline else 'TBA',
                        'link': grant.link or '#'
                    })
            except Exception as e:
                # If database error, keep empty data
                print(f"Dashboard data error: {e}")
        
        return render_template('dashboard.html', stats=stats, top_matches=top_matches)
    
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