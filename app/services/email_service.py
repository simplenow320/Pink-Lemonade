"""Email Service for Pink Lemonade Platform"""
import os
import logging
from flask import current_app, url_for

# For now, we'll log emails since we don't have SendGrid configured
# In production, you would use SendGrid or another email service

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.from_email = 'noreply@pinklemonade.app'
        self.from_name = 'Pink Lemonade'
        self.base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
        
    def send_verification_email(self, to_email, first_name, token):
        """Send email verification link"""
        verification_url = f"{self.base_url}/verify-email?token={token}"
        
        subject = "Verify Your Pink Lemonade Account"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #B8899A 0%, #A67989 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #B8899A; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Pink Lemonade!</h1>
                </div>
                <div class="content">
                    <p>Hi {first_name},</p>
                    <p>Thank you for creating an account with Pink Lemonade. To get started, please verify your email address by clicking the button below:</p>
                    <center>
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </center>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="background: #f5f5f5; padding: 10px; word-break: break-all;">{verification_url}</p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't create an account with Pink Lemonade, you can safely ignore this email.</p>
                    <p>Best regards,<br>The Pink Lemonade Team</p>
                </div>
                <div class="footer">
                    <p>© 2025 Pink Lemonade. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Log the email for development
        logger.info(f"[EMAIL] Verification email to {to_email}")
        logger.info(f"[EMAIL] Verification URL: {verification_url}")
        
        # In production, send via SendGrid:
        # self._send_email(to_email, subject, html_content)
        
        return True
    
    def send_password_reset_email(self, to_email, first_name, token):
        """Send password reset email"""
        reset_url = f"{self.base_url}/reset-password?token={token}"
        
        subject = "Reset Your Pink Lemonade Password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #B8899A 0%, #A67989 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #B8899A; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 4px; margin: 15px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hi {first_name},</p>
                    <p>We received a request to reset your Pink Lemonade password. Click the button below to create a new password:</p>
                    <center>
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </center>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="background: #f5f5f5; padding: 10px; word-break: break-all;">{reset_url}</p>
                    <div class="warning">
                        <strong>⚠️ This link will expire in 1 hour for security reasons.</strong>
                    </div>
                    <p>If you didn't request a password reset, you can safely ignore this email. Your password won't be changed.</p>
                    <p>Best regards,<br>The Pink Lemonade Team</p>
                </div>
                <div class="footer">
                    <p>© 2025 Pink Lemonade. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Log the email for development
        logger.info(f"[EMAIL] Password reset email to {to_email}")
        logger.info(f"[EMAIL] Reset URL: {reset_url}")
        
        # In production, send via SendGrid:
        # self._send_email(to_email, subject, html_content)
        
        return True
    
    def send_welcome_email(self, to_email, first_name):
        """Send welcome email after successful verification"""
        subject = "Welcome to Pink Lemonade - Let's Get Started!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #B8899A 0%, #A67989 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 8px 8px; }}
                .feature {{ margin: 20px 0; padding: 15px; background: #f9f9f9; border-left: 4px solid #B8899A; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #B8899A; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Pink Lemonade!</h1>
                </div>
                <div class="content">
                    <p>Hi {first_name},</p>
                    <p>Your email has been verified and your account is now active! Here's how to get started:</p>
                    
                    <div class="feature">
                        <strong>1. Complete Your Profile</strong><br>
                        Add your organization's mission, focus areas, and upload your 501(c)(3) documentation.
                    </div>
                    
                    <div class="feature">
                        <strong>2. Discover Grants</strong><br>
                        Browse thousands of grant opportunities matched to your organization's needs.
                    </div>
                    
                    <div class="feature">
                        <strong>3. Use AI Writing Tools</strong><br>
                        Generate compelling narratives, case statements, and grant proposals with our AI assistant.
                    </div>
                    
                    <center>
                        <a href="{self.base_url}/dashboard" class="button">Go to Dashboard</a>
                    </center>
                    
                    <p>If you have any questions, our support team is here to help!</p>
                    <p>Best regards,<br>The Pink Lemonade Team</p>
                </div>
                <div class="footer">
                    <p>© 2025 Pink Lemonade. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Log the email for development
        logger.info(f"[EMAIL] Welcome email to {to_email}")
        
        # In production, send via SendGrid:
        # self._send_email(to_email, subject, html_content)
        
        return True
    
    def _send_email(self, to_email, subject, html_content):
        """Internal method to send email via SendGrid (placeholder)"""
        # This would integrate with SendGrid API
        # For now, we just log the email
        pass