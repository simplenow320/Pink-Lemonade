"""
Opportunities API endpoints
Fetches grant opportunities from the API Manager
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app import db
from app.models.grant import Grant
from app.models.organization import Organization
from app.services.apiManager import api_manager
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('opportunities', __name__, url_prefix='/api')

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
                if search_lower in (opp.get('title', '') + ' ' + 
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
        
        # Determine mode (live vs mock) based on environment variable
        import os
        data_mode = os.environ.get('APP_DATA_MODE', 'MOCK')
        mode = 'mock' if data_mode == 'MOCK' else 'live'
        
        return jsonify({
            'opportunities': formatted_opportunities,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'mode': mode,
            'demo': data_mode == 'MOCK'  # Explicit demo flag
        })
        
    except Exception as e:
        logger.error(f"Error fetching opportunities: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/opportunities/save', methods=['POST'])
def save_opportunity():
    """Save an opportunity to the user's saved grants (org-scoped)"""
    try:
        data = request.json
        opportunity_id = data.get('opportunity_id')
        
        # For now, we need to get the opportunity data from the frontend
        # In a real implementation, we'd store opportunities temporarily
        
        # Get organization
        org = Organization.query.first()
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Create a new grant from the opportunity
        # This is a simplified version - you'd want to pass the full opportunity data
        grant = Grant(
            title=data.get('title', 'Grant Opportunity'),
            funder=data.get('funder', 'Unknown'),
            description=data.get('description', ''),
            amount_min=data.get('amount_min', 0),
            amount_max=data.get('amount_max', 0),
            due_date=data.get('deadline'),
            status='prospect',
            org_id=org.id,
            source_name=data.get('source', 'Opportunities'),
            discovered_at=datetime.now()
        )
        
        db.session.add(grant)
        db.session.commit()
        
        return jsonify({
            'message': 'Opportunity saved',
            'grant_id': grant.id
        })
        
    except Exception as e:
        logger.error(f"Error saving opportunity: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/opportunities/apply', methods=['POST'])
def apply_to_opportunity():
    """Create a draft application from an opportunity"""
    try:
        data = request.json
        opportunity_id = data.get('opportunity_id')
        
        # Get organization
        org = Organization.query.first()
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        # First save as grant
        grant = Grant(
            title=data.get('title', 'Grant Opportunity'),
            funder=data.get('funder', 'Unknown'),
            description=data.get('description', ''),
            amount_min=data.get('amount_min', 0),
            amount_max=data.get('amount_max', 0),
            due_date=data.get('deadline'),
            status='drafting',  # Set to drafting for applications
            org_id=org.id,
            source_name=data.get('source', 'Opportunities'),
            discovered_at=datetime.now()
        )
        
        db.session.add(grant)
        db.session.commit()
        
        return jsonify({
            'message': 'Added to applications',
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