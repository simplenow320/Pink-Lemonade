"""
Production mode service for Pink Lemonade

This module ensures the application always operates in production mode with real data only.
No demo or mock data functionality is supported.
"""

import os
import logging

logger = logging.getLogger(__name__)

def is_live():
    """
    Always returns True - the application only operates in production mode
    
    Returns:
        bool: Always True - no demo mode supported
    """
    return True

def get_mode():
    """
    Always returns 'LIVE' - no demo mode supported
    
    Returns:
        str: Always 'LIVE'
    """
    return 'LIVE'

def enforce_live_mode():
    """
    Decorator for functions that require live mode (always runs since we're always live)
    
    Usage:
        @enforce_live_mode()
        def some_function():
            # This always runs since we're always in live mode
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator