"""
PHASE 2: Automated Application Workflow Engine
Streamlines grant application tracking, deadlines, and collaboration
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from sqlalchemy import and_, or_
from app.models import db, Grant, Organization, User, LovedGrant
from app.services.ai_service import ai_service
from app.services.phase1_matching_engine import phase1_engine

logger = logging.getLogger(__name__)

class Phase2ApplicationWorkflow:
    """Automated workflow management for grant applications"""
    
    # Application stages
    STAGES = {
        'discovery': {'order': 1, 'name': 'Discovery', 'icon': 'search'},
        'research': {'order': 2, 'name': 'Research', 'icon': 'book'},
        'draft': {'order': 3, 'name': 'Drafting', 'icon': 'edit'},
        'review': {'order': 4, 'name': 'Review', 'icon': 'check-circle'},
        'submitted': {'order': 5, 'name': 'Submitted', 'icon': 'send'},
        'pending': {'order': 6, 'name': 'Pending Decision', 'icon': 'clock'},
        'awarded': {'order': 7, 'name': 'Awarded', 'icon': 'award'},
        'rejected': {'order': 8, 'name': 'Not Awarded', 'icon': 'x-circle'}
    }
    
    # Priority levels based on deadlines
    PRIORITY_LEVELS = {
        'urgent': {'days': 7, 'color': '#EF4444'},  # Red
        'high': {'days': 14, 'color': '#F59E0B'},   # Orange
        'medium': {'days': 30, 'color': '#3B82F6'}, # Blue
        'low': {'days': 90, 'color': '#10B981'}     # Green
    }
    
    def create_application(self, grant_data: Dict, user_id: int) -> Dict:
        """
        Create a new grant application with workflow tracking
        
        Args:
            grant_data: Grant opportunity data
            user_id: User creating the application
            
        Returns:
            Created application data
        """
        try:
            # Get organization
            org = Organization.query.filter_by(created_by_user_id=user_id).first()
            if not org:
                return {'success': False, 'error': 'Organization profile required'}
            
            # Calculate priority based on deadline
            priority = self._calculate_priority(grant_data.get('deadline'))
            
            # Create grant application
            grant = Grant(
                user_id=user_id,
                grant_name=grant_data.get('title', 'Untitled Grant'),
                funding_organization=grant_data.get('funder', ''),
                grant_amount=self._parse_amount(grant_data.get('amount_range', '')),
                submission_deadline=self._parse_deadline(grant_data.get('deadline')),
                status='discovery',
                match_score=grant_data.get('match_score', 0),
                application_stage='discovery',
                priority_level=priority,
                source_url=grant_data.get('url', ''),
                requirements=grant_data.get('requirements', {}),
                team_members=[user_id],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(grant)
            db.session.commit()
            
            # Generate initial checklist
            checklist = self._generate_checklist(grant)
            grant.checklist = checklist
            db.session.commit()
            
            return {
                'success': True,
                'application_id': grant.id,
                'stage': 'discovery',
                'priority': priority,
                'checklist': checklist,
                'deadline_days': self._days_until_deadline(grant.submission_deadline)
            }
            
        except Exception as e:
            logger.error(f"Error creating application: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def update_stage(self, application_id: int, new_stage: str, notes: str = "") -> Dict:
        """
        Move application to new stage in workflow
        
        Args:
            application_id: Grant application ID
            new_stage: New stage name
            notes: Optional notes about the transition
            
        Returns:
            Update result
        """
        try:
            grant = Grant.query.get(application_id)
            if not grant:
                return {'success': False, 'error': 'Application not found'}
            
            if new_stage not in self.STAGES:
                return {'success': False, 'error': 'Invalid stage'}
            
            # Record stage transition
            old_stage = grant.application_stage
            grant.application_stage = new_stage
            grant.updated_at = datetime.utcnow()
            
            # Add to activity log
            if not hasattr(grant, 'activity_log'):
                grant.activity_log = []
            
            grant.activity_log.append({
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'stage_change',
                'from_stage': old_stage,
                'to_stage': new_stage,
                'notes': notes
            })
            
            # Update status based on stage
            if new_stage == 'submitted':
                grant.status = 'submitted'
            elif new_stage == 'awarded':
                grant.status = 'awarded'
            elif new_stage == 'rejected':
                grant.status = 'rejected'
            
            db.session.commit()
            
            # Generate next steps
            next_steps = self._get_next_steps(new_stage)
            
            return {
                'success': True,
                'new_stage': new_stage,
                'old_stage': old_stage,
                'next_steps': next_steps,
                'stage_info': self.STAGES[new_stage]
            }
            
        except Exception as e:
            logger.error(f"Error updating stage: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_applications_by_stage(self, user_id: int) -> Dict:
        """
        Get all applications organized by workflow stage
        
        Args:
            user_id: User ID
            
        Returns:
            Applications grouped by stage
        """
        try:
            grants = Grant.query.filter_by(user_id=user_id).all()
            
            # Group by stage
            staged_apps = {}
            for stage_key, stage_info in self.STAGES.items():
                staged_apps[stage_key] = {
                    'info': stage_info,
                    'applications': [],
                    'count': 0
                }
            
            for grant in grants:
                stage = grant.application_stage or 'discovery'
                if stage in staged_apps:
                    app_data = {
                        'id': grant.id,
                        'title': grant.grant_name,
                        'funder': grant.funding_organization,
                        'amount': grant.grant_amount,
                        'deadline': grant.submission_deadline.isoformat() if grant.submission_deadline else None,
                        'priority': grant.priority_level,
                        'match_score': grant.match_score,
                        'days_left': self._days_until_deadline(grant.submission_deadline)
                    }
                    staged_apps[stage]['applications'].append(app_data)
                    staged_apps[stage]['count'] += 1
            
            # Calculate metrics
            metrics = self._calculate_workflow_metrics(grants)
            
            return {
                'success': True,
                'stages': staged_apps,
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting staged applications: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_upcoming_deadlines(self, user_id: int, days_ahead: int = 30) -> List[Dict]:
        """
        Get applications with upcoming deadlines
        
        Args:
            user_id: User ID
            days_ahead: Number of days to look ahead
            
        Returns:
            List of applications with deadlines
        """
        try:
            cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
            
            grants = Grant.query.filter(
                and_(
                    Grant.user_id == user_id,
                    Grant.submission_deadline != None,
                    Grant.submission_deadline <= cutoff_date,
                    Grant.status.notin_(['submitted', 'awarded', 'rejected'])
                )
            ).order_by(Grant.submission_deadline).all()
            
            deadlines = []
            for grant in grants:
                days_left = self._days_until_deadline(grant.submission_deadline)
                priority = self._calculate_priority(grant.submission_deadline)
                
                deadlines.append({
                    'id': grant.id,
                    'title': grant.grant_name,
                    'funder': grant.funding_organization,
                    'deadline': grant.submission_deadline.isoformat(),
                    'days_left': days_left,
                    'priority': priority,
                    'stage': grant.application_stage,
                    'completion_percentage': self._calculate_completion(grant)
                })
            
            return deadlines
            
        except Exception as e:
            logger.error(f"Error getting deadlines: {e}")
            return []
    
    def generate_reminders(self, user_id: int) -> List[Dict]:
        """
        Generate smart reminders for grant applications
        
        Args:
            user_id: User ID
            
        Returns:
            List of reminders
        """
        try:
            reminders = []
            
            # Get active applications
            grants = Grant.query.filter(
                and_(
                    Grant.user_id == user_id,
                    Grant.status.notin_(['awarded', 'rejected'])
                )
            ).all()
            
            for grant in grants:
                # Deadline reminders
                if grant.submission_deadline:
                    days_left = self._days_until_deadline(grant.submission_deadline)
                    
                    if days_left <= 3:
                        reminders.append({
                            'type': 'urgent',
                            'application_id': grant.id,
                            'title': f"URGENT: {grant.grant_name}",
                            'message': f"Deadline in {days_left} days!",
                            'action': 'Complete and submit immediately'
                        })
                    elif days_left <= 7:
                        reminders.append({
                            'type': 'high',
                            'application_id': grant.id,
                            'title': f"Week to deadline: {grant.grant_name}",
                            'message': f"Only {days_left} days remaining",
                            'action': 'Finalize application'
                        })
                    elif days_left <= 14 and grant.application_stage in ['discovery', 'research']:
                        reminders.append({
                            'type': 'medium',
                            'application_id': grant.id,
                            'title': f"Start drafting: {grant.grant_name}",
                            'message': f"{days_left} days until deadline",
                            'action': 'Begin writing application'
                        })
                
                # Stage reminders
                if grant.application_stage == 'draft' and grant.updated_at:
                    days_since_update = (datetime.utcnow() - grant.updated_at).days
                    if days_since_update > 5:
                        reminders.append({
                            'type': 'medium',
                            'application_id': grant.id,
                            'title': f"Continue drafting: {grant.grant_name}",
                            'message': f"Draft inactive for {days_since_update} days",
                            'action': 'Resume writing'
                        })
            
            # Sort by priority
            priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
            reminders.sort(key=lambda x: priority_order.get(x['type'], 99))
            
            return reminders
            
        except Exception as e:
            logger.error(f"Error generating reminders: {e}")
            return []
    
    def add_team_member(self, application_id: int, email: str, role: str = "collaborator") -> Dict:
        """
        Add team member to grant application
        
        Args:
            application_id: Grant application ID
            email: Team member email
            role: Member role (owner, editor, viewer)
            
        Returns:
            Result of adding member
        """
        try:
            grant = Grant.query.get(application_id)
            if not grant:
                return {'success': False, 'error': 'Application not found'}
            
            # Find user by email
            user = User.query.filter_by(email=email).first()
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Add to team
            if not hasattr(grant, 'team_members'):
                grant.team_members = []
            
            if user.id not in grant.team_members:
                grant.team_members.append(user.id)
                
                # Add to activity log
                if not hasattr(grant, 'activity_log'):
                    grant.activity_log = []
                
                grant.activity_log.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'action': 'team_member_added',
                    'user_id': user.id,
                    'email': email,
                    'role': role
                })
                
                db.session.commit()
                
                return {
                    'success': True,
                    'message': f"Added {email} as {role}",
                    'team_size': len(grant.team_members)
                }
            else:
                return {'success': False, 'error': 'User already on team'}
                
        except Exception as e:
            logger.error(f"Error adding team member: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def _calculate_priority(self, deadline) -> str:
        """Calculate priority level based on deadline"""
        if not deadline:
            return 'low'
        
        if isinstance(deadline, str):
            try:
                deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            except:
                return 'low'
        
        days_left = (deadline - datetime.utcnow()).days
        
        if days_left <= 7:
            return 'urgent'
        elif days_left <= 14:
            return 'high'
        elif days_left <= 30:
            return 'medium'
        else:
            return 'low'
    
    def _days_until_deadline(self, deadline) -> int:
        """Calculate days until deadline"""
        if not deadline:
            return 999
        
        if isinstance(deadline, str):
            try:
                deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            except:
                return 999
        
        days = (deadline - datetime.utcnow()).days
        return max(0, days)
    
    def _parse_amount(self, amount_str: str) -> int:
        """Parse grant amount from string"""
        if not amount_str or amount_str == 'Varies':
            return 0
        
        # Remove currency symbols and commas
        import re
        numbers = re.findall(r'[\d,]+', amount_str.replace('$', ''))
        if numbers:
            return int(numbers[0].replace(',', ''))
        return 0
    
    def _parse_deadline(self, deadline_str):
        """Parse deadline from various formats"""
        if not deadline_str or deadline_str == 'See article':
            return None
        
        try:
            if isinstance(deadline_str, str):
                return datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
            return deadline_str
        except:
            return None
    
    def _generate_checklist(self, grant: Grant) -> List[Dict]:
        """Generate application checklist based on grant type"""
        checklist = [
            {'task': 'Review grant guidelines', 'completed': False, 'stage': 'research'},
            {'task': 'Confirm eligibility', 'completed': False, 'stage': 'research'},
            {'task': 'Gather required documents', 'completed': False, 'stage': 'research'},
            {'task': 'Write executive summary', 'completed': False, 'stage': 'draft'},
            {'task': 'Develop project narrative', 'completed': False, 'stage': 'draft'},
            {'task': 'Create detailed budget', 'completed': False, 'stage': 'draft'},
            {'task': 'Collect letters of support', 'completed': False, 'stage': 'draft'},
            {'task': 'Internal review', 'completed': False, 'stage': 'review'},
            {'task': 'Final proofread', 'completed': False, 'stage': 'review'},
            {'task': 'Submit application', 'completed': False, 'stage': 'submitted'}
        ]
        
        # Add funder-specific items
        if 'federal' in grant.funding_organization.lower():
            checklist.insert(2, {'task': 'Register in SAM.gov', 'completed': False, 'stage': 'research'})
            checklist.insert(3, {'task': 'Obtain UEI number', 'completed': False, 'stage': 'research'})
        
        return checklist
    
    def _get_next_steps(self, stage: str) -> List[str]:
        """Get recommended next steps for a stage"""
        next_steps = {
            'discovery': [
                'Review full grant guidelines',
                'Confirm organization eligibility',
                'Set internal deadline 1 week before'
            ],
            'research': [
                'Gather past successful applications',
                'Identify required attachments',
                'Assign team responsibilities'
            ],
            'draft': [
                'Complete narrative sections',
                'Develop evaluation plan',
                'Finalize budget justification'
            ],
            'review': [
                'Conduct team review session',
                'Check all requirements met',
                'Prepare submission materials'
            ],
            'submitted': [
                'Save confirmation receipt',
                'Calendar follow-up dates',
                'Prepare for possible questions'
            ],
            'pending': [
                'Monitor for updates',
                'Prepare additional info if requested',
                'Plan for either outcome'
            ],
            'awarded': [
                'Review award terms',
                'Set up tracking systems',
                'Schedule kickoff meeting'
            ],
            'rejected': [
                'Request reviewer feedback',
                'Document lessons learned',
                'Identify similar opportunities'
            ]
        }
        
        return next_steps.get(stage, [])
    
    def _calculate_completion(self, grant: Grant) -> int:
        """Calculate application completion percentage"""
        if not hasattr(grant, 'checklist'):
            return 0
        
        total_tasks = len(grant.checklist)
        if total_tasks == 0:
            return 0
        
        completed_tasks = sum(1 for task in grant.checklist if task.get('completed'))
        return int((completed_tasks / total_tasks) * 100)
    
    def _calculate_workflow_metrics(self, grants: List[Grant]) -> Dict:
        """Calculate workflow performance metrics"""
        total = len(grants)
        if total == 0:
            return {
                'total_applications': 0,
                'active_applications': 0,
                'success_rate': 0,
                'average_days_to_submit': 0
            }
        
        active = sum(1 for g in grants if g.status not in ['awarded', 'rejected'])
        awarded = sum(1 for g in grants if g.status == 'awarded')
        completed = sum(1 for g in grants if g.status in ['awarded', 'rejected'])
        
        success_rate = (awarded / completed * 100) if completed > 0 else 0
        
        # Calculate average time to submission
        submission_times = []
        for grant in grants:
            if grant.status == 'submitted' and grant.created_at:
                days = (datetime.utcnow() - grant.created_at).days
                submission_times.append(days)
        
        avg_days = sum(submission_times) / len(submission_times) if submission_times else 0
        
        return {
            'total_applications': total,
            'active_applications': active,
            'success_rate': round(success_rate, 1),
            'average_days_to_submit': round(avg_days, 1),
            'awarded_count': awarded,
            'pending_count': sum(1 for g in grants if g.status == 'pending')
        }

# Singleton instance
phase2_workflow = Phase2ApplicationWorkflow()