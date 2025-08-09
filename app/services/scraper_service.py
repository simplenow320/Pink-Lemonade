"""
Scraper Service - Safe, LIVE/DEMO aware grant discovery with deduplication
Handles multiple grant sources including Grants.gov with proper error handling
"""

from __future__ import annotations
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import json
import requests
from urllib.parse import urlencode

from app import db
from app.models import Grant, Watchlist, WatchlistSource, ScraperSource
from app.services.mode import is_live, get_mode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperService:
    """Main scraper service coordinating grant discovery from multiple sources"""
    
    def __init__(self):
        self.mode = get_mode()
        self.is_live = is_live()
        self.sources = self._initialize_sources()
        logger.info(f"ScraperService initialized in {self.mode} mode")
        
    def _initialize_sources(self) -> Dict[str, Any]:
        """Initialize available grant sources"""
        sources = {}
        
        if self.is_live:
            # Initialize live sources only if API keys are available
            if os.getenv("GRANTS_GOV_API_KEY"):
                sources["grants_gov"] = GrantsGovConnector()
                logger.info("Grants.gov connector initialized")
            else:
                logger.warning("Grants.gov API key not found - source disabled")
                
            # Add other live sources here as needed
            # if os.getenv("FOUNDATION_API_KEY"):
            #     sources["foundation_directory"] = FoundationDirectoryConnector()
                
        else:
            # Demo mode - use mock data
            sources["demo"] = DemoDataConnector()
            logger.info("Demo data connector initialized for testing")
            
        return sources
    
    def discover_grants(self, org_id: int, limit: int = 50) -> Tuple[List[Grant], Dict[str, Any]]:
        """
        Discover new grants from all configured sources
        
        Returns:
            Tuple of (grants_list, statistics_dict)
        """
        all_grants = []
        stats = {
            "total_discovered": 0,
            "new_grants": 0,
            "duplicates_skipped": 0,
            "sources_checked": len(self.sources),
            "errors": []
        }
        
        logger.info(f"Starting grant discovery for org {org_id} with {len(self.sources)} sources")
        
        for source_name, connector in self.sources.items():
            try:
                logger.info(f"Fetching from {source_name}...")
                grants = connector.fetch_grants(limit=limit // len(self.sources) or 10)
                
                # Process and deduplicate grants
                for grant_data in grants:
                    grant = self._process_grant(grant_data, org_id, source_name)
                    if grant:
                        all_grants.append(grant)
                        stats["new_grants"] += 1
                    else:
                        stats["duplicates_skipped"] += 1
                        
                stats["total_discovered"] += len(grants)
                logger.info(f"Processed {len(grants)} grants from {source_name}")
                
            except Exception as e:
                error_msg = f"Error fetching from {source_name}: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                
        logger.info(f"Discovery complete: {stats['new_grants']} new, {stats['duplicates_skipped']} duplicates")
        return all_grants, stats
    
    def _process_grant(self, grant_data: Dict[str, Any], org_id: int, source: str) -> Optional[Grant]:
        """Process and deduplicate a single grant"""
        try:
            # Generate unique hash for deduplication
            unique_key = self._generate_grant_hash(grant_data)
            
            # Check for existing grant using title and funder
            existing = Grant.query.filter_by(
                org_id=org_id,
                title=grant_data.get("title", ""),
                funder=grant_data.get("funder", "")
            ).first()
            
            if existing:
                logger.debug(f"Duplicate grant found: {grant_data.get('title', 'Unknown')}")
                # Update last_seen timestamp
                existing.updated_at = datetime.utcnow()
                db.session.commit()
                return None
                
            # Create new grant
            grant = Grant()
            grant.org_id = org_id
            grant.title = grant_data.get("title", "Untitled Grant")
            grant.funder = grant_data.get("funder", "Unknown Funder")
            grant.link = grant_data.get("url", "")
            grant.amount_min = grant_data.get("amount_min")
            grant.amount_max = grant_data.get("amount_max")
            grant.deadline = self._parse_deadline(grant_data.get("deadline"))
            grant.geography = grant_data.get("geographic_focus", "")
            grant.eligibility = grant_data.get("eligibility", "")
            grant.status = "idea"  # Default status from model
            grant.source_name = source
            grant.source_url = grant_data.get("url", "")
            grant.match_score = None  # Will be calculated later
            grant.match_reason = None
            grant.created_at = datetime.utcnow()
            grant.updated_at = datetime.utcnow()
            
            # Store focus areas in eligibility if provided
            if "focus_areas" in grant_data:
                focus_areas_text = f"Focus Areas: {', '.join(grant_data['focus_areas'])}"
                if grant.eligibility:
                    grant.eligibility = f"{grant.eligibility}\n{focus_areas_text}"
                else:
                    grant.eligibility = focus_areas_text
                
            db.session.add(grant)
            db.session.commit()
            
            logger.info(f"Added new grant: {grant.title} from {source}")
            return grant
            
        except Exception as e:
            logger.error(f"Error processing grant: {str(e)}")
            db.session.rollback()
            return None
    
    def _generate_grant_hash(self, grant_data: Dict[str, Any]) -> str:
        """Generate unique hash for grant deduplication"""
        # Use title, funder, and deadline for uniqueness
        key_parts = [
            grant_data.get("title", "").lower().strip(),
            grant_data.get("funder", "").lower().strip(),
            str(grant_data.get("deadline", ""))
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _parse_deadline(self, deadline_str: Any) -> Optional[datetime]:
        """Parse various deadline formats"""
        if not deadline_str:
            return None
            
        if isinstance(deadline_str, datetime):
            return deadline_str
            
        try:
            # Try common date formats
            from dateutil import parser
            return parser.parse(str(deadline_str))
        except:
            logger.warning(f"Could not parse deadline: {deadline_str}")
            return None
    
    def update_watchlist_grants(self, watchlist_id: int) -> Dict[str, Any]:
        """Update grants for a specific watchlist based on its criteria"""
        watchlist = Watchlist.query.get(watchlist_id)
        if not watchlist:
            return {"error": "Watchlist not found"}
            
        stats = {
            "watchlist": watchlist.name,
            "grants_matched": 0,
            "sources_checked": 0
        }
        
        # Get watchlist sources
        sources = WatchlistSource.query.filter_by(watchlist_id=watchlist_id).all()
        
        for source in sources:
            # Fetch grants from this source
            # Match against watchlist criteria
            # Update associations
            stats["sources_checked"] += 1
            
        return stats


class GrantsGovConnector:
    """Connector for Grants.gov REST API"""
    
    def __init__(self):
        self.api_key = os.getenv("GRANTS_GOV_API_KEY")
        self.base_url = "https://api.grants.gov/v2/opportunities/search"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def fetch_grants(self, limit: int = 25, keywords: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch grants from Grants.gov API"""
        grants = []
        
        try:
            # Build query parameters
            params = {
                "limit": min(limit, 100),  # API max is 100
                "offset": 0,
                "sortBy": "postedDate|desc"
            }
            
            if keywords:
                params["keywords"] = keywords
                
            # Make API request
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get("opportunities", [])
                
                for opp in opportunities:
                    grant = self._parse_opportunity(opp)
                    if grant:
                        grants.append(grant)
                        
                logger.info(f"Fetched {len(grants)} grants from Grants.gov")
                
            else:
                logger.error(f"Grants.gov API error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            logger.error("Grants.gov API timeout")
        except Exception as e:
            logger.error(f"Error fetching from Grants.gov: {str(e)}")
            
        return grants
    
    def _parse_opportunity(self, opp: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Grants.gov opportunity into standard grant format"""
        try:
            # Extract deadline
            close_date = opp.get("closeDate")
            deadline = None
            if close_date:
                try:
                    deadline = datetime.strptime(close_date, "%Y-%m-%d")
                except:
                    deadline = close_date
                    
            return {
                "title": opp.get("oppTitle", "Untitled"),
                "funder": opp.get("agencyName", "Federal Agency"),
                "description": opp.get("description", opp.get("synopsis", "")),
                "amount_min": opp.get("awardFloor"),
                "amount_max": opp.get("awardCeiling"),
                "deadline": deadline,
                "url": f"https://grants.gov/search-results-detail/{opp.get('id')}",
                "opportunity_number": opp.get("oppNumber"),
                "eligibility": opp.get("eligibilityCodes", []),
                "focus_areas": opp.get("categories", []),
                "geographic_focus": opp.get("geographicScope", "National"),
                "posted_date": opp.get("postedDate"),
                "modified_date": opp.get("modifiedDate"),
                "source_id": opp.get("id")
            }
        except Exception as e:
            logger.error(f"Error parsing Grants.gov opportunity: {str(e)}")
            return None


class DemoDataConnector:
    """Demo data connector for testing without live APIs"""
    
    def fetch_grants(self, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Return demo grant data for testing"""
        demo_grants = [
            {
                "title": f"Demo Community Development Grant {i+1}",
                "funder": "Demo Foundation",
                "description": "This is a demo grant for testing purposes. In LIVE mode, real grants will appear here.",
                "amount_min": 5000 * (i+1),
                "amount_max": 10000 * (i+1),
                "deadline": datetime.utcnow() + timedelta(days=30+i*7),
                "url": f"https://example.com/demo-grant-{i+1}",
                "focus_areas": ["Education", "Community Development"],
                "geographic_focus": "Michigan"
            }
            for i in range(min(limit, 5))
        ]
        
        logger.info(f"Generated {len(demo_grants)} demo grants for testing")
        return demo_grants


class ScraperScheduler:
    """Scheduler for automated grant discovery"""
    
    def __init__(self):
        self.service = ScraperService()
        self.is_running = False
        
    def run_discovery(self, org_id: int):
        """Run grant discovery for an organization"""
        if not self.is_running:
            self.is_running = True
            try:
                logger.info(f"Starting scheduled discovery for org {org_id}")
                grants, stats = self.service.discover_grants(org_id)
                logger.info(f"Discovery complete: {stats}")
                
                # Update scraper sources status
                self._update_source_status(stats)
                
            finally:
                self.is_running = False
                
    def _update_source_status(self, stats: Dict[str, Any]):
        """Update source status in database"""
        try:
            for source_name in self.service.sources.keys():
                source = ScraperSource.query.filter_by(name=source_name).first()
                if source:
                    source.last_run = datetime.utcnow()
                    source.status = "active" if source_name not in [e.split(":")[0] for e in stats.get("errors", [])] else "error"
                    db.session.commit()
        except Exception as e:
            logger.error(f"Error updating source status: {str(e)}")
            db.session.rollback()


# Convenience functions for API usage
def discover_grants_for_org(org_id: int, limit: int = 50) -> Tuple[List[Grant], Dict[str, Any]]:
    """Convenience function to discover grants for an organization"""
    service = ScraperService()
    return service.discover_grants(org_id, limit)

def get_scraper_status() -> Dict[str, Any]:
    """Get current scraper status and configuration"""
    return {
        "mode": get_mode(),
        "is_live": is_live(),
        "sources_available": list(ScraperService().sources.keys()),
        "last_run": None  # Would need to query from database
    }

# Legacy functions for backward compatibility with existing API
def run_scraping_job(org_id: int = 1) -> Dict[str, Any]:
    """Run a scraping job for an organization (legacy function)"""
    grants, stats = discover_grants_for_org(org_id)
    return {
        "status": "completed",
        "grants_discovered": stats["new_grants"],
        "duplicates_skipped": stats["duplicates_skipped"],
        "sources_checked": stats["sources_checked"],
        "errors": stats.get("errors", [])
    }

def scrape_grants(source_url: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Scrape grants from sources (legacy function)"""
    service = ScraperService()
    all_grants = []
    
    # Use demo or live sources
    for source_name, connector in service.sources.items():
        try:
            grants = connector.fetch_grants(limit=limit)
            for grant_data in grants:
                all_grants.append(grant_data)
        except Exception as e:
            logger.error(f"Error in legacy scrape_grants from {source_name}: {str(e)}")
    
    return all_grants