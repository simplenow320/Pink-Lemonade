"""
Opportunities API - Aggregates all grant sources
"""
import logging
from flask import Blueprint, request, jsonify
from app.services.matching_service import assemble_results, build_tokens
from app.services.grants_gov_client import get_grants_gov_client
from app.services.candid_client import get_candid_client
from app import db
from app.models import Grant, Organization

logger = logging.getLogger(__name__)

bp = Blueprint('opportunities_api', __name__)

@bp.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    """
    Get all opportunities from all sources
    Combines federal grants, foundation news, and database grants
    """
    try:
        # Get query parameters
        search_query = request.args.get('q', '')
        city = request.args.get('city', '')
        focus_area = request.args.get('focus', '')
        source_filter = request.args.get('source', '')
        org_id = request.args.get('orgId')
        limit = int(request.args.get('limit', 100))
        
        all_opportunities = []
        
        # 1. Get Federal Grants from Grants.gov
        if not source_filter or source_filter in ['grants.gov', 'federal']:
            try:
                client = get_grants_gov_client()
                search_params = {
                    "opportunity_status": "open",
                    "page_size": 25
                }
                
                # Add search keywords
                if search_query:
                    search_params["keywords"] = [search_query]
                elif focus_area:
                    search_params["keywords"] = [focus_area]
                    
                federal_grants = client.search_opportunities(search_params)
                
                # Add source info and type
                for grant in federal_grants:
                    grant['source_type'] = 'Federal'
                    grant['source_name'] = 'Government Database'
                all_opportunities.extend(federal_grants)
                    
                logger.info(f"Found {len(federal_grants)} federal grants")
            except Exception as e:
                logger.error(f"Error fetching federal grants: {e}")
        
        # 2. Get Foundation Grants from Candid News
        if not source_filter or source_filter in ['foundation', 'candid_news', 'private']:
            try:
                client = get_candid_client()
                
                # Build search query for news
                news_query = search_query or focus_area or "grant OR foundation OR RFP OR funding"
                
                # Search news for grant opportunities
                news_results = client.search_news(news_query, page=1, size=25)
                
                if news_results and not news_results.get("error"):
                    articles = news_results.get("articles", [])
                    for article in articles:
                        # Transform news to opportunity format
                        opportunity = {
                            'source': 'candid_news',
                            'source_type': 'Foundation',
                            'source_name': 'Foundation News',
                            'title': article.get('title', 'Foundation Opportunity'),
                            'funder': article.get('publisher', 'Foundation'),
                            'description': article.get('summary', ''),
                            'url': article.get('url', ''),
                            'published_date': article.get('published_date'),
                            'keywords': article.get('keywords', [])
                        }
                        all_opportunities.append(opportunity)
                    
                    logger.info(f"Found {len(articles)} foundation opportunities from news")
            except Exception as e:
                logger.error(f"Error fetching Candid news: {e}")
        
        # 3. Get Historical Grants from Candid Transactions
        if not source_filter or source_filter in ['foundation', 'candid_grants', 'historical']:
            try:
                client = get_candid_client()
                
                # Build search for transactions
                trans_query = search_query or focus_area or "education"
                
                transactions = client.search_transactions(trans_query, page=1, size=15)
                
                if transactions and not transactions.get("error"):
                    grants_data = transactions.get("grants", [])
                    for grant in grants_data:
                        # Transform transaction to opportunity format
                        opportunity = {
                            'source': 'candid_grants',
                            'source_type': 'Historical Grant',
                            'source_name': 'Grant History Database',
                            'title': f"{grant.get('funder_name', 'Funder')} - {grant.get('description', 'Grant')}",
                            'funder': grant.get('funder_name', 'Foundation'),
                            'description': grant.get('description', ''),
                            'amount': grant.get('amount'),
                            'grant_date': grant.get('grant_date'),
                            'recipient': grant.get('recipient_name')
                        }
                        all_opportunities.append(opportunity)
                    
                    logger.info(f"Found {len(grants_data)} historical grants")
            except Exception as e:
                logger.error(f"Error fetching Candid transactions: {e}")
        
        # 4. Get grants from database
        if not source_filter or source_filter == 'saved':
            try:
                db_grants = Grant.query.all()
                for grant in db_grants:
                    opportunity = {
                        'source': 'database',
                        'source_type': 'Saved',
                        'source_name': 'Your Saved Grants',
                        'id': grant.id,
                        'title': grant.title or 'Saved Grant',
                        'funder': grant.funder or 'Unknown',
                        'deadline': grant.deadline.isoformat() if grant.deadline else None,
                        'amount_min': grant.amount_min,
                        'amount_max': grant.amount_max,
                        'status': grant.status or 'available'
                    }
                    all_opportunities.append(opportunity)
                    
                logger.info(f"Found {len(db_grants)} saved grants")
            except Exception as e:
                logger.error(f"Error fetching database grants: {e}")
        
        # Apply city filter if specified
        if city:
            filtered = []
            for opp in all_opportunities:
                # Check various location fields
                if city.lower() in str(opp.get('geography', '')).lower() or \
                   city.lower() in str(opp.get('location', '')).lower() or \
                   city.lower() in str(opp.get('state', '')).lower():
                    filtered.append(opp)
            all_opportunities = filtered
        
        # Apply focus area filter
        if focus_area:
            filtered = []
            for opp in all_opportunities:
                # Check if focus area matches
                if focus_area.lower() in str(opp.get('title', '')).lower() or \
                   focus_area.lower() in str(opp.get('description', '')).lower() or \
                   focus_area.lower() in str(opp.get('keywords', [])).lower():
                    filtered.append(opp)
            all_opportunities = filtered
        
        # Limit results
        all_opportunities = all_opportunities[:limit]
        
        return jsonify({
            'success': True,
            'opportunities': all_opportunities,
            'total': len(all_opportunities),
            'sources': {
                'federal': sum(1 for o in all_opportunities if o.get('source_type') == 'Federal'),
                'foundation': sum(1 for o in all_opportunities if o.get('source_type') == 'Foundation'),
                'historical': sum(1 for o in all_opportunities if o.get('source_type') == 'Historical Grant'),
                'saved': sum(1 for o in all_opportunities if o.get('source_type') == 'Saved')
            }
        })
        
    except Exception as e:
        logger.error(f"Error in opportunities endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'opportunities': [],
            'total': 0
        })

@bp.route('/api/opportunities/locations', methods=['GET'])
def get_available_locations():
    """
    Get all available locations from current opportunities
    Dynamic list based on actual data
    """
    try:
        locations = set()
        
        # Get locations from federal grants
        try:
            client = get_grants_gov_client()
            federal_grants = client.search_opportunities({"opportunity_status": "open", "page_size": 50})
            for grant in federal_grants:
                if grant.get('geography'):
                    locations.add(grant['geography'])
                if grant.get('state'):
                    locations.add(grant['state'])
        except:
            pass
        
        # Get locations from database
        try:
            db_grants = Grant.query.all()
            for grant in db_grants:
                if hasattr(grant, 'geography') and grant.geography:
                    locations.add(grant.geography)
        except:
            pass
        
        # Add major cities as defaults
        default_cities = [
            "National", "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
            "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
            "Austin", "Jacksonville", "Fort Worth", "Columbus", "Indianapolis",
            "Charlotte", "San Francisco", "Seattle", "Denver", "Washington DC",
            "Boston", "Nashville", "Detroit", "Portland", "Memphis", "Oklahoma City",
            "Las Vegas", "Louisville", "Baltimore", "Milwaukee", "Albuquerque",
            "Tucson", "Fresno", "Sacramento", "Kansas City", "Atlanta", "Miami",
            "Oakland", "Minneapolis", "Cleveland", "Tampa", "St. Louis", "Pittsburgh",
            "Cincinnati", "Orlando", "Newark", "Buffalo", "Raleigh", "Richmond"
        ]
        
        for city in default_cities:
            locations.add(city)
        
        # Sort alphabetically
        sorted_locations = sorted(list(locations))
        
        return jsonify({
            'success': True,
            'locations': sorted_locations
        })
        
    except Exception as e:
        logger.error(f"Error getting locations: {e}")
        return jsonify({
            'success': False,
            'locations': ["National"]
        })