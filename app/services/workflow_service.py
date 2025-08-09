"""
Grant Application Workflow Service
Manages grant lifecycle from discovery to decision
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.models import Grant, GrantDocument, GrantActivity
from app import db
import logging

logger = logging.getLogger(__name__)

class GrantWorkflowService:
    """Manages grant application workflow and status transitions"""
    
    WORKFLOW_STAGES = {
        'discovered': {
            'name': 'Discovered',
            'next': ['researching', 'saved', 'rejected'],
            'color': '#9CA3AF',
            'icon': '🔍'
        },
        'saved': {
            'name': 'Saved for Later',
            'next': ['researching', 'rejected'],
            'color': '#3B82F6',
            'icon': '📌'
        },
        'researching': {
            'name': 'Researching',
            'next': ['preparing', 'saved', 'rejected'],
            'color': '#8B5CF6',
            'icon': '📚'
        },
        'preparing': {
            'name': 'Preparing Application',
            'next': ['applying', 'saved', 'rejected'],
            'color': '#F59E0B',
            'icon': '✍️'
        },
        'applying': {
            'name': 'Application in Progress',
            'next': ['submitted', 'saved', 'rejected'],
            'color': '#EF4444',
            'icon': '📝'
        },
        'submitted': {
            'name': 'Submitted',
            'next': ['under_review', 'rejected'],
            'color': '#10B981',
            'icon': '✅'
        },
        'under_review': {
            'name': 'Under Review',
            'next': ['awarded', 'rejected'],
            'color': '#6366F1',
            'icon': '⏳'
        },
        'awarded': {
            'name': 'Awarded',
            'next': [],
            'color': '#059669',
            'icon': '🎉'
        },
        'rejected': {
            'name': 'Rejected/Not Pursuing',
            'next': ['saved'],
            'color': '#DC2626',
            'icon': '❌'
        }
    }
    
    def __init__(self):
        self.stages = self.WORKFLOW_STAGES
    
    def transition_grant(self, grant_id: int, new_status: str, notes: str = None, user_id: int = None) -> Dict:
        """
        Transition a grant to a new status
        """
        try:
            grant = Grant.query.get(grant_id)
            if not grant:
                return {'success': False, 'error': 'Grant not found'}
            
            current_status = grant.status or 'discovered'
            
            # Check if transition is valid
            if new_status not in self.stages:
                return {'success': False, 'error': f'Invalid status: {new_status}'}
            
            if current_status in self.stages:
                allowed_transitions = self.stages[current_status]['next']
                if new_status not in allowed_transitions and new_status != current_status:
                    return {
                        'success': False, 
                        'error': f'Cannot transition from {current_status} to {new_status}'
                    }
            
            # Update grant status
            old_status = grant.status
            grant.status = new_status
            grant.updated_at = datetime.now()
            
            # Log activity
            activity = GrantActivity()
            activity.grant_id = grant_id
            activity.user_id = user_id
            activity.action = 'status_change'
            activity.details = {
                'from': old_status,
                'to': new_status,
                'notes': notes
            }
            activity.created_at = datetime.now()
            
            db.session.add(activity)
            db.session.commit()
            
            return {
                'success': True,
                'grant_id': grant_id,
                'old_status': old_status,
                'new_status': new_status,
                'stage_info': self.stages[new_status]
            }
            
        except Exception as e:
            logger.error(f"Error transitioning grant {grant_id}: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_grant_timeline(self, grant_id: int) -> List[Dict]:
        """
        Get the activity timeline for a grant
        """
        try:
            activities = GrantActivity.query.filter_by(grant_id=grant_id)\
                .order_by(GrantActivity.created_at.desc()).all()
            
            timeline = []
            for activity in activities:
                timeline.append({
                    'id': activity.id,
                    'action': activity.action,
                    'details': activity.details,
                    'user_id': activity.user_id,
                    'timestamp': activity.created_at.isoformat()
                })
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error getting timeline for grant {grant_id}: {e}")
            return []
    
    def get_grants_by_stage(self, org_id: int) -> Dict[str, List[Dict]]:
        """
        Get all grants organized by workflow stage
        """
        try:
            grants_by_stage = {}
            
            for stage_key in self.stages:
                grants = Grant.query.filter_by(
                    org_id=org_id,
                    status=stage_key
                ).order_by(Grant.deadline.asc()).all()
                
                grants_by_stage[stage_key] = [grant.to_dict() for grant in grants]
            
            return grants_by_stage
            
        except Exception as e:
            logger.error(f"Error getting grants by stage: {e}")
            return {}
    
    def get_upcoming_deadlines(self, org_id: int, days_ahead: int = 30) -> List[Dict]:
        """
        Get grants with upcoming deadlines
        """
        try:
            cutoff_date = datetime.now() + timedelta(days=days_ahead)
            
            grants = Grant.query.filter(
                Grant.org_id == org_id,
                Grant.deadline != None,
                Grant.deadline <= cutoff_date,
                Grant.deadline >= datetime.now(),
                Grant.status.in_(['researching', 'preparing', 'applying'])
            ).order_by(Grant.deadline.asc()).all()
            
            deadlines = []
            for grant in grants:
                days_until = (grant.deadline - datetime.now()).days
                
                urgency = 'low'
                if days_until <= 7:
                    urgency = 'critical'
                elif days_until <= 14:
                    urgency = 'high'
                elif days_until <= 21:
                    urgency = 'medium'
                
                deadlines.append({
                    'grant_id': grant.id,
                    'title': grant.title,
                    'funder': grant.funder,
                    'deadline': grant.deadline.isoformat(),
                    'days_until': days_until,
                    'status': grant.status,
                    'urgency': urgency,
                    'amount_max': grant.amount_max
                })
            
            return deadlines
            
        except Exception as e:
            logger.error(f"Error getting upcoming deadlines: {e}")
            return []
    
    def calculate_success_metrics(self, org_id: int) -> Dict:
        """
        Calculate grant application success metrics
        """
        try:
            total_grants = Grant.query.filter_by(org_id=org_id).count()
            
            metrics = {
                'total_discovered': total_grants,
                'in_progress': Grant.query.filter_by(org_id=org_id).filter(
                    Grant.status.in_(['researching', 'preparing', 'applying'])
                ).count(),
                'submitted': Grant.query.filter_by(org_id=org_id, status='submitted').count(),
                'under_review': Grant.query.filter_by(org_id=org_id, status='under_review').count(),
                'awarded': Grant.query.filter_by(org_id=org_id, status='awarded').count(),
                'rejected': Grant.query.filter_by(org_id=org_id, status='rejected').count(),
                'success_rate': 0,
                'total_awarded_amount': 0
            }
            
            # Calculate success rate
            total_decided = metrics['awarded'] + metrics['rejected']
            if total_decided > 0:
                metrics['success_rate'] = round((metrics['awarded'] / total_decided) * 100, 1)
            
            # Calculate total awarded amount
            awarded_grants = Grant.query.filter_by(org_id=org_id, status='awarded').all()
            for grant in awarded_grants:
                if grant.amount_max:
                    metrics['total_awarded_amount'] += grant.amount_max
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating success metrics: {e}")
            return {}

# Singleton instance
workflow_service = GrantWorkflowService()