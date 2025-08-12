"""
API Configuration for Grant Data Sources
Central configuration for all external APIs and data sources
"""

import os
from typing import Dict, Any

# API Source Configurations
API_SOURCES = {
    'grants_gov': {
        'name': 'Grants.gov',
        'enabled': True,
        'base_url': 'https://www.grants.gov/grantsws/rest',
        'api_key': None,  # Public API, no key required
        'rate_limit': {
            'calls': 100,
            'period': 3600  # per hour
        },
        'cache_ttl': 60,  # minutes
        'supports': ['search', 'details'],
        'description': 'Federal grant opportunities from US government',
        'endpoints': {
            'search': '/opportunities/search',
            'details': '/opportunity/details/{id}'
        },
        'params': {
            'status': 'posted',
            'sortBy': 'closeDate',
            'oppStatuses': 'posted',
            'rows': 25
        }
    },
    
    'philanthropy_news': {
        'name': 'Philanthropy News Digest',
        'enabled': False,  # Returns 403 Forbidden - NOT WORKING
        'base_url': 'https://philanthropynewsdigest.org/rfps/rss',
        'api_key': None,
        'rate_limit': {
            'calls': 50,
            'period': 3600
        },
        'cache_ttl': 120,
        'supports': ['search'],
        'description': 'Foundation grant opportunities and RFPs'
    },
    
    'foundation_directory': {
        'name': 'Foundation Directory Online',
        'enabled': False,  # Requires paid subscription
        'base_url': 'https://api.foundationdirectory.org/v1',
        'api_key': os.environ.get('FDO_API_KEY'),
        'rate_limit': {
            'calls': 1000,
            'period': 86400  # per day
        },
        'cache_ttl': 240,
        'supports': ['search', 'details', 'funder_profiles'],
        'description': 'Comprehensive foundation data (requires subscription)'
    },
    
    'grantwatch': {
        'name': 'GrantWatch',
        'enabled': False,  # Placeholder for future integration
        'base_url': 'https://www.grantwatch.com/api',
        'api_key': os.environ.get('GRANTWATCH_API_KEY'),
        'rate_limit': {
            'calls': 100,
            'period': 3600
        },
        'cache_ttl': 60,
        'supports': ['search', 'details'],
        'description': 'Diverse grant opportunities across sectors'
    },
    
    'candid': {
        'name': 'Candid (formerly Foundation Center)',
        'enabled': False,  # Placeholder for paid API
        'base_url': 'https://api.candid.org/v1',
        'api_key': os.environ.get('CANDID_API_KEY'),
        'rate_limit': {
            'calls': 5000,
            'period': 86400
        },
        'cache_ttl': 1440,  # 24 hours
        'supports': ['search', 'details', 'funder_profiles', 'analytics'],
        'description': 'Premium foundation and nonprofit data'
    },
    
    'michigan_portal': {
        'name': 'Michigan Open Data Portal',
        'enabled': False,  # No implementation - returns empty
        'base_url': 'https://data.michigan.gov/api',
        'api_key': None,
        'rate_limit': {
            'calls': 100,
            'period': 3600
        },
        'cache_ttl': 240,
        'supports': ['search'],
        'description': 'Michigan state and local grants'
    },
    
    'georgia_portal': {
        'name': 'Georgia Grants Portal',
        'enabled': False,  # No implementation - returns empty
        'base_url': 'https://georgia.grantplatform.com/api',
        'api_key': None,
        'rate_limit': {
            'calls': 50,
            'period': 3600
        },
        'cache_ttl': 240,
        'supports': ['search'],
        'description': 'Georgia state funding opportunities'
    },
    
    'north_carolina_portal': {
        'name': 'North Carolina Grants',
        'enabled': False,
        'base_url': 'https://ncgrants.nc.gov/api',
        'api_key': None,
        'rate_limit': {
            'calls': 50,
            'period': 3600
        },
        'cache_ttl': 240,
        'supports': ['search'],
        'description': 'North Carolina state grants'
    },
    
    'south_carolina_portal': {
        'name': 'South Carolina Grants',
        'enabled': False,
        'base_url': 'https://admin.sc.gov/grants/api',
        'api_key': None,
        'rate_limit': {
            'calls': 50,
            'period': 3600
        },
        'cache_ttl': 240,
        'supports': ['search'],
        'description': 'South Carolina state grants'
    },
    
    'federal_register': {
        'name': 'Federal Register',
        'enabled': True,
        'base_url': 'https://www.federalregister.gov/api/v1',
        'api_key': None,  # Public API
        'rate_limit': {
            'calls': 1000,
            'period': 3600
        },
        'cache_ttl': 120,
        'supports': ['search'],
        'description': 'Federal funding notices and NOFOs',
        'endpoints': {
            'search': '/documents.json'
        },
        'params': {
            'fields[]': 'title,html_url,publication_date,abstract',
            'per_page': 20,
            'order': 'newest'
        }
    },
    
    'govinfo': {
        'name': 'GovInfo API',
        'enabled': True,
        'base_url': 'https://api.govinfo.gov',
        'api_key': None,  # Public API
        'rate_limit': {
            'calls': 1000,
            'period': 3600
        },
        'cache_ttl': 120,
        'supports': ['search'],
        'description': 'Government information and documents',
        'endpoints': {
            'search': '/search'
        },
        'params': {
            'collection': 'FR',  # Federal Register
            'format': 'json',
            'pageSize': 25,
            'offsetMark': '*'
        }
    }
}

# Search filters configuration
SEARCH_FILTERS = {
    'categories': [
        'Arts & Culture',
        'Community Development',
        'Education',
        'Environment',
        'Faith-Based',
        'Health & Human Services',
        'Technology & Innovation',
        'Youth Programs'
    ],
    'funding_types': [
        'Operating Support',
        'Project/Program',
        'Capital',
        'Capacity Building',
        'General Support',
        'Research'
    ],
    'geographic_focus': [
        'National',
        'Regional',
        'State',
        'Local/City',
        'International'
    ],
    'organization_types': [
        '501(c)(3)',
        'Faith-Based Organization',
        'Educational Institution',
        'Government Agency',
        'Individual',
        'Small Business'
    ]
}

# Data standardization mappings
FIELD_MAPPINGS = {
    'grants_gov': {
        'title': 'opportunityTitle',
        'funder': 'agencyName',
        'amount_min': 'awardFloor',
        'amount_max': 'awardCeiling',
        'deadline': 'closeDate',
        'description': 'description',
        'eligibility': 'eligibilityCategory'
    },
    'default': {
        'title': 'title',
        'funder': 'funder',
        'amount_min': 'amount_min',
        'amount_max': 'amount_max',
        'deadline': 'deadline',
        'description': 'description',
        'eligibility': 'eligibility'
    }
}

class APIConfig:
    """API Configuration Manager"""
    
    def __init__(self):
        self.sources = API_SOURCES
        self.filters = SEARCH_FILTERS
        self.field_mappings = FIELD_MAPPINGS
        self._load_environment_keys()
    
    def _load_environment_keys(self):
        """Load API keys from environment variables"""
        for source_id, config in self.sources.items():
            env_key = f"{source_id.upper()}_API_KEY"
            if os.environ.get(env_key):
                config['api_key'] = os.environ.get(env_key)
    
    def get_source_config(self, source_id: str) -> Dict[str, Any]:
        """Get configuration for a specific source"""
        return self.sources.get(source_id, {})
    
    def get_enabled_sources(self) -> Dict[str, Dict]:
        """Get all enabled sources"""
        return {
            source_id: config 
            for source_id, config in self.sources.items() 
            if config.get('enabled', False)
        }
    
    def is_source_enabled(self, source_id: str) -> bool:
        """Check if a source is enabled"""
        return self.sources.get(source_id, {}).get('enabled', False)
    
    def get_field_mapping(self, source_id: str) -> Dict[str, str]:
        """Get field mapping for a source"""
        return self.field_mappings.get(source_id, self.field_mappings['default'])
    
    def update_source_status(self, source_id: str, enabled: bool):
        """Enable or disable a source"""
        if source_id in self.sources:
            self.sources[source_id]['enabled'] = enabled
    
    def add_api_key(self, source_id: str, api_key: str):
        """Add or update API key for a source"""
        if source_id in self.sources:
            self.sources[source_id]['api_key'] = api_key
            # Also enable the source if it was disabled
            if api_key:
                self.sources[source_id]['enabled'] = True