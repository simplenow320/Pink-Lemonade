from datetime import datetime
import pytz
from app.services.auth_manager import AuthManager

def format_user_date(dt, format_str='%b %d, %Y'):
    """Format datetime according to user's timezone"""
    if not dt:
        return 'TBA'

    user = AuthManager.get_current_user()
    if user and user.timezone:
        try:
            tz = pytz.timezone(user.timezone)
            dt = dt.astimezone(tz)
        except:
            pass

    return dt.strftime(format_str)