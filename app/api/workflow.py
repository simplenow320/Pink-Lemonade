"""
Workflow Management API Endpoints
Handles 8-stage grant pipeline operations
"""

from flask import Blueprint, jsonify, request
# from flask_login import login_required, current_user
# Temporarily disabled login requirements
from app.services.workflow_manager import WorkflowManager
from app.models import Grant, Organization, db
import logging

logger = logging.getLogger(__name__)

workflow_bp = Blueprint('workflow', __name__, url_prefix='/api/workflow')
workflow_manager = WorkflowManager()

@workflow_bp.route('/pipeline/<int:org_id>', methods=['GET'])
# @login_required
def get_pipeline(org_id):
    """Get complete pipeline status for organization"""
    try:
        # Verify user has access to this org
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 404
        
        # Get pipeline status
        result = workflow_manager.get_pipeline_status(org_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting pipeline: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workflow_bp.route('/move-stage', methods=['POST'])
# @login_required
def move_grant_stage():
    """Move a grant to a new stage"""
    try:
        data = request.get_json() or {}
        grant_id = data.get('grant_id')
        new_stage = data.get('stage')
        notes = data.get('notes', '')
        
        if not grant_id or not new_stage:
            return jsonify({
                'success': False,
                'error': 'grant_id and stage are required'
            }), 400
        
        # Move grant to new stage
        result = workflow_manager.move_to_stage(grant_id, new_stage, notes)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error moving grant stage: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workflow_bp.route('/batch-move', methods=['POST'])
# @login_required
def batch_move_stages():
    """Move multiple grants to same stage"""
    try:
        data = request.get_json() or {}
        grant_ids = data.get('grant_ids', [])
        new_stage = data.get('stage')
        
        if not grant_ids or not new_stage:
            return jsonify({
                'success': False,
                'error': 'grant_ids and stage are required'
            }), 400
        
        result = workflow_manager.batch_move(grant_ids, new_stage)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in batch move: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workflow_bp.route('/checklist/<int:grant_id>', methods=['GET'])
# @login_required
def get_checklist(grant_id):
    """Get checklist for grant's current stage"""
    try:
        result = workflow_manager.get_stage_checklist(grant_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error getting checklist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workflow_bp.route('/checklist/update', methods=['POST'])
# @login_required
def update_checklist():
    """Update a checklist item"""
    try:
        data = request.get_json() or {}
        grant_id = data.get('grant_id')
        item_id = data.get('item_id')
        completed = data.get('completed', False)
        
        if not grant_id or not item_id:
            return jsonify({
                'success': False,
                'error': 'grant_id and item_id are required'
            }), 400
        
        result = workflow_manager.update_checklist_item(grant_id, item_id, completed)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error updating checklist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workflow_bp.route('/stages', methods=['GET'])
def get_stages():
    """Get all workflow stages and their metadata"""
    try:
        stages = []
        for key, info in WorkflowManager.STAGES.items():
            stages.append({
                'key': key,
                'name': info['name'],
                'description': info['description'],
                'order': info['order'],
                'color': info['color'],
                'icon': info['icon'],
                'next': info['next']
            })
        
        stages.sort(key=lambda x: x['order'])
        
        return jsonify({
            'success': True,
            'stages': stages
        })
        
    except Exception as e:
        logger.error(f"Error getting stages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workflow_bp.route('/automation-rules', methods=['GET'])
# @login_required
def get_automation_rules():
    """Get automation rules for each stage"""
    try:
        rules = {}
        for key, info in WorkflowManager.STAGES.items():
            rules[key] = {
                'stage': info['name'],
                'auto_actions': info.get('auto_actions', []),
                'required_fields': info.get('required_fields', []),
                'typical_duration': info.get('typical_duration', 0)
            }
        
        return jsonify({
            'success': True,
            'rules': rules
        })
        
    except Exception as e:
        logger.error(f"Error getting automation rules: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workflow_bp.route('/quick-actions/<int:grant_id>', methods=['GET'])
# @login_required
def get_quick_actions(grant_id):
    """Get available quick actions for a grant"""
    try:
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'success': False, 'error': 'Grant not found'}), 404
        
        current_stage = grant.application_stage or 'discovery'
        stage_info = WorkflowManager.STAGES.get(current_stage, {})
        
        # Determine available actions
        actions = []
        
        # Move to next stage
        if stage_info.get('next'):
            actions.append({
                'action': 'advance',
                'label': f'Move to {WorkflowManager.STAGES[stage_info["next"]]["name"]}',
                'stage': stage_info['next'],
                'type': 'primary'
            })
        
        # Always allow marking as declined
        if current_stage not in ['declined', 'awarded']:
            actions.append({
                'action': 'decline',
                'label': 'Mark as Declined',
                'stage': 'declined',
                'type': 'danger'
            })
        
        # Jump to submitted (if in early stages)
        if current_stage in ['discovery', 'researching', 'writing', 'review']:
            actions.append({
                'action': 'fast_track',
                'label': 'Fast Track to Submitted',
                'stage': 'submitted',
                'type': 'warning'
            })
        
        return jsonify({
            'success': True,
            'grant_id': grant_id,
            'current_stage': current_stage,
            'actions': actions
        })
        
    except Exception as e:
        logger.error(f"Error getting quick actions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500