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
            from flask import current_app
            
            # Use app context to ensure proper database session
            with current_app.app_context():
                # Delete all grants and related information
                db.session.query(Grant).delete()
                
                # Delete all organization profile data
                db.session.query(Organization).delete()
                
                # Delete all narratives
                db.session.query(Narrative).delete()
                
                # Delete all scraper sources and history
                db.session.query(ScraperSource).delete()
                db.session.query(ScraperHistory).delete()
                
                # Delete all analytics data
                db.session.query(GrantAnalytics).delete()
                db.session.query(GrantSuccessMetrics).delete()
                
                # Commit all changes
                db.session.commit()
                
            logger.info("Database tables cleared successfully - ALL FOUNDATION AND USER DATA ERASED")
        except Exception as db_error:
            logger.error(f"Error clearing database tables: {str(db_error)}")
        
        # PART 4: Look for and remove any other files that might contain foundation or grant info
        data_files = [
            'seed.json',  # Contains foundation sample data
            'foundation_data.json', 
            'discovered_grants.json',
            'user_profile.json',
            'scraped_grants.json',
            'org_profile.json',
            'grants_data.json',
            'grant_matches.json',
            'grant_stats.json'
        ]
        
        # Search in root directory and common subdirectories
        search_dirs = ['.', 'data', 'app/data', 'instance', 'static/data']
        
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                for file in data_files:
                    full_path = os.path.join(search_dir, file)
                    if os.path.exists(full_path):
                        try:
                            # If it's likely a JSON file, reset with empty structure
                            with open(full_path, 'w') as f:
                                if 'profile' in file.lower():
                                    json.dump({}, f)  # Empty object for profile files
                                else:
                                    json.dump([], f)  # Empty array for other data files
                                    
                            logger.info(f"IMPORTANT: Cleared foundation/user data in file: {full_path}")
                        except Exception as file_error:
                            logger.error(f"Error clearing file {full_path}: {str(file_error)}")
        
        # PART 5: Specifically handle the seed.json file in root which contains foundation data
        if os.path.exists('./seed.json'):
            try:
                # Completely empty the seed file to remove all test foundation data
                with open('./seed.json', 'w') as f:
                    json.dump([], f)
                logger.info("CRITICAL: Successfully erased all foundation data from seed.json")
            except Exception as seed_error:
                logger.error(f"Error clearing seed.json: {str(seed_error)}")
        
        # PART 6: Clear AI-generated content and analysis
        ai_files = [
            'grant_matches.json',
            'grant_analysis.json',
            'ai_narratives.json',
            'match_results.json',
            'openai_cache.json'
        ]
        
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                for file in ai_files:
                    full_path = os.path.join(search_dir, file)
                    if os.path.exists(full_path):
                        try:
                            # Empty all AI-related files
                            with open(full_path, 'w') as f:
                                json.dump([], f)
                            logger.info(f"Cleared AI-generated content from: {full_path}")
                        except Exception as ai_error:
                            logger.error(f"Error clearing AI file {full_path}: {str(ai_error)}")
                
        logger.info("COMPLETE: Mock data and ALL foundation/user information has been COMPLETELY ERASED")
        return "Mock data cleared"
        
    except Exception as e:
        logger.error(f"Error clearing mock data: {str(e)}")
        return f"Error clearing mock data: {str(e)}"

# Additional data service functions would go here