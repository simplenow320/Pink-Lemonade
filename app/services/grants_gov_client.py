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
    """Client for Grants.gov API"""
    
    BASE_URL = "https://api.grants.gov/v1/api"
    
    def __init__(self):
        self.timeout = 30
        
    def _post_json(self, endpoint: str, payload: Dict) -> Optional[Dict]:
        """Make POST request with JSON payload"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                logger.info(f"Grants.gov API endpoint hit: {url}, status: {response.status}")
                if response.status == 200:
                    return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            logger.error(f"Grants.gov API endpoint hit: {url}, HTTP Error {e.code}: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"Grants.gov API request error: {e}")
            return None
            
        return None
    
    def search_opportunities(self, payload: Dict) -> List[Dict]:
        """
        Search for grant opportunities
        
        Args:
            payload: Search parameters dict
            
        Returns:
            List of normalized opportunity dicts
        """
        try:
            result = self._post_json("search2", payload)
            if not result:
                return []
                
            opportunities = []
            
            # Extract opportunities from response
            opps_data = result.get("opportunities", [])
            if isinstance(opps_data, list):
                for opp in opps_data:
                    normalized = self._normalize_opportunity(opp)
                    if normalized:
                        opportunities.append(normalized)
                        
            return opportunities
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def fetch_opportunity(self, opp_number: str) -> Dict:
        """
        Fetch detailed opportunity by number
        
        Args:
            opp_number: Opportunity number
            
        Returns:
            Detailed opportunity dict or empty dict on error
        """
        try:
            payload = {"opportunityNumber": opp_number}
            result = self._post_json("fetchOpportunity", payload)
            
            if not result:
                return {}
                
            # Return detailed fields without guessing
            detail = {
                "source": "grants_gov",
                "opp_number": opp_number,
                "raw": result
            }
            
            # Extract known fields safely
            if "title" in result:
                detail["title"] = result["title"]
            if "agency" in result:
                detail["agency"] = result["agency"]
            if "description" in result:
                detail["description"] = result["description"]
            if "eligibility" in result:
                detail["eligibility_text"] = result["eligibility"]
            if "closeDate" in result:
                detail["close_date"] = result["closeDate"]
            if "postedDate" in result:
                detail["posted_date"] = result["postedDate"]
                
            # Format link
            detail["link"] = f"https://www.grants.gov/search-results-detail/{opp_number}"
            
            return detail
            
        except Exception as e:
            print(f"Fetch error: {e}")
            return {}
    
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