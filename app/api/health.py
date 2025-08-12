"""Health check API endpoints"""
from flask import Blueprint, jsonify
from app import db
import os

bp = Blueprint('health', __name__, url_prefix='/api')

@bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except:
        db_status = 'unhealthy'
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
        'version': '1.0.0'
    }), 200

@bp.route('/smart-tools/health', methods=['GET'])
def smart_tools_health():
    """Smart Tools health check"""
    return jsonify({
        'status': 'healthy',
        'tools': {
            'case_support': 'enabled',
            'grant_pitch': 'enabled',
            'impact_report': 'enabled',
            'writing_assistant': 'enabled',
            'analytics': 'enabled',
            'smart_reports': 'enabled'
        }
    }), 200

@bp.route('/ai/status', methods=['GET'])
def ai_status():
    """AI service status"""
    return jsonify({
        'enabled': bool(os.getenv('OPENAI_API_KEY')),
        'features': {
            'grant_extraction': True,
            'grant_matching': True,
            'narrative_generation': True,
            'text_improvement': True
        },
        'model': 'gpt-4o'
    }), 200