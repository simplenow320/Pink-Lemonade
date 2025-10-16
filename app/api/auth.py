"""
Authentication API endpoints

Handles user registration, login, logout, and password reset functionality.
"""

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from app import db
from app.models import User, UserInvite
from datetime import datetime, timedelta
import secrets
import re
import logging
import pyotp
import qrcode
import io
import base64
from user_agents import parse

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Import the auth service
from app.services.auth_service import AuthService
auth_service = AuthService()

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
    """Register a new user using the AuthService"""
    try:
        data = request.get_json()
        
        # Extract registration data
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        org_name = data.get('org_name', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        job_title = data.get('job_title', '').strip()
        
        # Validate required fields
        if not email or not password or not org_name or not first_name or not last_name:
            return jsonify({'error': 'All required fields must be filled'}), 400
        
        # Use AuthService to register user
        result = auth_service.register_user(
            email=email,
            password=password,
            org_name=org_name,
            first_name=first_name,
            last_name=last_name,
            job_title=job_title
        )
        
        if result['success']:
            # Automatically log in the user after registration
            session['user_id'] = result['user']['id']
            session['user_email'] = result['user']['email']
            session.permanent = False  # Don't remember by default on registration
            
            # Create minimal Organization for the new user
            # Low completeness ensures they go through onboarding
            from app.models import Organization
            org = Organization()
            org.name = org_name
            org.legal_name = org_name
            org.user_id = result['user']['id']
            org.created_by_user_id = result['user']['id']
            org.profile_completeness = 10  # Needs onboarding
            db.session.add(org)
            db.session.commit()
            
            logger.info(f"User registered and logged in: {email}")
            
            return jsonify({
                'message': 'Registration successful! Let\'s set up your organization profile.',
                'user': result['user'],
                'redirect': '/onboarding/welcome'
            }), 201
        else:
            return jsonify({'error': result['error']}), 400
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500


@bp.route('/login', methods=['POST'])
def login():
    """Log in a user using the AuthService"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        # Get credentials
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Use AuthService to login user
        result = auth_service.login_user(
            email=email,
            password=password,
            remember=remember
        )

        if result['success']:
            user = User.query.get(result['user']['id'])
            
            # Check if 2FA is enabled
            if user and user.two_factor_enabled:
                # Store user ID temporarily for 2FA verification
                session['pending_2fa_user_id'] = user.id
                return jsonify({
                    'requires_2fa': True,
                    'message': 'Please enter your 2FA code'
                }), 200
            
            # Set session (session regeneration happens automatically with session.clear())
            session['user_id'] = result['user']['id']
            session['user_email'] = result['user']['email']
            session['is_authenticated'] = True
            session['login_time'] = datetime.utcnow().isoformat()
            session.permanent = remember
            
            # Track session with device information
            from app.models import UserSession
            
            ua_string = request.headers.get('User-Agent', '')
            user_agent = parse(ua_string)
            
            session_token = secrets.token_urlsafe(32)
            user_session = UserSession(
                user_id=result['user']['id'],
                session_token=session_token,
                ip_address=request.remote_addr,
                user_agent=ua_string,
                device_type=user_agent.device.family if user_agent.device.family != 'Other' else 'desktop',
                browser=f"{user_agent.browser.family} {user_agent.browser.version_string}",
                os=f"{user_agent.os.family} {user_agent.os.version_string}",
                is_current=True,
                expires_at=datetime.utcnow() + timedelta(days=30 if remember else 1)
            )
            
            # Mark all other sessions as not current
            UserSession.query.filter_by(user_id=result['user']['id']).update({'is_current': False})
            
            db.session.add(user_session)
            db.session.commit()
            
            # Store session ID
            session['session_id'] = session_token
            
            logger.info(f"Session created for user {result['user']['email']} from {request.remote_addr}")
            
            # Check if user needs onboarding
            from app.models import Organization
            user_id = result['user']['id']
            # Check both user_id and created_by_user_id fields
            org = Organization.query.filter(
                (Organization.user_id == user_id) | 
                (Organization.created_by_user_id == user_id)
            ).first()
            
            # Check if organization profile is complete
            if not org:
                redirect_url = '/onboarding/welcome'
            elif hasattr(org, 'profile_completeness') and org.profile_completeness < 60:
                redirect_url = '/onboarding/welcome'
            elif hasattr(org, 'onboarding_completed_at') and org.onboarding_completed_at:
                # User has completed onboarding flow, go to dashboard
                redirect_url = '/dashboard'
            else:
                redirect_url = '/dashboard'
            
            return jsonify({
                'message': 'Login successful',
                'token': result['token'],
                'user': result['user'],
                'redirect': redirect_url
            }), 200
        else:
            return jsonify({'error': result['error']}), 401
        
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


@bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request a password reset token"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Use AuthService to request password reset
        result = auth_service.request_password_reset(email)
        
        # Always return success to not reveal if email exists
        return jsonify({
            'message': 'If an account exists with that email, reset instructions have been sent.'
        }), 200
        
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


# ==================== SESSION MANAGEMENT ====================

@bp.route('/sessions', methods=['GET'])
def get_sessions():
    """Get all active sessions for current user"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        from app.models import UserSession
        
        current_session_id = session.get('session_id')
        sessions = UserSession.query.filter_by(
            user_id=session['user_id']
        ).filter(
            UserSession.expires_at > datetime.utcnow()
        ).all()
        
        # Mark current session
        session_list = []
        for s in sessions:
            s_dict = s.to_dict()
            s_dict['is_current'] = (s.session_token == current_session_id)
            session_list.append(s_dict)
        
        return jsonify({
            'sessions': session_list
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        return jsonify({'error': 'Failed to fetch sessions'}), 500


@bp.route('/sessions/<int:session_id>', methods=['DELETE'])
def revoke_session(session_id):
    """Revoke a specific session"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        from app.models import UserSession
        
        user_session = UserSession.query.filter_by(
            id=session_id,
            user_id=session['user_id']
        ).first()
        
        if not user_session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Prevent revoking current session
        if user_session.session_token == session.get('session_id'):
            return jsonify({'error': 'Cannot revoke current session'}), 400
        
        db.session.delete(user_session)
        db.session.commit()
        
        logger.info(f"Session {session_id} revoked by user {session['user_id']}")
        
        return jsonify({'message': 'Session revoked successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error revoking session: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to revoke session'}), 500


@bp.route('/sessions/all', methods=['DELETE'])
def revoke_all_sessions():
    """Revoke all other sessions except current"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        from app.models import UserSession
        
        current_session_id = session.get('session_id')
        
        # Delete all sessions except current
        deleted = UserSession.query.filter(
            UserSession.user_id == session['user_id'],
            UserSession.session_token != current_session_id
        ).delete()
        
        db.session.commit()
        
        logger.info(f"Revoked {deleted} sessions for user {session['user_id']}")
        
        return jsonify({
            'message': f'Successfully revoked {deleted} session(s)',
            'count': deleted
        }), 200
        
    except Exception as e:
        logger.error(f"Error revoking all sessions: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to revoke sessions'}), 500

# ==================== TWO-FACTOR AUTHENTICATION ====================

@bp.route('/2fa/setup', methods=['POST'])
def setup_2fa():
    """Generate TOTP secret and QR code for 2FA setup"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        import pyotp
        import qrcode
        import io
        import base64
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Generate TOTP secret
        totp_secret = pyotp.random_base32()
        
        # Store temporarily (not enabled yet)
        user.totp_secret = totp_secret
        db.session.commit()
        
        # Generate QR code
        totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
            name=user.email,
            issuer_name='GrantFlow'
        )
        
        # Create QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        logger.info(f"2FA setup initiated for user {user.email}")
        
        return jsonify({
            'secret': totp_secret,
            'qr_code': f'data:image/png;base64,{qr_code_base64}',
            'totp_uri': totp_uri
        }), 200
        
    except Exception as e:
        logger.error(f"Error setting up 2FA: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to setup 2FA'}), 500


@bp.route('/2fa/enable', methods=['POST'])
def enable_2fa():
    """Verify TOTP code and enable 2FA"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        import pyotp
        
        data = request.get_json() or {}
        code = data.get('code')
        
        if not code:
            return jsonify({'error': 'Verification code required'}), 400
        
        user = User.query.get(session['user_id'])
        if not user or not user.totp_secret:
            return jsonify({'error': 'No 2FA setup found'}), 400
        
        # Verify TOTP code
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            return jsonify({'error': 'Invalid verification code'}), 400
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        hashed_backup_codes = [generate_password_hash(code) for code in backup_codes]
        
        # Enable 2FA
        user.two_factor_enabled = True
        user.backup_codes = hashed_backup_codes
        user.two_factor_verified_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"2FA enabled for user {user.email}")
        
        return jsonify({
            'message': '2FA enabled successfully',
            'backup_codes': backup_codes
        }), 200
        
    except Exception as e:
        logger.error(f"Error enabling 2FA: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to enable 2FA'}), 500


@bp.route('/2fa/verify', methods=['POST'])
def verify_2fa():
    """Verify 2FA code during login"""
    try:
        import pyotp
        from werkzeug.security import check_password_hash
        
        data = request.get_json() or {}
        code = data.get('code')
        user_id = session.get('pending_2fa_user_id')
        
        if not code:
            return jsonify({'error': 'Verification code required'}), 400
        
        if not user_id:
            return jsonify({'error': 'No pending 2FA verification'}), 400
        
        user = User.query.get(user_id)
        if not user or not user.two_factor_enabled:
            return jsonify({'error': 'Invalid 2FA state'}), 400
        
        # Check if it's a TOTP code
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code, valid_window=1):
            # Complete login
            session['user_id'] = user.id
            session['user_email'] = user.email
            session.pop('pending_2fa_user_id', None)
            
            logger.info(f"2FA verification successful for user {user.email}")
            
            return jsonify({
                'message': '2FA verification successful',
                'redirect': '/dashboard'
            }), 200
        
        # Check if it's a backup code
        for hashed_code in (user.backup_codes or []):
            if check_password_hash(hashed_code, code):
                # Remove used backup code
                user.backup_codes.remove(hashed_code)
                db.session.commit()
                
                # Complete login
                session['user_id'] = user.id
                session['user_email'] = user.email
                session.pop('pending_2fa_user_id', None)
                
                logger.info(f"2FA backup code used for user {user.email}")
                
                return jsonify({
                    'message': '2FA verification successful (backup code used)',
                    'redirect': '/dashboard'
                }), 200
        
        return jsonify({'error': 'Invalid verification code'}), 400
        
    except Exception as e:
        logger.error(f"Error verifying 2FA: {e}")
        return jsonify({'error': 'Failed to verify 2FA'}), 500


@bp.route('/2fa/disable', methods=['POST'])
def disable_2fa():
    """Disable 2FA for user"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        import pyotp
        
        data = request.get_json() or {}
        password = data.get('password')
        code = data.get('code')
        
        if not password or not code:
            return jsonify({'error': 'Password and verification code required'}), 400
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify password
        if not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Invalid password'}), 401
        
        # Verify TOTP code
        if user.two_factor_enabled and user.totp_secret:
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(code, valid_window=1):
                return jsonify({'error': 'Invalid verification code'}), 400
        
        # Disable 2FA
        user.two_factor_enabled = False
        user.totp_secret = None
        user.backup_codes = None
        user.two_factor_verified_at = None
        db.session.commit()
        
        logger.info(f"2FA disabled for user {user.email}")
        
        return jsonify({'message': '2FA disabled successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error disabling 2FA: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to disable 2FA'}), 500
