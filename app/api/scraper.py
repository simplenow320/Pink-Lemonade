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
    """Add a new scraper source"""
    try:
        data = request.json
        
        new_source = ScraperSource(
            name=data.get('name'),
            url=data.get('url'),
            selector_config=data.get('selector_config', {}),
            is_active=data.get('is_active', True)
        )
        
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
    """Update a scraper source"""
    try:
        source = ScraperSource.query.get(id)
        if source is None:
            return jsonify({"error": "Scraper source not found"}), 404
        
        data = request.json
        
        if 'name' in data:
            source.name = data['name']
        if 'url' in data:
            source.url = data['url']
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
        # Run the scraping job
        result = run_scraping_job()
        
        # Record the scraping history
        history = ScraperHistory(
            start_time=result['start_time'],
            end_time=result['end_time'],
            sources_scraped=result['sources_scraped'],
            grants_found=result['grants_found'],
            grants_added=result['grants_added'],
            status=result['status'],
            error_message=result.get('error_message', '')
        )
        
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            "message": "Scraping job completed",
            "results": result
        })
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error during scraping: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error running scraper: {str(e)}")
        return jsonify({"error": "Failed to run scraper"}), 500

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
