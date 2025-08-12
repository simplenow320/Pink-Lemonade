"""
Email Notification System
Handles email alerts for grant deadlines, team updates, and more
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)
bp = Blueprint('email_notifications', __name__)

# Check if SendGrid is available
SENDGRID_AVAILABLE = False
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')

if SENDGRID_API_KEY:
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content
        SENDGRID_AVAILABLE = True
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        logger.info("SendGrid configured successfully")
    except ImportError:
        logger.warning("SendGrid package not installed")
    except Exception as e:
        logger.warning(f"SendGrid configuration error: {e}")

# Email templates
EMAIL_TEMPLATES = {
    'grant_deadline': {
        'subject': 'Grant Deadline Reminder: {grant_title}',
        'body': """
        <h2>Grant Deadline Approaching</h2>
        <p>This is a reminder that the deadline for <strong>{grant_title}</strong> is approaching.</p>
        <p>Deadline: <strong>{deadline}</strong></p>
        <p>Funder: {funder}</p>
        <p>Amount: {amount}</p>
        <p><a href="{link}">View Grant Details</a></p>
        """
    },
    'team_invite': {
        'subject': 'You\'ve been invited to join {org_name} on Pink Lemonade',
        'body': """
        <h2>Team Invitation</h2>
        <p>You've been invited to join <strong>{org_name}</strong> on Pink Lemonade.</p>
        <p>Role: <strong>{role}</strong></p>
        <p><a href="{invite_link}">Accept Invitation</a></p>
        <p>This invitation expires in 7 days.</p>
        """
    },
    'grant_match': {
        'subject': 'New Grant Match: {grant_title}',
        'body': """
        <h2>New Grant Opportunity Matched</h2>
        <p>We found a grant that matches your organization's profile!</p>
        <p><strong>{grant_title}</strong></p>
        <p>Match Score: <strong>{score}/5</strong></p>
        <p>Reason: {reason}</p>
        <p><a href="{link}">View Grant</a></p>
        """
    },
    'weekly_summary': {
        'subject': 'Your Weekly Grant Summary',
        'body': """
        <h2>Weekly Grant Summary</h2>
        <p>Here's your weekly grant activity summary:</p>
        <ul>
            <li>New Opportunities: <strong>{new_grants}</strong></li>
            <li>Upcoming Deadlines: <strong>{deadlines}</strong></li>
            <li>Team Activities: <strong>{activities}</strong></li>
            <li>Documents Uploaded: <strong>{documents}</strong></li>
        </ul>
        <p><a href="{dashboard_link}">View Dashboard</a></p>
        """
    }
}

def send_email(to_email, template_name, context):
    """
    Send an email using SendGrid or log it if SendGrid is not available
    """
    try:
        template = EMAIL_TEMPLATES.get(template_name)
        if not template:
            return {'success': False, 'error': 'Template not found'}
        
        subject = template['subject'].format(**context)
        body = template['body'].format(**context)
        
        if SENDGRID_AVAILABLE:
            # Send actual email via SendGrid
            message = Mail(
                from_email=Email('notifications@pinklemonade.ai'),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", body)
            )
            
            response = sg.send(message)
            
            return {
                'success': True,
                'status_code': response.status_code,
                'message': 'Email sent successfully'
            }
        else:
            # Log email for development
            logger.info(f"Email would be sent to {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Template: {template_name}")
            
            return {
                'success': True,
                'message': 'Email logged (SendGrid not configured)',
                'preview': {
                    'to': to_email,
                    'subject': subject,
                    'template': template_name
                }
            }
            
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return {'success': False, 'error': str(e)}

@bp.route('/api/notifications/send', methods=['POST'])
def send_notification():
    """
    Send an email notification
    """
    try:
        data = request.get_json() or {}
        to_email = data.get('to_email')
        template = data.get('template')
        context = data.get('context', {})
        
        if not to_email or not template:
            return jsonify({'error': 'Email and template are required'}), 400
        
        result = send_email(to_email, template, context)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in send notification: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/notifications/test', methods=['POST'])
def test_email():
    """
    Test email configuration
    """
    try:
        data = request.get_json() or {}
        test_email = data.get('email', 'test@example.com')
        
        result = send_email(
            test_email,
            'grant_deadline',
            {
                'grant_title': 'Test Grant Opportunity',
                'deadline': 'December 31, 2025',
                'funder': 'Test Foundation',
                'amount': '$10,000 - $50,000',
                'link': 'https://pinklemonade.ai/grants/test'
            }
        )
        
        return jsonify({
            'success': result['success'],
            'sendgrid_configured': SENDGRID_AVAILABLE,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error testing email: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/notifications/schedule', methods=['POST'])
def schedule_notifications():
    """
    Schedule automated notifications
    """
    try:
        data = request.get_json() or {}
        notification_type = data.get('type')  # deadline, weekly, match
        
        # This would integrate with a task scheduler in production
        scheduled_time = datetime.utcnow() + timedelta(days=1)
        
        return jsonify({
            'success': True,
            'message': f'{notification_type} notifications scheduled',
            'scheduled_for': scheduled_time.isoformat(),
            'sendgrid_configured': SENDGRID_AVAILABLE
        })
        
    except Exception as e:
        logger.error(f"Error scheduling notifications: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/notifications/preferences', methods=['GET', 'POST'])
def notification_preferences():
    """
    Get or update notification preferences for a user
    """
    try:
        if request.method == 'GET':
            # Return current preferences
            return jsonify({
                'success': True,
                'preferences': {
                    'deadline_reminders': True,
                    'new_matches': True,
                    'team_updates': True,
                    'weekly_summary': True,
                    'reminder_days': [7, 3, 1]  # Days before deadline
                }
            })
        
        else:  # POST
            data = request.get_json() or {}
            # Update preferences (would save to database in production)
            
            return jsonify({
                'success': True,
                'message': 'Preferences updated',
                'preferences': data
            })
            
    except Exception as e:
        logger.error(f"Error with preferences: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/notifications/status', methods=['GET'])
def notification_status():
    """
    Get email notification system status
    """
    return jsonify({
        'success': True,
        'sendgrid_configured': SENDGRID_AVAILABLE,
        'api_key_present': bool(SENDGRID_API_KEY),
        'templates_available': list(EMAIL_TEMPLATES.keys()),
        'status': 'active' if SENDGRID_AVAILABLE else 'development_mode'
    })