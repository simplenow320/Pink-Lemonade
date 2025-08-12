"""
Team Collaboration Features
Manages team members, roles, and collaborative grant work
"""
from flask import Blueprint, jsonify, request
from app import db
from app.models import User, UserInvite, GrantActivity, GrantNote
from datetime import datetime, timedelta
import secrets
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('team_collaboration', __name__)

@bp.route('/api/team/members', methods=['GET'])
def get_team_members():
    """
    Get all team members for an organization
    """
    try:
        org_id = request.args.get('org_id', 1, type=int)
        
        members = User.query.filter_by(org_id=str(org_id)).all()
        
        team_data = []
        for member in members:
            team_data.append({
                'id': member.id,
                'name': f"{member.first_name or ''} {member.last_name or ''}".strip() or member.email,
                'email': member.email,
                'role': member.role,
                'job_title': member.job_title,
                'last_login': member.last_login.isoformat() if member.last_login else None,
                'is_active': member.is_active
            })
        
        return jsonify({
            'success': True,
            'members': team_data,
            'total': len(team_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting team members: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/team/invite', methods=['POST'])
def invite_team_member():
    """
    Invite a new team member via email
    """
    try:
        data = request.get_json() or {}
        email = data.get('email')
        role = data.get('role', 'member')
        org_id = data.get('org_id', 1)
        invited_by = data.get('invited_by', 1)
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'User already exists'}), 400
        
        # Check for existing invite
        existing_invite = UserInvite.query.filter_by(
            email=email,
            org_id=org_id
        ).first()
        
        if existing_invite and existing_invite.is_valid():
            return jsonify({'error': 'Invite already sent to this email'}), 400
        
        # Create new invite
        invite = UserInvite(
            email=email,
            org_id=org_id,
            role=role,
            invited_by=invited_by
        )
        invite.generate_invite_token()
        
        db.session.add(invite)
        db.session.commit()
        
        # In production, this would send an email
        invite_link = f"/join/invite/{invite.invite_token}"
        
        return jsonify({
            'success': True,
            'message': f'Invitation sent to {email}',
            'invite_link': invite_link,
            'expires_at': invite.expires_at.isoformat() if invite.expires_at else None
        })
        
    except Exception as e:
        logger.error(f"Error inviting team member: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/team/activity', methods=['GET'])
def get_team_activity():
    """
    Get recent team activity on grants
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        grant_id = request.args.get('grant_id', type=int)
        
        query = GrantActivity.query
        if grant_id:
            query = query.filter_by(grant_id=grant_id)
        
        activities = query.order_by(GrantActivity.created_at.desc()).limit(limit).all()
        
        activity_data = []
        for activity in activities:
            # Get user info
            user = User.query.get(activity.user_id) if activity.user_id else None
            user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() if user else "System"
            
            activity_data.append({
                'id': activity.id,
                'grant_id': activity.grant_id,
                'user': user_name or user.email if user else "System",
                'action': activity.action,
                'details': activity.details,
                'created_at': activity.created_at.isoformat() if activity.created_at else None
            })
        
        return jsonify({
            'success': True,
            'activities': activity_data,
            'total': len(activity_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting team activity: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/team/notes', methods=['POST'])
def add_team_note():
    """
    Add a collaborative note to a grant
    """
    try:
        data = request.get_json() or {}
        grant_id = data.get('grant_id')
        body = data.get('body')
        author = data.get('author', 'Team Member')
        
        if not grant_id or not body:
            return jsonify({'error': 'Grant ID and note body are required'}), 400
        
        # Create note
        note = GrantNote(
            grant_id=grant_id,
            body=body,
            author=author
        )
        db.session.add(note)
        
        # Log activity
        activity = GrantActivity(
            grant_id=grant_id,
            user_id=1,  # Default user
            action='note_added',
            details=f'Added note: {body[:100]}...' if len(body) > 100 else body
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'note': note.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error adding note: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/team/roles', methods=['GET'])
def get_team_roles():
    """
    Get available team roles
    """
    return jsonify({
        'roles': [
            {'value': 'admin', 'label': 'Administrator', 'description': 'Full access to all features'},
            {'value': 'manager', 'label': 'Grant Manager', 'description': 'Manage grants and applications'},
            {'value': 'member', 'label': 'Team Member', 'description': 'View and collaborate on grants'},
            {'value': 'viewer', 'label': 'Viewer', 'description': 'Read-only access'}
        ]
    })

@bp.route('/api/team/permissions/<int:user_id>', methods=['PUT'])
def update_user_permissions(user_id):
    """
    Update user role and permissions
    """
    try:
        data = request.get_json() or {}
        new_role = data.get('role')
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if new_role:
            user.role = new_role
        
        # Log activity
        activity = GrantActivity(
            user_id=1,  # Admin user
            action='permission_change',
            details=f'Updated {user.email} role to {new_role}'
        )
        db.session.add(activity)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User permissions updated',
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating permissions: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/team/stats', methods=['GET'])
def get_team_stats():
    """
    Get team collaboration statistics
    """
    try:
        org_id = request.args.get('org_id', 1, type=int)
        
        # Get team stats
        total_members = User.query.filter_by(org_id=str(org_id)).count()
        active_members = User.query.filter_by(org_id=str(org_id), is_active=True).count()
        
        # Get activity stats (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_activities = GrantActivity.query.filter(
            GrantActivity.created_at >= thirty_days_ago
        ).count()
        
        # Get notes count
        total_notes = GrantNote.query.count()
        
        # Get pending invites count (simplified query)
        pending_invites = 0  # Default value for now
        
        return jsonify({
            'success': True,
            'stats': {
                'total_members': total_members,
                'active_members': active_members,
                'pending_invites': pending_invites,
                'recent_activities': recent_activities,
                'total_notes': total_notes,
                'collaboration_score': min(100, (active_members * 20) + (recent_activities * 2))
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting team stats: {e}")
        return jsonify({'error': str(e)}), 500