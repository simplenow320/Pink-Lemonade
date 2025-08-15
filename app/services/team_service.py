"""
Team Collaboration Service
Manages team members, roles, and collaborative features
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.models import User, Organization, Grant, db
import logging
import secrets
import hashlib

logger = logging.getLogger(__name__)

class TeamService:
    """
    Provides team collaboration features:
    - Team member management
    - Role-based permissions
    - Activity tracking
    - Notifications
    - Shared workspaces
    """
    
    # Role definitions
    ROLES = {
        'owner': {
            'name': 'Owner',
            'level': 100,
            'permissions': [
                'manage_billing',
                'manage_team',
                'manage_settings',
                'delete_organization',
                'all_grants',
                'all_tools'
            ]
        },
        'admin': {
            'name': 'Administrator',
            'level': 80,
            'permissions': [
                'manage_team',
                'manage_settings',
                'all_grants',
                'all_tools',
                'export_data'
            ]
        },
        'manager': {
            'name': 'Manager',
            'level': 60,
            'permissions': [
                'manage_grants',
                'approve_submissions',
                'all_tools',
                'view_analytics',
                'export_data'
            ]
        },
        'member': {
            'name': 'Team Member',
            'level': 40,
            'permissions': [
                'view_grants',
                'create_grants',
                'use_tools',
                'add_comments'
            ]
        },
        'viewer': {
            'name': 'Viewer',
            'level': 20,
            'permissions': [
                'view_grants',
                'view_analytics'
            ]
        }
    }
    
    def invite_team_member(self, org_id: int, inviter_id: int, 
                          email: str, role: str, message: str = None) -> Dict:
        """Send team invitation"""
        try:
            # Validate role
            if role not in self.ROLES:
                return {'success': False, 'error': 'Invalid role'}
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                # Check if already in team
                team_member = db.session.query(TeamMember).filter_by(
                    org_id=org_id,
                    user_id=existing_user.id
                ).first()
                
                if team_member:
                    return {'success': False, 'error': 'User already in team'}
            
            # Generate invitation token
            token = secrets.token_urlsafe(32)
            
            # Create invitation record
            invitation = TeamInvitation(
                org_id=org_id,
                inviter_id=inviter_id,
                email=email,
                role=role,
                token=token,
                message=message,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(invitation)
            db.session.commit()
            
            # Send invitation email (would integrate with SendGrid)
            self._send_invitation_email(email, token, message)
            
            return {
                'success': True,
                'invitation_id': invitation.id,
                'token': token,
                'expires_at': invitation.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error inviting team member: {e}")
            return {'success': False, 'error': str(e)}
    
    def accept_invitation(self, token: str, user_id: int) -> Dict:
        """Accept team invitation"""
        try:
            # Find invitation
            invitation = TeamInvitation.query.filter_by(token=token).first()
            
            if not invitation:
                return {'success': False, 'error': 'Invalid invitation'}
            
            if invitation.accepted:
                return {'success': False, 'error': 'Invitation already accepted'}
            
            if invitation.expires_at < datetime.utcnow():
                return {'success': False, 'error': 'Invitation expired'}
            
            # Add user to team
            team_member = TeamMember(
                org_id=invitation.org_id,
                user_id=user_id,
                role=invitation.role,
                invited_by=invitation.inviter_id,
                joined_at=datetime.utcnow()
            )
            db.session.add(team_member)
            
            # Mark invitation as accepted
            invitation.accepted = True
            invitation.accepted_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log activity
            self._log_activity(
                invitation.org_id,
                user_id,
                'joined_team',
                f'Joined as {invitation.role}'
            )
            
            return {
                'success': True,
                'org_id': invitation.org_id,
                'role': invitation.role
            }
            
        except Exception as e:
            logger.error(f"Error accepting invitation: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_member_role(self, org_id: int, admin_id: int, 
                          member_id: int, new_role: str) -> Dict:
        """Update team member role"""
        try:
            # Validate role
            if new_role not in self.ROLES:
                return {'success': False, 'error': 'Invalid role'}
            
            # Check admin permissions
            if not self.has_permission(admin_id, org_id, 'manage_team'):
                return {'success': False, 'error': 'Insufficient permissions'}
            
            # Find team member
            member = TeamMember.query.filter_by(
                org_id=org_id,
                user_id=member_id
            ).first()
            
            if not member:
                return {'success': False, 'error': 'Member not found'}
            
            # Prevent demoting owner
            if member.role == 'owner' and new_role != 'owner':
                return {'success': False, 'error': 'Cannot demote organization owner'}
            
            old_role = member.role
            member.role = new_role
            db.session.commit()
            
            # Log activity
            self._log_activity(
                org_id,
                admin_id,
                'role_changed',
                f'Changed {member_id} role from {old_role} to {new_role}'
            )
            
            return {
                'success': True,
                'member_id': member_id,
                'old_role': old_role,
                'new_role': new_role
            }
            
        except Exception as e:
            logger.error(f"Error updating role: {e}")
            return {'success': False, 'error': str(e)}
    
    def remove_team_member(self, org_id: int, admin_id: int, member_id: int) -> Dict:
        """Remove team member"""
        try:
            # Check permissions
            if not self.has_permission(admin_id, org_id, 'manage_team'):
                return {'success': False, 'error': 'Insufficient permissions'}
            
            # Find member
            member = TeamMember.query.filter_by(
                org_id=org_id,
                user_id=member_id
            ).first()
            
            if not member:
                return {'success': False, 'error': 'Member not found'}
            
            # Prevent removing owner
            if member.role == 'owner':
                return {'success': False, 'error': 'Cannot remove organization owner'}
            
            # Remove member
            db.session.delete(member)
            db.session.commit()
            
            # Log activity
            self._log_activity(
                org_id,
                admin_id,
                'member_removed',
                f'Removed user {member_id} from team'
            )
            
            return {
                'success': True,
                'removed_member_id': member_id
            }
            
        except Exception as e:
            logger.error(f"Error removing member: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_team_members(self, org_id: int) -> Dict:
        """Get all team members"""
        try:
            members = TeamMember.query.filter_by(org_id=org_id).all()
            
            team_list = []
            for member in members:
                user = User.query.get(member.user_id)
                if user:
                    team_list.append({
                        'user_id': user.id,
                        'email': user.email,
                        'name': f"{user.first_name} {user.last_name}".strip() or user.email,
                        'role': member.role,
                        'role_name': self.ROLES[member.role]['name'],
                        'joined_at': member.joined_at.isoformat(),
                        'last_active': member.last_active.isoformat() if member.last_active else None,
                        'permissions': self.ROLES[member.role]['permissions']
                    })
            
            # Sort by role level (owners first)
            team_list.sort(key=lambda x: self.ROLES[x['role']]['level'], reverse=True)
            
            return {
                'success': True,
                'team': team_list,
                'total_members': len(team_list)
            }
            
        except Exception as e:
            logger.error(f"Error getting team: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_activity_feed(self, org_id: int, limit: int = 50) -> Dict:
        """Get team activity feed"""
        try:
            activities = TeamActivity.query.filter_by(org_id=org_id)\
                .order_by(TeamActivity.created_at.desc())\
                .limit(limit)\
                .all()
            
            feed = []
            for activity in activities:
                user = User.query.get(activity.user_id)
                feed.append({
                    'id': activity.id,
                    'user': user.email if user else 'Unknown',
                    'action': activity.action,
                    'details': activity.details,
                    'entity_type': activity.entity_type,
                    'entity_id': activity.entity_id,
                    'created_at': activity.created_at.isoformat()
                })
            
            return {
                'success': True,
                'activities': feed,
                'count': len(feed)
            }
            
        except Exception as e:
            logger.error(f"Error getting activity feed: {e}")
            return {'success': False, 'error': str(e)}
    
    def add_comment(self, org_id: int, user_id: int, grant_id: int, 
                   comment_text: str, parent_id: Optional[int] = None) -> Dict:
        """Add comment to grant"""
        try:
            # Check permissions
            if not self.has_permission(user_id, org_id, 'add_comments'):
                return {'success': False, 'error': 'Insufficient permissions'}
            
            # Verify grant belongs to org
            grant = Grant.query.filter_by(id=grant_id, org_id=org_id).first()
            if not grant:
                return {'success': False, 'error': 'Grant not found'}
            
            # Create comment
            comment = GrantComment(
                grant_id=grant_id,
                user_id=user_id,
                comment_text=comment_text,
                parent_id=parent_id,
                created_at=datetime.utcnow()
            )
            db.session.add(comment)
            db.session.commit()
            
            # Log activity
            self._log_activity(
                org_id,
                user_id,
                'comment_added',
                f'Commented on grant {grant.title}',
                entity_type='grant',
                entity_id=grant_id
            )
            
            # Create notifications for mentioned users
            self._process_mentions(comment_text, org_id, user_id, grant_id)
            
            return {
                'success': True,
                'comment_id': comment.id,
                'created_at': comment.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_notifications(self, user_id: int, unread_only: bool = False) -> Dict:
        """Get user notifications"""
        try:
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(read=False)
            
            notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
            
            notif_list = []
            for notif in notifications:
                notif_list.append({
                    'id': notif.id,
                    'type': notif.type,
                    'message': notif.message,
                    'link': notif.link,
                    'read': notif.read,
                    'created_at': notif.created_at.isoformat()
                })
            
            # Mark as read
            if not unread_only:
                Notification.query.filter_by(user_id=user_id, read=False).update({'read': True})
                db.session.commit()
            
            return {
                'success': True,
                'notifications': notif_list,
                'unread_count': len([n for n in notif_list if not n['read']])
            }
            
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return {'success': False, 'error': str(e)}
    
    def has_permission(self, user_id: int, org_id: int, permission: str) -> bool:
        """Check if user has specific permission"""
        try:
            member = TeamMember.query.filter_by(
                org_id=org_id,
                user_id=user_id
            ).first()
            
            if not member:
                return False
            
            role_permissions = self.ROLES.get(member.role, {}).get('permissions', [])
            return permission in role_permissions
            
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    def get_team_statistics(self, org_id: int) -> Dict:
        """Get team collaboration statistics"""
        try:
            # Team composition
            members = TeamMember.query.filter_by(org_id=org_id).all()
            role_distribution = {}
            for member in members:
                role_distribution[member.role] = role_distribution.get(member.role, 0) + 1
            
            # Activity metrics
            last_30_days = datetime.utcnow() - timedelta(days=30)
            recent_activities = TeamActivity.query.filter(
                TeamActivity.org_id == org_id,
                TeamActivity.created_at >= last_30_days
            ).count()
            
            # Collaboration metrics
            comments = GrantComment.query.join(Grant).filter(
                Grant.org_id == org_id,
                GrantComment.created_at >= last_30_days
            ).count()
            
            # Active users
            active_users = set()
            for activity in TeamActivity.query.filter(
                TeamActivity.org_id == org_id,
                TeamActivity.created_at >= last_30_days
            ).all():
                active_users.add(activity.user_id)
            
            return {
                'success': True,
                'statistics': {
                    'total_members': len(members),
                    'role_distribution': role_distribution,
                    'active_users_30d': len(active_users),
                    'activities_30d': recent_activities,
                    'comments_30d': comments,
                    'collaboration_score': min(100, (len(active_users) / len(members) * 100) if members else 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {'success': False, 'error': str(e)}
    
    # Helper methods
    
    def _send_invitation_email(self, email: str, token: str, message: str = None):
        """Send invitation email (placeholder for SendGrid integration)"""
        # This would integrate with SendGrid service
        logger.info(f"Invitation sent to {email} with token {token}")
    
    def _log_activity(self, org_id: int, user_id: int, action: str, 
                     details: str, entity_type: str = None, entity_id: int = None):
        """Log team activity"""
        try:
            activity = TeamActivity(
                org_id=org_id,
                user_id=user_id,
                action=action,
                details=details,
                entity_type=entity_type,
                entity_id=entity_id,
                created_at=datetime.utcnow()
            )
            db.session.add(activity)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    def _process_mentions(self, text: str, org_id: int, sender_id: int, grant_id: int):
        """Process @mentions in comments"""
        import re
        
        # Find @mentions
        mentions = re.findall(r'@(\w+)', text)
        
        for username in mentions:
            # Find user
            user = User.query.filter_by(username=username).first()
            if user:
                # Check if user is in team
                member = TeamMember.query.filter_by(
                    org_id=org_id,
                    user_id=user.id
                ).first()
                
                if member:
                    # Create notification
                    notification = Notification(
                        user_id=user.id,
                        type='mention',
                        message=f'You were mentioned in a comment',
                        link=f'/grants/{grant_id}#comments',
                        created_at=datetime.utcnow()
                    )
                    db.session.add(notification)
        
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Error processing mentions: {e}")


# Model placeholders (would be in models.py)
class TeamMember:
    """Team member model"""
    pass

class TeamInvitation:
    """Team invitation model"""
    pass

class TeamActivity:
    """Team activity log model"""
    pass

class GrantComment:
    """Grant comment model"""
    pass

class Notification:
    """User notification model"""
    pass