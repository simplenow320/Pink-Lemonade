import os

def is_live():
    """Check if the application is in live mode"""
    return os.environ.get("MODE", "DEMO").upper() == "LIVE"

def get_mode():
    """Get the current application mode"""
    return os.environ.get("MODE", "DEMO").upper()