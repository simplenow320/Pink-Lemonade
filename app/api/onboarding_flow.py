"""
Smart Onboarding Flow API
Handles the 3-step onboarding process with progress tracking
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from app import db
from app.models import User, Organization, UserProgress
from app.services.auth_manager import AuthManager
from datetime import datetime
import json

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/onboarding')

@onboarding_bp.route('/welcome')
@AuthManager.require_auth
def welcome():
    """Show the welcome screen with preparation checklist"""
    user = AuthManager.get_current_user()
    if not user:
        flash('Please log in to continue.', 'warning')
        return redirect('/login')
    org = Organization.query.filter_by(user_id=user.id).first()
    
    # If already onboarded, redirect to dashboard
    if org and org.profile_completeness >= 80:
        return redirect('/dashboard')
    
    return render_template('onboarding/welcome.html', user=user)

@onboarding_bp.route('/step1')
@AuthManager.require_auth
def step1():
    """Step 1: Basic organization information"""
    user = AuthManager.get_current_user()
    if not user:
        flash('Please log in to continue.', 'warning')
        return redirect('/login')
    org = Organization.query.filter_by(user_id=user.id).first()
    
    return render_template('onboarding/step1_basic.html', user=user, org=org)

@onboarding_bp.route('/step1/save', methods=['POST'])
@AuthManager.require_auth
def save_step1():
    """Save step 1 data and proceed or skip"""
    user = AuthManager.get_current_user()
    if not user:
        flash('Please log in to continue.', 'warning')
        return redirect('/login')
    org = Organization.query.filter_by(user_id=user.id).first()
    
    if not org:
        org = Organization()
        org.user_id = user.id
        org.created_by_user_id = user.id
        db.session.add(org)
    
    # Update basic info
    org.name = request.form.get('org_name', '')
    org.type = request.form.get('org_type', '')
    org.city = request.form.get('city', '')
    org.state = request.form.get('state', '')
    org.ein = request.form.get('ein', '')
    org.website = request.form.get('website', '')
    org.year_established = request.form.get('year_established')
    
    # Calculate profile completeness for step 1 (33%)
    org.profile_completeness = calculate_profile_completeness(org, step=1)
    
    # Update user progress
    update_user_progress(user.id, 'step1_complete', xp_earned=100)
    
    db.session.commit()
    
    if request.form.get('skip') == 'true':
        flash('Profile saved! You can complete it anytime from Settings.', 'info')
        return redirect('/dashboard')
    
    flash('Great start! Let\'s continue with your mission.', 'success')
    return redirect(url_for('onboarding.step2'))

@onboarding_bp.route('/step2')
@AuthManager.require_auth
def step2():
    """Step 2: Mission and Programs"""
    user = AuthManager.get_current_user()
    if not user:
        flash('Please log in to continue.', 'warning')
        return redirect('/login')
    org = Organization.query.filter_by(user_id=user.id).first()
    
    if not org:
        return redirect(url_for('onboarding.step1'))
    
    return render_template('onboarding/step2_mission.html', user=user, org=org)

@onboarding_bp.route('/step2/save', methods=['POST'])
@AuthManager.require_auth
def save_step2():
    """Save step 2 data"""
    user = AuthManager.get_current_user()
    if not user:
        flash('Please log in to continue.', 'warning')
        return redirect('/login')
    org = Organization.query.filter_by(user_id=user.id).first()
    
    if not org:
        return redirect(url_for('onboarding.step1'))
    
    # Update mission and programs
    org.mission_statement = request.form.get('mission_statement', '')
    org.focus_areas = request.form.getlist('focus_areas')
    org.target_population = request.form.get('target_population', '')
    org.geographic_scope = request.form.get('geographic_scope', '')
    org.key_programs = request.form.get('key_programs', '')
    
    # Store as JSON
    org.keywords = json.dumps(org.focus_areas) if org.focus_areas else '[]'
    
    # Calculate profile completeness for step 2 (66%)
    org.profile_completeness = calculate_profile_completeness(org, step=2)
    
    # Update user progress
    update_user_progress(user.id, 'step2_complete', xp_earned=150)
    
    db.session.commit()
    
    if request.form.get('skip') == 'true':
        flash('Profile saved! Complete the final step anytime.', 'info')
        return redirect('/dashboard')
    
    flash('Excellent! One more step to go.', 'success')
    return redirect(url_for('onboarding.step3'))

@onboarding_bp.route('/step3')
@AuthManager.require_auth
def step3():
    """Step 3: Capacity and History"""
    user = AuthManager.get_current_user()
    if not user:
        flash('Please log in to continue.', 'warning')
        return redirect('/login')
    org = Organization.query.filter_by(user_id=user.id).first()
    
    if not org:
        return redirect(url_for('onboarding.step1'))
    
    return render_template('onboarding/step3_capacity.html', user=user, org=org)

@onboarding_bp.route('/step3/save', methods=['POST'])
@AuthManager.require_auth
def save_step3():
    """Save step 3 data and complete onboarding"""
    user = AuthManager.get_current_user()
    if not user:
        flash('Please log in to continue.', 'warning')
        return redirect('/login')
    org = Organization.query.filter_by(user_id=user.id).first()
    
    if not org:
        return redirect(url_for('onboarding.step1'))
    
    # Update capacity info
    org.annual_budget = request.form.get('annual_budget', '')
    org.staff_count = request.form.get('staff_count', 0)
    org.board_members = request.form.get('board_members', 0)
    org.previous_grants = request.form.get('previous_grants', '')
    org.grant_experience = request.form.get('grant_experience', '')
    
    # Calculate final profile completeness (100%)
    org.profile_completeness = calculate_profile_completeness(org, step=3)
    
    # Mark onboarding complete
    session['onboarding_complete'] = True
    
    # Update user progress
    progress = update_user_progress(user.id, 'step3_complete', xp_earned=200)
    progress.onboarding_complete = True
    
    # Achievement for completing onboarding
    update_user_progress(user.id, 'onboarding_champion', xp_earned=500)
    
    db.session.commit()
    
    flash('🎉 Congratulations! Your profile is complete. Let\'s find your perfect grants!', 'success')
    return redirect('/dashboard/smart-discovery')

@onboarding_bp.route('/progress')
@AuthManager.require_auth
def get_progress():
    """Get current onboarding progress"""
    user = AuthManager.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    org = Organization.query.filter_by(user_id=user.id).first()
    progress = UserProgress.query.filter_by(user_id=user.id).first()
    
    return jsonify({
        'profile_completeness': org.profile_completeness if org else 0,
        'steps_completed': json.loads(progress.completed_steps) if progress and progress.completed_steps else [],
        'total_xp': progress.total_xp if progress else 0,
        'onboarding_complete': progress.onboarding_complete if progress else False
    })

def calculate_profile_completeness(org, step=None):
    """Calculate profile completeness percentage"""
    total_fields = 18  # Total number of important fields
    completed = 0
    
    # Step 1 fields (6 fields)
    if org.name: completed += 1
    if org.type: completed += 1
    if org.city: completed += 1
    if org.state: completed += 1
    if org.ein: completed += 0.5  # Optional but valuable
    if org.website: completed += 0.5  # Optional but valuable
    
    # Step 2 fields (6 fields)
    if step and step >= 2:
        if org.mission_statement: completed += 2  # Very important
        if org.keywords: completed += 1
        if org.target_population: completed += 1
        if org.geographic_scope: completed += 1
        if org.key_programs: completed += 1
    
    # Step 3 fields (6 fields)
    if step and step >= 3:
        if org.annual_budget: completed += 2  # Very important
        if org.staff_count: completed += 1
        if org.board_members: completed += 0.5
        if org.previous_grants: completed += 1
        if org.grant_experience: completed += 1.5
    
    return min(int((completed / total_fields) * 100), 100)

def update_user_progress(user_id, step_completed, xp_earned=0):
    """Update user progress and XP"""
    progress = UserProgress.query.filter_by(user_id=user_id).first()
    
    if not progress:
        progress = UserProgress()
        progress.user_id = user_id
        progress.completed_steps = '[]'
        progress.achievements = '[]'
        db.session.add(progress)
    
    # Update completed steps
    completed_steps = json.loads(progress.completed_steps) if progress.completed_steps else []
    if step_completed not in completed_steps:
        completed_steps.append(step_completed)
        progress.completed_steps = json.dumps(completed_steps)
    
    # Add XP
    progress.total_xp = (progress.total_xp or 0) + xp_earned
    
    # Calculate level (every 500 XP = 1 level)
    progress.current_level = 1 + (progress.total_xp // 500)
    
    progress.updated_at = datetime.utcnow()
    
    db.session.commit()
    return progress

@onboarding_bp.route('/skip-all')
@AuthManager.require_auth
def skip_all():
    """Skip entire onboarding (not recommended)"""
    session['onboarding_complete'] = True
    flash('You can complete your profile anytime from Settings to get better grant matches.', 'info')
    return redirect(url_for('dashboard.index'))