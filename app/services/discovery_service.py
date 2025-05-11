"""
Grant Discovery Service

This module provides functionality to discover new grant opportunities from across
the internet based on the organization's profile and focus areas.
"""

import logging
import json
import os
from datetime import datetime, timedelta
import time
import random
from typing import List, Dict, Any, Optional

from app.services.ai_service import extract_grant_info_from_url

# Initialize OpenAI client if API key is available
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = None

# Only initialize OpenAI if API key is provided
if OPENAI_API_KEY:
    from openai import OpenAI
    openai = OpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger(__name__)


def discover_grants(org_profile: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Discover grant opportunities from across the internet based on the organization's profile.
    
    Args:
        org_profile: The organization profile
        limit: Maximum number of grants to discover
        
    Returns:
        List of discovered grant opportunities
    """
    if not openai:
        logger.error("OpenAI API key not configured. Grant discovery requires the OpenAI API.")
        return []
    
    logger.info(f"Starting internet-wide grant discovery for {org_profile.get('name', 'Unknown Organization')}")
    
    discovered_grants = []
    
    # Extract key information from the organization profile
    org_name = org_profile.get('name', '')
    focus_areas = org_profile.get('focus_areas', [])
    funding_priorities = org_profile.get('funding_priorities', [])
    geographic_focus = org_profile.get('geographic_focus', [])
    
    # If we don't have enough information about the organization, we can't discover grants
    if not focus_areas:
        logger.error("Cannot discover grants without organization focus areas")
        return []
    
    # Create search queries based on organization profile
    search_queries = []
    
    # Add focus area-based queries
    for area in focus_areas:
        search_queries.append(f"grant funding for {area} nonprofit organizations")
    
    # Add funding priority-based queries
    for priority in funding_priorities:
        search_queries.append(f"grants supporting {priority} programs")
    
    # Add geographic focus-based queries
    for location in geographic_focus:
        search_queries.append(f"nonprofit grants in {location}")
        # Also combine with focus areas for more targeted results
        for area in focus_areas[:2]:  # Limit to first 2 focus areas to keep queries manageable
            search_queries.append(f"{area} nonprofit grants in {location}")
    
    # Add general queries
    search_queries.append("new grant opportunities for nonprofits")
    search_queries.append("foundation grants for community programs")
    
    # Shuffle to get a diverse set of results
    random.shuffle(search_queries)
    
    # Limit the number of queries to prevent too many API calls
    search_queries = search_queries[:5]
    
    logger.info(f"Generated {len(search_queries)} search queries for grant discovery")
    
    # Use OpenAI to find grant opportunities based on the search queries
    try:
        for query in search_queries:
            if len(discovered_grants) >= limit:
                break
                
            logger.info(f"Searching for grants with query: {query}")
            
            # Use OpenAI to find grant opportunities
            response = openai.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a grant research assistant. Your task is to identify relevant grant opportunities
                        for nonprofit organizations based on the search query provided. 
                        
                        For each grant opportunity, provide the following information:
                        1. name: The full name of the grant program
                        2. funder: The foundation or organization offering the grant
                        3. website: The direct URL to the grant information (very important)
                        4. description: A brief description of what the grant funds
                        5. eligibility: Who can apply for this grant
                        6. focus_areas: A list of focus areas this grant supports
                        
                        Return EXACTLY 3 grants that are the most promising matches for the query.
                        Format your response as a JSON array of objects, with each object containing the above fields.
                        Important: Only include real grant opportunities with actual URLs. Do not make up or fabricate any information."""
                    },
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            try:
                results = json.loads(content if content else "{}")
                
                # The results should be a list of grants
                grants = results.get("grants", [])
                if not grants and isinstance(results, list):
                    grants = results
                
                if not grants:
                    logger.warning(f"No grants found for query: {query}")
                    continue
                
                logger.info(f"Found {len(grants)} potential grants for query: {query}")
                
                # Process each grant
                for grant in grants:
                    # Skip if we don't have a website
                    if not grant.get('website'):
                        continue
                        
                    # Check if we already have this grant in our list
                    website = grant.get('website')
                    if any(g.get('website') == website for g in discovered_grants):
                        continue
                    
                    try:
                        # Try to extract more detailed information from the website
                        logger.info(f"Extracting detailed information from {website}")
                        
                        # Add a short delay to avoid hitting rate limits
                        time.sleep(1)
                        
                        detailed_grant = extract_grant_info_from_url(website)
                        
                        # Merge the information
                        if detailed_grant.get('title') and detailed_grant.get('title') != "Unknown Grant":
                            # Use the detailed information
                            # But keep some fields from the original if they're missing in the detailed info
                            if not detailed_grant.get('funder') and grant.get('funder'):
                                detailed_grant['funder'] = grant.get('funder')
                                
                            if not detailed_grant.get('focus_areas') and grant.get('focus_areas'):
                                detailed_grant['focus_areas'] = grant.get('focus_areas')
                                
                            if not detailed_grant.get('eligibility') and grant.get('eligibility'):
                                detailed_grant['eligibility'] = grant.get('eligibility')
                                
                            discovered_grants.append(detailed_grant)
                        else:
                            # Use the original information with minimal processing
                            final_grant = {
                                'title': grant.get('name', 'Unknown Grant'),
                                'funder': grant.get('funder', 'Unknown'),
                                'description': grant.get('description', ''),
                                'website': website,
                                'focus_areas': grant.get('focus_areas', []),
                                'eligibility': grant.get('eligibility', ''),
                                'discovery_method': 'web-search',
                                'discovery_date': datetime.now().strftime('%Y-%m-%d')
                            }
                            
                            # Set a default due date if none is provided
                            if not final_grant.get('due_date'):
                                # Set due date to 3 months from now as a placeholder
                                due_date = datetime.now() + timedelta(days=90)
                                final_grant['due_date'] = due_date.strftime('%Y-%m-%d')
                                
                            discovered_grants.append(final_grant)
                        
                        if len(discovered_grants) >= limit:
                            break
                            
                    except Exception as e:
                        logger.error(f"Error processing grant from {website}: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error parsing grant results for query '{query}': {str(e)}")
                continue
                
            # Add a small delay between queries
            time.sleep(2)
                
    except Exception as e:
        logger.error(f"Error during grant discovery: {str(e)}")
        
    logger.info(f"Discovered {len(discovered_grants)} new grant opportunities")
    return discovered_grants


def discover_grants_for_focus_area(focus_area: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Discover grant opportunities for a specific focus area.
    
    Args:
        focus_area: The focus area to discover grants for
        limit: Maximum number of grants to discover
        
    Returns:
        List of discovered grant opportunities
    """
    if not openai:
        logger.error("OpenAI API key not configured. Grant discovery requires the OpenAI API.")
        return []
    
    logger.info(f"Starting focused grant discovery for area: {focus_area}")
    
    discovered_grants = []
    
    # Create search query based on focus area
    query = f"grants funding {focus_area} nonprofit programs"
    
    try:
        # Use OpenAI to find grant opportunities
        response = openai.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {
                    "role": "system", 
                    "content": """You are a grant research assistant. Your task is to identify relevant grant opportunities
                    for nonprofit organizations based on the search query provided. 
                    
                    For each grant opportunity, provide the following information:
                    1. name: The full name of the grant program
                    2. funder: The foundation or organization offering the grant
                    3. website: The direct URL to the grant information (very important)
                    4. description: A brief description of what the grant funds
                    5. eligibility: Who can apply for this grant
                    6. focus_areas: A list of focus areas this grant supports
                    
                    Return EXACTLY 3 grants that are the most promising matches for the query.
                    Format your response as a JSON array of objects, with each object containing the above fields.
                    Important: Only include real grant opportunities with actual URLs. Do not make up or fabricate any information."""
                },
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        content = response.choices[0].message.content
        try:
            results = json.loads(content if content else "{}")
            
            # The results should be a list of grants
            grants = results.get("grants", [])
            if not grants and isinstance(results, list):
                grants = results
            
            if not grants:
                logger.warning(f"No grants found for focus area: {focus_area}")
                return []
            
            logger.info(f"Found {len(grants)} potential grants for focus area: {focus_area}")
            
            # Process each grant
            for grant in grants:
                # Skip if we don't have a website
                if not grant.get('website'):
                    continue
                    
                try:
                    # Try to extract more detailed information from the website
                    logger.info(f"Extracting detailed information from {grant.get('website')}")
                    
                    # Add a short delay to avoid hitting rate limits
                    time.sleep(1)
                    
                    detailed_grant = extract_grant_info_from_url(grant.get('website'))
                    
                    # Merge the information
                    if detailed_grant.get('title') and detailed_grant.get('title') != "Unknown Grant":
                        # Use the detailed information
                        # But keep some fields from the original if they're missing in the detailed info
                        if not detailed_grant.get('funder') and grant.get('funder'):
                            detailed_grant['funder'] = grant.get('funder')
                            
                        if not detailed_grant.get('focus_areas') and grant.get('focus_areas'):
                            detailed_grant['focus_areas'] = grant.get('focus_areas')
                            
                        if not detailed_grant.get('eligibility') and grant.get('eligibility'):
                            detailed_grant['eligibility'] = grant.get('eligibility')
                            
                        discovered_grants.append(detailed_grant)
                    else:
                        # Use the original information with minimal processing
                        final_grant = {
                            'title': grant.get('name', 'Unknown Grant'),
                            'funder': grant.get('funder', 'Unknown'),
                            'description': grant.get('description', ''),
                            'website': grant.get('website'),
                            'focus_areas': grant.get('focus_areas', []),
                            'eligibility': grant.get('eligibility', ''),
                            'discovery_method': 'focused-search',
                            'discovery_date': datetime.now().strftime('%Y-%m-%d')
                        }
                        
                        # Set a default due date if none is provided
                        if not final_grant.get('due_date'):
                            # Set due date to 3 months from now as a placeholder
                            due_date = datetime.now() + timedelta(days=90)
                            final_grant['due_date'] = due_date.strftime('%Y-%m-%d')
                            
                        discovered_grants.append(final_grant)
                    
                    if len(discovered_grants) >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing grant from {grant.get('website')}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing grant results for focus area '{focus_area}': {str(e)}")
            return []
            
    except Exception as e:
        logger.error(f"Error during focused grant discovery: {str(e)}")
        
    logger.info(f"Discovered {len(discovered_grants)} new grant opportunities for focus area: {focus_area}")
    return discovered_grants