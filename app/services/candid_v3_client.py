"""
Candid Premier API v3 Client - Foundation and Grant Data
"""
import os
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class CandidV3Client:
    """Client for Candid Premier API v3"""
    
    BASE_URL = "https://api.candid.org"
    
    def __init__(self):
        # Get API keys from environment - use the new working keys
        self.grants_keys = os.environ.get('CANDID_GRANTS_KEYS', 'cd6150ff5b27410899495f96969451ea,243699cfa8c9422f9347b970e391fb59').split(',')
        self.news_keys = os.environ.get('CANDID_NEWS_KEYS', '7647f9fe2d9645d48def7a04b6835083,0da558d408e74654baa000836cb88bef').split(',')
        self.primary_key = os.environ.get('CANDID_API_KEY', 'cd6150ff5b27410899495f96969451ea')
        self.current_key_index = 0
        self.timeout = 30
        
    def search_foundations(self, search_term: str = "", state: str = "", limit: int = 25) -> List[Dict]:
        """
        Search for foundations using Essentials API v3 (works with trial keys)
        
        Args:
            search_term: Keywords to search
            state: State code (e.g., 'NY')
            limit: Number of results
            
        Returns:
            List of foundation profiles
        """
        try:
            # Use Essentials API v3 search endpoint (works with trial keys)
            params = {}
            if search_term:
                params['search_terms'] = search_term
            if state:
                params['state'] = state
            params['page_size'] = str(limit)
            
            url = f"{self.BASE_URL}/essentials/v3/search"
            if params:
                url += '?' + urllib.parse.urlencode(params)
            
            headers = {
                'Accept': 'application/json',
                'Subscription-Key': self.primary_key
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                foundations = []
                if data.get('code') == 200:
                    # Extract foundation data
                    for result in data.get('data', {}).get('hits', []):
                        foundation = self._normalize_foundation(result)
                        if foundation:
                            foundations.append(foundation)
                            
                logger.info(f"Candid: Found {len(foundations)} foundations")
                return foundations
                
        except Exception as e:
            logger.error(f"Candid search error: {e}")
            return []
    
    def get_organization_profile(self, ein: str) -> Optional[Dict]:
        """
        Get detailed organization profile by EIN
        
        Args:
            ein: Organization EIN
            
        Returns:
            Organization profile dict or None
        """
        try:
            url = f"{self.BASE_URL}/premier/v3/{ein}"
            
            headers = {
                'Accept': 'application/json',
                'Subscription-Key': self.primary_key
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get('code') == 200:
                    return self._normalize_profile(data.get('data', {}))
                    
        except Exception as e:
            logger.error(f"Candid profile error for EIN {ein}: {e}")
            
        return None
    
    def search_grants(self, keywords: str = "", funder_name: str = "") -> List[Dict]:
        """
        Search for grant opportunities
        
        Args:
            keywords: Search keywords
            funder_name: Filter by funder name
            
        Returns:
            List of grant opportunities
        """
        try:
            # This would use the Candid Grants API endpoint
            # For now, we'll search foundations and create opportunities from them
            foundations = self.search_foundations(search_term=keywords or funder_name)
            
            opportunities = []
            for foundation in foundations[:10]:  # Limit for performance
                opportunity = {
                    'source': 'candid',
                    'source_type': 'Foundation',
                    'source_name': 'Candid Foundation Directory',
                    'title': f"Grant Opportunity from {foundation.get('name', 'Foundation')}",
                    'funder': foundation.get('name', ''),
                    'description': foundation.get('mission', ''),
                    'ein': foundation.get('ein', ''),
                    'location': f"{foundation.get('city', '')}, {foundation.get('state', '')}",
                    'website': foundation.get('website', ''),
                    'grant_type': 'Foundation Grant'
                }
                opportunities.append(opportunity)
                
            return opportunities
            
        except Exception as e:
            logger.error(f"Candid grants search error: {e}")
            return []
    
    def _normalize_foundation(self, raw_data: Dict) -> Optional[Dict]:
        """Normalize foundation search result"""
        try:
            summary = raw_data.get('summary', {})
            return {
                'ein': summary.get('ein', ''),
                'name': summary.get('organization_name', ''),
                'city': summary.get('city', ''),
                'state': summary.get('state', ''),
                'mission': summary.get('mission', ''),
                'website': summary.get('website_url', ''),
                'contact_email': summary.get('contact_email', ''),
                'profile_level': summary.get('gs_profile_update_level', ''),
                'year_founded': summary.get('year_founded', '')
            }
        except Exception as e:
            logger.error(f"Error normalizing foundation: {e}")
            return None
    
    def _normalize_profile(self, profile_data: Dict) -> Dict:
        """Normalize detailed organization profile"""
        try:
            summary = profile_data.get('summary', {})
            financials = profile_data.get('financials', {})
            
            return {
                'ein': summary.get('ein', ''),
                'name': summary.get('organization_name', ''),
                'mission': summary.get('mission', ''),
                'description': summary.get('impact_statement', ''),
                'address': {
                    'line1': summary.get('address_line_1', ''),
                    'line2': summary.get('address_line_2', ''),
                    'city': summary.get('city', ''),
                    'state': summary.get('state', ''),
                    'zip': summary.get('zip', '')
                },
                'contact': {
                    'name': summary.get('contact_name', ''),
                    'title': summary.get('contact_title', ''),
                    'email': summary.get('contact_email', ''),
                    'phone': summary.get('contact_phone', '')
                },
                'website': summary.get('website_url', ''),
                'year_founded': summary.get('year_founded', ''),
                'ntee_code': summary.get('ntee_code', ''),
                'financials': financials,
                'keywords': summary.get('keywords', '').split(', ') if summary.get('keywords') else [],
                'social_media': summary.get('social_media_urls', [])
            }
        except Exception as e:
            logger.error(f"Error normalizing profile: {e}")
            return {}

# Singleton instance
_client = None

def get_candid_v3_client() -> CandidV3Client:
    """Get singleton Candid v3 client instance"""
    global _client
    if _client is None:
        _client = CandidV3Client()
    return _client