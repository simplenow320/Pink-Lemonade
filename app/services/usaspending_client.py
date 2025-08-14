"""
USAspending.gov API Client - Free government spending data
"""
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class USAspendingClient:
    """Client for USAspending.gov API - no auth needed"""
    
    BASE_URL = "https://api.usaspending.gov/api/v2"
    
    def __init__(self):
        self.timeout = 30
        
    def search_assistance_listings(self, keywords: str = "") -> List[Dict]:
        """
        Search for federal assistance programs
        
        Args:
            keywords: Search terms
            
        Returns:
            List of normalized assistance programs
        """
        try:
            payload = {
                "filters": {
                    "keywords": [keywords] if keywords else [],
                    "award_type_codes": ["02", "03", "04", "05"]  # Grant types
                },
                "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency", 
                          "Start Date", "End Date", "Description", "Place of Performance"],
                "page": 1,
                "limit": 50,
                "sort": "Award Amount",
                "order": "desc"
            }
            
            url = f"{self.BASE_URL}/search/spending_by_award/"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                programs = []
                for award in result.get('results', []):
                    normalized = self._normalize_award(award)
                    if normalized:
                        programs.append(normalized)
                        
                logger.info(f"USAspending: Found {len(programs)} grant awards")
                return programs
                
        except Exception as e:
            logger.error(f"USAspending search error: {e}")
            return []
    
    def _normalize_award(self, award: Dict) -> Optional[Dict]:
        """Normalize USAspending award to opportunity format"""
        try:
            return {
                'source': 'usaspending',
                'source_type': 'Historical',
                'source_name': 'USAspending.gov',
                'title': award.get('Description', 'Federal Grant Award'),
                'funder': award.get('Awarding Agency', 'Federal Agency'),
                'recipient': award.get('Recipient Name', ''),
                'amount': award.get('Award Amount', ''),
                'award_id': award.get('Award ID', ''),
                'start_date': award.get('Start Date', ''),
                'end_date': award.get('End Date', ''),
                'location': award.get('Place of Performance', ''),
                'grant_type': 'Historical Award'
            }
        except Exception as e:
            logger.error(f"Error normalizing award: {e}")
            return None

# Singleton instance
_client = None

def get_usaspending_client() -> USAspendingClient:
    """Get singleton USAspending client instance"""
    global _client
    if _client is None:
        _client = USAspendingClient()
    return _client