"""
Production Email Service - Complete Implementation
Full SMTP email service for production notifications
"""

import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    """Production-ready email service with SMTP configuration"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@pinklemonade.ai')
        self.use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        
        # Validate configuration
        self.is_configured = bool(self.smtp_username and self.smtp_password)
        
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: Optional[str] = None, attachments: Optional[List] = None) -> Dict[str, Any]:
        """
        Send email with HTML and optional text content
        """
        try:
            if not self.is_configured:
                logger.warning("Email service not configured - using development mode")
                return self._log_email_dev_mode(to_email, subject, html_content)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return {
                'success': True,
                'message': 'Email sent successfully',
                'timestamp': datetime.utcnow().isoformat(),
                'method': 'smtp'
            }
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def send_grant_match_notification(self, to_email: str, grant_data: Dict, match_analysis: Dict) -> Dict[str, Any]:
        """Send grant match notification email"""
        subject = f"🎯 High-Value Grant Match: {grant_data.get('title', 'New Grant')} ({match_analysis.get('match_score', 0)}% match)"
        
        html_content = self._create_grant_match_html(grant_data, match_analysis)
        text_content = self._create_grant_match_text(grant_data, match_analysis)
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_deadline_reminder(self, to_email: str, grant_data: Dict, days_remaining: int) -> Dict[str, Any]:
        """Send deadline reminder email"""
        urgency = self._get_urgency_level(days_remaining)
        subject = f"⏰ {urgency} Grant Deadline: {grant_data.get('title', 'Grant')} ({days_remaining} days left)"
        
        html_content = self._create_deadline_reminder_html(grant_data, days_remaining, urgency)
        text_content = self._create_deadline_reminder_text(grant_data, days_remaining, urgency)
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_weekly_digest(self, to_email: str, digest_data: Dict) -> Dict[str, Any]:
        """Send weekly digest email"""
        subject = f"📊 Your Weekly Grant Digest - {digest_data.get('new_grants', 0)} New Opportunities"
        
        html_content = self._create_weekly_digest_html(digest_data)
        text_content = self._create_weekly_digest_text(digest_data)
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_system_alert(self, to_emails: List[str], alert_type: str, message: str) -> Dict[str, Any]:
        """Send system alert to administrators"""
        subject = f"🚨 System Alert: {alert_type}"
        
        html_content = self._create_system_alert_html(alert_type, message)
        text_content = self._create_system_alert_text(alert_type, message)
        
        results = []
        for email in to_emails:
            result = self.send_email(email, subject, html_content, text_content)
            results.append({'email': email, 'result': result})
        
        success_count = sum(1 for r in results if r['result'].get('success'))
        
        return {
            'success': success_count > 0,
            'total_sent': success_count,
            'total_recipients': len(to_emails),
            'results': results
        }
    
    def test_configuration(self) -> Dict[str, Any]:
        """Test email configuration"""
        try:
            if not self.is_configured:
                return {
                    'success': False,
                    'error': 'Email service not configured',
                    'missing_vars': [var for var in ['SMTP_USERNAME', 'SMTP_PASSWORD'] if not os.getenv(var)]
                }
            
            # Test SMTP connection
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            
            return {
                'success': True,
                'message': 'Email configuration is valid',
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port,
                'from_email': self.from_email
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'configuration': {
                    'smtp_server': self.smtp_server,
                    'smtp_port': self.smtp_port,
                    'from_email': self.from_email
                }
            }
    
    def _log_email_dev_mode(self, to_email: str, subject: str, content: str) -> Dict[str, Any]:
        """Log email in development mode"""
        logger.info(f"EMAIL (Development Mode):")
        logger.info(f"To: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Content length: {len(content)} characters")
        
        return {
            'success': True,
            'message': 'Email logged in development mode',
            'method': 'development_log',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict):
        """Add attachment to email message"""
        try:
            with open(attachment['path'], 'rb') as file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["filename"]}'
                )
                msg.attach(part)
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment}: {e}")
    
    def _create_grant_match_html(self, grant_data: Dict, match_analysis: Dict) -> str:
        """Create HTML content for grant match email"""
        return f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Grant Match Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #FF6B9D, #C44CAF); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🎯 High-Value Grant Match!</h1>
                <p style="color: white; margin: 10px 0 0 0; font-size: 18px;">{match_analysis.get('match_score', 0)}% Match Confidence</p>
            </div>
            
            <div style="padding: 30px; background: white; border: 1px solid #ddd; border-top: none;">
                <h2 style="color: #333; margin-top: 0; font-size: 20px;">{grant_data.get('title', 'Grant Opportunity')}</h2>
                
                <div style="margin: 20px 0;">
                    <p style="color: #666; font-size: 16px; line-height: 1.6; margin: 5px 0;">
                        <strong>Funder:</strong> {grant_data.get('funder', 'Not specified')}<br>
                        <strong>Amount:</strong> ${grant_data.get('amount_min', 0):,.0f} - ${grant_data.get('amount_max', 0):,.0f}<br>
                        <strong>Deadline:</strong> {grant_data.get('deadline', 'Not specified')}<br>
                        <strong>AI Confidence:</strong> {match_analysis.get('confidence', 'Medium').title()}
                    </p>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-left: 4px solid #FF6B9D; margin: 20px 0; border-radius: 5px;">
                    <h3 style="color: #333; margin-top: 0; font-size: 16px;">Why This Grant Matches Your Organization</h3>
                    <p style="color: #666; line-height: 1.6; margin: 10px 0 0 0;">{match_analysis.get('reasoning', 'This grant has been identified as a potential match for your organization.')}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{grant_data.get('source_url', '#')}" 
                       style="background: #FF6B9D; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                        View Grant Details
                    </a>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; color: #666; border-radius: 0 0 10px 10px;">
                <p style="margin: 0;">Happy grant hunting! 🌟</p>
                <p style="margin: 10px 0 0 0;"><small>Pink Lemonade - AI-Powered Grant Management</small></p>
            </div>
        </body>
        </html>
        """
    
    def _create_grant_match_text(self, grant_data: Dict, match_analysis: Dict) -> str:
        """Create text content for grant match email"""
        return f"""
HIGH-VALUE GRANT MATCH - {match_analysis.get('match_score', 0)}% Match

{grant_data.get('title', 'Grant Opportunity')}

Funder: {grant_data.get('funder', 'Not specified')}
Amount: ${grant_data.get('amount_min', 0):,.0f} - ${grant_data.get('amount_max', 0):,.0f}
Deadline: {grant_data.get('deadline', 'Not specified')}
AI Confidence: {match_analysis.get('confidence', 'Medium').title()}

Why This Grant Matches Your Organization:
{match_analysis.get('reasoning', 'This grant has been identified as a potential match for your organization.')}

View Grant Details: {grant_data.get('source_url', 'Contact your administrator')}

Happy grant hunting!
Pink Lemonade - AI-Powered Grant Management
        """
    
    def _create_deadline_reminder_html(self, grant_data: Dict, days_remaining: int, urgency: str) -> str:
        """Create HTML content for deadline reminder"""
        urgency_colors = {'Critical': '#dc3545', 'High': '#fd7e14', 'Medium': '#ffc107', 'Low': '#28a745'}
        color = urgency_colors.get(urgency, '#6c757d')
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: {color}; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">⏰ Deadline Reminder</h1>
                <p style="color: white; margin: 10px 0 0 0; font-size: 18px;">{days_remaining} days remaining</p>
            </div>
            
            <div style="padding: 30px; background: white; border: 1px solid #ddd; border-top: none;">
                <h2 style="color: #333; margin-top: 0;">{grant_data.get('title', 'Grant Opportunity')}</h2>
                
                <p style="color: #666; font-size: 16px; line-height: 1.6;">
                    <strong>Deadline:</strong> {grant_data.get('deadline', 'Not specified')}<br>
                    <strong>Days Remaining:</strong> {days_remaining}<br>
                    <strong>Urgency:</strong> {urgency}<br>
                    <strong>Amount:</strong> ${grant_data.get('amount_min', 0):,.0f} - ${grant_data.get('amount_max', 0):,.0f}
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background: {color}; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                        Work on Application
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_deadline_reminder_text(self, grant_data: Dict, days_remaining: int, urgency: str) -> str:
        """Create text content for deadline reminder"""
        return f"""
DEADLINE REMINDER - {urgency} Priority

{grant_data.get('title', 'Grant Opportunity')}

Deadline: {grant_data.get('deadline', 'Not specified')}
Days Remaining: {days_remaining}
Urgency: {urgency}
Amount: ${grant_data.get('amount_min', 0):,.0f} - ${grant_data.get('amount_max', 0):,.0f}

Don't miss this opportunity! Work on your application today.

Pink Lemonade - AI-Powered Grant Management
        """
    
    def _create_weekly_digest_html(self, digest_data: Dict) -> str:
        """Create HTML content for weekly digest"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #FF6B9D, #C44CAF); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">📊 Weekly Grant Digest</h1>
                <p style="color: white; margin: 10px 0 0 0;">Your personalized weekly summary</p>
            </div>
            
            <div style="padding: 30px; background: white; border: 1px solid #ddd; border-top: none;">
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center; margin: 20px 0;">
                    <div>
                        <h3 style="color: #FF6B9D; margin: 0; font-size: 36px;">{digest_data.get('new_grants', 0)}</h3>
                        <p style="color: #666; margin: 5px 0;">New Grants</p>
                    </div>
                    <div>
                        <h3 style="color: #FF6B9D; margin: 0; font-size: 36px;">{digest_data.get('high_matches', 0)}</h3>
                        <p style="color: #666; margin: 5px 0;">High Matches</p>
                    </div>
                    <div>
                        <h3 style="color: #FF6B9D; margin: 0; font-size: 36px;">{digest_data.get('applications_due', 0)}</h3>
                        <p style="color: #666; margin: 5px 0;">Due Soon</p>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background: #FF6B9D; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                        View Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_weekly_digest_text(self, digest_data: Dict) -> str:
        """Create text content for weekly digest"""
        return f"""
WEEKLY GRANT DIGEST

Your Weekly Summary:
- New Grants: {digest_data.get('new_grants', 0)}
- High Matches: {digest_data.get('high_matches', 0)}
- Applications Due Soon: {digest_data.get('applications_due', 0)}

Visit your dashboard to explore new opportunities!

Pink Lemonade - AI-Powered Grant Management
        """
    
    def _create_system_alert_html(self, alert_type: str, message: str) -> str:
        """Create HTML content for system alert"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #dc3545; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">🚨 System Alert</h1>
                <p style="color: white; margin: 10px 0 0 0;">{alert_type}</p>
            </div>
            
            <div style="padding: 30px; background: white; border: 1px solid #ddd; border-top: none;">
                <h2 style="color: #333; margin-top: 0;">Alert Details</h2>
                <p style="color: #666; line-height: 1.6;">{message}</p>
                
                <p style="color: #666; margin-top: 20px;">
                    <strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
                    <strong>System:</strong> Pink Lemonade Platform
                </p>
            </div>
        </body>
        </html>
        """
    
    def _create_system_alert_text(self, alert_type: str, message: str) -> str:
        """Create text content for system alert"""
        return f"""
SYSTEM ALERT: {alert_type}

{message}

Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
System: Pink Lemonade Platform
        """
    
    def _get_urgency_level(self, days_remaining: int) -> str:
        """Get urgency level based on days remaining"""
        if days_remaining <= 3:
            return 'Critical'
        elif days_remaining <= 7:
            return 'High'
        elif days_remaining <= 14:
            return 'Medium'
        else:
            return 'Low'