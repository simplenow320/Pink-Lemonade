"""
Survey Invitation Service
Handles survey invitations, QR code generation, and email distribution
"""

import os
import json
import uuid
import secrets
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from flask import url_for, current_app
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models_extended import (
    SurveyInvitation, SurveyRespondent, SurveyAccessLog,
    SurveyDistribution, Project, ImpactQuestion, SurveyTemplate
)


class SurveyInvitationService:
    """Service for managing survey invitations and distribution"""
    
    def __init__(self, logger=None):
        self.logger = logger
        
    def create_invitation(self, invitation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new survey invitation
        
        Args:
            invitation_data: Dictionary containing invitation details
            
        Returns:
            Dict with invitation result and details
        """
        try:
            # Generate unique invitation token
            invitation_token = secrets.token_urlsafe(32)
            
            # Create invitation record
            invitation = SurveyInvitation(
                project_id=invitation_data['project_id'],
                invitation_token=invitation_token,
                email=invitation_data['email'],
                respondent_type=invitation_data.get('respondent_type', 'participant'),
                respondent_name=invitation_data.get('respondent_name'),
                survey_template_id=invitation_data.get('survey_template_id'),
                questions_assigned=json.dumps(invitation_data.get('questions', [])),
                language=invitation_data.get('language', 'en'),
                requires_login=invitation_data.get('requires_login', True),
                anonymous_allowed=invitation_data.get('anonymous_allowed', False),
                single_use=invitation_data.get('single_use', True),
                expires_at=datetime.utcnow() + timedelta(days=invitation_data.get('expiry_days', 14))
            )
            
            db.session.add(invitation)
            db.session.flush()
            
            # Generate QR code if requested
            if invitation_data.get('generate_qr', False):
                qr_result = self.generate_qr_code(invitation.id, invitation_token)
                if qr_result['success']:
                    invitation.qr_code_generated = True
                    invitation.qr_code_path = qr_result['qr_code_path']
            
            db.session.commit()
            
            return {
                "success": True,
                "invitation": invitation.to_dict(),
                "survey_url": self._generate_survey_url(invitation_token),
                "qr_code": invitation.qr_code_path if invitation.qr_code_generated else None
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create invitation: {e}")
            db.session.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_qr_code(self, invitation_id: int, token: str) -> Dict[str, Any]:
        """
        Generate QR code for survey invitation
        
        Args:
            invitation_id: ID of the invitation
            token: Invitation token
            
        Returns:
            Dict with QR code generation result
        """
        try:
            # Generate survey URL
            survey_url = self._generate_survey_url(token)
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(survey_url)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to BytesIO
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Convert to base64
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            qr_data_url = f"data:image/png;base64,{qr_base64}"
            
            return {
                "success": True,
                "qr_code_path": qr_data_url,
                "survey_url": survey_url
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to generate QR code: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_invitation_email(self, invitation_id: int) -> Dict[str, Any]:
        """
        Send invitation email via SendGrid
        
        Args:
            invitation_id: ID of the invitation to send
            
        Returns:
            Dict with email sending result
        """
        try:
            invitation = SurveyInvitation.query.get(invitation_id)
            if not invitation:
                return {"success": False, "error": "Invitation not found"}
            
            # Check if SendGrid is configured
            sendgrid_key = os.environ.get('SENDGRID_API_KEY')
            if not sendgrid_key:
                return {
                    "success": False,
                    "error": "SendGrid API key not configured. Please add SENDGRID_API_KEY to secrets."
                }
            
            # Get project details
            project = Project.query.get(invitation.project_id)
            
            # Generate survey URL
            survey_url = self._generate_survey_url(invitation.invitation_token)
            
            # Email content
            subject = f"Survey Invitation: {project.name}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #ec4899;">You're Invited to Participate in Our Survey</h2>
                
                <p>Dear {invitation.respondent_name or 'Participant'},</p>
                
                <p>We value your input and would appreciate your participation in our survey for the project: <strong>{project.name}</strong></p>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Survey Type:</strong> {invitation.respondent_type.replace('_', ' ').title()}</p>
                    <p><strong>Expires:</strong> {invitation.expires_at.strftime('%B %d, %Y')}</p>
                    {f'<p><strong>Login Required:</strong> Yes</p>' if invitation.requires_login else ''}
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{survey_url}" style="background-color: #ec4899; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Take Survey
                    </a>
                </div>
                
                {f'<div style="text-align: center; margin: 20px 0;"><img src="{invitation.qr_code_path}" alt="QR Code" style="max-width: 200px;"/><p style="font-size: 12px;">Scan QR code to take survey on mobile</p></div>' if invitation.qr_code_generated else ''}
                
                <p style="color: #6b7280; font-size: 14px;">
                    If you have any questions, please don't hesitate to contact us.
                    This survey link will expire on {invitation.expires_at.strftime('%B %d, %Y')}.
                </p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;"/>
                
                <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                    Powered by Pink Lemonade Grant Management Platform
                </p>
            </body>
            </html>
            """
            
            text_content = f"""
            You're Invited to Participate in Our Survey
            
            Dear {invitation.respondent_name or 'Participant'},
            
            We value your input and would appreciate your participation in our survey for: {project.name}
            
            Survey Type: {invitation.respondent_type.replace('_', ' ').title()}
            Expires: {invitation.expires_at.strftime('%B %d, %Y')}
            
            Take Survey: {survey_url}
            
            This survey link will expire on {invitation.expires_at.strftime('%B %d, %Y')}.
            
            Powered by Pink Lemonade Grant Management Platform
            """
            
            # Import SendGrid helper
            try:
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail, Email, To, Content
                
                sg = SendGridAPIClient(sendgrid_key)
                
                message = Mail(
                    from_email=Email(os.environ.get('SENDGRID_FROM_EMAIL', 'surveys@pinklemonade.app')),
                    to_emails=To(invitation.email),
                    subject=subject
                )
                
                message.content = [
                    Content("text/plain", text_content),
                    Content("text/html", html_content)
                ]
                
                response = sg.send(message)
                
                # Update invitation status
                invitation.status = 'sent'
                invitation.sent_at = datetime.utcnow()
                db.session.commit()
                
                return {
                    "success": True,
                    "message": "Invitation email sent successfully"
                }
                
            except ImportError:
                return {
                    "success": False,
                    "error": "SendGrid library not installed. Please install python-sendgrid."
                }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to send invitation email: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_bulk_distribution(self, distribution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a bulk survey distribution campaign
        
        Args:
            distribution_data: Dictionary containing distribution details
            
        Returns:
            Dict with distribution result
        """
        try:
            # Create distribution campaign
            distribution = SurveyDistribution(
                project_id=distribution_data['project_id'],
                campaign_name=distribution_data['campaign_name'],
                description=distribution_data.get('description'),
                distribution_method=distribution_data.get('method', 'email'),
                recipient_list=json.dumps(distribution_data.get('recipients', [])),
                total_recipients=len(distribution_data.get('recipients', [])),
                track_names=distribution_data.get('track_names', True),
                allow_anonymous=distribution_data.get('allow_anonymous', False),
                use_different_templates=distribution_data.get('use_different_templates', False),
                template_assignments=json.dumps(distribution_data.get('template_assignments', {})),
                generate_qr_codes=distribution_data.get('generate_qr_codes', False),
                qr_code_size=distribution_data.get('qr_code_size', 'medium'),
                qr_code_format=distribution_data.get('qr_code_format', 'png')
            )
            
            db.session.add(distribution)
            db.session.flush()
            
            # Create individual invitations
            recipients = distribution_data.get('recipients', [])
            invitations_created = []
            
            for recipient in recipients:
                invitation_data = {
                    'project_id': distribution_data['project_id'],
                    'email': recipient.get('email'),
                    'respondent_type': recipient.get('type', 'participant'),
                    'respondent_name': recipient.get('name') if distribution.track_names else None,
                    'requires_login': not distribution.allow_anonymous,
                    'anonymous_allowed': distribution.allow_anonymous,
                    'generate_qr': distribution.generate_qr_codes,
                    'expiry_days': distribution_data.get('expiry_days', 14)
                }
                
                # Assign template based on respondent type if configured
                if distribution.use_different_templates:
                    template_assignments = json.loads(distribution.template_assignments)
                    template_id = template_assignments.get(recipient.get('type'))
                    if template_id:
                        invitation_data['survey_template_id'] = template_id
                
                result = self.create_invitation(invitation_data)
                if result['success']:
                    invitations_created.append(result['invitation'])
            
            distribution.invitations_sent = len(invitations_created)
            distribution.status = 'ready'
            db.session.commit()
            
            return {
                "success": True,
                "distribution": distribution.to_dict(),
                "invitations_created": len(invitations_created),
                "message": f"Created {len(invitations_created)} survey invitations"
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create bulk distribution: {e}")
            db.session.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def register_respondent(self, respondent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new survey respondent
        
        Args:
            respondent_data: Dictionary containing respondent details
            
        Returns:
            Dict with registration result
        """
        try:
            # Check if respondent already exists
            existing = SurveyRespondent.query.filter_by(email=respondent_data['email']).first()
            if existing:
                return {
                    "success": False,
                    "error": "Respondent already registered"
                }
            
            # Create new respondent
            respondent = SurveyRespondent(
                email=respondent_data['email'],
                password_hash=generate_password_hash(respondent_data['password']) if respondent_data.get('password') else None,
                first_name=respondent_data.get('first_name'),
                last_name=respondent_data.get('last_name'),
                organization_id=respondent_data.get('organization_id'),
                respondent_type=respondent_data.get('respondent_type', 'participant'),
                verification_token=secrets.token_urlsafe(32)
            )
            
            db.session.add(respondent)
            db.session.commit()
            
            return {
                "success": True,
                "respondent": respondent.to_dict(),
                "verification_token": respondent.verification_token
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to register respondent: {e}")
            db.session.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def track_survey_access(self, invitation_token: str, access_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track when a survey is accessed
        
        Args:
            invitation_token: The invitation token used to access survey
            access_data: Dictionary containing access details
            
        Returns:
            Dict with tracking result
        """
        try:
            # Find invitation
            invitation = SurveyInvitation.query.filter_by(invitation_token=invitation_token).first()
            if not invitation:
                return {"success": False, "error": "Invalid invitation token"}
            
            # Update invitation status
            if invitation.status == 'sent':
                invitation.status = 'opened'
                invitation.opened_at = datetime.utcnow()
            
            # Create access log
            access_log = SurveyAccessLog(
                invitation_id=invitation.id,
                respondent_id=access_data.get('respondent_id'),
                access_type=access_data.get('access_type', 'direct_link'),
                ip_address=access_data.get('ip_address'),
                user_agent=access_data.get('user_agent'),
                referrer=access_data.get('referrer'),
                session_token=secrets.token_urlsafe(16)
            )
            
            db.session.add(access_log)
            db.session.commit()
            
            return {
                "success": True,
                "access_log": access_log.to_dict(),
                "session_token": access_log.session_token
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to track survey access: {e}")
            db.session.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_survey_url(self, token: str) -> str:
        """Generate survey URL from token"""
        base_url = os.environ.get('REPLIT_DOMAINS', 'http://localhost:5000')
        if base_url and ',' in base_url:
            base_url = f"https://{base_url.split(',')[0]}"
        return f"{base_url}/survey/{token}"
    
    def get_distribution_metrics(self, distribution_id: int) -> Dict[str, Any]:
        """
        Get metrics for a survey distribution campaign
        
        Args:
            distribution_id: ID of the distribution
            
        Returns:
            Dict with distribution metrics
        """
        try:
            distribution = SurveyDistribution.query.get(distribution_id)
            if not distribution:
                return {"success": False, "error": "Distribution not found"}
            
            # Get invitation metrics
            invitations = SurveyInvitation.query.filter_by(project_id=distribution.project_id).all()
            
            metrics = {
                "total_invitations": len(invitations),
                "sent": sum(1 for i in invitations if i.status in ['sent', 'opened', 'started', 'completed']),
                "opened": sum(1 for i in invitations if i.status in ['opened', 'started', 'completed']),
                "started": sum(1 for i in invitations if i.status in ['started', 'completed']),
                "completed": sum(1 for i in invitations if i.status == 'completed'),
                "expired": sum(1 for i in invitations if i.expires_at < datetime.utcnow()),
                "response_rate": 0,
                "completion_rate": 0,
                "average_completion_time": None
            }
            
            # Calculate rates
            if metrics['sent'] > 0:
                metrics['response_rate'] = round((metrics['started'] / metrics['sent']) * 100, 1)
                metrics['completion_rate'] = round((metrics['completed'] / metrics['sent']) * 100, 1)
            
            # Update distribution metrics
            distribution.invitations_opened = metrics['opened']
            distribution.surveys_started = metrics['started']
            distribution.surveys_completed = metrics['completed']
            db.session.commit()
            
            return {
                "success": True,
                "metrics": metrics,
                "distribution": distribution.to_dict()
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get distribution metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }