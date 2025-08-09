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
    """Settings page"""
    return render_template('settings.html')

@bp.route('/saved')
def saved():
    """Saved grants page"""
    return render_template('saved.html')

@bp.route('/applications')
def applications():
    """Applications page"""
    return render_template('applications.html')

@bp.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@bp.route('/register')
def register():
    """Register page"""
    return render_template('register.html')

@bp.route('/reset-password')
def reset_password():
    """Password reset page"""
    return render_template('reset_password.html')

# Add other page routes as needed