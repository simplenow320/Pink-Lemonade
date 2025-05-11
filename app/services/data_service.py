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
    
    Returns:
        str: A message confirming data has been cleared
    """
    # Reset the JSON files with empty data structures
    try:
        # Reset grants.json with empty array
        with open(GRANTS_FILE, 'w') as f:
            json.dump([], f)
            
        # Reset org_profile.json with empty object
        with open(ORG_PROFILE_FILE, 'w') as f:
            json.dump({}, f)
            
        # Reset manual_sources.json with empty array
        with open(MANUAL_SOURCES_FILE, 'w') as f:
            json.dump([], f)
            
        # Reset grant_results.json with empty array
        with open(GRANT_RESULTS_FILE, 'w') as f:
            json.dump([], f)
        
        # Reset in-memory data structures
        global mock_grants, mock_sources, mock_results, mock_profile
        mock_grants = []
        mock_sources = []
        mock_results = []
        mock_profile = {}
        
        logger.info("Mock data cleared successfully")
        return "Mock data cleared"
        
    except Exception as e:
        logger.error(f"Error clearing mock data: {str(e)}")
        return f"Error clearing mock data: {str(e)}"

# Additional data service functions would go here