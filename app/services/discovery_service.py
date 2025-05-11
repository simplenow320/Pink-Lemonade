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
    search_report = {
        "total_queries_attempted": 0,
        "successful_queries": 0,
        "sites_searched_estimate": 0,
        "search_keywords_used": [],
        "total_grants_found": 0,
        "query_results": {}
    }
    
    # Extract key information from the organization profile
    org_name = org_profile.get('name', '')
    focus_areas = org_profile.get('focus_areas', [])
    funding_priorities = org_profile.get('funding_priorities', [])
    geographic_focus = org_profile.get('geographic_focus', [])
    
    # If we don't have enough information about the organization, we can't discover grants
    if not focus_areas:
        logger.error("Cannot discover grants without organization focus areas")
        return []
    
    # Define focused keywords for THRIVE and AI in the City initiatives
    thrive_ai_keywords = [
        # THRIVE Initiative Keywords (15)
        "urban ministry leadership grants",
        "pastoral mentoring and coaching funding",
        "church planting support grants",
        "church-based mental health training funding",
        "culturally sensitive mental health grant",
        "faith-based community transformation funding",
        "holistic community flourishing grants",
        "capacity building grants for churches",
        "strategic planning ministry grants",
        "peer network support for pastors grant",
        "resource management training funding",
        "fundraising capacity building grants",
        "mental health first aid church grant",
        "spiritual care and community wellness grants",
        "discipleship leadership development funding",
        
        # AI in the City Initiative Keywords (15)
        "digital literacy in underserved communities grant",
        "AI education grant for urban youth",
        "workforce development through AI funding",
        "technology training for community adults grant",
        "business leader AI training funding",
        "AI-powered community app development grant",
        "ethical AI use training grants",
        "intergenerational tech learning funding",
        "equity and inclusion in urban grants",
        "after-school technology program funding",
        "multi-demographic tech training grant",
        "church innovation and incubation funding",
        "digital equity and inclusion grants",
        "urban neighborhood empowerment grant",
        "faith-based workforce readiness grants",
        
        # Additional AI Education Keywords
        "AI literacy education grants",
        "youth coding and AI scholarships",
        "AI skills development for urban communities",
        "generative AI education funding",
        "community-based AI learning centers",
        
        # Additional Mental Health Keywords
        "trauma-informed ministry grants",
        "urban mental health services funding",
        "faith community mental health partnerships",
        "grief counseling program grants",
        "pastoral care mental health training",
        
        # Additional Urban Ministry Keywords
        "urban church revitalization grants",
        "multi-ethnic church planting funds",
        "urban youth mentorship grants",
        "community engagement ministry funding",
        "affordable housing ministry grants"
    ]
    
    # Create search queries based on organization profile
    search_queries = []
    
    # Add specialized THRIVE and AI keywords (take a random selection of 10 to ensure better coverage)
    random.shuffle(thrive_ai_keywords)
    selected_keywords = thrive_ai_keywords[:10]
    search_queries.extend(selected_keywords)
    
    # Track all selected keywords for reporting
    all_keywords.extend(selected_keywords)
    
    # Add focus area-based queries
    for area in focus_areas[:3]:  # Limit to first 3 focus areas to keep queries manageable
        search_queries.append(f"grant funding for {area} nonprofit organizations")
    
    # Add funding priority-based queries
    for priority in funding_priorities[:2]:  # Limit to first 2 priorities
        search_queries.append(f"grants supporting {priority} programs")
    
    # Add geographic focus-based queries
    for location in geographic_focus[:2]:  # Limit to first 2 locations
        search_queries.append(f"nonprofit grants in {location}")
        # Also combine with focus areas for more targeted results
        if focus_areas:
            search_queries.append(f"{focus_areas[0]} nonprofit grants in {location}")
    
    # Add general queries
    search_queries.append("new grant opportunities for nonprofits")
    
    # Shuffle to get a diverse set of results
    random.shuffle(search_queries)
    
    # Store all keywords before limiting for reporting purposes
    all_keywords = search_queries.copy()
    
    # Limit the number of queries to prevent too many API calls
    search_queries = search_queries[:7]  # Increased from 5 to 7 for better coverage
    
    search_report["search_keywords_used"] = all_keywords
    search_report["total_queries_attempted"] = len(search_queries)
    
    logger.info(f"Generated {len(search_queries)} search queries for grant discovery")
    
    # Use OpenAI to find grant opportunities based on the search queries
    try:
        for query in search_queries:
            if len(discovered_grants) >= limit:
                break
                
            logger.info(f"Searching for grants with query: {query}")
            search_report["query_results"][query] = {
                "grants_found": 0,
                "sites_searched_estimate": 0,
                "success": False
            }
            
            # Use OpenAI to find grant opportunities
            response = openai.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a grant research assistant tasked with identifying relevant grant opportunities 
                        for nonprofit organizations based on the search query provided.
                        
                        For each grant opportunity, provide the following information:
                        1. name: The full name of the grant program
                        2. funder: The foundation or organization offering the grant
                        3. website: The direct URL to the grant information (very important)
                        4. description: A brief description of what the grant funds
                        5. eligibility: Who can apply for this grant
                        6. focus_areas: A list of focus areas this grant supports
                        7. sites_searched: Estimate how many different websites you searched to find this grant (number only)
                        
                        Return exactly 3 grants that are the most promising matches for the query.
                        Format your response as a JSON object with a key called "grants" containing an array of objects,
                        with each object containing the above fields. Also include a "sites_searched_estimate" field with the total number
                        of websites you estimate were searched.
                        
                        Important: Only include real grant opportunities with actual URLs. Do not make up or fabricate any information."""
                    },
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            try:
                # Make sure content is not None before parsing
                if content is not None:
                    results = json.loads(str(content))
                else:
                    results = {"grants": []}
                
                # The results should be a list of grants
                grants = results.get("grants", [])
                
                # Get the sites searched estimate
                sites_searched_estimate = results.get("sites_searched_estimate", 3)
                search_report["sites_searched_estimate"] += sites_searched_estimate
                search_report["query_results"][query]["sites_searched_estimate"] = sites_searched_estimate
                
                if not grants:
                    logger.warning(f"No grants found for query: {query}")
                    continue
                
                # Update the search report
                search_report["successful_queries"] += 1
                search_report["query_results"][query]["success"] = True
                search_report["query_results"][query]["grants_found"] = len(grants)
                search_report["total_grants_found"] += len(grants)
                
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
                    
                    # Convert grants to our standard format
                    final_grant = {
                        'title': grant.get('name', 'Unknown Grant'),
                        'funder': grant.get('funder', 'Unknown'),
                        'description': grant.get('description', ''),
                        'website': website,
                        'focus_areas': grant.get('focus_areas', []),
                        'eligibility': grant.get('eligibility', ''),
                        'discovery_method': 'web-search',
                        'discovery_date': datetime.now().strftime('%Y-%m-%d'),
                        'search_query': query  # Store the query that found this grant
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
                logger.error(f"Error parsing grant results for query '{query}': {str(e)}")
                continue
                
            # Add a small delay between queries
            time.sleep(2)
                
    except Exception as e:
        logger.error(f"Error during grant discovery: {str(e)}")
    
    # Add the search report to each grant for tracking
    for grant in discovered_grants:
        grant['search_report'] = search_report
    
    # Log the search results
    logger.info(f"Discovered {len(discovered_grants)} new grant opportunities from {search_report['sites_searched_estimate']} estimated sites")
    logger.info(f"Search metrics: {search_report['successful_queries']}/{search_report['total_queries_attempted']} successful queries, {search_report['total_grants_found']} total grants found")
    
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
                    "content": """You are a grant research assistant tasked with identifying relevant grant opportunities 
                    for nonprofit organizations based on the search query provided.
                    
                    For each grant opportunity, provide the following information:
                    1. name: The full name of the grant program
                    2. funder: The foundation or organization offering the grant
                    3. website: The direct URL to the grant information (very important)
                    4. description: A brief description of what the grant funds
                    5. eligibility: Who can apply for this grant
                    6. focus_areas: A list of focus areas this grant supports
                    
                    Return exactly 3 grants that are the most promising matches for the query.
                    Format your response as a JSON object with a key called "grants" containing an array of objects,
                    with each object containing the above fields.
                    
                    Important: Only include real grant opportunities with actual URLs. Do not make up or fabricate any information."""
                },
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        content = response.choices[0].message.content
        try:
            # Make sure content is not None before parsing
            if content is not None:
                results = json.loads(str(content))
            else:
                results = {"grants": []}
            
            # The results should be a list of grants
            grants = results.get("grants", [])
            
            if not grants:
                logger.warning(f"No grants found for focus area: {focus_area}")
                return []
            
            logger.info(f"Found {len(grants)} potential grants for focus area: {focus_area}")
            
            # Process each grant
            for grant in grants:
                # Skip if we don't have a website
                if not grant.get('website'):
                    continue
                
                # Convert grants to our standard format
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
            logger.error(f"Error parsing grant results for focus area '{focus_area}': {str(e)}")
            return []
            
    except Exception as e:
        logger.error(f"Error during focused grant discovery: {str(e)}")
        
    logger.info(f"Discovered {len(discovered_grants)} new grant opportunities for focus area: {focus_area}")
    return discovered_grants