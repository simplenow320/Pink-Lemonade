from flask import Blueprint, request, jsonify
import json
import os
import logging

bp = Blueprint('profile', __name__, url_prefix='/api/profile')

@bp.route('', methods=['GET'])
def get_profile():
    """
    Load and return the organization profile from org_profile.json
    
    Returns:
        Response: JSON with organization profile data
    """
    try:
        # Check if the profile file exists
        if not os.path.exists('org_profile.json'):
            # Return empty profile if file doesn't exist
            return jsonify({
                "mission": "",
                "focus_areas": [],
                "funding_priorities": []
            })
        
        # Read the profile file
        with open('org_profile.json', 'r') as f:
            profile_data = json.load(f)
        
        return jsonify(profile_data)
    
    except Exception as e:
        logging.error(f"Error loading organization profile: {str(e)}")
        return jsonify({"error": "Failed to load organization profile"}), 500

@bp.route('', methods=['POST'])
def update_profile():
    """
    Update the organization profile
    
    Request Body:
        mission (str): Organization mission statement
        focus_areas (list): List of focus areas
        funding_priorities (list): List of funding priorities
        
    Returns:
        Response: JSON with updated profile data
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ['mission', 'focus_areas', 'funding_priorities']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create profile object
        profile = {
            "mission": data['mission'],
            "focus_areas": data['focus_areas'],
            "funding_priorities": data['funding_priorities']
        }
        
        # Write to file
        with open('org_profile.json', 'w') as f:
            json.dump(profile, f, indent=2)
        
        return jsonify(profile)
    
    except Exception as e:
        logging.error(f"Error updating organization profile: {str(e)}")
        return jsonify({"error": "Failed to update organization profile"}), 500