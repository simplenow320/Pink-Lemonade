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
    return render_template('opportunities.html', active='opportunities')

@bp.route('/grants')
def grants():
    """Grants page - show all available grants"""
    return render_template('grants.html', active='grants')

@bp.route('/grants/discovery')
def grants_discovery():
    """Grant discovery page"""
    return render_template('discovery.html', active='discovery')

@bp.route('/discovery')
def discovery():
    """Discovery page"""
    return render_template('discovery.html', active='discovery')

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

@bp.route('/r/<token>')
def public_intake(token):
    """Public intake form with token access"""
    # Pass the token to the React app via template
    return render_template('public_intake.html', token=token, active=None)

@bp.route('/clear-cache')
def clear_cache():
    """Cache clearing endpoint for production testing"""
    from flask import request, redirect, url_for, current_app
    import time
    
    # Update the cache version to force all static assets to refresh
    new_cache_version = str(int(time.time()))
    current_app.config['CACHE_VERSION'] = new_cache_version
    
    # Get the referring page or default to home
    referer = request.args.get('referer') or request.referrer or '/'
    
    # Parse the referer to get the route name
    from urllib.parse import urlparse
    parsed = urlparse(referer)
    redirect_path = parsed.path if parsed.path else '/'
    
    # Add cache-busting query parameters for immediate effect
    cache_buster = f"_cb={new_cache_version}"
    if '?' in redirect_path:
        redirect_url = f"{redirect_path}&{cache_buster}"
    else:
        redirect_url = f"{redirect_path}?{cache_buster}"
    
    # Set headers to prevent this redirect from being cached
    response = redirect(redirect_url)
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.must_revalidate = True
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@bp.route('/cache-status')
def cache_status():
    """Show current cache version for debugging"""
    from flask import jsonify, current_app
    import time
    return jsonify({
        'cache_version': current_app.config.get('CACHE_VERSION', 'not-set'),
        'timestamp': int(time.time()),
        'cache_clearing_url': '/clear-cache',
        'instructions': 'Visit /clear-cache to force cache refresh for all users'
    })

# Add other page routes as needed