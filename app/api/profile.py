"""
User Profile API endpoints
Handles user profile management and organization settings
"""

from flask import Blueprint, request, jsonify, session
from app import db
from app.models import User, Organization
from app.api.auth import login_required, get_current_user
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('profile', __name__, url_prefix='/api/profile')

@bp.route('/user', methods=['GET'])
@login_required
def get_user_profile():
    """Get current user's profile"""
    try:
        user = get_current_user()
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/user', methods=['PUT'])
@login_required
def update_user_profile():
    """Update current user's profile"""
    try:
        user = get_current_user()
        data = request.get_json()
        
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
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        })
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/organization', methods=['GET'])
@login_required  
def get_organization():
    """Get user's organization profile"""
    try:
        user = get_current_user()
        # Get user's organization by matching org_id string/int
        if user.org_id:
            org = Organization.query.filter_by(id=user.org_id).first()
            if not org:
                # Try by string match if org_id is a string
                org = Organization.query.filter(Organization.name.ilike(f'%{user.org_id}%')).first()
        else:
            org = Organization.query.first()
        
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
            
        return jsonify({
            'success': True,
            'organization': org.to_dict()
        })
    except Exception as e:
        logger.error(f"Error getting organization: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/organization', methods=['PUT'])
@login_required
def update_organization():
    """Update organization profile"""
    try:
        user = get_current_user()
        if user.role not in ['admin', 'manager']:
            return jsonify({'error': 'Insufficient permissions'}), 403
            
        # Get user's organization by matching org_id string/int
        if user.org_id:
            org = Organization.query.filter_by(id=user.org_id).first()
            if not org:
                # Try by string match if org_id is a string
                org = Organization.query.filter(Organization.name.ilike(f'%{user.org_id}%')).first()
        else:
            org = Organization.query.first()
            
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
            
        data = request.get_json()
        
        # Update organization fields
        if 'name' in data:
            org.name = data['name'].strip()
        if 'description' in data:
            org.description = data['description'].strip()
        if 'website' in data:
            org.website = data['website'].strip()
        if 'focus_areas' in data:
            org.focus_areas = data['focus_areas']
        if 'keywords' in data:
            org.keywords = data['keywords']
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Organization updated successfully',
            'organization': org.to_dict()
        })
    except Exception as e:
        logger.error(f"Error updating organization: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/grants', methods=['GET'])
@login_required
def get_user_grants():
    """Get user's saved grants and applications"""
    try:
        user = get_current_user()
        from app.models import Grant
        
        # Get all grants for user's organization
        grants = Grant.query.filter_by(org_id=user.org_id).all()
        
        # Categorize grants
        saved_grants = [g.to_dict() for g in grants if g.status == 'prospect']
        applications = [g.to_dict() for g in grants if g.status in ['drafting', 'submitted']]
        awarded = [g.to_dict() for g in grants if g.status == 'awarded']
        
        return jsonify({
            'success': True,
            'saved_grants': saved_grants,
            'applications': applications,
            'awarded': awarded,
            'total_saved': len(saved_grants),
            'total_applications': len(applications),
            'total_awarded': len(awarded)
        })
    except Exception as e:
        logger.error(f"Error getting user grants: {e}")
        return jsonify({'error': str(e)}), 500