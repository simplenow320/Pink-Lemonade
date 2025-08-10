"""
Automated Monitoring API - Phase 2
Provides endpoints for system monitoring, health checks, and performance analytics
"""

from flask import Blueprint, request, jsonify
from app.services.automated_monitoring import AutomatedMonitoringService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('automated_monitoring', __name__, url_prefix='/api/monitoring')

# Initialize monitoring service
monitoring_service = AutomatedMonitoringService()

@bp.route('/health', methods=['GET'])
def get_health_status():
    """
    Get comprehensive system health status
    Public endpoint for health monitoring
    """
    try:
        health_report = monitoring_service.run_health_check()
        
        # Determine HTTP status code based on health
        status_code = 200
        if health_report.get('overall_status') == 'critical':
            status_code = 503
        elif health_report.get('overall_status') == 'warning':
            status_code = 200  # Still operational
        
        return jsonify(health_report), status_code
        
    except Exception as e:
        logger.error(f"Health check endpoint failed: {e}")
        return jsonify({
            'overall_status': 'critical',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@bp.route('/discovery', methods=['GET'])
def get_discovery_metrics():
    """
    Get grant discovery performance metrics
    """
    try:
        discovery_metrics = monitoring_service.monitor_grant_discovery()
        
        return jsonify({
            'success': True,
            'metrics': discovery_metrics
        })
        
    except Exception as e:
        logger.error(f"Discovery metrics endpoint failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/ai-performance', methods=['GET'])
def get_ai_performance():
    """
    Get AI analysis performance metrics
    """
    try:
        ai_metrics = monitoring_service.monitor_ai_performance()
        
        return jsonify({
            'success': True,
            'metrics': ai_metrics
        })
        
    except Exception as e:
        logger.error(f"AI performance endpoint failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/system-report', methods=['GET'])
def get_system_report():
    """
    Get comprehensive system performance report
    """
    try:
        report = monitoring_service.generate_system_report()
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logger.error(f"System report endpoint failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/alerts', methods=['GET'])
def get_active_alerts():
    """
    Get current system alerts
    """
    try:
        health_report = monitoring_service.run_health_check()
        alerts = health_report.get('alerts', [])
        
        # Add discovery and AI alerts
        discovery_metrics = monitoring_service.monitor_grant_discovery()
        ai_metrics = monitoring_service.monitor_ai_performance()
        
        alerts.extend(discovery_metrics.get('alerts', []))
        alerts.extend(ai_metrics.get('alerts', []))
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'alert_count': len(alerts),
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Alerts endpoint failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/trends', methods=['GET'])
def get_performance_trends():
    """
    Get performance trends over time
    """
    try:
        from app.models import Analytics, Grant
        from datetime import timedelta
        from sqlalchemy import func
        
        # Get trend parameters
        days = int(request.args.get('days', 7))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Grant discovery trends
        grant_trends = []
        for i in range(days):
            date = end_date.date() - timedelta(days=i)
            grants_count = Grant.query.filter(
                Grant.created_at >= datetime.combine(date, datetime.min.time()),
                Grant.created_at < datetime.combine(date + timedelta(days=1), datetime.min.time())
            ).count()
            grant_trends.append({
                'date': date.isoformat(),
                'grants_discovered': grants_count
            })
        
        # AI analysis trends
        ai_trends = []
        for i in range(days):
            date = end_date.date() - timedelta(days=i)
            analyses_count = Analytics.query.filter(
                Analytics.event_type.in_(['grant_decision', 'high_match']),
                Analytics.created_at >= datetime.combine(date, datetime.min.time()),
                Analytics.created_at < datetime.combine(date + timedelta(days=1), datetime.min.time())
            ).count()
            ai_trends.append({
                'date': date.isoformat(),
                'analyses_performed': analyses_count
            })
        
        return jsonify({
            'success': True,
            'trends': {
                'grant_discovery': grant_trends,
                'ai_analysis': ai_trends,
                'period_days': days
            }
        })
        
    except Exception as e:
        logger.error(f"Trends endpoint failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/metrics/summary', methods=['GET'])
def get_metrics_summary():
    """
    Get summarized metrics for dashboard
    """
    try:
        from app.models import Grant, Organization, Analytics
        
        # Get basic counts
        total_grants = Grant.query.count()
        total_orgs = Organization.query.count()
        total_analytics = Analytics.query.count()
        
        # Get recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_grants = Grant.query.filter(Grant.created_at >= yesterday).count()
        recent_analytics = Analytics.query.filter(Analytics.created_at >= yesterday).count()
        
        # Calculate growth rates
        week_ago = datetime.utcnow() - timedelta(days=7)
        grants_last_week = Grant.query.filter(Grant.created_at >= week_ago).count()
        grant_growth_rate = (grants_last_week / max(total_grants - grants_last_week, 1)) * 100
        
        summary = {
            'totals': {
                'grants': total_grants,
                'organizations': total_orgs,
                'analytics_events': total_analytics
            },
            'recent_activity': {
                'grants_24h': recent_grants,
                'analytics_24h': recent_analytics
            },
            'growth_rates': {
                'grants_weekly': round(grant_growth_rate, 2)
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Metrics summary endpoint failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/status/integration', methods=['GET'])
def get_integration_status():
    """
    Get status of integration components
    """
    try:
        from app.services.integration_service import IntegrationService
        integration_service = IntegrationService()
        
        # Get integration dashboard data
        dashboard_data = integration_service.get_integration_dashboard_data()
        
        # Extract status information
        status = {
            'discovery_services': 'operational',
            'ai_services': 'operational',
            'notification_services': 'operational',
            'analytics_services': 'operational',
            'last_updated': datetime.utcnow().isoformat()
        }
        
        # Check for errors in dashboard data
        if 'error' in dashboard_data:
            status['discovery_services'] = 'degraded'
            status['error'] = dashboard_data['error']
        
        return jsonify({
            'success': True,
            'integration_status': status
        })
        
    except Exception as e:
        logger.error(f"Integration status endpoint failed: {e}")
        return jsonify({'error': str(e)}), 500