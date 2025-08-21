"""
Opportunities API - Aggregates all grant sources
"""
import logging
from flask import Blueprint, request, jsonify
from app.services.matching_service import assemble_results, build_tokens
from app.services.grants_gov_client import get_grants_gov_client
from app.services.candid_client import get_candid_client
from app.services.candid_v3_client import get_candid_v3_client
from app.services.candid_grants_client import get_candid_grants_client
from app.services.candid_news_client import get_candid_news_client
from app.services.federal_register_client import get_federal_register_client
from app.services.usaspending_client import get_usaspending_client
from app.services.pnd_client import get_pnd_client
from app.services.foundation_aggregator import get_foundation_aggregator
from app import db
from app.models import Grant, Organization

logger = logging.getLogger(__name__)

bp = Blueprint('opportunities_api', __name__)

@bp.route('/api/opportunities/search', methods=['POST'])
def search_opportunities():
    """
    Search opportunities with POST request
    Accepts filters in request body
    """
    try:
        # Get search data from request body
        data = request.get_json() or {}
        
        # Extract search parameters
        search_query = data.get('query', '')
        location = data.get('location', '')
        focus_area = data.get('focus_area', '')
        amount = data.get('amount', '')
        deadline = data.get('deadline', '')
        source = data.get('source', '')
        grant_type = data.get('type', '')
        
        all_opportunities = []
        
        # First, get grants from our database
        try:
            from app.models import Grant
            query = Grant.query
            
            # Apply filters to database grants
            if search_query:
                query = query.filter(
                    db.or_(
                        Grant.title.ilike(f'%{search_query}%'),
                        Grant.eligibility.ilike(f'%{search_query}%'),
                        Grant.funder.ilike(f'%{search_query}%')
                    )
                )
            
            if location:
                # Handle location filter for database grants
                if location == 'michigan':
                    query = query.filter(
                        db.or_(
                            Grant.geography.ilike('%michigan%'),
                            Grant.geography.ilike('%detroit%'),
                            Grant.geography.ilike('%MI%')
                        )
                    )
                elif location == 'national':
                    query = query.filter(
                        db.or_(
                            Grant.geography.ilike('%national%'),
                            Grant.geography.ilike('%nationwide%'),
                            Grant.geography.ilike('%USA%')
                        )
                    )
            
            if focus_area:
                # Filter by focus area in eligibility text since focus_areas column doesn't exist
                query = query.filter(Grant.eligibility.ilike(f'%{focus_area}%'))
            
            # Get database grants
            db_grants = query.limit(50).all()
            
            for grant in db_grants:
                opportunity = {
                    'source': 'database',
                    'source_type': 'Grant Database',
                    'source_name': 'Pink Lemonade Database',
                    'id': grant.id,
                    'title': grant.title or 'Grant Opportunity',
                    'funder': grant.funder or 'Foundation',
                    'description': grant.eligibility or '',
                    'deadline': grant.deadline.isoformat() if grant.deadline else None,
                    'amount_min': grant.amount_min,
                    'amount_max': grant.amount_max,
                    'geography': grant.geography,
                    'focus_areas': '',  # Not in model
                    'status': grant.status or 'available'
                }
                all_opportunities.append(opportunity)
            
            logger.info(f"Found {len(db_grants)} grants from database")
            
        except Exception as e:
            logger.error(f"Error fetching database grants: {e}")
        
        # Try to get federal grants if available
        if not source or source in ['federal_grants', 'grants.gov', 'federal']:
            try:
                from app.services.grants_gov_client import get_grants_gov_client
                client = get_grants_gov_client()
                
                search_params = {
                    "opportunity_status": "open",
                    "page_size": 10
                }
                
                if search_query:
                    search_params["keywords"] = [search_query]
                
                federal_grants = client.search_opportunities(search_params)
                
                for grant in federal_grants:
                    grant['source_type'] = 'Federal'
                    grant['source_name'] = 'Grants.gov'
                    
                all_opportunities.extend(federal_grants)
                
            except Exception as e:
                logger.warning(f"Could not fetch federal grants: {e}")
        
        # Get foundation grants if requested
        if not source or source in ['foundation_news', 'foundations']:
            try:
                from app.services.candid_grants_client import CandidGrantsClient
                candid_client = CandidGrantsClient()
                
                foundation_grants = candid_client.search_grants(
                    keyword=search_query or focus_area,
                    limit=20
                )
                
                all_opportunities.extend(foundation_grants)
                
            except Exception as e:
                logger.error(f"Error fetching foundation grants: {e}")
        
        # Filter by amount if specified
        if amount:
            amount_ranges = {
                'under_10k': (0, 10000),
                '10k_50k': (10000, 50000),
                '50k_100k': (50000, 100000),
                '100k_500k': (100000, 500000),
                'over_500k': (500000, float('inf'))
            }
            
            if amount in amount_ranges:
                min_amt, max_amt = amount_ranges[amount]
                all_opportunities = [
                    opp for opp in all_opportunities
                    if opp.get('amount_min', 0) >= min_amt or opp.get('amount_max', float('inf')) <= max_amt
                ]
        
        # Filter by location if specified
        if location:
            location_keywords = {
                'michigan': ['Michigan', 'MI', 'Detroit', 'Grand Rapids'],
                'national': ['National', 'United States', 'USA', 'Nationwide'],
                'midwest': ['Midwest', 'Michigan', 'Ohio', 'Illinois', 'Indiana', 'Wisconsin']
            }
            
            if location in location_keywords:
                keywords = location_keywords[location]
                all_opportunities = [
                    opp for opp in all_opportunities
                    if any(kw.lower() in str(opp.get('location', '')).lower() or 
                          kw.lower() in str(opp.get('geography', '')).lower() 
                          for kw in keywords)
                ]
        
        # Sort by relevance/date
        all_opportunities.sort(
            key=lambda x: x.get('deadline') or '9999-12-31',
            reverse=False
        )
        
        # Limit results
        all_opportunities = all_opportunities[:100]
        
        return jsonify({
            'success': True,
            'grants': all_opportunities,
            'count': len(all_opportunities),
            'filters_applied': {
                'query': search_query,
                'location': location,
                'focus_area': focus_area,
                'amount': amount,
                'source': source
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching opportunities: {e}")
        return jsonify({
            'success': False,
            'error': 'Error searching grants. Please try again.',
            'grants': []
        }), 500

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
        
        # 2. Get Federal Register Notices (FREE API)
        if not source_filter or source_filter in ['federal_register', 'federal']:
            try:
                client = get_federal_register_client()
                search_term = search_query or focus_area or "grant"
                notices = client.search_grant_notices(keywords=search_term, days_back=30)
                all_opportunities.extend(notices)
                logger.info(f"Added {len(notices)} Federal Register notices")
            except Exception as e:
                logger.error(f"Error fetching Federal Register: {e}")
        
        # 3. Get USAspending Historical Awards (FREE API)
        if not source_filter or source_filter in ['usaspending', 'historical']:
            try:
                client = get_usaspending_client()
                search_term = search_query or focus_area or ""
                awards = client.search_assistance_listings(keywords=search_term)
                all_opportunities.extend(awards[:20])  # Limit to 20 for performance
                logger.info(f"Added {len(awards[:20])} USAspending awards")
            except Exception as e:
                logger.error(f"Error fetching USAspending: {e}")
        
        # 4. Get Foundation Opportunities from PND (FREE RSS Feed)
        if not source_filter or source_filter in ['foundation', 'pnd', 'private']:
            try:
                client = get_pnd_client()
                foundation_opps = client.get_foundation_opportunities()
                all_opportunities.extend(foundation_opps[:25])  # Limit to 25
                logger.info(f"Added {len(foundation_opps[:25])} foundation opportunities from PND")
            except Exception as e:
                logger.error(f"Error fetching PND opportunities: {e}")
        
        # 5. Get REAL Grant Data from Candid Grants API (WORKING!)
        if not source_filter or source_filter in ['foundation', 'candid', 'private']:
            try:
                client = get_candid_grants_client()
                
                # Get summary first to verify connection
                summary = client.get_summary()
                if summary:
                    logger.info(f"Candid API Connected: {summary.get('number_of_grants', 0):,} grants available")
                
                # Search for grants based on criteria
                keyword = search_query or focus_area or ""
                candid_grants = client.search_grants(
                    keyword=keyword,
                    state=city[:2].upper() if city and len(city) >= 2 else "",
                    limit=25
                )
                
                # If no specific grants found, get top funders instead
                if not candid_grants:
                    funders = client.get_funders(limit=10)
                    all_opportunities.extend(funders)
                    logger.info(f"Added {len(funders)} Candid funders")
                else:
                    all_opportunities.extend(candid_grants)
                    logger.info(f"Added {len(candid_grants)} Candid grants")
                    
            except Exception as e:
                logger.error(f"Error fetching Candid data: {e}")
                # Fallback to major foundations if Candid fails
                try:
                    aggregator = get_foundation_aggregator()
                    foundation_opps = aggregator.get_all_foundation_opportunities(search_query or focus_area)
                    all_opportunities.extend(foundation_opps)
                    logger.info(f"Added {len(foundation_opps)} foundation opportunities (fallback)")
                except Exception as e2:
                    logger.error(f"Error fetching foundation data: {e2}")
        
        # 6. Get Grant News from Candid News API (WORKING!)
        if not source_filter or source_filter in ['news', 'candid']:
            try:
                news_client = get_candid_news_client()
                news_opps = news_client.get_grant_news_opportunities(
                    keyword=search_query or focus_area or "grant opportunity"
                )
                all_opportunities.extend(news_opps[:5])  # Add top 5 news items
                logger.info(f"Added {len(news_opps[:5])} Candid news opportunities")
            except Exception as e:
                logger.error(f"Error fetching Candid news: {e}")
        
        # 7. Old Candid API (deprecated)
        if False:  # Disabled - using new APIs
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
                            'source_name': 'Candid Foundation News',
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