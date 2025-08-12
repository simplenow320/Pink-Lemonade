"""
Live Grant Search API - Only real-time government data
No cached data, no fake data - direct from government sources
"""
from flask import Blueprint, jsonify, request
from app.services.real_grant_fetcher import real_grant_fetcher
from app import db
from app.models import Grant
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
live_grants_bp = Blueprint('live_grants', __name__)

@live_grants_bp.route('/api/live-grants/search', methods=['GET'])
def search_live_grants():
    """
    Search for LIVE grants directly from government APIs
    No database caching - always fresh data
    """
    try:
        # Get search parameters
        keyword = request.args.get('search', 'nonprofit grant')
        city = request.args.get('city', '')
        focus_area = request.args.get('focus_area', '')
        source = request.args.get('source', 'all')
        
        # Build search query
        search_terms = []
        if keyword:
            search_terms.append(keyword)
        if city:
            search_terms.append(city)
        if focus_area:
            search_terms.append(focus_area)
            
        search_query = ' '.join(search_terms) if search_terms else 'nonprofit grant opportunity'
        
        # Fetch from multiple real sources
        all_grants = []
        
        # Always try Federal Register (confirmed working)
        if source in ['all', 'federal_register']:
            logger.info(f"Fetching from Federal Register with query: {search_query}")
            federal_grants = real_grant_fetcher.fetch_federal_register_grants(
                keyword=search_query,
                limit=30
            )
            all_grants.extend(federal_grants)
            logger.info(f"Got {len(federal_grants)} grants from Federal Register")
        
        # Try USAspending if requested
        if source in ['all', 'usaspending']:
            logger.info(f"Fetching from USAspending with query: {search_query}")
            usa_grants = real_grant_fetcher.fetch_usaspending_grants(
                keyword=search_query,
                limit=20
            )
            all_grants.extend(usa_grants)
            logger.info(f"Got {len(usa_grants)} grants from USAspending")
        
        # Format for frontend
        formatted_grants = []
        for grant in all_grants:
            formatted_grants.append({
                'id': grant.get('source_id', ''),
                'title': grant.get('title', 'Untitled Grant'),
                'funder': grant.get('funder', 'Government Agency'),
                'description': grant.get('description', ''),
                'amount_min': grant.get('amount_min'),
                'amount_max': grant.get('amount_max'),
                'deadline': grant.get('deadline'),
                'source': grant.get('source', 'Federal'),
                'link': grant.get('link', ''),
                'pdf_url': grant.get('pdf_url', ''),
                'type': grant.get('type', 'Grant'),
                'is_real': True,
                'fetched_at': datetime.now().isoformat()
            })
        
        # Store in database for future reference (optional)
        if all_grants and request.args.get('save', 'false') == 'true':
            saved_count = 0
            for grant_data in all_grants[:10]:  # Save max 10 to avoid overwhelming DB
                try:
                    # Check if already exists
                    existing = Grant.query.filter_by(
                        title=grant_data['title'],
                        funder=grant_data['funder']
                    ).first()
                    
                    if not existing:
                        grant = Grant(
                            title=grant_data['title'],
                            funder=grant_data['funder'],
                            link=grant_data.get('link', ''),
                            deadline=None,  # Parse properly if needed
                            org_id=1,  # Default org
                            source_name=grant_data.get('source', 'Federal'),
                            source_url=grant_data.get('link', ''),
                            ai_summary=grant_data.get('description', ''),
                            status='idea'
                        )
                        db.session.add(grant)
                        saved_count += 1
                except Exception as e:
                    logger.error(f"Error saving grant: {e}")
                    db.session.rollback()
            
            if saved_count > 0:
                try:
                    db.session.commit()
                    logger.info(f"Saved {saved_count} new grants to database")
                except Exception as e:
                    logger.error(f"Error committing grants: {e}")
                    db.session.rollback()
        
        return jsonify({
            'success': True,
            'grants': formatted_grants,
            'total': len(formatted_grants),
            'sources_queried': ['Federal Register', 'USAspending'] if source == 'all' else [source],
            'search_query': search_query,
            'is_live_data': True,
            'message': f'Found {len(formatted_grants)} real grants from government sources'
        })
        
    except Exception as e:
        logger.error(f"Error in live grant search: {e}")
        return jsonify({
            'success': False,
            'grants': [],
            'total': 0,
            'error': str(e),
            'message': 'Unable to fetch grants. Please check your search criteria.'
        }), 500

@live_grants_bp.route('/api/live-grants/sources', methods=['GET'])
def get_available_sources():
    """Get list of available grant sources and their status"""
    try:
        sources = {
            'federal_register': {
                'name': 'Federal Register',
                'description': 'Official U.S. government grant notices and funding opportunities',
                'status': 'active',
                'reliability': 'high'
            },
            'usaspending': {
                'name': 'USAspending.gov',
                'description': 'Federal spending and grant award data',
                'status': 'active',
                'reliability': 'high'
            },
            'sam_gov': {
                'name': 'SAM.gov',
                'description': 'System for Award Management - federal contracts and grants',
                'status': 'limited',
                'reliability': 'medium'
            }
        }
        
        return jsonify({
            'success': True,
            'sources': sources,
            'recommended': 'federal_register',
            'message': 'These are verified government grant sources'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500