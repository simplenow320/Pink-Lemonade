"""
User Profile API endpoints
"""

from flask import Blueprint, request, jsonify, session
from app import db
from app.models import User, UserProgress, Organization
from app.api.auth import login_required, get_current_user
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('profile', __name__, url_prefix='/api/profile')

@bp.route('/get', methods=['GET'])
@login_required
def get_profile():
    """Get current user's profile"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user progress
        progress = UserProgress.query.filter_by(user_id=user.id).first()
        
        # Get organization if user has one
        organization = None
        if user.org_id:
            organization = Organization.query.filter_by(id=user.org_id).first()
        
        profile_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'phone': user.phone or '',
            'job_title': user.job_title or '',
            'org_name': user.org_name or '',
            'role': user.role or 'member',
            'timezone': user.timezone or 'America/New_York',
            'notification_preferences': user.notification_preferences or {
                'email_notifications': True,
                'grant_alerts': True,
                'weekly_digest': True,
                'deadline_reminders': True
            },
            'is_verified': user.is_verified,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
        
        # Add progress info if exists
        if progress:
            profile_data['progress'] = {
                'total_xp': progress.total_xp,
                'current_level': progress.current_level,
                'streak_days': progress.streak_days,
                'onboarding_complete': progress.onboarding_complete
            }
        
        # Add organization info if exists
        if organization:
            profile_data['organization'] = {
                'id': organization.id,
                'name': organization.name,
                'mission': organization.mission,
                'primary_focus_areas': organization.primary_focus_areas
            }
        
        return jsonify({'profile': profile_data}), 200
        
    except Exception as e:
        logger.error(f"Error fetching profile: {e}")
        return jsonify({'error': 'Failed to fetch profile'}), 500


@bp.route('/update', methods=['POST'])
@login_required
def update_profile():
    """Update current user's profile"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = [
            'first_name', 'last_name', 'phone', 'job_title', 
            'org_name', 'timezone', 'notification_preferences'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Update email only if changed and valid
        if 'email' in data and data['email'] != user.email:
            # Check if email already exists
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user.id:
                return jsonify({'error': 'Email already in use'}), 400
            user.email = data['email']
            user.is_verified = False  # Require re-verification on email change
        
        db.session.commit()
        
        # Return updated profile
        profile_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'job_title': user.job_title,
            'org_name': user.org_name,
            'timezone': user.timezone,
            'notification_preferences': user.notification_preferences
        }
        
        return jsonify({
            'message': 'Profile updated successfully',
            'profile': profile_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500


@bp.route('/onboarding/status', methods=['GET'])
@login_required
def get_onboarding_status():
    """Get user's onboarding status"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get or create user progress
        progress = UserProgress.query.filter_by(user_id=user.id).first()
        if not progress:
            progress = UserProgress()
            progress.user_id = user.id
            progress.total_xp = 0
            progress.current_level = 1
            progress.streak_days = 0
            progress.onboarding_complete = False
            db.session.add(progress)
            db.session.commit()
        
        # Check what's completed
        completed_steps = []
        if user.first_name and user.last_name:
            completed_steps.append('personal_info')
        if user.email and user.is_verified:
            completed_steps.append('email_verified')
        if user.job_title and user.org_name:
            completed_steps.append('work_info')
        if user.org_id:
            completed_steps.append('organization_setup')
        
        # Calculate completion percentage
        total_steps = 4
        completion_percentage = (len(completed_steps) / total_steps) * 100
        
        return jsonify({
            'onboarding_complete': progress.onboarding_complete,
            'completed_steps': completed_steps,
            'completion_percentage': completion_percentage,
            'current_xp': progress.total_xp,
            'current_level': progress.current_level
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching onboarding status: {e}")
        return jsonify({'error': 'Failed to fetch onboarding status'}), 500


@bp.route('/lookup-ein', methods=['POST'])
def lookup_ein():
    """Look up organization by EIN using Candid Essentials API"""
    try:
        data = request.get_json()
        ein = data.get('ein', '').strip()
        
        if not ein:
            return jsonify({'error': 'EIN is required'}), 400
        
        # Import Essentials client
        try:
            from app.services.candid_client import get_essentials_client
            essentials = get_essentials_client()
            
            if not essentials:
                return jsonify({
                    'error': 'EIN lookup service not configured',
                    'message': 'Essentials API is not available'
                }), 503
            
            # Search organization by EIN
            org_data = essentials.search_org(ein)
            
            if not org_data:
                return jsonify({
                    'error': 'Organization not found',
                    'message': 'No organization found for the provided EIN'
                }), 404
            
            # Extract tokens for matching
            tokens = essentials.extract_tokens(org_data)
            
            # Return organization data for profile population
            profile_data = {
                'organization_name': org_data.get('organization_name', ''),
                'ein': org_data.get('ein', ein),
                'city': org_data.get('city', ''),
                'state': org_data.get('state', ''),
                'mission': org_data.get('mission_statement', ''),
                'website': org_data.get('website', ''),
                'pcs_subject_codes': tokens.get('pcs_subject_codes', []),
                'pcs_population_codes': tokens.get('pcs_population_codes', []),
                'locations': tokens.get('locations', []),
                'keywords': tokens.get('keywords', []),
                'annual_revenue': org_data.get('annual_revenue'),
                'total_assets': org_data.get('total_assets'),
                'ntee_code': org_data.get('ntee_code', ''),
                'classification': org_data.get('classification', '')
            }
            
            return jsonify({
                'success': True,
                'message': 'Organization found successfully',
                'data': profile_data
            }), 200
            
        except ImportError:
            return jsonify({
                'error': 'EIN lookup service not available',
                'message': 'Essentials service is not configured'
            }), 503
            
    except Exception as e:
        logger.error(f"Error in EIN lookup: {type(e).__name__}")
        return jsonify({
            'error': 'EIN lookup failed',
            'message': 'Unable to complete organization lookup'
        }), 500


@bp.route('/onboarding/complete', methods=['POST'])
@login_required
def complete_onboarding():
    """Mark onboarding as complete"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        progress = UserProgress.query.filter_by(user_id=user.id).first()
        if not progress:
            progress = UserProgress()
            progress.user_id = user.id
            progress.total_xp = 500  # Bonus XP for completing onboarding
            progress.current_level = 2
            progress.onboarding_complete = True
            db.session.add(progress)
        else:
            progress.onboarding_complete = True
            progress.total_xp += 500  # Bonus XP
            if progress.total_xp >= 500:
                progress.current_level = 2
        
        db.session.commit()
        
        return jsonify({
            'message': 'Onboarding completed!',
            'bonus_xp': 500,
            'new_level': progress.current_level
        }), 200
        
    except Exception as e:
        logger.error(f"Error completing onboarding: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to complete onboarding'}), 500