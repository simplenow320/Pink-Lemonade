"""
Integration Service - Phase 2 Implementation
Manages real-time data synchronization, automated monitoring, and cross-system communication
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from app import db
from app.models import Grant, Organization, Analytics, ScraperSource, ScraperHistory, Watchlist
from app.services.discovery import DiscoveryService
from app.services.ai_reasoning_engine import AIReasoningEngine
from app.services.notification_service import NotificationService
from app.services.monitoring_service import MonitoringService

logger = logging.getLogger(__name__)

class IntegrationService:
    """Orchestrates integration between all system components"""
    
    def __init__(self):
        self.discovery_service = DiscoveryService()
        self.ai_engine = AIReasoningEngine()
        self.notification_service = NotificationService()
        self.monitoring_service = MonitoringService()
    
    def run_full_discovery_cycle(self, org_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Run complete discovery and integration cycle
        Returns comprehensive status and results
        """
        start_time = datetime.utcnow()
        results = {
            'start_time': start_time.isoformat(),
            'discovery_stats': {},
            'ai_analysis': {},
            'notifications': [],
            'status': 'running'
        }
        
        try:
            # Step 1: Run discovery from all active sources
            logger.info("Starting discovery cycle")
            discovery_results = self.discovery_service.run_all_connectors()
            results['discovery_stats'] = discovery_results
            
            # Step 2: Get organization context if specified
            organization = None
            if org_id:
                organization = Organization.query.get(org_id)
            
            # Step 3: Process new grants with AI analysis
            new_grants = Grant.query.filter(
                Grant.created_at >= start_time - timedelta(hours=1)
            ).all()
            
            ai_analyses = []
            for grant in new_grants[:10]:  # Process up to 10 grants per cycle
                if organization:
                    grant_data = self._grant_to_analysis_format(grant)
                    analysis = self.ai_engine.analyze_grant_match(organization, grant_data)
                    ai_analyses.append({
                        'grant_id': grant.id,
                        'grant_title': grant.title,
                        'match_score': analysis.get('match_score', 0),
                        'confidence': analysis.get('confidence', 'low'),
                        'recommendation': analysis.get('recommendation', '')
                    })
            
            results['ai_analysis'] = {
                'grants_analyzed': len(ai_analyses),
                'high_matches': len([a for a in ai_analyses if a['match_score'] > 75]),
                'analyses': ai_analyses
            }
            
            # Step 4: Update watchlists and send notifications
            notifications_sent = self._process_watchlist_notifications(new_grants)
            results['notifications'] = notifications_sent
            
            # Step 5: Record analytics
            self._record_integration_analytics('discovery_cycle', results)
            
            results['status'] = 'completed'
            results['end_time'] = datetime.utcnow().isoformat()
            
            logger.info(f"Discovery cycle completed: {len(new_grants)} grants found")
            return results
            
        except Exception as e:
            logger.error(f"Discovery cycle failed: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
            results['end_time'] = datetime.utcnow().isoformat()
            return results
    
    def sync_organization_data(self, org_id: int) -> Dict[str, Any]:
        """
        Synchronize organization data across all systems
        """
        try:
            organization = Organization.query.get(org_id)
            if not organization:
                return {'success': False, 'error': 'Organization not found'}
            
            # Update completeness score
            completeness = organization.calculate_completeness()
            organization.profile_completeness = completeness
            
            # Sync AI learning data
            try:
                from app.services.ai_learning_system import AILearningSystem
                ai_learning = AILearningSystem()
                insights = ai_learning.get_personalized_insights(org_id)
                # Store insights as JSON in event_data field or similar
            except ImportError:
                insights = None
            
            # Update analytics
            self._record_integration_analytics('org_sync', {
                'org_id': org_id,
                'completeness': completeness,
                'sync_time': datetime.utcnow().isoformat()
            })
            
            db.session.commit()
            
            return {
                'success': True,
                'organization_id': org_id,
                'completeness': completeness,
                'last_sync': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Organization sync failed: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def process_real_time_grants(self, source: str, grants_data: List[Dict]) -> Dict[str, Any]:
        """
        Process grants from real-time sources with immediate AI analysis
        """
        try:
            processed_grants = []
            
            for grant_data in grants_data:
                # Create or update grant
                grant = self._create_or_update_grant(grant_data, source)
                
                if grant:
                    # Get all organizations for quick matching
                    organizations = Organization.query.filter(
                        Organization.profile_completeness > 50
                    ).all()
                    
                    # Run AI analysis for high-completeness orgs
                    for org in organizations[:5]:  # Limit for performance
                        analysis = self.ai_engine.analyze_grant_match(org, grant_data)
                        
                        if analysis.get('match_score', 0) > 70:
                            # Record high-match event
                            self._record_integration_analytics('high_match', {
                                'grant_id': grant.id,
                                'org_id': org.id,
                                'match_score': analysis['match_score'],
                                'confidence': analysis['confidence']
                            })
                            
                            # Send notification if org has alerts enabled
                            self._send_match_notification(org, grant, analysis)
                    
                    processed_grants.append(grant.to_dict())
            
            return {
                'success': True,
                'grants_processed': len(processed_grants),
                'source': source,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Real-time processing failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_integration_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for integration monitoring
        """
        try:
            # System health
            health = self.monitoring_service.get_health_status()
            
            # Recent discovery stats
            recent_history = ScraperHistory.query.filter(
                ScraperHistory.start_time >= datetime.utcnow() - timedelta(days=7)
            ).order_by(ScraperHistory.start_time.desc()).limit(10).all()
            
            # AI analysis stats
            recent_analytics = Analytics.query.filter(
                Analytics.event_type.in_(['discovery_cycle', 'high_match']),
                Analytics.created_at >= datetime.utcnow() - timedelta(days=7)
            ).all()
            
            # Active watchlists
            active_watchlists = Watchlist.query.filter_by(is_active=True).count()
            
            # Grant discovery trends  
            discovery_trend = []
            for i in range(7):
                date = datetime.utcnow().date() - timedelta(days=i)
                grants_count = Grant.query.filter(
                    Grant.created_at >= datetime.combine(date, datetime.min.time()),
                    Grant.created_at < datetime.combine(date + timedelta(days=1), datetime.min.time())
                ).count()
                discovery_trend.append({
                    'date': date.isoformat(),
                    'grants_found': grants_count
                })
            
            return {
                'system_health': health,
                'discovery_history': [h.to_dict() for h in recent_history],
                'ai_analysis_stats': {
                    'total_analyses': len(recent_analytics),
                    'high_matches': len([a for a in recent_analytics if a.event_type == 'high_match']),
                    'avg_confidence': self._calculate_avg_confidence(recent_analytics)
                },
                'active_watchlists': active_watchlists,
                'discovery_trend': discovery_trend,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Dashboard data retrieval failed: {e}")
            return {'error': str(e)}
    
    def _grant_to_analysis_format(self, grant: Grant) -> Dict[str, Any]:
        """Convert Grant model to format expected by AI engine"""
        return {
            'title': grant.title,
            'funder': grant.funder,
            'amount_min': grant.amount_min,
            'amount_max': grant.amount_max,
            'deadline': grant.deadline.isoformat() if grant.deadline else None,
            'description': getattr(grant, 'ai_summary', '') or '',
            'eligibility': grant.eligibility.split('\n') if grant.eligibility else [],
            'focus_areas': [],  # Grant model doesn't have focus_area field
            'geographic_scope': grant.geography or '',
            'requirements': {}
        }
    
    def _create_or_update_grant(self, grant_data: Dict, source: str) -> Optional[Grant]:
        """Create or update grant from external data"""
        try:
            # Check for existing grant by title and funder
            existing = Grant.query.filter_by(
                title=grant_data.get('title'),
                funder=grant_data.get('funder')
            ).first()
            
            if existing:
                # Update existing grant
                existing.ai_summary = grant_data.get('description', existing.ai_summary)
                existing.amount_min = grant_data.get('amount_min', existing.amount_min)
                existing.amount_max = grant_data.get('amount_max', existing.amount_max)
                existing.updated_at = datetime.utcnow()
                db.session.commit()
                return existing
            else:
                # Create new grant
                grant = Grant()
                grant.title = grant_data.get('title')
                grant.funder = grant_data.get('funder')
                grant.ai_summary = grant_data.get('description')
                grant.amount_min = grant_data.get('amount_min')
                grant.amount_max = grant_data.get('amount_max')
                grant.geography = grant_data.get('geographic_scope')
                grant.source_url = grant_data.get('source_url')
                # Convert list to newline-separated string
                eligibility_list = grant_data.get('eligibility', [])
                grant.eligibility = '\n'.join(eligibility_list) if isinstance(eligibility_list, list) else str(eligibility_list)
                
                # Parse deadline
                deadline_str = grant_data.get('deadline')
                if deadline_str:
                    try:
                        grant.deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                    except:
                        pass
                
                db.session.add(grant)
                db.session.commit()
                return grant
                
        except Exception as e:
            logger.error(f"Grant creation/update failed: {e}")
            db.session.rollback()
            return None
    
    def _process_watchlist_notifications(self, new_grants: List[Grant]) -> List[Dict]:
        """Process watchlists and send notifications for matching grants"""
        notifications = []
        
        try:
            active_watchlists = Watchlist.query.filter_by(is_active=True).all()
            
            for watchlist in active_watchlists:
                matching_grants = self._find_matching_grants(watchlist, new_grants)
                
                if matching_grants and (watchlist.notify_email or watchlist.notify_app):
                    notification = {
                        'watchlist_id': watchlist.id,
                        'watchlist_name': watchlist.name,
                        'matching_grants': len(matching_grants),
                        'sent_at': datetime.utcnow().isoformat()
                    }
                    
                    # Send notification (implementation depends on notification service)
                    if watchlist.notify_email:
                        logger.info(f"Watchlist notification: {watchlist.name}, {len(matching_grants)} matches")
                        # TODO: Implement actual notification when service method is available
                    
                    notifications.append(notification)
            
        except Exception as e:
            logger.error(f"Watchlist notification processing failed: {e}")
        
        return notifications
    
    def _find_matching_grants(self, watchlist: Watchlist, grants: List[Grant]) -> List[Grant]:
        """Find grants matching watchlist criteria"""
        matching = []
        # Watchlist model may not have criteria field in current schema
        criteria = getattr(watchlist, 'criteria', {}) or {}
        
        for grant in grants:
            matches = True
            
            # Check query terms
            query = criteria.get('query', '').lower()
            if query:
                if query not in (grant.title or '').lower() and query not in (grant.ai_summary or '').lower():
                    matches = False
            
            # Check focus area (not available in current Grant model)
            focus_area = criteria.get('focus_area')
            if focus_area:
                # Could match against ai_summary or other fields
                if focus_area.lower() not in (grant.ai_summary or '').lower():
                    matches = False
            
            # Check location
            location = criteria.get('location')
            if location and location not in (grant.geography or ''):
                matches = False
            
            if matches:
                matching.append(grant)
        
        return matching
    
    def _send_match_notification(self, org: Organization, grant: Grant, analysis: Dict):
        """Send notification for high-match grant"""
        try:
            # Use available notification methods
            logger.info(f"High match notification: Org {org.id}, Grant {grant.id}, Score {analysis.get('match_score', 0)}")
            # TODO: Implement actual notification sending when service methods are available
        except Exception as e:
            logger.error(f"Match notification failed: {e}")
    
    def _record_integration_analytics(self, event_type: str, data: Dict):
        """Record analytics event for integration tracking"""
        try:
            analytics = Analytics()
            analytics.event_type = event_type
            analytics.event_data = data
            analytics.created_at = datetime.utcnow()
            
            db.session.add(analytics)
            db.session.commit()
        except Exception as e:
            logger.error(f"Analytics recording failed: {e}")
            db.session.rollback()
    
    def _calculate_avg_confidence(self, analytics: List[Analytics]) -> str:
        """Calculate average confidence from analytics events"""
        confidences = []
        confidence_values = {'low': 1, 'medium': 2, 'high': 3}
        
        for analytic in analytics:
            event_data = analytic.event_data or {}
            confidence = event_data.get('confidence', 'low')
            if confidence in confidence_values:
                confidences.append(confidence_values[confidence])
        
        if not confidences:
            return 'low'
        
        avg_value = sum(confidences) / len(confidences)
        if avg_value <= 1.3:
            return 'low'
        elif avg_value <= 2.3:
            return 'medium'
        else:
            return 'high'