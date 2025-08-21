"""
Authentication Routes - Login, Register, Logout
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app import db
from app.models import User, Organization
from app.services.auth_manager import AuthManager
from werkzeug.security import generate_password_hash, check_password_hash
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'GET':
        return render_template('auth/login_standalone.html')
    
    email = request.form.get('email', '').lower().strip()
    password = request.form.get('password', '')
    
    # Validate input
    if not email or not password:
        flash('Please enter both email and password.', 'error')
        return render_template('auth/login_standalone.html')
    
    # Find user
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        flash('Invalid email or password. Please try again.', 'error')
        return render_template('auth/login_standalone.html')
    
    # Log user in
    AuthManager.login_user(user)
    
    # Check if user needs onboarding
    org = Organization.query.filter_by(user_id=user.id).first()
    if not org or org.profile_completeness < 80:
        flash('Welcome back! Let\'s complete your profile to find perfect grants.', 'info')
        return redirect(url_for('onboarding.welcome'))
    
    flash(f'Welcome back, {user.first_name or user.email}!', 'success')
    next_page = request.args.get('next')
    return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if request.method == 'GET':
        return render_template('auth/register_standalone.html')
    
    # Get form data
    email = request.form.get('email', '').lower().strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    org_name = request.form.get('org_name', '').strip()
    
    # Validate input
    errors = []
    
    if not email or not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        errors.append('Please enter a valid email address.')
    
    if User.query.filter_by(email=email).first():
        errors.append('An account with this email already exists.')
    
    if not password or len(password) < 8:
        errors.append('Password must be at least 8 characters long.')
    
    if password != confirm_password:
        errors.append('Passwords do not match.')
    
    if not first_name:
        errors.append('Please enter your first name.')
    
    if errors:
        for error in errors:
            flash(error, 'error')
        return render_template('auth/register_standalone.html', 
                             email=email, 
                             first_name=first_name,
                             last_name=last_name,
                             org_name=org_name)
    
    # Create new user
    user = User()
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    user.org_name = org_name
    user.set_password(password)
    user.is_active = True
    user.is_verified = False  # Will add email verification later
    
    db.session.add(user)
    db.session.commit()
    
    # Log user in automatically
    AuthManager.login_user(user)
    
    flash('🎉 Welcome to Pink Lemonade! Let\'s set up your organization profile.', 'success')
    return redirect(url_for('onboarding.welcome'))

@auth_bp.route('/logout')
def logout():
    """Log user out"""
    AuthManager.logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))