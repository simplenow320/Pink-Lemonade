from flask import Blueprint, request, jsonify
from app.models.scraper import ScraperSource, ScraperHistory
from app.models.grant import Grant
from app import db
from app.services.scraper_service import run_scraping_job
from sqlalchemy.exc import SQLAlchemyError
import logging
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
