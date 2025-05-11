import time
from flask import Blueprint, render_template, redirect, url_for, jsonify, current_app

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Render the modern application page"""
    return render_template('modern.html', now=int(time.time()))

@bp.route('/classic')
def classic_index():
    """Render the classic application page"""
    return render_template('index.html', now=int(time.time()))

@bp.route('/scraper')
def scraper():
    """Render the scraper page with modern UI"""
    return render_template('modern.html', page='scraper', now=int(time.time()))

@bp.route('/grants')
def grants_route():
    """Render the grants page with modern UI"""
    return render_template('modern.html', page='grants', now=int(time.time()))

@bp.route('/organization')
def organization_route():
    """Render the organization page with modern UI"""
    return render_template('modern.html', page='organization', now=int(time.time()))

@bp.route('/dashboard')
def dashboard_route():
    """Render the dashboard page with modern UI"""
    return render_template('modern.html', page='dashboard', now=int(time.time()))

@bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0"
    })

@bp.app_errorhandler(404)
def page_not_found(e):
    """Handle 404 errors by returning the modern UI"""
    return render_template('modern.html', now=int(time.time()))

@bp.app_errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal server error",
        "message": str(e)
    }), 500
