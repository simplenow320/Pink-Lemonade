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
from concurrent.futures import ThreadPoolExecutor, as_completed

from app import db
from app.models.scraper import ScraperSource, ScraperHistory
from app.models.grant import Grant
from app.models.organization import Organization
# AI service methods imported when needed
from app.services.discovery_service import discover_grants
from app.utils.http_utils import fetch_url, extract_main_content, with_retry

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
            # Extract grant info from URL using AI if available
            from app.services.ai_service import ai_service
            
            # Fetch the content from URL first
            content = fetch_url(url)
            if content:
                grant_data = ai_service.extract_grant_from_text(content, url)
            else:
                grant_data = None
            
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
    
    # Never generate fake/demo data - only real grants allowed
    if hasattr(source, 'is_demo') and source.is_demo:
        logger.warning(f"Demo source requested: {source.name} - returning empty (no fake data allowed)")
        return []  # Never return fake data
    
    # Real scraping logic
    try:
        try:
            # Use our fetch_url utility with automatic retries and rate limiting
            response = fetch_url(source.url, timeout=20)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch {source.name}: Status code {response.status_code}")
                return grants
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error when scraping {source.name}: {str(e)}")
            return grants
        except Exception as e:
            logger.error(f"Unexpected error when scraping {source.name}: {str(e)}")
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
                # Use our extract_main_content utility with retry logic
                text = extract_main_content(source.url)
                
                if text and len(text) > 500:  # Ensure we have meaningful content
                    # Use AI to extract grants from the text
                    if "grant" in text.lower() or "fund" in text.lower() or "nonprofit" in text.lower():
                        logger.info(f"Found potential grant content on {source.name}, extracting information...")
                        
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
                                logger.info(f"Extracted grant using AI: {grant_data.get('title')}")
                        except Exception as ai_extract_error:
                            logger.warning(f"AI extraction error for {source.name}: {str(ai_extract_error)}")
            except Exception as e:
                logger.warning(f"Content extraction failed for {source.name}: {str(e)}")
        
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
        "status": "in_progress",  # Set initial status to in_progress
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
    
    # Create a history record immediately to track this job
    history = ScraperHistory()
    history.start_time = start_time
    history.status = "in_progress"
    history.sources_scraped = 0
    history.grants_found = 0
    history.grants_added = 0
    # Initialize search metrics columns
    history.sites_searched_estimate = 0
    history.total_queries_attempted = 0
    history.successful_queries = 0
    history.search_keywords_used = []
    db.session.add(history)
    db.session.commit()
    
    try:
        # Get organization profile for matching
        org = Organization.query.first()
        if not org:
            logger.warning("No organization profile found for matching")
            result["status"] = "completed_with_errors"
            result["error_message"] = "No organization profile found for matching"
            
            # Update history record
            history.end_time = datetime.now()
            history.status = "completed_with_errors"
            history.error_message = result["error_message"]
            db.session.commit()
            
            result["end_time"] = datetime.now()
            return result
        
        org_keywords = org.keywords
        org_data = org.to_dict()
        
        # Get all active scraper sources
        sources = ScraperSource.query.filter_by(is_active=True).all()
        
        if not sources and not include_web_search:
            logger.warning("No active scraper sources found and web search is disabled")
            result["status"] = "completed_with_errors"
            result["error_message"] = "No active scraper sources found and web search is disabled"
            
            # Update history record
            history.end_time = datetime.now()
            history.status = "completed_with_errors"
            history.error_message = result["error_message"]
            db.session.commit()
            
            result["end_time"] = datetime.now()
            return result
        
        # Step 1: First try federal grants API discovery - multi-category search
        discovered_grants = []
        try:
            logger.info("Starting comprehensive federal grants API discovery...")
            from app.services.rapidapi_service import grants_gov_service
            
            # Get grants from multiple categories as requested by user
            api_grants = []
            
            # Faith-based and community grants
            faith_grants = grants_gov_service.get_faith_based_grants(limit=5)
            if faith_grants:
                api_grants.extend(faith_grants)
                logger.info(f"Found {len(faith_grants)} faith-based grants")
            
            # Tech and AI grants
            tech_grants = grants_gov_service.get_tech_ai_grants(limit=5)
            if tech_grants:
                api_grants.extend(tech_grants)
                logger.info(f"Found {len(tech_grants)} tech/AI grants")
            
            # Arts grants
            arts_grants = grants_gov_service.get_arts_grants(limit=5)
            if arts_grants:
                api_grants.extend(arts_grants)
                logger.info(f"Found {len(arts_grants)} arts grants")
            
            # Mental health grants
            health_grants = grants_gov_service.get_mental_health_grants(limit=5)
            if health_grants:
                api_grants.extend(health_grants)
                logger.info(f"Found {len(health_grants)} mental health grants")
            
            # Community development grants
            community_grants = grants_gov_service.get_community_grants(limit=3)
            if community_grants:
                api_grants.extend(community_grants)
                logger.info(f"Found {len(community_grants)} community grants")
            
            if api_grants:
                logger.info(f"Total: Found {len(api_grants)} grants from Grants.gov API across all categories")
                discovered_grants.extend(api_grants)
                result["grants_found"] += len(api_grants)
                
                # Log grant titles for debugging
                for grant in api_grants[:5]:
                    logger.info(f"API Grant: {grant.get('title', 'No title')[:60]}...")
            else:
                logger.info("No grants found from Grants.gov API")
                
        except Exception as e:
            logger.error(f"Error during Grants.gov API discovery: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Step 2: Perform internet-wide grant discovery if enabled
        if include_web_search:
            logger.info("Starting internet-wide grant discovery")
            try:
                # Update history status to show we're running web search
                # We'll use the existing status field
                db.session.commit()
                
                # Perform internet-wide grant discovery
                internet_grants = discover_grants(org_data, limit=10)
                
                result["grants_found"] += len(internet_grants)
                
                # Extract search report if it's available and update metrics in real-time (from the first grant)
                if internet_grants and 'search_report' in internet_grants[0]:
                    search_report = internet_grants[0].get('search_report', {})
                    
                    # Update history with search metrics
                    # Refresh the history object first to avoid potential session issues
                    db.session.refresh(history)
                    
                    # Update with the search metrics
                    history.sites_searched_estimate = search_report.get("sites_searched_estimate", 0)
                    history.total_queries_attempted = search_report.get("total_queries_attempted", 0)
                    history.successful_queries = search_report.get("successful_queries", 0)
                    history.search_keywords_used = search_report.get("search_keywords_used", [])
                    
                    # Commit immediately so frontend can see updated metrics in real-time
                    db.session.commit()
                    
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
        
        # Next, process foundation sources in parallel
        logger.info(f"Scraping {len(sources)} foundation sources in parallel")
        
        # Define a worker function for parallel processing
        def scrape_source_worker(source):
            logger.info(f"Starting scrape for source: {source.name}")
            try:
                # Scrape the source
                source_grants = scrape_source(source)
                logger.info(f"Completed scrape for {source.name}, found {len(source_grants)} grants")
                
                # Return the result for this source
                return {
                    "source": source,
                    "grants": source_grants,
                    "success": True,
                    "error": None
                }
            except Exception as e:
                logger.error(f"Error scraping source {source.name}: {str(e)}")
                return {
                    "source": source,
                    "grants": [],
                    "success": False, 
                    "error": str(e)
                }
        
        # Use ThreadPoolExecutor for parallel processing
        # Use min(len(sources), 5) to avoid creating too many threads
        max_workers = min(len(sources), 5)
        source_results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scraping tasks
            future_to_source = {executor.submit(scrape_source_worker, source): source for source in sources}
            
            # Process results as they complete
            for future in as_completed(future_to_source):
                source_result = future.result()
                source_results.append(source_result)
                
                if source_result["success"]:
                    # Update the last_scraped timestamp for the source
                    source = source_result["source"]
                    source.last_scraped = datetime.now()
                    
                    # Add to discovered grants
                    discovered_grants.extend(source_result["grants"])
                    
                    # Update counters
                    result["sources_scraped"] += 1
                    result["grants_found"] += len(source_result["grants"])
        
        # Commit all timestamp updates at once
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error updating source timestamps: {str(e)}")
            db.session.rollback()
        
        # Process all discovered grants (both from API, web search and foundation sources)
        logger.info(f"Processing {len(discovered_grants)} total grants discovered")
        for i, grant_data in enumerate(discovered_grants):
            logger.info(f"Processing grant {i+1}/{len(discovered_grants)}: {grant_data.get('title', 'No title')[:50]}... from {grant_data.get('funder', 'No funder')}")
            # Skip if we don't have key information
            if not grant_data.get('title') or not grant_data.get('funder'):
                logger.warning(f"Skipping grant with missing title or funder: title='{grant_data.get('title')}', funder='{grant_data.get('funder')}'")
                continue
                
            # Check if grant already exists (by title and funder)
            existing_grant = Grant.query.filter_by(
                title=grant_data.get('title'),
                funder=grant_data.get('funder')
            ).first()
            
            if existing_grant:
                logger.info(f"Duplicate grant skipped: {grant_data.get('title')} from {grant_data.get('funder')}")
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
                            web_source = ScraperSource()
                            web_source.name = "Internet Search"
                            web_source.url = "https://grantflow.app/web-discovery"
                            web_source.is_active = True
                            web_source.last_scraped = datetime.now()
                            db.session.add(web_source)
                            db.session.commit()
                        source_id = web_source.id
                    
                    # Create new grant
                    new_grant = Grant()
                    new_grant.title = grant_data.get('title')
                    new_grant.funder = grant_data.get('funder')
                    new_grant.description = grant_data.get('description', '')
                    new_grant.amount = grant_data.get('amount')
                    new_grant.due_date = grant_data.get('due_date')
                    new_grant.eligibility = grant_data.get('eligibility', '')
                    new_grant.website = grant_data.get('website', '')
                    new_grant.status = "Not Started"
                    new_grant.match_score = grant_data.get('match_score', 0)
                    new_grant.match_explanation = grant_data.get('match_explanation', '')
                    new_grant.focus_areas = grant_data.get('focus_areas', [])
                    new_grant.contact_info = grant_data.get('contact_info', '')
                    
                    # Add enhanced contact and application details
                    new_grant.contact_name = grant_data.get('contact_name', '')
                    new_grant.contact_email = grant_data.get('contact_email', '')
                    new_grant.contact_phone = grant_data.get('contact_phone', '')
                    new_grant.submission_url = grant_data.get('submission_url', '')
                    new_grant.application_process = grant_data.get('application_process', '')
                    new_grant.grant_cycle = grant_data.get('grant_cycle', '')
                    
                    new_grant.is_scraped = True
                    new_grant.source_id = source_id
                    
                    # Add the new search-related fields
                    new_grant.search_query = grant_data.get('search_query', '')
                    new_grant.discovery_method = grant_data.get('discovery_method', 'manual')
                    
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
            
            # Add search report data if available with error handling
            if "search_report" in result:
                try:
                    history.sites_searched_estimate = result["search_report"]["sites_searched_estimate"]
                    history.total_queries_attempted = result["search_report"]["total_queries_attempted"] 
                    history.successful_queries = result["search_report"]["successful_queries"]
                    history.search_keywords_used = result["search_report"]["search_keywords_used"]
                    
                    # Log final metrics for debugging
                    logger.info(f"Final search metrics: {history.sites_searched_estimate} sites searched, " +
                               f"{history.successful_queries}/{history.total_queries_attempted} successful queries, " +
                               f"{history.grants_found} grants found, {history.grants_added} grants added")
                except KeyError as ke:
                    logger.warning(f"Missing key in search report: {ke}")
                except Exception as e:
                    logger.warning(f"Error updating search metrics: {e}")
            
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