"""
Grant Workflow Manager
Handles 8-stage grant pipeline with automation
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app.models import Grant, Organization, User, db
import logging

logger = logging.getLogger(__name__)

class WorkflowManager:
    """
    Manages grant lifecycle through 8 stages:
    1. Discovery - Finding new opportunities
    2. Researching - Evaluating fit and requirements
    3. Writing - Preparing application materials
    4. Review - Internal review before submission
    5. Submitted - Application sent to funder
    6. Pending - Awaiting funder decision
    7. Awarded - Grant won (or Declined)
    8. Reporting - Post-award compliance
    """
    
    STAGES = {
        'discovery': {
            'order': 1,
            'name': 'Discovery',
            'description': 'Finding and evaluating opportunities',
            'next': 'researching',
            'color': '#E5E7EB',  # Gray
            'icon': '🔍',
            'auto_actions': ['fetch_grant_details', 'calculate_match_score'],
            'required_fields': ['title', 'funder'],
            'typical_duration': 7  # days
        },
        'researching': {
            'order': 2,
            'name': 'Researching',
            'description': 'Gathering requirements and funder intel',
            'next': 'writing',
            'color': '#DBEAFE',  # Blue
            'icon': '📚',
            'auto_actions': ['analyze_requirements', 'check_eligibility'],
            'required_fields': ['eligibility', 'requirements_summary'],
            'typical_duration': 14
        },
        'writing': {
            'order': 3,
            'name': 'Writing',
            'description': 'Drafting application and narratives',
            'next': 'review',
            'color': '#FEF3C7',  # Yellow
            'icon': '✍️',
            'auto_actions': ['generate_narratives', 'create_checklist'],
            'required_fields': ['narratives', 'budget'],
            'typical_duration': 21
        },
        'review': {
            'order': 4,
            'name': 'Review',
            'description': 'Internal review and refinement',
            'next': 'submitted',
            'color': '#F3E8FF',  # Purple
            'icon': '👀',
            'auto_actions': ['quality_check', 'completeness_check'],
            'required_fields': ['review_notes', 'approval'],
            'typical_duration': 3
        },
        'submitted': {
            'order': 5,
            'name': 'Submitted',
            'description': 'Application sent to funder',
            'next': 'pending',
            'color': '#D1FAE5',  # Green
            'icon': '📮',
            'auto_actions': ['log_submission', 'set_reminder'],
            'required_fields': ['submission_date', 'confirmation'],
            'typical_duration': 1
        },
        'pending': {
            'order': 6,
            'name': 'Pending',
            'description': 'Awaiting funder decision',
            'next': 'awarded',
            'color': '#FED7AA',  # Orange
            'icon': '⏳',
            'auto_actions': ['track_status', 'send_reminders'],
            'required_fields': ['expected_decision_date'],
            'typical_duration': 90
        },
        'awarded': {
            'order': 7,
            'name': 'Awarded',
            'description': 'Grant won - implementation phase',
            'next': 'reporting',
            'color': '#BBF7D0',  # Bright Green
            'icon': '🎉',
            'auto_actions': ['notify_team', 'setup_reporting'],
            'required_fields': ['award_amount', 'award_date'],
            'typical_duration': 365
        },
        'declined': {
            'order': 7,
            'name': 'Declined',
            'description': 'Application not funded',
            'next': None,
            'color': '#FECACA',  # Red
            'icon': '❌',
            'auto_actions': ['log_feedback', 'archive'],
            'required_fields': ['decline_reason'],
            'typical_duration': 0
        },
        'reporting': {
            'order': 8,
            'name': 'Reporting',
            'description': 'Post-award compliance and reporting',
            'next': None,
            'color': '#C7D2FE',  # Indigo
            'icon': '📊',
            'auto_actions': ['schedule_reports', 'track_metrics'],
            'required_fields': ['report_schedule', 'metrics'],
            'typical_duration': 365
        }
    }
    
    def __init__(self):
        self.stage_validators = {
            'discovery': self._validate_discovery,
            'researching': self._validate_researching,
            'writing': self._validate_writing,
            'review': self._validate_review,
            'submitted': self._validate_submitted,
            'pending': self._validate_pending,
            'awarded': self._validate_awarded,
            'reporting': self._validate_reporting
        }
    
    def get_pipeline_status(self, org_id: int) -> Dict:
        """Get complete pipeline status for an organization"""
        try:
            # Get grants grouped by stage
            grants = Grant.query.filter_by(org_id=org_id).all()
            
            pipeline = {}
            for stage_key, stage_info in self.STAGES.items():
                stage_grants = [g for g in grants if g.application_stage == stage_key]
                pipeline[stage_key] = {
                    'info': stage_info,
                    'count': len(stage_grants),
                    'grants': [self._grant_summary(g) for g in stage_grants[:5]],  # Top 5
                    'total_value': sum(g.amount_max or 0 for g in stage_grants)
                }
            
            # Calculate metrics
            total_grants = len(grants)
            in_progress = len([g for g in grants if g.application_stage not in ['awarded', 'declined']])
            success_rate = self._calculate_success_rate(grants)
            
            return {
                'success': True,
                'pipeline': pipeline,
                'metrics': {
                    'total_grants': total_grants,
                    'in_progress': in_progress,
                    'success_rate': success_rate,
                    'total_potential': sum(g.amount_max or 0 for g in grants),
                    'next_deadline': self._get_next_deadline(grants)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return {'success': False, 'error': str(e)}
    
    def move_to_stage(self, grant_id: int, new_stage: str, notes: str = None) -> Dict:
        """Move grant to a new stage with validation"""
        try:
            grant = Grant.query.get(grant_id)
            if not grant:
                return {'success': False, 'error': 'Grant not found'}
            
            # Validate stage transition
            current_stage = grant.application_stage or 'discovery'
            if new_stage not in self.STAGES:
                return {'success': False, 'error': f'Invalid stage: {new_stage}'}
            
            # Check if transition is allowed
            allowed_next = self.STAGES[current_stage].get('next')
            if allowed_next and new_stage != allowed_next and new_stage != 'declined':
                # Allow skipping stages forward but log it
                logger.warning(f"Skipping stages: {current_stage} -> {new_stage}")
            
            # Validate requirements for new stage
            validation = self._validate_stage_requirements(grant, new_stage)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': f"Missing requirements for {new_stage}",
                    'missing': validation['missing']
                }
            
            # Update grant
            old_stage = grant.application_stage
            grant.application_stage = new_stage
            grant.updated_at = datetime.utcnow()
            
            # Log activity
            activity = {
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'stage_change',
                'from': old_stage,
                'to': new_stage,
                'notes': notes,
                'user': 'system'  # Would get from current_user in real app
            }
            
            if not grant.activity_log:
                grant.activity_log = []
            grant.activity_log.append(activity)
            
            # Execute auto actions
            self._execute_auto_actions(grant, new_stage)
            
            db.session.commit()
            
            return {
                'success': True,
                'grant_id': grant_id,
                'old_stage': old_stage,
                'new_stage': new_stage,
                'stage_info': self.STAGES[new_stage]
            }
            
        except Exception as e:
            logger.error(f"Error moving grant to stage: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def batch_move(self, grant_ids: List[int], new_stage: str) -> Dict:
        """Move multiple grants to same stage"""
        results = []
        for grant_id in grant_ids:
            result = self.move_to_stage(grant_id, new_stage)
            results.append({
                'grant_id': grant_id,
                'success': result['success'],
                'error': result.get('error')
            })
        
        successful = sum(1 for r in results if r['success'])
        return {
            'success': successful > 0,
            'moved': successful,
            'failed': len(results) - successful,
            'results': results
        }
    
    def get_stage_checklist(self, grant_id: int) -> Dict:
        """Get checklist for current grant stage"""
        try:
            grant = Grant.query.get(grant_id)
            if not grant:
                return {'success': False, 'error': 'Grant not found'}
            
            stage = grant.application_stage or 'discovery'
            stage_info = self.STAGES[stage]
            
            # Generate checklist based on stage
            checklist = self._generate_checklist(grant, stage)
            
            # Check completion status
            completed_items = grant.checklist or {}
            for item in checklist:
                item['completed'] = completed_items.get(item['id'], False)
            
            completion_rate = sum(1 for i in checklist if i['completed']) / len(checklist) if checklist else 0
            
            return {
                'success': True,
                'stage': stage,
                'stage_info': stage_info,
                'checklist': checklist,
                'completion_rate': completion_rate,
                'ready_to_advance': completion_rate >= 0.8  # 80% threshold
            }
            
        except Exception as e:
            logger.error(f"Error getting checklist: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_checklist_item(self, grant_id: int, item_id: str, completed: bool) -> Dict:
        """Update a checklist item status"""
        try:
            grant = Grant.query.get(grant_id)
            if not grant:
                return {'success': False, 'error': 'Grant not found'}
            
            if not grant.checklist:
                grant.checklist = {}
            
            grant.checklist[item_id] = completed
            grant.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'grant_id': grant_id,
                'item_id': item_id,
                'completed': completed
            }
            
        except Exception as e:
            logger.error(f"Error updating checklist: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    # Private helper methods
    
    def _grant_summary(self, grant: Grant) -> Dict:
        """Create summary dict for a grant"""
        return {
            'id': grant.id,
            'title': grant.title[:50] + '...' if len(grant.title) > 50 else grant.title,
            'funder': grant.funder,
            'amount': grant.amount_max,
            'deadline': grant.deadline.isoformat() if grant.deadline else None,
            'days_remaining': (grant.deadline - datetime.now().date()).days if grant.deadline else None
        }
    
    def _calculate_success_rate(self, grants: List[Grant]) -> float:
        """Calculate grant success rate"""
        completed = [g for g in grants if g.application_stage in ['awarded', 'declined']]
        if not completed:
            return 0.0
        awarded = len([g for g in completed if g.application_stage == 'awarded'])
        return (awarded / len(completed)) * 100
    
    def _get_next_deadline(self, grants: List[Grant]) -> Optional[str]:
        """Get next upcoming deadline"""
        future_deadlines = [
            g.deadline for g in grants 
            if g.deadline and g.deadline > datetime.now().date()
        ]
        if future_deadlines:
            return min(future_deadlines).isoformat()
        return None
    
    def _validate_stage_requirements(self, grant: Grant, stage: str) -> Dict:
        """Validate if grant meets requirements for stage"""
        if stage not in self.stage_validators:
            return {'valid': True, 'missing': []}
        
        return self.stage_validators[stage](grant)
    
    def _validate_discovery(self, grant: Grant) -> Dict:
        """Validate discovery stage requirements"""
        missing = []
        if not grant.title:
            missing.append('title')
        if not grant.funder:
            missing.append('funder')
        return {'valid': len(missing) == 0, 'missing': missing}
    
    def _validate_researching(self, grant: Grant) -> Dict:
        """Validate researching stage requirements"""
        missing = []
        if not grant.eligibility:
            missing.append('eligibility')
        return {'valid': len(missing) == 0, 'missing': missing}
    
    def _validate_writing(self, grant: Grant) -> Dict:
        """Validate writing stage requirements"""
        # Writing stage has soft requirements
        return {'valid': True, 'missing': []}
    
    def _validate_review(self, grant: Grant) -> Dict:
        """Validate review stage requirements"""
        # Review stage has soft requirements
        return {'valid': True, 'missing': []}
    
    def _validate_submitted(self, grant: Grant) -> Dict:
        """Validate submitted stage requirements"""
        missing = []
        if not grant.deadline:
            missing.append('submission_deadline')
        return {'valid': len(missing) == 0, 'missing': missing}
    
    def _validate_pending(self, grant: Grant) -> Dict:
        """Validate pending stage requirements"""
        return {'valid': True, 'missing': []}
    
    def _validate_awarded(self, grant: Grant) -> Dict:
        """Validate awarded stage requirements"""
        missing = []
        if not grant.amount_max:
            missing.append('award_amount')
        return {'valid': len(missing) == 0, 'missing': missing}
    
    def _validate_reporting(self, grant: Grant) -> Dict:
        """Validate reporting stage requirements"""
        return {'valid': True, 'missing': []}
    
    def _execute_auto_actions(self, grant: Grant, stage: str):
        """Execute automatic actions for stage transition"""
        stage_info = self.STAGES.get(stage, {})
        auto_actions = stage_info.get('auto_actions', [])
        
        for action in auto_actions:
            try:
                if action == 'calculate_match_score':
                    # Trigger AI matching
                    logger.info(f"Would calculate match score for grant {grant.id}")
                elif action == 'generate_narratives':
                    # Trigger narrative generation
                    logger.info(f"Would generate narratives for grant {grant.id}")
                elif action == 'set_reminder':
                    # Set reminder for follow-up
                    logger.info(f"Would set reminder for grant {grant.id}")
                # Add more actions as needed
            except Exception as e:
                logger.error(f"Error executing action {action}: {e}")
    
    def _generate_checklist(self, grant: Grant, stage: str) -> List[Dict]:
        """Generate stage-specific checklist"""
        checklists = {
            'discovery': [
                {'id': 'verify_eligibility', 'task': 'Verify organization eligibility', 'priority': 'high'},
                {'id': 'check_deadline', 'task': 'Confirm application deadline', 'priority': 'high'},
                {'id': 'review_requirements', 'task': 'Review all requirements', 'priority': 'medium'},
                {'id': 'assess_capacity', 'task': 'Assess organizational capacity', 'priority': 'medium'}
            ],
            'researching': [
                {'id': 'funder_research', 'task': 'Research funder priorities', 'priority': 'high'},
                {'id': 'past_awards', 'task': 'Review past award recipients', 'priority': 'medium'},
                {'id': 'contact_funder', 'task': 'Contact program officer', 'priority': 'low'},
                {'id': 'gather_data', 'task': 'Gather supporting data', 'priority': 'high'}
            ],
            'writing': [
                {'id': 'exec_summary', 'task': 'Write executive summary', 'priority': 'high'},
                {'id': 'need_statement', 'task': 'Complete statement of need', 'priority': 'high'},
                {'id': 'project_desc', 'task': 'Write project description', 'priority': 'high'},
                {'id': 'budget', 'task': 'Prepare detailed budget', 'priority': 'high'},
                {'id': 'attachments', 'task': 'Gather required attachments', 'priority': 'medium'}
            ],
            'review': [
                {'id': 'internal_review', 'task': 'Complete internal review', 'priority': 'high'},
                {'id': 'compliance_check', 'task': 'Verify compliance with guidelines', 'priority': 'high'},
                {'id': 'proofread', 'task': 'Proofread all materials', 'priority': 'medium'},
                {'id': 'final_approval', 'task': 'Get executive approval', 'priority': 'high'}
            ],
            'submitted': [
                {'id': 'submission_confirm', 'task': 'Confirm submission receipt', 'priority': 'high'},
                {'id': 'save_copy', 'task': 'Save final application copy', 'priority': 'medium'},
                {'id': 'calendar_reminder', 'task': 'Set follow-up reminder', 'priority': 'low'}
            ],
            'pending': [
                {'id': 'track_status', 'task': 'Check application status', 'priority': 'medium'},
                {'id': 'prepare_questions', 'task': 'Prepare for Q&A if requested', 'priority': 'low'}
            ],
            'awarded': [
                {'id': 'accept_award', 'task': 'Accept award formally', 'priority': 'high'},
                {'id': 'setup_tracking', 'task': 'Set up financial tracking', 'priority': 'high'},
                {'id': 'kickoff_meeting', 'task': 'Schedule kickoff meeting', 'priority': 'medium'},
                {'id': 'reporting_schedule', 'task': 'Note reporting requirements', 'priority': 'high'}
            ],
            'reporting': [
                {'id': 'quarterly_report', 'task': 'Submit quarterly report', 'priority': 'high'},
                {'id': 'financial_report', 'task': 'Prepare financial report', 'priority': 'high'},
                {'id': 'impact_metrics', 'task': 'Collect impact metrics', 'priority': 'medium'},
                {'id': 'site_visit', 'task': 'Prepare for site visit', 'priority': 'low'}
            ]
        }
        
        return checklists.get(stage, [])