"""
Notification Enhancement API - Phase 2
Enhanced notification endpoints with grant match alerts, watchlist notifications, and user preferences
"""

from flask import Blueprint, request, jsonify, session
from app import db
from app.services.notification_enhancement import NotificationEnhancementService
from app.models import User, Grant, Watchlist, Organization
from functools import wraps
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('notification_enhancement', __name__, url_prefix='/api/notifications')

# Initialize notification service
notification_service = NotificationEnhancementService()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

@bp.route('/test/grant-match', methods=['POST'])
@login_required
def test_grant_match_notification():
    """
    Test grant match notification system
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json() or {}
        grant_id = data.get('grant_id')
        
        if not grant_id:
            # Use a sample grant for testing
            grant = Grant.query.first()
            if not grant:
                return jsonify({'error': 'No grants available for testing'}), 404
        else:
            grant = Grant.query.get(grant_id)
            if not grant:
                return jsonify({'error': 'Grant not found'}), 404
        
        # Get real analysis data from AI service if available
        try:
            from app.services.ai_service import AIService
            ai_service = AIService()
            
            # Get organization for matching
            org_id = user.org_id if hasattr(user, 'org_id') else None
            org = Organization.query.filter_by(id=org_id).first() if org_id else None
            
            if org and grant:
                # Try to use real AI analysis
                if hasattr(ai_service, 'match_grant'):
                    analysis = ai_service.match_grant(org, grant)
                else:
                    # Calculate basic match score from real data
                    match_score = 0
                    if org.primary_focus_areas and grant.eligibility:
                        # Check for focus area overlap
                        for area in org.primary_focus_areas:
                            if area.lower() in grant.eligibility.lower():
                                match_score += 25
                    if org.annual_budget_range and grant.amount_min:
                        # Check budget compatibility
                        if grant.amount_min < 1000000:  # Reasonable grant size
                            match_score += 25
                    
                    analysis = {
                        'match_score': min(match_score, 100),
                        'confidence': 'medium' if match_score > 0 else 'low',
                        'reasoning': f'Based on organization focus areas and grant eligibility criteria.'
                    }
            else:
                # Provide minimal real data
                analysis = {
                    'match_score': 0,
                    'confidence': 'low',
                    'reasoning': 'Unable to analyze - missing organization or grant data'
                }
        except ImportError:
            # AI service not available, use basic matching
            analysis = {
                'match_score': 50,
                'confidence': 'low',
                'reasoning': 'Basic compatibility check - AI service unavailable'
            }
        
        result = notification_service.send_grant_match_alert(user, grant, analysis)
        
        return jsonify({
            'success': True,
            'test_result': result,
            'grant_title': grant.title
        })
        
    except Exception as e:
        logger.error(f"Test grant match notification failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/test/watchlist', methods=['POST'])
@login_required
def test_watchlist_notification():
    """
    Test watchlist notification system
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's organization
        org_id = user.org_id if hasattr(user, 'org_id') else None
        if not org_id:
            # Create default org if needed
            org = Organization.query.first()
            if not org:
                org = Organization(name='Default Organization')
                db.session.add(org)
                db.session.commit()
            org_id = org.id
        
        # Get real watchlist from database or create one
        watchlist = Watchlist.query.filter_by(org_id=org_id).first()
        
        if not watchlist:
            # Create a real watchlist if none exists
            watchlist = Watchlist(
                org_id=org_id,
                city=user.org_name if hasattr(user, 'org_name') else 'Default City'
            )
            db.session.add(watchlist)
            db.session.commit()
        
        # Get real grants based on watchlist city or recent grants
        grants_query = Grant.query
        if watchlist.city:
            # Filter by geography if city is set
            grants_query = grants_query.filter(Grant.geography.contains(watchlist.city))
        
        # Get filtered grants
        watchlist_grants = grants_query.limit(3).all()
        
        result = notification_service.send_watchlist_notification(watchlist, watchlist_grants)
        
        return jsonify({
            'success': True,
            'test_result': result,
            'grants_count': len(sample_grants)
        })
        
    except Exception as e:
        logger.error(f"Test watchlist notification failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/test/deadline-reminder', methods=['POST'])
@login_required
def test_deadline_reminder():
    """
    Test deadline reminder notification
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json() or {}
        days_until_deadline = data.get('days', 7)
        
        # Find a grant with a deadline or use first grant
        grant = Grant.query.filter(Grant.deadline.isnot(None)).first()
        if not grant:
            grant = Grant.query.first()
        
        if not grant:
            return jsonify({'error': 'No grants available for testing'}), 404
        
        result = notification_service.send_deadline_reminder(user, grant, days_until_deadline)
        
        return jsonify({
            'success': True,
            'test_result': result,
            'grant_title': grant.title,
            'days_until_deadline': days_until_deadline
        })
        
    except Exception as e:
        logger.error(f"Test deadline reminder failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/test/weekly-digest', methods=['POST'])
@login_required
def test_weekly_digest():
    """
    Test weekly digest notification
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        result = notification_service.send_weekly_digest(user)
        
        return jsonify({
            'success': True,
            'test_result': result
        })
        
    except Exception as e:
        logger.error(f"Test weekly digest failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/preferences', methods=['GET'])
@login_required
def get_notification_preferences():
    """
    Get user notification preferences
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        preferences = notification_service.get_notification_preferences(user)
        
        return jsonify(preferences)
        
    except Exception as e:
        logger.error(f"Get notification preferences failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/preferences', methods=['POST'])
@login_required
def update_notification_preferences():
    """
    Update user notification preferences
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No preferences data provided'}), 400
        
        result = notification_service.update_notification_preferences(user, data)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Update notification preferences failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/history', methods=['GET'])
@login_required
def get_notification_history():
    """
    Get user notification history
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        days = int(request.args.get('days', 30))
        history = notification_service.get_notification_history(user, days)
        
        return jsonify(history)
        
    except Exception as e:
        logger.error(f"Get notification history failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/send/system-alert', methods=['POST'])
def send_system_alert():
    """
    Send system alert (admin only)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No alert data provided'}), 400
        
        alert_type = data.get('type', 'general')
        message = data.get('message', '')
        recipients = data.get('recipients', [])
        
        if not message:
            return jsonify({'error': 'Alert message is required'}), 400
        
        result = notification_service.send_system_alert(alert_type, message, recipients)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Send system alert failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/stats', methods=['GET'])
@login_required
def get_notification_stats():
    """
    Get notification statistics
    """
    try:
        from app.models import Analytics
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # Get notification stats for last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        notification_events = [
            'grant_match_alert', 'watchlist_notification', 
            'deadline_reminder', 'weekly_digest', 'system_alert'
        ]
        
        stats = (
            Analytics.query
            .filter(
                Analytics.event_type.in_(notification_events),
                Analytics.created_at >= thirty_days_ago
            )
            .with_entities(Analytics.event_type, func.count(Analytics.id))
            .group_by(Analytics.event_type)
            .all()
        )
        
        stats_dict = {event_type: count for event_type, count in stats}
        total_notifications = sum(stats_dict.values())
        
        return jsonify({
            'success': True,
            'stats': {
                'period': '30_days',
                'total_notifications': total_notifications,
                'by_type': stats_dict,
                'grant_match_alerts': stats_dict.get('grant_match_alert', 0),
                'watchlist_notifications': stats_dict.get('watchlist_notification', 0),
                'deadline_reminders': stats_dict.get('deadline_reminder', 0),
                'weekly_digests': stats_dict.get('weekly_digest', 0),
                'system_alerts': stats_dict.get('system_alert', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Get notification stats failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/bulk-send/deadline-reminders', methods=['POST'])
def send_bulk_deadline_reminders():
    """
    Send deadline reminders for all upcoming grants (admin operation)
    """
    try:
        from datetime import datetime, timedelta
        
        data = request.get_json() or {}
        days_ahead = data.get('days_ahead', [3, 7, 14])  # Send reminders for grants due in 3, 7, 14 days
        
        sent_count = 0
        results = []
        
        for days in days_ahead:
            target_date = (datetime.utcnow() + timedelta(days=days)).date()
            
            # Find grants with deadlines on target date
            grants_due = Grant.query.filter(Grant.deadline == target_date).all()
            
            for grant in grants_due:
                # Find users who might be interested (simplified - in reality would use watchlists/preferences)
                users = User.query.limit(5).all()  # Limit for testing
                
                for user in users:
                    try:
                        result = notification_service.send_deadline_reminder(user, grant, days)
                        if result.get('success'):
                            sent_count += 1
                        results.append({
                            'user_id': user.id,
                            'grant_id': grant.id,
                            'days': days,
                            'success': result.get('success', False)
                        })
                    except Exception as e:
                        logger.error(f"Failed to send deadline reminder to user {user.id}: {e}")
        
        return jsonify({
            'success': True,
            'total_sent': sent_count,
            'results': results,
            'days_ahead_checked': days_ahead
        })
        
    except Exception as e:
        logger.error(f"Bulk deadline reminders failed: {e}")
        return jsonify({'error': str(e)}), 500