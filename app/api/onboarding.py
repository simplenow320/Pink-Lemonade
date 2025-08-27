"""
Onboarding API endpoints for gamified journey
"""
import re
from flask import Blueprint, request, jsonify, session
from app.services.onboarding_service import onboarding_service
from app import db
from app.models import Organization
from app.services.candid_essentials import search_by_ein, search_by_name, extract_tokens
import logging

logger = logging.getLogger(__name__)

onboarding_bp = Blueprint('onboarding', __name__)

def is_ein(query: str) -> bool:
    """Check if query looks like an EIN (digits and optional hyphen)"""
    # EIN format: XX-XXXXXXX or XXXXXXXXX
    ein_pattern = r'^[0-9]{2}-?[0-9]{7}$'
    return re.match(ein_pattern, query.replace(' ', '')) is not None

@onboarding_bp.route('/api/onboarding/progress', methods=['GET'])
def get_progress():
    """Get user's onboarding progress and character info"""
    try:
        # Get user ID from session or default to 1 for testing
        user_id = session.get('user_id', 1)
        
        progress = onboarding_service.get_user_progress(user_id)
        
        return jsonify({
            'success': True,
            'progress': progress
        })
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@onboarding_bp.route('/api/onboarding/steps', methods=['GET'])
def get_steps():
    """Get onboarding steps with completion status"""
    try:
        user_id = session.get('user_id', 1)
        
        steps = onboarding_service.get_onboarding_steps(user_id)
        
        return jsonify({
            'success': True,
            'steps': steps
        })
    except Exception as e:
        logger.error(f"Error getting steps: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@onboarding_bp.route('/api/onboarding/complete-task', methods=['POST'])
def complete_task():
    """Mark a task as complete and award XP"""
    try:
        data = request.json
        user_id = session.get('user_id', 1)
        step_id = data.get('step_id')
        task_id = data.get('task_id')
        
        if not step_id or not task_id:
            return jsonify({'success': False, 'error': 'Missing step_id or task_id'}), 400
        
        result = onboarding_service.complete_task(user_id, step_id, task_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@onboarding_bp.route('/api/onboarding/award-achievement', methods=['POST'])
def award_achievement():
    """Award an achievement to user"""
    try:
        data = request.json
        user_id = session.get('user_id', 1)
        achievement_id = data.get('achievement_id')
        
        if not achievement_id:
            return jsonify({'success': False, 'error': 'Missing achievement_id'}), 400
        
        result = onboarding_service.award_achievement(user_id, achievement_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error awarding achievement: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@onboarding_bp.route('/api/onboarding/update-streak', methods=['POST'])
def update_streak():
    """Update login streak"""
    try:
        user_id = session.get('user_id', 1)
        
        result = onboarding_service.update_login_streak(user_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error updating streak: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@onboarding_bp.route('/api/onboarding/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get top users by XP"""
    try:
        from app.models import UserProgress, User
        
        # Get top 10 users by XP
        top_users = db.session.query(
            UserProgress, User
        ).join(
            User, UserProgress.user_id == User.id
        ).order_by(
            UserProgress.total_xp.desc()
        ).limit(10).all()
        
        leaderboard = []
        for progress, user in top_users:
            level = onboarding_service.calculate_level(progress.total_xp)
            leaderboard.append({
                'username': user.username,
                'total_xp': progress.total_xp,
                'level': level['level'],
                'title': level['title'],
                'icon': level['icon']
            })
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard
        })
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@onboarding_bp.route('/api/onboarding/essentials/lookup', methods=['GET'])
def lookup_organization():
    """
    Look up organization by EIN or name via Candid Essentials
    
    Query params:
        query: EIN or organization name to search
        
    Returns:
        200: { "record": <raw>, "tokens": extract_tokens(record) }
        404: { "error": "not_found" }
    """
    query = request.args.get('query', '').strip()
    
    if not query:
        return jsonify({"error": "Query parameter required"}), 400
    
    # Determine if it's an EIN or name search
    record = None
    if is_ein(query):
        # Search by EIN
        record = search_by_ein(query)
    else:
        # Search by name
        record = search_by_name(query)
    
    if record:
        # Extract useful tokens from the record
        tokens = extract_tokens(record)
        
        return jsonify({
            "record": record,
            "tokens": tokens
        }), 200
    else:
        return jsonify({"error": "not_found"}), 404

@onboarding_bp.route('/api/onboarding/essentials/apply', methods=['POST'])
def apply_organization_data():
    """
    Apply selected fields from Candid record to organization profile
    
    Body:
        {
            "org_id": <id>,
            "record": <raw record>,
            "apply": {
                "org_name": true/false,
                "ein": true/false,
                "website": true/false,
                "mission": true/false,
                "programs": true/false,
                "pcs_subject_codes": true/false,
                "pcs_population_codes": true/false,
                "service_locations": true/false
            }
        }
        
    Returns:
        200: { "saved": true, "appliedFields": [...] }
        400: Error message
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        org_id = data.get('org_id')
        record = data.get('record', {})
        apply = data.get('apply', {})
        
        if not org_id:
            return jsonify({"error": "org_id required"}), 400
        
        # Get or create organization
        org = Organization.query.get(org_id)
        if not org:
            # Create new org if doesn't exist
            org = Organization(id=org_id, name="New Organization")
            db.session.add(org)
        
        applied_fields = []
        
        # Extract tokens from the record
        tokens = extract_tokens(record)
        
        # Map and apply fields based on 'apply' settings
        field_mapping = {
            'org_name': ('name', lambda: record.get('name') or record.get('legal_name')),
            'ein': ('ein', lambda: record.get('ein')),
            'website': ('website', lambda: tokens.get('website')),
            'mission': ('mission', lambda: tokens.get('mission')),
            'programs': ('programs', lambda: record.get('programs') or record.get('program_description')),
            'pcs_subject_codes': ('pcs_subject_codes', lambda: tokens.get('pcs_subject_codes')),
            'pcs_population_codes': ('pcs_population_codes', lambda: tokens.get('pcs_population_codes')),
            'service_locations': ('service_locations', lambda: tokens.get('locations'))
        }
        
        # Apply selected fields
        for field_key, (db_field, getter) in field_mapping.items():
            if apply.get(field_key, False):
                value = getter()
                if value is not None:
                    # Only update if value exists and field was requested
                    setattr(org, db_field, value)
                    applied_fields.append(field_key)
        
        # Commit changes
        db.session.commit()
        
        return jsonify({
            "saved": True,
            "appliedFields": applied_fields
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500