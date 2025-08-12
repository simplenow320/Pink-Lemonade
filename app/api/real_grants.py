"""
Real Grants API - Only real data from working sources
"""
from flask import Blueprint, jsonify, request
from app import db
from app.models import Grant
from app.services.real_grant_fetcher import real_grant_fetcher
import logging

logger = logging.getLogger(__name__)
real_grants_bp = Blueprint('real_grants', __name__)

@real_grants_bp.route('/api/real-grants/fetch', methods=['POST'])
def fetch_real_grants():
    """
    Fetch ONLY real grants from confirmed working APIs
    No fake data, no mocks, only actual opportunities
    """
    try:
        data = request.get_json() or {}
        keyword = data.get('keyword', 'nonprofit grant')
        # Don't require org_id for now - it's causing foreign key issues
        org_id = None
        
        # Fetch real grants
        grants = real_grant_fetcher.fetch_all_real_grants(keyword)
        
        # Store in database - with proper rollback handling
        saved_count = 0
        for grant_data in grants:
            try:
                # Rollback any previous failed transaction
                db.session.rollback()
                
                # Check if grant already exists
                existing = Grant.query.filter_by(
                    title=grant_data['title'],
                    funder=grant_data['funder']
                ).first()
                
                if not existing:
                    # Parse deadline string to date object if needed
                    deadline_str = grant_data.get('deadline')
                    deadline = None
                    if deadline_str:
                        try:
                            from datetime import datetime
                            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
                        except:
                            pass
                    
                    # Use org_id 1 which exists now
                    grant = Grant(
                        title=grant_data['title'],
                        funder=grant_data['funder'],
                        link=grant_data.get('link', ''),
                        deadline=deadline,
                        org_id=1,  # We have org with ID 1 now
                        source_name=grant_data.get('source', 'Federal Register'),
                        source_url=grant_data.get('link', ''),
                        ai_summary=grant_data.get('description', ''),  # Store description in ai_summary
                        status='idea'  # Default status for new grants
                    )
                    db.session.add(grant)
                    db.session.commit()  # Commit each grant individually
                    saved_count += 1
            except Exception as e:
                logger.error(f"Error saving grant: {e}")
                db.session.rollback()  # Rollback on error
                continue
        
        return jsonify({
            'success': True,
            'message': f'Fetched {len(grants)} real grants, saved {saved_count} new ones',
            'grants': grants,
            'total_fetched': len(grants),
            'new_saved': saved_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching real grants: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch real grants'
        }), 500

@real_grants_bp.route('/api/real-grants/test', methods=['GET'])
def test_real_sources():
    """
    Test which grant sources are actually working
    """
    results = {
        'federal_register': False,
        'sam_gov': False,
        'usaspending': False
    }
    
    try:
        # Test Federal Register
        fr_grants = real_grant_fetcher.fetch_federal_register_grants(limit=2)
        results['federal_register'] = len(fr_grants) > 0
        
        # Test SAM.gov
        sam_grants = real_grant_fetcher.fetch_sam_gov_grants(limit=2)
        results['sam_gov'] = len(sam_grants) > 0
        
        # Test USAspending
        usa_grants = real_grant_fetcher.fetch_usaspending_grants(limit=2)
        results['usaspending'] = len(usa_grants) > 0
        
        return jsonify({
            'success': True,
            'working_sources': results,
            'message': 'Source connectivity test complete'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'working_sources': results
        }), 500