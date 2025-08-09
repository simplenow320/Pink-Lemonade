"""
Unified API & Data Integration Manager
Handles all external API calls and data source integrations
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
import time
import hashlib
from flask import current_app
from app.config.apiConfig import APIConfig, API_SOURCES

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self):
        self.calls = {}
    
    def check_rate_limit(self, source_name: str, max_calls: int, period_seconds: int) -> bool:
        """Check if we can make another API call"""
        now = time.time()
        if source_name not in self.calls:
            self.calls[source_name] = []
        
        # Clean old calls
        self.calls[source_name] = [
            call_time for call_time in self.calls[source_name] 
            if now - call_time < period_seconds
        ]
        
        if len(self.calls[source_name]) >= max_calls:
            return False
        
        self.calls[source_name].append(now)
        return True

class CacheManager:
    """Simple cache manager for API responses"""
    def __init__(self):
        self.cache = {}
    
    def get_cache_key(self, source: str, params: dict) -> str:
        """Generate cache key from source and params"""
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(f"{source}:{param_str}".encode()).hexdigest()
    
    def get(self, source: str, params: dict, max_age_minutes: int = 60) -> Optional[Any]:
        """Get cached data if available and not expired"""
        key = self.get_cache_key(source, params)
        if key in self.cache:
            cached_data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(minutes=max_age_minutes):
                logger.info(f"Cache hit for {source}")
                return cached_data
        return None
    
    def set(self, source: str, params: dict, data: Any):
        """Cache data with timestamp"""
        key = self.get_cache_key(source, params)
        self.cache[key] = (data, datetime.now())
        logger.info(f"Cached data for {source}")

class APIManager:
    """Central API Manager for all grant data sources"""
    
    def __init__(self):
        self.config = APIConfig()
        self.rate_limiter = RateLimiter()
        self.cache = CacheManager()
        self.sources = self._initialize_sources()
    
    def _initialize_sources(self) -> Dict:
        """Initialize all API sources from config"""
        sources = {}
        for source_id, source_config in API_SOURCES.items():
            if source_config.get('enabled', False):
                sources[source_id] = source_config
                logger.info(f"Initialized source: {source_id}")
        return sources
    
    def get_grants_from_source(self, source_name: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Fetch grants from a specific source
        Returns list of standardized grant objects
        """
        params = params or {}
        
        # Check if source is enabled
        if source_name not in self.sources:
            logger.warning(f"Source {source_name} not found or disabled")
            return []
        
        # Check cache first
        cached_data = self.cache.get(source_name, params)
        if cached_data:
            return cached_data
        
        # Check rate limit
        source_config = self.sources[source_name]
        rate_limit = source_config.get('rate_limit', {'calls': 10, 'period': 60})
        if not self.rate_limiter.check_rate_limit(
            source_name, 
            rate_limit['calls'], 
            rate_limit['period']
        ):
            logger.warning(f"Rate limit exceeded for {source_name}")
            return []  # Return empty when rate limited
        
        # Route to appropriate fetcher
        try:
            if source_name == 'grants_gov':
                grants = self._fetch_grants_gov(params)
            elif source_name == 'federal_register':
                grants = self._fetch_federal_register(params)
            elif source_name == 'govinfo':
                grants = self._fetch_govinfo(params)
            elif source_name == 'philanthropy_news':
                grants = self._fetch_philanthropy_news(params)
            elif source_name == 'foundation_directory':
                grants = self._fetch_foundation_directory(params)
            elif source_name == 'grantwatch':
                grants = self._fetch_grantwatch(params)
            elif source_name == 'michigan_portal':
                grants = self._fetch_michigan_portal(params)
            elif source_name == 'georgia_portal':
                grants = self._fetch_georgia_portal(params)
            else:
                logger.warning(f"Unknown source: {source_name}")
                grants = []  # No data for unknown sources
            
            # Cache successful response
            if grants:
                self.cache.set(source_name, params, grants)
            
            return grants
            
        except Exception as e:
            logger.error(f"Error fetching from {source_name}: {e}")
            return []  # Return empty on error, never fake data
    
    def get_enabled_sources(self) -> Dict[str, Dict]:
        """Get all enabled sources with their configurations"""
        return self.sources
    
    def search_grants(self, source_name: str, params: Optional[Dict] = None) -> List[Dict]:
        """Search grants from a specific source - alias for get_grants_from_source"""
        return self.get_grants_from_source(source_name, params)
    
    def _get_current_timestamp(self) -> str:
        """Get current ISO timestamp"""
        return datetime.now().isoformat()
    
    def search_opportunities(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Search for grant opportunities across all enabled sources
        """
        filters = filters or {}
        all_grants = []
        
        # Search each enabled source
        for source_name in self.sources:
            params = {
                'query': query,
                **filters
            }
            grants = self.get_grants_from_source(source_name, params)
            all_grants.extend(grants)
        
        # Deduplicate and sort by relevance
        seen = set()
        unique_grants = []
        for grant in all_grants:
            grant_id = f"{grant.get('title', '')}:{grant.get('funder', '')}"
            if grant_id not in seen:
                seen.add(grant_id)
                unique_grants.append(grant)
        
        return unique_grants
    
    def fetch_grant_details(self, grant_id: str, source: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch detailed information about a specific grant
        """
        if source and source in self.sources:
            params = {'grant_id': grant_id}
            grants = self.get_grants_from_source(source, params)
            if grants:
                return grants[0]
        
        # Try all sources if source not specified
        for source_name in self.sources:
            params = {'grant_id': grant_id}
            grants = self.get_grants_from_source(source_name, params)
            if grants:
                return grants[0]
        
        return None
    
    def get_watchlist_updates(self, watchlist_id: str, last_check: Optional[datetime] = None) -> List[Dict]:
        """
        Get new grant opportunities for a watchlist since last check
        """
        # This would integrate with the existing watchlist system
        # For now, return recent grants
        all_grants = []
        for source_name in self.sources:
            params = {
                'since': last_check.isoformat() if last_check else None,
                'watchlist_id': watchlist_id
            }
            grants = self.get_grants_from_source(source_name, params)
            all_grants.extend(grants)
        
        return all_grants
    
    # Source-specific fetchers
    def _fetch_grants_gov(self, params: Dict) -> List[Dict]:
        """
        Fetch grants from Grants.gov API
        Note: Grants.gov has a public API that doesn't require authentication
        """
        try:
            base_url = self.sources['grants_gov']['base_url']
            
            # Build query parameters
            query_params = {
                'keyword': params.get('query', ''),
                'oppStatus': 'open',
                'rows': params.get('limit', 25)
            }
            
            # Make request
            response = requests.get(
                f"{base_url}/search/v2/",
                params=query_params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                grants = []
                
                for opp in data.get('opportunities', []):
                    grant = self._standardize_grant({
                        'title': opp.get('title'),
                        'funder': opp.get('agency'),
                        'amount_min': opp.get('awardFloor'),
                        'amount_max': opp.get('awardCeiling'),
                        'deadline': opp.get('closeDate'),
                        'description': opp.get('description'),
                        'link': f"https://grants.gov/search-results-detail/{opp.get('id')}",
                        'source': 'Grants.gov',
                        'source_id': opp.get('id')
                    })
                    grants.append(grant)
                
                return grants
                
        except Exception as e:
            logger.error(f"Error fetching from Grants.gov: {e}")
        
        return []
    
    def _fetch_philanthropy_news(self, params: Dict) -> List[Dict]:
        """
        Fetch grants from Philanthropy News Digest RSS
        """
        try:
            # Note: feedparser dependency not available - using alternative approach
            base_url = self.sources['philanthropy_news']['base_url']
            
            # Simple RSS parsing without feedparser
            response = requests.get(base_url, timeout=10)
            if response.status_code == 200:
                # Basic RSS parsing - extract title and link from XML
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                grants = []
                items = root.findall('.//item')[:params.get('limit', 25)]
                
                for item in items:
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    pub_date = item.find('pubDate')
                    
                    grant = self._standardize_grant({
                        'title': title.text if title is not None else 'Grant Opportunity',
                        'description': description.text if description is not None else '',
                        'link': link.text if link is not None else '',
                        'deadline': pub_date.text if pub_date is not None else '',
                        'source': 'Philanthropy News Digest'
                    })
                    grants.append(grant)
                
                return grants
            else:
                logger.warning(f"Failed to fetch RSS feed: {response.status_code}")
                return []
            
        except Exception as e:
            logger.error(f"Error fetching from Philanthropy News: {e}")
        
        return []
    
    def _fetch_foundation_directory(self, params: Dict) -> List[Dict]:
        """
        Fetch from Foundation Directory Online (placeholder for paid API)
        """
        # This requires API credentials
        logger.warning("Foundation Directory API requires paid subscription")
        return []  # No data without API key
    
    def _fetch_grantwatch(self, params: Dict) -> List[Dict]:
        """
        Fetch from GrantWatch free listings
        """
        # GrantWatch requires subscription for API
        logger.warning("GrantWatch API requires paid subscription")
        return []  # No data without API key
    
    def _fetch_michigan_portal(self, params: Dict) -> List[Dict]:
        """
        Fetch from Michigan state portal
        """
        # Implementation would depend on available Michigan open data APIs
        logger.info("Michigan portal: No public API available yet")
        return []  # No data source configured
    
    def _fetch_georgia_portal(self, params: Dict) -> List[Dict]:
        """
        Fetch from Georgia state portal
        """
        # Implementation would depend on available Georgia open data APIs
        logger.info("Georgia portal: No public API available yet")
        return []  # No data source configured
    
    def _fetch_federal_register(self, params: Dict) -> List[Dict]:
        """
        Fetch grants from Federal Register API
        """
        try:
            base_url = self.sources['federal_register']['base_url']
            
            # Build query parameters for Federal Register
            # Note: Federal Register API has specific URL encoding requirements
            query_params = {
                'conditions[term]': params.get('query', 'grant'),
                'per_page': params.get('limit', 20),
                'order': 'newest'
            }
            
            response = requests.get(
                f"{base_url}/documents.json",
                params=query_params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                grants = []
                
                for doc in data.get('results', []):
                    grant = self._standardize_grant({
                        'title': doc.get('title'),
                        'description': doc.get('abstract'),
                        'link': doc.get('html_url'),
                        'deadline': doc.get('publication_date'),
                        'source': 'Federal Register',
                        'source_id': doc.get('document_number')
                    })
                    grants.append(grant)
                
                return grants
                
        except Exception as e:
            logger.error(f"Error fetching from Federal Register: {e}")
        
        return []
    
    def _fetch_govinfo(self, params: Dict) -> List[Dict]:
        """
        Fetch grants from GovInfo API
        """
        try:
            base_url = self.sources['govinfo']['base_url']
            
            # Build query parameters for GovInfo
            query_params = {
                'query': params.get('query', 'grant funding opportunity'),
                'collection': 'FR',  # Federal Register
                'format': 'json',
                'pageSize': params.get('limit', 25),
                'offsetMark': '*'
            }
            
            response = requests.get(
                f"{base_url}/search",
                params=query_params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                grants = []
                
                for item in data.get('packages', []):
                    grant = self._standardize_grant({
                        'title': item.get('title'),
                        'description': item.get('summary'),
                        'link': item.get('packageLink'),
                        'deadline': item.get('dateIssued'),
                        'source': 'GovInfo',
                        'source_id': item.get('packageId')
                    })
                    grants.append(grant)
                
                return grants
                
        except Exception as e:
            logger.error(f"Error fetching from GovInfo: {e}")
        
        return []
    
    def _standardize_grant(self, raw_grant: Dict) -> Dict:
        """
        Standardize grant data format across all sources
        """
        return {
            'id': raw_grant.get('source_id', self._generate_id(raw_grant)),
            'title': raw_grant.get('title', 'Untitled Grant'),
            'funder': raw_grant.get('funder', 'Unknown Funder'),
            'amount_min': raw_grant.get('amount_min'),
            'amount_max': raw_grant.get('amount_max'),
            'deadline': raw_grant.get('deadline'),
            'description': raw_grant.get('description', ''),
            'eligibility': raw_grant.get('eligibility', ''),
            'link': raw_grant.get('link', ''),
            'source': raw_grant.get('source', 'Unknown'),
            'source_url': raw_grant.get('source_url', ''),
            'tags': raw_grant.get('tags', []),
            'discovered_at': datetime.now().isoformat(),
            'status': 'discovered'
        }
    
    def _generate_id(self, grant: Dict) -> str:
        """Generate unique ID for grant"""
        unique_str = f"{grant.get('title', '')}:{grant.get('funder', '')}:{grant.get('source', '')}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:12]
    
    def _handle_no_data(self, source_name: str) -> List[Dict]:
        """
        Handle cases where no real data is available
        """
        logger.warning(f"No real data available from {source_name}. API keys or configuration may be needed.")
        return []  # Return empty list - never fake data

# Singleton instance
api_manager = APIManager()

# Convenience functions for direct import
def get_grants_from_source(source_name: str, params: Optional[Dict] = None) -> List[Dict]:
    """Fetch grants from a specific source"""
    return api_manager.get_grants_from_source(source_name, params)

def search_opportunities(query: str, filters: Optional[Dict] = None) -> List[Dict]:
    """Search for opportunities across all sources"""
    return api_manager.search_opportunities(query, filters)

def fetch_grant_details(grant_id: str, source: Optional[str] = None) -> Optional[Dict]:
    """Fetch detailed grant information"""
    return api_manager.fetch_grant_details(grant_id, source)

def get_watchlist_updates(watchlist_id: str, last_check: Optional[datetime] = None) -> List[Dict]:
    """Get watchlist updates"""
    return api_manager.get_watchlist_updates(watchlist_id, last_check)