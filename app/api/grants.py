from flask import Blueprint, request, jsonify
from app.models.grant import Grant
from app import db
from app.utils.helpers import parse_grant_data
from sqlalchemy.exc import SQLAlchemyError
import logging

bp = Blueprint('grants', __name__, url_prefix='/api/grants')

@bp.route('', methods=['GET'])
def get_grants():
    """Get all grants with optional filtering"""
    try:
        # Get query parameters for filtering
        status = request.args.get('status')
        sort_by = request.args.get('sort_by', 'due_date')
        sort_dir = request.args.get('sort_dir', 'asc')
        
        # Start with a base query
        query = Grant.query
        
        # Apply filters if provided
        if status:
            query = query.filter(Grant.status == status)
        
        # Apply sorting
        if sort_dir == 'asc':
            query = query.order_by(getattr(Grant, sort_by))
        else:
            query = query.order_by(getattr(Grant, sort_by).desc())
        
        # Execute query and get results
        grants = query.all()
        
        # Convert to dictionary format
        result = [grant.to_dict() for grant in grants]
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error fetching grants: {str(e)}")
        return jsonify({"error": "Failed to fetch grants"}), 500

@bp.route('', methods=['POST'])
def add_grant():
    """Add a new grant"""
    try:
        data = request.json
        
        # Create new grant object
        new_grant = Grant(
            title=data.get('title'),
            funder=data.get('funder'),
            description=data.get('description'),
            amount=data.get('amount'),
            due_date=data.get('due_date'),
            eligibility=data.get('eligibility'),
            website=data.get('website'),
            status=data.get('status', 'Not Started'),
            match_score=data.get('match_score', 0),
            notes=data.get('notes', ''),
            focus_areas=data.get('focus_areas', []),
            contact_info=data.get('contact_info', ''),
            is_scraped=data.get('is_scraped', False)
        )
        
        # Add to database
        db.session.add(new_grant)
        db.session.commit()
        
        return jsonify(new_grant.to_dict()), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error adding grant: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error adding grant: {str(e)}")
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
        
        dashboard_data = {
            "status_counts": status_counts,
            "upcoming_deadlines": upcoming,
            "potential_funding": potential_funding,
            "won_funding": won_funding,
            "match_score_distribution": match_ranges,
            "total_grants": Grant.query.count()
        }
        
        return jsonify(dashboard_data)
    
    except Exception as e:
        logging.error(f"Error fetching dashboard data: {str(e)}")
        return jsonify({"error": "Failed to fetch dashboard data"}), 500
