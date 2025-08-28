"""
Authentication Manager - Simple session-based auth without flask-login
"""
from flask import session, redirect, url_for, flash, request
from functools import wraps
from app import db
from app.models import User, UserProgress, Organization
from datetime import datetime
import secrets

class AuthManager:
    """Manages user authentication and session state"""
    
    @staticmethod
    def login_user(user):
        """Log in a user by storing their ID in session"""
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = f"{user.first_name} {user.last_name}".strip() or user.email
        session['is_authenticated'] = True
        session['onboarding_complete'] = False
        
        # Check if user has completed onboarding
        org = Organization.query.filter_by(user_id=user.id).first()
        if org and org.profile_completeness >= 80:
            session['onboarding_complete'] = True
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return True
    
    @staticmethod
    def logout_user():
        """Log out the current user"""
        session.clear()
        return True
    
    @staticmethod
    def get_current_user():
        """Get the currently logged in user"""
        user_id = session.get('user_id')
        if user_id:
            return User.query.get(user_id)
        return None
    
    @staticmethod
    def is_authenticated():
        """Check if a user is logged in"""
        return session.get('is_authenticated', False)
    
    @staticmethod
    def require_auth(f):
        """Decorator to require authentication for routes"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('is_authenticated'):
                flash('Please log in to access this page.', 'warning')
                session['next_url'] = request.url
                return redirect('/login')
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def require_onboarding(f):
        """Decorator to ensure onboarding is complete"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('onboarding_complete'):
                user = AuthManager.get_current_user()
                if user:
                    org = Organization.query.filter_by(user_id=user.id).first()
                    if not org or org.profile_completeness < 80:
                        flash('Please complete your organization profile to access all features.', 'info')
                        return redirect(url_for('onboarding.start'))
            return f(*args, **kwargs)
        return decorated_function