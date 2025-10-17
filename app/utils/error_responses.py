"""
Consistent error response utilities for organization profile issues
"""

def org_profile_error(message, missing_fields=None, profile_completeness=0, redirect_url='/profile'):
    """Return helpful error response for organization profile issues
    
    Args:
        message: Main error message
        missing_fields: List of missing field names
        profile_completeness: Percentage (0-100)
        redirect_url: Where to send user to fix the issue
    
    Returns:
        dict: Formatted error response
    """
    response = {
        'error': 'Organization Profile Required',
        'message': message,
        'profile_completeness': profile_completeness,
        'action': 'redirect',
        'url': redirect_url
    }
    
    if missing_fields:
        response['missing_fields'] = missing_fields
        response['help_text'] = f"Add these fields to enable AI matching: {', '.join(missing_fields)}"
    
    return response


def ai_match_prerequisites():
    """Return list of prerequisites for AI matching
    
    Returns:
        dict: Prerequisites information
    """
    return {
        'required_fields': ['mission', 'focus_areas', 'location', 'budget'],
        'minimum_completeness': 50,
        'help_url': '/help/ai-matching',
        'description': 'AI matching requires basic organization information to find relevant grants'
    }


def organization_not_found_error(user_id):
    """Return error for missing organization
    
    Args:
        user_id: The user ID that has no organization
    
    Returns:
        dict: Error response
    """
    return {
        'error': 'Organization Not Found',
        'message': 'No organization profile found. Please complete your profile to use AI matching.',
        'action': 'redirect',
        'url': '/profile',
        'user_id': user_id
    }


def incomplete_profile_error(missing_fields, completeness=0):
    """Return error for incomplete profile
    
    Args:
        missing_fields: List of missing field names
        completeness: Profile completion percentage
    
    Returns:
        dict: Error response
    """
    return org_profile_error(
        message=f"Your organization profile is {completeness}% complete.",
        missing_fields=missing_fields,
        profile_completeness=completeness
    )
