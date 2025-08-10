"""
User Settings API - Personal profile management
"""

from flask import Blueprint, request, jsonify
import logging

bp = Blueprint('user_settings', __name__, url_prefix='/api/settings')

@bp.route('/user', methods=['GET'])
def get_user_settings():
    """Get current user settings/profile"""
    try:
        # For now, return sample user data that would come from onboarding
        # In production, this would get the authenticated user's data
        user_data = {
            'first_name': 'John',
            'last_name': 'Doe', 
            'email': 'john@nitrogennetwork.org',
            'phone': '(555) 123-4567',
            'title': 'Grant Manager',
            'organization': 'Nitrogen Network',
            'department': 'Development',
            'bio': 'Experienced grant manager passionate about urban ministry',
            'notifications': {
                'email_updates': True,
                'grant_alerts': True,
                'deadline_reminders': True,
                'weekly_digest': False
            },
            'preferences': {
                'theme': 'light',
                'timezone': 'America/New_York',
                'date_format': 'MM/DD/YYYY',
                'currency': 'USD'
            }
        }
        
        return jsonify(user_data)
        
    except Exception as e:
        logging.error(f"Error getting user settings: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/user', methods=['POST'])
def update_user_settings():
    """Update user settings/profile"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            if not data.get(field, '').strip():
                return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
        
        # In production, this would update the authenticated user
        logging.info(f"User settings update: {data.get('first_name')} {data.get('last_name')}")
        
        return jsonify({
            'message': 'User settings updated successfully',
            'user': {
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'email': data.get('email'),
                'title': data.get('title')
            }
        })
        
    except Exception as e:
        logging.error(f"Error updating user settings: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/password', methods=['POST'])
def change_password():
    """Change user password"""
    try:
        data = request.json
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validate inputs
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'error': 'All password fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'New passwords do not match'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        # In production, verify current password and update
        logging.info("Password change requested")
        
        return jsonify({'message': 'Password updated successfully'})
        
    except Exception as e:
        logging.error(f"Error changing password: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/notifications', methods=['POST'])
def update_notifications():
    """Update notification preferences"""
    try:
        data = request.json
        
        notification_settings = data.get('notifications', {})
        
        # In production, save to user preferences
        logging.info(f"Notification settings updated: {notification_settings}")
        
        return jsonify({
            'message': 'Notification settings updated successfully',
            'notifications': notification_settings
        })
        
    except Exception as e:
        logging.error(f"Error updating notifications: {e}")
        return jsonify({'error': str(e)}), 500