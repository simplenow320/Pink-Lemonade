"""
Grants.gov API Client
"""
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class GrantsGovClient:
    """Client for Grants.gov using GSA Search API (same API grants.gov uses internally)"""
    
    BASE_URL = "https://api.gsa.gov/technology/searchgov/v2/results/i14y"
    AFFILIATE = "prod_grants"
    ACCESS_KEY = "YNhIX2DaXaH2XZFS6cVf5O6hySoFtg5WsiiKCoV3eEg="
    
    def __init__(self):
        self.timeout = 30
        
    def _get_json(self, params: Dict) -> Optional[Dict]:
        """Make GET request with query parameters"""
        # Add required GSA Search API parameters
        params.update({
            'affiliate': self.AFFILIATE,
            'access_key': self.ACCESS_KEY
        })
        
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                logger.info(f"GSA Search API endpoint hit: {url}, status: {response.status}")
                if response.status == 200:
                    return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            logger.error(f"GSA Search API HTTP Error {e.code}: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"GSA Search API request error: {e}")
            return None
            
        return None
    
    def search_opportunities(self, payload: Dict) -> List[Dict]:
        """
        Search for grant opportunities using GSA Search API
        
        Args:
            payload: Search parameters dict
            
        Returns:
            List of normalized opportunity dicts
        """
        try:
            # Build search query from payload
            keywords = payload.get("keywords", ["grant"])
            if isinstance(keywords, list):
                query = " ".join(keywords)
            else:
                query = str(keywords)
            
            # Add opportunity-specific terms to find actual grant opportunities
            query += " opportunity OR funding OR NOFO OR solicitation"
            
            search_params = {
                "query": query,
                "limit": payload.get("limit", 20)
            }
            
            result = self._get_json(search_params)
            if not result:
                return []
                
            opportunities = []
            
            # Extract web results that look like grant opportunities
            web_results = result.get("web", {}).get("results", [])
            for result_item in web_results:
                if self._is_grant_opportunity(result_item):
                    normalized = self._normalize_search_result(result_item)
                    if normalized:
                        opportunities.append(normalized)
                        
            logger.info(f"Found {len(opportunities)} grant opportunities from GSA Search")
            return opportunities
            
        except Exception as e:
            logger.error(f"Grants.gov search error: {e}")
            return []
    
    def fetch_opportunity(self, opp_number: str) -> Dict:
        """
        Fetch detailed opportunity by searching for the specific opportunity number
        
        Args:
            opp_number: Opportunity number
            
        Returns:
            Detailed opportunity dict or empty dict on error
        """
        try:
            # Search for the specific opportunity number
            search_params = {
                "query": opp_number,
                "limit": 5
            }
            
            result = self._get_json(search_params)
            if not result:
                return {}
                
            # Look for the exact opportunity in search results
            web_results = result.get("web", {}).get("results", [])
            for result_item in web_results:
                if opp_number.lower() in result_item.get("url", "").lower():
                    return self._normalize_search_result(result_item) or {}
                    
            return {}
            
        except Exception as e:
            logger.error(f"Grants.gov fetch error: {e}")
            return {}
    
    def _is_grant_opportunity(self, result: Dict) -> bool:
        """Check if a search result looks like a grant opportunity"""
        url = result.get("url", "").lower()
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        
        # Look for opportunity indicators
        opportunity_indicators = [
            "/web/grants/search-grants.html",
            "search-results-detail",
            "funding-opportunity",
            "notice-of-funding"
        ]
        
        # Check URL for opportunity patterns
        for indicator in opportunity_indicators:
            if indicator in url:
                return True
                
        # Check title/snippet for grant terms
        grant_terms = ["funding", "grant", "opportunity", "nofo", "solicitation", "award"]
        if any(term in title or term in snippet for term in grant_terms):
            # But exclude general information pages
            exclusions = ["about grants", "grant policies", "grant terminology", "help"]
            if not any(excl in title or excl in snippet for excl in exclusions):
                return True
                
        return False
    
    def _normalize_search_result(self, result: Dict) -> Optional[Dict]:
        """Normalize search result to opportunity format"""
        try:
            url = result.get("url", "")
            
            # Extract opportunity number from URL if possible
            opp_number = ""
            if "search-results-detail" in url:
                opp_number = url.split("/")[-1] if "/" in url else ""
            
            return {
                "source": "grants_gov",
                "source_type": "Federal",
                "source_name": "Grants.gov Search",
                "funder_name": "Federal Government",  # Add default funder
                "funder": "Federal Government",
                "opp_number": opp_number,
                "title": result.get("title", ""),
                "description": result.get("snippet", ""),
                "source_url": url,
                "link": url,
                "published_date": result.get("publication_date", ""),
                "raw": result
            }
        except Exception as e:
            logger.error(f"Error normalizing search result: {e}")
            return None
    
    def _normalize_opportunity(self, opp: Dict) -> Optional[Dict]:
        """
        Normalize opportunity data
        
        Never invents amounts or data not present
        """
        try:
            # Required fields
            opp_number = opp.get("opportunityNumber") or opp.get("oppNumber")
            if not opp_number:
                return None
                
            normalized = {
                "source": "grants_gov",
                "opp_number": opp_number,
                "title": opp.get("title", ""),
                "agency": opp.get("agency", ""),
                "posted_date": opp.get("postedDate", ""),
                "close_date": opp.get("closeDate", ""),
                "eligibility_text": opp.get("eligibility", ""),
                "link": f"https://www.grants.gov/search-results-detail/{opp_number}",
                "raw": opp
            }
            
            # Only include amount if explicitly present - never invent
            if "awardFloor" in opp and opp["awardFloor"]:
                normalized["award_floor"] = opp["awardFloor"]
            if "awardCeiling" in opp and opp["awardCeiling"]:
                normalized["award_ceiling"] = opp["awardCeiling"]
                
            return normalized
            
        except Exception:
            return None

# Singleton instance
_client = None

def get_grants_gov_client() -> GrantsGovClient:
    """Get singleton Grants.gov client"""
    global _client
    if _client is None:
        _client = GrantsGovClient()
    return _client