from flask import Blueprint, render_template, redirect, url_for, jsonify, current_app

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')

@bp.route('/landing')
def landing():
    """Landing page for new visitors"""
    return render_template('landing.html')

@bp.route('/scraper')
def scraper():
    """Render the scraper page"""
    return render_template('scraper.html')

@bp.route('/grants')
@bp.route('/organization')
@bp.route('/dashboard')
@bp.route('/funders')
def spa_routes():
    """Route any SPA paths back to the index"""
    return render_template('index.html')

@bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0"
    })

@bp.app_errorhandler(404)
def page_not_found(e):
    """Handle 404 errors by returning the SPA index"""
    return render_template('index.html')

@bp.app_errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal server error",
        "message": str(e)
    }), 500
