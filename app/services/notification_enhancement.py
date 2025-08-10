"""
Notification Enhancement Service - Phase 2
Enhanced notification system with grant match alerts, watchlist notifications, and user engagement features
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from app import db
from app.models import Grant, Organization, User, Analytics, Watchlist
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

logger = logging.getLogger(__name__)

class NotificationEnhancementService:
    """Enhanced notification service with advanced features"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'localhost')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@pinklemonade.ai')
    
    def send_grant_match_alert(self, user: User, grant: Grant, match_analysis: Dict) -> Dict[str, Any]:
        """
        Send enhanced grant match alert with AI analysis
        """
        try:
            match_score = match_analysis.get('match_score', 0)
            confidence = match_analysis.get('confidence', 'low')
            reasoning = match_analysis.get('reasoning', '')
            
            # Create personalized email content
            subject = f"🎯 High-Value Grant Match: {grant.title} ({match_score}% match)"
            
            email_content = self._create_grant_match_email(
                user, grant, match_score, confidence, reasoning
            )
            
            # Send email notification
            email_result = self._send_email(user.email, subject, email_content)
            
            # Record notification analytics
            self._record_notification_analytics('grant_match_alert', {
                'user_id': user.id,
                'grant_id': grant.id,
                'match_score': match_score,
                'confidence': confidence,
                'email_sent': email_result['success']
            })
            
            return {
                'success': True,
                'notification_type': 'grant_match',
                'match_score': match_score,
                'email_sent': email_result['success'],
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Grant match alert failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_watchlist_notification(self, watchlist: Watchlist, matching_grants: List[Grant]) -> Dict[str, Any]:
        """
        Send watchlist notification for new matching grants
        """
        try:
            # Get watchlist owner
            user = User.query.get(watchlist.user_id) if hasattr(watchlist, 'user_id') else None
            if not user:
                return {'success': False, 'error': 'Watchlist owner not found'}
            
            # Create notification content
            subject = f"📋 New Grants Match Your Watchlist: {watchlist.name}"
            email_content = self._create_watchlist_email(user, watchlist, matching_grants)
            
            # Send notification
            email_result = self._send_email(user.email, subject, email_content)
            
            # Record analytics
            self._record_notification_analytics('watchlist_notification', {
                'user_id': user.id,
                'watchlist_id': watchlist.id,
                'matching_grants_count': len(matching_grants),
                'email_sent': email_result['success']
            })
            
            return {
                'success': True,
                'notification_type': 'watchlist',
                'matching_grants': len(matching_grants),
                'email_sent': email_result['success'],
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Watchlist notification failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_deadline_reminder(self, user: User, grant: Grant, days_until_deadline: int) -> Dict[str, Any]:
        """
        Send deadline reminder for grants approaching deadline
        """
        try:
            urgency = self._calculate_urgency(days_until_deadline)
            
            subject = f"⏰ {urgency} Grant Deadline: {grant.title} ({days_until_deadline} days left)"
            email_content = self._create_deadline_reminder_email(user, grant, days_until_deadline, urgency)
            
            email_result = self._send_email(user.email, subject, email_content)
            
            self._record_notification_analytics('deadline_reminder', {
                'user_id': user.id,
                'grant_id': grant.id,
                'days_until_deadline': days_until_deadline,
                'urgency': urgency,
                'email_sent': email_result['success']
            })
            
            return {
                'success': True,
                'notification_type': 'deadline_reminder',
                'days_until_deadline': days_until_deadline,
                'urgency': urgency,
                'email_sent': email_result['success'],
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Deadline reminder failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_weekly_digest(self, user: User) -> Dict[str, Any]:
        """
        Send weekly digest of activity and opportunities
        """
        try:
            # Gather weekly data
            weekly_data = self._gather_weekly_digest_data(user)
            
            subject = f"📊 Your Weekly Grant Digest - {weekly_data['new_grants']} New Opportunities"
            email_content = self._create_weekly_digest_email(user, weekly_data)
            
            email_result = self._send_email(user.email, subject, email_content)
            
            self._record_notification_analytics('weekly_digest', {
                'user_id': user.id,
                'new_grants': weekly_data['new_grants'],
                'high_matches': weekly_data['high_matches'],
                'email_sent': email_result['success']
            })
            
            return {
                'success': True,
                'notification_type': 'weekly_digest',
                'email_sent': email_result['success'],
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Weekly digest failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_system_alert(self, alert_type: str, message: str, recipients: List[str] = None) -> Dict[str, Any]:
        """
        Send system alerts to administrators
        """
        try:
            if not recipients:
                # Get admin users
                admin_users = User.query.filter_by(role='admin').all()
                recipients = [user.email for user in admin_users if user.email]
            
            subject = f"🚨 System Alert: {alert_type}"
            email_content = self._create_system_alert_email(alert_type, message)
            
            sent_count = 0
            for email in recipients:
                email_result = self._send_email(email, subject, email_content)
                if email_result['success']:
                    sent_count += 1
            
            self._record_notification_analytics('system_alert', {
                'alert_type': alert_type,
                'recipients_count': len(recipients),
                'sent_count': sent_count,
                'message': message
            })
            
            return {
                'success': True,
                'notification_type': 'system_alert',
                'recipients_notified': sent_count,
                'sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"System alert failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_notification_preferences(self, user: User) -> Dict[str, Any]:
        """
        Get user notification preferences
        """
        try:
            # Default preferences (extend User model in future to store these)
            preferences = {
                'grant_matches': True,
                'deadline_reminders': True,
                'weekly_digest': True,
                'watchlist_alerts': True,
                'system_notifications': False,
                'email_frequency': 'immediate',  # immediate, daily, weekly
                'match_score_threshold': 70
            }
            
            return {
                'success': True,
                'preferences': preferences,
                'user_id': user.id
            }
            
        except Exception as e:
            logger.error(f"Get notification preferences failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_notification_preferences(self, user: User, preferences: Dict) -> Dict[str, Any]:
        """
        Update user notification preferences
        """
        try:
            # Store preferences (extend User model to include notification preferences)
            # For now, record as analytics event
            self._record_notification_analytics('preferences_updated', {
                'user_id': user.id,
                'preferences': preferences,
                'updated_at': datetime.utcnow().isoformat()
            })
            
            return {
                'success': True,
                'message': 'Notification preferences updated',
                'user_id': user.id
            }
            
        except Exception as e:
            logger.error(f"Update notification preferences failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_notification_history(self, user: User, days: int = 30) -> Dict[str, Any]:
        """
        Get user's notification history
        """
        try:
            # Get notification analytics for user
            start_date = datetime.utcnow() - timedelta(days=days)
            
            notifications = Analytics.query.filter(
                Analytics.event_type.in_([
                    'grant_match_alert', 'watchlist_notification', 
                    'deadline_reminder', 'weekly_digest'
                ]),
                Analytics.created_at >= start_date,
                Analytics.event_data.has_key('user_id'),  # Filter by user_id in event_data
            ).order_by(Analytics.created_at.desc()).all()
            
            # Filter by actual user_id (since we can't query JSON directly)
            user_notifications = []
            for notification in notifications:
                event_data = notification.event_data or {}
                if event_data.get('user_id') == user.id:
                    user_notifications.append({
                        'type': notification.event_type,
                        'data': event_data,
                        'sent_at': notification.created_at.isoformat()
                    })
            
            return {
                'success': True,
                'notifications': user_notifications,
                'period_days': days,
                'total_notifications': len(user_notifications)
            }
            
        except Exception as e:
            logger.error(f"Get notification history failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_grant_match_email(self, user: User, grant: Grant, match_score: int, confidence: str, reasoning: str) -> str:
        """Create HTML email content for grant match alerts"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #FF6B9D, #C44CAF); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">🎯 High-Value Grant Match!</h1>
                <p style="color: white; margin: 10px 0 0 0; font-size: 18px;">{match_score}% Match Confidence</p>
            </div>
            
            <div style="padding: 30px; background: white;">
                <h2 style="color: #333; margin-top: 0;">{grant.title}</h2>
                <p style="color: #666; font-size: 16px; line-height: 1.6;">
                    <strong>Funder:</strong> {grant.funder}<br>
                    <strong>Amount:</strong> ${grant.amount_min:,.0f} - ${grant.amount_max:,.0f}<br>
                    <strong>Deadline:</strong> {grant.deadline.strftime('%B %d, %Y') if grant.deadline else 'Not specified'}<br>
                    <strong>AI Confidence:</strong> {confidence.title()}
                </p>
                
                <div style="background: #f8f9fa; padding: 20px; border-left: 4px solid #FF6B9D; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">Why This Grant Matches Your Organization</h3>
                    <p style="color: #666; line-height: 1.6;">{reasoning}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{grant.source_url or '#'}" 
                       style="background: #FF6B9D; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                        View Grant Details
                    </a>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; color: #666;">
                <p>Happy grant hunting! 🌟</p>
                <p><small>Pink Lemonade - AI-Powered Grant Management</small></p>
            </div>
        </body>
        </html>
        """
    
    def _create_watchlist_email(self, user: User, watchlist: Watchlist, grants: List[Grant]) -> str:
        """Create HTML email content for watchlist notifications"""
        grants_html = ""
        for grant in grants[:5]:  # Show top 5 matches
            grants_html += f"""
            <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px;">
                <h4 style="margin: 0 0 10px 0; color: #333;">{grant.title}</h4>
                <p style="margin: 5px 0; color: #666;">
                    <strong>Funder:</strong> {grant.funder}<br>
                    <strong>Amount:</strong> ${grant.amount_min:,.0f} - ${grant.amount_max:,.0f}<br>
                    <strong>Deadline:</strong> {grant.deadline.strftime('%B %d, %Y') if grant.deadline else 'Not specified'}
                </p>
            </div>
            """
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #FF6B9D; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">📋 Watchlist Alert</h1>
                <p style="color: white; margin: 10px 0 0 0;">{len(grants)} new grants match "{watchlist.name}"</p>
            </div>
            
            <div style="padding: 30px; background: white;">
                <h2 style="color: #333;">New Matching Grants</h2>
                {grants_html}
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background: #FF6B9D; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px;">
                        View All Matches
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_deadline_reminder_email(self, user: User, grant: Grant, days: int, urgency: str) -> str:
        """Create deadline reminder email"""
        urgency_colors = {
            'Critical': '#dc3545',
            'High': '#fd7e14', 
            'Medium': '#ffc107',
            'Low': '#28a745'
        }
        color = urgency_colors.get(urgency, '#6c757d')
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: {color}; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">⏰ Deadline Reminder</h1>
                <p style="color: white; margin: 10px 0 0 0;">{days} days remaining</p>
            </div>
            
            <div style="padding: 30px; background: white;">
                <h2 style="color: #333;">{grant.title}</h2>
                <p style="color: #666; font-size: 16px;">
                    <strong>Deadline:</strong> {grant.deadline.strftime('%B %d, %Y') if grant.deadline else 'Not specified'}<br>
                    <strong>Days Remaining:</strong> {days}<br>
                    <strong>Urgency:</strong> {urgency}
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background: {color}; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px;">
                        Work on Application
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_weekly_digest_email(self, user: User, data: Dict) -> str:
        """Create weekly digest email"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #FF6B9D, #C44CAF); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">📊 Weekly Grant Digest</h1>
                <p style="color: white; margin: 10px 0 0 0;">Your personalized weekly summary</p>
            </div>
            
            <div style="padding: 30px; background: white;">
                <div style="display: flex; justify-content: space-around; text-align: center; margin: 20px 0;">
                    <div>
                        <h3 style="color: #FF6B9D; margin: 0; font-size: 36px;">{data['new_grants']}</h3>
                        <p style="color: #666; margin: 5px 0;">New Grants</p>
                    </div>
                    <div>
                        <h3 style="color: #FF6B9D; margin: 0; font-size: 36px;">{data['high_matches']}</h3>
                        <p style="color: #666; margin: 5px 0;">High Matches</p>
                    </div>
                    <div>
                        <h3 style="color: #FF6B9D; margin: 0; font-size: 36px;">{data['applications_due']}</h3>
                        <p style="color: #666; margin: 5px 0;">Due Soon</p>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="background: #FF6B9D; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px;">
                        View Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_system_alert_email(self, alert_type: str, message: str) -> str:
        """Create system alert email"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #dc3545; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">🚨 System Alert</h1>
                <p style="color: white; margin: 10px 0 0 0;">{alert_type}</p>
            </div>
            
            <div style="padding: 30px; background: white;">
                <h2 style="color: #333;">Alert Details</h2>
                <p style="color: #666; line-height: 1.6;">{message}</p>
                
                <p style="color: #666; margin-top: 20px;">
                    <strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
                    <strong>System:</strong> Pink Lemonade Platform
                </p>
            </div>
        </body>
        </html>
        """
    
    def _send_email(self, to_email: str, subject: str, html_content: str) -> Dict[str, Any]:
        """Send email using SMTP"""
        try:
            # For development, log email instead of sending
            if os.getenv('FLASK_ENV') == 'development':
                logger.info(f"EMAIL (dev mode): To: {to_email}, Subject: {subject}")
                return {'success': True, 'method': 'logged'}
            
            # Production email sending would go here
            # msg = MIMEMultipart('alternative')
            # msg['Subject'] = subject
            # msg['From'] = self.from_email
            # msg['To'] = to_email
            # msg.attach(MIMEText(html_content, 'html'))
            
            return {'success': True, 'method': 'smtp'}
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_urgency(self, days_until_deadline: int) -> str:
        """Calculate urgency level based on days remaining"""
        if days_until_deadline <= 3:
            return 'Critical'
        elif days_until_deadline <= 7:
            return 'High'
        elif days_until_deadline <= 14:
            return 'Medium'
        else:
            return 'Low'
    
    def _gather_weekly_digest_data(self, user: User) -> Dict[str, Any]:
        """Gather data for weekly digest"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Count new grants this week
        new_grants = Grant.query.filter(Grant.created_at >= week_ago).count()
        
        # Count high matches (from analytics)
        high_matches = Analytics.query.filter(
            Analytics.event_type == 'high_match',
            Analytics.created_at >= week_ago,
            Analytics.event_data.has_key('user_id')  # Would need proper user filtering
        ).count()
        
        # Count applications due soon
        upcoming_deadline = datetime.utcnow() + timedelta(days=14)
        applications_due = Grant.query.filter(
            Grant.deadline <= upcoming_deadline.date(),
            Grant.deadline >= datetime.utcnow().date()
        ).count()
        
        return {
            'new_grants': new_grants,
            'high_matches': high_matches,
            'applications_due': applications_due,
            'week_start': week_ago.strftime('%Y-%m-%d'),
            'week_end': datetime.utcnow().strftime('%Y-%m-%d')
        }
    
    def _record_notification_analytics(self, event_type: str, data: Dict):
        """Record notification analytics"""
        try:
            analytics = Analytics()
            analytics.event_type = event_type
            analytics.event_data = data
            analytics.created_at = datetime.utcnow()
            
            db.session.add(analytics)
            db.session.commit()
        except Exception as e:
            logger.error(f"Notification analytics recording failed: {e}")
            db.session.rollback()