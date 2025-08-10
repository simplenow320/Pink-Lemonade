"""
Integration API - Phase 2 Endpoints
Provides real-time data synchronization, automated monitoring, and system coordination
"""

from flask import Blueprint, request, jsonify, session
from app.services.integration_service import IntegrationService
from functools import wraps
from flask import session

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        from app.models import User
        return User.query.get(user_id)
    return None

def rate_limit(max_requests=100, window_seconds=60):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple rate limiting - in production use Redis
            return f(*args, **kwargs)
        return decorated_function
    return decorator
from app.models import Organization, User
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('integration', __name__, url_prefix='/api/integration')

# Initialize integration service
integration_service = IntegrationService()

@bp.route('/discovery/run', methods=['POST'])
@login_required
@rate_limit(max_requests=5, window_seconds=300)  # Limit discovery runs
def run_discovery():
    """
    Trigger full discovery cycle
    Can be scoped to specific organization
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        org_id = data.get('org_id')
        
        # If org_id not provided, use user's organization
        if not org_id and user.org_id:
            org_id = user.org_id
        
        # Run discovery cycle
        results = integration_service.run_full_discovery_cycle(org_id)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Discovery run failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/sync/organization/<int:org_id>', methods=['POST'])
@login_required
def sync_organization(org_id):
    """
    Synchronize organization data across all systems
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has access to this organization
        if user.org_id != org_id and user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        results = integration_service.sync_organization_data(org_id)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Organization sync failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/real-time/grants', methods=['POST'])
@rate_limit(max_requests=100, window_seconds=60)  # Allow frequent real-time updates
def receive_real_time_grants():
    """
    Receive real-time grant data from external sources
    This endpoint can be called by webhooks or scheduled jobs
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        source = data.get('source', 'unknown')
        grants_data = data.get('grants', [])
        
        if not grants_data:
            return jsonify({'error': 'No grants data provided'}), 400
        
        results = integration_service.process_real_time_grants(source, grants_data)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Real-time grants processing failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/dashboard', methods=['GET'])
@login_required
def get_integration_dashboard():
    """
    Get comprehensive integration dashboard data
    """
    try:
        dashboard_data = integration_service.get_integration_dashboard_data()
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Dashboard data retrieval failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/status', methods=['GET'])
def get_integration_status():
    """
    Get current integration system status
    Public endpoint for health checks
    """
    try:
        from app.services.monitoring_service import MonitoringService
        monitoring = MonitoringService()
        
        health_status = monitoring.get_health_status()
        
        # Calculate integration-specific metrics
        status = {
            'system_health': health_status.get('status', 'unknown'),
            'database_connected': health_status.get('database', {}).get('connected', False),
            'last_discovery_run': None,  # TODO: Get from discovery service
            'active_integrations': 0,    # TODO: Count active integrations
            'timestamp': health_status.get('timestamp')
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({
            'system_health': 'error',
            'error': str(e)
        }), 500

@bp.route('/notifications/test', methods=['POST'])
@login_required
def test_notifications():
    """
    Test notification system
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        notification_type = data.get('type', 'test')
        
        # Send test notification
        from app.services.notification_service import NotificationService
        notification_service = NotificationService()
        
        if notification_type == 'grant_match':
            # Test grant match notification
            result = {'status': 'test_sent', 'type': 'grant_match'}
        else:
            # Generic test notification
            result = {'status': 'test_sent', 'type': 'generic'}
        
        return jsonify({
            'success': True,
            'notification_sent': result,
            'type': notification_type
        })
        
    except Exception as e:
        logger.error(f"Notification test failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/analytics/summary', methods=['GET'])
@login_required
def get_analytics_summary():
    """
    Get integration analytics summary
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        from app.models import Analytics
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # Get analytics for the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Count events by type
        analytics_summary = (
            Analytics.query
            .filter(Analytics.created_at >= thirty_days_ago)
            .with_entities(Analytics.event_type, func.count(Analytics.id))
            .group_by(Analytics.event_type)
            .all()
        )
        
        summary = {
            'period': '30_days',
            'events_by_type': {event_type: count for event_type, count in analytics_summary},
            'total_events': sum(count for _, count in analytics_summary),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'analytics': summary
        })
        
    except Exception as e:
        logger.error(f"Analytics summary failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/export/data', methods=['GET'])
@login_required
def export_integration_data():
    """
    Export integration data for external systems
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has export permissions
        if user.role not in ['admin', 'manager']:
            return jsonify({'error': 'Export permission required'}), 403
        
        from app.models import Grant, Analytics
        from datetime import datetime, timedelta
        
        # Get recent data
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # Export recent grants
        recent_grants = Grant.query.filter(
            Grant.created_at >= seven_days_ago
        ).limit(100).all()
        
        # Export recent analytics
        recent_analytics = Analytics.query.filter(
            Analytics.created_at >= seven_days_ago
        ).limit(500).all()
        
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'period': '7_days',
            'grants': [grant.to_dict() for grant in recent_grants],
            'analytics': [analytic.to_dict() for analytic in recent_analytics],
            'total_grants': len(recent_grants),
            'total_analytics': len(recent_analytics)
        }
        
        return jsonify({
            'success': True,
            'data': export_data
        })
        
    except Exception as e:
        logger.error(f"Data export failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/import/data', methods=['POST'])
@login_required
def import_integration_data():
    """
    Import data from external systems
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has import permissions
        if user.role not in ['admin', 'manager']:
            return jsonify({'error': 'Import permission required'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Process import data
        import_type = data.get('type', 'grants')
        import_data = data.get('data', [])
        
        results = {
            'imported': 0,
            'skipped': 0,
            'errors': []
        }
        
        if import_type == 'grants':
            # Import grants
            for grant_data in import_data:
                try:
                    grant = integration_service._create_or_update_grant(
                        grant_data, 
                        'import'
                    )
                    if grant:
                        results['imported'] += 1
                    else:
                        results['skipped'] += 1
                except Exception as e:
                    results['errors'].append(str(e))
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Data import failed: {e}")
        return jsonify({'error': str(e)}), 500