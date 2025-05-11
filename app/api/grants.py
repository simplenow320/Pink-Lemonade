from flask import Blueprint, request, jsonify, Response, abort, current_app as app
from app.models.grant import Grant
from app.models.organization import Organization
from app import db
from app.utils.helpers import parse_grant_data
from app.api import log_request, log_response
from app.services.ai_service import extract_grant_info, extract_grant_info_from_url
from app.services.match_service import match_grants
from app.services.writing_assistant_service import generate_narrative
from sqlalchemy.exc import SQLAlchemyError, NoResultFound, DataError
from sqlalchemy.orm.exc import MultipleResultsFound
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

bp = Blueprint('grants', __name__, url_prefix='/api/grants')

@bp.route('', methods=['GET'])
def get_grants() -> Union[Response, Tuple[Response, int]]:
    """
    Get all grants with optional filtering.
    
    Query Parameters:
        status (str, optional): Filter grants by status.
        sort_by (str, optional): Field to sort by. Default: 'due_date'.
        sort_dir (str, optional): Sort direction ('asc' or 'desc'). Default: 'asc'.
        
    Returns:
        Response: JSON response with list of grants.
        
    Error Codes:
        500: Server error occurred during request processing.
    """
    endpoint = f"{request.method} {request.path}"
    log_request(request.method, endpoint, dict(request.args))
    
    try:
        # Get query parameters for filtering
        status = request.args.get('status')
        sort_by = request.args.get('sort_by', 'due_date')
        sort_dir = request.args.get('sort_dir', 'asc')
        
        # Validate sort_by parameter
        if not hasattr(Grant, sort_by):
            log_response(endpoint, 400, f"Invalid sort_by parameter: {sort_by}")
            return jsonify({
                "error": f"Invalid sort_by parameter: {sort_by}",
                "valid_fields": [c.name for c in Grant.__table__.columns]
            }), 400
        
        # Start with a base query
        query = Grant.query
        
        # Apply filters if provided
        if status:
            query = query.filter(Grant.status == status)
        
        # Apply sorting
        if sort_dir.lower() not in ['asc', 'desc']:
            log_response(endpoint, 400, f"Invalid sort_dir parameter: {sort_dir}")
            return jsonify({
                "error": f"Invalid sort_dir parameter: {sort_dir}",
                "valid_values": ['asc', 'desc']
            }), 400
            
        if sort_dir.lower() == 'asc':
            query = query.order_by(getattr(Grant, sort_by))
        else:
            query = query.order_by(getattr(Grant, sort_by).desc())
        
        # Execute query and get results
        grants = query.all()
        
        # Convert to dictionary format
        result = [grant.to_dict() for grant in grants]
        
        log_response(endpoint, 200)
        return jsonify(result)
    
    except DataError as e:
        db.session.rollback()
        error_msg = f"Database query error: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 400, error_msg)
        return jsonify({"error": error_msg}), 400
        
    except SQLAlchemyError as e:
        db.session.rollback()
        error_msg = f"Database error fetching grants: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 500, error_msg)
        return jsonify({"error": "A database error occurred while fetching grants"}), 500
        
    except Exception as e:
        error_msg = f"Error fetching grants: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 500, error_msg)
        return jsonify({"error": "Failed to fetch grants"}), 500

@bp.route('', methods=['POST'])
def add_grant() -> Union[Response, Tuple[Response, int]]:
    """
    Add a new grant to the database.
    
    Request Body:
        title (str): The title of the grant. Required.
        funder (str): The organization providing the grant. Required.
        description (str, optional): Detailed description of the grant.
        amount (float, optional): The grant amount.
        due_date (str, optional): The due date in ISO format (YYYY-MM-DD).
        eligibility (str, optional): Eligibility criteria for the grant.
        website (str, optional): Website URL with more information.
        status (str, optional): Current application status. Default: 'Not Started'.
        match_score (float, optional): AI-calculated match score. Default: 0.
        notes (str, optional): Additional notes about the grant.
        focus_areas (list, optional): List of focus areas for the grant.
        contact_info (str, optional): Contact information for the grant.
        is_scraped (bool, optional): Whether the grant was scraped. Default: False.
        
    Returns:
        Response: JSON response with the newly created grant data.
        
    Error Codes:
        400: Invalid request data.
        500: Server error occurred during request processing.
    """
    endpoint = f"{request.method} {request.path}"
    log_request(request.method, endpoint, request.json)
    
    try:
        data = request.json
        
        # Validate required fields
        if not data:
            log_response(endpoint, 400, "No data provided")
            return jsonify({"error": "No data provided"}), 400
            
        if not data.get('title'):
            log_response(endpoint, 400, "Title is required")
            return jsonify({"error": "Title is required"}), 400
            
        if not data.get('funder'):
            log_response(endpoint, 400, "Funder is required")
            return jsonify({"error": "Funder is required"}), 400
        
        # Handle date conversion if provided
        due_date = None
        if data.get('due_date'):
            try:
                due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
            except ValueError:
                log_response(endpoint, 400, "Invalid date format. Use YYYY-MM-DD")
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Create new grant object
        new_grant = Grant(
            title=data.get('title'),
            funder=data.get('funder'),
            description=data.get('description'),
            amount=data.get('amount'),
            due_date=due_date,
            eligibility=data.get('eligibility'),
            website=data.get('website'),
            status=data.get('status', 'Not Started'),
            match_score=data.get('match_score', 0),
            match_explanation=data.get('match_explanation', ''),
            notes=data.get('notes', ''),
            focus_areas=data.get('focus_areas', []),
            contact_info=data.get('contact_info', ''),
            is_scraped=data.get('is_scraped', False)
        )
        
        # Add to database
        db.session.add(new_grant)
        db.session.commit()
        
        log_response(endpoint, 201)
        return jsonify(new_grant.to_dict()), 201
    
    except DataError as e:
        db.session.rollback()
        error_msg = f"Database field error: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 400, error_msg)
        return jsonify({"error": "Invalid data format"}), 400
        
    except SQLAlchemyError as e:
        db.session.rollback()
        error_msg = f"Database error adding grant: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 500, error_msg)
        return jsonify({"error": "A database error occurred while adding the grant"}), 500
        
    except Exception as e:
        if hasattr(db, 'session') and db.session:
            db.session.rollback()
        error_msg = f"Error adding grant: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 500, error_msg)
        return jsonify({"error": "Failed to add grant"}), 500

@bp.route('/<int:id>', methods=['GET'])
def get_grant(id):
    """Get a specific grant by ID"""
    try:
        grant = Grant.query.get(id)
        if grant is None:
            return jsonify({"error": "Grant not found"}), 404
        
        return jsonify(grant.to_dict())
    
    except Exception as e:
        logging.error(f"Error fetching grant {id}: {str(e)}")
        return jsonify({"error": "Failed to fetch grant"}), 500

@bp.route('/<int:id>', methods=['PUT'])
def update_grant(id):
    """Update a specific grant"""
    try:
        grant = Grant.query.get(id)
        if grant is None:
            return jsonify({"error": "Grant not found"}), 404
        
        data = request.json
        
        # Update grant fields if provided in request
        if 'title' in data:
            grant.title = data['title']
        if 'funder' in data:
            grant.funder = data['funder']
        if 'description' in data:
            grant.description = data['description']
        if 'amount' in data:
            grant.amount = data['amount']
        if 'due_date' in data:
            grant.due_date = data['due_date']
        if 'eligibility' in data:
            grant.eligibility = data['eligibility']
        if 'website' in data:
            grant.website = data['website']
        if 'status' in data:
            grant.status = data['status']
        if 'match_score' in data:
            grant.match_score = data['match_score']
        if 'notes' in data:
            grant.notes = data['notes']
        if 'focus_areas' in data:
            grant.focus_areas = data['focus_areas']
        if 'contact_info' in data:
            grant.contact_info = data['contact_info']
        
        db.session.commit()
        return jsonify(grant.to_dict())
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error updating grant {id}: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error updating grant {id}: {str(e)}")
        return jsonify({"error": "Failed to update grant"}), 500

@bp.route('/<int:id>/status', methods=['PUT'])
def update_grant_status(id):
    """
    Update the status of a specific grant
    
    Request Body:
        status (str): New status value (In Progress, Submitted, Approved, Rejected)
        
    Returns:
        Response: JSON response with the updated grant data
        
    Error Codes:
        400: Invalid status value
        404: Grant not found
        500: Server error during processing
    """
    endpoint = f"PUT /api/grants/{id}/status"
    log_request("PUT", endpoint, request.json)
    
    try:
        # Get the grant
        grant = Grant.query.get(id)
        if grant is None:
            log_response(endpoint, 404, "Grant not found")
            return jsonify({"error": "Grant not found"}), 404
        
        # Get data from request
        data = request.json
        if not data or 'status' not in data:
            log_response(endpoint, 400, "Status is required")
            return jsonify({"error": "Status is required"}), 400
        
        # Validate status
        valid_statuses = ["Not Started", "In Progress", "Submitted", "Approved", "Rejected"]
        if data['status'] not in valid_statuses:
            log_response(endpoint, 400, f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
            return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
        
        # Update the status using the model's method to ensure proper analytics tracking
        success = grant.update_status(data['status'])
        if not success:
            log_response(endpoint, 500, "Failed to update grant status")
            return jsonify({"error": "Failed to update grant status"}), 500
        
        # Commit the changes
        db.session.commit()
        
        log_response(endpoint, 200)
        return jsonify(grant.to_dict())
    
    except SQLAlchemyError as e:
        db.session.rollback()
        error_msg = f"Database error updating grant status for {id}: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 500, error_msg)
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        error_msg = f"Error updating grant status for {id}: {str(e)}"
        logging.error(error_msg)
        log_response(endpoint, 500, error_msg)
        return jsonify({"error": "Failed to update grant status"}), 500

@bp.route('/<int:id>', methods=['DELETE'])
def delete_grant(id):
    """Delete a specific grant"""
    try:
        grant = Grant.query.get(id)
        if grant is None:
            return jsonify({"error": "Grant not found"}), 404
        
        db.session.delete(grant)
        db.session.commit()
        
        return jsonify({"message": "Grant deleted successfully"}), 200
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error deleting grant {id}: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error deleting grant {id}: {str(e)}")
        return jsonify({"error": "Failed to delete grant"}), 500

@bp.route('/upload', methods=['POST'])
def upload_grant():
    """Process and extract grant information from uploaded file"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Only process PDF files
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Only PDF files are supported"}), 400
        
        # Parse the grant data from the file
        from app.services.ai_service import extract_grant_info
        file_content = file.read()
        grant_data = extract_grant_info(file_content)
        
        return jsonify(grant_data), 200
    
    except Exception as e:
        logging.error(f"Error processing uploaded grant: {str(e)}")
        return jsonify({"error": "Failed to process the grant file"}), 500

@bp.route('/url', methods=['POST'])
def process_grant_url():
    """Process and extract grant information from a URL"""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        # Parse the grant data from the URL
        from app.services.ai_service import extract_grant_info_from_url
        grant_data = extract_grant_info_from_url(url)
        
        return jsonify(grant_data), 200
    
    except Exception as e:
        logging.error(f"Error processing grant URL: {str(e)}")
        return jsonify({"error": "Failed to process the grant URL"}), 500

@bp.route('/seed', methods=['POST'])
def seed_grants():
    """Seed the database with sample grant data"""
    try:
        # Check if grants already exist
        existing_grants = Grant.query.count()
        if existing_grants > 0:
            return jsonify({"error": "Grants already exist in the database"}), 400
        
        # Load sample data from seed.json
        try:
            with open('seed.json', 'r') as f:
                seed_data = json.load(f)
                grants_data = seed_data.get('grants', [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error loading seed data: {str(e)}")
            return jsonify({"error": "Failed to load seed data"}), 500
        
        # Create grants from seed data
        added_grants = []
        for grant_data in grants_data:
            # Convert date string to date object
            due_date = None
            if grant_data.get('due_date'):
                try:
                    due_date = datetime.strptime(grant_data['due_date'], '%Y-%m-%d').date()
                except ValueError:
                    logging.warning(f"Invalid date format for grant: {grant_data.get('title')}")
            
            # Create new grant object
            new_grant = Grant(
                title=grant_data.get('title', ''),
                funder=grant_data.get('funder', ''),
                description=grant_data.get('description', ''),
                amount=grant_data.get('amount'),
                due_date=due_date,
                eligibility=grant_data.get('eligibility', ''),
                website=grant_data.get('website', ''),
                status=grant_data.get('status', 'Not Started'),
                match_score=grant_data.get('match_score', 0),
                match_explanation=grant_data.get('match_explanation', ''),
                focus_areas=grant_data.get('focus_areas', []),
                contact_info=grant_data.get('contact_info', ''),
                is_scraped=False
            )
            
            db.session.add(new_grant)
            added_grants.append(new_grant)
        
        db.session.commit()
        
        return jsonify({
            "message": f"Successfully seeded {len(added_grants)} grants",
            "grants": [grant.to_dict() for grant in added_grants]
        }), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error seeding grants: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error seeding grants: {str(e)}")
        return jsonify({"error": "Failed to seed grants"}), 500

@bp.route('/recently-discovered', methods=['GET'])
def get_recently_discovered():
    """Get recently discovered grants"""
    try:
        # Get query parameters
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # Get recently discovered grants
        from datetime import datetime, timedelta
        start_date = datetime.now() - timedelta(days=days)
        
        recent_grants = Grant.query.filter(
            Grant.is_scraped == True,
            Grant.created_at >= start_date
        ).order_by(Grant.created_at.desc()).limit(limit).all()
        
        result = [grant.to_dict() for grant in recent_grants]
        
        return jsonify({
            "count": len(result),
            "grants": result,
            "period_days": days
        })
    
    except Exception as e:
        logging.error(f"Error fetching recently discovered grants: {str(e)}")
        return jsonify({"error": "Failed to fetch recently discovered grants"}), 500

@bp.route('/extract', methods=['POST'])
def extract():
    """Extract structured grant information from text or URL"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Check if text or URL is provided
        if 'text' in data:
            # Extract from text
            grant_data = extract_grant_info(data['text'])
            return jsonify(grant_data)
        elif 'url' in data:
            # Extract from URL
            grant_data = extract_grant_info_from_url(data['url'])
            return jsonify(grant_data)
        else:
            return jsonify({"error": "Either text or URL must be provided"}), 400
    
    except Exception as e:
        logging.error(f"Error extracting grant information: {str(e)}")
        return jsonify({"error": "Failed to extract grant information"}), 500

@bp.route('/match', methods=['POST'])
def match():
    """Match a grant to the organization profile"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        grant_id = data.get('grant_id')
        if not grant_id:
            return jsonify({"error": "Grant ID is required"}), 400
        
        # Get the grant
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({"error": "Grant not found"}), 404
        
        # Get the organization profile
        org = Organization.query.first()
        if not org:
            return jsonify({"error": "Organization profile not found"}), 404
        
        # Match the grant with the organization
        match_result = match_grants(grant, org)
        
        return jsonify(match_result)
    
    except Exception as e:
        logging.error(f"Error matching grant: {str(e)}")
        return jsonify({"error": "Failed to match grant"}), 500

@bp.route('/write', methods=['POST'])
def write():
    """Generate a narrative for a grant"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        grant_id = data.get('grant_id')
        if not grant_id:
            return jsonify({"error": "Grant ID is required"}), 400
        
        section_type = data.get('section_type', 'overview')
        
        # Get the grant
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({"error": "Grant not found"}), 404
        
        # Get the organization profile
        org = Organization.query.first()
        if not org:
            return jsonify({"error": "Organization profile not found"}), 404
        
        # Generate the narrative
        narrative = generate_narrative(grant, org, section_type)
        
        return jsonify(narrative)
    
    except Exception as e:
        logging.error(f"Error generating narrative: {str(e)}")
        return jsonify({"error": "Failed to generate narrative"}), 500

@bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get statistics for the dashboard"""
    try:
        # Get counts by status
        status_counts = {}
        statuses = ['Not Started', 'In Progress', 'Submitted', 'Won', 'Declined']
        
        for status in statuses:
            count = Grant.query.filter_by(status=status).count()
            status_counts[status] = count
        
        # Get upcoming deadlines (next 30 days)
        from datetime import datetime, timedelta
        today = datetime.now().date()
        thirty_days_later = today + timedelta(days=30)
        
        upcoming_grants = Grant.query.filter(
            Grant.due_date >= today,
            Grant.due_date <= thirty_days_later,
            Grant.status.in_(['Not Started', 'In Progress'])
        ).order_by(Grant.due_date).limit(5).all()
        
        upcoming = [grant.to_dict() for grant in upcoming_grants]
        
        # Get total potential funding amount
        from sqlalchemy import func
        potential_funding = db.session.query(func.sum(Grant.amount)).filter(
            Grant.status.in_(['Not Started', 'In Progress'])
        ).scalar() or 0
        
        # Get won funding amount
        won_funding = db.session.query(func.sum(Grant.amount)).filter(
            Grant.status == 'Won'
        ).scalar() or 0
        
        # Get counts by matching score ranges
        match_ranges = {
            "90-100": Grant.query.filter(Grant.match_score >= 90).count(),
            "70-89": Grant.query.filter(Grant.match_score >= 70, Grant.match_score < 90).count(),
            "50-69": Grant.query.filter(Grant.match_score >= 50, Grant.match_score < 70).count(),
            "0-49": Grant.query.filter(Grant.match_score < 50).count()
        }
        
        # Get recently discovered grants (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_grants = Grant.query.filter(
            Grant.is_scraped == True,
            Grant.created_at >= seven_days_ago
        ).order_by(Grant.created_at.desc()).limit(5).all()
        
        recently_discovered = [grant.to_dict() for grant in recent_grants]
        
        # Add search metrics data
        search_metrics = {}
        try:
            # Get the latest scraper history with search data
            from app.models.scraper import ScraperHistory
            latest_history = ScraperHistory.query.filter(
                ScraperHistory.search_keywords_used.isnot(None),
                ScraperHistory.total_queries_attempted > 0
            ).order_by(ScraperHistory.start_time.desc()).first()
            
            if latest_history:
                # Count grants discovered through search
                search_discovered_count = Grant.query.filter(
                    Grant.discovery_method.in_(['web-search', 'focused-search'])
                ).count()
                
                search_metrics = {
                    "sites_searched": latest_history.sites_searched_estimate,
                    "search_success_rate": round((latest_history.successful_queries / latest_history.total_queries_attempted * 100), 1) 
                                       if latest_history.total_queries_attempted > 0 else 0,
                    "discovered_grants_count": search_discovered_count,
                    "last_search_date": latest_history.end_time.isoformat() if latest_history.end_time else None
                }
        except Exception as search_e:
            logging.error(f"Error getting search metrics for dashboard: {str(search_e)}")
            search_metrics = {
                "error": "Could not retrieve search metrics"
            }
        
        dashboard_data = {
            "status_counts": status_counts,
            "upcoming_deadlines": upcoming,
            "potential_funding": potential_funding,
            "won_funding": won_funding,
            "match_score_distribution": match_ranges,
            "total_grants": Grant.query.count(),
            "recently_discovered": recently_discovered,
            "search_metrics": search_metrics
        }
        
        return jsonify(dashboard_data)
    
    except Exception as e:
        logging.error(f"Error fetching dashboard data: {str(e)}")
        return jsonify({"error": "Failed to fetch dashboard data"}), 500
