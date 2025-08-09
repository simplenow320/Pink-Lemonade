"""
Watchlist and Saved Searches API
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
from app import db
from app.models import Watchlist, Grant
from app.services.apiManager import api_manager
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('watchlist', __name__, url_prefix='/api/watchlist')

@bp.route('/searches', methods=['GET'])
def get_saved_searches():
    """Get all saved searches for current user"""
    try:
        user_id = session.get('user_id', 'default')
        
        searches = Watchlist.query.filter_by(
            user_id=user_id,
            type='search'
        ).order_by(Watchlist.created_at.desc()).all()
        
        return jsonify({
            'searches': [s.to_dict() for s in searches],
            'total': len(searches)
        })
        
    except Exception as e:
        logger.error(f"Error fetching saved searches: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/searches', methods=['POST'])
def save_search():
    """Save a new search with criteria"""
    try:
        data = request.get_json()
        user_id = session.get('user_id', 'default')
        
        # Create watchlist entry
        watchlist = Watchlist(
            user_id=user_id,
            name=data.get('name'),
            type='search',
            criteria=data.get('criteria', {}),
            notify_email=data.get('notify_email', True),
            notify_app=data.get('notify_app', True),
            frequency=data.get('frequency', 'daily'),
            is_active=True
        )
        
        db.session.add(watchlist)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'watchlist': watchlist.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error saving search: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/searches/<int:search_id>/run', methods=['POST'])
def run_saved_search(search_id):
    """Run a saved search and return results"""
    try:
        watchlist = Watchlist.query.get_or_404(search_id)
        criteria = watchlist.criteria or {}
        
        # Run search using criteria
        results = []
        sources = criteria.get('sources', ['federal_register', 'grants_gov'])
        
        for source in sources:
            params = {
                'query': criteria.get('query', ''),
                'location': criteria.get('location'),
                'keyword': criteria.get('focus_area'),
                'limit': 20
            }
            
            grants = api_manager.get_grants_from_source(source, params)
            results.extend(grants)
        
        # Update last checked time
        watchlist.last_checked = datetime.now()
        db.session.commit()
        
        return jsonify({
            'results': results,
            'total': len(results),
            'search_name': watchlist.name
        })
        
    except Exception as e:
        logger.error(f"Error running saved search: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get alert preferences"""
    try:
        user_id = session.get('user_id', 'default')
        
        alerts = Watchlist.query.filter_by(
            user_id=user_id,
            type='alert'
        ).all()
        
        preferences = {
            'email_enabled': any(a.notify_email for a in alerts),
            'app_enabled': any(a.notify_app for a in alerts),
            'sms_enabled': False,  # Implement with Twilio
            'digest_frequency': 'daily',
            'alert_types': []
        }
        
        for alert in alerts:
            preferences['alert_types'].append({
                'type': alert.name,
                'enabled': alert.is_active,
                'frequency': alert.frequency
            })
        
        return jsonify(preferences)
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/alerts', methods=['PUT'])
def update_alert_preferences():
    """Update alert preferences"""
    try:
        data = request.get_json()
        user_id = session.get('user_id', 'default')
        
        # Update or create alert preferences
        alert_types = data.get('alert_types', [])
        
        for alert_type in alert_types:
            watchlist = Watchlist.query.filter_by(
                user_id=user_id,
                type='alert',
                name=alert_type['type']
            ).first()
            
            if not watchlist:
                watchlist = Watchlist(
                    user_id=user_id,
                    type='alert',
                    name=alert_type['type']
                )
                db.session.add(watchlist)
            
            watchlist.is_active = alert_type.get('enabled', True)
            watchlist.frequency = alert_type.get('frequency', 'daily')
            watchlist.notify_email = data.get('email_enabled', True)
            watchlist.notify_app = data.get('app_enabled', True)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alert preferences updated'
        })
        
    except Exception as e:
        logger.error(f"Error updating alerts: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/digest', methods=['POST'])
def send_digest():
    """Send digest email with saved search results"""
    try:
        user_id = session.get('user_id', 'default')
        frequency = request.get_json().get('frequency', 'daily')
        
        # Get active saved searches
        searches = Watchlist.query.filter_by(
            user_id=user_id,
            type='search',
            is_active=True,
            frequency=frequency
        ).all()
        
        all_results = []
        
        for search in searches:
            criteria = search.criteria or {}
            sources = criteria.get('sources', ['federal_register'])
            
            for source in sources:
                params = {
                    'query': criteria.get('query', ''),
                    'limit': 5
                }
                
                grants = api_manager.get_grants_from_source(source, params)
                for grant in grants:
                    grant['search_name'] = search.name
                    all_results.append(grant)
        
        # Send digest (implement email service)
        from app.services.notification_service import NotificationService
        # NotificationService.send_digest(user_id, all_results)
        
        return jsonify({
            'success': True,
            'grants_found': len(all_results),
            'searches_run': len(searches)
        })
        
    except Exception as e:
        logger.error(f"Error sending digest: {e}")
        return jsonify({'error': str(e)}), 500