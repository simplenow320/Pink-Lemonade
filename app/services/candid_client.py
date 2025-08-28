"""
Candid API Client with News, Grants, and Essentials endpoints
Configured with trial keys confirmed active by Candid support
"""
import requests
import os
import statistics
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.services.http_helpers import SimpleCache


class NewsClient:
    """Candid News API Client"""
    
    def __init__(self):
        self.base_url = "https://api.candid.org/news/v1"
        # Confirmed News API key from Candid support
        self.api_key = os.environ.get('CANDID_NEWS_KEYS', 'dea86cce366d452a87b9b3a2e5eadbae')
        self.cache = SimpleCache()
    
    def _make_request(self, url: str, params: Dict) -> Optional[Dict]:
        """Make request to Candid News API"""
        try:
            headers = {
                'Accept': 'application/json',
                'Subscription-Key': self.api_key
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # 404 means no results found for the search parameters - not an error
                # As per Candid docs: broaden search parameters if this occurs
                return {"results": [], "count": 0, "message": "No results found - consider broadening search parameters"}
            elif response.status_code in [401, 429]:
                return {"error": f"API authentication/rate limit error: {response.status_code}"}
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except requests.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def search(self, query: str, start_date: Optional[str] = None, end_date: Optional[str] = None, 
               pcs_subject_codes: Optional[List[str]] = None, pcs_population_codes: Optional[List[str]] = None,
               region: Optional[str] = None, page: int = 1, size: int = 25) -> List[Dict]:
        """Search Candid news with filters"""
        
        # Check cache first
        params = {
            'search_terms': query,  # Corrected parameter name
            'page': page
        }
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date  
        if pcs_subject_codes:
            params['subjects'] = pcs_subject_codes  # Changed to match API docs
        if pcs_population_codes:
            params['populations'] = pcs_population_codes  # Changed to match API docs
        
        # Try cache first  
        url = f"{self.base_url}/search"  # Changed from /articles to /search
        cached_result = self.cache.get('GET', url, params)
        if cached_result is not None:
            return cached_result
        
        # Make API request
        url = f"{self.base_url}/search"
        response_data = self._make_request(url, params)
        
        if not response_data or 'error' in response_data:
            return []
        
        # Parse and format results
        results = []
        articles = response_data.get('data', []) if 'data' in response_data else response_data.get('results', [])
        
        for article in articles:
            formatted = {
                'source': 'candid_news',
                'data_id': article.get('id', ''),
                'title': article.get('title', ''),
                'link': article.get('url', article.get('link', '')),
                'publication_date': article.get('publication_date', article.get('published_date', '')),
                'rfp_mentioned': article.get('rfp_mentioned', False),
                'grant_mentioned': article.get('grant_mentioned', False),
                'staff_change_mentioned': article.get('staff_change_mentioned', False),
                'site_name': article.get('site_name', article.get('source_name', '')),
                'content': article.get('content', article.get('summary', '')),
                'locations_mentioned': article.get('locations_mentioned', []),
                'organizations_mentioned': article.get('organizations_mentioned', [])
            }
            results.append(formatted)
        
        # Cache results
        self.cache.set('GET', url, results, 600, params)
        return results


class GrantsClient:
    """Candid Grants API Client"""
    
    def __init__(self):
        self.base_url = "https://api.candid.org/grants/v1"
        # Confirmed Grants API key from Candid support
        self.api_key = os.environ.get('CANDID_GRANTS_KEYS', '9178555867b84c8fbe9a828a77eaf953')
        self.cache = SimpleCache()
    
    def _make_request(self, url: str, params: Optional[Dict] = None, method: str = 'GET') -> Optional[Dict]:
        """Make request to Candid Grants API"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            headers = {
                'Accept': 'application/json',
                'Subscription-Key': self.api_key
            }
            
            logger.debug(f"Making {method} request to: {url}")
            logger.debug(f"Parameters: {params}")
            
            if method == 'POST':
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, json=params, headers=headers, timeout=30)
            else:
                response = requests.get(url, params=params, headers=headers, timeout=30)
            
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # 404 means no results found for the search parameters - not an error
                # As per Candid docs: broaden search parameters if this occurs
                logger.info("404 - No results found for search parameters")
                return {"results": [], "count": 0, "message": "No results found - consider broadening search parameters"}
            elif response.status_code == 400:
                # 400 means bad request - try different format
                logger.warning(f"400 Bad request: {response.text}")
                return {"error": f"Bad request: {response.text}"}
            elif response.status_code in [401, 429]:
                logger.error(f"Authentication/rate limit error: {response.status_code}")
                return {"error": f"API authentication/rate limit error: {response.status_code}"}
            else:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except requests.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def transactions(self, query: Optional[str] = None, location: Optional[int] = None, page: int = 1) -> List[Dict]:
        """Search grant transactions using the official transactions endpoint
        
        Args:
            query: Keyword to search for
            location: Geoname ID for location (e.g., 5001836 for Michigan)
            page: Page number (1-100)
        """
        
        # Build parameters according to Candid API spec
        params = {}
        if query:
            params['query'] = query
        if location:
            params['location'] = location  # Geoname ID as integer
        if page:
            params['page'] = page  # Page number 1-100
        
        url = f"{self.base_url}/transactions"  # Correct endpoint
        
        # Check cache first
        cached_result = self.cache.get('GET', url, params)
        if cached_result is not None:
            return cached_result
        
        # Make API request
        response_data = self._make_request(url, params, 'GET')
        
        if not response_data or 'error' in response_data:
            return []
        
        # Parse transactions from the API response
        transactions = []
        
        # The transactions endpoint returns {"meta": {...}, "data": {"rows": [...]}}
        if isinstance(response_data, dict) and 'data' in response_data:
            data = response_data['data']
            if isinstance(data, dict) and 'rows' in data:
                grant_records = data['rows']
            else:
                grant_records = []
        else:
            grant_records = []
        
        # Parse each grant record - actual field names from API
        for grant in grant_records:
            if isinstance(grant, dict):
                transactions.append({
                    'funder_name': grant.get('funder_name', ''),
                    'recipient_name': grant.get('recip_name', ''),
                    'amount': grant.get('amount', 0),
                    'grant_date': grant.get('year_issued', ''),
                    'description': grant.get('description', ''),
                    'source': 'candid_api',
                    'funder_key': grant.get('funder_key', ''),
                    'recip_key': grant.get('recip_key', ''),
                    'funder_city': grant.get('funder_city', ''),
                    'funder_state': grant.get('funder_state', ''),
                    'recip_city': grant.get('recip_city', ''),
                    'recip_state': grant.get('recip_state', '')
                })
        
        # Cache and return results
        self.cache.set('GET', url, transactions, 600, params)
        return transactions
    
    def funders(self, query: str, page: int = 1, size: int = 25) -> List[Dict]:
        """Search grant funders"""
        
        params = {
            'search_terms': query,
            'page': page,
            'page_size': size
        }
        
        url = f"{self.base_url}/funders"
        
        # Check cache first
        cached_result = self.cache.get('GET', url, params)
        if cached_result is not None:
            return cached_result
        
        # Make API request
        response_data = self._make_request(url, params, 'GET')
        
        if response_data and 'error' in response_data and '400' in response_data['error']:
            # Try POST method as fallback
            response_data = self._make_request(url, params, 'POST')
        
        if not response_data or 'error' in response_data:
            return []
        
        # Extract and return data
        funders = response_data.get('data', []) if 'data' in response_data else response_data.get('results', [])
        self.cache.set('GET', url, funders, 600, params)
        return funders
    
    def _generate_sample_transactions(self, query: str) -> List[Dict]:
        """Generate realistic sample data when API unavailable"""
        import random
        from datetime import datetime, timedelta
        
        samples = []
        base_funders = {
            'education': ['Gates Foundation', 'Carnegie Foundation', 'Walton Family Foundation'],
            'youth': ['Annie E. Casey Foundation', 'W.K. Kellogg Foundation', 'Robert Wood Johnson'],
            'community': ['Ford Foundation', 'Kresge Foundation', 'MacArthur Foundation'],
            'health': ['Robert Wood Johnson', 'Commonwealth Fund', 'Kaiser Family Foundation'],
            'arts': ['Andrew W. Mellon Foundation', 'NEA', 'Knight Foundation']
        }
        
        funders = base_funders.get(query.lower(), ['Sample Foundation'])
        
        for i in range(min(10, random.randint(5, 15))):
            date = datetime.now() - timedelta(days=random.randint(1, 365))
            samples.append({
                'funder_name': random.choice(funders),
                'recipient_name': f'Sample {query.title()} Organization {i+1}',
                'amount': random.choice([25000, 50000, 75000, 100000, 150000, 250000, 500000]),
                'grant_date': date.strftime('%Y-%m-%d'),
                'description': f'Grant for {query} programs and initiatives',
                'source': 'candid_sample'
            })
        
        return samples
    
    def snapshot_for(self, topic: str, geo: str) -> Dict:
        """Get grant snapshot for topic and geography"""
        query = f"{topic} {geo}".strip()
        transactions = self.transactions(query=query)  # Use correct parameter name
        
        if not transactions:
            return {
                'award_count': 0,
                'median_award': None,
                'recent_funders': [],
                'query_used': query
            }
        
        # Extract numeric amounts
        amounts = []
        funders = set()
        
        for transaction in transactions:
            # Try different possible field names for amount
            amount = transaction.get('amount')
            if amount is None:
                amount = transaction.get('award_amount')
            if amount is None:
                amount = transaction.get('grant_amount')
            
            if amount and isinstance(amount, (int, float)):
                amounts.append(amount)
            
            # Extract funder names
            funder_name = transaction.get('funder_name')
            if funder_name is None:
                funder_name = transaction.get('grantmaker')
            if funder_name is None:
                funder_name = transaction.get('foundation_name')
            
            if funder_name:
                funders.add(funder_name)
        
        # Calculate statistics
        median_amount = statistics.median(amounts) if amounts else None
        
        return {
            'award_count': len(transactions),
            'median_award': median_amount,
            'recent_funders': list(funders)[:10],  # Top 10 funders
            'query_used': query
        }


class EssentialsClient:
    """Candid Essentials API Client"""
    
    def __init__(self):
        self.base_url = "https://api.candid.org/essentials/v3"  # Updated to v3
        # Updated Essentials API key from Candid support
        self.api_key = os.environ.get('CANDID_ESSENTIALS_KEY', '8b0f054101a24cd79a2f445632ec9ac2')
        self.cache = SimpleCache()
    
    def _make_request(self, url: str, params: Dict, method: str = 'POST') -> Optional[Dict]:
        """Make request to Candid Essentials API using POST method as required"""
        try:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Subscription-Key': self.api_key
            }
            
            # Essentials API requires POST method
            response = requests.post(url, json=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # 404 means no results found for the search parameters - not an error
                # As per Candid docs: broaden search parameters if this occurs
                return {"results": [], "count": 0, "message": "No results found - consider broadening search parameters"}
            elif response.status_code in [401, 429]:
                return {"error": f"API authentication/rate limit error: {response.status_code}"}
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except requests.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def search_org(self, search_terms: Optional[str] = None, from_offset: int = 0, 
                   size: int = 25) -> List[Dict]:
        """Search organizations in Candid Essentials using proper v3 format
        
        Args:
            search_terms: Any string to search (EIN, organization name, keywords)
            from_offset: Offset from first result (default 0)
            size: Maximum results to return (default 25, max 25)
        """
        
        # Build request body according to API spec
        request_body = {}
        
        if search_terms:
            request_body['search_terms'] = search_terms
        
        # Add pagination
        request_body['from'] = from_offset
        request_body['size'] = min(size, 25)  # Max 25 per API docs
        
        # Try cache first
        url = self.base_url
        cache_key = f"{search_terms}_{from_offset}_{size}"
        cached_result = self.cache.get('POST', url, {'key': cache_key})
        if cached_result is not None:
            return cached_result
        
        # Make API request
        response_data = self._make_request(url, request_body)
        
        if not response_data or 'error' in response_data:
            return []
        
        # Parse results - Essentials v3 returns {"hits": [...]}
        results = []
        if isinstance(response_data, dict) and 'hits' in response_data:
            orgs = response_data['hits']
        else:
            orgs = []
        
        for hit in orgs:
            # Each hit contains an 'organization' object
            org = hit.get('organization', {}) if isinstance(hit, dict) else {}
            formatted = {
                'source': 'candid_essentials',
                'ein': org.get('ein', ''),
                'name': org.get('organization_name', ''),
                'city': org.get('city', ''),
                'state': org.get('state', ''),
                'zip_code': org.get('zip_code', ''),
                'ntee_code': org.get('ntee_code', ''),
                'assets': org.get('assets'),
                'income': org.get('income'),
                'revenue': org.get('revenue'),
                'ruling_date': org.get('ruling_date', ''),
                'tax_period': org.get('tax_period', ''),
                'foundation_type': org.get('foundation_type', ''),
                'contact_info': {
                    'phone': org.get('phone', ''),
                    'url': org.get('url', ''),
                    'contact_name': org.get('contact_name', ''),
                    'title': org.get('title', '')
                }
            }
            results.append(formatted)
        
        # Cache results
        search_terms = request_body.get('search_terms', '') if 'request_body' in locals() else ''
        cache_key = f"{search_terms}_{request_body.get('from', 0)}_{request_body.get('size', 25)}" if 'request_body' in locals() else ""
        self.cache.set('POST', url, results, 600, {'key': cache_key})
        return results
    
    def get_profile(self, ein: str) -> Optional[Dict]:
        """Get detailed organization profile by EIN"""
        
        # Try cache first
        url = f"{self.base_url}/{ein}"
        cached_result = self.cache.get('GET', url, {})
        if cached_result is not None:
            return cached_result
        
        # Make API request
        response_data = self._make_request(url, {})
        
        if not response_data or 'error' in response_data:
            return None
        
        # Format profile data
        profile = {
            'source': 'candid_essentials',
            'ein': response_data.get('ein', ein),
            'name': response_data.get('name', ''),
            'aka': response_data.get('aka', ''),
            'address': response_data.get('address', {}),
            'contact': response_data.get('contact', {}),
            'year_formed': response_data.get('year_formed'),
            'irs_ruling_year': response_data.get('irs_ruling_year'),
            'fiscal_year_end': response_data.get('fiscal_year_end', ''),
            'ntee_codes': response_data.get('ntee_codes', []),
            'mission': response_data.get('mission', ''),
            'programs': response_data.get('programs', []),
            'financials': {
                'assets': response_data.get('assets'),
                'income': response_data.get('income'),
                'revenue': response_data.get('revenue'),
                'expenses': response_data.get('expenses'),
                'grants_paid': response_data.get('grants_paid')
            },
            'people': response_data.get('people', []),
            'bmf_status': response_data.get('bmf_status', ''),
            'pub78_status': response_data.get('pub78_status', ''),
            'foundation_type': response_data.get('foundation_type', '')
        }
        
        # Cache results
        self.cache.set('GET', url, profile, 3600, {})
        return profile


# Singleton instances
_news_client = None
_grants_client = None
_essentials_client = None

def get_news_client():
    """Get singleton news client"""
    global _news_client
    if _news_client is None:
        _news_client = NewsClient()
    return _news_client

def get_grants_client():
    """Get singleton grants client"""
    global _grants_client
    if _grants_client is None:
        _grants_client = GrantsClient()
    return _grants_client

def get_essentials_client():
    """Get singleton essentials client"""
    global _essentials_client
    if _essentials_client is None:
        _essentials_client = EssentialsClient()
    return _essentials_client

# Backward compatibility
def get_candid_client():
    """Backward compatibility - returns grants client"""
    return get_grants_client()