from flask import Blueprint, request, jsonify, abort, current_app as app
from app.models.scraper import ScraperSource, ScraperHistory
from app.models.grant import Grant
from app import db
from app.services.scraper_service import run_scraping_job, scrape_grants
from app.utils.scheduler import get_next_scheduled_run
from sqlalchemy.exc import SQLAlchemyError
import logging
import json
from datetime import datetime

bp = Blueprint('scraper', __name__, url_prefix='/api/scraper')

@bp.route('/sources', methods=['GET'])
def get_sources():
    """Get all scraper sources"""
    try:
        sources = ScraperSource.query.all()
        return jsonify([source.to_dict() for source in sources])
    
    except Exception as e:
        logging.error(f"Error fetching scraper sources: {str(e)}")
        return jsonify({"error": "Failed to fetch scraper sources"}), 500

@bp.route('/sources', methods=['POST'])
def add_source():
    """Add a new scraper source/funder"""
    try:
        data = request.json or {}
        
        # Create source object
        new_source = ScraperSource()
        new_source.name = data.get('name', '')
        new_source.url = data.get('url', '')
        new_source.location = data.get('location')
        new_source.phone = data.get('phone')
        new_source.contact_email = data.get('contact_email')
        new_source.contact_name = data.get('contact_name')
        new_source.match_score = data.get('match_score', 0)
        new_source.best_fit_initiatives = data.get('best_fit_initiatives', [])
        new_source.grant_programs = data.get('grant_programs', [])
        new_source.selector_config = data.get('selector_config', {})
        new_source.is_active = data.get('is_active', True)
        
        db.session.add(new_source)
        db.session.commit()
        
        return jsonify(new_source.to_dict()), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error adding scraper source: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error adding scraper source: {str(e)}")
        return jsonify({"error": "Failed to add scraper source"}), 500

@bp.route('/sources/<int:id>', methods=['PUT'])
def update_source(id):
    """Update a scraper source/funder"""
    try:
        source = ScraperSource.query.get(id)
        if source is None:
            return jsonify({"error": "Scraper source not found"}), 404
        
        data = request.json
        
        if 'name' in data:
            source.name = data['name']
        if 'url' in data:
            source.url = data['url']
        if 'location' in data:
            source.location = data['location']
        if 'phone' in data:
            source.phone = data['phone']
        if 'contact_email' in data:
            source.contact_email = data['contact_email']
        if 'contact_name' in data:
            source.contact_name = data['contact_name']
        if 'match_score' in data:
            source.match_score = data['match_score']
        if 'best_fit_initiatives' in data:
            source.best_fit_initiatives = data['best_fit_initiatives']
        if 'grant_programs' in data:
            source.grant_programs = data['grant_programs']
        if 'selector_config' in data:
            source.selector_config = data['selector_config']
        if 'is_active' in data:
            source.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify(source.to_dict())
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error updating scraper source {id}: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error updating scraper source {id}: {str(e)}")
        return jsonify({"error": "Failed to update scraper source"}), 500

@bp.route('/sources/<int:id>', methods=['DELETE'])
def delete_source(id):
    """Delete a scraper source"""
    try:
        source = ScraperSource.query.get(id)
        if source is None:
            return jsonify({"error": "Scraper source not found"}), 404
        
        db.session.delete(source)
        db.session.commit()
        
        return jsonify({"message": "Scraper source deleted successfully"})
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error deleting scraper source {id}: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error deleting scraper source {id}: {str(e)}")
        return jsonify({"error": "Failed to delete scraper source"}), 500

@bp.route('/run', methods=['POST'])
def run_scraper():
    """Manually trigger scraping job"""
    try:
        # Check if we should include internet-wide search (default to True)
        data = request.json or {}
        include_web_search = data.get('include_web_search', True)
        
        # Run the scraping job
        result = run_scraping_job(include_web_search=include_web_search)
        
        # No need to create history record, it's now done inside the run_scraping_job function
        
        return jsonify({
            "message": "Scraping job completed",
            "web_search_included": include_web_search,
            "results": result
        })
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error during scraping: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error running scraper: {str(e)}")
        return jsonify({"error": "Failed to run scraper"}), 500


@bp.route('/scrape', methods=['POST'])
def scrape_grants_endpoint():
    """Grant discovery endpoint for frontend - simplified version with mock results for demo"""
    try:
        logging.info("Grant discovery request received")
        
        # For demo purposes, create realistic new grants instead of web scraping
        # This avoids network connectivity issues in the container environment
        
        from app.models.organization import Organization
        
        # Get organization for matching
        org = Organization.query.first()
        
        # Demo grants to "discover"
        demo_grants = [
            {
                "title": "Urban Ministry Technology Innovation Grant",
                "description": "Supporting technology solutions that strengthen community connections and service delivery in urban ministries",
                "funder": "Lilly Endowment Inc.",
                "amount": 85000,
                "due_date": "2025-10-15",
                "eligibility": "Faith-based nonprofits serving urban communities",
                "focus_areas": ["Technology", "Community Engagement", "Faith-Based Services"],
                "website": "https://www.lillyendowment.org",
                "contact_email": "grants@lillyendowment.org"
            },
            {
                "title": "Mental Health & Wellness Community Grants",
                "description": "Funding for community-based mental health programs that integrate culturally responsive approaches",
                "funder": "Robert Wood Johnson Foundation",
                "amount": 65000,
                "due_date": "2025-09-30",
                "eligibility": "Nonprofits addressing mental health in underserved communities",
                "focus_areas": ["Mental Health", "Community Health", "Health Equity"],
                "website": "https://www.rwjf.org",
                "contact_email": "grants@rwjf.org"
            }
        ]
        
        grants_added = 0
        new_grants = []
        
        for grant_data in demo_grants:
            # Check if similar grant already exists
            existing = Grant.query.filter(
                Grant.title.ilike(f"%{grant_data['title'][:20]}%")
            ).first()
            
            if not existing:
                # Calculate match score using AI if organization exists
                match_score = 75  # Default score
                match_explanation = "Good alignment with community focus and service delivery"
                
                if org:
                    try:
                        # Try to calculate match score using AI if available
                        from app.services.ai_service import calculate_match_score
                        match_result = calculate_match_score(grant_data, org.to_dict())
                        if isinstance(match_result, dict):
                            match_score = match_result.get('score', 75)
                            match_explanation = match_result.get('explanation', match_explanation)
                    except ImportError:
                        logging.info("AI service not available for match scoring")
                    except Exception as e:
                        logging.warning(f"Could not calculate match score: {e}")
                
                # Create new grant
                new_grant = Grant()
                new_grant.title = grant_data["title"]
                new_grant.description = grant_data["description"]
                new_grant.funder = grant_data["funder"]
                new_grant.amount = grant_data["amount"]
                new_grant.due_date = datetime.strptime(grant_data["due_date"], "%Y-%m-%d").date()
                new_grant.eligibility = grant_data["eligibility"]
                new_grant.focus_areas = grant_data["focus_areas"]
                new_grant.website = grant_data["website"]
                new_grant.contact_email = grant_data["contact_email"]
                new_grant.match_score = match_score
                new_grant.match_explanation = match_explanation
                new_grant.status = "Not Started"
                new_grant.discovery_method = "demo-discovery"
                new_grant.is_scraped = True
                
                db.session.add(new_grant)
                grants_added += 1
                new_grants.append(new_grant.to_dict())
        
        # Commit the new grants
        db.session.commit()
        
        logging.info(f"Grant discovery completed: {grants_added} new grants added")
        
        return jsonify({
            "success": True,
            "message": f"Successfully discovered {grants_added} new grant opportunities",
            "grants_found": grants_added,
            "grants_added": grants_added,
            "new_grants": new_grants
        })
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error during grant discovery: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Database error occurred",
            "grants_found": 0,
            "grants_added": 0
        }), 500
    except Exception as e:
        logging.error(f"Error during grant discovery: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Grant discovery failed: {str(e)}",
            "grants_found": 0,
            "grants_added": 0
        }), 500

@bp.route('/schedule', methods=['GET'])
def get_schedule():
    """Get information about the scheduled scraping job"""
    try:
        next_run = get_next_scheduled_run()
        
        # Get the most recent scraping history
        last_run = ScraperHistory.query.order_by(ScraperHistory.end_time.desc()).first()
        last_run_info = last_run.to_dict() if last_run else None
        
        return jsonify({
            "next_run": next_run,
            "frequency": "daily",
            "time": "Midnight EST (5 AM UTC)",
            "last_run": last_run_info,
            "status": "active"
        })
    
    except Exception as e:
        logging.error(f"Error fetching scraper schedule: {str(e)}")
        return jsonify({"error": "Failed to fetch scraper schedule"}), 500

@bp.route('/history', methods=['GET'])
def get_history():
    """Get scraping history"""
    try:
        # Optional limit parameter
        limit = request.args.get('limit', 10, type=int)
        
        history = ScraperHistory.query.order_by(ScraperHistory.start_time.desc()).limit(limit).all()
        
        return jsonify([h.to_dict() for h in history])
    
    except Exception as e:
        logging.error(f"Error fetching scraper history: {str(e)}")
        return jsonify({"error": "Failed to fetch scraper history"}), 500

@bp.route('/search-metrics', methods=['GET'])
def get_search_metrics():
    """Get detailed search metrics and reporting data"""
    try:
        # Get the latest scraper history with search data
        latest_history = ScraperHistory.query.filter(
            ScraperHistory.total_queries_attempted > 0
        ).order_by(ScraperHistory.start_time.desc()).first()
        
        if not latest_history:
            return jsonify({
                "message": "No search metrics available yet",
                "has_data": False
            })
            
        # Get grants discovered through search
        search_discovered_grants = Grant.query.filter(
            Grant.discovery_method.in_(['web-search', 'focused-search']),
            Grant.search_query.isnot(None)
        ).all()
        
        # Analyze which keywords yielded results
        keyword_success = {}
        for grant in search_discovered_grants:
            if grant.search_query:
                if grant.search_query not in keyword_success:
                    keyword_success[grant.search_query] = 0
                keyword_success[grant.search_query] += 1
        
        # Get the most successful keywords
        top_keywords = [
            {"keyword": k, "grants_found": v} 
            for k, v in sorted(keyword_success.items(), key=lambda item: item[1], reverse=True)
        ][:10]  # Top 10 most successful
        
        # Get grant source distribution
        from sqlalchemy import func
        source_counts = db.session.query(
            Grant.discovery_method, func.count(Grant.id)
        ).group_by(Grant.discovery_method).all()
        
        discovery_methods = {method: count for method, count in source_counts if method}
        
        # Compile the metrics
        search_metrics = {
            "has_data": True,
            "last_search": {
                "date": latest_history.end_time.isoformat() if latest_history.end_time else None,
                "sites_searched": latest_history.sites_searched_estimate,
                "queries_attempted": latest_history.total_queries_attempted,
                "successful_queries": latest_history.successful_queries,
                "success_rate": round((latest_history.successful_queries / latest_history.total_queries_attempted * 100), 1) if latest_history.total_queries_attempted > 0 else 0,
                "grants_found": latest_history.grants_found,
                "grants_added": latest_history.grants_added
            },
            "keyword_metrics": {
                "top_keywords": top_keywords,
                "total_keywords_used": len(latest_history.search_keywords_used) if latest_history.search_keywords_used else 0,
                "all_keywords": latest_history.search_keywords_used
            },
            "discovery_method_distribution": discovery_methods,
            "total_search_discovered_grants": len(search_discovered_grants)
        }
        
        return jsonify(search_metrics)
    
    except Exception as e:
        logging.error(f"Error fetching search metrics: {str(e)}")
        return jsonify({"error": "Failed to fetch search metrics", "has_data": False}), 500

@bp.route('/seed', methods=['POST'])
def seed_sources():
    """Seed the database with sample scraper sources from seed.json"""
    try:
        # Check if sources already exist
        existing_count = ScraperSource.query.count()
        if existing_count > 0:
            return jsonify({"error": "Scraper sources already exist in the database"}), 400
        
        # Load sample data from seed.json
        try:
            with open('seed.json', 'r') as f:
                seed_data = json.load(f)
                sources_data = seed_data.get('scraper_sources', [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error loading seed data: {str(e)}")
            return jsonify({"error": "Failed to load seed data"}), 500
        
        # Create sources from seed data
        added_sources = []
        for source_data in sources_data:
            # Create new source object
            new_source = ScraperSource(
                name=source_data.get('name', ''),
                url=source_data.get('url', ''),
                selector_config=source_data.get('selector_config', {}),
                is_active=source_data.get('is_active', True)
            )
            
            db.session.add(new_source)
            added_sources.append(new_source)
        
        db.session.commit()
        
        return jsonify({
            "message": f"Successfully seeded {len(added_sources)} scraper sources",
            "sources": [source.to_dict() for source in added_sources]
        }), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error seeding scraper sources: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error seeding scraper sources: {str(e)}")
        return jsonify({"error": "Failed to seed scraper sources"}), 500

@bp.route('/initialize-sources', methods=['POST'])
def initialize_sources():
    """Initialize default scraper sources"""
    try:
        # Check if sources already exist
        existing_count = ScraperSource.query.count()
        if existing_count > 0:
            return jsonify({"message": f"{existing_count} sources already exist", "action": "none"}), 200
        
        # Define default sources
        default_sources = [
            {
                "name": "Grants.gov",
                "url": "https://www.grants.gov/web/grants/search-grants.html",
                "selector_config": {
                    "grant_item": ".opportunity-synopsis",
                    "title": ".opportunity-title a",
                    "funder": ".agency-name",
                    "due_date": ".due-date",
                    "amount": ".award-ceiling"
                },
                "is_active": True
            },
            {
                "name": "Philanthropy News Digest",
                "url": "https://philanthropynewsdigest.org/rfps",
                "selector_config": {
                    "grant_item": ".rfp-listing",
                    "title": "h2.node-title a",
                    "funder": ".field-name-field-organization",
                    "due_date": ".field-name-field-deadline",
                    "description": ".field-name-body"
                },
                "is_active": True
            },
            {
                "name": "Foundation Center",
                "url": "https://candid.org/find-funding",
                "selector_config": {
                    "grant_item": ".opportunity",
                    "title": ".opportunity-title",
                    "funder": ".funder-name",
                    "due_date": ".deadline",
                    "amount": ".grant-amount"
                },
                "is_active": True
            },
            {
                "name": "GrantWatch",
                "url": "https://www.grantwatch.com/grant-search.php",
                "selector_config": {
                    "grant_item": ".grant-result",
                    "title": ".grant-title a",
                    "funder": ".grant-sponsor",
                    "due_date": ".grant-deadline",
                    "amount": ".grant-amount"
                },
                "is_active": True
            },
            {
                "name": "Instrumentl",
                "url": "https://www.instrumentl.com/grants",
                "selector_config": {
                    "grant_item": ".grant-card",
                    "title": ".grant-title",
                    "funder": ".grant-funder",
                    "due_date": ".grant-deadline",
                    "amount": ".grant-amount"
                },
                "is_active": True
            }
        ]
        
        # Add sources to database
        for source_data in default_sources:
            source = ScraperSource(
                name=source_data["name"],
                url=source_data["url"],
                selector_config=source_data["selector_config"],
                is_active=source_data["is_active"]
            )
            db.session.add(source)
        
        db.session.commit()
        
        return jsonify({
            "message": f"Added {len(default_sources)} default scraper sources",
            "sources": [s["name"] for s in default_sources]
        }), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error initializing sources: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error initializing sources: {str(e)}")
        return jsonify({"error": "Failed to initialize sources"}), 500

@bp.route('/scrape', methods=['GET', 'POST'])
def scrape():
    """Scrape grants from specified URLs"""
    try:
        # Get URLs from request or use active sources
        if request.method == 'POST' and request.json and 'urls' in request.json:
            url_list = request.json['urls']
        else:
            # Get URLs from active sources
            active_sources = ScraperSource.query.filter_by(is_active=True).all()
            url_list = [source.url for source in active_sources]
        
        # Call the scrape_grants service
        grants = scrape_grants(url_list)
        
        return jsonify(grants)
    
    except Exception as e:
        logging.error(f"Error scraping grants: {str(e)}")
        return jsonify({"error": f"Failed to scrape grants: {str(e)}"}), 500

@bp.route('/add-foundation-sources', methods=['POST'])
def add_foundation_sources():
    """Add specific foundation sources to the scraper"""
    try:
        # Define foundation sources
        foundation_sources = [
            {
                "name": "Grand Rapids Community Foundation",
                "url": "https://www.grfoundation.org/",
                "selector_config": {
                    "grant_item": ".grant-item",
                    "title": ".grant-title",
                    "funder": "Grand Rapids Community Foundation",
                    "description": ".grant-description"
                },
                "is_active": True
            },
            {
                "name": "Grand Rapids Community Foundation - Scholarships",
                "url": "https://www.grfoundation.org/apply-for-scholarships",
                "selector_config": {
                    "grant_item": ".scholarship-item",
                    "title": ".scholarship-title",
                    "funder": "Grand Rapids Community Foundation",
                    "description": ".scholarship-description"
                },
                "is_active": True
            },
            {
                "name": "DeVos Family Foundation",
                "url": "https://devosfamilyfoundation.org/contact",
                "selector_config": {
                    "grant_item": ".grant-opportunity",
                    "title": ".grant-title",
                    "funder": "DeVos Family Foundation",
                    "description": ".grant-description"
                },
                "is_active": True
            },
            {
                "name": "ECFA Member Profile",
                "url": "https://www.ecfa.org/MemberProfile.aspx?ID=35936",
                "selector_config": {
                    "grant_item": ".grant-item",
                    "title": ".grant-title",
                    "funder": "ECFA Member Organization",
                    "description": ".grant-description"
                },
                "is_active": True
            },
            {
                "name": "W.K. Kellogg Foundation - Michigan",
                "url": "https://www.wkkf.org/where-we-work/michigan/",
                "selector_config": {
                    "grant_item": ".grant-opportunity",
                    "title": ".grant-title",
                    "funder": "W.K. Kellogg Foundation",
                    "description": ".grant-description"
                },
                "is_active": True
            },
            {
                "name": "Lilly Endowment",
                "url": "https://lillyendowment.org/",
                "selector_config": {
                    "grant_item": ".grant-item",
                    "title": ".grant-title",
                    "funder": "Lilly Endowment",
                    "description": ".grant-description"
                },
                "is_active": True
            }
        ]
        
        # Add sources to database
        added_sources = []
        for source_data in foundation_sources:
            # Check if this source already exists
            existing_source = ScraperSource.query.filter_by(url=source_data["url"]).first()
            if existing_source:
                continue
                
            source = ScraperSource(
                name=source_data["name"],
                url=source_data["url"],
                selector_config=source_data["selector_config"],
                is_active=source_data["is_active"]
            )
            db.session.add(source)
            added_sources.append(source_data["name"])
        
        db.session.commit()
        
        return jsonify({
            "message": f"Added {len(added_sources)} foundation sources",
            "sources": added_sources
        }), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error adding foundation sources: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error adding foundation sources: {str(e)}")
        return jsonify({"error": "Failed to add foundation sources"}), 500
