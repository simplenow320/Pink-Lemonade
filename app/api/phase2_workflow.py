"""
PHASE 2: Application Workflow API Endpoints
"""
from flask import Blueprint, request, jsonify, session
from app.services.phase2_application_workflow import phase2_workflow
from app.models import db, Grant, Organization
import logging

logger = logging.getLogger(__name__)

phase2_bp = Blueprint('phase2_workflow', __name__)

@phase2_bp.route('/api/phase2/application/create', methods=['POST'])
def create_application():
    """Create a new grant application from opportunity"""
    try:
        user_id = session.get('user_id', 1)
        grant_data = request.json
        
        result = phase2_workflow.create_application(grant_data, user_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase2_bp.route('/api/phase2/application/<int:app_id>/stage', methods=['PUT'])
def update_stage(app_id):
    """Update application workflow stage"""
    try:
        data = request.json
        new_stage = data.get('stage')
        notes = data.get('notes', '')
        
        result = phase2_workflow.update_stage(app_id, new_stage, notes)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error updating stage: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase2_bp.route('/api/phase2/applications/staged', methods=['GET'])
def get_staged_applications():
    """Get all applications organized by stage"""
    try:
        user_id = session.get('user_id', 1)
        result = phase2_workflow.get_applications_by_stage(user_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting staged applications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase2_bp.route('/api/phase2/deadlines', methods=['GET'])
def get_deadlines():
    """Get upcoming application deadlines"""
    try:
        user_id = session.get('user_id', 1)
        days_ahead = request.args.get('days', 30, type=int)
        
        deadlines = phase2_workflow.get_upcoming_deadlines(user_id, days_ahead)
        
        return jsonify({
            'success': True,
            'deadlines': deadlines,
            'count': len(deadlines)
        })
        
    except Exception as e:
        logger.error(f"Error getting deadlines: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase2_bp.route('/api/phase2/reminders', methods=['GET'])
def get_reminders():
    """Get smart reminders for applications"""
    try:
        user_id = session.get('user_id', 1)
        reminders = phase2_workflow.generate_reminders(user_id)
        
        return jsonify({
            'success': True,
            'reminders': reminders,
            'count': len(reminders)
        })
        
    except Exception as e:
        logger.error(f"Error getting reminders: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase2_bp.route('/api/phase2/application/<int:app_id>/team', methods=['POST'])
def add_team_member(app_id):
    """Add team member to application"""
    try:
        data = request.json
        email = data.get('email')
        role = data.get('role', 'collaborator')
        
        result = phase2_workflow.add_team_member(app_id, email, role)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error adding team member: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase2_bp.route('/api/phase2/application/<int:app_id>/checklist', methods=['GET'])
def get_checklist(app_id):
    """Get application checklist"""
    try:
        grant = Grant.query.get(app_id)
        if not grant:
            return jsonify({'success': False, 'error': 'Application not found'}), 404
        
        checklist = grant.checklist if hasattr(grant, 'checklist') else []
        completion = phase2_workflow._calculate_completion(grant)
        
        return jsonify({
            'success': True,
            'checklist': checklist,
            'completion_percentage': completion
        })
        
    except Exception as e:
        logger.error(f"Error getting checklist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase2_bp.route('/api/phase2/application/<int:app_id>/checklist/<int:task_index>', methods=['PUT'])
def update_checklist_task(app_id, task_index):
    """Update checklist task status"""
    try:
        grant = Grant.query.get(app_id)
        if not grant:
            return jsonify({'success': False, 'error': 'Application not found'}), 404
        
        data = request.json
        completed = data.get('completed', False)
        
        if hasattr(grant, 'checklist') and task_index < len(grant.checklist):
            grant.checklist[task_index]['completed'] = completed
            db.session.commit()
            
            completion = phase2_workflow._calculate_completion(grant)
            
            return jsonify({
                'success': True,
                'task_index': task_index,
                'completed': completed,
                'completion_percentage': completion
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid task index'}), 400
            
    except Exception as e:
        logger.error(f"Error updating checklist: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@phase2_bp.route('/api/phase2/workflow/stats', methods=['GET'])
def get_workflow_stats():
    """Get workflow statistics"""
    try:
        user_id = session.get('user_id', 1)
        grants = Grant.query.filter_by(user_id=user_id).all()
        
        stats = {
            'total_applications': len(grants),
            'by_stage': {},
            'by_priority': {},
            'success_rate': 0
        }
        
        # Count by stage
        for stage in phase2_workflow.STAGES.keys():
            count = sum(1 for g in grants if g.application_stage == stage)
            stats['by_stage'][stage] = count
        
        # Count by priority
        for priority in ['urgent', 'high', 'medium', 'low']:
            count = sum(1 for g in grants if g.priority_level == priority)
            stats['by_priority'][priority] = count
        
        # Calculate success rate
        completed = sum(1 for g in grants if g.status in ['awarded', 'rejected'])
        if completed > 0:
            awarded = sum(1 for g in grants if g.status == 'awarded')
            stats['success_rate'] = round((awarded / completed) * 100, 1)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting workflow stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500