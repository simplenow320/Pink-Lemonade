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
            
        # Create a serializable copy of grants and org_profile
        serializable_grants = []
        for grant in grants:
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
                
        # Prepare data for AI
        data = {
            "grants": serializable_grants,
            "org_profile": serializable_org
        }
        
        # System prompt for OpenAI
        system_prompt = """You are an AI grant matcher. Input two JSON items:
1. grants: an array of grants with title, summary, due_date, amount, eligibility_criteria
2. org_profile: an object with mission, focus_areas, funding_priorities
Score each grant 1 to 5 for fit with the profile. Return a JSON array sorted by score descending. Each item must include the grant data, score, and a one-sentence reason."""
        
        # Make API call to OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(data)}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse response
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