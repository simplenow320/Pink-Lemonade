"""
Admin Dashboard API
System monitoring and user management
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.grant import Grant
from app.models.organization import Organization
from app.services.apiManager import api_manager
from sqlalchemy import func
import logging
import os

logger = logging.getLogger(__name__)

bp = Blueprint('admin_dashboard', __name__, url_prefix='/api/admin')

def require_admin(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard', methods=['GET'])
@require_admin
def get_dashboard_stats():
    """Get admin dashboard statistics"""
    try:
        # System statistics
        stats = {
            'users': {
                'total': User.query.count(),
                'active': User.query.filter_by(is_active=True).count(),
                'new_this_week': User.query.filter(
                    User.created_at >= datetime.now() - timedelta(days=7)
                ).count()
            },
            'grants': {
                'total': Grant.query.count(),
                'in_progress': Grant.query.filter_by(status='in_progress').count(),
                'submitted': Grant.query.filter_by(status='submitted').count(),
                'awarded': Grant.query.filter_by(status='awarded').count()
            },
            'organizations': {
                'total': Organization.query.count(),
                'with_profile': Organization.query.filter(
                    Organization.mission != None
                ).count()
            },
            'api_usage': {
                'calls_today': 0,  # Implement API tracking
                'errors_today': 0,
                'avg_response_time': 0
            },
            'data_sources': {
                'total': len(api_manager.get_enabled_sources()),
                'active': sum(1 for s in api_manager.get_enabled_sources().values() if s.get('enabled'))
            }
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/users', methods=['GET'])
@require_admin
def get_users():
    """Get all users with management options"""
    try:
        page = int(request.args.get('page', 1))
        per_page = 20
        
        users = User.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        user_data = []
        for user in users.items:
            user_dict = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'grants_count': Grant.query.filter_by(org_id=user.id).count()
            }
            user_data.append(user_dict)
        
        return jsonify({
            'users': user_data,
            'total': users.total,
            'pages': users.pages,
            'current_page': page
        })
        
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@require_admin
def toggle_user_status(user_id):
    """Enable or disable a user account"""
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = not user.is_active
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'is_active': user.is_active
        })
        
    except Exception as e:
        logger.error(f"Error toggling user status: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/users/<int:user_id>/role', methods=['PUT'])
@require_admin
def update_user_role(user_id):
    """Update user role"""
    try:
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['admin', 'manager', 'member']:
            return jsonify({'error': 'Invalid role'}), 400
        
        user = User.query.get_or_404(user_id)
        user.role = new_role
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'role': new_role
        })
        
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/system/health', methods=['GET'])
@require_admin
def system_health():
    """Get system health status"""
    try:
        health = {
            'database': 'healthy',
            'api_sources': {},
            'disk_usage': {},
            'memory_usage': {},
            'error_rate': 0
        }
        
        # Check database connection
        try:
            db.session.execute('SELECT 1')
            health['database'] = 'healthy'
        except:
            health['database'] = 'unhealthy'
        
        # Check API sources
        for source_id, config in api_manager.get_enabled_sources().items():
            health['api_sources'][source_id] = {
                'enabled': config.get('enabled'),
                'last_check': None,  # Implement tracking
                'status': 'unknown'
            }
        
        # Check disk usage
        if os.path.exists('/'):
            stat = os.statvfs('/')
            health['disk_usage'] = {
                'total_gb': (stat.f_blocks * stat.f_frsize) / (1024**3),
                'used_gb': ((stat.f_blocks - stat.f_avail) * stat.f_frsize) / (1024**3),
                'free_gb': (stat.f_avail * stat.f_frsize) / (1024**3),
                'percent_used': ((stat.f_blocks - stat.f_avail) / stat.f_blocks) * 100
            }
        
        return jsonify(health)
        
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/logs', methods=['GET'])
@require_admin
def get_error_logs():
    """Get recent error logs"""
    try:
        # Read last N lines from log file
        log_file = 'app.log'  # Configure log file path
        lines = int(request.args.get('lines', 100))
        
        logs = []
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                # Read last N lines
                logs = f.readlines()[-lines:]
        
        # Parse and filter for errors
        error_logs = []
        for log in logs:
            if 'ERROR' in log or 'WARNING' in log:
                error_logs.append(log.strip())
        
        return jsonify({
            'logs': error_logs,
            'total': len(error_logs)
        })
        
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/sources', methods=['GET'])
@require_admin
def manage_data_sources():
    """Manage data source configurations"""
    try:
        sources = api_manager.get_enabled_sources()
        
        source_data = []
        for source_id, config in sources.items():
            source_data.append({
                'id': source_id,
                'name': config.get('name'),
                'enabled': config.get('enabled'),
                'type': config.get('type'),
                'rate_limit': config.get('rate_limit'),
                'last_sync': None,  # Implement tracking
                'records_fetched': 0  # Implement tracking
            })
        
        return jsonify({
            'sources': source_data,
            'total': len(source_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching sources: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/sources/<source_id>/toggle', methods=['POST'])
@require_admin
def toggle_source(source_id):
    """Enable or disable a data source"""
    try:
        sources = api_manager.get_enabled_sources()
        
        if source_id not in sources:
            return jsonify({'error': 'Source not found'}), 404
        
        # Toggle source (implement in api_manager)
        # sources[source_id]['enabled'] = not sources[source_id].get('enabled', True)
        
        return jsonify({
            'success': True,
            'source_id': source_id,
            'enabled': sources[source_id].get('enabled')
        })
        
    except Exception as e:
        logger.error(f"Error toggling source: {e}")
        return jsonify({'error': str(e)}), 500