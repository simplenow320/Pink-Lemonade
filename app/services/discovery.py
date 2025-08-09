"""
Discovery Connectors Service
Pulls grant opportunities from multiple sources and manages watchlists
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class DiscoveryConnector:
    """Base class for all discovery connectors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.id = config.get('id')
        self.name = config.get('name')
        self.type = config.get('type')  # 'api' or 'scrape'
        self.endpoint = config.get('endpoint')
        self.auth = config.get('auth', {})
        self.params = config.get('params', {})
        self.enabled = config.get('enabled', True)
        self.source_url = config.get('source_url', '')
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch grants from this connector"""
        raise NotImplementedError
    
    def parse(self, data: Any) -> List[Dict[str, Any]]:
        """Parse raw data into standardized GrantRecord format"""
        raise NotImplementedError
    
    def generate_grant_id(self, grant: Dict[str, Any]) -> str:
        """Generate unique ID for deduplication"""
        unique_string = f"{grant.get('title', '')}-{grant.get('funder', '')}-{grant.get('deadline', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()


class GrantsGovConnector(DiscoveryConnector):
    """Connector for Grants.gov API"""
    
    def fetch(self) -> List[Dict[str, Any]]:
        try:
            # Mock implementation - replace with actual API call when keys available
            if self.endpoint == 'MOCK':
                return self._fetch_mock()
            
            headers = self.auth if self.auth else {}
            params = {
                'eligibility': 'nonprofits',
                'status': 'open',
                **self.params
            }
            
            response = requests.get(
                self.endpoint,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return self.parse(response.json())
            
        except Exception as e:
            logger.error(f"Error fetching from Grants.gov: {e}")
            return self._fetch_mock()
    
    def _fetch_mock(self) -> List[Dict[str, Any]]:
        """Return mock data when API unavailable"""
        mock_grants = [
            {
                'title': 'Community Development Block Grant',
                'funder': 'Department of Housing and Urban Development',
                'link': 'https://grants.gov/opportunity/12345',
                'amountMin': 50000,
                'amountMax': 500000,
                'deadline': (datetime.now() + timedelta(days=45)).isoformat(),
                'geography': 'National',
                'eligibility': '501(c)(3) nonprofits engaged in community development',
                'tags': ['Community Development', 'Housing', 'Federal'],
                'sourceName': 'Grants.gov',
                'sourceURL': 'https://grants.gov'
            },
            {
                'title': 'Youth Mentoring Program Grant',
                'funder': 'Department of Justice',
                'link': 'https://grants.gov/opportunity/67890',
                'amountMin': 25000,
                'amountMax': 150000,
                'deadline': (datetime.now() + timedelta(days=60)).isoformat(),
                'geography': 'National',
                'eligibility': 'Organizations providing mentoring services to at-risk youth',
                'tags': ['Youth Development', 'Mentoring', 'Federal'],
                'sourceName': 'Grants.gov',
                'sourceURL': 'https://grants.gov'
            }
        ]
        return mock_grants
    
    def parse(self, data: Any) -> List[Dict[str, Any]]:
        """Parse Grants.gov API response"""
        grants = []
        # Implement actual parsing logic based on API response structure
        return grants


class FederalRegisterConnector(DiscoveryConnector):
    """Connector for Federal Register API"""
    
    def fetch(self) -> List[Dict[str, Any]]:
        try:
            if self.endpoint == 'MOCK':
                return self._fetch_mock()
            
            params = {
                'conditions[term]': 'grant funding nonprofit',
                'conditions[type]': 'NOTICE',
                'per_page': 20,
                **self.params
            }
            
            response = requests.get(
                'https://www.federalregister.gov/api/v1/documents',
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return self.parse(response.json())
            
        except Exception as e:
            logger.error(f"Error fetching from Federal Register: {e}")
            return self._fetch_mock()
    
    def _fetch_mock(self) -> List[Dict[str, Any]]:
        """Return mock data when API unavailable"""
        mock_grants = [
            {
                'title': 'Notice of Funding Opportunity: Rural Health Network Development',
                'funder': 'Health Resources and Services Administration',
                'link': 'https://federalregister.gov/documents/2025/01/rural-health',
                'amountMin': 100000,
                'amountMax': 300000,
                'deadline': (datetime.now() + timedelta(days=75)).isoformat(),
                'geography': 'Rural Areas',
                'eligibility': 'Rural nonprofit health networks',
                'tags': ['Health', 'Rural Development', 'Federal'],
                'sourceName': 'Federal Register',
                'sourceURL': 'https://federalregister.gov'
            }
        ]
        return mock_grants
    
    def parse(self, data: Any) -> List[Dict[str, Any]]:
        """Parse Federal Register API response"""
        grants = []
        if 'results' in data:
            for doc in data['results']:
                # Extract grant information from document
                grant = {
                    'title': doc.get('title', ''),
                    'funder': doc.get('agencies', [{}])[0].get('name', '') if doc.get('agencies') else '',
                    'link': doc.get('html_url', ''),
                    'deadline': doc.get('comments_close_on', ''),
                    'geography': 'National',
                    'eligibility': doc.get('abstract', ''),
                    'tags': ['Federal', 'Notice'],
                    'sourceName': 'Federal Register',
                    'sourceURL': 'https://federalregister.gov'
                }
                grants.append(grant)
        return grants


class PhilanthropyNewsConnector(DiscoveryConnector):
    """Connector for Philanthropy News Digest RFPs"""
    
    def fetch(self) -> List[Dict[str, Any]]:
        try:
            if self.endpoint == 'MOCK':
                return self._fetch_mock()
            
            # Respect robots.txt and scrape responsibly
            response = requests.get(
                self.endpoint,
                headers={'User-Agent': 'GrantFlow Bot (respect robots.txt)'},
                timeout=30
            )
            response.raise_for_status()
            return self.parse(response.text)
            
        except Exception as e:
            logger.error(f"Error fetching from Philanthropy News: {e}")
            return self._fetch_mock()
    
    def _fetch_mock(self) -> List[Dict[str, Any]]:
        """Return mock data when scraping unavailable"""
        mock_grants = [
            {
                'title': 'Arts and Culture Innovation Grant',
                'funder': 'National Arts Foundation',
                'link': 'https://philanthropynewsdigest.org/rfps/arts-innovation',
                'amountMin': 10000,
                'amountMax': 50000,
                'deadline': (datetime.now() + timedelta(days=30)).isoformat(),
                'geography': 'National',
                'eligibility': 'Arts organizations with innovative programming',
                'tags': ['Arts', 'Culture', 'Innovation'],
                'sourceName': 'Philanthropy News Digest',
                'sourceURL': 'https://philanthropynewsdigest.org'
            }
        ]
        return mock_grants
    
    def parse(self, html: str) -> List[Dict[str, Any]]:
        """Parse HTML from Philanthropy News Digest"""
        grants = []
        # Implement actual HTML parsing with BeautifulSoup
        # This is a placeholder implementation
        return grants


class CityFoundationConnector(DiscoveryConnector):
    """Connector for city/regional foundation websites"""
    
    def fetch(self) -> List[Dict[str, Any]]:
        try:
            if self.endpoint == 'MOCK' or not self.endpoint:
                return self._fetch_mock()
            
            response = requests.get(
                self.endpoint,
                headers={'User-Agent': 'GrantFlow Bot'},
                timeout=30
            )
            response.raise_for_status()
            return self.parse(response.text)
            
        except Exception as e:
            logger.error(f"Error fetching from {self.name}: {e}")
            return self._fetch_mock()
    
    def _fetch_mock(self) -> List[Dict[str, Any]]:
        """Return mock data for city foundations"""
        city = self.params.get('city', 'Grand Rapids')
        mock_grants = [
            {
                'title': f'{city} Community Impact Grant',
                'funder': f'{city} Community Foundation',
                'link': f'https://{city.lower().replace(" ", "")}-foundation.org/grants',
                'amountMin': 5000,
                'amountMax': 25000,
                'deadline': (datetime.now() + timedelta(days=45)).isoformat(),
                'geography': city,
                'eligibility': f'Local nonprofits serving {city} residents',
                'tags': ['Local', 'Community Development', city],
                'sourceName': f'{city} Community Foundation',
                'sourceURL': f'https://{city.lower().replace(" ", "")}-foundation.org'
            }
        ]
        return mock_grants
    
    def parse(self, html: str) -> List[Dict[str, Any]]:
        """Parse HTML from foundation website"""
        grants = []
        # Implement actual parsing logic based on site structure
        return grants


class DiscoveryService:
    """Main service for managing discovery connectors and watchlists"""
    
    def __init__(self):
        self.connectors = self._initialize_connectors()
    
    def _initialize_connectors(self) -> Dict[str, DiscoveryConnector]:
        """Initialize all available connectors"""
        connectors = {}
        
        # Grants.gov connector
        connectors['grants_gov'] = GrantsGovConnector({
            'id': 'grants_gov',
            'name': 'Grants.gov',
            'type': 'api',
            'endpoint': 'MOCK',  # Replace with actual endpoint when API key available
            'auth': {},
            'params': {},
            'source_url': 'https://grants.gov'
        })
        
        # Federal Register connector
        connectors['federal_register'] = FederalRegisterConnector({
            'id': 'federal_register',
            'name': 'Federal Register',
            'type': 'api',
            'endpoint': 'https://www.federalregister.gov/api/v1/documents',
            'params': {},
            'source_url': 'https://federalregister.gov'
        })
        
        # Philanthropy News Digest connector
        connectors['philanthropy_news'] = PhilanthropyNewsConnector({
            'id': 'philanthropy_news',
            'name': 'Philanthropy News Digest',
            'type': 'scrape',
            'endpoint': 'MOCK',  # Replace with actual URL
            'params': {},
            'source_url': 'https://philanthropynewsdigest.org'
        })
        
        # City foundation connectors (Grand Rapids examples)
        grand_rapids_foundations = [
            'Grand Rapids Community Foundation',
            'Steelcase Foundation',
            'Frey Foundation',
            'Wege Foundation',
            'DeVos Family Foundation'
        ]
        
        for idx, foundation in enumerate(grand_rapids_foundations):
            connector_id = f'gr_foundation_{idx + 1}'
            connectors[connector_id] = CityFoundationConnector({
                'id': connector_id,
                'name': foundation,
                'type': 'scrape',
                'endpoint': 'MOCK',  # Replace with actual foundation URL
                'params': {'city': 'Grand Rapids'},
                'source_url': f'https://{foundation.lower().replace(" ", "-")}.org'
            })
        
        return connectors
    
    def run_all_connectors(self) -> List[Dict[str, Any]]:
        """Run all enabled connectors and return aggregated results"""
        all_grants = []
        
        for connector_id, connector in self.connectors.items():
            if connector.enabled:
                try:
                    logger.info(f"Running connector: {connector.name}")
                    grants = connector.fetch()
                    
                    # Add connector metadata to each grant
                    for grant in grants:
                        grant['connectorId'] = connector_id
                        grant['discoveredAt'] = datetime.now().isoformat()
                        grant['id'] = connector.generate_grant_id(grant)
                    
                    all_grants.extend(grants)
                    logger.info(f"Fetched {len(grants)} grants from {connector.name}")
                    
                except Exception as e:
                    logger.error(f"Error running connector {connector.name}: {e}")
        
        return all_grants
    
    def run_connector(self, connector_id: str) -> List[Dict[str, Any]]:
        """Run a specific connector"""
        if connector_id in self.connectors:
            connector = self.connectors[connector_id]
            grants = connector.fetch()
            
            # Add metadata
            for grant in grants:
                grant['connectorId'] = connector_id
                grant['discoveredAt'] = datetime.now().isoformat()
                grant['id'] = connector.generate_grant_id(grant)
            
            return grants
        else:
            raise ValueError(f"Connector {connector_id} not found")
    
    def run_watchlist_connectors(self, source_ids: List[str]) -> List[Dict[str, Any]]:
        """Run specific connectors for a watchlist"""
        all_grants = []
        
        for source_id in source_ids:
            if source_id in self.connectors:
                try:
                    grants = self.run_connector(source_id)
                    all_grants.extend(grants)
                except Exception as e:
                    logger.error(f"Error running watchlist connector {source_id}: {e}")
        
        return all_grants
    
    def deduplicate_grants(self, new_grants: List[Dict[str, Any]], 
                          existing_grants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates based on title, funder, and deadline"""
        existing_ids = set()
        
        for grant in existing_grants:
            unique_string = f"{grant.get('title', '')}-{grant.get('funder', '')}-{grant.get('deadline', '')}"
            existing_ids.add(hashlib.md5(unique_string.encode()).hexdigest())
        
        unique_grants = []
        for grant in new_grants:
            if grant['id'] not in existing_ids:
                unique_grants.append(grant)
        
        return unique_grants


# Initialize the discovery service
discovery_service = DiscoveryService()