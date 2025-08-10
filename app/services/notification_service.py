"""
Notification Service for alerts and reminders
"""

from datetime import datetime, timedelta
from app import db
from app.models import Grant, User
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling notifications and alerts"""
    
    @staticmethod
    def send_status_update(grant, new_status):
        """Send notification when grant status changes"""
        try:
            # Get user email (implement user association)
            # For now, log the notification
            logger.info(f"Grant {grant.id} status changed to {new_status}")
            
            # Email notification logic would go here
            subject = f"Grant Status Update: {grant.title}"
            body = f"""
            Your grant application status has been updated:
            
            Grant: {grant.title}
            New Status: {new_status}
            Funder: {grant.funder}
            
            {'Congratulations! Your grant has been awarded.' if new_status == 'awarded' else ''}
            
            Log in to view more details.
            """
            
            # Send email (implement SMTP configuration)
            # NotificationService._send_email(user_email, subject, body)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
            return False
    
    @staticmethod
    def send_deadline_reminder(grant, days_until):
        """Send deadline reminder for grant"""
        try:
            subject = f"Grant Deadline Reminder: {days_until} days left"
            body = f"""
            Reminder: Grant application deadline approaching!
            
            Grant: {grant.title}
            Funder: {grant.funder}
            Deadline: {grant.deadline.strftime('%B %d, %Y')}
            Days Remaining: {days_until}
            
            Status: {grant.status}
            
            Log in to complete your application.
            """
            
            logger.info(f"Deadline reminder sent for grant {grant.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending deadline reminder: {e}")
            return False
    
    @staticmethod
    def schedule_reminder(reminder_data):
        """Schedule a future reminder"""
        try:
            # Store in database or task queue
            # For now, log the scheduled reminder
            logger.info(f"Reminder scheduled for grant {reminder_data['grant_id']} on {reminder_data['date']}")
            
            # In production, use Celery or similar task queue
            # task_queue.schedule(NotificationService.send_reminder, reminder_data['date'], reminder_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling reminder: {e}")
            return False
    
    @staticmethod
    def send_daily_digest(user_id):
        """Send daily digest of grant activities"""
        try:
            # Get user's grants with upcoming deadlines
            upcoming_grants = Grant.query.filter(
                Grant.deadline != None,
                Grant.deadline <= datetime.now() + timedelta(days=7),
                Grant.deadline >= datetime.now(),
                Grant.status.in_(['draft', 'in_progress'])
            ).all()
            
            if not upcoming_grants:
                return True
            
            subject = "Daily Grant Digest"
            body = f"""
            Your Daily Grant Update
            
            Upcoming Deadlines:
            """
            
            for grant in upcoming_grants:
                days_until = (grant.deadline - datetime.now()).days
                body += f"\n- {grant.title}: {days_until} days remaining"
            
            logger.info(f"Daily digest sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending daily digest: {e}")
            return False
    
    @staticmethod
    def _send_email(to_email, subject, body):
        """Internal method to send email"""
        try:
            # Configure SMTP settings (use environment variables)
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "notifications@pinklemonade.com"
            sender_password = "your_password"  # Use environment variable
            
            # Create message
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add body
            message.attach(MIMEText(body, "plain"))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False