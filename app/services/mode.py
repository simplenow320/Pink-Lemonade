"""
Mode detection service for GrantFlow

This module provides utilities to determine if the application is running in LIVE or DEMO mode
based on the APP_DATA_MODE environment variable.
"""

import os
import logging

logger = logging.getLogger(__name__)

def is_live():
    """
    Check if the application is running in LIVE mode
    
    Returns:
        bool: True if APP_DATA_MODE is set to 'LIVE', False otherwise
    """
    mode = os.environ.get('APP_DATA_MODE', 'MOCK').upper()
    return mode == 'LIVE'

def get_mode():
    """
    Get the current application mode
    
    Returns:
        str: 'LIVE' or 'DEMO' based on APP_DATA_MODE environment variable
    """
    return 'LIVE' if is_live() else 'DEMO'

def enforce_live_mode():
    """
    Decorator to ensure a function only runs in LIVE mode
    
    Usage:
        @enforce_live_mode()
        def some_function():
            # This will only run if APP_DATA_MODE=LIVE
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if is_live():
                return func(*args, **kwargs)
            else:
                logger.info(f"Skipping {func.__name__} - not in LIVE mode")
                return None
        return wrapper
    return decorator