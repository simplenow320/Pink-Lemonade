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
    # 1. Overwrites JSON files with empty structures
    with open(GRANTS_FILE, 'w') as f:
        json.dump([], f)
        
    with open(ORG_PROFILE_FILE, 'w') as f:
        json.dump({}, f)
        
    with open(MANUAL_SOURCES_FILE, 'w') as f:
        json.dump([], f)
        
    with open(GRANT_RESULTS_FILE, 'w') as f:
        json.dump([], f)
    
    # 2. Reset in-memory test data structures
    global mock_grants, mock_sources, mock_results, mock_profile
    mock_grants = []
    mock_sources = []
    mock_results = []
    mock_profile = {}
    
    # 3. Log the operation
    logger.info("Mock data cleared")
    
    return "Mock data cleared"

# Additional data service functions would go here