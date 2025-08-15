"""
PHASE 0: Smart Onboarding API Endpoints
"""
from flask import Blueprint, request, jsonify, session
from app.services.phase0_onboarding_service import phase0_service
# Import will be added when matching service is ready
# from app.services.matching_service import get_opportunities_for_profile
from app.models import db, Organization
import logging

logger = logging.getLogger(__name__)

phase0_bp = Blueprint('phase0_onboarding', __name__)

@phase0_bp.route('/api/phase0/onboarding/questions/<step>', methods=['GET'])
def get_onboarding_questions(step):
    """Get onboarding questions for a specific step"""
    try:
        questions = phase0_service.get_onboarding_questions(step)
        return jsonify({
            'success': True,
            'questions': questions
        })
    except Exception as e:
        logger.error(f"Error getting onboarding questions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase0_bp.route('/api/phase0/organization/profile', methods=['POST'])
def create_or_update_profile():
    """Create or update organization profile with custom fields"""
    try:
        user_id = session.get('user_id', 1)  # Default for testing
        profile_data = request.json
        
        result = phase0_service.create_organization_profile(user_id, profile_data)
        
        if result['success'] and result.get('ready_for_matching'):
            # Trigger immediate matching if profile is complete enough
            org_id = result['organization']['id']
            _trigger_initial_matching(org_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase0_bp.route('/api/phase0/organization/profile', methods=['GET'])
def get_organization_profile():
    """Get current organization profile"""
    try:
        user_id = session.get('user_id', 1)
        org = Organization.query.filter_by(created_by_user_id=user_id).first()
        
        if org:
            return jsonify({
                'success': True,
                'organization': org.to_dict(),
                'completeness': org.profile_completeness
            })
        else:
            return jsonify({
                'success': True,
                'organization': None,
                'completeness': 0
            })
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase0_bp.route('/api/phase0/loved-grants', methods=['POST'])
def save_loved_grant():
    """Save a grant to loved/favorites"""
    try:
        user_id = session.get('user_id', 1)
        grant_data = request.json
        
        result = phase0_service.save_loved_grant(user_id, grant_data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error saving loved grant: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase0_bp.route('/api/phase0/loved-grants', methods=['GET'])
def get_loved_grants():
    """Get user's loved grants"""
    try:
        user_id = session.get('user_id', 1)
        loved_grants = phase0_service.get_loved_grants(user_id)
        
        return jsonify({
            'success': True,
            'loved_grants': loved_grants,
            'count': len(loved_grants)
        })
    except Exception as e:
        logger.error(f"Error getting loved grants: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase0_bp.route('/api/phase0/loved-grants/<int:grant_id>/status', methods=['PATCH'])
def update_loved_grant_status(grant_id):
    """Update status of a loved grant"""
    try:
        from app.models import LovedGrant
        
        user_id = session.get('user_id', 1)
        data = request.json
        
        loved = LovedGrant.query.filter_by(
            id=grant_id,
            user_id=user_id
        ).first()
        
        if not loved:
            return jsonify({'success': False, 'error': 'Grant not found'}), 404
        
        # Update fields
        if 'status' in data:
            loved.status = data['status']
        if 'notes' in data:
            loved.notes = data['notes']
        if 'progress_percentage' in data:
            loved.progress_percentage = data['progress_percentage']
        if 'reminder_date' in data:
            from datetime import datetime
            loved.reminder_date = datetime.fromisoformat(data['reminder_date'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'loved_grant': loved.to_dict()
        })
    except Exception as e:
        logger.error(f"Error updating loved grant: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@phase0_bp.route('/api/phase0/initial-matches', methods=['GET'])
def get_initial_matches():
    """Get initial grant matches based on profile"""
    try:
        user_id = session.get('user_id', 1)
        org = Organization.query.filter_by(created_by_user_id=user_id).first()
        
        if not org:
            return jsonify({
                'success': False,
                'error': 'Please complete your organization profile first'
            }), 400
        
        # Get matches using all our APIs
        from app.api.opportunities import get_opportunities_internal
        matches = get_opportunities_internal(
            org_id=org.id,
            search=org.mission or '',
            city=org.primary_city,
            focus_area=org.primary_focus_areas[0] if org.primary_focus_areas else None
        )
        
        return jsonify({
            'success': True,
            'matches': matches[:10],  # Top 10 matches
            'total_found': len(matches)
        })
    except Exception as e:
        logger.error(f"Error getting initial matches: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def _trigger_initial_matching(org_id: int):
    """Trigger initial matching after profile completion"""
    try:
        org = Organization.query.get(org_id)
        if org and org.profile_completeness >= 70:
            # Run matching in background (or queue)
            logger.info(f"Triggered initial matching for org {org_id}")
            # Matching will be done when user requests initial matches
    except Exception as e:
        logger.error(f"Error triggering initial matching: {e}")

# Helper function to get dropdown options
@phase0_bp.route('/api/phase0/dropdown-options/<category>', methods=['GET'])
def get_dropdown_options(category):
    """Get dropdown options for a category"""
    try:
        options = phase0_service.ONBOARDING_OPTIONS.get(category, [])
        return jsonify({
            'success': True,
            'category': category,
            'options': options
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500