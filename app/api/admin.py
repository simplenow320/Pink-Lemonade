"""
Admin API endpoints for system monitoring and management
"""
from flask import Blueprint, jsonify, request, session
from app.services.monitoring_service import monitor
from app.services.cache_service import cache
from app.services.security_service import security
from app.services.workflow_service import workflow_service
from app.models import User, Grant, UserProgress
from app import db
import logging
from functools import wraps

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is admin (simplified for demo)
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/api/admin/health', methods=['GET'])
def health_check():
    """Public health check endpoint"""
    try:
        health = monitor.get_health_status()
        
        # Determine overall status
        if health.get('database', {}).get('connected') == False:
            health['status'] = 'unhealthy'
            status_code = 503
        elif health.get('recent_errors', 0) > 50:
            health['status'] = 'degraded'
            status_code = 200
        else:
            health['status'] = 'healthy'
            status_code = 200
        
        return jsonify(health), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@admin_bp.route('/api/admin/metrics', methods=['GET'])
@security.rate_limit(max_requests=30, window_seconds=60)
@admin_required
def get_metrics():
    """Get system metrics (admin only)"""
    try:
        metrics = monitor.get_metrics_summary()
        cache_stats = cache.get_stats()
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'cache': cache_stats
        })
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/admin/performance', methods=['GET'])
@admin_required
def get_performance():
    """Get performance report (admin only)"""
    try:
        report = monitor.get_performance_report()
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logger.error(f"Error getting performance report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/admin/cache/clear', methods=['POST'])
@admin_required
def clear_cache():
    """Clear application cache (admin only)"""
    try:
        cache.clear()
        
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/admin/stats', methods=['GET'])
@admin_required
def get_admin_stats():
    """Get comprehensive admin statistics"""
    try:
        # User stats
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(role='admin').count()
        
        # Grant stats
        total_grants = Grant.query.count()
        awarded_grants = Grant.query.filter_by(status='awarded').count()
        submitted_grants = Grant.query.filter_by(status='submitted').count()
        
        # Gamification stats
        total_progress_users = UserProgress.query.count()
        avg_xp = db.session.query(db.func.avg(UserProgress.total_xp)).scalar() or 0
        max_level = db.session.query(db.func.max(UserProgress.current_level)).scalar() or 0
        
        # Workflow stats
        workflow_metrics = workflow_service.calculate_success_metrics(1)  # Org ID 1
        
        stats = {
            'users': {
                'total': total_users,
                'active': active_users,
                'admins': admin_users
            },
            'grants': {
                'total': total_grants,
                'awarded': awarded_grants,
                'submitted': submitted_grants,
                'success_rate': workflow_metrics.get('success_rate', 0)
            },
            'gamification': {
                'engaged_users': total_progress_users,
                'average_xp': round(avg_xp),
                'highest_level': max_level
            },
            'workflow': workflow_metrics
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/admin/errors', methods=['GET'])
@admin_required
def get_recent_errors():
    """Get recent application errors (admin only)"""
    try:
        errors = monitor.metrics.get('errors', [])
        
        # Group errors by type
        error_types = {}
        for error in errors:
            error_type = error.get('type', 'Unknown')
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1
        
        return jsonify({
            'success': True,
            'total_errors': len(errors),
            'error_types': error_types,
            'recent_errors': errors[-20:]  # Last 20 errors
        })
        
    except Exception as e:
        logger.error(f"Error getting error log: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/admin/database/optimize', methods=['POST'])
@admin_required
def optimize_database():
    """Run database optimization (admin only)"""
    try:
        # Run VACUUM for PostgreSQL (cleanup deleted rows)
        if 'postgresql' in db.engine.url.drivername:
            db.session.execute('VACUUM ANALYZE')
            db.session.commit()
            message = 'Database optimized with VACUUM ANALYZE'
        else:
            message = 'Database optimization not available for this database type'
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error optimizing database: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/admin/test/rate-limit', methods=['GET'])
@security.rate_limit(max_requests=5, window_seconds=60)
def test_rate_limit():
    """Test endpoint for rate limiting"""
    return jsonify({
        'success': True,
        'message': 'Request successful. Rate limit: 5 requests per minute.'
    })