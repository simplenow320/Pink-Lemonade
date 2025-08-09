"""
API routes for discovery connectors and watchlists
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import logging
from app import db
from app.models.watchlist import Watchlist
from app.models.grant import Grant
from app.services.discovery import discovery_service

logger = logging.getLogger(__name__)

discovery_bp = Blueprint('discovery', __name__)


@discovery_bp.route('/api/discovery/run', methods=['POST'])
def run_discovery():
    """Run discovery connectors"""
    try:
        # Get org_id from session (mock for now)
        org_id = session.get('org_id', 'org-001')
        
        # Get request data
        data = request.get_json() or {}
        connector_id = data.get('connector_id')
        
        # Run connectors
        if connector_id:
            # Run specific connector
            new_grants = discovery_service.run_connector(connector_id)
        else:
            # Run all connectors
            new_grants = discovery_service.run_all_connectors()
        
        # Get existing grants for deduplication
        existing_grants = Grant.query.filter_by(org_id=org_id).all()
        existing_grant_dicts = [g.to_dict() for g in existing_grants]
        
        # Deduplicate
        unique_grants = discovery_service.deduplicate_grants(new_grants, existing_grant_dicts)
        
        # Save unique grants to database
        saved_count = 0
        for grant_data in unique_grants:
            try:
                # Handle date fields properly
                deadline = grant_data.get('deadline')
                if deadline and isinstance(deadline, str):
                    try:
                        deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    except:
                        deadline = None
                elif not deadline:
                    deadline = None
                
                discovered_at = grant_data.get('discoveredAt') or datetime.now()
                if isinstance(discovered_at, str):
                    try:
                        discovered_at = datetime.fromisoformat(discovered_at.replace('Z', '+00:00'))
                    except:
                        discovered_at = datetime.now()
                
                grant = Grant(
                    org_id=org_id,
                    title=grant_data.get('title'),
                    funder=grant_data.get('funder'),
                    amount_min=grant_data.get('amountMin'),
                    amount_max=grant_data.get('amountMax'),
                    deadline=deadline,
                    description=grant_data.get('eligibility'),
                    link=grant_data.get('link'),
                    status='discovered',
                    source_name=grant_data.get('sourceName'),
                    source_url=grant_data.get('sourceURL'),
                    tags=grant_data.get('tags', []),
                    discovered_at=discovered_at
                )
                db.session.add(grant)
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving grant: {e}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'totalFetched': len(new_grants),
            'newGrantsSaved': saved_count,
            'duplicatesSkipped': len(new_grants) - saved_count,
            'grants': unique_grants
        })
        
    except Exception as e:
        logger.error(f"Error running discovery: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@discovery_bp.route('/api/discovery/latest', methods=['GET'])
def get_latest_opportunities():
    """Get latest discovered opportunities"""
    try:
        org_id = session.get('org_id', 'org-001')
        
        # Get query parameters
        source_filter = request.args.get('source')
        limit = int(request.args.get('limit', 50))
        
        # Query latest grants
        query = Grant.query.filter_by(
            org_id=org_id,
            status='discovered'
        )
        
        if source_filter:
            query = query.filter_by(source_name=source_filter)
        
        grants = query.order_by(Grant.discovered_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'grants': [g.to_dict() for g in grants]
        })
        
    except Exception as e:
        logger.error(f"Error fetching latest opportunities: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@discovery_bp.route('/api/watchlists', methods=['GET'])
def get_watchlists():
    """Get all watchlists for organization"""
    try:
        org_id = session.get('org_id', 'org-001')
        
        watchlists = Watchlist.query.filter_by(org_id=org_id).all()
        
        # Create default watchlists if none exist
        if not watchlists:
            watchlists = Watchlist.create_default_watchlists(org_id)
            for watchlist in watchlists:
                db.session.add(watchlist)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'watchlists': [w.to_dict() for w in watchlists]
        })
        
    except Exception as e:
        logger.error(f"Error fetching watchlists: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@discovery_bp.route('/api/watchlists', methods=['POST'])
def create_watchlist():
    """Create a new watchlist"""
    try:
        org_id = session.get('org_id', 'org-001')
        data = request.get_json()
        
        watchlist = Watchlist(
            org_id=org_id,
            city=data.get('city'),
            sources=data.get('sources', []),
            enabled=data.get('enabled', True)
        )
        
        db.session.add(watchlist)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'watchlist': watchlist.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error creating watchlist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@discovery_bp.route('/api/watchlists/<int:watchlist_id>', methods=['PUT'])
def update_watchlist(watchlist_id):
    """Update a watchlist"""
    try:
        org_id = session.get('org_id', 'org-001')
        data = request.get_json()
        
        watchlist = Watchlist.query.filter_by(
            id=watchlist_id,
            org_id=org_id
        ).first()
        
        if not watchlist:
            return jsonify({'success': False, 'error': 'Watchlist not found'}), 404
        
        # Update fields
        if 'city' in data:
            watchlist.city = data['city']
        if 'sources' in data:
            watchlist.sources = data['sources']
        if 'enabled' in data:
            watchlist.enabled = data['enabled']
        
        watchlist.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'watchlist': watchlist.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating watchlist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@discovery_bp.route('/api/watchlists/<int:watchlist_id>', methods=['DELETE'])
def delete_watchlist(watchlist_id):
    """Delete a watchlist"""
    try:
        org_id = session.get('org_id', 'org-001')
        
        watchlist = Watchlist.query.filter_by(
            id=watchlist_id,
            org_id=org_id
        ).first()
        
        if not watchlist:
            return jsonify({'success': False, 'error': 'Watchlist not found'}), 404
        
        db.session.delete(watchlist)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting watchlist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@discovery_bp.route('/api/watchlists/<int:watchlist_id>/run', methods=['POST'])
def run_watchlist(watchlist_id):
    """Run discovery for a specific watchlist"""
    try:
        org_id = session.get('org_id', 'org-001')
        
        watchlist = Watchlist.query.filter_by(
            id=watchlist_id,
            org_id=org_id
        ).first()
        
        if not watchlist:
            return jsonify({'success': False, 'error': 'Watchlist not found'}), 404
        
        # Run connectors for this watchlist
        new_grants = discovery_service.run_watchlist_connectors(watchlist.sources)
        
        # Get existing grants for deduplication
        existing_grants = Grant.query.filter_by(org_id=org_id).all()
        existing_grant_dicts = [g.to_dict() for g in existing_grants]
        
        # Deduplicate
        unique_grants = discovery_service.deduplicate_grants(new_grants, existing_grant_dicts)
        
        # Save unique grants
        saved_count = 0
        for grant_data in unique_grants:
            try:
                grant = Grant(
                    org_id=org_id,
                    title=grant_data.get('title'),
                    funder=grant_data.get('funder'),
                    amount_min=grant_data.get('amountMin'),
                    amount_max=grant_data.get('amountMax'),
                    deadline=grant_data.get('deadline'),
                    description=grant_data.get('eligibility'),
                    link=grant_data.get('link'),
                    status='discovered',
                    source_name=grant_data.get('sourceName'),
                    source_url=grant_data.get('sourceURL'),
                    tags=grant_data.get('tags', []),
                    discovered_at=grant_data.get('discoveredAt')
                )
                db.session.add(grant)
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving grant: {e}")
        
        # Update watchlist last_run
        watchlist.last_run = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'totalFetched': len(new_grants),
            'newGrantsSaved': saved_count,
            'duplicatesSkipped': len(new_grants) - saved_count,
            'grants': unique_grants
        })
        
    except Exception as e:
        logger.error(f"Error running watchlist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500