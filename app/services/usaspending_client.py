"""
USAspending.gov API Client - Free government spending data
Fixed to use correct endpoints and parameters
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
        
    def search_assistance_listings(self, keywords: str = "grant") -> List[Dict]:
        """
        Search for federal assistance programs using the correct API endpoint
        
        Args:
            keywords: Search terms
            
        Returns:
            List of normalized assistance programs
        """
        try:
            # Use the assistance listings endpoint instead of awards search
            # This endpoint provides CFDA programs, not historical awards
            url = f"{self.BASE_URL}/autocomplete/cfda/"
            
            params = {
                'search_text': keywords,
                'limit': 50
            }
            
            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"
            
            headers = {
                'Accept': 'application/json'
            }
            
            req = urllib.request.Request(full_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                programs = []
                for program in result.get('results', []):
                    normalized = self._normalize_cfda_program(program)
                    if normalized:
                        programs.append(normalized)
                        
                logger.info(f"USAspending: Found {len(programs)} assistance programs")
                return programs
                
        except Exception as e:
            logger.error(f"USAspending CFDA search error: {e}")
            # Try alternative awards endpoint
            return self._search_recent_grants(keywords)
    
    def _search_recent_grants(self, keywords: str = "") -> List[Dict]:
        """
        Alternative: Search recent grant awards using spending by award endpoint
        """
        try:
            # Calculate date range - last 90 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            payload = {
                "filters": {
                    "time_period": [{
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d")
                    }],
                    "award_type_codes": ["06", "07", "08", "09", "10", "11"],  # Correct grant codes
                    "keywords": [keywords] if keywords else None
                },
                "fields": [
                    "Award ID",
                    "Recipient Name", 
                    "Award Amount",
                    "Awarding Agency",
                    "Start Date",
                    "End Date",
                    "Description",
                    "Award Type"
                ],
                "page": 1,
                "limit": 50,
                "sort": "Award Amount",
                "order": "desc"
            }
            
            # Remove None values
            if not payload["filters"]["keywords"]:
                del payload["filters"]["keywords"]
            
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
                        
                logger.info(f"USAspending: Found {len(programs)} recent grant awards")
                return programs
                
        except Exception as e:
            logger.error(f"USAspending awards search error: {e}")
            return []
    
    def _normalize_cfda_program(self, program: Dict) -> Optional[Dict]:
        """Normalize CFDA program to opportunity format"""
        try:
            return {
                'source': 'usaspending',
                'source_type': 'Federal',
                'source_name': 'USAspending.gov',
                'title': program.get('program_title', 'Federal Assistance Program'),
                'funder': program.get('popular_name', 'Federal Agency'),
                'cfda_number': program.get('program_number', ''),
                'description': f"CFDA Program {program.get('program_number', '')}: {program.get('program_title', '')}",
                'grant_type': 'Federal Assistance Program'
            }
        except Exception as e:
            logger.error(f"Error normalizing CFDA program: {e}")
            return None
    
    def _normalize_award(self, award: Dict) -> Optional[Dict]:
        """Normalize USAspending award to opportunity format"""
        try:
            return {
                'source': 'usaspending',
                'source_type': 'Historical',
                'source_name': 'USAspending.gov',
                'title': award.get('Description', award.get('Award Type', 'Federal Grant Award')),
                'funder': award.get('Awarding Agency', 'Federal Agency'),
                'recipient': award.get('Recipient Name', ''),
                'amount': award.get('Award Amount', ''),
                'award_id': award.get('Award ID', ''),
                'start_date': award.get('Start Date', ''),
                'end_date': award.get('End Date', ''),
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
