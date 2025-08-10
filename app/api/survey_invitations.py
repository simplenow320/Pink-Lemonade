"""
Survey Invitation API endpoints
"""

import json
from flask import Blueprint, request, jsonify, session
from datetime import datetime

from app import db
from app.models_extended import Project, SurveyInvitation, SurveyDistribution
from app.services.survey_invitation_service import SurveyInvitationService

bp = Blueprint('survey_invitations', __name__, url_prefix='/api/survey-invitations')

# Initialize service
invitation_service = SurveyInvitationService()


@bp.route('/create', methods=['POST'])
def create_invitation():
    """Create a new survey invitation"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('project_id'):
            return jsonify({"success": False, "error": "Project ID required"}), 400
        if not data.get('email'):
            return jsonify({"success": False, "error": "Email required"}), 400
        
        # Create invitation
        result = invitation_service.create_invitation(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/send/<int:invitation_id>', methods=['POST'])
def send_invitation(invitation_id):
    """Send invitation email"""
    try:
        result = invitation_service.send_invitation_email(invitation_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/bulk-create', methods=['POST'])
def create_bulk_distribution():
    """Create bulk survey distribution"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('project_id'):
            return jsonify({"success": False, "error": "Project ID required"}), 400
        if not data.get('campaign_name'):
            return jsonify({"success": False, "error": "Campaign name required"}), 400
        if not data.get('recipients'):
            return jsonify({"success": False, "error": "Recipients list required"}), 400
        
        # Create distribution
        result = invitation_service.create_bulk_distribution(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/generate-qr/<int:invitation_id>', methods=['POST'])
def generate_qr_code(invitation_id):
    """Generate QR code for invitation"""
    try:
        invitation = SurveyInvitation.query.get(invitation_id)
        if not invitation:
            return jsonify({"success": False, "error": "Invitation not found"}), 404
        
        result = invitation_service.generate_qr_code(invitation.id, invitation.invitation_token)
        
        if result['success']:
            # Update invitation
            invitation.qr_code_generated = True
            invitation.qr_code_path = result['qr_code_path']
            db.session.commit()
            
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/track-access/<token>', methods=['POST'])
def track_access(token):
    """Track survey access"""
    try:
        data = request.json or {}
        
        # Add request metadata
        data['ip_address'] = request.remote_addr
        data['user_agent'] = request.headers.get('User-Agent')
        data['referrer'] = request.headers.get('Referer')
        
        result = invitation_service.track_survey_access(token, data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/project/<int:project_id>/invitations', methods=['GET'])
def get_project_invitations(project_id):
    """Get all invitations for a project"""
    try:
        invitations = SurveyInvitation.query.filter_by(project_id=project_id).all()
        
        return jsonify({
            "success": True,
            "invitations": [inv.to_dict() for inv in invitations],
            "total": len(invitations)
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/distribution/<int:distribution_id>/metrics', methods=['GET'])
def get_distribution_metrics(distribution_id):
    """Get metrics for a distribution campaign"""
    try:
        result = invitation_service.get_distribution_metrics(distribution_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/register-respondent', methods=['POST'])
def register_respondent():
    """Register a new survey respondent"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('email'):
            return jsonify({"success": False, "error": "Email required"}), 400
        
        result = invitation_service.register_respondent(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/send-reminders/<int:distribution_id>', methods=['POST'])
def send_reminders(distribution_id):
    """Send reminder emails for incomplete surveys"""
    try:
        distribution = SurveyDistribution.query.get(distribution_id)
        if not distribution:
            return jsonify({"success": False, "error": "Distribution not found"}), 404
        
        # Get incomplete invitations
        invitations = SurveyInvitation.query.filter_by(
            project_id=distribution.project_id
        ).filter(
            SurveyInvitation.status.in_(['sent', 'opened', 'started'])
        ).all()
        
        reminders_sent = 0
        for invitation in invitations:
            # Skip if recently reminded
            if invitation.last_reminder_at and (datetime.utcnow() - invitation.last_reminder_at).days < 3:
                continue
            
            # Send reminder
            result = invitation_service.send_invitation_email(invitation.id)
            if result['success']:
                invitation.reminder_count += 1
                invitation.last_reminder_at = datetime.utcnow()
                reminders_sent += 1
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "reminders_sent": reminders_sent,
            "message": f"Sent {reminders_sent} reminder emails"
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500