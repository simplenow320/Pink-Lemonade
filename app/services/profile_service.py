"""
Profile Service Module for GrantFlow

This module provides services for building and managing organization profiles.
"""

import json
import requests
import logging
from openai import OpenAI
import os
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

def build_profile_from_input(raw_input: str) -> Dict[str, Any]:
    """
    Build a structured organization profile from raw input text.
    
    Args:
        raw_input (str): Raw input text, either a URL or organization description.
        
    Returns:
        Dict[str, Any]: Structured organization profile data.
    """
    # If raw_input starts with "http", fetch page content from URL
    content = raw_input
    if raw_input.startswith('http'):
        try:
            response = requests.get(raw_input, timeout=10)
            response.raise_for_status()  # Raise exception for non-200 status codes
            content = response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching URL content: {str(e)}")
            raise ValueError(f"Failed to fetch content from URL: {str(e)}")
    
    # Set up OpenAI client
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    
    client = OpenAI(api_key=api_key)
    
    # Create the system prompt for profile extraction
    system_prompt = """
    You are an AI profile builder. Input raw_input, which is either user-pasted profile or case support text, or a website URL. Extract and structure into this JSON:
    {
      name: string,
      mission: string,
      vision: string,
      focus_areas: [string],
      funding_priorities: [string],
      keywords: [string],
      summary: string
    }
    Return valid JSON.
    """
    
    try:
        # Call OpenAI ChatCompletion
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            response_format={"type": "json_object"}
        )
        
        # Extract and parse the JSON from the response
        json_response = response.choices[0].message.content
        profile_data = json.loads(json_response)
        
        return profile_data
    
    except Exception as e:
        logger.error(f"Error processing profile with OpenAI: {str(e)}")
        raise ValueError(f"Failed to build profile: {str(e)}")