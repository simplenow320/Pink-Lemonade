"""
Application monitoring and health checks
"""

import psutil
import os
from datetime import datetime
from app import db
import logging

logger = logging.getLogger(__name__)

class MonitoringService:
    """Service for monitoring application health and performance"""
    
    @staticmethod
    def get_system_metrics():
        """Get system resource metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': psutil.cpu_percent(interval=1),
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total_gb': psutil.virtual_memory().total / (1024**3),
                    'used_gb': psutil.virtual_memory().used / (1024**3),
                    'available_gb': psutil.virtual_memory().available / (1024**3),
                    'percent': psutil.virtual_memory().percent
                },
                'disk': {},
                'network': {
                    'bytes_sent': psutil.net_io_counters().bytes_sent,
                    'bytes_received': psutil.net_io_counters().bytes_recv
                }
            }
            
            # Disk usage
            disk = psutil.disk_usage('/')
            metrics['disk'] = {
                'total_gb': disk.total / (1024**3),
                'used_gb': disk.used / (1024**3),
                'free_gb': disk.free / (1024**3),
                'percent': disk.percent
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return None
    
    @staticmethod
    def check_database_health():
        """Check database connection and performance"""
        try:
            # Test connection
            start = datetime.now()
            db.session.execute('SELECT 1')
            response_time = (datetime.now() - start).total_seconds() * 1000
            
            # Get connection stats
            result = db.session.execute("""
                SELECT 
                    numbackends as active_connections,
                    xact_commit as transactions_committed,
                    xact_rollback as transactions_rolled_back,
                    blks_read as blocks_read,
                    blks_hit as blocks_hit
                FROM pg_stat_database 
                WHERE datname = current_database()
            """).first()
            
            health = {
                'status': 'healthy' if response_time < 100 else 'degraded',
                'response_time_ms': response_time,
                'active_connections': result[0] if result else 0,
                'transactions': {
                    'committed': result[1] if result else 0,
                    'rolled_back': result[2] if result else 0
                },
                'cache_hit_ratio': (result[4] / (result[3] + result[4]) * 100) if result and (result[3] + result[4]) > 0 else 0
            }
            
            return health
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    def get_application_metrics():
        """Get application-specific metrics"""
        from app.models.grant import Grant
        from app.models.user import User
        from app.services.cache_service import cache
        
        try:
            metrics = {
                'grants': {
                    'total': Grant.query.count(),
                    'in_progress': Grant.query.filter_by(status='in_progress').count(),
                    'submitted_today': Grant.query.filter(
                        Grant.date_submitted == datetime.now().date()
                    ).count()
                },
                'users': {
                    'total': User.query.count(),
                    'active_today': User.query.filter(
                        User.last_login >= datetime.now().date()
                    ).count()
                },
                'cache': cache.get_stats()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting application metrics: {e}")
            return None
    
    @staticmethod
    def create_health_report():
        """Create comprehensive health report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'system': MonitoringService.get_system_metrics(),
            'database': MonitoringService.check_database_health(),
            'application': MonitoringService.get_application_metrics()
        }
        
        # Determine overall health
        if report['database'].get('status') == 'unhealthy':
            report['overall_status'] = 'unhealthy'
        elif report['system'] and report['system']['memory']['percent'] > 90:
            report['overall_status'] = 'degraded'
        elif report['system'] and report['system']['disk']['percent'] > 90:
            report['overall_status'] = 'degraded'
        else:
            report['overall_status'] = 'healthy'
        
        return report