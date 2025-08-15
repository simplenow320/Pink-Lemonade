"""
PHASE 3: Analytics API Endpoints
"""
from flask import Blueprint, request, jsonify, session
from app.services.phase3_analytics_engine import phase3_analytics
import logging

logger = logging.getLogger(__name__)

phase3_bp = Blueprint('phase3_analytics', __name__)

@phase3_bp.route('/api/phase3/analytics/dashboard', methods=['GET'])
def get_dashboard():
    """Get executive analytics dashboard"""
    try:
        user_id = session.get('user_id', 1)
        result = phase3_analytics.get_executive_dashboard(user_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase3_bp.route('/api/phase3/analytics/success-metrics', methods=['GET'])
def get_success_metrics():
    """Get detailed success metrics"""
    try:
        user_id = session.get('user_id', 1)
        period_days = request.args.get('days', 365, type=int)
        
        result = phase3_analytics.calculate_success_metrics(user_id, period_days)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting success metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase3_bp.route('/api/phase3/analytics/predictions', methods=['POST'])
def get_predictions():
    """Generate predictions for a grant opportunity"""
    try:
        user_id = session.get('user_id', 1)
        grant_data = request.json
        
        result = phase3_analytics.generate_predictions(user_id, grant_data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase3_bp.route('/api/phase3/analytics/trends', methods=['GET'])
def get_trends():
    """Get historical trends analysis"""
    try:
        user_id = session.get('user_id', 1)
        months = request.args.get('months', 12, type=int)
        
        result = phase3_analytics.analyze_trends(user_id, months)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error analyzing trends: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase3_bp.route('/api/phase3/analytics/roi', methods=['GET'])
def get_roi():
    """Calculate ROI metrics"""
    try:
        user_id = session.get('user_id', 1)
        result = phase3_analytics.calculate_roi(user_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error calculating ROI: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase3_bp.route('/api/phase3/analytics/team', methods=['GET'])
def get_team_performance():
    """Get team performance metrics"""
    try:
        user_id = session.get('user_id', 1)
        result = phase3_analytics.get_team_performance(user_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting team performance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500