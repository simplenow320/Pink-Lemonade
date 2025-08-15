"""
Team Collaboration API Endpoints
Multi-user support and role management
"""

from flask import Blueprint, jsonify, request
from app.services.team_service import TeamService
from flask_login import login_required, current_user
import logging

logger = logging.getLogger(__name__)

team_bp = Blueprint('team', __name__, url_prefix='/api/team')
team_service = TeamService()

@team_bp.route('/members', methods=['GET'])
@login_required
def get_team_members():
    """Get all team members"""
    try:
        org_id = current_user.org_id
        result = team_service.get_team_members(org_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting team members: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/invite', methods=['POST'])
@login_required
def invite_member():
    """Send team invitation"""
    try:
        data = request.json
        email = data.get('email')
        role = data.get('role', 'member')
        message = data.get('message')
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email required'
            }), 400
        
        # Check permission
        if not team_service.has_permission(current_user.id, current_user.org_id, 'manage_team'):
            return jsonify({
                'success': False,
                'error': 'Insufficient permissions'
            }), 403
        
        result = team_service.invite_team_member(
            org_id=current_user.org_id,
            inviter_id=current_user.id,
            email=email,
            role=role,
            message=message
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error inviting member: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/invitation/accept', methods=['POST'])
def accept_invitation():
    """Accept team invitation"""
    try:
        data = request.json
        token = data.get('token')
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Token required'
            }), 400
        
        # User must be logged in
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        result = team_service.accept_invitation(token, current_user.id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error accepting invitation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/member/<int:member_id>/role', methods=['PUT'])
@login_required
def update_member_role(member_id):
    """Update team member role"""
    try:
        data = request.json
        new_role = data.get('role')
        
        if not new_role:
            return jsonify({
                'success': False,
                'error': 'New role required'
            }), 400
        
        result = team_service.update_member_role(
            org_id=current_user.org_id,
            admin_id=current_user.id,
            member_id=member_id,
            new_role=new_role
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating role: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/member/<int:member_id>', methods=['DELETE'])
@login_required
def remove_member(member_id):
    """Remove team member"""
    try:
        result = team_service.remove_team_member(
            org_id=current_user.org_id,
            admin_id=current_user.id,
            member_id=member_id
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error removing member: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/activity', methods=['GET'])
@login_required
def get_activity_feed():
    """Get team activity feed"""
    try:
        limit = request.args.get('limit', 50, type=int)
        result = team_service.get_activity_feed(current_user.org_id, limit)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/grant/<int:grant_id>/comment', methods=['POST'])
@login_required
def add_comment(grant_id):
    """Add comment to grant"""
    try:
        data = request.json
        comment_text = data.get('comment')
        parent_id = data.get('parent_id')
        
        if not comment_text:
            return jsonify({
                'success': False,
                'error': 'Comment text required'
            }), 400
        
        result = team_service.add_comment(
            org_id=current_user.org_id,
            user_id=current_user.id,
            grant_id=grant_id,
            comment_text=comment_text,
            parent_id=parent_id
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get user notifications"""
    try:
        unread_only = request.args.get('unread_only', False, type=bool)
        result = team_service.get_notifications(current_user.id, unread_only)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/statistics', methods=['GET'])
@login_required
def get_team_statistics():
    """Get team collaboration statistics"""
    try:
        result = team_service.get_team_statistics(current_user.org_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/permissions/check', methods=['POST'])
@login_required
def check_permission():
    """Check if user has specific permission"""
    try:
        data = request.json
        permission = data.get('permission')
        
        if not permission:
            return jsonify({
                'success': False,
                'error': 'Permission name required'
            }), 400
        
        has_permission = team_service.has_permission(
            current_user.id,
            current_user.org_id,
            permission
        )
        
        return jsonify({
            'success': True,
            'has_permission': has_permission,
            'permission': permission
        })
        
    except Exception as e:
        logger.error(f"Error checking permission: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/roles', methods=['GET'])
def get_available_roles():
    """Get all available roles and permissions"""
    try:
        roles = []
        for role_key, role_info in TeamService.ROLES.items():
            roles.append({
                'id': role_key,
                'name': role_info['name'],
                'level': role_info['level'],
                'permissions': role_info['permissions']
            })
        
        return jsonify({
            'success': True,
            'roles': sorted(roles, key=lambda x: x['level'], reverse=True)
        })
        
    except Exception as e:
        logger.error(f"Error getting roles: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500