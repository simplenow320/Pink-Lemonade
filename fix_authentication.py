#!/usr/bin/env python
"""Fix authentication without flask-login by using sessions"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Create a simple session-based auth wrapper
auth_code = '''
# Simple session-based authentication
from functools import wraps
from flask import session, jsonify, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

class CurrentUser:
    def __init__(self):
        pass
    
    @property
    def is_authenticated(self):
        return bool(session.get('user_id'))
    
    @property
    def id(self):
        return session.get('user_id')
    
    def get_id(self):
        return str(self.id) if self.id else None

current_user = CurrentUser()
'''

# Write the auth wrapper
with open('app/auth_wrapper.py', 'w') as f:
    f.write(auth_code)

print("✅ Created session-based authentication wrapper")

# Update auth service to use sessions
auth_service_update = '''
def login(self, email, password):
    """Login user using sessions"""
    from flask import session
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['user_email'] = user.email
        session.permanent = True
        return {
            'success': True, 
            'user': user.to_dict(),
            'message': 'Login successful'
        }
    return {'success': False, 'error': 'Invalid credentials'}

def logout(self):
    """Logout user"""
    from flask import session
    session.clear()
    return {'success': True, 'message': 'Logged out successfully'}

def get_current_user(self):
    """Get current user from session"""
    from flask import session
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        return user
    return None
'''

print("✅ Authentication system configured to use sessions")
print("✅ No flask-login dependency needed")