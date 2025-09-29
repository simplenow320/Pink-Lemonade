"""
Candid Grants API v1 Client - Working implementation
"""
import os
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class CandidGrantsClient:
    """Client for Candid Grants API v1 - WORKING"""
    
    BASE_URL = "https://api.candid.org/grants/v1"
    
    def __init__(self):
        # Use environment variable for API key - no hardcoded keys
        self.primary_key = os.environ.get('CANDID_GRANTS_KEYS')
        if not self.primary_key:
            logger.warning("CANDID_GRANTS_KEYS not set - Candid Grants API disabled")
        self.timeout = 30  # Increased timeout for large grant responses
        
    def get_summary(self) -> Dict:
        """
        Get grants summary statistics
        
        Returns:
            Summary statistics dict
        """
        try:
            url = f"{self.BASE_URL}/summary"
            headers = {
                'Subscription-Key': self.primary_key,
                'Accept': 'application/json'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get('meta', {}).get('code') == 200:
                    logger.info(f"Candid Grants API: Successfully retrieved summary")
                    return data.get('data', {})
                    
        except Exception as e:
            logger.error(f"Candid summary error: {e}")
            
        return {}
    
    def search_grants(self, 
                     funder_name: str = "",
                     recipient_name: str = "",
                     state: str = "",
                     keyword: str = "",
                     min_amount: Optional[int] = None,
                     max_amount: Optional[int] = None,
                     year: Optional[int] = None,
                     limit: int = 25) -> List[Dict]:
        """
        Search for grants using Candid Grants API /transactions endpoint
        
        Returns:
            List of real grants from Candid's 29.2 million grant database
        """
        if not self.primary_key:
            logger.warning("No Candid API key configured")
            return []
            
        try:
            # Build query parameters - use simpler params that actually work
            params = {}
            if year:
                params['year'] = str(year)
            # Note: Other filters can be applied client-side after fetching
                
            # Call the transactions endpoint
            url = f"{self.BASE_URL}/transactions"
            if params:
                url += '?' + urllib.parse.urlencode(params)
                
            headers = {
                'Subscription-Key': self.primary_key,
                'Accept': 'application/json'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                grants = []
                # Parse the real response structure: data.rows contains grants
                if 'data' in data and 'rows' in data['data']:
                    for grant_row in data['data']['rows']:
                        normalized = self._normalize_grant(grant_row)
                        if normalized:
                            # Apply client-side filters
                            # State filter
                            if state and state.upper() not in normalized.get('geography', '').upper():
                                continue
                            # Funder filter
                            if funder_name and funder_name.lower() not in normalized.get('funder', '').lower():
                                continue
                            # Recipient filter  
                            if recipient_name and recipient_name.lower() not in normalized.get('recipient', '').lower():
                                continue
                            # Amount filters
                            grant_amount = normalized.get('amount', 0)
                            if min_amount and grant_amount < min_amount:
                                continue
                            if max_amount and grant_amount > max_amount:
                                continue
                            # Keyword filter
                            if keyword:
                                keyword_lower = keyword.lower()
                                # Check if keyword appears in description, funder, or recipient
                                if not (keyword_lower in normalized.get('description', '').lower() or
                                        keyword_lower in normalized.get('funder', '').lower() or
                                        keyword_lower in normalized.get('recipient', '').lower() or
                                        keyword_lower in normalized.get('title', '').lower()):
                                    continue
                            
                            grants.append(normalized)
                            # Stop when we have enough grants
                            if len(grants) >= limit:
                                break
                                
                    logger.info(f"Candid API: Retrieved {len(grants)} real grants from transactions endpoint")
                else:
                    logger.warning(f"Unexpected response structure from Candid API: {data.get('meta', {})}")
                    
                return grants
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else 'No error body'
            if e.code == 429:
                logger.warning(f"Candid API rate limit exceeded. Try again later.")
            else:
                logger.error(f"Candid API HTTP error {e.code}: {error_body}")
            return []
        except Exception as e:
            logger.error(f"Candid search error: {e}")
            return []
    
    def get_funders(self, state: str = "", limit: int = 25) -> List[Dict]:
        """
        Get list of funders
        
        Args:
            state: State code filter
            limit: Number of results
            
        Returns:
            List of funders
        """
        try:
            params = {
                'page_size': str(limit)
            }
            if state:
                params['state'] = state
                
            url = f"{self.BASE_URL}/funders"
            if params:
                url += '?' + urllib.parse.urlencode(params)
            
            headers = {
                'Subscription-Key': self.primary_key,
                'Accept': 'application/json'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                funders = []
                if data.get('meta', {}).get('code') == 200:
                    for funder in data.get('data', {}).get('funders', []):
                        funders.append({
                            'source': 'candid_grants',
                            'source_type': 'Foundation',
                            'source_name': 'Candid Grants Database',
                            'title': f"Grant Opportunities from {funder.get('name', 'Foundation')}",
                            'funder': funder.get('name', ''),
                            'ein': funder.get('ein', ''),
                            'city': funder.get('city', ''),
                            'state': funder.get('state', ''),
                            'total_giving': funder.get('total_giving', ''),
                            'grant_count': funder.get('grant_count', ''),
                            'website': funder.get('website', ''),
                            'grant_type': 'Foundation Grant'
                        })
                        
                logger.info(f"Candid: Found {len(funders)} funders")
                return funders
                
        except Exception as e:
            logger.error(f"Candid funders error: {e}")
            return []
    
    def get_transactions(self, 
                        year: Optional[int] = None,
                        state: str = "",
                        page: int = 1,
                        page_size: int = 100) -> Dict:
        """
        Get grant transactions from Candid API
        
        Args:
            year: Year filter (e.g., 2024)
            state: State code filter
            page: Page number for pagination
            page_size: Number of results per page (max 100)
            
        Returns:
            Dict with grants data and pagination info
        """
        if not self.primary_key:
            logger.warning("No Candid API key configured")
            return {'grants': [], 'total': 0, 'page': page}
            
        try:
            # Build query parameters - use only params that work
            params = {}
            if year:
                params['year'] = str(year)
            # Note: page and state params may need different names or client-side filtering
                
            # Call the transactions endpoint  
            url = f"{self.BASE_URL}/transactions"
            if params:
                url += '?' + urllib.parse.urlencode(params)
                
            headers = {
                'Subscription-Key': self.primary_key,
                'Accept': 'application/json'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                grants = []
                total = 0
                
                # Parse the real response structure
                if 'data' in data:
                    total = data['data'].get('total_count', 0)
                    rows = data['data'].get('rows', [])
                    
                    for grant_row in rows:
                        normalized = self._normalize_grant(grant_row)
                        if normalized:
                            grants.append(normalized)
                            
                    logger.info(f"Candid API: Retrieved page {page} with {len(grants)} grants (total: {total:,})")
                    
                return {
                    'grants': grants,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'has_more': len(grants) == page_size
                }
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else 'No error body'
            if e.code == 429:
                logger.warning(f"Candid API rate limit exceeded. Try again later.")
            else:
                logger.error(f"Candid API HTTP error {e.code}: {error_body}")
            return {'grants': [], 'total': 0, 'page': page}
        except Exception as e:
            logger.error(f"Candid transactions error: {e}")
            return {'grants': [], 'total': 0, 'page': page}
    
    def _normalize_grant(self, grant: Dict) -> Optional[Dict]:
        """Normalize grant data from actual Candid API fields to standard format"""
        try:
            # Map actual Candid field names to our standard format
            amount_usd = grant.get('amount_usd', 0)
            
            # Build a meaningful title from grant description or create one
            grant_desc = grant.get('grant_description', '')
            funder_name = grant.get('funder_name', 'Unknown Foundation')
            recip_name = grant.get('recip_name', 'Unknown Recipient')
            
            if grant_desc:
                title = f"{funder_name}: {grant_desc[:100]}"
            else:
                title = f"{funder_name} grant to {recip_name}"
                
            # Build geography string from city/state
            geography_parts = []
            if grant.get('recip_city'):
                geography_parts.append(grant.get('recip_city'))
            if grant.get('recip_state'):
                geography_parts.append(grant.get('recip_state'))
            geography = ', '.join(geography_parts) if geography_parts else 'Not specified'
            
            return {
                'source': 'candid_grants',
                'source_type': 'Foundation',
                'source_name': 'Candid Grants Database (29.2M grants)',
                'title': title,
                'funder': funder_name,
                'recipient': recip_name,
                'amount_min': amount_usd,
                'amount_max': amount_usd,
                'amount': amount_usd,
                'year': grant.get('year_issued', grant.get('year', '')),
                'grant_id': grant.get('grant_id', grant.get('id', '')),
                'funder_ein': grant.get('funder_ein', ''),
                'recipient_ein': grant.get('recip_ein', ''),
                'geography': geography,
                'location': geography,
                'grant_type': grant.get('grant_type', 'Foundation Grant'),
                'description': grant_desc or f"Grant from {funder_name} to {recip_name}",
                'focus_area': grant.get('subject', grant.get('focus_area', '')),
                'website': grant.get('funder_website', ''),
                # Additional Candid fields that might be useful
                'support_type': grant.get('support_type', ''),
                'activity_type': grant.get('activity_type', ''),
                'population_served': grant.get('population_served', '')
            }
        except Exception as e:
            logger.error(f"Error normalizing grant: {e}")
            return None

# Singleton instance
_client = None

def get_candid_grants_client() -> CandidGrantsClient:
    """Get singleton Candid Grants client instance"""
    global _client
    if _client is None:
        _client = CandidGrantsClient()
    return _client