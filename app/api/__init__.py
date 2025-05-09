"""
API Blueprint Initialization Module

This module initializes the API blueprints and provides logging configuration
for the API endpoints.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging for API operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create a logger for API operations
api_logger = logging.getLogger("api")

def log_request(request_type: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Log API request details
    
    Args:
        request_type: The HTTP method (GET, POST, etc.)
        endpoint: The API endpoint being accessed
        data: Optional request data to log (sensitive data should be filtered)
    """
    if data is None:
        data = {}
    
    # Filter sensitive data
    filtered_data = {
        k: "******" if k.lower() in ["password", "api_key", "secret", "token"] else v
        for k, v in data.items()
    }
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event": "api_request",
        "request_type": request_type,
        "endpoint": endpoint,
        "data": filtered_data
    }
    
    api_logger.info(json.dumps(log_entry))

def log_response(endpoint: str, status_code: int, error: Optional[str] = None) -> None:
    """
    Log API response details
    
    Args:
        endpoint: The API endpoint that responded
        status_code: The HTTP status code
        error: Optional error message if applicable
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event": "api_response",
        "endpoint": endpoint,
        "status_code": status_code
    }
    
    if error:
        log_entry["error"] = error
        api_logger.error(json.dumps(log_entry))
    else:
        api_logger.info(json.dumps(log_entry))