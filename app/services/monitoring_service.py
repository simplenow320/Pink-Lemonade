"""
Monitoring Service for Production Health Checks
Tracks system metrics, errors, and performance
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import logging
from functools import wraps
from flask import g, request
from app import db

# Try to import psutil, but don't fail if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

class MonitoringService:
    """System monitoring and health checks"""
    
    def __init__(self):
        self.metrics = {
            'requests': {},
            'errors': [],
            'performance': {},
            'database': {},
            'system': {}
        }
        self.start_time = datetime.now()
    
    def track_request(self, endpoint: str, method: str, status_code: int, duration_ms: float):
        """Track API request metrics"""
        key = f"{method}:{endpoint}"
        
        if key not in self.metrics['requests']:
            self.metrics['requests'][key] = {
                'count': 0,
                'success': 0,
                'errors': 0,
                'total_duration': 0,
                'avg_duration': 0
            }
        
        stats = self.metrics['requests'][key]
        stats['count'] += 1
        stats['total_duration'] += duration_ms
        stats['avg_duration'] = stats['total_duration'] / stats['count']
        
        if 200 <= status_code < 400:
            stats['success'] += 1
        else:
            stats['errors'] += 1
    
    def track_error(self, error_type: str, message: str, endpoint: str = None):
        """Track application errors"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': message[:500],  # Truncate long messages
            'endpoint': endpoint
        }
        
        # Keep only last 100 errors
        self.metrics['errors'].append(error_entry)
        if len(self.metrics['errors']) > 100:
            self.metrics['errors'] = self.metrics['errors'][-100:]
    
    def performance_monitor(self, name: str):
        """Decorator to monitor function performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Track performance
                    if name not in self.metrics['performance']:
                        self.metrics['performance'][name] = {
                            'calls': 0,
                            'total_time': 0,
                            'avg_time': 0,
                            'max_time': 0
                        }
                    
                    perf = self.metrics['performance'][name]
                    perf['calls'] += 1
                    perf['total_time'] += duration_ms
                    perf['avg_time'] = perf['total_time'] / perf['calls']
                    perf['max_time'] = max(perf['max_time'], duration_ms)
                    
                    return result
                    
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    self.track_error(type(e).__name__, str(e), name)
                    raise
                    
            return wrapper
        return decorator
    
    def check_database_health(self) -> Dict:
        """Check database connectivity and performance"""
        from sqlalchemy import text
        health = {
            'connected': False,
            'response_time_ms': None,
            'active_connections': None,
            'table_count': None
        }
        
        try:
            start_time = time.time()
            
            # Test query
            result = db.session.execute(text('SELECT 1'))
            
            health['connected'] = True
            health['response_time_ms'] = (time.time() - start_time) * 1000
            
            # Get connection info (PostgreSQL specific)
            try:
                conn_result = db.session.execute(
                    text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
                )
                health['active_connections'] = conn_result.scalar()
            except:
                pass
            
            # Count tables
            try:
                tables_result = db.session.execute(
                    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )
                health['table_count'] = tables_result.scalar()
            except:
                pass
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health['error'] = str(e)
        
        self.metrics['database'] = health
        return health
    
    def check_system_health(self) -> Dict:
        """Check system resources"""
        try:
            health = {
                'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600
            }
            
            if PSUTIL_AVAILABLE:
                health.update({
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory': {
                        'total': psutil.virtual_memory().total,
                        'available': psutil.virtual_memory().available,
                        'percent': psutil.virtual_memory().percent
                    },
                    'disk': {
                        'total': psutil.disk_usage('/').total,
                        'free': psutil.disk_usage('/').free,
                        'percent': psutil.disk_usage('/').percent
                    }
                })
            else:
                health['note'] = 'System metrics unavailable (psutil not installed)'
            
            self.metrics['system'] = health
            return health
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {'error': str(e), 'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600}
    
    def get_health_status(self) -> Dict:
        """Get overall system health status"""
        return {
            'status': 'healthy',  # or 'degraded', 'unhealthy'
            'timestamp': datetime.now().isoformat(),
            'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
            'database': self.check_database_health(),
            'system': self.check_system_health(),
            'recent_errors': len(self.metrics['errors'])
        }
    
    def get_metrics_summary(self) -> Dict:
        """Get summary of all metrics"""
        total_requests = sum(r['count'] for r in self.metrics['requests'].values())
        total_errors = sum(r['errors'] for r in self.metrics['requests'].values())
        
        return {
            'requests': {
                'total': total_requests,
                'success_rate': ((total_requests - total_errors) / total_requests * 100) if total_requests > 0 else 100,
                'endpoints': self.metrics['requests']
            },
            'performance': self.metrics['performance'],
            'errors': {
                'total': len(self.metrics['errors']),
                'recent': self.metrics['errors'][-10:]  # Last 10 errors
            },
            'database': self.metrics['database'],
            'system': self.metrics['system']
        }
    
    def get_performance_report(self) -> Dict:
        """Generate performance report"""
        slow_endpoints = []
        for name, stats in self.metrics['performance'].items():
            if stats['avg_time'] > 1000:  # Slower than 1 second
                slow_endpoints.append({
                    'name': name,
                    'avg_time_ms': round(stats['avg_time'], 2),
                    'max_time_ms': round(stats['max_time'], 2),
                    'calls': stats['calls']
                })
        
        return {
            'slow_endpoints': sorted(slow_endpoints, key=lambda x: x['avg_time_ms'], reverse=True),
            'total_monitored': len(self.metrics['performance']),
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Check for slow endpoints
        for name, stats in self.metrics['performance'].items():
            if stats['avg_time'] > 2000:
                recommendations.append(f"Optimize {name}: Average response time is {stats['avg_time']:.0f}ms")
        
        # Check system resources
        if self.metrics.get('system', {}).get('memory', {}).get('percent', 0) > 80:
            recommendations.append("High memory usage detected. Consider scaling up or optimizing memory usage.")
        
        if self.metrics.get('system', {}).get('cpu_percent', 0) > 80:
            recommendations.append("High CPU usage detected. Consider optimizing CPU-intensive operations.")
        
        # Check error rate
        if self.metrics['errors']:
            error_rate = len(self.metrics['errors'])
            if error_rate > 50:
                recommendations.append(f"High error rate: {error_rate} errors in recent history")
        
        return recommendations

# Singleton instance
monitor = MonitoringService()

# Flask middleware for automatic request tracking
def init_monitoring(app):
    """Initialize monitoring for Flask app"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000
            monitor.track_request(
                request.endpoint or 'unknown',
                request.method,
                response.status_code,
                duration_ms
            )
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        monitor.track_error(
            type(e).__name__,
            str(e),
            request.endpoint
        )
        # Don't re-raise 404 errors
        from werkzeug.exceptions import NotFound
        if isinstance(e, NotFound):
            from flask import jsonify
            return jsonify({'error': 'Not found'}), 404
        # Re-raise other exceptions for normal handling
        raise e