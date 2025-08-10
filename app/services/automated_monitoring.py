"""
Automated Monitoring Service - Phase 2
Provides continuous monitoring of grant discovery, AI analysis, and system health
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from app import db
from app.models import Grant, Analytics, ScraperHistory, Organization
from app.services.integration_service import IntegrationService
from app.services.monitoring_service import MonitoringService

logger = logging.getLogger(__name__)

class AutomatedMonitoringService:
    """Service for automated monitoring and alerting"""
    
    def __init__(self):
        self.integration_service = IntegrationService()
        self.monitoring_service = MonitoringService()
    
    def run_health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check for all system components
        """
        health_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'components': {},
            'alerts': [],
            'performance_metrics': {}
        }
        
        try:
            # Check database connectivity
            db_health = self._check_database_health()
            health_report['components']['database'] = db_health
            
            # Check AI services
            ai_health = self._check_ai_services()
            health_report['components']['ai_services'] = ai_health
            
            # Check discovery services
            discovery_health = self._check_discovery_services()
            health_report['components']['discovery'] = discovery_health
            
            # Check recent grant discovery performance
            discovery_performance = self._check_discovery_performance()
            health_report['performance_metrics']['discovery'] = discovery_performance
            
            # Check organization profile completeness trends
            profile_metrics = self._check_profile_completeness()
            health_report['performance_metrics']['profiles'] = profile_metrics
            
            # Generate alerts based on health status
            health_report['alerts'] = self._generate_health_alerts(health_report)
            
            # Determine overall status
            health_report['overall_status'] = self._calculate_overall_status(health_report)
            
            # Record health check analytics
            self._record_health_analytics(health_report)
            
            return health_report
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_report['overall_status'] = 'critical'
            health_report['error'] = str(e)
            return health_report
    
    def monitor_grant_discovery(self) -> Dict[str, Any]:
        """
        Monitor grant discovery performance and trends
        """
        try:
            # Get discovery metrics for last 24 hours
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            # Recent grants discovered
            recent_grants = Grant.query.filter(
                Grant.created_at >= yesterday
            ).count()
            
            # Recent discovery jobs
            recent_jobs = ScraperHistory.query.filter(
                ScraperHistory.start_time >= yesterday
            ).all()
            
            # Calculate success rates
            successful_jobs = [job for job in recent_jobs if job.status == 'completed']
            success_rate = len(successful_jobs) / len(recent_jobs) if recent_jobs else 0
            
            # Average grants per job
            avg_grants_per_job = sum(job.grants_found or 0 for job in recent_jobs) / len(recent_jobs) if recent_jobs else 0
            
            discovery_metrics = {
                'period': '24_hours',
                'grants_discovered': recent_grants,
                'discovery_jobs_run': len(recent_jobs),
                'successful_jobs': len(successful_jobs),
                'success_rate': success_rate,
                'avg_grants_per_job': avg_grants_per_job,
                'last_successful_run': None,
                'alerts': []
            }
            
            # Find last successful run
            if successful_jobs:
                last_success = max(successful_jobs, key=lambda x: x.start_time)
                discovery_metrics['last_successful_run'] = last_success.start_time.isoformat()
            
            # Generate discovery alerts
            if success_rate < 0.5:
                discovery_metrics['alerts'].append({
                    'type': 'warning',
                    'message': f'Discovery success rate is low: {success_rate:.1%}'
                })
            
            if recent_grants == 0:
                discovery_metrics['alerts'].append({
                    'type': 'critical',
                    'message': 'No grants discovered in the last 24 hours'
                })
            
            return discovery_metrics
            
        except Exception as e:
            logger.error(f"Discovery monitoring failed: {e}")
            return {'error': str(e)}
    
    def monitor_ai_performance(self) -> Dict[str, Any]:
        """
        Monitor AI analysis performance and accuracy
        """
        try:
            # Get AI analytics for last 7 days
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            ai_analytics = Analytics.query.filter(
                Analytics.event_type.in_(['grant_decision', 'high_match', 'discovery_cycle']),
                Analytics.created_at >= week_ago
            ).all()
            
            # Analyze AI confidence distribution
            confidence_distribution = {'low': 0, 'medium': 0, 'high': 0}
            total_analyses = 0
            high_match_count = 0
            
            for analytic in ai_analytics:
                event_data = analytic.event_data or {}
                confidence = event_data.get('confidence', 'low')
                if confidence in confidence_distribution:
                    confidence_distribution[confidence] += 1
                    total_analyses += 1
                
                if analytic.event_type == 'high_match':
                    high_match_count += 1
            
            # Calculate average confidence score
            confidence_score = (
                confidence_distribution['low'] * 1 +
                confidence_distribution['medium'] * 2 +
                confidence_distribution['high'] * 3
            ) / max(total_analyses, 1) if total_analyses > 0 else 0
            
            ai_metrics = {
                'period': '7_days',
                'total_analyses': total_analyses,
                'high_matches_found': high_match_count,
                'confidence_distribution': confidence_distribution,
                'avg_confidence_score': confidence_score,
                'performance_rating': self._calculate_ai_performance_rating(confidence_score, high_match_count),
                'alerts': []
            }
            
            # Generate AI performance alerts
            if confidence_score < 1.5:
                ai_metrics['alerts'].append({
                    'type': 'warning',
                    'message': 'AI confidence scores are consistently low'
                })
            
            if total_analyses == 0:
                ai_metrics['alerts'].append({
                    'type': 'critical',
                    'message': 'No AI analyses recorded in the last 7 days'
                })
            
            return ai_metrics
            
        except Exception as e:
            logger.error(f"AI performance monitoring failed: {e}")
            return {'error': str(e)}
    
    def generate_system_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive system performance report
        """
        try:
            report = {
                'generated_at': datetime.utcnow().isoformat(),
                'health_status': self.run_health_check(),
                'discovery_performance': self.monitor_grant_discovery(),
                'ai_performance': self.monitor_ai_performance(),
                'system_metrics': self._get_system_metrics(),
                'recommendations': []
            }
            
            # Generate recommendations based on findings
            report['recommendations'] = self._generate_recommendations(report)
            
            return report
            
        except Exception as e:
            logger.error(f"System report generation failed: {e}")
            return {'error': str(e)}
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            # Test basic query
            grant_count = Grant.query.count()
            org_count = Organization.query.count()
            
            return {
                'status': 'healthy',
                'grants_in_database': grant_count,
                'organizations_in_database': org_count,
                'last_checked': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_checked': datetime.utcnow().isoformat()
            }
    
    def _check_ai_services(self) -> Dict[str, Any]:
        """Check AI services availability"""
        try:
            # Check if AI reasoning engine can be imported
            from app.services.ai_reasoning_engine import AIReasoningEngine
            engine = AIReasoningEngine()
            
            return {
                'status': 'healthy',
                'reasoning_engine': 'available',
                'last_checked': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_checked': datetime.utcnow().isoformat()
            }
    
    def _check_discovery_services(self) -> Dict[str, Any]:
        """Check discovery services status"""
        try:
            # Check recent discovery activity
            recent_history = ScraperHistory.query.filter(
                ScraperHistory.start_time >= datetime.utcnow() - timedelta(hours=24)
            ).first()
            
            return {
                'status': 'healthy' if recent_history else 'warning',
                'last_discovery_run': recent_history.start_time.isoformat() if recent_history else None,
                'last_checked': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_checked': datetime.utcnow().isoformat()
            }
    
    def _check_discovery_performance(self) -> Dict[str, Any]:
        """Check discovery performance metrics"""
        try:
            # Get last 7 days of discovery data
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            daily_grants = []
            for i in range(7):
                date = datetime.utcnow().date() - timedelta(days=i)
                grants_count = Grant.query.filter(
                    Grant.created_at >= datetime.combine(date, datetime.min.time()),
                    Grant.created_at < datetime.combine(date + timedelta(days=1), datetime.min.time())
                ).count()
                daily_grants.append(grants_count)
            
            avg_daily_grants = sum(daily_grants) / len(daily_grants)
            
            return {
                'avg_daily_grants': avg_daily_grants,
                'daily_breakdown': daily_grants,
                'trend': 'increasing' if daily_grants[0] > daily_grants[-1] else 'decreasing'
            }
        except Exception as e:
            logger.error(f"Discovery performance check failed: {e}")
            return {'error': str(e)}
    
    def _check_profile_completeness(self) -> Dict[str, Any]:
        """Check organization profile completeness metrics"""
        try:
            organizations = Organization.query.all()
            
            if not organizations:
                return {'total_orgs': 0, 'avg_completeness': 0}
            
            completeness_scores = []
            for org in organizations:
                score = org.calculate_completeness()
                completeness_scores.append(score)
            
            return {
                'total_orgs': len(organizations),
                'avg_completeness': sum(completeness_scores) / len(completeness_scores),
                'high_completeness_orgs': len([s for s in completeness_scores if s > 80]),
                'low_completeness_orgs': len([s for s in completeness_scores if s < 50])
            }
        except Exception as e:
            logger.error(f"Profile completeness check failed: {e}")
            return {'error': str(e)}
    
    def _generate_health_alerts(self, health_report: Dict) -> List[Dict]:
        """Generate alerts based on health report"""
        alerts = []
        
        # Check component health
        for component, health in health_report.get('components', {}).items():
            if health.get('status') == 'unhealthy':
                alerts.append({
                    'type': 'critical',
                    'component': component,
                    'message': f'{component} is unhealthy: {health.get("error", "Unknown error")}'
                })
            elif health.get('status') == 'warning':
                alerts.append({
                    'type': 'warning',
                    'component': component,
                    'message': f'{component} has warnings'
                })
        
        return alerts
    
    def _calculate_overall_status(self, health_report: Dict) -> str:
        """Calculate overall system status"""
        components = health_report.get('components', {})
        
        if any(comp.get('status') == 'unhealthy' for comp in components.values()):
            return 'critical'
        elif any(comp.get('status') == 'warning' for comp in components.values()):
            return 'warning'
        else:
            return 'healthy'
    
    def _calculate_ai_performance_rating(self, confidence_score: float, high_match_count: int) -> str:
        """Calculate AI performance rating"""
        if confidence_score >= 2.5 and high_match_count > 5:
            return 'excellent'
        elif confidence_score >= 2.0 and high_match_count > 2:
            return 'good'
        elif confidence_score >= 1.5:
            return 'fair'
        else:
            return 'needs_improvement'
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get general system metrics"""
        try:
            return {
                'total_grants': Grant.query.count(),
                'total_organizations': Organization.query.count(),
                'total_analytics_events': Analytics.query.count(),
                'system_uptime': '24h+',  # Placeholder
                'last_backup': None  # Placeholder
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _generate_recommendations(self, report: Dict) -> List[Dict]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check discovery performance
        discovery = report.get('discovery_performance', {})
        if discovery.get('grants_discovered', 0) == 0:
            recommendations.append({
                'priority': 'high',
                'category': 'discovery',
                'action': 'Check and restart grant discovery services',
                'reason': 'No grants discovered in the last 24 hours'
            })
        
        # Check AI performance
        ai_perf = report.get('ai_performance', {})
        if ai_perf.get('avg_confidence_score', 0) < 1.5:
            recommendations.append({
                'priority': 'medium',
                'category': 'ai',
                'action': 'Review and retrain AI matching algorithms',
                'reason': 'AI confidence scores are consistently low'
            })
        
        # Check profile completeness
        profiles = report.get('system_metrics', {})
        if profiles.get('total_organizations', 0) > 0:
            # Add profile-specific recommendations based on completeness
            recommendations.append({
                'priority': 'low',
                'category': 'profiles',
                'action': 'Encourage users to complete organization profiles',
                'reason': 'Better profiles improve AI matching accuracy'
            })
        
        return recommendations
    
    def _record_health_analytics(self, health_report: Dict):
        """Record health check results in analytics"""
        try:
            analytics = Analytics()
            analytics.event_type = 'health_check'
            analytics.event_data = {
                'overall_status': health_report.get('overall_status'),
                'component_count': len(health_report.get('components', {})),
                'alert_count': len(health_report.get('alerts', [])),
                'timestamp': health_report.get('timestamp')
            }
            analytics.created_at = datetime.utcnow()
            
            db.session.add(analytics)
            db.session.commit()
        except Exception as e:
            logger.error(f"Health analytics recording failed: {e}")
            db.session.rollback()