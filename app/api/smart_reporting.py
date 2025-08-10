"""
Smart Reporting API - Phase 1 Implementation
Project management and foundation endpoints
"""

from flask import Blueprint, request, jsonify, current_app
from app.services.smart_reporting_service import smart_reporting_service
from app.models_extended import Project, ReportingSchedule, ImpactQuestion
from app.models import Grant, Organization
from app import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('smart_reporting', __name__, url_prefix='/api/smart-reporting')


@bp.route('/projects', methods=['POST'])
def create_project():
    """
    Create new project linked to grant
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'grant_id', 'organization_id', 'start_date', 'end_date']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Missing required fields',
                'required': required_fields
            }), 400
        
        # Create project using service
        result = smart_reporting_service.create_project(
            grant_id=data['grant_id'],
            organization_id=data['organization_id'],
            project_data=data
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Project creation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """
    Get project details with dashboard data
    """
    try:
        result = smart_reporting_service.get_project_dashboard_data(project_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Project retrieval failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """
    Update project details
    """
    try:
        data = request.get_json()
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Update allowed fields
        updateable_fields = ['name', 'description', 'project_owner', 'target_participants', 
                           'target_outcome', 'budget_allocated', 'status']
        
        for field in updateable_fields:
            if field in data:
                setattr(project, field, data[field])
        
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Clear cache
        from app.services.redis_cache_service import cache_service
        cache_service.delete(f'smart_reporting:project:{project_id}')
        cache_service.delete(f'smart_reporting:dashboard:{project_id}')
        
        return jsonify({
            'success': True,
            'project': project.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Project update failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/projects', methods=['GET'])
def list_projects():
    """
    List projects for organization
    """
    try:
        organization_id = request.args.get('organization_id', type=int)
        status = request.args.get('status', 'all')
        
        if not organization_id:
            return jsonify({
                'success': False,
                'error': 'organization_id parameter required'
            }), 400
        
        # Build query
        query = Project.query.filter_by(organization_id=organization_id)
        
        if status != 'all':
            query = query.filter_by(status=status)
        
        projects = query.order_by(Project.created_at.desc()).all()
        
        # Get basic stats for each project
        projects_data = []
        for project in projects:
            project_dict = project.to_dict()
            
            # Add quick stats
            project_dict['stats'] = {
                'total_questions': ImpactQuestion.query.filter_by(project_id=project.id, active=True).count(),
                'approved_questions': ImpactQuestion.query.filter_by(project_id=project.id, active=True, approved=True).count(),
                'upcoming_deadlines': ReportingSchedule.query.filter_by(project_id=project.id, status='pending').count()
            }
            
            projects_data.append(project_dict)
        
        return jsonify({
            'success': True,
            'projects': projects_data,
            'total': len(projects_data)
        })
        
    except Exception as e:
        logger.error(f"Project listing failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/projects/<int:project_id>/questions/generate', methods=['POST'])
def generate_impact_questions(project_id):
    """
    Generate AI-powered impact questions
    """
    try:
        data = request.get_json() or {}
        custom_focus = data.get('custom_focus')
        
        result = smart_reporting_service.generate_impact_questions(project_id, custom_focus)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Question generation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/projects/<int:project_id>/questions', methods=['GET'])
def get_impact_questions(project_id):
    """
    Get impact questions for project
    """
    try:
        include_unapproved = request.args.get('include_unapproved', 'false').lower() == 'true'
        
        query = ImpactQuestion.query.filter_by(project_id=project_id, active=True)
        
        if not include_unapproved:
            query = query.filter_by(approved=True)
        
        questions = query.order_by(ImpactQuestion.display_order).all()
        
        return jsonify({
            'success': True,
            'questions': [q.to_dict() for q in questions],
            'total': len(questions)
        })
        
    except Exception as e:
        logger.error(f"Questions retrieval failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/projects/<int:project_id>/questions/approve', methods=['POST'])
def approve_impact_questions(project_id):
    """
    Approve and customize impact questions
    """
    try:
        data = request.get_json()
        
        if 'question_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'question_ids required'
            }), 400
        
        result = smart_reporting_service.approve_impact_questions(
            project_id=project_id,
            question_ids=data['question_ids'],
            customizations=data.get('customizations', {})
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Question approval failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/projects/<int:project_id>/schedule', methods=['GET'])
def get_reporting_schedule(project_id):
    """
    Get reporting schedule for project
    """
    try:
        schedules = ReportingSchedule.query.filter_by(project_id=project_id)\
            .order_by(ReportingSchedule.due_date).all()
        
        return jsonify({
            'success': True,
            'schedules': [s.to_dict() for s in schedules],
            'total': len(schedules)
        })
        
    except Exception as e:
        logger.error(f"Schedule retrieval failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/projects/<int:project_id>/schedule', methods=['POST'])
def create_reporting_schedule(project_id):
    """
    Create custom reporting schedule entry
    """
    try:
        data = request.get_json()
        
        required_fields = ['report_type', 'due_date']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Missing required fields',
                'required': required_fields
            }), 400
        
        schedule = ReportingSchedule(
            project_id=project_id,
            report_type=data['report_type'],
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
            deliverable_type=data.get('deliverable_type', 'impact_metrics'),
            funder_requirements=data.get('funder_requirements', '')
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'schedule': schedule.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Schedule creation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/organizations/<int:organization_id>/stats', methods=['GET'])
def get_organization_stats(organization_id):
    """
    Get Smart Reporting statistics for organization
    """
    try:
        result = smart_reporting_service.get_smart_reporting_stats(organization_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/dashboard/overview', methods=['GET'])
def get_dashboard_overview():
    """
    Get overview dashboard data across all projects
    """
    try:
        organization_id = request.args.get('organization_id', type=int)
        
        if not organization_id:
            return jsonify({
                'success': False,
                'error': 'organization_id parameter required'
            }), 400
        
        # Get projects summary
        projects = Project.query.filter_by(organization_id=organization_id).all()
        active_projects = [p for p in projects if p.status == 'active']
        
        # Get upcoming deadlines across all projects
        upcoming_deadlines = ReportingSchedule.query.join(Project)\
            .filter(Project.organization_id == organization_id,
                   ReportingSchedule.status == 'pending')\
            .order_by(ReportingSchedule.due_date)\
            .limit(5).all()
        
        # Get recent activity
        from app.models.smart_reporting import SurveyResponse
        recent_responses = SurveyResponse.query.join(Project)\
            .filter(Project.organization_id == organization_id)\
            .order_by(SurveyResponse.submitted_at.desc())\
            .limit(10).all()
        
        overview = {
            'success': True,
            'summary': {
                'total_projects': len(projects),
                'active_projects': len(active_projects),
                'completed_projects': len([p for p in projects if p.status == 'completed']),
                'upcoming_deadlines': len(upcoming_deadlines)
            },
            'recent_activity': [r.to_dict() for r in recent_responses],
            'upcoming_deadlines': [d.to_dict() for d in upcoming_deadlines],
            'quick_actions': [
                {'action': 'create_project', 'label': 'Create New Project', 'count': len([g for g in Grant.query.filter_by(organization_id=organization_id).all() if not g.projects])},
                {'action': 'review_questions', 'label': 'Review AI Questions', 'count': ImpactQuestion.query.join(Project).filter(Project.organization_id == organization_id, ImpactQuestion.approved == False).count()},
                {'action': 'submit_reports', 'label': 'Submit Reports', 'count': len([d for d in upcoming_deadlines if d.status == 'pending'])}
            ]
        }
        
        return jsonify(overview)
        
    except Exception as e:
        logger.error(f"Dashboard overview failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """
    Smart Reporting system health check
    """
    try:
        # Test database connectivity
        db.session.execute('SELECT 1')
        
        # Test AI service connectivity
        ai_status = smart_reporting_service.ai_engine.health_check()
        
        # Get system stats
        total_projects = Project.query.count()
        total_questions = ImpactQuestion.query.count()
        total_responses = db.session.execute('SELECT COUNT(*) FROM survey_responses').scalar()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'components': {
                'database': 'operational',
                'ai_service': 'operational' if ai_status.get('success') else 'degraded',
                'cache': 'operational'
            },
            'stats': {
                'total_projects': total_projects,
                'total_questions': total_questions,
                'total_responses': total_responses
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500