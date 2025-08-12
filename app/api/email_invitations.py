"""
Email Invitations API for Smart Reporting Surveys
Handles survey invitations, bulk sending, and reminders
"""

from flask import Blueprint, request, jsonify, current_app
from app.services.sendgrid_service import sendgrid_service
from app.models_extended import Project, SurveyResponse
from app.models import Grant, Organization
from app import db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('email_invitations', __name__, url_prefix='/api/email-invitations')


@bp.route('/send-survey-invitation', methods=['POST'])
def send_survey_invitation():
    """
    Send individual survey invitation
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['project_id', 'recipient_email', 'recipient_name', 'role']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Missing required fields',
                'required': required_fields
            }), 400
        
        # Check if SendGrid is configured
        if not sendgrid_service.is_enabled():
            return jsonify({
                'success': False,
                'error': 'Email service not configured. Please contact administrator.',
                'needs_setup': True
            }), 503
        
        # Verify project exists
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({
                'success': False,
                'error': 'Project not found'
            }), 404
        
        # Send invitation
        result = sendgrid_service.send_survey_invitation(
            project_id=data['project_id'],
            recipient_email=data['recipient_email'],
            recipient_name=data['recipient_name'],
            role=data['role'],
            custom_message=data.get('custom_message')
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Survey invitation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/send-bulk-invitations', methods=['POST'])
def send_bulk_invitations():
    """
    Send bulk survey invitations to multiple recipients
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'project_id' not in data or 'recipients' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing project_id or recipients'
            }), 400
        
        # Check if SendGrid is configured
        if not sendgrid_service.is_enabled():
            return jsonify({
                'success': False,
                'error': 'Email service not configured. Please contact administrator.',
                'needs_setup': True
            }), 503
        
        # Verify project exists
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({
                'success': False,
                'error': 'Project not found'
            }), 404
        
        # Validate recipients format
        recipients = data['recipients']
        if not isinstance(recipients, list) or len(recipients) == 0:
            return jsonify({
                'success': False,
                'error': 'Recipients must be a non-empty list'
            }), 400
        
        # Validate each recipient
        for i, recipient in enumerate(recipients):
            required_fields = ['email', 'name', 'role']
            if not all(field in recipient for field in required_fields):
                return jsonify({
                    'success': False,
                    'error': f'Recipient {i+1} missing required fields: {required_fields}'
                }), 400
        
        # Send bulk invitations
        result = sendgrid_service.send_bulk_invitations(
            project_id=data['project_id'],
            recipients=recipients,
            custom_message=data.get('custom_message')
        )
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Bulk invitations failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/send-reminders', methods=['POST'])
def send_reminders():
    """
    Send reminder emails to participants who haven't completed surveys
    """
    try:
        data = request.get_json()
        
        if 'project_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing project_id'
            }), 400
        
        # Check if SendGrid is configured
        if not sendgrid_service.is_enabled():
            return jsonify({
                'success': False,
                'error': 'Email service not configured. Please contact administrator.',
                'needs_setup': True
            }), 503
        
        project_id = data['project_id']
        project = Project.query.get(project_id)
        if not project:
            return jsonify({
                'success': False,
                'error': 'Project not found'
            }), 404
        
        # Calculate days remaining (example: 30 days from project start)
        days_remaining = max(0, (project.end_date - datetime.now().date()).days)
        
        # For demo purposes, send to provided recipients
        # In production, this would query for incomplete responses
        recipients = data.get('recipients', [])
        
        results = {
            'total_sent': 0,
            'total_failed': 0,
            'failed_emails': []
        }
        
        for recipient in recipients:
            result = sendgrid_service.send_reminder_email(
                project_id=project_id,
                recipient_email=recipient['email'],
                recipient_name=recipient['name'],
                role=recipient['role'],
                days_remaining=days_remaining
            )
            
            if result['success']:
                results['total_sent'] += 1
            else:
                results['total_failed'] += 1
                results['failed_emails'].append({
                    'email': recipient['email'],
                    'error': result['error']
                })
        
        results['success'] = results['total_failed'] == 0
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Reminder emails failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/generate-survey-link/<int:project_id>', methods=['GET'])
def generate_survey_link(project_id):
    """
    Generate shareable survey link with QR code
    """
    try:
        # Verify project exists
        project = Project.query.get(project_id)
        if not project:
            return jsonify({
                'success': False,
                'error': 'Project not found'
            }), 404
        
        role = request.args.get('role', 'participant')
        
        # Generate base URL
        base_url = current_app.config.get('BASE_URL', 'https://your-app.replit.app')
        survey_url = f"{base_url}/survey/{project_id}?role={role}"
        
        # Generate QR code if SendGrid service is available
        qr_code_data = ""
        if sendgrid_service.is_enabled():
            qr_code_data = sendgrid_service._generate_qr_code(survey_url)
        
        return jsonify({
            'success': True,
            'survey_url': survey_url,
            'qr_code_base64': qr_code_data,
            'project_name': project.name,
            'role': role
        }), 200
        
    except Exception as e:
        logger.error(f"Survey link generation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/email-service-status', methods=['GET'])
def email_service_status():
    """
    Check email service configuration status
    """
    try:
        is_enabled = sendgrid_service.is_enabled()
        
        return jsonify({
            'success': True,
            'email_service_enabled': is_enabled,
            'provider': 'SendGrid' if is_enabled else None,
            'features_available': {
                'survey_invitations': is_enabled,
                'bulk_sending': is_enabled,
                'qr_code_generation': is_enabled,
                'reminder_emails': is_enabled
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Email service status check failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500