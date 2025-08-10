"""
Simple Organization Profile API - Working implementation
"""

from flask import Blueprint, request, jsonify
from app import db
from app.models import Org
from app.models_extended import OrgProfile
import logging
import json

bp = Blueprint('simple_org', __name__, url_prefix='/api/profile')

@bp.route('/organization', methods=['GET'])
def get_organization():
    """Get organization profile - working version with extended data"""
    try:
        # Get the basic org first
        org = Org.query.first()
        if not org:
            return jsonify({
                'name': '',
                'mission': '',
                'focus_areas': [],
                'keywords': [],
                'location': '',
                'website': '',
                'annual_budget': '',
                'profile_complete': False
            })
        
        # Get extended profile
        profile = OrgProfile.query.filter_by(org_id=org.id).first()
        if not profile:
            # Return basic org data
            return jsonify({
                'name': org.name or '',
                'mission': org.mission or '',
                'focus_areas': [],
                'keywords': [],
                'location': '',
                'website': '',
                'annual_budget': '',
                'profile_complete': False
            })
        
        # Return full profile data
        return jsonify(profile.to_dict())
        
    except Exception as e:
        logging.error(f"Error getting organization: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/organization', methods=['POST'])
def save_organization():
    """Save organization profile - working version with extended data"""
    try:
        data = request.json
        
        # Get or create basic organization
        org = Org.query.first()
        if not org:
            org = Org(name=data.get('name', ''), mission=data.get('mission', ''))
            db.session.add(org)
            db.session.flush()  # Get the ID
        else:
            # Update basic org
            org.name = data.get('name', org.name)
            org.mission = data.get('mission', org.mission)
        
        # Get or create extended profile
        profile = OrgProfile.query.filter_by(org_id=org.id).first()
        if not profile:
            profile = OrgProfile(org_id=org.id)
            db.session.add(profile)
        
        # Update profile fields
        profile.name = data.get('name', '')
        profile.mission = data.get('mission', '')
        profile.location = data.get('location', '')
        profile.website = data.get('website', '')
        profile.annual_budget = data.get('annual_budget', '')
        
        # Handle focus areas
        focus_areas = data.get('focus_areas', [])
        if isinstance(focus_areas, str) and focus_areas.strip():
            # Split comma-separated string
            focus_areas = [area.strip() for area in focus_areas.split(',') if area.strip()]
        elif not isinstance(focus_areas, list):
            focus_areas = []
        profile.focus_areas = focus_areas
        
        # Handle keywords
        keywords = data.get('keywords', [])
        if isinstance(keywords, str) and keywords.strip():
            # Split comma-separated string
            keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        elif not isinstance(keywords, list):
            keywords = []
        profile.keywords = keywords
        
        # Calculate profile completeness
        completeness = profile.calculate_completeness()
        profile.profile_complete = completeness >= 80
        
        db.session.commit()
        
        logging.info(f"Organization profile saved: {profile.name} ({completeness}% complete)")
        
        return jsonify({
            'message': 'Organization profile saved successfully',
            'profile_complete': profile.profile_complete,
            'completeness': completeness,
            'data': profile.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error saving organization: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/ai-context', methods=['GET'])
def get_ai_context():
    """Show how organization profile is used for AI matching"""
    try:
        org = Org.query.first()
        if not org:
            return jsonify({
                'context': 'No organization profile set up yet',
                'status': 'incomplete',
                'message': 'Please complete your organization profile for personalized AI matching'
            })
        
        profile = OrgProfile.query.filter_by(org_id=org.id).first()
        if not profile:
            return jsonify({
                'context': f"Organization: {org.name}\nMission: {org.mission or 'Not specified'}\n\nProfile incomplete - please add focus areas and keywords for better AI matching",
                'status': 'incomplete',
                'message': 'Add focus areas and keywords to improve AI grant matching'
            })
        
        # Get AI context string
        context_text = profile.get_ai_context_string()
        completeness = profile.calculate_completeness()
        
        return jsonify({
            'context': context_text,
            'status': 'ready' if profile.profile_complete else 'incomplete',
            'message': f'This profile information is used by AI to match grants specifically for your organization ({completeness}% complete)',
            'profile_complete': profile.profile_complete,
            'completeness': completeness
        })
        
    except Exception as e:
        logging.error(f"Error getting AI context: {e}")
        return jsonify({'error': str(e)}), 500