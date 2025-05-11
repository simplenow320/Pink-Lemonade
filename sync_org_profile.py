"""
Synchronize Organization Profile

This script synchronizes the organization profile from org_profile.json to the database.
It needs to be run after the import_agent.py script has updated the JSON files.
"""

import json
import logging
import os
import sys
from app import db
from app.models.organization import Organization

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_profile():
    """
    Sync the organization profile from org_profile.json to the database
    """
    try:
        # Check if org_profile.json exists
        if not os.path.exists('org_profile.json'):
            logger.error("org_profile.json not found")
            return False
        
        # Read the org_profile.json file
        with open('org_profile.json', 'r') as f:
            org_data = json.load(f)
        
        # Get or create Organization record
        org = Organization.query.first()
        if org is None:
            # Create new organization
            org = Organization(
                name=org_data.get('name', ''),
                mission=org_data.get('mission', ''),
                website=org_data.get('website', ''),
                focus_areas=org_data.get('focus_areas', []),
                keywords=org_data.get('keywords', []),
                location={
                    'city': '',
                    'state': '',
                    'zip': ''
                }
            )
            db.session.add(org)
            logger.info("Created new organization profile")
        else:
            # Update existing organization
            org.name = org_data.get('name', org.name)
            org.mission = org_data.get('mission', org.mission)
            org.website = org_data.get('website', org.website)
            org.focus_areas = org_data.get('focus_areas', org.focus_areas)
            org.keywords = org_data.get('keywords', org.keywords)
            logger.info("Updated existing organization profile")
        
        # If the JSON has additional fields, map them to the Organization model
        if 'vision' in org_data:
            # Add vision to the case_for_support field
            org.case_for_support = org_data.get('vision', '')
        
        # Commit the changes
        db.session.commit()
        logger.info("Organization profile synchronized successfully")
        return True
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error synchronizing organization profile: {str(e)}")
        return False

def main():
    """
    Main function
    """
    from app import create_app
    app = create_app()
    
    with app.app_context():
        success = sync_profile()
        if success:
            print("Organization profile synchronized successfully")
            return 0
        else:
            print("Failed to synchronize organization profile")
            return 1

if __name__ == "__main__":
    sys.exit(main())