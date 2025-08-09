"""
Dashboard API endpoints for CRM functionality
"""

from flask import Blueprint, jsonify, session, request
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_
import logging
from app import db
from app.models.grant import Grant
from app.models.watchlist import Watchlist
from app.models.organization import Organization

logger = logging.getLogger(__name__)

# Create Blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    """Get key performance metrics for the dashboard"""
    try:
        import os
        data_mode = os.environ.get('APP_DATA_MODE', 'MOCK')
        org_id = session.get('org_id', 'org-001')
        
        # Get all grants for the organization
        grants = Grant.query.filter_by(org_id=org_id).all()
        
        # Calculate metrics from real data
        total_grants = len(grants)
        
        # Funds Applied For (submitted, won, or declined)
        applied_grants = [g for g in grants if g.status in ['submitted', 'won', 'declined']]
        funds_applied = sum([
            g.amount or g.amount_max or 0 
            for g in applied_grants
        ])
        
        # Funds Won
        won_grants = [g for g in grants if g.status == 'won']
        funds_won = sum([
            g.amount or g.amount_max or 0 
            for g in won_grants
        ])
        
        # Win Rate
        decided_grants = [g for g in grants if g.status in ['won', 'declined']]
        win_rate = 0
        if decided_grants:
            win_rate = (len(won_grants) / len(decided_grants)) * 100
        
        # Additional metrics
        active_grants = [g for g in grants if g.status not in ['won', 'declined', 'abandoned']]
        upcoming_deadlines = [
            g for g in active_grants 
            if g.due_date and g.due_date > datetime.now().date() 
            and g.due_date <= (datetime.now() + timedelta(days=30)).date()
        ]
        
        # Build metrics based on data mode
        if data_mode == 'LIVE':
            # LIVE mode: only return real data, no fallbacks
            metrics = {
                'totalGrants': total_grants if total_grants > 0 else None,
                'activeGrants': len(active_grants) if len(active_grants) > 0 else None,
                'fundsApplied': funds_applied if funds_applied > 0 else None,
                'fundsWon': funds_won if funds_won > 0 else None,
                'winRate': win_rate if decided_grants else None,
                'upcomingDeadlines': len(upcoming_deadlines),
                'submittedGrants': len([g for g in grants if g.status == 'submitted']),
                'wonGrants': len(won_grants)
            }
        else:
            # MOCK mode: provide demo data for better UX
            metrics = {
                'totalGrants': total_grants if total_grants > 0 else 12,
                'activeGrants': len(active_grants) if len(active_grants) > 0 else 8,
                'fundsApplied': funds_applied if funds_applied > 0 else 450000,
                'fundsWon': funds_won if funds_won > 0 else 125000,
                'winRate': win_rate if decided_grants else 28,
                'upcomingDeadlines': len(upcoming_deadlines) if len(upcoming_deadlines) > 0 else 3,
                'submittedGrants': len([g for g in grants if g.status == 'submitted']) or 4,
                'wonGrants': len(won_grants) if len(won_grants) > 0 else 2
            }
        
        # Cache metrics for faster subsequent loads
        session['cached_metrics'] = metrics
        session['metrics_timestamp'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'dataMode': data_mode
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'metrics': {
                'totalGrants': None,
                'activeGrants': None,
                'fundsApplied': None,
                'fundsWon': None,
                'winRate': None,
                'upcomingDeadlines': 0,
                'submittedGrants': 0,
                'wonGrants': 0
            }
        }), 500


@dashboard_bp.route('/api/dashboard/recent-activity', methods=['GET'])
def get_recent_activity():
    """Get recent activity feed items"""
    try:
        org_id = session.get('org_id', 'org-001')
        limit = int(request.args.get('limit', 10))
        
        activities = []
        
        # Get recently updated grants
        recent_grants = Grant.query.filter_by(org_id=org_id)\
            .order_by(desc(Grant.updated_at))\
            .limit(5)\
            .all()
        
        for grant in recent_grants:
            # Check if grant was recently added (created within last 7 days)
            if grant.created_at and (datetime.now() - grant.created_at).days <= 7:
                activities.append({
                    'type': 'grant_added',
                    'description': f'New grant added: {grant.title}',
                    'timestamp': grant.created_at.isoformat(),
                    'grantId': grant.id
                })
            elif grant.updated_at != grant.created_at:
                # Grant was updated
                activities.append({
                    'type': 'grant_updated',
                    'description': f'Grant updated: {grant.title}',
                    'timestamp': grant.updated_at.isoformat() if grant.updated_at else datetime.now().isoformat(),
                    'grantId': grant.id
                })
        
        # Check for approaching deadlines
        upcoming_grants = Grant.query.filter(
            and_(
                Grant.org_id == org_id,
                Grant.due_date != None,
                Grant.due_date >= datetime.now().date(),
                Grant.due_date <= (datetime.now() + timedelta(days=7)).date(),
                Grant.status.notin_(['won', 'declined', 'abandoned'])
            )
        ).all()
        
        for grant in upcoming_grants:
            days_until = (grant.due_date - datetime.now().date()).days
            activities.append({
                'type': 'deadline_approaching',
                'description': f'Deadline in {days_until} day{"s" if days_until != 1 else ""}: {grant.title}',
                'timestamp': datetime.now().isoformat(),
                'grantId': grant.id,
                'priority': 'high'
            })
        
        # Check for recent status changes
        status_changed_grants = Grant.query.filter(
            and_(
                Grant.org_id == org_id,
                Grant.updated_at != None,
                Grant.updated_at >= datetime.now() - timedelta(days=3)
            )
        ).all()
        
        for grant in status_changed_grants:
            if grant.status and grant.updated_at != grant.created_at:
                activities.append({
                    'type': 'status_changed',
                    'description': f'Status updated to "{grant.status.title()}" for {grant.title}',
                    'timestamp': grant.updated_at.isoformat() if grant.updated_at else datetime.now().isoformat(),
                    'grantId': grant.id
                })
        
        # Check for watchlist alerts
        watchlists = Watchlist.query.filter_by(org_id=org_id).all()
        for watchlist in watchlists:
            # Check if watchlist was recently run
            if watchlist.last_run and (datetime.now() - watchlist.last_run).days <= 1:
                # Count new opportunities (this is a simplified check)
                activities.append({
                    'type': 'watchlist_alert',
                    'description': f'Watchlist checked: {watchlist.city}',
                    'timestamp': watchlist.last_run.isoformat(),
                    'watchlistId': watchlist.id
                })
        
        # Sort activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limit to requested number
        activities = activities[:limit]
        
        return jsonify({
            'success': True,
            'activities': activities
        })
        
    except Exception as e:
        logger.error(f"Error fetching recent activity: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'activities': []
        }), 500


@dashboard_bp.route('/api/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """Get complete dashboard summary including all sections"""
    try:
        org_id = session.get('org_id', 'org-001')
        
        # Get metrics
        metrics_response = get_dashboard_metrics()
        if isinstance(metrics_response, tuple):
            metrics_data = metrics_response[0].get_json()
        else:
            metrics_data = metrics_response.get_json()
        
        # Get recent activity
        activity_response = get_recent_activity()
        if isinstance(activity_response, tuple):
            activity_data = activity_response[0].get_json()
        else:
            activity_data = activity_response.get_json()
        
        # Get watchlists with new opportunity counts
        watchlists = Watchlist.query.filter_by(org_id=org_id).all()
        watchlist_data = []
        
        for watchlist in watchlists:
            # Count opportunities discovered since last login (simplified)
            new_opportunities = 0
            if watchlist.last_run:
                # Count grants discovered after last run
                new_grants = Grant.query.filter(
                    and_(
                        Grant.org_id == org_id,
                        Grant.discovered_at != None,
                        Grant.discovered_at >= watchlist.last_run,
                        Grant.source_name != None
                    )
                ).count()
                new_opportunities = new_grants
            
            watchlist_data.append({
                'id': watchlist.id,
                'city': watchlist.city,
                'sources': watchlist.sources or [],
                'enabled': watchlist.enabled,
                'lastRun': watchlist.last_run.isoformat() if watchlist.last_run else None,
                'newOpportunities': new_opportunities
            })
        
        # Get upcoming grants (top 5 by deadline)
        upcoming_grants = Grant.query.filter(
            and_(
                Grant.org_id == org_id,
                Grant.status.notin_(['won', 'declined', 'abandoned']),
                or_(Grant.due_date != None, Grant.deadline != None)
            )
        ).order_by(
            func.coalesce(Grant.due_date, Grant.deadline)
        ).limit(5).all()
        
        grants_data = [g.to_dict() for g in upcoming_grants]
        
        return jsonify({
            'success': True,
            'summary': {
                'metrics': metrics_data.get('metrics', {}),
                'activities': activity_data.get('activities', []),
                'watchlists': watchlist_data,
                'upcomingGrants': grants_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/api/dashboard/cache/clear', methods=['POST'])
def clear_dashboard_cache():
    """Clear cached dashboard data to force refresh"""
    try:
        # Clear session cache
        if 'cached_metrics' in session:
            del session['cached_metrics']
        if 'metrics_timestamp' in session:
            del session['metrics_timestamp']
        
        return jsonify({
            'success': True,
            'message': 'Dashboard cache cleared'
        })
        
    except Exception as e:
        logger.error(f"Error clearing dashboard cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500