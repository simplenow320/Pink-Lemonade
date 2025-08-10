"""
Flask routes for rendering pages
"""

from flask import Blueprint, render_template, redirect

bp = Blueprint('routes', __name__)

@bp.route('/profile')
def profile():
    """Organization Profile page"""
    return render_template('profile.html', active='profile')

@bp.route('/')
def index():
    """Home page - show landing page"""
    return render_template('index.html', active='home')

@bp.route('/dashboard')
def dashboard():
    """Dashboard page"""
    from datetime import datetime, timedelta
    from app.services.mode import is_live
    from app.models import Grant
    
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
    
    return render_template('dashboard.html', stats=stats, top_matches=top_matches, active='dashboard')

@bp.route('/opportunities')
def opportunities():
    """Render the opportunities page"""
    return render_template('opportunities_new.html', active='opportunities')

@bp.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html', active='settings')

@bp.route('/saved')
def saved():
    """Saved grants page"""
    return render_template('saved.html', active='saved')

@bp.route('/applications')
def applications():
    """Applications page"""
    return render_template('applications.html', active='apps')

@bp.route('/login')
def login():
    """Login page"""
    return render_template('login.html', active=None)

@bp.route('/register')
def register():
    """Register page"""
    return render_template('register.html', active=None)

@bp.route('/reset-password')
def reset_password():
    """Password reset page"""
    return render_template('reset_password.html', active=None)

@bp.route('/grant/<int:grant_id>')
def grant_detail(grant_id):
    """Grant detail page"""
    from app.models import Grant
    grant = Grant.query.get_or_404(grant_id)
    return render_template('grant_detail.html', grant=grant, active='opportunities')

@bp.route('/smart-tools')
def smart_tools():
    """Smart Tools Dashboard page"""
    return render_template('smart_tools.html', active='smart-tools')

@bp.route('/smart-tools/<tool_id>')
def smart_tool_detail(tool_id):
    """Individual Smart Tool page"""
    return render_template('smart_tools.html', active='smart-tools', tool_id=tool_id)

@bp.route('/case-support')
def case_support():
    """Case for Support tool page"""
    return render_template('case_support_form.html', active='smart-tools')

@bp.route('/impact-report')
def impact_report():
    """Impact Report tool page"""
    return render_template('impact_report_form.html', active='smart-tools')

@bp.route('/grant-pitch')
def grant_pitch():
    """Grant Pitch tool page"""
    return render_template('grant_pitch_form.html', active='smart-tools')

# Add other page routes as needed