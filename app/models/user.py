"""
User Model for Authentication

This module contains the User model for authentication and user management.
"""

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

# Try to import Flask-Login, provide fallback if not available
try:
    from flask_login import UserMixin
except ImportError:
    # Create a simple UserMixin replacement
    class UserMixin:
        @property
        def is_authenticated(self):
            return True

        @property
        def is_active(self):
            return True

        @property
        def is_anonymous(self):
            return False

        def get_id(self):
            try:
                return str(self.id)
            except AttributeError:
                raise NotImplementedError('No `id` attribute - override `get_id`')


class User(UserMixin, db.Model):
    """
    User model for authentication and multi-tenancy
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    
    # Organization and role fields for multi-tenancy
    org_id = db.Column(db.String(100), nullable=True, index=True)  # Organization ID for data scoping
    role = db.Column(db.String(50), default='member')  # admin, manager, member
    
    # Account status and metadata
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True)
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Profile fields
    phone = db.Column(db.String(20))
    timezone = db.Column(db.String(50), default='America/New_York')
    notification_preferences = db.Column(db.JSON, default=dict)
    
    def set_password(self, password):
        """Set password hash from plain text password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self):
        """Generate a unique verification token"""
        self.verification_token = secrets.token_urlsafe(32)
        return self.verification_token
    
    def generate_reset_token(self):
        """Generate a unique password reset token"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.now() + timedelta(hours=24)
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verify if reset token is valid and not expired"""
        if self.reset_token != token:
            return False
        if self.reset_token_expiry and self.reset_token_expiry < datetime.now():
            return False
        return True
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def has_role(self, role):
        """Check if user has a specific role or higher"""
        role_hierarchy = {'member': 0, 'manager': 1, 'admin': 2}
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(role, 0)
    
    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'org_id': self.org_id,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'phone': self.phone,
            'timezone': self.timezone,
            'notification_preferences': self.notification_preferences
        }


from datetime import timedelta


class UserInvite(db.Model):
    """
    Model for user invitations to organizations
    """
    __tablename__ = 'user_invites'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    org_id = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), default='member')
    invited_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    invite_token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    accepted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship
    inviter = db.relationship('User', foreign_keys=[invited_by])
    
    def generate_token(self):
        """Generate invitation token"""
        self.invite_token = secrets.token_urlsafe(32)
        self.expires_at = datetime.now() + timedelta(days=7)
        return self.invite_token
    
    def is_valid(self):
        """Check if invitation is still valid"""
        return self.expires_at > datetime.now() and self.accepted_at is None
    
    def to_dict(self):
        """Convert invite to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'org_id': self.org_id,
            'role': self.role,
            'invited_by': self.invited_by,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_valid': self.is_valid()
        }