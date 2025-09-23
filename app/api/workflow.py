"""
Workflow Management API Endpoints
Handles 8-stage grant pipeline operations
"""

from flask import Blueprint, jsonify, request
from app.services.workflow_manager import WorkflowManager
from app.api.auth import login_required, get_current_user
from app.models import Grant, Organization, Application, ApplicationContent, ToolUsage, db
import logging

logger = logging.getLogger(__name__)

workflow_bp = Blueprint('workflow', __name__, url_prefix='/api/workflow')
workflow_manager = WorkflowManager()

@workflow_bp.route('/pipeline/<int:org_id>', methods=['GET'])
@login_required
def get_pipeline(org_id):
    """Get complete pipeline status for organization"""
    try:
        # Get current authenticated user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get user's organization
        user_org = Organization.query.filter(
            (Organization.user_id == current_user.id) | 
            (Organization.created_by_user_id == current_user.id)
        ).first()
        
        if not user_org:
            return jsonify({
                'success': False,
                'error': 'Access denied: No organization associated with user'
            }), 403
        
        # Verify user has access to this org
        if org_id != user_org.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
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
@login_required
def move_grant_stage():
    """Move a grant to a new stage"""
    try:
        # Get current authenticated user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        grant_id = data.get('grant_id')
        new_stage = data.get('stage')
        notes = data.get('notes', '')
        
        if not grant_id or not new_stage:
            return jsonify({
                'success': False,
                'error': 'grant_id and stage are required'
            }), 400
        
        # Get user's organization
        user_org = Organization.query.filter(
            (Organization.user_id == current_user.id) | 
            (Organization.created_by_user_id == current_user.id)
        ).first()
        
        if not user_org:
            return jsonify({
                'success': False,
                'error': 'Access denied: No organization associated with user'
            }), 403
        
        # Verify grant exists and belongs to user's organization
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'success': False, 'error': 'Grant not found'}), 404
        
        if not grant.org_id or grant.org_id != user_org.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
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
@login_required
def batch_move_stages():
    """Move multiple grants to same stage"""
    try:
        # Get current authenticated user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        grant_ids = data.get('grant_ids', [])
        new_stage = data.get('stage')
        
        if not grant_ids or not new_stage:
            return jsonify({
                'success': False,
                'error': 'grant_ids and stage are required'
            }), 400
        
        # Get user's organization
        user_org = Organization.query.filter(
            (Organization.user_id == current_user.id) | 
            (Organization.created_by_user_id == current_user.id)
        ).first()
        
        if not user_org:
            return jsonify({
                'success': False,
                'error': 'Access denied: No organization associated with user'
            }), 403
        
        # Verify all grants exist and belong to user's organization
        for grant_id in grant_ids:
            grant = Grant.query.get(grant_id)
            if not grant:
                return jsonify({'success': False, 'error': f'Grant {grant_id} not found'}), 404
            
            if not grant.org_id or grant.org_id != user_org.id:
                return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        result = workflow_manager.batch_move(grant_ids, new_stage)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in batch move: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workflow_bp.route('/checklist/<int:grant_id>', methods=['GET'])
@login_required
def get_checklist(grant_id):
    """Get checklist for grant's current stage"""
    try:
        # Get current authenticated user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get user's organization
        user_org = Organization.query.filter(
            (Organization.user_id == current_user.id) | 
            (Organization.created_by_user_id == current_user.id)
        ).first()
        
        if not user_org:
            return jsonify({
                'success': False,
                'error': 'Access denied: No organization associated with user'
            }), 403
        
        # Verify grant exists and belongs to user's organization
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'success': False, 'error': 'Grant not found'}), 404
        
        if not grant.org_id or grant.org_id != user_org.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        result = workflow_manager.get_stage_checklist(grant_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error getting checklist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@workflow_bp.route('/checklist/update', methods=['POST'])
@login_required
def update_checklist():
    """Update a checklist item"""
    try:
        # Get current authenticated user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        grant_id = data.get('grant_id')
        item_id = data.get('item_id')
        completed = data.get('completed', False)
        
        if not grant_id or not item_id:
            return jsonify({
                'success': False,
                'error': 'grant_id and item_id are required'
            }), 400
        
        # Get user's organization
        user_org = Organization.query.filter(
            (Organization.user_id == current_user.id) | 
            (Organization.created_by_user_id == current_user.id)
        ).first()
        
        if not user_org:
            return jsonify({
                'success': False,
                'error': 'Access denied: No organization associated with user'
            }), 403
        
        # Verify grant exists and belongs to user's organization
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'success': False, 'error': 'Grant not found'}), 404
        
        if not grant.org_id or grant.org_id != user_org.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
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
@login_required
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
@login_required
def get_quick_actions(grant_id):
    """Get available quick actions for a grant"""
    try:
        # Get current authenticated user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get user's organization
        user_org = Organization.query.filter(
            (Organization.user_id == current_user.id) | 
            (Organization.created_by_user_id == current_user.id)
        ).first()
        
        if not user_org:
            return jsonify({
                'success': False,
                'error': 'Access denied: No organization associated with user'
            }), 403
        
        # Verify grant exists and belongs to user's organization
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'success': False, 'error': 'Grant not found'}), 404
        
        if not grant.org_id or grant.org_id != user_org.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
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

@workflow_bp.route('/applications/<int:grant_id>/content', methods=['POST'])
@login_required
def save_application_content(grant_id):
    """Save Smart Tools content to grant application"""
    try:
        # Get current authenticated user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        data = request.get_json() or {}
        section = data.get('section')
        content = data.get('content')
        source_tool = data.get('source_tool')
        tool_usage_id = data.get('tool_usage_id')
        
        # Validate required fields
        if not section or not content:
            return jsonify({
                'success': False,
                'error': 'Section and content are required'
            }), 400
        
        # Validate section name against allowed sections
        VALID_SECTIONS = {
            'need_statement', 'approach', 'budget_narrative', 'executive_summary',
            'impact_measurement', 'organizational_capacity', 'sustainability',
            'evaluation_plan', 'timeline', 'partnerships', 'risk_management',
            'project_description', 'goals_objectives', 'methodology'
        }
        
        if section not in VALID_SECTIONS:
            return jsonify({
                'success': False,
                'error': 'Invalid section name'
            }), 400
        
        # Verify grant exists
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'success': False, 'error': 'Resource not found'}), 404
        
        # Get user's organization
        from app.models import Organization
        user_org = Organization.query.filter(
            (Organization.user_id == current_user.id) | 
            (Organization.created_by_user_id == current_user.id)
        ).first()
        
        if not user_org:
            return jsonify({
                'success': False,
                'error': 'Access denied: No organization associated with user'
            }), 403
        
        # Verify grant ownership - user's org must match grant's org
        if not grant.org_id or grant.org_id != user_org.id:
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        # Find or create application
        application = Application.query.filter_by(grant_id=grant_id).first()
        if not application:
            application = Application(
                grant_id=grant_id,
                org_id=user_org.id,
                user_id=current_user.id,
                title=f"Application for {grant.title}",
                status='draft'
            )
            db.session.add(application)
            db.session.flush()  # Get the application.id
        
        # Verify application ownership
        if application.org_id != user_org.id:
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        # Check for existing content in this section
        existing_content = ApplicationContent.query.filter_by(
            application_id=application.id,
            section=section,
            is_current=True
        ).first()
        
        # Calculate next version number without mutating existing content
        next_version = 1
        if existing_content:
            next_version = existing_content.version + 1
            # Mark existing content as not current
            existing_content.is_current = False
        
        # Create new content entry
        new_content = ApplicationContent(
            application_id=application.id,
            section=section,
            content=content,
            source_tool=source_tool,
            tool_usage_id=tool_usage_id,
            version=next_version,
            is_current=True
        )
        db.session.add(new_content)
        
        # Update application sections_completed using proper dict assignment for JSON persistence
        sections_completed = application.sections_completed or {}
        sections_completed[section] = True
        application.sections_completed = sections_completed
        
        # Update application status
        if application.status == 'draft':
            application.status = 'in_progress'
        
        # Update ToolUsage status if this content came from a Smart Tool
        if tool_usage_id:
            try:
                # SECURITY FIX: Add ownership validation when updating ToolUsage records
                # Load and validate ToolUsage ownership
                tool_usage = ToolUsage.query.filter_by(
                    id=tool_usage_id,
                    org_id=user_org.id,
                    grant_id=grant_id
                ).first()
                
                if not tool_usage:
                    logger.warning(f"ToolUsage {tool_usage_id} not found or access denied for org {user_org.id}, grant {grant_id}")
                    return jsonify({
                        'success': False, 
                        'error': 'Tool usage not found or access denied'
                    }), 403
                
                # Only update if status is still 'generated' to prevent race conditions
                if tool_usage.status == 'generated':
                    tool_usage.status = 'applied'
                    logger.info(f"Updated ToolUsage {tool_usage_id} status to 'applied' for org {user_org.id}")
            except Exception as e:
                logger.error(f"Error validating ToolUsage ownership for {tool_usage_id}: {e}")
                return jsonify({
                    'success': False, 
                    'error': 'Failed to validate tool usage ownership'
                }), 500
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'application_id': application.id,
            'content_id': new_content.id,
            'section': section,
            'deep_link': f'/grants/{grant_id}/application',
            'message': f'Content saved to {section} section successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving application content for grant {grant_id}: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'Failed to save application content'
        }), 500

@workflow_bp.route('/grants/<int:grant_id>/tool-usage', methods=['GET'])
@login_required
def get_grant_tool_usage(grant_id):
    """Get Smart Tools usage for a specific grant"""
    try:
        # Get current authenticated user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Verify grant exists
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'success': False, 'error': 'Grant not found'}), 404
        
        # Get user's organization
        user_org = Organization.query.filter(
            (Organization.user_id == current_user.id) | 
            (Organization.created_by_user_id == current_user.id)
        ).first()
        
        if not user_org:
            return jsonify({
                'success': False,
                'error': 'Access denied: No organization associated with user'
            }), 403
        
        # Verify grant ownership - user's org must match grant's org
        if not grant.org_id or grant.org_id != user_org.id:
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        # Fetch all tool usage records for this grant
        from app.models import User
        tool_usage_records = db.session.query(ToolUsage, User).join(
            User, ToolUsage.user_id == User.id
        ).filter(
            ToolUsage.grant_id == grant_id
        ).order_by(ToolUsage.created_at.desc()).all()
        
        # Format the results
        tools_used = []
        for tool_usage, user in tool_usage_records:
            tool_data = tool_usage.to_dict()
            tool_data['user_name'] = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email
            tool_data['user_email'] = user.email
            
            # Add tool display information
            tool_names = {
                'pitch': 'Grant Pitch',
                'case': 'Case for Support',
                'impact': 'Impact Report',
                'thank_you': 'Thank You Letter',
                'social': 'Social Media Post',
                'newsletter': 'Newsletter Content'
            }
            tool_data['tool_display_name'] = tool_names.get(tool_usage.tool, tool_usage.tool.title())
            
            # Add status display information
            status_colors = {
                'generated': 'blue',
                'applied': 'green',
                'submitted': 'purple',
                'awarded': 'gold'
            }
            tool_data['status_color'] = status_colors.get(tool_usage.status, 'gray')
            
            tools_used.append(tool_data)
        
        # Get usage summary
        total_tools = len(tools_used)
        tools_by_type = {}
        tools_by_status = {}
        
        for tool in tools_used:
            tool_type = tool['tool']
            status = tool['status']
            
            tools_by_type[tool_type] = tools_by_type.get(tool_type, 0) + 1
            tools_by_status[status] = tools_by_status.get(status, 0) + 1
        
        return jsonify({
            'success': True,
            'grant_id': grant_id,
            'grant_title': grant.title,
            'tools_used': tools_used,
            'summary': {
                'total_tools': total_tools,
                'by_type': tools_by_type,
                'by_status': tools_by_status
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting tool usage for grant {grant_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500