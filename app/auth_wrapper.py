
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
