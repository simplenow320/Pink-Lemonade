"""
Smart Reporting Service - Enterprise AI Integration
Cross-tool learning and data sharing for impact measurement
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from app import db
from app.models_extended import Project, ReportingSchedule, ImpactQuestion, SurveyResponse, ImpactReport
from app.models import Grant, Organization
from app.services.ai_reasoning_engine import AIReasoningEngine
from app.services.redis_cache_service import cache_service
import json

logger = logging.getLogger(__name__)


class SmartReportingService:
    """Enterprise-level Smart Reporting service with AI integration"""
    
    def __init__(self):
        self.ai_engine = AIReasoningEngine()
        self.cache_prefix = 'smart_reporting:'
        
    def create_project(self, grant_id: int, organization_id: int, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new project with AI-enhanced setup
        """
        try:
            # Validate grant and organization
            grant = Grant.query.get(grant_id)
            organization = Organization.query.get(organization_id)
            
            if not grant or not organization:
                return {'success': False, 'error': 'Grant or organization not found'}
            
            # Create project
            project = Project(
                name=project_data['name'],
                description=project_data.get('description', ''),
                grant_id=grant_id,
                organization_id=organization_id,
                start_date=datetime.strptime(project_data['start_date'], '%Y-%m-%d').date(),
                end_date=datetime.strptime(project_data['end_date'], '%Y-%m-%d').date(),
                project_owner=project_data.get('project_owner'),
                target_participants=project_data.get('target_participants'),
                target_outcome=project_data.get('target_outcome'),
                budget_allocated=project_data.get('budget_allocated')
            )
            
            db.session.add(project)
            db.session.flush()  # Get project.id
            
            # Auto-generate reporting schedule based on grant requirements
            self._create_reporting_schedule(project, grant)
            
            # Trigger AI impact question generation
            self._initialize_impact_framework(project, grant, organization)
            
            db.session.commit()
            
            # Cache project data
            cache_service.set(f'{self.cache_prefix}project:{project.id}', project.to_dict(), 3600)
            
            logger.info(f"Created project {project.id} for grant {grant_id}")
            
            return {
                'success': True,
                'project': project.to_dict(),
                'ai_framework_initialized': True,
                'reporting_schedule_created': True
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Project creation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_impact_questions(self, project_id: int, custom_focus: Optional[str] = None) -> Dict[str, Any]:
        """
        AI-powered impact question generation with cross-tool learning
        """
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'success': False, 'error': 'Project not found'}
            
            # Get context from existing tools
            grant_context = self._get_grant_context(project.grant)
            org_context = self._get_organization_context(project.organization)
            historical_context = self._get_historical_question_context(project.organization_id)
            
            # Prepare AI prompt with enterprise context
            prompt_context = {
                'grant_title': project.grant.title,
                'grant_description': project.grant.description,
                'grant_focus_areas': project.grant.focus_areas,
                'grant_amount': f"${project.grant.amount_min:,.0f} - ${project.grant.amount_max:,.0f}",
                'project_name': project.name,
                'project_description': project.description,
                'target_participants': project.target_participants,
                'target_outcome': project.target_outcome,
                'organization_mission': org_context.get('mission', ''),
                'organization_focus_areas': org_context.get('focus_areas', []),
                'custom_focus': custom_focus,
                'historical_questions': historical_context.get('successful_questions', []),
                'industry_best_practices': historical_context.get('best_practices', [])
            }
            
            # Generate questions using AI reasoning engine
            questions_result = self.ai_engine.generate_impact_questions(prompt_context)
            
            if not questions_result.get('success'):
                return questions_result
            
            # Save generated questions to database
            questions_saved = []
            for i, question_data in enumerate(questions_result['questions']):
                impact_question = ImpactQuestion(
                    project_id=project_id,
                    question_text=question_data['question'],
                    question_type=question_data['type'],
                    category=question_data.get('category', 'general'),
                    ai_generated=True,
                    ai_confidence_score=question_data.get('confidence', 0.8),
                    ai_reasoning=question_data.get('reasoning', ''),
                    display_order=i + 1,
                    response_format=question_data.get('format', 'text'),
                    options=question_data.get('options'),
                    learning_tags=question_data.get('tags', []),
                    approved=False  # Requires manual approval
                )
                
                db.session.add(impact_question)
                questions_saved.append(impact_question)
            
            # Update project AI status
            project.impact_framework_generated = True
            project.ai_analysis_version = '2.0'
            
            db.session.commit()
            
            # Cache generated questions
            cache_key = f'{self.cache_prefix}questions:{project_id}'
            cache_service.set(cache_key, [q.to_dict() for q in questions_saved], 1800)
            
            # Update cross-tool learning data
            self._update_question_learning_data(project.organization_id, questions_saved)
            
            logger.info(f"Generated {len(questions_saved)} impact questions for project {project_id}")
            
            return {
                'success': True,
                'questions': [q.to_dict() for q in questions_saved],
                'ai_confidence': questions_result.get('overall_confidence', 0.8),
                'customization_suggestions': questions_result.get('suggestions', [])
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Impact question generation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_project_dashboard_data(self, project_id: int) -> Dict[str, Any]:
        """
        Get comprehensive project dashboard data
        """
        try:
            # Check cache first
            cache_key = f'{self.cache_prefix}dashboard:{project_id}'
            cached_data = cache_service.get(cache_key)
            if cached_data:
                return cached_data
            
            project = Project.query.get(project_id)
            if not project:
                return {'success': False, 'error': 'Project not found'}
            
            # Get project progress metrics
            total_questions = ImpactQuestion.query.filter_by(project_id=project_id, active=True).count()
            approved_questions = ImpactQuestion.query.filter_by(project_id=project_id, active=True, approved=True).count()
            total_responses = SurveyResponse.query.filter_by(project_id=project_id).count()
            
            # Get reporting schedule status
            schedules = ReportingSchedule.query.filter_by(project_id=project_id).all()
            upcoming_deadlines = [s for s in schedules if s.due_date > date.today() and s.status != 'submitted']
            overdue_reports = [s for s in schedules if s.due_date <= date.today() and s.status != 'submitted']
            
            # Calculate project health score
            health_score = self._calculate_project_health_score(project, total_questions, approved_questions, total_responses, schedules)
            
            # Get recent activity
            recent_responses = SurveyResponse.query.filter_by(project_id=project_id)\
                .order_by(SurveyResponse.submitted_at.desc()).limit(5).all()
            
            dashboard_data = {
                'success': True,
                'project': project.to_dict(),
                'metrics': {
                    'total_questions': total_questions,
                    'approved_questions': approved_questions,
                    'total_responses': total_responses,
                    'response_rate': self._calculate_response_rate(project_id),
                    'health_score': health_score
                },
                'schedule': {
                    'upcoming_deadlines': [s.to_dict() for s in upcoming_deadlines[:3]],
                    'overdue_reports': [s.to_dict() for s in overdue_reports],
                    'next_deadline': upcoming_deadlines[0].to_dict() if upcoming_deadlines else None
                },
                'recent_activity': [r.to_dict() for r in recent_responses],
                'ai_insights': self._get_project_ai_insights(project_id)
            }
            
            # Cache dashboard data
            cache_service.set(cache_key, dashboard_data, 300)  # 5 minutes
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Dashboard data retrieval failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def approve_impact_questions(self, project_id: int, question_ids: List[int], customizations: Dict = None) -> Dict[str, Any]:
        """
        Approve and customize AI-generated impact questions
        """
        try:
            questions = ImpactQuestion.query.filter(
                ImpactQuestion.project_id == project_id,
                ImpactQuestion.id.in_(question_ids)
            ).all()
            
            if not questions:
                return {'success': False, 'error': 'No questions found'}
            
            approved_count = 0
            for question in questions:
                question.approved = True
                question.updated_at = datetime.utcnow()
                
                # Apply customizations if provided
                if customizations and str(question.id) in customizations:
                    custom_data = customizations[str(question.id)]
                    if 'question_text' in custom_data:
                        question.question_text = custom_data['question_text']
                    if 'required' in custom_data:
                        question.required = custom_data['required']
                    if 'display_order' in custom_data:
                        question.display_order = custom_data['display_order']
                
                approved_count += 1
            
            db.session.commit()
            
            # Clear cache
            cache_service.delete(f'{self.cache_prefix}questions:{project_id}')
            cache_service.delete(f'{self.cache_prefix}dashboard:{project_id}')
            
            # Update learning system
            self._update_approval_learning_data(questions)
            
            logger.info(f"Approved {approved_count} impact questions for project {project_id}")
            
            return {
                'success': True,
                'approved_count': approved_count,
                'questions': [q.to_dict() for q in questions]
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Question approval failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_smart_reporting_stats(self, organization_id: int) -> Dict[str, Any]:
        """
        Get organization-wide Smart Reporting statistics
        """
        try:
            cache_key = f'{self.cache_prefix}stats:{organization_id}'
            cached_stats = cache_service.get(cache_key)
            if cached_stats:
                return cached_stats
            
            # Get project statistics
            projects = Project.query.filter_by(organization_id=organization_id).all()
            active_projects = [p for p in projects if p.status == 'active']
            
            # Get reporting statistics
            total_schedules = ReportingSchedule.query.join(Project)\
                .filter(Project.organization_id == organization_id).count()
            
            submitted_reports = ReportingSchedule.query.join(Project)\
                .filter(Project.organization_id == organization_id, ReportingSchedule.status == 'submitted').count()
            
            # Get AI usage statistics
            ai_questions = ImpactQuestion.query.join(Project)\
                .filter(Project.organization_id == organization_id, ImpactQuestion.ai_generated == True).count()
            
            approved_ai_questions = ImpactQuestion.query.join(Project)\
                .filter(Project.organization_id == organization_id, 
                       ImpactQuestion.ai_generated == True, 
                       ImpactQuestion.approved == True).count()
            
            # Calculate effectiveness metrics
            ai_approval_rate = (approved_ai_questions / max(ai_questions, 1)) * 100
            reporting_completion_rate = (submitted_reports / max(total_schedules, 1)) * 100
            
            stats = {
                'success': True,
                'projects': {
                    'total': len(projects),
                    'active': len(active_projects),
                    'completed': len([p for p in projects if p.status == 'completed'])
                },
                'reporting': {
                    'total_schedules': total_schedules,
                    'submitted_reports': submitted_reports,
                    'completion_rate': round(reporting_completion_rate, 1)
                },
                'ai_assistance': {
                    'questions_generated': ai_questions,
                    'questions_approved': approved_ai_questions,
                    'approval_rate': round(ai_approval_rate, 1)
                },
                'efficiency_gains': {
                    'estimated_time_saved_hours': len(active_projects) * 8,  # Estimated 8 hours saved per project
                    'reports_automated': submitted_reports,
                    'data_points_collected': SurveyResponse.query.join(Project)\
                        .filter(Project.organization_id == organization_id).count()
                }
            }
            
            # Cache stats
            cache_service.set(cache_key, stats, 1800)  # 30 minutes
            
            return stats
            
        except Exception as e:
            logger.error(f"Stats retrieval failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_reporting_schedule(self, project: Project, grant: Grant):
        """Create reporting schedule based on grant requirements"""
        try:
            # Default schedule based on project duration
            project_duration = (project.end_date - project.start_date).days
            
            schedules = []
            
            if project_duration > 365:  # Multi-year project
                # Annual reports
                current_date = project.start_date
                year_count = 1
                while current_date < project.end_date:
                    annual_due = current_date.replace(year=current_date.year + 1)
                    if annual_due > project.end_date:
                        annual_due = project.end_date + timedelta(days=30)
                    
                    schedule = ReportingSchedule(
                        project_id=project.id,
                        report_type=f'annual_year_{year_count}',
                        due_date=annual_due,
                        deliverable_type='impact_metrics',
                        funder_requirements=f'Annual impact report for year {year_count}'
                    )
                    schedules.append(schedule)
                    
                    current_date = annual_due
                    year_count += 1
            
            elif project_duration > 180:  # 6+ month project
                # Quarterly reports
                quarter_dates = []
                current = project.start_date
                while current < project.end_date:
                    current += timedelta(days=90)
                    if current < project.end_date:
                        quarter_dates.append(current)
                
                for i, quarter_date in enumerate(quarter_dates):
                    schedule = ReportingSchedule(
                        project_id=project.id,
                        report_type=f'quarterly_q{i+1}',
                        due_date=quarter_date,
                        deliverable_type='impact_metrics',
                        funder_requirements=f'Quarterly progress report Q{i+1}'
                    )
                    schedules.append(schedule)
            
            # Final report
            final_schedule = ReportingSchedule(
                project_id=project.id,
                report_type='final',
                due_date=project.end_date + timedelta(days=30),
                deliverable_type='impact_metrics',
                funder_requirements='Final project impact report'
            )
            schedules.append(final_schedule)
            
            # Add all schedules to session
            for schedule in schedules:
                db.session.add(schedule)
            
            logger.info(f"Created {len(schedules)} reporting schedules for project {project.id}")
            
        except Exception as e:
            logger.error(f"Reporting schedule creation failed: {e}")
            raise
    
    def _initialize_impact_framework(self, project: Project, grant: Grant, organization: Organization):
        """Initialize AI impact framework for project"""
        try:
            # This will be expanded in Phase 2 with full AI integration
            project.impact_framework_generated = False  # Will be generated when requested
            
        except Exception as e:
            logger.error(f"Impact framework initialization failed: {e}")
            raise
    
    def _get_grant_context(self, grant: Grant) -> Dict[str, Any]:
        """Extract context from grant for AI analysis"""
        return {
            'title': grant.title,
            'description': grant.description,
            'focus_areas': grant.focus_areas,
            'amount_range': f"${grant.amount_min:,.0f} - ${grant.amount_max:,.0f}",
            'deadline': grant.deadline.isoformat() if grant.deadline else None,
            'funder': grant.funder
        }
    
    def _get_organization_context(self, organization: Organization) -> Dict[str, Any]:
        """Extract context from organization for AI analysis"""
        return {
            'mission': organization.mission,
            'focus_areas': organization.focus_areas,
            'target_population': organization.target_population,
            'geographic_focus': organization.geographic_focus
        }
    
    def _get_historical_question_context(self, organization_id: int) -> Dict[str, Any]:
        """Get historical question patterns for learning"""
        try:
            # Get successful questions from previous projects
            successful_questions = ImpactQuestion.query.join(Project)\
                .filter(Project.organization_id == organization_id,
                       ImpactQuestion.approved == True)\
                .order_by(ImpactQuestion.created_at.desc())\
                .limit(20).all()
            
            return {
                'successful_questions': [q.question_text for q in successful_questions],
                'best_practices': [q.learning_tags for q in successful_questions if q.learning_tags]
            }
        except Exception as e:
            logger.error(f"Historical context retrieval failed: {e}")
            return {}
    
    def _calculate_project_health_score(self, project: Project, total_questions: int, 
                                      approved_questions: int, total_responses: int, 
                                      schedules: List[ReportingSchedule]) -> float:
        """Calculate project health score"""
        try:
            score = 0.0
            
            # Question readiness (30%)
            if total_questions > 0:
                question_score = (approved_questions / total_questions) * 30
                score += question_score
            
            # Data collection progress (25%)
            if approved_questions > 0:
                response_rate = min(total_responses / (approved_questions * 10), 1.0)  # Target 10 responses per question
                score += response_rate * 25
            
            # Schedule compliance (25%)
            if schedules:
                on_time_schedules = len([s for s in schedules if s.status == 'submitted' or s.due_date > date.today()])
                schedule_score = (on_time_schedules / len(schedules)) * 25
                score += schedule_score
            
            # Project timeline (20%)
            project_duration = (project.end_date - project.start_date).days
            days_elapsed = (date.today() - project.start_date).days
            if project_duration > 0:
                timeline_progress = min(days_elapsed / project_duration, 1.0)
                score += timeline_progress * 20
            
            return round(score, 1)
            
        except Exception as e:
            logger.error(f"Health score calculation failed: {e}")
            return 0.0
    
    def _calculate_response_rate(self, project_id: int) -> float:
        """Calculate survey response rate"""
        try:
            approved_questions = ImpactQuestion.query.filter_by(
                project_id=project_id, approved=True, active=True
            ).count()
            
            if approved_questions == 0:
                return 0.0
            
            total_responses = SurveyResponse.query.filter_by(project_id=project_id).count()
            target_responses = approved_questions * 10  # Target 10 responses per question
            
            return round(min((total_responses / target_responses) * 100, 100), 1)
            
        except Exception as e:
            logger.error(f"Response rate calculation failed: {e}")
            return 0.0
    
    def _get_project_ai_insights(self, project_id: int) -> Dict[str, Any]:
        """Get AI-powered insights for project"""
        try:
            # This will be expanded with more sophisticated AI analysis
            return {
                'data_quality': 'good',
                'response_trends': 'increasing',
                'recommendations': ['Consider additional qualitative questions', 'Target more beneficiary responses'],
                'confidence': 0.8
            }
        except Exception as e:
            logger.error(f"AI insights generation failed: {e}")
            return {}
    
    def _update_question_learning_data(self, organization_id: int, questions: List[ImpactQuestion]):
        """Update cross-tool learning data for question generation"""
        try:
            # This will be expanded with machine learning integration
            learning_data = {
                'organization_id': organization_id,
                'question_patterns': [q.question_text for q in questions],
                'question_types': [q.question_type for q in questions],
                'generation_timestamp': datetime.utcnow().isoformat()
            }
            
            cache_key = f'{self.cache_prefix}learning:questions:{organization_id}'
            cache_service.set(cache_key, learning_data, 86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Learning data update failed: {e}")
    
    def _update_approval_learning_data(self, questions: List[ImpactQuestion]):
        """Update learning data based on question approvals"""
        try:
            # Track approval patterns for AI improvement
            approval_patterns = {
                'approved_questions': [q.question_text for q in questions],
                'approval_timestamp': datetime.utcnow().isoformat(),
                'ai_confidence_scores': [q.ai_confidence_score for q in questions if q.ai_confidence_score]
            }
            
            cache_key = f'{self.cache_prefix}learning:approvals'
            cache_service.set(cache_key, approval_patterns, 86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Approval learning update failed: {e}")


# Global service instance
smart_reporting_service = SmartReportingService()