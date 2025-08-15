"""
PHASE 1: World-Class Matching API Endpoints
"""
from flask import Blueprint, request, jsonify, session
from app.services.phase1_matching_engine import phase1_engine
from app.models import db, Organization, Grant, LovedGrant
import logging

logger = logging.getLogger(__name__)

phase1_bp = Blueprint('phase1_matching', __name__)

@phase1_bp.route('/api/phase1/match/all', methods=['GET'])
def get_all_matches():
    """Get matched grants from all 5 data sources"""
    try:
        user_id = session.get('user_id', 1)
        org = Organization.query.filter_by(created_by_user_id=user_id).first()
        
        if not org:
            return jsonify({
                'success': False,
                'error': 'Please complete your organization profile first'
            }), 400
        
        # Get matches with scoring
        matches = phase1_engine.match_and_score(org, limit=30)
        
        # Group by source for UI display
        grouped = {}
        for match in matches:
            source = match.get('source', 'Unknown')
            if source not in grouped:
                grouped[source] = []
            grouped[source].append(match)
        
        return jsonify({
            'success': True,
            'total_matches': len(matches),
            'matches': matches[:20],  # Top 20
            'by_source': grouped,
            'profile_completeness': org.profile_completeness
        })
        
    except Exception as e:
        logger.error(f"Error getting matches: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase1_bp.route('/api/phase1/match/<source>', methods=['GET'])
def get_matches_by_source(source):
    """Get matches from a specific data source"""
    try:
        user_id = session.get('user_id', 1)
        org = Organization.query.filter_by(created_by_user_id=user_id).first()
        
        if not org:
            return jsonify({
                'success': False,
                'error': 'Please complete your organization profile first'
            }), 400
        
        # Build search context
        context = phase1_engine._build_search_context(org)
        
        # Fetch from specific source
        if source == 'federal':
            opportunities = phase1_engine._fetch_federal_grants(context)
        elif source == 'usaspending':
            opportunities = phase1_engine._fetch_usaspending_data(context)
        elif source == 'candid-grants':
            opportunities = phase1_engine._fetch_candid_grants(context)
        elif source == 'candid-news':
            opportunities = phase1_engine._fetch_candid_news(context)
        elif source == 'foundations':
            opportunities = phase1_engine._fetch_foundation_grants(context)
        else:
            return jsonify({'success': False, 'error': 'Invalid source'}), 400
        
        # Score each opportunity
        for opp in opportunities:
            score, reasoning = phase1_engine._calculate_match_score(org, opp)
            opp['match_score'] = score
            opp['match_reasoning'] = reasoning
        
        # Sort by score
        opportunities.sort(key=lambda x: x['match_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'source': source,
            'count': len(opportunities),
            'opportunities': opportunities
        })
        
    except Exception as e:
        logger.error(f"Error getting matches from {source}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase1_bp.route('/api/phase1/match/score', methods=['POST'])
def score_opportunity():
    """Score a specific opportunity for the organization"""
    try:
        user_id = session.get('user_id', 1)
        org = Organization.query.filter_by(created_by_user_id=user_id).first()
        
        if not org:
            return jsonify({
                'success': False,
                'error': 'Please complete your organization profile first'
            }), 400
        
        opportunity = request.json
        
        # Calculate detailed score
        score, reasoning = phase1_engine._calculate_match_score(org, opportunity)
        factors = phase1_engine._get_match_factors(org, opportunity)
        
        return jsonify({
            'success': True,
            'match_score': score,
            'match_reasoning': reasoning,
            'match_factors': factors,
            'recommendation': 'Apply' if score >= 70 else 'Consider' if score >= 50 else 'Skip'
        })
        
    except Exception as e:
        logger.error(f"Error scoring opportunity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase1_bp.route('/api/phase1/funder/<path:funder_name>', methods=['GET'])
def get_funder_intelligence(funder_name):
    """Get intelligence about a specific funder"""
    try:
        intelligence = phase1_engine.get_funder_intelligence(funder_name)
        
        return jsonify({
            'success': True,
            'funder': intelligence
        })
        
    except Exception as e:
        logger.error(f"Error getting funder intelligence: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase1_bp.route('/api/phase1/match/<int:match_id>/love', methods=['POST'])
def love_match(match_id):
    """Save a matched grant to loved grants"""
    try:
        user_id = session.get('user_id', 1)
        data = request.json
        
        # Create loved grant entry
        loved = LovedGrant(
            user_id=user_id,
            opportunity_data=data.get('opportunity_data'),
            status='interested',
            notes=data.get('notes', '')
        )
        db.session.add(loved)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Grant added to favorites',
            'loved_grant_id': loved.id
        })
        
    except Exception as e:
        logger.error(f"Error loving grant: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@phase1_bp.route('/api/phase1/stats', methods=['GET'])
def get_matching_stats():
    """Get statistics about matching performance"""
    try:
        user_id = session.get('user_id', 1)
        org = Organization.query.filter_by(created_by_user_id=user_id).first()
        
        if not org:
            return jsonify({
                'success': False,
                'error': 'Please complete your organization profile first'
            }), 400
        
        # Get all opportunities for stats
        all_opps = phase1_engine.get_all_opportunities(org)
        
        # Calculate stats
        stats = {
            'total_opportunities': len(all_opps),
            'sources': {
                'federal': len([o for o in all_opps if o.get('source') == 'Federal Register']),
                'usaspending': len([o for o in all_opps if o.get('source') == 'USAspending.gov']),
                'candid': len([o for o in all_opps if 'Candid' in o.get('source', '')]),
                'foundations': len([o for o in all_opps if o.get('source') == 'Foundation Directory'])
            },
            'profile_completeness': org.profile_completeness,
            'matching_quality': 'Excellent' if org.profile_completeness >= 80 else 'Good' if org.profile_completeness >= 60 else 'Fair'
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500