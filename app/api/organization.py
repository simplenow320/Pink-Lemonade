"""Organization API endpoints for profile management and onboarding"""
from flask import Blueprint, request, jsonify, session
from app import db
from app.models import Organization, User
from app.services.ai_service import AIService
from app.api.auth import login_required, get_current_user
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
bp = Blueprint('organization', __name__)
ai_service = AIService()

@bp.route('/onboarding', methods=['POST'])
@login_required
def update_onboarding():
    """Update organization profile during onboarding"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        step = data.get('step', 1)
        
        # Get current user
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Get or create organization for current user
        org = Organization.query.filter_by(created_by_user_id=user.id).first()
        
        if not org:
            # Create new organization
            org = Organization()
            org.name = user.org_name or data.get('legal_name', '')
            org.created_by_user_id = user.id
            db.session.add(org)
        
        # Update based on step
        if step == 1:  # Basic Info
            org.legal_name = data.get('legal_name')
            org.ein = data.get('ein')
            org.org_type = data.get('org_type')
            org.year_founded = data.get('year_founded')
            org.website = data.get('website')
            org.mission = data.get('mission')
            org.vision = data.get('vision')
            org.values = data.get('values')
            org.faith_based = data.get('faith_based', False)
            org.minority_led = data.get('minority_led', False)
            org.woman_led = data.get('woman_led', False)
            org.veteran_led = data.get('veteran_led', False)
            
            # Parse social media
            social = data.get('social_media', '')
            if social:
                org.social_media = {'handle': social}
                
        elif step == 2:  # Programs & Services
            org.primary_focus_areas = data.get('primary_focus_areas', [])
            org.secondary_focus_areas = data.get('secondary_focus_areas', [])
            org.programs_services = data.get('programs_services')
            org.target_demographics = data.get('target_demographics', [])
            org.age_groups_served = data.get('age_groups_served', [])
            org.service_area_type = data.get('service_area_type')
            org.primary_city = data.get('primary_city')
            org.primary_state = data.get('primary_state')
            org.primary_zip = data.get('primary_zip')
            org.counties_served = data.get('counties_served', [])
            org.states_served = data.get('states_served', [])
            
        elif step == 3:  # Organizational Capacity
            org.annual_budget_range = data.get('annual_budget_range')
            org.staff_size = data.get('staff_size')
            org.volunteer_count = data.get('volunteer_count')
            org.board_size = data.get('board_size')
            org.people_served_annually = data.get('people_served_annually')
            org.key_achievements = data.get('key_achievements')
            
            # Parse impact metrics
            metrics = data.get('impact_metrics', {})
            if metrics:
                org.impact_metrics = metrics
                
        elif step == 4:  # Grant History
            org.previous_funders = data.get('previous_funders', [])
            org.typical_grant_size = data.get('typical_grant_size')
            org.grant_success_rate = data.get('grant_success_rate')
            org.preferred_grant_types = data.get('preferred_grant_types', [])
            org.grant_writing_capacity = data.get('grant_writing_capacity')
            
        elif step == 5:  # AI Learning
            org.keywords = data.get('keywords', [])
            org.unique_capabilities = data.get('unique_capabilities')
            org.partnership_interests = data.get('partnership_interests')
            org.funding_priorities = data.get('funding_priorities')
            org.exclusions = data.get('exclusions', [])
            
            # Mark onboarding complete
            org.onboarding_completed_at = datetime.utcnow()
        
        # Update profile completeness
        org.calculate_completeness()
        org.last_profile_update = datetime.utcnow()
        
        # Commit changes
        db.session.commit()
        
        # If AI data is updated, trigger AI learning
        if step in [1, 2, 5]:  # Steps with AI-relevant data
            try:
                # Get AI context for learning
                ai_context = org.to_ai_context()
                logger.info(f"AI learning from updated org profile: {org.name}")
                # The AI service will use this context for future matching
            except Exception as e:
                logger.error(f"AI learning error: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Step {step} completed successfully',
            'profile_completeness': org.profile_completeness,
            'org_id': org.id
        })
        
    except Exception as e:
        logger.error(f"Onboarding update error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current organization profile"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        org = Organization.query.filter_by(created_by_user_id=user.id).first()
        
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        return jsonify({
            'success': True,
            'organization': org.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error fetching profile: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update organization profile (from profile page)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        org = Organization.query.filter_by(created_by_user_id=user.id).first()
        
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Update all provided fields
        updateable_fields = [
            'legal_name', 'ein', 'org_type', 'year_founded', 'website',
            'mission', 'vision', 'values', 'primary_focus_areas',
            'secondary_focus_areas', 'programs_services', 'target_demographics',
            'age_groups_served', 'service_area_type', 'primary_city',
            'primary_state', 'primary_zip', 'annual_budget_range',
            'staff_size', 'volunteer_count', 'board_size', 'people_served_annually',
            'key_achievements', 'previous_funders', 'typical_grant_size',
            'grant_success_rate', 'preferred_grant_types', 'grant_writing_capacity',
            'faith_based', 'minority_led', 'woman_led', 'veteran_led',
            'keywords', 'unique_capabilities', 'partnership_interests',
            'funding_priorities', 'exclusions'
        ]
        
        for field in updateable_fields:
            if data and field in data:
                setattr(org, field, data[field])
        
        # Recalculate completeness
        org.calculate_completeness()
        org.last_profile_update = datetime.utcnow()
        
        db.session.commit()
        
        # Trigger AI learning with updated data
        try:
            ai_context = org.to_ai_context()
            logger.info(f"AI learning from profile update: {org.name}")
        except Exception as e:
            logger.error(f"AI learning error on profile update: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'organization': org.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/ai-context', methods=['GET'])
@login_required  
def get_ai_context():
    """Get organization's AI context for debugging/transparency"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        org = Organization.query.filter_by(created_by_user_id=user.id).first()
        
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        return jsonify({
            'success': True,
            'ai_context': org.to_ai_context(),
            'profile_completeness': org.profile_completeness
        })
        
    except Exception as e:
        logger.error(f"Error fetching AI context: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/check-onboarding', methods=['GET'])
@login_required
def check_onboarding_status():
    """Check if user needs to complete onboarding"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        org = Organization.query.filter_by(created_by_user_id=user.id).first()
        
        needs_onboarding = not org or not org.onboarding_completed_at
        current_step = 1
        
        if org:
            # Determine current step based on what's filled
            if org.mission and org.org_type:
                current_step = 2
            if org.primary_focus_areas:
                current_step = 3
            if org.annual_budget_range:
                current_step = 4
            if org.typical_grant_size:
                current_step = 5
            if org.onboarding_completed_at:
                current_step = 0  # Completed
        
        return jsonify({
            'needs_onboarding': needs_onboarding,
            'current_step': current_step,
            'profile_completeness': org.profile_completeness if org else 0
        })
        
    except Exception as e:
        logger.error(f"Error checking onboarding: {e}")
        return jsonify({'error': str(e)}), 500