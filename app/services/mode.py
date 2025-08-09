import os

def is_live() -> bool:
    return os.getenv("APP_DATA_MODE", "LIVE").upper() == "LIVE"

def require_live_or_404(live: bool):
    if not live:
        from flask import abort
        abort(404, description="Feature unavailable in DEMO mode")