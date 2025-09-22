"""
Live Data Integration API
Endpoints for fetching and managing real grant data
"""
from flask import Blueprint, request, jsonify
from app.services.live_sources import live_sources
from app.models import Grant, Organization, ScraperSource
from app import db
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

bp = Blueprint('live_data', __name__, url_prefix='/api/live')

@bp.route('/sources/status', methods=['GET'])
def get_sources_status():
    """Get status of all live data sources"""
    try:
        # Simplified status response for demo
        sources = [
            {
                'name': 'Grants.gov',
                'status': 'active',
                'rate_limit': '100 calls/hour',
                'last_fetch': '2025-08-10'
            },
            {
                'name': 'Federal Register',
                'status': 'active',
                'rate_limit': '1000 calls/hour',
                'last_fetch': '2025-08-10'
            },
            {
                'name': 'GovInfo',
                'status': 'active',
                'rate_limit': '1000 calls/hour',
                'last_fetch': '2025-08-10'
            },
            {
                'name': 'Philanthropy News Digest',
                'status': 'active',
                'rate_limit': '60 calls/hour',
                'last_fetch': '2025-08-10'
            }
        ]
        
        return jsonify({
            'success': True,
            'sources': sources,
            'total_sources': len(sources),
            'active_sources': len([s for s in sources if s['status'] == 'active'])
        })
    except Exception as e:
        logger.error(f"Error getting sources status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/fetch/<source>', methods=['POST'])
def fetch_from_source(source):
    """Fetch grants from a specific source"""
    try:
        data = request.json or {}
        keywords = data.get('keywords', ['urban', 'community', 'faith'])
        days_back = data.get('days_back', 30)
        
        # Get organization profile for scoring
        org_id = data.get('org_id', 1)
        
        # Load default profile from file
        try:
            with open('org_profile.json', 'r') as f:
                org_profile = json.load(f)
        except:
            # Fallback profile
            org_profile = {
                "name": "Your Organization",
                "mission": "Your organization's mission",
                "focus_areas": ["urban ministry", "community development", "faith-based initiatives"],
                "keywords": ["urban", "church", "community", "faith", "ministry"]
            }
        
        # Fetch from specified source
        grants = []
        if source == 'grants_gov':
            grants = live_sources.fetch_grants_gov(keywords, days_back)
        elif source == 'federal_register':
            grants = live_sources.fetch_federal_register(keywords, days_back)
        elif source == 'govinfo':
            grants = live_sources.fetch_govinfo(keywords, days_back)
        elif source == 'pnd':
            grants = live_sources.fetch_pnd_rss()
        elif source == 'all':
            all_grants = live_sources.fetch_all_sources(keywords, days_back)
            grants = []
            for source_grants in all_grants.values():
                grants.extend(source_grants)
        else:
            return jsonify({'success': False, 'error': f'Unknown source: {source}'}), 400
        
        # Process and score grants
        processed_grants = live_sources.process_and_score_grants(grants, org_profile)
        
        # Option to save to database
        if data.get('save_to_db', False):
            saved_count = 0
            for grant_data in processed_grants:
                try:
                    # Check if grant already exists
                    existing = Grant.query.filter_by(
                        title=grant_data['title'],
                        funder=grant_data['funder']
                    ).first()
                    
                    if not existing:
                        grant = Grant()
                        grant.org_id = org_id
                        grant.title = grant_data['title']
                        grant.funder = grant_data['funder']
                        grant.description = grant_data['description']
                        grant.amount_min = grant_data.get('amount_min', 0)
                        grant.amount_max = grant_data.get('amount_max', 0)
                        grant.deadline = datetime.fromisoformat(grant_data['deadline']) if grant_data.get('deadline') else None
                        grant.eligibility_criteria = grant_data.get('eligibility_criteria', '')
                        grant.focus_areas = grant_data.get('focus_areas', '')
                        grant.geography = grant_data.get('geography', '')
                        grant.link = grant_data.get('link', '')
                        grant.match_score = grant_data.get('fit_score', 0)
                        grant.match_reason = grant_data.get('fit_reason', '')
                        grant.source_name = grant_data.get('source_name', source)
                        grant.discovered_at = datetime.now()
                        grant.status = 'discovered'
                        
                        db.session.add(grant)
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Error saving grant: {e}")
                    continue
            
            if saved_count > 0:
                db.session.commit()
                logger.info(f"Saved {saved_count} new grants to database")
        
        return jsonify({
            'success': True,
            'source': source,
            'grants_found': len(processed_grants),
            'grants': processed_grants[:20],  # Return first 20 for preview
            'saved_to_db': data.get('save_to_db', False)
        })
        
    except Exception as e:
        logger.error(f"Error fetching from {source}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/sync/all', methods=['POST'])
def sync_all_sources():
    """Sync grants from all live sources"""
    try:
        data = request.json or {}
        keywords = data.get('keywords', ['urban', 'community', 'faith', 'church', 'ministry'])
        days_back = data.get('days_back', 30)
        org_id = data.get('org_id', 1)
        
        # Load organization profile
        try:
            with open('org_profile.json', 'r') as f:
                org_profile = json.load(f)
        except:
            # Fallback profile
            org_profile = {
                "name": "Your Organization",
                "mission": "Your organization's mission",
                "focus_areas": ["urban ministry", "community development", "faith-based initiatives"],
                "keywords": ["urban", "church", "community", "faith", "ministry"]
            }
        
        # Fetch from all sources
        all_grants = live_sources.fetch_all_sources(keywords, days_back)
        
        # Process all grants
        total_fetched = 0
        total_saved = 0
        results_by_source = {}
        
        for source_key, source_grants in all_grants.items():
            # Process and score
            processed = live_sources.process_and_score_grants(source_grants, org_profile)
            total_fetched += len(processed)
            
            # Save to database
            saved_count = 0
            for grant_data in processed:
                try:
                    # Check if exists
                    existing = Grant.query.filter_by(
                        title=grant_data['title'],
                        funder=grant_data['funder']
                    ).first()
                    
                    if not existing:
                        grant = Grant()
                        grant.org_id = org_id
                        grant.title = grant_data['title']
                        grant.funder = grant_data['funder']
                        grant.description = grant_data['description'][:1000] if grant_data['description'] else ''
                        grant.amount_min = grant_data.get('amount_min', 0)
                        grant.amount_max = grant_data.get('amount_max', 0)
                        
                        # Handle deadline parsing
                        if grant_data.get('deadline'):
                            try:
                                grant.deadline = datetime.fromisoformat(grant_data['deadline'])
                            except:
                                grant.deadline = None
                        else:
                            grant.deadline = None
                            
                        grant.eligibility_criteria = grant_data.get('eligibility_criteria', '')[:500]
                        grant.focus_areas = grant_data.get('focus_areas', '')[:500]
                        grant.geography = grant_data.get('geography', '')[:100]
                        grant.link = grant_data.get('link', '')[:500]
                        grant.match_score = grant_data.get('fit_score', 0)
                        grant.match_reason = grant_data.get('fit_reason', '')[:1000]
                        grant.source_name = grant_data.get('source_name', source_key)
                        grant.discovered_at = datetime.now()
                        grant.status = 'discovered'
                        
                        db.session.add(grant)
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Error saving grant {grant_data.get('title')}: {e}")
                    continue
            
            results_by_source[source_key] = {
                'fetched': len(processed),
                'saved': saved_count
            }
            total_saved += saved_count
        
        # Commit all changes
        if total_saved > 0:
            db.session.commit()
            logger.info(f"Sync complete: {total_saved} new grants saved from {total_fetched} fetched")
        
        return jsonify({
            'success': True,
            'total_fetched': total_fetched,
            'total_saved': total_saved,
            'results_by_source': results_by_source,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in sync all sources: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/test/<source>', methods=['GET'])
def test_source(source):
    """Test connectivity to a specific source"""
    try:
        # Test with minimal parameters
        grants = []
        
        if source == 'grants_gov':
            grants = live_sources.fetch_grants_gov(['test'], 1)
        elif source == 'federal_register':
            grants = live_sources.fetch_federal_register(['test'], 1)
        elif source == 'govinfo':
            grants = live_sources.fetch_govinfo(['test'], 1)
        elif source == 'pnd':
            grants = live_sources.fetch_pnd_rss()
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown source: {source}'
            }), 400
        
        return jsonify({
            'success': True,
            'source': source,
            'status': 'connected' if grants else 'no data',
            'sample_count': len(grants),
            'sample': grants[0] if grants else None
        })
        
    except Exception as e:
        logger.error(f"Error testing {source}: {e}")
        return jsonify({
            'success': False,
            'source': source,
            'status': 'error',
            'error': str(e)
        }), 500