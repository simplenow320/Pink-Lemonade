"""
Mock Team Collaboration API Endpoints
Multi-user support without Flask-Login dependency
"""

from flask import Blueprint, jsonify, request, session
from app.services.team_service import TeamService
import logging

logger = logging.getLogger(__name__)

team_bp = Blueprint('team', __name__, url_prefix='/api/team')
team_service = TeamService()

def login_required(f):
    """Mock login required decorator"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

class MockUser:
    """Mock current user object"""
    def __init__(self):
        self.id = session.get('user_id', 1)
        self.org_id = session.get('org_id', 1)
        self.is_authenticated = 'user_id' in session

# Create a mock current_user object
def get_current_user():
    return MockUser()

@team_bp.route('/members', methods=['GET'])
@login_required
def get_team_members():
    """Get all team members"""
    try:
        current_user = get_current_user()
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
        current_user = get_current_user()
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
        current_user = get_current_user()
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
        current_user = get_current_user()
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
        current_user = get_current_user()
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

@team_bp.route('/permissions', methods=['GET'])
@login_required
def get_permissions():
    """Get current user permissions"""
    try:
        current_user = get_current_user()
        result = team_service.get_user_permissions(
            current_user.id,
            current_user.org_id
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting permissions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/activity', methods=['GET'])
@login_required
def get_activity():
    """Get team activity log"""
    try:
        current_user = get_current_user()
        days = request.args.get('days', 30, type=int)
        
        result = team_service.get_team_activity(
            current_user.org_id,
            days=days
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/collaboration/grants/<int:grant_id>', methods=['GET'])
@login_required
def get_grant_collaboration(grant_id):
    """Get collaboration data for a grant"""
    try:
        current_user = get_current_user()
        result = team_service.get_grant_collaboration(
            grant_id,
            current_user.org_id
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting collaboration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/collaboration/grants/<int:grant_id>/assign', methods=['POST'])
@login_required
def assign_grant(grant_id):
    """Assign grant to team member"""
    try:
        current_user = get_current_user()
        data = request.json
        assignee_id = data.get('assignee_id')
        
        if not assignee_id:
            return jsonify({
                'success': False,
                'error': 'Assignee ID required'
            }), 400
        
        result = team_service.assign_grant(
            grant_id=grant_id,
            assignee_id=assignee_id,
            assigned_by=current_user.id,
            org_id=current_user.org_id
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error assigning grant: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@team_bp.route('/collaboration/grants/<int:grant_id>/comment', methods=['POST'])
@login_required
def add_comment(grant_id):
    """Add comment to grant"""
    try:
        current_user = get_current_user()
        data = request.json
        comment = data.get('comment')
        
        if not comment:
            return jsonify({
                'success': False,
                'error': 'Comment required'
            }), 400
        
        result = team_service.add_grant_comment(
            grant_id=grant_id,
            user_id=current_user.id,
            comment=comment,
            org_id=current_user.org_id
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500