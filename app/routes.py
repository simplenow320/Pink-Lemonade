"""
Flask routes for rendering pages
"""

from flask import Blueprint, render_template, redirect

bp = Blueprint('routes', __name__)

@bp.route('/')
def index():
    """Home page - show landing page"""
    return render_template('landing.html')

@bp.route('/dashboard')
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html')

@bp.route('/opportunities')
def opportunities():
    """Render the opportunities page"""
    return render_template('opportunities.html')

@bp.route('/profile')
def profile():
    """Render the profile page"""
    return render_template('profile.html')

@bp.route('/settings')
def settings():
    """Redirect settings to profile page"""
    from flask import redirect
    return redirect('/profile')

# Add other page routes as needed