"""
Administrative API Endpoints for GrantFlow

This module provides API endpoints for administrative functions like clearing test data.
"""

import logging
from flask import Blueprint, jsonify, Response
from typing import Union, Tuple
# Removed unused logging imports
from app.services.data_service import clear_mock_data

# Create a blueprint for admin APIs
bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@bp.route('/clear-data', methods=['POST'])
def clear_all_data() -> Union[Response, Tuple[Response, int]]:
    """
    Clear all foundation grant and user profile data.
    
    This endpoint completely erases all foundation grant and user profile information
    from both the database and JSON files. This is a destructive operation and cannot
    be undone.
    
    Returns:
        Response: JSON response confirming data has been cleared.
        
    Error Codes:
        500: Server error occurred during the operation.
    """
    endpoint = "POST /api/admin/clear-data"
    logging.info(f"POST request to {endpoint}")
    
    try:
        # Call the clear_mock_data function from the data service
        result = clear_mock_data()
        
        logging.info(f"Successfully cleared mock data from {endpoint}")
        return jsonify({
            "message": "All foundation grant and user profile data has been completely erased",
            "status": "success",
            "details": result
        })
        
    except Exception as e:
        error_msg = f"Error clearing data: {str(e)}"
        logging.error(error_msg)
        logging.error(f"Error response from {endpoint}: {error_msg}")
        return jsonify({
            "error": "Failed to clear data",
            "details": str(e)
        }), 500