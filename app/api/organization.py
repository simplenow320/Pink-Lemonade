from flask import Blueprint, request, jsonify
from app.models import Organization
from app import db
from sqlalchemy.exc import SQLAlchemyError
import logging
import json

bp = Blueprint('organization', __name__, url_prefix='/api/organization')

@bp.route('', methods=['GET'])
def get_organization():
    """Get organization profile"""
    try:
        # Get the organization profile
        # Assume we only have one organization profile in the system
        org = Organization.query.first()
        
        if org is None:
            return jsonify({"error": "Organization profile not found"}), 404
        
        return jsonify(org.to_dict())
    
    except Exception as e:
        logging.error(f"Error fetching organization profile: {str(e)}")
        return jsonify({"error": "Failed to fetch organization profile"}), 500

@bp.route('', methods=['PUT', 'POST'])
def update_organization():
    """Update organization profile"""
    try:
        data = request.json
        
        # Get the organization profile (or create if it doesn't exist)
        org = Organization.query.first()
        
        if org is None:
            # Create new organization profile
            org = Organization(
                name=data.get('name', ''),
                mission=data.get('mission', ''),
                website=data.get('website', ''),
                location=data.get('location', {}),
                founding_year=data.get('founding_year'),
                team=data.get('team', []),
                focus_areas=data.get('focus_areas', []),
                keywords=data.get('keywords', []),
                past_programs=data.get('past_programs', []),
                financials=data.get('financials', {}),
                case_for_support=data.get('case_for_support', '')
            )
            db.session.add(org)
        else:
            # Update existing organization profile
            if 'name' in data:
                org.name = data['name']
            if 'mission' in data:
                org.mission = data['mission']
            if 'website' in data:
                org.website = data['website']
            if 'location' in data:
                org.location = data['location']
            if 'founding_year' in data:
                org.founding_year = data['founding_year']
            if 'team' in data:
                org.team = data['team']
            if 'focus_areas' in data:
                org.focus_areas = data['focus_areas']
            if 'keywords' in data:
                org.keywords = data['keywords']
            if 'past_programs' in data:
                org.past_programs = data['past_programs']
            if 'financials' in data:
                org.financials = data['financials']
            if 'case_for_support' in data:
                org.case_for_support = data['case_for_support']
        
        db.session.commit()
        
        return jsonify(org.to_dict())
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error updating organization profile: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error updating organization profile: {str(e)}")
        return jsonify({"error": "Failed to update organization profile"}), 500

@bp.route('/seed', methods=['POST'])
def seed_organization():
    """Seed the organization profile with sample data"""
    try:
        # Check if organization already exists
        existing_org = Organization.query.first()
        if existing_org:
            return jsonify({"error": "Organization profile already exists"}), 400
        
        # Load sample data from seed.json
        try:
            with open('seed.json', 'r') as f:
                seed_data = json.load(f)
                org_data = seed_data.get('organization', {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error loading seed data: {str(e)}")
            return jsonify({"error": "Failed to load seed data"}), 500
        
        # Create new organization with seed data
        new_org = Organization(
            name=org_data.get('name', ''),
            mission=org_data.get('mission', ''),
            website=org_data.get('website', ''),
            location=org_data.get('location', {}),
            founding_year=org_data.get('founding_year'),
            team=org_data.get('team', []),
            focus_areas=org_data.get('focus_areas', []),
            keywords=org_data.get('keywords', []),
            past_programs=org_data.get('past_programs', []),
            financials=org_data.get('financials', {}),
            case_for_support=org_data.get('case_for_support', '')
        )
        
        db.session.add(new_org)
        db.session.commit()
        
        return jsonify({"message": "Organization profile seeded successfully", "data": new_org.to_dict()}), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Database error seeding organization profile: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error seeding organization profile: {str(e)}")
        return jsonify({"error": "Failed to seed organization profile"}), 500
