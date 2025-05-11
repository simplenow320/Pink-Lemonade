"""
Data Service Module for GrantFlow

This module provides functionality for managing data storage and retrieval,
including functions for working with mock data for testing.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

# File paths for data storage
GRANTS_FILE = 'grants.json'
ORG_PROFILE_FILE = 'org_profile.json'
MANUAL_SOURCES_FILE = 'manual_sources.json'
GRANT_RESULTS_FILE = 'grant_results.json'

# In-memory mock data structures that might be used in testing
mock_grants = []
mock_sources = []
mock_results = []
mock_profile = {}

def clear_mock_data():
    """
    Clear all mock data files and reset in-memory test data structures.
    
    This function:
    1. Overwrites grants.json, org_profile.json, manual_sources.json, and grant_results.json
       with empty data structures ([] or {} as appropriate)
    2. Resets any in-memory test data structures to empty
    3. Logs the operation
    4. CRITICAL: Completely erases all foundation grant and user profile information
    
    Returns:
        str: A message confirming data has been cleared
    """
    try:
        # PART 1: Reset the JSON files with empty data structures
        
        # Reset grants.json with empty array - ERASE ALL GRANT DATA
        with open(GRANTS_FILE, 'w') as f:
            json.dump([], f)
            
        # Reset org_profile.json with empty object - ERASE ALL USER PROFILE DATA
        with open(ORG_PROFILE_FILE, 'w') as f:
            json.dump({}, f)
            
        # Reset manual_sources.json with empty array - ERASE ALL FOUNDATION DATA
        with open(MANUAL_SOURCES_FILE, 'w') as f:
            json.dump([], f)
            
        # Reset grant_results.json with empty array - ERASE ALL RESULT DATA
        with open(GRANT_RESULTS_FILE, 'w') as f:
            json.dump([], f)
        
        # PART 2: Reset in-memory data structures
        global mock_grants, mock_sources, mock_results, mock_profile
        mock_grants = []
        mock_sources = []
        mock_results = []
        mock_profile = {}
        
        # PART 3: Clear database tables using SQLAlchemy
        try:
            from app import db
            from app.models.grant import Grant
            from app.models.organization import Organization
            from app.models.narrative import Narrative
            from app.models.scraper import ScraperSource, ScraperHistory
            from app.models.analytics import GrantAnalytics, GrantSuccessMetrics
            
            with db.session() as session:
                # Delete all grants and related information
                session.query(Grant).delete()
                
                # Delete all organization profile data
                session.query(Organization).delete()
                
                # Delete all narratives
                session.query(Narrative).delete()
                
                # Delete all scraper sources and history
                session.query(ScraperSource).delete()
                session.query(ScraperHistory).delete()
                
                # Delete all analytics data
                session.query(GrantAnalytics).delete()
                session.query(GrantSuccessMetrics).delete()
                
                # Commit all changes
                session.commit()
                
            logger.info("Database tables cleared successfully")
        except Exception as db_error:
            logger.error(f"Error clearing database tables: {str(db_error)}")
        
        # PART 4: Look for and remove any other files that might contain foundation or grant info
        data_files = [
            'seed.json',
            'foundation_data.json', 
            'discovered_grants.json',
            'user_profile.json',
            'scraped_grants.json'
        ]
        
        for file in data_files:
            if os.path.exists(file):
                try:
                    # If it's likely a JSON file, reset with empty structure
                    with open(file, 'w') as f:
                        if file.endswith('_profile.json'):
                            json.dump({}, f)  # Empty object for profile
                        else:
                            json.dump([], f)  # Empty array for other data
                    logger.info(f"Cleared additional file: {file}")
                except Exception as file_error:
                    logger.error(f"Error clearing file {file}: {str(file_error)}")
        
        logger.info("Mock data and all foundation/user information cleared successfully")
        return "Mock data cleared"
        
    except Exception as e:
        logger.error(f"Error clearing mock data: {str(e)}")
        return f"Error clearing mock data: {str(e)}"

# Additional data service functions would go here