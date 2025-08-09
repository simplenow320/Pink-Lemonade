"""
Analytics API Endpoints for GrantFlow

This module provides API endpoints for grant success analytics and reporting.
"""

import logging
from flask import Blueprint, jsonify, request, abort, current_app as app
from sqlalchemy import func

from app import db
from app.models import Grant, GrantAnalytics, GrantSuccessMetrics
from app.services.analytics_service import (
    get_success_metrics,
    get_trend_data,
    get_category_comparison,
    get_grant_timeline,
    update_success_metrics
)
# Removed unused imports

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@bp.route('', methods=['GET'])
def get_analytics():
    """Get general analytics data"""
    try:
        # Calculate real analytics from database - no mock data allowed
        total_grants = Grant.query.count()
        submitted_grants = Grant.query.filter_by(status='submitted').count()
        won_grants = Grant.query.filter_by(status='won').count()
        
        success_rate = (won_grants / submitted_grants) if submitted_grants > 0 else 0
        total_awarded = db.session.query(func.sum(Grant.amount)).filter(Grant.status == 'won').scalar() or 0
        
        analytics = {
            'total_grants': total_grants,
            'total_applications': submitted_grants,
            'success_rate': success_rate,
            'total_awarded': total_awarded
        }
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/dashboard', methods=['GET'])
def get_dashboard_analytics():
    """Get dashboard-specific analytics"""
    try:
        # Calculate real dashboard analytics from database - no mock data allowed
        grants_by_status = {
            'discovered': Grant.query.filter_by(status='idea').count(),
            'saved': Grant.query.filter_by(status='saved').count(),
            'applied': Grant.query.filter_by(status='submitted').count(),
            'awarded': Grant.query.filter_by(status='won').count()
        }
        
        # Get recent activity (last 10 grants updated)
        recent_grants = Grant.query.order_by(Grant.updated_at.desc()).limit(10).all()
        recent_activity = [grant.to_dict() for grant in recent_grants]
        
        # Get upcoming deadlines (next 30 days)
        from datetime import datetime, timedelta
        upcoming_date = (datetime.now() + timedelta(days=30)).date()
        upcoming_grants = Grant.query.filter(
            Grant.due_date.isnot(None),
            Grant.due_date <= upcoming_date,
            Grant.due_date > datetime.now().date()
        ).order_by(Grant.due_date).all()
        upcoming_deadlines = [grant.to_dict() for grant in upcoming_grants]
        
        dashboard = {
            'grants_by_status': grants_by_status,
            'recent_activity': recent_activity,
            'upcoming_deadlines': upcoming_deadlines
        }
        return jsonify(dashboard)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
    logger.info("Request processed")
    
    try:
        period = request.args.get('period', 'all')
        limit = request.args.get('limit', None, type=int)
        include_categories = request.args.get('include_categories', 'true').lower() == 'true'
        
        result = get_success_metrics(period, limit, include_categories)
        
        logger.info("Response sent")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting success metrics: {str(e)}")
        logger.info("Response sent")
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
    logger.info("Request processed")
    
    try:
        metric = request.args.get('metric', 'success_rate')
        period = request.args.get('period', 'monthly')
        months = request.args.get('months', 12, type=int)
        
        result = get_trend_data(metric, period, months)
        
        logger.info("Response sent")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting trend data: {str(e)}")
        logger.info("Response sent")
        return jsonify({"success": False, "error": "Failed to get trend data"}), 500


@bp.route('/category-comparison', methods=['GET'])
def get_analytics_category_comparison():
    """
    Get comparison of success metrics across different focus areas/categories
    
    Returns:
        Response: JSON response with category comparison data.
    """
    logger.info("Request processed")
    
    try:
        result = get_category_comparison()
        
        logger.info("Response sent")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting category comparison: {str(e)}")
        logger.info("Response sent")
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
    logger.info("Request processed")
    
    try:
        result = get_grant_timeline(grant_id)
        
        if not result["success"]:
            logger.info("Response sent")
            return jsonify(result), 404
        
        logger.info("Response sent")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting grant timeline: {str(e)}")
        logger.info("Response sent")
        return jsonify({"success": False, "error": "Failed to get grant timeline"}), 500


@bp.route('/overview', methods=['GET'])
def get_analytics_overview():
    """
    Get a comprehensive overview of grant performance metrics
    
    Returns:
        Response: JSON response with overview data.
    """
    logger.info("Request processed")
    
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
        
        logger.info("Response sent")
        return jsonify(overview)
    
    except Exception as e:
        logger.error(f"Error getting analytics overview: {str(e)}")
        logger.info("Response sent")
        return jsonify({"success": False, "error": "Failed to get analytics overview"}), 500


@bp.route('/stats', methods=['GET'])
def get_basic_stats():
    """
    Get basic dashboard statistics
    
    Returns:
        Response: JSON response with basic stats.
    """
    logger.info('GET /api/analytics/stats')
    
    try:
        # Calculate basic statistics from database
        total_grants = Grant.query.count()
        
        # Count active applications (submitted status)
        active_applications = Grant.query.filter(
            Grant.status.in_(["Submitted", "In Progress", "Under Review"])
        ).count()
        
        # Count grants won
        grants_won = Grant.query.filter(
            Grant.status.in_(["Won", "Approved", "Funded"])
        ).count()
        
        # Calculate total funding received
        total_funding = db.session.query(func.sum(Grant.amount)).filter(
            Grant.status.in_(["Won", "Approved", "Funded"])
        ).scalar() or 0
        
        # Calculate success rate
        submitted_grants = Grant.query.filter(
            Grant.status.in_(["Submitted", "Won", "Approved", "Funded", "Declined", "Rejected"])
        ).count()
        
        success_rate = 0
        if submitted_grants > 0:
            success_rate = round((grants_won / submitted_grants) * 100, 1)
        
        stats = {
            "success": True,
            "total_grants": total_grants,
            "active_applications": active_applications,
            "grants_won": grants_won,
            "total_funding": float(total_funding),
            "success_rate": success_rate,
            "submitted_grants": submitted_grants
        }
        
        logger.info("Response sent")
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting basic stats: {str(e)}")
        logger.info("Response sent")
        return jsonify({
            "success": False, 
            "error": "Failed to get basic stats",
            "total_grants": 0,
            "active_applications": 0,
            "grants_won": 0,
            "total_funding": 0,
            "success_rate": 0,
            "submitted_grants": 0
        }), 500


@bp.route('/update-metrics', methods=['POST'])
def update_analytics_metrics():
    """
    Manually trigger an update of all success metrics
    
    Returns:
        Response: JSON response with update status.
    """
    logger.info("Request processed")
    
    try:
        result = update_success_metrics()
        
        logger.info("Response sent")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error updating success metrics: {str(e)}")
        logger.info("Response sent")
        return jsonify({"success": False, "error": "Failed to update success metrics"}), 500