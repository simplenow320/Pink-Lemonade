import os
import logging
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import trafilatura

# Initialize OpenAI client if API key is available
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = None

# Only initialize OpenAI if API key is provided
if OPENAI_API_KEY:
    from openai import OpenAI
    openai = OpenAI(api_key=OPENAI_API_KEY)

def extract_grant_info(grant_url):
    """
    Extract structured grant information from text using OpenAI
    
    Args:
        grant_url (str): The URL containing grant information
        
    Returns:
        dict: Structured grant information
    """
    try:
        # Check if OpenAI is available
        if not openai:
            return {
                "error": "OpenAI API key not configured",
                "title": "Unknown Grant",
                "funder": "Unknown",
                "description": "Grant information unavailable without OpenAI API key",
                "requires_api_key": True
            }
            
        system_prompt = """You are an AI data extractor specialized in grant information. Your task is to extract comprehensive details about grants from provided text. 

Extract the following information and return as a JSON object:
1. title: Full name of the grant program (required)
2. funder: Name of the organization providing the grant (required)
3. description: Detailed summary of what the grant funds and its purpose
4. amount: Funding amount as a number (without currency symbols)
5. due_date: Application deadline in YYYY-MM-DD format
6. eligibility: Who can apply for this grant
7. website: Direct URL to the grant information page
8. focus_areas: Array of focus areas or categories this grant supports
9. contact_info: Comprehensive contact information including:
   - contact_name: Name of the contact person
   - contact_email: Email address for inquiries
   - contact_phone: Phone number for inquiries
   - contact_position: Position/title of the contact person
10. application_process: Description of how to apply
11. grant_duration: Period the grant covers (if specified)

Be thorough in extracting all available contact information as this is critically important."""
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": grant_url}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        result = json.loads(content if content else "{}")
        
        return result
    
    except Exception as e:
        logging.error(f"Error extracting grant information: {str(e)}")
        return {
            "error": "Could not extract grant information",
            "title": "Unknown Grant",
            "funder": "Unknown",
            "description": f"Error: {str(e)}"
        }

def extract_grant_info_from_url(url):
    """
    Extract grant information from a URL
    
    Args:
        url (str): The URL to extract grant information from
        
    Returns:
        dict: Structured grant information
    """
    try:
        # Fetch web content
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise Exception("Failed to download the URL")
        
        # Extract main content
        text = trafilatura.extract(downloaded)
        if not text:
            # Fallback to simple HTML parsing
            response = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            text = soup.get_text(separator=' ', strip=True)
        
        # Process with the AI
        grant_info = extract_grant_info(text)
        
        # Add the source URL
        grant_info['website'] = url
        
        return grant_info
    
    except Exception as e:
        logging.error(f"Error extracting grant from URL {url}: {str(e)}")
        return {
            "error": f"Could not extract grant information from URL: {str(e)}",
            "title": "Unknown Grant",
            "funder": "Unknown",
            "website": url
        }

def analyze_grant_match(grant, organization):
    """
    Analyze how well a grant matches the organization profile
    
    Args:
        grant (dict): The grant information
        organization (dict): The organization profile
        
    Returns:
        dict: Match analysis with score and explanation
    """
    try:
        # Check if OpenAI is available
        if not openai:
            return {
                "score": 0,
                "explanation": "OpenAI API key not configured",
                "error": "OpenAI API key required for grant matching",
                "requires_api_key": True
            }
        
        # Create a serializable copy of grant data
        serializable_grant = {}
        for key, value in grant.items():
            # Convert date objects to strings
            if hasattr(value, 'isoformat'):  # Check if it's a date-like object
                serializable_grant[key] = value.isoformat()
            else:
                serializable_grant[key] = value
        
        # Create a serializable copy of organization data
        serializable_org = {}
        for key, value in organization.items():
            # Convert date objects to strings
            if hasattr(value, 'isoformat'):  # Check if it's a date-like object
                serializable_org[key] = value.isoformat()
            else:
                serializable_org[key] = value
            
        system_prompt = """
        You are an expert grant consultant for nonprofits. Your task is to analyze how well a grant opportunity 
        matches a nonprofit organization's profile and provide a match score and detailed explanation.
        
        Consider the following factors:
        1. Alignment of focus areas - How well do the organization's focus areas match the grant's focus areas?
        2. Mission alignment - Does the grant purpose align with the organization's mission?
        3. Eligibility - Does the organization meet the grant's eligibility requirements?
        4. Organization history - Does the organization have relevant experience and past programs?
        5. Grant amount - Is the grant amount appropriate for the organization's size and capacity?
        
        Provide the following in your response as a JSON object:
        1. score: A numeric score from 0-100 indicating the match percentage
        2. explanation: A detailed explanation of why the grant does or doesn't match the organization
        3. strengths: Key organizational strengths in relation to this grant
        4. weaknesses: Areas where the organization may be less competitive
        5. recommendations: Suggestions for strengthening an application
        """
        
        user_prompt = f"""
        Analyze the match between this grant and organization and respond with a JSON object:
        
        Grant: {json.dumps(serializable_grant)}
        
        Organization: {json.dumps(serializable_org)}
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        result = json.loads(content if content else "{}")
        
        # Ensure score is within 0-100 range
        if 'score' in result:
            result['score'] = max(0, min(100, result['score']))
        
        return result
    
    except Exception as e:
        logging.error(f"Error analyzing grant match: {str(e)}")
        return {
            "score": 0,
            "explanation": "An error occurred while analyzing the match",
            "error": str(e)
        }

def generate_grant_narrative(grant, organization, case_for_support=""):
    """
    Generate a grant narrative based on the grant requirements and organization profile
    
    Args:
        grant (dict): The grant information
        organization (dict): The organization profile
        case_for_support (str): Additional case for support text
        
    Returns:
        str: Generated narrative text
    """
    try:
        # Check if OpenAI is available
        if not openai:
            return "OpenAI API key not configured. Please provide an API key to use the narrative generation feature."
        
        # Create serializable copies with date handling
        serializable_grant = {}
        for key, value in grant.items():
            # Convert date objects to strings
            if hasattr(value, 'isoformat'):
                serializable_grant[key] = value.isoformat()
            else:
                serializable_grant[key] = value
                
        serializable_org = {}
        for key, value in organization.items():
            # Convert date objects to strings
            if hasattr(value, 'isoformat'):
                serializable_org[key] = value.isoformat()
            else:
                serializable_org[key] = value
                
        # Format due date for display if available
        due_date_display = ""
        if grant.get('due_date'):
            if hasattr(grant['due_date'], 'strftime'):
                due_date_display = grant['due_date'].strftime('%B %d, %Y')
            else:
                due_date_display = str(grant['due_date'])
            
        system_prompt = """
        You are an expert grant writer for nonprofits. Your task is to create a compelling 
        grant narrative that connects the nonprofit's strengths and mission with the 
        funder's priorities. Use specific language that aligns with the funder's interests 
        while authentically representing the organization.
        
        Follow these guidelines:
        1. Begin with a strong, engaging opening that establishes the need
        2. Clearly state the organization's qualifications to address the need
        3. Describe the proposed project/program with specific details
        4. Include measurable outcomes and evaluation methods
        5. Explain how the project aligns with the funder's priorities
        6. Use concise, active language without jargon
        7. Include specific data points and examples from the organization's history
        8. Address any specific questions or sections required by the grant
        
        The tone should be professional but passionate, demonstrating both expertise 
        and commitment to the mission.
        """
        
        user_content = f"""
        Organization Information:
        Name: {serializable_org.get('name')}
        Mission: {serializable_org.get('mission')}
        Focus Areas: {', '.join(serializable_org.get('focus_areas', []))}
        Past Programs: {json.dumps(serializable_org.get('past_programs', []))}
        Team: {json.dumps(serializable_org.get('team', []))}
        
        Grant Information:
        Title: {serializable_grant.get('title')}
        Funder: {serializable_grant.get('funder')}
        Due Date: {due_date_display}
        Focus Areas: {', '.join(serializable_grant.get('focus_areas', []))}
        Requirements: {serializable_grant.get('eligibility')}
        Description: {serializable_grant.get('description')}
        
        Case for Support:
        {case_for_support}
        
        Please write a compelling grant narrative (750-1000 words) that connects the organization's 
        strengths with the funder's priorities. Include a strong opening, clear description of the 
        proposed work, explanation of the organization's qualifications, and expected outcomes.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logging.error(f"Error generating grant narrative: {str(e)}")
        return "Error generating narrative: " + str(e)
