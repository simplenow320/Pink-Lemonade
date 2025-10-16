        """
        User Settings API - Personal profile management
        """

        from flask import Blueprint, request, jsonify, session
        from werkzeug.security import check_password_hash, generate_password_hash
        from app.models import User
        from app import db
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
                    'email': 'user@example.org',
                    'phone': '(555) 123-4567',
                    'title': 'Grant Manager',
                    'organization': 'Your Organization',
                    'department': 'Development',
                    'bio': 'Experienced grant manager',
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
                # Check authentication
                if 'user_id' not in session:
                    return jsonify({'error': 'Not authenticated'}), 401

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

                # Get current user from database
                user = User.query.get(session['user_id'])

                if not user:
                    return jsonify({'error': 'User not found'}), 404

                # Verify current password
                if not check_password_hash(user.password_hash, current_password):
                    logging.warning(f"Failed password change attempt for user {user.email}")
                    return jsonify({'error': 'Current password is incorrect'}), 401

                # Hash and update new password
                user.password_hash = generate_password_hash(new_password)
                db.session.commit()

                logging.info(f"Password changed successfully for user {user.email}")

                # Send security notification email (optional)
                try:
                    from app.services.email_service import send_password_change_notification
                    send_password_change_notification(user.email)
                except Exception as email_error:
                    logging.error(f"Failed to send password change email: {email_error}")
                    # Don't fail the request if email fails

                # Clear current session to force re-login (optional security enhancement)
                session.clear()

                return jsonify({'message': 'Password updated successfully'})

            except Exception as e:
                db.session.rollback()
                logging.error(f"Error changing password: {e}")
                return jsonify({'error': 'Failed to change password'}), 500

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