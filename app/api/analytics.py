"""
Analytics API Endpoints for GrantFlow

This module provides API endpoints for grant success analytics and reporting.
"""

import logging
from flask import Blueprint, jsonify, request, abort, current_app as app
from sqlalchemy import func

from app import db
from app.models.grant import Grant
from app.models.analytics import GrantAnalytics, GrantSuccessMetrics
from app.services.analytics_service import (
    get_success_metrics,
    get_trend_data,
    get_category_comparison,
    get_grant_timeline,
    update_success_metrics
)
from app.api import log_request, log_response

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


@bp.route('/success-metrics', methods=['GET'])
def get_analytics_success_metrics():
    """
    Get grant success metrics for different time periods
    
    Query Parameters:
        period (str, optional): Time period - 'monthly', 'quarterly', 'yearly', 'all-time', or 'all'. Default: 'all'.
        limit (int, optional): Number of periods to return. Default: None (all periods).
        include_categories (bool, optional): Whether to include focus area categories. Default: true.
        
    Returns:
        Response: JSON response with success metrics data.
    """
    log_request('GET', '/api/analytics/success-metrics')
    
    try:
        period = request.args.get('period', 'all')
        limit = request.args.get('limit', None, type=int)
        include_categories = request.args.get('include_categories', 'true').lower() == 'true'
        
        result = get_success_metrics(period, limit, include_categories)
        
        log_response('/api/analytics/success-metrics', 200)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting success metrics: {str(e)}")
        log_response('/api/analytics/success-metrics', 500, str(e))
        return jsonify({"success": False, "error": "Failed to get success metrics"}), 500


@bp.route('/trends', methods=['GET'])
def get_analytics_trends():
    """
    Get trend data for analytics metrics over time
    
    Query Parameters:
        metric (str, optional): Metric to track - 'success_rate', 'total_funding_received', etc. Default: 'success_rate'.
        period (str, optional): Time period - 'monthly', 'quarterly', 'yearly'. Default: 'monthly'.
        months (int, optional): Number of periods to include. Default: 12.
        
    Returns:
        Response: JSON response with trend data.
    """
    log_request('GET', '/api/analytics/trends')
    
    try:
        metric = request.args.get('metric', 'success_rate')
        period = request.args.get('period', 'monthly')
        months = request.args.get('months', 12, type=int)
        
        result = get_trend_data(metric, period, months)
        
        log_response('/api/analytics/trends', 200)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting trend data: {str(e)}")
        log_response('/api/analytics/trends', 500, str(e))
        return jsonify({"success": False, "error": "Failed to get trend data"}), 500


@bp.route('/category-comparison', methods=['GET'])
def get_analytics_category_comparison():
    """
    Get comparison of success metrics across different focus areas/categories
    
    Returns:
        Response: JSON response with category comparison data.
    """
    log_request('GET', '/api/analytics/category-comparison')
    
    try:
        result = get_category_comparison()
        
        log_response('/api/analytics/category-comparison', 200)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting category comparison: {str(e)}")
        log_response('/api/analytics/category-comparison', 500, str(e))
        return jsonify({"success": False, "error": "Failed to get category comparison"}), 500


@bp.route('/grant-timeline/<int:grant_id>', methods=['GET'])
def get_analytics_grant_timeline(grant_id):
    """
    Get the timeline of status changes for a specific grant
    
    Path Parameters:
        grant_id (int): ID of the grant
        
    Returns:
        Response: JSON response with grant timeline data.
    """
    log_request('GET', f'/api/analytics/grant-timeline/{grant_id}')
    
    try:
        result = get_grant_timeline(grant_id)
        
        if not result["success"]:
            log_response(f'/api/analytics/grant-timeline/{grant_id}', 404, result.get("error"))
            return jsonify(result), 404
        
        log_response(f'/api/analytics/grant-timeline/{grant_id}', 200)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting grant timeline: {str(e)}")
        log_response(f'/api/analytics/grant-timeline/{grant_id}', 500, str(e))
        return jsonify({"success": False, "error": "Failed to get grant timeline"}), 500


@bp.route('/overview', methods=['GET'])
def get_analytics_overview():
    """
    Get a comprehensive overview of grant performance metrics
    
    Returns:
        Response: JSON response with overview data.
    """
    log_request('GET', '/api/analytics/overview')
    
    try:
        # Update metrics to ensure we have the latest data
        update_success_metrics()
        
        # Get success rates by period
        success_metrics = get_success_metrics('yearly', 3, False)
        
        # Get category comparison
        categories = get_category_comparison()
        
        # Get overall statistics
        total_grants = Grant.query.count()
        total_submitted = Grant.query.filter(Grant.status.in_(["Submitted", "Won", "Declined"])).count()
        total_won = Grant.query.filter_by(status="Won").count()
        
        # Calculate overall success rate
        overall_success_rate = 0
        if total_submitted > 0:
            overall_success_rate = (total_won / total_submitted) * 100
        
        # Get total funding won
        total_funding = db.session.query(func.sum(Grant.amount)).filter(
            Grant.status == "Won"
        ).scalar() or 0
        
        # Get average time to decision (days between submission and decision)
        avg_time_query = db.session.query(
            func.avg(
                func.julianday(GrantAnalytics.date_decision) - 
                func.julianday(GrantAnalytics.date_submitted)
            )
        ).filter(
            GrantAnalytics.date_decision.isnot(None),
            GrantAnalytics.date_submitted.isnot(None)
        )
        
        avg_time = avg_time_query.scalar() or 0
        
        # Assemble the overview data
        overview = {
            "success": True,
            "total_grants": total_grants,
            "total_submitted": total_submitted,
            "total_won": total_won,
            "overall_success_rate": overall_success_rate,
            "total_funding_won": total_funding,
            "avg_days_to_decision": round(avg_time),
            "success_metrics": success_metrics.get("metrics", []),
            "categories": categories.get("categories", []),
            "category_metrics": categories.get("metrics", {})
        }
        
        log_response('/api/analytics/overview', 200)
        return jsonify(overview)
    
    except Exception as e:
        logger.error(f"Error getting analytics overview: {str(e)}")
        log_response('/api/analytics/overview', 500, str(e))
        return jsonify({"success": False, "error": "Failed to get analytics overview"}), 500


@bp.route('/update-metrics', methods=['POST'])
def update_analytics_metrics():
    """
    Manually trigger an update of all success metrics
    
    Returns:
        Response: JSON response with update status.
    """
    log_request('POST', '/api/analytics/update-metrics')
    
    try:
        result = update_success_metrics()
        
        log_response('/api/analytics/update-metrics', 200)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error updating success metrics: {str(e)}")
        log_response('/api/analytics/update-metrics', 500, str(e))
        return jsonify({"success": False, "error": "Failed to update success metrics"}), 500