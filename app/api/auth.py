"""
Authentication API endpoints

Handles user registration, login, logout, and password reset functionality.
"""

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from functools import wraps
from app import db
from app.models import User, UserInvite
from datetime import datetime, timedelta
import secrets
import re
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Session-based authentication helpers
def get_current_user():
    """Get the current logged-in user from session"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def init_auth(app):
    """Initialize authentication with the app"""
    # Session-based auth configuration
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"


@bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        email = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        if not email or not username or not password:
            return jsonify({'error': 'Email, username, and password are required'}), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 409
        
        # Create new user
        user = User()
        user.email = email
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = True
        user.is_verified = False  # Email verification required
        user.set_password(password)
        user.generate_verification_token()
        
        # Check if this is the first user (make them admin)
        if User.query.count() == 0:
            user.role = 'admin'
            user.is_verified = True  # Auto-verify first user
        
        # Generate organization ID if not provided
        if not user.org_id:
            user.org_id = f"org_{secrets.token_hex(8)}"
        
        db.session.add(user)
        db.session.commit()
        
        # Auto-login if first user
        if user.role == 'admin' and user.is_verified:
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_org_id'] = user.org_id
            session.permanent = True
        
        logger.info(f"New user registered: {email}")
        
        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict(),
            'verification_required': not user.is_verified
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500


@bp.route('/login', methods=['POST'])
def login():
    """Log in a user"""
    try:
        data = request.get_json()
        
        # Get credentials
        email_or_username = data.get('email', '').strip().lower()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        if not email_or_username or not password:
            return jsonify({'error': 'Email/username and password are required'}), 400
        
        # Find user by email or username
        user = User.query.filter(
            (User.email == email_or_username) | 
            (User.username == email_or_username)
        ).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if account is active
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 403
        
        # Check if email is verified (skip for admin)
        if not user.is_verified and user.role != 'admin':
            return jsonify({'error': 'Please verify your email before logging in'}), 403
        
        # Update last login
        user.last_login = datetime.now()
        db.session.commit()
        
        # Log the user in
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_org_id'] = user.org_id
        session.permanent = remember
        
        logger.info(f"User logged in: {user.email}")
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500


@bp.route('/logout', methods=['POST'])
def logout():
    """Log out the current user"""
    try:
        user_email = session.get('user_email', 'unknown')
        session.clear()
        
        logger.info(f"User logged out: {user_email}")
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500


@bp.route('/me', methods=['GET'])
def me():
    """Get current user information"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({'user': user.to_dict()}), 200
    
    return jsonify({'error': 'Not authenticated'}), 401


@bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify user's email with token"""
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'error': 'Verification token is required'}), 400
        
        # Find user by verification token
        user = User.query.filter_by(verification_token=token).first()
        
        if not user:
            return jsonify({'error': 'Invalid verification token'}), 404
        
        # Mark user as verified
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        
        logger.info(f"Email verified for user: {user.email}")
        
        return jsonify({
            'message': 'Email verified successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Verification failed'}), 500


@bp.route('/request-reset', methods=['POST'])
def request_password_reset():
    """Request a password reset token"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Don't reveal if email exists or not
            return jsonify({'message': 'If the email exists, a reset link has been sent'}), 200
        
        # Generate reset token
        token = user.generate_reset_token()
        db.session.commit()
        
        # In production, send email with reset link
        # For now, just return the token (development only)
        logger.info(f"Password reset requested for: {email}")
        
        return jsonify({
            'message': 'Password reset token generated',
            'token': token  # Remove this in production
        }), 200
        
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Reset request failed'}), 500


@bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        new_password = data.get('password', '')
        
        if not token or not new_password:
            return jsonify({'error': 'Token and new password are required'}), 400
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Find user by reset token
        user = User.query.filter_by(reset_token=token).first()
        
        if not user or not user.verify_reset_token(token):
            return jsonify({'error': 'Invalid or expired reset token'}), 404
        
        # Update password
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        logger.info(f"Password reset for user: {user.email}")
        
        return jsonify({
            'message': 'Password reset successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Password reset failed'}), 500


@bp.route('/update-profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        if 'phone' in data:
            user.phone = data['phone'].strip()
        if 'timezone' in data:
            user.timezone = data['timezone']
        if 'notification_preferences' in data:
            user.notification_preferences = data['notification_preferences']
        
        user.updated_at = datetime.now()
        db.session.commit()
        
        logger.info(f"Profile updated for user: {user.email}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Profile update failed'}), 500


@bp.route('/check-session', methods=['GET'])
def check_session():
    """Check if user is logged in"""
    user = get_current_user()
    if user:
        return jsonify({
            'authenticated': True,
            'user': user.to_dict()
        }), 200
    else:
        return jsonify({
            'authenticated': False
        }), 200