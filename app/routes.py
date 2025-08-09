"""
Flask routes for rendering pages
"""

from flask import Blueprint, render_template

bp = Blueprint('routes', __name__)

@bp.route('/opportunities')
def opportunities():
    """Render the opportunities page"""
    return render_template('opportunities.html')

# Add other page routes as needed