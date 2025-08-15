"""
Role-Based Access Control (RBAC) Service
Enhanced permissions and team management
Phase 2: Authentication & User Management
"""

import logging
from typing import Dict, List, Optional, Any
from functools import wraps
from flask import jsonify, session
from datetime import datetime
from app import db
from app.models import User
from app.models import TeamMember

logger = logging.getLogger(__name__)

class RBACService:
    """Service for managing roles and permissions"""
    
    # Role hierarchy (higher level includes all lower permissions)
    ROLE_HIERARCHY = {
        'owner': 5,      # Full control including billing
        'admin': 4,      # Full control except billing
        'manager': 3,    # Can manage grants and applications
        'member': 2,     # Can view and edit assigned items
        'viewer': 1      # Read-only access
    }
    
    # Permission definitions
    PERMISSIONS = {
        'owner': [
            'billing.manage',
            'subscription.manage',
            'team.manage',
            'settings.manage',
            'grants.manage',
            'applications.manage',
            'reports.manage',
            'analytics.view',
            'api.access'
        ],
        'admin': [
            'team.manage',
            'settings.manage',
            'grants.manage',
            'applications.manage',
            'reports.manage',
            'analytics.view',
            'api.access'
        ],
        'manager': [
            'grants.manage',
            'applications.manage',
            'reports.create',
            'analytics.view',
            'team.invite'
        ],
        'member': [
            'grants.view',
            'grants.edit_assigned',
            'applications.view',
            'applications.edit_assigned',
            'reports.view',
            'analytics.view_limited'
        ],
        'viewer': [
            'grants.view',
            'applications.view',
            'reports.view',
            'analytics.view_limited'
        ]
    }
    
    # Feature-specific permissions
    FEATURE_PERMISSIONS = {
        'smart_tools': ['grants.manage', 'applications.manage'],
        'ai_writing': ['applications.manage', 'grants.manage'],
        'analytics': ['analytics.view'],
        'team_management': ['team.manage'],
        'billing': ['billing.manage'],
        'api': ['api.access']
    }
    
    @classmethod
    def check_permission(cls, user_id: int, permission: str, organization_id: Optional[int] = None) -> bool:
        """Check if user has specific permission"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            # System admin (if implemented) has all permissions
            if hasattr(user, 'is_system_admin') and user.is_system_admin:
                return True
            
            # Get user's role
            if organization_id:
                # Check team member role for organization
                team_member = TeamMember.query.filter_by(
                    user_id=user_id,
                    organization_id=organization_id,
                    is_active=True
                ).first()
                
                if not team_member:
                    return False
                
                role = team_member.role
            else:
                # Use user's default role
                role = user.role if hasattr(user, 'role') else 'member'
            
            # Check if role has permission
            role_permissions = cls.PERMISSIONS.get(role, [])
            
            # Direct permission check
            if permission in role_permissions:
                return True
            
            # Check wildcard permissions (e.g., 'grants.*' includes 'grants.view')
            permission_parts = permission.split('.')
            if len(permission_parts) == 2:
                wildcard = f"{permission_parts[0]}.*"
                if wildcard in role_permissions:
                    return True
                
                # Check manage permission (includes all sub-permissions)
                manage_permission = f"{permission_parts[0]}.manage"
                if manage_permission in role_permissions:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    @classmethod
    def check_feature_access(cls, user_id: int, feature: str, organization_id: Optional[int] = None) -> bool:
        """Check if user has access to a feature based on permissions"""
        try:
            required_permissions = cls.FEATURE_PERMISSIONS.get(feature, [])
            if not required_permissions:
                return True  # Feature has no permission requirements
            
            # User needs at least one of the required permissions
            for permission in required_permissions:
                if cls.check_permission(user_id, permission, organization_id):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return False
    
    @classmethod
    def get_user_permissions(cls, user_id: int, organization_id: Optional[int] = None) -> List[str]:
        """Get all permissions for a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return []
            
            # Get role
            if organization_id:
                team_member = TeamMember.query.filter_by(
                    user_id=user_id,
                    organization_id=organization_id,
                    is_active=True
                ).first()
                
                if not team_member:
                    return []
                
                role = team_member.role
                
                # Include custom permissions if any
                custom_permissions = team_member.permissions or []
            else:
                role = user.role if hasattr(user, 'role') else 'member'
                custom_permissions = []
            
            # Get role permissions
            role_permissions = cls.PERMISSIONS.get(role, [])
            
            # Combine role and custom permissions
            all_permissions = list(set(role_permissions + custom_permissions))
            
            return all_permissions
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return []
    
    @classmethod
    def can_manage_user(cls, manager_id: int, target_user_id: int, organization_id: Optional[int] = None) -> bool:
        """Check if manager can manage target user"""
        try:
            # User can always manage themselves
            if manager_id == target_user_id:
                return True
            
            # Check if manager has team management permission
            if not cls.check_permission(manager_id, 'team.manage', organization_id):
                return False
            
            if organization_id:
                # Get both users' roles in the organization
                manager_member = TeamMember.query.filter_by(
                    user_id=manager_id,
                    organization_id=organization_id,
                    is_active=True
                ).first()
                
                target_member = TeamMember.query.filter_by(
                    user_id=target_user_id,
                    organization_id=organization_id,
                    is_active=True
                ).first()
                
                if not manager_member or not target_member:
                    return False
                
                # Check role hierarchy
                manager_level = cls.ROLE_HIERARCHY.get(manager_member.role, 0)
                target_level = cls.ROLE_HIERARCHY.get(target_member.role, 0)
                
                # Manager must have higher or equal role
                return manager_level >= target_level
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking management permission: {e}")
            return False
    
    @classmethod
    def assign_role(cls, user_id: int, role: str, organization_id: Optional[int] = None,
                   assigned_by_user_id: Optional[int] = None) -> Dict[str, Any]:
        """Assign a role to a user"""
        try:
            # Validate role
            if role not in cls.ROLE_HIERARCHY:
                return {'success': False, 'error': 'Invalid role'}
            
            # Check if assigner has permission
            if assigned_by_user_id:
                if not cls.can_manage_user(assigned_by_user_id, user_id, organization_id):
                    return {'success': False, 'error': 'Insufficient permissions'}
            
            if organization_id:
                # Update team member role
                team_member = TeamMember.query.filter_by(
                    user_id=user_id,
                    organization_id=organization_id
                ).first()
                
                if not team_member:
                    # Create new team member
                    team_member = TeamMember(
                        user_id=user_id,
                        organization_id=organization_id,
                        role=role,
                        invited_by_user_id=assigned_by_user_id,
                        invitation_accepted_at=datetime.utcnow()
                    )
                    db.session.add(team_member)
                else:
                    team_member.role = role
            else:
                # Update user's default role
                user = User.query.get(user_id)
                if not user:
                    return {'success': False, 'error': 'User not found'}
                
                user.role = role
            
            db.session.commit()
            
            return {
                'success': True,
                'role': role,
                'permissions': cls.PERMISSIONS.get(role, [])
            }
            
        except Exception as e:
            logger.error(f"Error assigning role: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

# Decorator for route protection
def require_permission(permission: str):
    """Decorator to require specific permission for a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = session['user_id']
            organization_id = session.get('organization_id')
            
            if not RBACService.check_permission(user_id, permission, organization_id):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(minimum_role: str):
    """Decorator to require minimum role level for a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = session['user_id']
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            user_role = user.role if hasattr(user, 'role') else 'member'
            required_level = RBACService.ROLE_HIERARCHY.get(minimum_role, 0)
            user_level = RBACService.ROLE_HIERARCHY.get(user_role, 0)
            
            if user_level < required_level:
                return jsonify({'error': f'Minimum role required: {minimum_role}'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator