"""
Security Service for Production Hardening
Implements rate limiting, input validation, and security headers
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from functools import wraps
from flask import request, jsonify, g
import hashlib
import hmac
import secrets
import re
import logging

logger = logging.getLogger(__name__)

class SecurityService:
    """Security utilities and middleware"""
    
    # Rate limiting storage (in production, use Redis)
    _rate_limits: Dict[str, list] = {}
    
    # Input validation patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^[\d\s\-\+\(\)]+$')
    URL_PATTERN = re.compile(r'^https?://[^\s<>]+$')
    SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_\.,!?\'"]+$')
    
    @classmethod
    def rate_limit(cls, max_requests: int = 60, window_seconds: int = 60):
        """Rate limiting decorator"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get client identifier (IP address or user ID)
                client_id = request.remote_addr
                if hasattr(g, 'user_id'):
                    client_id = f"user_{g.user_id}"
                
                key = f"{func.__name__}:{client_id}"
                now = datetime.now()
                window_start = now - timedelta(seconds=window_seconds)
                
                # Clean old entries and count recent requests
                if key not in cls._rate_limits:
                    cls._rate_limits[key] = []
                
                cls._rate_limits[key] = [
                    timestamp for timestamp in cls._rate_limits[key]
                    if timestamp > window_start
                ]
                
                if len(cls._rate_limits[key]) >= max_requests:
                    logger.warning(f"Rate limit exceeded for {key}")
                    return jsonify({
                        'success': False,
                        'error': 'Rate limit exceeded. Please try again later.'
                    }), 429
                
                cls._rate_limits[key].append(now)
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format"""
        if not email or len(email) > 255:
            return False
        return bool(cls.EMAIL_PATTERN.match(email))
    
    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """Validate phone number format"""
        if not phone or len(phone) > 20:
            return False
        return bool(cls.PHONE_PATTERN.match(phone))
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Validate URL format"""
        if not url or len(url) > 2048:
            return False
        return bool(cls.URL_PATTERN.match(url))
    
    @classmethod
    def sanitize_input(cls, text: str, max_length: int = 1000) -> str:
        """Sanitize text input to prevent XSS"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove potentially dangerous characters
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        text = text.replace('"', '&quot;').replace("'", '&#39;')
        
        # Truncate to max length
        return text[:max_length]
    
    @classmethod
    def generate_csrf_token(cls) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def verify_csrf_token(cls, token: str, session_token: str) -> bool:
        """Verify CSRF token"""
        if not token or not session_token:
            return False
        return hmac.compare_digest(token, session_token)
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash password with salt (use werkzeug in production)"""
        from werkzeug.security import generate_password_hash
        return generate_password_hash(password)
    
    @classmethod
    def verify_password(cls, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        from werkzeug.security import check_password_hash
        return check_password_hash(password_hash, password)
    
    @classmethod
    def add_security_headers(cls, response):
        """Add security headers to response"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; connect-src 'self';"
        return response
    
    @classmethod
    def validate_api_key(cls, api_key: str) -> bool:
        """Validate API key format"""
        if not api_key:
            return False
        
        # Check length and format
        if len(api_key) < 32 or len(api_key) > 128:
            return False
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9\-_]+$', api_key):
            return False
        
        return True
    
    @classmethod
    def check_sql_injection(cls, text: str) -> bool:
        """Basic SQL injection detection"""
        if not text:
            return True
        
        # Common SQL injection patterns
        dangerous_patterns = [
            r'\bUNION\b.*\bSELECT\b',
            r'\bDROP\b.*\bTABLE\b',
            r'\bINSERT\b.*\bINTO\b',
            r'\bDELETE\b.*\bFROM\b',
            r'--\s*$',
            r';\s*--',
            r'\bOR\b.*=.*',
            r'\bAND\b.*=.*',
            r"'\s*OR\s*'",
            r'"\s*OR\s*"'
        ]
        
        text_upper = text.upper()
        for pattern in dangerous_patterns:
            if re.search(pattern, text_upper):
                logger.warning(f"Potential SQL injection detected: {text[:100]}")
                return False
        
        return True

class InputValidator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_grant_data(data: dict) -> tuple[bool, str]:
        """Validate grant submission data"""
        errors = []
        
        # Required fields
        if not data.get('title'):
            errors.append('Title is required')
        elif len(data['title']) > 500:
            errors.append('Title must be less than 500 characters')
        
        if not data.get('funder'):
            errors.append('Funder is required')
        elif len(data['funder']) > 255:
            errors.append('Funder must be less than 255 characters')
        
        # Optional fields validation
        if data.get('amount_min'):
            try:
                amount = float(data['amount_min'])
                if amount < 0:
                    errors.append('Minimum amount must be positive')
            except (ValueError, TypeError):
                errors.append('Invalid minimum amount')
        
        if data.get('amount_max'):
            try:
                amount = float(data['amount_max'])
                if amount < 0:
                    errors.append('Maximum amount must be positive')
            except (ValueError, TypeError):
                errors.append('Invalid maximum amount')
        
        if data.get('link'):
            if not SecurityService.validate_url(data['link']):
                errors.append('Invalid grant link URL')
        
        if data.get('deadline'):
            try:
                # Validate date format
                from datetime import datetime
                datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                errors.append('Invalid deadline format')
        
        if errors:
            return False, '; '.join(errors)
        return True, ''
    
    @staticmethod
    def validate_search_params(params: dict) -> tuple[bool, str]:
        """Validate search parameters"""
        errors = []
        
        # Validate query
        if params.get('query'):
            if len(params['query']) > 200:
                errors.append('Search query too long')
            if not SecurityService.check_sql_injection(params['query']):
                errors.append('Invalid search query')
        
        # Validate pagination
        if params.get('page'):
            try:
                page = int(params['page'])
                if page < 1 or page > 1000:
                    errors.append('Invalid page number')
            except (ValueError, TypeError):
                errors.append('Page must be a number')
        
        if params.get('per_page'):
            try:
                per_page = int(params['per_page'])
                if per_page < 1 or per_page > 100:
                    errors.append('Items per page must be between 1 and 100')
            except (ValueError, TypeError):
                errors.append('Items per page must be a number')
        
        if errors:
            return False, '; '.join(errors)
        return True, ''

# Singleton instance
security = SecurityService()
validator = InputValidator()