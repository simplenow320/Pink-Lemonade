import os
import json
import logging
from datetime import datetime
from openai import OpenAI

# Initialize OpenAI client if API key is available
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = None

# Only initialize OpenAI if API key is provided
if OPENAI_API_KEY:
    openai = OpenAI(api_key=OPENAI_API_KEY)

def match_grants(grants, org_profile):
    """
    Match grants to organization profile using OpenAI
    
    Args:
        grants (list): List of grant dictionaries
        org_profile (dict): Organization profile
        
    Returns:
        list: Sorted list of grants with match scores
    """
    try:
        # Check if OpenAI is available
        if not openai:
            logging.warning("OpenAI API key not configured. Cannot match grants.")
            # Return grants as-is with default score of 0
            for grant in grants:
                grant["score"] = 0
                grant["reason"] = "AI matching unavailable - API key not configured."
            return grants
        
        # 1. Load manual_sources.json if it exists
        manual_sources = []
        try:
            if os.path.exists('manual_sources.json'):
                with open('manual_sources.json', 'r') as f:
                    manual_sources = json.load(f)
        except Exception as e:
            logging.error(f"Error loading manual sources: {str(e)}")
        
        # 2. Add any manual sources to grants_list if not already present
        grants_list = list(grants)  # Create a copy of grants list
        
        # Create a set of existing grant names for quick lookup
        existing_grant_names = {grant.get('name', '') for grant in grants_list}
        
        # Add manual sources that aren't already in grants_list
        for source in manual_sources:
            if source.get('name') and source.get('name') not in existing_grant_names:
                # Convert source to a grant-like object
                new_grant = {
                    'name': source.get('name', ''),
                    'title': source.get('name', ''),
                    'url': source.get('url', ''),
                    'source': 'manual',
                    'is_manual_source': True
                }
                grants_list.append(new_grant)
                
        # Create a serializable copy of grants and org_profile
        serializable_grants = []
        for grant in grants_list:
            # Convert date objects to strings
            serializable_grant = {}
            for key, value in grant.items():
                if hasattr(value, 'isoformat'):  # Check if it's a date-like object
                    serializable_grant[key] = value.isoformat()
                else:
                    serializable_grant[key] = value
            serializable_grants.append(serializable_grant)
            
        serializable_org = {}
        for key, value in org_profile.items():
            # Convert date objects to strings
            if hasattr(value, 'isoformat'):  # Check if it's a date-like object
                serializable_org[key] = value.isoformat()
            else:
                serializable_org[key] = value
                
        # 3. Prepare data for AI
        data = {
            "grants": serializable_grants,
            "org_profile": serializable_org
        }
        
        # System prompt for OpenAI
        system_prompt = """You are an AI grant matcher. Input:
1. grants: an array of grant objects (including manual sources)
2. org_profile: {mission, focus_areas, funding_priorities}
Score each grant 1 to 5 for fit and return a JSON array sorted by score desc. Each item includes the grant data, score, and a one-sentence reason."""
        
        # Make API call to OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(data)}
            ],
            response_format={"type": "json_object"}
        )
        
        # 4. Parse response and return sorted list
        result = json.loads(response.choices[0].message.content)
        
        # Get the array from the result
        matched_grants = []
        for key, value in result.items():
            if isinstance(value, list) and len(value) > 0:
                matched_grants = value
                break
        
        # If we didn't find an array, the whole result might be an array
        if not matched_grants and isinstance(result, list):
            matched_grants = result
            
        # Convert any date strings back to date objects
        for grant in matched_grants:
            if grant.get('due_date'):
                try:
                    date_str = grant['due_date']
                    if isinstance(date_str, str):
                        grant['due_date'] = datetime.strptime(date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    # Keep as string if conversion fails
                    pass
        
        return matched_grants
        
    except Exception as e:
        logging.error(f"Error matching grants: {str(e)}")
        # Return grants as-is with error message
        for grant in grants:
            grant["score"] = 0
            grant["reason"] = f"Error in AI matching: {str(e)}"
        return grants