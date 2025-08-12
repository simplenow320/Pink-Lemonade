"""
SendGrid Email Service for Survey Invitations and Notifications
Handles all email communications for the Smart Reporting system
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional
from flask import current_app, url_for
import io
import base64

# Optional imports for SendGrid and QR Code
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content, Personalization
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

logger = logging.getLogger(__name__)

class SendGridService:
    """Service for sending emails via SendGrid"""
    
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.from_email = "noreply@pinklemonade.app"
        self.client = None
        
        if SENDGRID_AVAILABLE and self.api_key:
            self.client = SendGridAPIClient(self.api_key)
            logger.info("SendGrid service initialized successfully")
        else:
            if not SENDGRID_AVAILABLE:
                logger.warning("SendGrid package not available - email features disabled")
            else:
                logger.warning("SendGrid API key not found - email features disabled")
    
    def is_enabled(self) -> bool:
        """Check if SendGrid is properly configured"""
        return self.client is not None
    
    def send_survey_invitation(self, 
                             project_id: int, 
                             recipient_email: str, 
                             recipient_name: str,
                             role: str,
                             custom_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Send survey invitation email with QR code and personalized content
        """
        if not self.is_enabled():
            return {
                'success': False,
                'error': 'SendGrid not configured - API key required'
            }
        
        try:
            # Generate survey URL
            survey_url = f"{self._get_base_url()}/survey/{project_id}?role={role}"
            
            # Generate QR code for mobile access
            qr_code_data = self._generate_qr_code(survey_url)
            
            # Create email content
            subject = f"📊 Impact Survey Invitation - Your Input Needed"
            
            # HTML email template
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f9fafb; padding: 20px;">
                <div style="background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #ec4899; margin: 0; font-size: 24px;">🍋 Pink Lemonade</h1>
                        <p style="color: #6b7280; margin: 5px 0 0 0;">Impact Measurement Platform</p>
                    </div>
                    
                    <h2 style="color: #374151; margin-bottom: 20px;">Hi {recipient_name},</h2>
                    
                    <p style="color: #4b5563; line-height: 1.6; margin-bottom: 20px;">
                        You've been invited to participate in an important impact survey as a <strong>{role}</strong>. 
                        Your insights will help measure the real-world outcomes of our programs and improve future initiatives.
                    </p>
                    
                    {f'<div style="background: #fef3f4; border-left: 4px solid #ec4899; padding: 15px; margin: 20px 0;"><p style="margin: 0; color: #4b5563; font-style: italic;">"{custom_message}"</p></div>' if custom_message else ''}
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{survey_url}" 
                           style="background: #ec4899; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                            Take Survey Now
                        </a>
                    </div>
                    
                    <div style="background: #f3f4f6; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                        <p style="color: #6b7280; margin: 0 0 10px 0; font-size: 14px;">
                            <strong>Quick Mobile Access</strong><br>
                            Scan with your phone camera:
                        </p>
                        <div style="display: inline-block; padding: 10px; background: white; border-radius: 5px;">
                            <img src="data:image/png;base64,{qr_code_data}" alt="Survey QR Code" style="width: 150px; height: 150px;">
                        </div>
                    </div>
                    
                    <div style="margin: 30px 0 20px 0; padding: 20px; background: #f9fafb; border-radius: 8px;">
                        <h3 style="color: #374151; margin: 0 0 15px 0; font-size: 16px;">🎯 Why Your Input Matters:</h3>
                        <ul style="color: #4b5563; line-height: 1.6; margin: 0; padding-left: 20px;">
                            <li>Help measure real program impact</li>
                            <li>Inform future funding decisions</li>
                            <li>Improve program effectiveness</li>
                            <li>Support community needs assessment</li>
                        </ul>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px; margin: 30px 0 0 0; text-align: center;">
                        Questions? Contact us at support@pinklemonade.app<br>
                        This survey is mobile-optimized and takes approximately 5-10 minutes to complete.
                    </p>
                </div>
            </div>
            """
            
            # Text version
            text_content = f"""
            Hi {recipient_name},
            
            You've been invited to participate in an important impact survey as a {role}.
            
            Your insights will help measure the real-world outcomes of our programs and improve future initiatives.
            
            Take the survey here: {survey_url}
            
            {f'Personal message: "{custom_message}"' if custom_message else ''}
            
            Why your input matters:
            - Help measure real program impact
            - Inform future funding decisions  
            - Improve program effectiveness
            - Support community needs assessment
            
            Questions? Contact us at support@pinklemonade.app
            
            Thanks,
            Pink Lemonade Team
            """
            
            # Send email
            message = Mail(
                from_email=Email(self.from_email, "Pink Lemonade Impact Team"),
                to_emails=To(recipient_email, recipient_name),
                subject=subject
            )
            
            message.content = [
                Content("text/plain", text_content),
                Content("text/html", html_content)
            ]
            
            response = self.client.send(message)
            
            logger.info(f"Survey invitation sent to {recipient_email} for project {project_id}")
            
            return {
                'success': True,
                'message_id': response.headers.get('X-Message-Id'),
                'survey_url': survey_url,
                'qr_code_generated': True
            }
            
        except Exception as e:
            logger.error(f"Failed to send survey invitation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_bulk_invitations(self, 
                            project_id: int, 
                            recipients: List[Dict[str, Any]],
                            custom_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Send bulk survey invitations to multiple recipients
        """
        if not self.is_enabled():
            return {
                'success': False,
                'error': 'SendGrid not configured - API key required'
            }
        
        results = {
            'total_sent': 0,
            'total_failed': 0,
            'failed_emails': [],
            'success': True
        }
        
        for recipient in recipients:
            result = self.send_survey_invitation(
                project_id=project_id,
                recipient_email=recipient['email'],
                recipient_name=recipient['name'],
                role=recipient['role'],
                custom_message=custom_message
            )
            
            if result['success']:
                results['total_sent'] += 1
            else:
                results['total_failed'] += 1
                results['failed_emails'].append({
                    'email': recipient['email'],
                    'error': result['error']
                })
        
        if results['total_failed'] > 0:
            results['success'] = False
        
        logger.info(f"Bulk invitations completed: {results['total_sent']} sent, {results['total_failed']} failed")
        
        return results
    
    def send_reminder_email(self, 
                          project_id: int,
                          recipient_email: str,
                          recipient_name: str,
                          role: str,
                          days_remaining: int) -> Dict[str, Any]:
        """
        Send reminder email for incomplete surveys
        """
        if not self.is_enabled():
            return {'success': False, 'error': 'SendGrid not configured'}
        
        try:
            survey_url = f"{self._get_base_url()}/survey/{project_id}?role={role}"
            
            subject = f"⏰ Reminder: Survey Response Needed ({days_remaining} days left)"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f9fafb; padding: 20px;">
                <div style="background: white; border-radius: 10px; padding: 30px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #ec4899; margin: 0;">🍋 Pink Lemonade</h1>
                    </div>
                    
                    <h2 style="color: #374151;">Hi {recipient_name},</h2>
                    
                    <p style="color: #4b5563; line-height: 1.6;">
                        This is a friendly reminder that your survey response is still needed for our impact measurement study.
                    </p>
                    
                    <div style="background: #fef3f4; border-left: 4px solid #ec4899; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0; color: #7c2d12; font-weight: bold;">
                            ⏰ Survey closes in {days_remaining} day{'s' if days_remaining != 1 else ''}
                        </p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{survey_url}" 
                           style="background: #ec4899; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                            Complete Survey Now
                        </a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px; text-align: center;">
                        Takes only 5-10 minutes • Mobile optimized
                    </p>
                </div>
            </div>
            """
            
            message = Mail(
                from_email=Email(self.from_email, "Pink Lemonade Team"),
                to_emails=To(recipient_email, recipient_name),
                subject=subject,
                html_content=html_content
            )
            
            response = self.client.send(message)
            
            return {
                'success': True,
                'message_id': response.headers.get('X-Message-Id')
            }
            
        except Exception as e:
            logger.error(f"Failed to send reminder email: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_qr_code(self, url: str) -> str:
        """
        Generate QR code for survey URL and return as base64 string
        """
        if not QRCODE_AVAILABLE:
            logger.warning("QR code package not available")
            return ""
            
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return img_str
            
        except Exception as e:
            logger.error(f"QR code generation failed: {e}")
            return ""
    
    def _get_base_url(self) -> str:
        """Get the base URL for the application"""
        if current_app:
            return current_app.config.get('BASE_URL', 'https://your-app.replit.app')
        return 'https://your-app.replit.app'

# Global service instance
sendgrid_service = SendGridService()