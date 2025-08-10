"""
Opportunities API endpoints
Fetches grant opportunities from the API Manager
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app import db
from app.models import Grant
from app.models import Organization
from app.services.apiManager import api_manager
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('opportunities', __name__, url_prefix='/api')

@bp.route('/opportunities/search', methods=['GET'])
def search_opportunities():
    """Search endpoint that returns simplified data from database"""
    try:
        # Get query parameters
        search_query = request.args.get('search', '')
        city = request.args.get('city', '')
        focus_area = request.args.get('focus_area', '')
        deadline_days = request.args.get('deadline_days', '')
        source = request.args.get('source', '')
        page = int(request.args.get('page', 1))
        per_page = 20
        
        # Get grants from database
        query = Grant.query.filter(Grant.status != 'abandoned')
        
        # Apply search filter
        if search_query:
            search_pattern = f'%{search_query}%'
            query = query.filter(db.or_(
                Grant.title.ilike(search_pattern),
                Grant.funder.ilike(search_pattern),
                Grant.eligibility.ilike(search_pattern)
            ))
        
        # Apply city filter
        if city:
            query = query.filter(Grant.geography.ilike(f'%{city}%'))
        
        # Apply focus area filter
        if focus_area:
            query = query.filter(Grant.eligibility.ilike(f'%{focus_area}%'))
        
        # Apply deadline filter
        if deadline_days:
            cutoff_date = datetime.now().date() + timedelta(days=int(deadline_days))
            query = query.filter(Grant.deadline <= cutoff_date)
        
        # Apply source filter
        if source:
            query = query.filter(Grant.source_name == source)
        
        # Order by deadline and created date
        query = query.order_by(Grant.deadline.asc().nullslast(), Grant.created_at.desc())
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Format results
        opportunities = []
        for grant in paginated.items:
            opportunities.append({
                'id': grant.id,
                'title': grant.title,
                'funder': grant.funder,
                'description': grant.eligibility or '',
                'amount_min': grant.amount_min,
                'amount_max': grant.amount_max,
                'deadline': grant.deadline.isoformat() if grant.deadline else None,
                'source': grant.source_name,
                'status': grant.status,
                'fit_score': grant.match_score,
                'fit_reason': grant.match_reason,
                'location': grant.geography,
                'focus_areas': grant.eligibility
            })
        
        return jsonify({
            'opportunities': opportunities,
            'total': paginated.total,
            'page': page,
            'per_page': per_page,
            'total_pages': paginated.pages,
            'mode': 'live'
        })
        
    except Exception as e:
        logger.error(f"Error searching opportunities: {e}")
        return jsonify({
            'opportunities': [],
            'total': 0,
            'page': 1,
            'per_page': 20,
            'total_pages': 0,
            'mode': 'live',
            'error': str(e)
        })

@bp.route('/opportunities', methods=['GET'])
def get_opportunities():
    """
    Fetch opportunities from various sources via API Manager
    Supports search, filtering, and pagination
    """
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = 20
        search_query = request.args.get('search', '')
        city = request.args.get('city', '')
        focus_area = request.args.get('focus_area', '')
        deadline_days = request.args.get('deadline_days', '')
        source = request.args.get('source', '')
        
        # Get current organization
        org = Organization.query.first()
        org_data = org.to_dict() if org else {}
        
        # Fetch opportunities from API Manager
        all_opportunities = []
        sources_to_query = [source] if source else ['grants_gov', 'philanthropy_news', 'federal_register', 
                                                     'govinfo', 'michigan_portal', 'georgia_portal']
        
        for src in sources_to_query:
            try:
                # Build search parameters for each source
                params = {'query': search_query} if search_query else {}
                
                # Add location filter if specified
                if city:
                    params['location'] = city
                
                # Add focus area filter
                if focus_area:
                    params['keyword'] = focus_area
                
                # Fetch from source using the correct method
                grants = api_manager.get_grants_from_source(src, params)
                
                if grants and isinstance(grants, list):
                    # Process each grant
                    for grant in grants:
                        # Add source information
                        grant['source'] = src
                        
                        # Calculate fit score if AI is enabled
                        if ai_service.is_enabled() and org:
                            score, reason = ai_service.match_grant(org_data, grant)
                            grant['fit_score'] = score
                            grant['fit_reason'] = reason
                        else:
                            grant['fit_score'] = None
                            grant['fit_reason'] = None
                        
                        # Apply deadline filter
                        if deadline_days:
                            deadline_date = grant.get('deadline') or grant.get('close_date')
                            if deadline_date:
                                try:
                                    deadline = datetime.fromisoformat(deadline_date.replace('Z', '+00:00'))
                                    cutoff = datetime.now() + timedelta(days=int(deadline_days))
                                    if deadline > cutoff:
                                        continue
                                except:
                                    pass
                        
                        # Apply focus area filter (additional filtering)
                        if focus_area and focus_area.lower() not in grant.get('description', '').lower():
                            continue
                        
                        # Apply city filter (additional filtering)
                        if city and city.lower() not in grant.get('eligible_applicants', '').lower():
                            continue
                        
                        all_opportunities.append(grant)
                        
            except Exception as e:
                logger.warning(f"Failed to fetch from {src}: {e}")
                continue
        
        # Apply search filter across all fields
        if search_query:
            search_lower = search_query.lower()
            all_opportunities = [
                opp for opp in all_opportunities
                if search_lower in str(opp.get('title', '') + ' ' + 
                                      opp.get('description', '') + ' ' + 
                                      opp.get('funder', '')).lower()
            ]
        
        # Sort by deadline (soonest first) and fit score (highest first)
        all_opportunities.sort(key=lambda x: (
            x.get('deadline') or '9999-12-31',
            -(x.get('fit_score') or 0)
        ))
        
        # Paginate results
        total = len(all_opportunities)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = all_opportunities[start:end]
        
        # Transform for frontend
        formatted_opportunities = []
        for idx, opp in enumerate(paginated):
            formatted_opportunities.append({
                'id': start + idx + 1,  # Temporary ID for frontend
                'title': opp.get('title', 'Untitled'),
                'funder': opp.get('agency_name') or opp.get('funder') or 'Unknown',
                'description': opp.get('description', ''),
                'fit_score': opp.get('fit_score'),
                'fit_reason': opp.get('fit_reason'),
                'amount_min': parse_amount(opp.get('award_floor')) or 0,
                'amount_max': parse_amount(opp.get('award_ceiling')) or parse_amount(opp.get('amount')) or 0,
                'deadline': opp.get('close_date') or opp.get('deadline'),
                'source': opp.get('source'),
                'url': opp.get('url') or opp.get('link'),
                'opportunity_number': opp.get('opportunity_number'),
                '_raw': opp  # Keep raw data for save/apply actions
            })
        
        # Always use LIVE mode - no mock data allowed
        import os
        data_mode = 'LIVE'  # Always live data, never mock
        mode = 'live'
        
        return jsonify({
            'opportunities': formatted_opportunities,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'mode': mode,
            'demo': False  # Never demo - always real data
        })
        
    except Exception as e:
        logger.error(f"Error fetching opportunities: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/opportunities/save/<int:grant_id>', methods=['POST'])
def save_opportunity(grant_id):
    """Save an existing grant to user's saved list"""
    try:
        # Get the grant from database
        grant = Grant.query.get_or_404(grant_id)
        
        # Change status to saved/prospect
        grant.status = 'prospect'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Grant saved to your library',
            'grant_id': grant.id
        })
        
    except Exception as e:
        logger.error(f"Error saving opportunity: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/opportunities/apply/<int:grant_id>', methods=['POST'])
def apply_to_opportunity(grant_id):
    """Start application process for a grant"""
    try:
        # Get the grant from database
        grant = Grant.query.get_or_404(grant_id)
        
        # Change status to drafting (application started)
        grant.status = 'drafting'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Application started successfully',
            'application_id': grant.id
        })
        
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def parse_amount(amount_str):
    """Parse amount string to integer"""
    if not amount_str:
        return None
    
    if isinstance(amount_str, (int, float)):
        return int(amount_str)
    
    # Remove currency symbols and commas
    amount_str = str(amount_str).replace('$', '').replace(',', '').strip()
    
    try:
        return int(float(amount_str))
    except:
        return None