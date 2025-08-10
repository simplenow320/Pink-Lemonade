"""Authentication Service for Pink Lemonade Platform"""
import os
import secrets
import hashlib
import json
import base64
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from app import db
from app.models import User
from app.services.email_service import EmailService

class AuthService:
    def __init__(self):
        self.email_service = EmailService()
        
    def register_user(self, email, password, org_name, first_name, last_name, job_title=None):
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return {'success': False, 'error': 'Email already registered'}
            
            # Create new user
            user = User(
                email=email,
                password_hash=generate_password_hash(password),
                org_name=org_name,
                first_name=first_name,
                last_name=last_name,
                job_title=job_title,
                is_verified=False,
                created_at=datetime.utcnow()
            )
            
            # Generate verification token
            verification_token = self.generate_verification_token()
            user.verification_token = verification_token
            user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
            
            # Save user to database
            db.session.add(user)
            db.session.commit()
            
            # Send verification email
            self.email_service.send_verification_email(
                email, 
                first_name,
                verification_token
            )
            
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'org_name': user.org_name
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def login_user(self, email, password, remember=False):
        """Authenticate user and generate JWT token"""
        try:
            # Find user by email
            user = User.query.filter_by(email=email).first()
            
            if not user:
                return {'success': False, 'error': 'Invalid email or password'}
            
            # Check password
            if not check_password_hash(user.password_hash, password):
                return {'success': False, 'error': 'Invalid email or password'}
            
            # Check if email is verified
            if not user.is_verified:
                return {'success': False, 'error': 'Please verify your email before logging in'}
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Generate JWT token
            token_expiry = timedelta(days=30) if remember else timedelta(days=7)
            token = self.generate_jwt_token(user.id, token_expiry)
            
            return {
                'success': True,
                'token': token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'org_name': user.org_name,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def request_password_reset(self, email):
        """Generate password reset token and send email"""
        try:
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Don't reveal if email exists or not
                return {'success': True, 'message': 'If the email exists, reset instructions have been sent'}
            
            # Generate reset token
            reset_token = self.generate_reset_token()
            user.reset_token = reset_token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            
            db.session.commit()
            
            # Send reset email
            self.email_service.send_password_reset_email(
                email,
                user.first_name,
                reset_token
            )
            
            return {'success': True, 'message': 'Reset instructions sent to your email'}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def reset_password(self, token, new_password):
        """Reset user password with valid token"""
        try:
            user = User.query.filter_by(reset_token=token).first()
            
            if not user:
                return {'success': False, 'error': 'Invalid or expired reset token'}
            
            # Check if token is expired
            if user.reset_token_expires < datetime.utcnow():
                return {'success': False, 'error': 'Reset token has expired'}
            
            # Update password
            user.password_hash = generate_password_hash(new_password)
            user.reset_token = None
            user.reset_token_expires = None
            
            db.session.commit()
            
            return {'success': True, 'message': 'Password reset successfully'}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def verify_email(self, token):
        """Verify user email with token"""
        try:
            user = User.query.filter_by(verification_token=token).first()
            
            if not user:
                return {'success': False, 'error': 'Invalid verification token'}
            
            # Check if token is expired
            if user.verification_token_expires < datetime.utcnow():
                return {'success': False, 'error': 'Verification token has expired'}
            
            # Mark email as verified
            user.is_verified = True
            user.verification_token = None
            user.verification_token_expires = None
            user.verified_at = datetime.utcnow()
            
            db.session.commit()
            
            return {'success': True, 'message': 'Email verified successfully'}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def resend_verification(self, email):
        """Resend verification email"""
        try:
            user = User.query.filter_by(email=email).first()
            
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            if user.is_verified:
                return {'success': False, 'error': 'Email already verified'}
            
            # Generate new verification token
            verification_token = self.generate_verification_token()
            user.verification_token = verification_token
            user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
            
            db.session.commit()
            
            # Send verification email
            self.email_service.send_verification_email(
                email,
                user.first_name,
                verification_token
            )
            
            return {'success': True, 'message': 'Verification email sent'}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def generate_jwt_token(self, user_id, expiry_delta):
        """Generate a simple signed token for user"""
        secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key')
        
        # Create token data
        token_data = {
            'user_id': user_id,
            'exp': (datetime.utcnow() + expiry_delta).isoformat(),
            'iat': datetime.utcnow().isoformat()
        }
        
        # Encode token data
        token_json = json.dumps(token_data)
        token_bytes = token_json.encode('utf-8')
        token_b64 = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
        
        # Create signature
        signature = hashlib.sha256((token_b64 + secret_key).encode()).hexdigest()
        
        # Combine token and signature
        return f"{token_b64}.{signature}"
    
    def verify_jwt_token(self, token):
        """Verify and decode simple signed token"""
        try:
            secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key')
            
            # Split token and signature
            parts = token.split('.')
            if len(parts) != 2:
                return {'success': False, 'error': 'Invalid token format'}
            
            token_b64, signature = parts
            
            # Verify signature
            expected_signature = hashlib.sha256((token_b64 + secret_key).encode()).hexdigest()
            if signature != expected_signature:
                return {'success': False, 'error': 'Invalid token signature'}
            
            # Decode token
            token_bytes = base64.urlsafe_b64decode(token_b64.encode('utf-8'))
            token_json = token_bytes.decode('utf-8')
            token_data = json.loads(token_json)
            
            # Check expiration
            exp_time = datetime.fromisoformat(token_data['exp'])
            if exp_time < datetime.utcnow():
                return {'success': False, 'error': 'Token has expired'}
            
            return {'success': True, 'user_id': token_data['user_id']}
            
        except Exception as e:
            return {'success': False, 'error': 'Invalid token'}
    
    def generate_verification_token(self):
        """Generate a random verification token"""
        return secrets.token_urlsafe(32)
    
    def generate_reset_token(self):
        """Generate a random password reset token"""
        return secrets.token_urlsafe(32)
    
    def get_current_user(self, token):
        """Get current user from JWT token"""
        token_result = self.verify_jwt_token(token)
        if not token_result['success']:
            return None
        
        user = User.query.get(token_result['user_id'])
        return user