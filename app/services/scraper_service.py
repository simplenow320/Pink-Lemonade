"""
Scraper Service Module

This module provides functionality for scraping grants from various sources
and integrating with internet-wide grant discovery.
"""

import os
import logging
import requests
import time
import random
import json
from datetime import datetime, timedelta
import uuid
from bs4 import BeautifulSoup
import trafilatura
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models.scraper import ScraperSource, ScraperHistory
from app.models.grant import Grant
from app.models.organization import Organization
from app.services.ai_service import extract_grant_info, analyze_grant_match, extract_grant_info_from_url
from app.services.discovery_service import discover_grants

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_grants(url_list):
    """
    Scrape grants from a list of URLs using OpenAI
    
    Args:
        url_list (list): List of URLs to scrape
        
    Returns:
        list: List of extracted grants
    """
    grants = []
    
    try:
        for url in url_list:
            logger.info(f"Scraping URL: {url}")
            grant_data = extract_grant_info_from_url(url)
            
            if grant_data.get('title') and grant_data.get('funder'):
                grants.append(grant_data)
                logger.info(f"Extracted grant: {grant_data.get('title')}")
    
    except Exception as e:
        logger.error(f"Error scraping grants with OpenAI: {str(e)}")
    
    return grants


def scrape_source(source):
    """
    Scrape grants from a single source
    
    Args:
        source (ScraperSource): The source to scrape
        
    Returns:
        list: List of extracted grants
    """
    grants = []
    
    # If this is a mock/demo source, generate sample grants
    if source.is_demo:
        logger.info(f"Generating sample grants for demo source: {source.name}")
        
        # Generate 1-3 sample grants
        num_grants = random.randint(1, 3)
        
        for _ in range(num_grants):
            # Generate random data
            focus_areas = ["Education", "Healthcare", "Environment", "Arts", "Community Development", 
                         "Youth Services", "Economic Development", "Social Justice"]
            random.shuffle(focus_areas)
            focus_areas = focus_areas[:random.randint(1, 3)]
            
            amount = random.choice(["$5,000", "$10,000", "$25,000", "$50,000", 
                                  "$100,000", "$250,000", "$10,000 - $50,000"])
            
            # Generate a due date between 30 and 120 days from now
            days_ahead = random.randint(30, 120)
            due_date = datetime.now() + timedelta(days=days_ahead)
            
            # Construct a fictitious title and funder
            title = f"{random.choice(['Community', 'Innovation', 'Development', 'Leadership', 'Transformation'])} " \
                  f"{random.choice(['Grant', 'Fund', 'Initiative', 'Program'])} for " \
                  f"{focus_areas[0]}"
            
            funder = source.name if source.name else "Sample Foundation"
            
            grant_data = {
                'title': title,
                'funder': funder,
                'description': f"This grant supports organizations working on {', '.join(focus_areas)}. Applications must demonstrate clear outcomes and community impact.",
                'amount': amount,
                'due_date': due_date.date(),
                'eligibility': "501(c)(3) organizations with at least 2 years of operating history",
                'website': f"https://example.org/grants/{uuid.uuid4().hex[:8]}",
                'focus_areas': focus_areas,
                'contact_info': "grants@example.org"
            }
            
            grants.append(grant_data)
            logger.info(f"Generated sample grant: {grant_data.get('title')}")
        
        return grants
    
    # Real scraping logic
    try:
        # Set up headers for the request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Make the request with timeout
        response = requests.get(source.url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch {source.name}: Status code {response.status_code}")
            return grants
        
        # Use direct URL extraction as the most reliable method
        try:
            grant_data = extract_grant_info_from_url(source.url)
            
            # Validate the grant data and add it to the list
            if grant_data.get('title') and grant_data.get('funder'):
                # Make sure the source name is set as funder if not detected
                if grant_data.get('funder') == "Unknown" and source.name:
                    grant_data['funder'] = source.name
                
                grants.append(grant_data)
                logger.info(f"Extracted grant from URL: {grant_data.get('title')}")
                
            else:
                logger.warning(f"Failed to extract grant info from {source.url}")
        except Exception as e:
            logger.warning(f"Error extracting grant from URL {source.url}: {str(e)}")
            # Continue with other extraction methods
        
        # If we didn't get a result from direct URL extraction, try other methods
        if not grants:
            try:
                # Use trafilatura to get clean content
                downloaded = trafilatura.fetch_url(source.url)
                if downloaded:
                    # Extract main content 
                    text = trafilatura.extract(downloaded)
                    
                    if text and len(text) > 500:  # Ensure we have meaningful content
                        # Use AI to extract grants from the text
                        if "grant" in text.lower() or "fund" in text.lower():
                            logger.info(f"Found potential grant content on {source.name}, extracting information...")
                            
                            grant_data = extract_grant_info(text)
                            
                            # Ensure the funder name is set correctly if not detected
                            if (not grant_data.get('funder') or grant_data.get('funder') == "Unknown") and source.name:
                                grant_data['funder'] = source.name
                                
                            # Ensure website is set
                            if not grant_data.get('website'):
                                grant_data['website'] = source.url
                            
                            # Validate that we have at least title and funder
                            if grant_data.get('title') and grant_data.get('funder'):
                                grants.append(grant_data)
                                logger.info(f"Extracted grant using AI: {grant_data.get('title')}")
            except Exception as e:
                logger.warning(f"AI extraction failed for {source.name}: {str(e)}")
        
        # If still no grants found, try HTML parsing approaches
        if not grants:
            try:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for grant sections based on common patterns
                
                # 1. Find sections with 'grant' in heading
                grant_headings = []
                for tag in ['h1', 'h2', 'h3', 'h4']:
                    headings = soup.find_all(tag)
                    for heading in headings:
                        if 'grant' in heading.text.lower() or 'fund' in heading.text.lower():
                            grant_headings.append(heading)
                
                # 2. For each potential grant heading, extract information
                for heading in grant_headings:
                    # Get the text and clean it
                    title = heading.text.strip()
                    
                    # Look for description in the next paragraphs
                    desc = ""
                    next_elem = heading.find_next('p')
                    if next_elem:
                        desc = next_elem.text.strip()
                    
                    # Look for a link that might point to more information
                    link = None
                    next_elem = heading.find_next('a')
                    if not next_elem:
                        next_elem = heading.find_next('p')
                        if next_elem:
                            link = next_elem.find('a')
                    
                    website = None
                    if link and 'href' in link.attrs:
                        href = link['href']
                        if href.startswith('/'):
                            from urllib.parse import urlparse
                            parsed_url = urlparse(source.url)
                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                            href = base_url + href
                        website = href
                    
                    # Create grant data
                    grant_data = {
                        'title': title,
                        'funder': source.name,  # Use source name as default funder
                        'description': desc,
                        'website': website or source.url
                    }
                    
                    grants.append(grant_data)
                    logger.info(f"Extracted grant from heading: {title}")
                
                # If we still don't have grants and the page is not too large, try AI extraction on sections
                if not grants and len(response.content) < 200000:  # Limit to manageable HTML size
                    main_content = soup.find('main') or soup.find(id='content') or soup.find(class_='content')
                    
                    if main_content:
                        # Extract text from main content
                        text = main_content.get_text(separator=' ', strip=True)
                        
                        if text and len(text) < 15000:  # Limit to manageable text size
                            # Use AI to extract grants from the text
                            try:
                                grant_data = extract_grant_info(text)
                                
                                # Ensure the funder name is set correctly if not detected
                                if (not grant_data.get('funder') or grant_data.get('funder') == "Unknown") and source.name:
                                    grant_data['funder'] = source.name
                                    
                                # Ensure website is set
                                if not grant_data.get('website'):
                                    grant_data['website'] = source.url
                                
                                # Validate that we have at least title and funder
                                if grant_data.get('title') and grant_data.get('funder'):
                                    grants.append(grant_data)
                                    logger.info(f"Extracted grant using AI on main content: {grant_data.get('title')}")
                            except Exception as e:
                                logger.warning(f"AI extraction on main content failed: {str(e)}")
            
            except Exception as e:
                logger.warning(f"HTML parsing failed for {source.name}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error scraping source {source.name}: {str(e)}")
    
    return grants


def run_scraping_job(include_web_search=True):
    """
    Run the scraping job for all active sources and optionally perform internet-wide grant searching
    
    Args:
        include_web_search (bool): Whether to include internet-wide grant searching
    
    Returns:
        dict: Results of the scraping job
    """
    start_time = datetime.now()
    result = {
        "start_time": start_time,
        "end_time": None,
        "sources_scraped": 0,
        "web_search_performed": include_web_search,
        "grants_found": 0,
        "grants_added": 0,
        "status": "completed",
        "error_message": "",
        "new_grants": [],
        "search_report": {
            "sites_searched_estimate": 0,
            "total_queries_attempted": 0,
            "successful_queries": 0,
            "search_keywords_used": [],
            "sites_by_category": {
                "government": 0,
                "foundation": 0,
                "nonprofit": 0,
                "corporate": 0,
                "other": 0
            }
        }
    }
    
    try:
        # Get organization profile for matching
        org = Organization.query.first()
        if not org:
            logger.warning("No organization profile found for matching")
            result["status"] = "completed"
            result["error_message"] = "No organization profile found for matching"
            result["end_time"] = datetime.now()
            return result
        
        org_keywords = org.keywords
        org_data = org.to_dict()
        
        # Get all active scraper sources
        sources = ScraperSource.query.filter_by(is_active=True).all()
        
        if not sources and not include_web_search:
            logger.warning("No active scraper sources found and web search is disabled")
            result["status"] = "completed"
            result["error_message"] = "No active scraper sources found and web search is disabled"
            result["end_time"] = datetime.now()
            return result
        
        # First, perform internet-wide grant discovery if enabled
        discovered_grants = []
        if include_web_search:
            logger.info("Starting internet-wide grant discovery")
            try:
                # Perform internet-wide grant discovery
                internet_grants = discover_grants(org_data, limit=10)
                
                result["grants_found"] += len(internet_grants)
                
                # Extract search report if available (from the first grant)
                if internet_grants and 'search_report' in internet_grants[0]:
                    search_report = internet_grants[0].get('search_report', {})
                    
                    # Update the main result's search report
                    result["search_report"]["sites_searched_estimate"] = search_report.get("sites_searched_estimate", 0)
                    result["search_report"]["total_queries_attempted"] = search_report.get("total_queries_attempted", 0)
                    result["search_report"]["successful_queries"] = search_report.get("successful_queries", 0)
                    result["search_report"]["search_keywords_used"] = search_report.get("search_keywords_used", [])
                    
                    # Log search report details
                    logger.info(f"Search report: {result['search_report']['successful_queries']}/{result['search_report']['total_queries_attempted']} " +
                               f"successful queries, {result['search_report']['sites_searched_estimate']} sites searched")
                
                if internet_grants:
                    logger.info(f"Discovered {len(internet_grants)} grants from internet-wide search")
                    # Remove the search_report from each grant to avoid duplication
                    for grant in internet_grants:
                        if 'search_report' in grant:
                            del grant['search_report']
                    discovered_grants.extend(internet_grants)
                else:
                    logger.info("No grants discovered from internet-wide search")
                    
            except Exception as e:
                logger.error(f"Error during internet-wide grant discovery: {str(e)}")
                # Continue with regular scraping even if internet search fails
        
        # Next, process foundation sources
        for source in sources:
            logger.info(f"Scraping source: {source.name}")
            
            try:
                # Scrape the source
                source_grants = scrape_source(source)
                
                # Update the last_scraped timestamp for the source
                source.last_scraped = datetime.now()
                db.session.commit()
                
                result["sources_scraped"] += 1
                result["grants_found"] += len(source_grants)
                
                # Add source grants to the discovered grants for unified processing
                discovered_grants.extend(source_grants)
            
            except Exception as e:
                logger.error(f"Error scraping source {source.name}: {str(e)}")
        
        # Process all discovered grants (both from web search and foundation sources)
        logger.info(f"Processing {len(discovered_grants)} total grants discovered")
        for grant_data in discovered_grants:
            # Skip if we don't have key information
            if not grant_data.get('title') or not grant_data.get('funder'):
                logger.warning("Skipping grant with missing title or funder")
                continue
                
            # Check if grant already exists (by title and funder)
            existing_grant = Grant.query.filter_by(
                title=grant_data.get('title'),
                funder=grant_data.get('funder')
            ).first()
            
            if existing_grant:
                logger.info(f"Grant already exists: {grant_data.get('title')}")
                continue
            
            # Use OpenAI API to get a real match score based on organization profile
            try:
                # Add organization data to grant for match analysis
                match_result = analyze_grant_match(grant_data, org_data)
                grant_data['match_score'] = match_result.get('score', 50)
                grant_data['match_explanation'] = match_result.get('explanation', 
                                                  f"The grant aligns with {grant_data.get('match_score', 50)}% of your organization's focus areas and requirements.")
            except Exception as e:
                logger.warning(f"Error getting match score: {str(e)}")
                # Fallback to estimating match based on keyword overlap
                org_keywords_set = set([k.lower() for k in org_keywords])
                grant_keywords = set([grant_data.get('title', '').lower(), 
                                    grant_data.get('funder', '').lower()])
                if 'focus_areas' in grant_data and isinstance(grant_data['focus_areas'], list):
                    grant_keywords.update([area.lower() for area in grant_data['focus_areas']])
                
                overlap = org_keywords_set.intersection(grant_keywords)
                match_score = min(95, max(30, len(overlap) * 10))
                grant_data['match_score'] = match_score
                grant_data['match_explanation'] = f"Based on keyword matching, this grant has {len(overlap)} keyword overlaps with your organization's profile."
            
            # Only add grants with match score above threshold (30%)
            if grant_data.get('match_score', 0) >= 30:
                try:
                    # Determine source_id - for internet-discovered grants we don't have a source
                    source_id = None
                    
                    # For grants from foundation sources, get the source_id
                    for source in sources:
                        if source.name == grant_data.get('funder') or (
                            grant_data.get('website') and source.url in grant_data.get('website')):
                            source_id = source.id
                            break
                    
                    # For internet-discovered grants, create a special source
                    if source_id is None and ('discovery_method' in grant_data and 
                                            grant_data['discovery_method'] in ['web-search', 'focused-search']):
                        # Create a special "Internet Search" source if it doesn't exist
                        web_source = ScraperSource.query.filter_by(name="Internet Search").first()
                        if not web_source:
                            web_source = ScraperSource(
                                name="Internet Search",
                                url="https://grantflow.app/web-discovery",
                                is_active=True,
                                last_scraped=datetime.now()
                            )
                            db.session.add(web_source)
                            db.session.commit()
                        source_id = web_source.id
                    
                    # Create new grant
                    new_grant = Grant(
                        title=grant_data.get('title'),
                        funder=grant_data.get('funder'),
                        description=grant_data.get('description', ''),
                        amount=grant_data.get('amount'),
                        due_date=grant_data.get('due_date'),
                        eligibility=grant_data.get('eligibility', ''),
                        website=grant_data.get('website', ''),
                        status="Not Started",
                        match_score=grant_data.get('match_score', 0),
                        match_explanation=grant_data.get('match_explanation', ''),
                        focus_areas=grant_data.get('focus_areas', []),
                        contact_info=grant_data.get('contact_info', ''),
                        is_scraped=True,
                        source_id=source_id
                    )
                    
                    db.session.add(new_grant)
                    db.session.commit()
                    
                    result["grants_added"] += 1
                    result["new_grants"].append({
                        "id": new_grant.id,
                        "title": new_grant.title,
                        "funder": new_grant.funder,
                        "match_score": new_grant.match_score
                    })
                    logger.info(f"Added new grant: {new_grant.title} from {new_grant.funder}")
                except Exception as e:
                    logger.error(f"Error saving grant {grant_data.get('title')}: {str(e)}")
                    continue
        
        # Update the scraper history
        try:
            # Create a new history object
            history = ScraperHistory()
            history.start_time = start_time
            history.end_time = datetime.now()
            history.sources_scraped = result["sources_scraped"]
            history.grants_found = result["grants_found"] 
            history.grants_added = result["grants_added"]
            history.status = result["status"]
            history.error_message = result["error_message"]
            
            # Add search report data if available
            if "search_report" in result:
                history.sites_searched_estimate = result["search_report"]["sites_searched_estimate"]
                history.total_queries_attempted = result["search_report"]["total_queries_attempted"] 
                history.successful_queries = result["search_report"]["successful_queries"]
                history.search_keywords_used = result["search_report"]["search_keywords_used"]
            db.session.add(history)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating scraper history: {str(e)}")
        
        # Set end time
        result["end_time"] = datetime.now()
        return result
    
    except Exception as e:
        logger.error(f"Error in scraping job: {str(e)}")
        result["status"] = "error"
        result["error_message"] = str(e)
        result["end_time"] = datetime.now()
        return result