"""
User Settings API - Personal profile management
"""

from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User, Organization
from app.services.auth_manager import AuthManager
from app import db
import logging

bp = Blueprint('user_settings', __name__, url_prefix='/api/settings')
logger = logging.getLogger(__name__)

@bp.route('/user', methods=['GET'])
def get_user_settings():
    """Get current user settings/profile"""
    try:
        user = AuthManager.get_current_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get user's organization if exists
        org = db.session.query(Organization).filter_by(user_id=user.id).first()
        
        user_data = {
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'email': user.email,
            'phone': user.phone or '',
            'org_name': user.org_name or (org.name if org else ''),
            'job_title': user.job_title or '',
            'role': user.role or 'member',
            
            # Organization fields if available
            'ein': org.ein if org else '',
            'org_type': org.org_type if org else '',
            'budget_range': org.annual_budget_range if org else '',
            'mission': org.mission if org else '',
            'website': org.website if org else '',
            'service_area': f"{org.primary_city or ''}, {org.primary_state or ''}".strip(', ') if org else '',
            'focus_areas': org.primary_focus_areas if org and org.primary_focus_areas else [],
            'programs': [],  # Could be extracted from org.programs_services
            
            # Notification preferences
            'notifications': user.notification_preferences or {
                'email_updates': True,
                'grant_alerts': True,
                'deadline_reminders': True,
                'weekly_digest': False
            },
            
            # User preferences
            'preferences': {
                'timezone': user.timezone or 'America/New_York',
                'date_format': 'MM/DD/YYYY',  # Could be added to user model
                'currency': 'USD',  # Could be added to user model
                'theme': 'light'  # Could be added to user model
            }
        }
        
        return jsonify(user_data)
        
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/user', methods=['POST'])
def update_user_settings():
    """Update user settings/profile"""
    try:
        user = AuthManager.get_current_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json() or {}
        
        # Update user fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'org_name' in data:
            user.org_name = data['org_name']
        if 'job_title' in data:
            user.job_title = data['job_title']
        
        # Update preferences
        if 'preferences' in data:
            prefs = data['preferences']
            if 'timezone' in prefs:
                user.timezone = prefs['timezone']
            # Note: date_format, currency, theme could be stored in notification_preferences
            # or we could add a separate preferences JSON column
        
        # Update organization if exists
        org = db.session.query(Organization).filter_by(user_id=user.id).first()
        
        if data.get('org_name') or data.get('ein') or data.get('org_type'):
            if not org:
                # Create organization if it doesn't exist
                org = Organization()
                org.user_id = user.id
                org.created_by_user_id = user.id
                db.session.add(org)
            
            if 'org_name' in data and data['org_name']:
                org.name = data['org_name']
            if 'ein' in data:
                org.ein = data['ein']
            if 'org_type' in data:
                org.org_type = data['org_type']
            if 'budget_range' in data:
                org.annual_budget_range = data['budget_range']
            if 'mission' in data:
                org.mission = data['mission']
            if 'website' in data:
                org.website = data['website']
            if 'focus_areas' in data:
                org.primary_focus_areas = data['focus_areas']
        
        db.session.commit()
        
        logger.info(f"User settings updated for: {user.email}")
        
        return jsonify({
            'message': 'User settings updated successfully',
            'user': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user settings: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/password', methods=['POST'])
def change_password():
    """Change user password"""
    try:
        user = AuthManager.get_current_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json() or {}
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validate inputs
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'error': 'All password fields are required'}), 400
        
        # Type assertions for LSP (already validated above)
        assert new_password is not None
        assert current_password is not None
        assert confirm_password is not None
        
        if new_password != confirm_password:
            return jsonify({'error': 'New passwords do not match'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        # Verify current password
        if not user.check_password(current_password):
            logger.warning(f"Failed password change attempt for user {user.email}")
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        logger.info(f"Password changed successfully for user {user.email}")
        
        return jsonify({'message': 'Password updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing password: {e}")
        return jsonify({'error': 'Failed to change password'}), 500

@bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Get notification preferences"""
    try:
        user = AuthManager.get_current_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Return current notification preferences
        return jsonify({
            'notifications': user.notification_preferences or {
                'email_updates': True,
                'grant_alerts': True,
                'deadline_reminders': True,
                'weekly_digest': False
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/notifications', methods=['POST'])
def update_notifications():
    """Update notification preferences"""
    try:
        user = AuthManager.get_current_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json() or {}
        notification_settings = data.get('notifications', {})
        
        # Update user's notification preferences in database
        user.notification_preferences = notification_settings
        db.session.commit()
        
        logger.info(f"Notification settings updated for user: {user.email}")
        logger.debug(f"New notification settings: {notification_settings}")
        
        return jsonify({
            'message': 'Notification settings updated successfully',
            'notifications': notification_settings
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating notifications: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/preferences', methods=['GET'])
def get_preferences():
    """Get user preferences"""
    try:
        user = AuthManager.get_current_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        return jsonify({
            'preferences': {
                'timezone': user.timezone or 'America/New_York',
                'date_format': 'MM/DD/YYYY',
                'currency': 'USD',
                'theme': 'light'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/preferences', methods=['POST'])
def update_preferences():
    """Update user preferences"""
    try:
        user = AuthManager.get_current_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json() or {}
        preferences = data.get('preferences', {})
        
        # Update timezone in user model
        if 'timezone' in preferences:
            user.timezone = preferences['timezone']
        
        # Store other preferences in notification_preferences for now
        # (could create a separate preferences column in the future)
        current_prefs = user.notification_preferences or {}
        current_prefs['date_format'] = preferences.get('date_format', 'MM/DD/YYYY')
        current_prefs['currency'] = preferences.get('currency', 'USD')
        current_prefs['theme'] = preferences.get('theme', 'light')
        user.notification_preferences = current_prefs
        
        db.session.commit()
        
        logger.info(f"Preferences updated for user: {user.email}")
        
        return jsonify({
            'message': 'Preferences updated successfully',
            'preferences': preferences
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating preferences: {e}")
        return jsonify({'error': str(e)}), 500
