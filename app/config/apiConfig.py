"""
API Configuration for Grant Data Sources
Central configuration for all external APIs and data sources
"""

import os
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# API Source Configurations
API_SOURCES = {
    'grants_gov': {
        'name': 'Grants.gov',
        'enabled': True,
        'base_url': 'https://www.grants.gov/grantsws/rest',
        'api_key': None,  # Public API, no key required
        'credential_required': False,
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
        'credential_required': False,
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
        'credential_required': True,
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
        'credential_required': True,
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
        'credential_required': True,
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
        'credential_required': False,
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
        'credential_required': False,
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
        'credential_required': False,
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
        'credential_required': False,
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
        'credential_required': False,
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
        'api_key_env': 'GOVINFO_API_KEY',
        'api_key': None,  # Public API, but supports optional API key
        'credential_required': False,  # Optional API key for enhanced access
        'credential_fallbacks': ['GOVINFO_KEY'],
        'auth_type': 'api_key',
        'auth_header': 'X-API-Key',
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
    },
    
    # New API Sources
    'sam_gov_opportunities': {
        'name': 'SAM.gov Get Opportunities API',
        'enabled': False,  # Requires API key
        'base_url': 'https://api.sam.gov/opportunities/v2',
        'api_key_env': 'SAM_GOV_API_KEY',
        'api_key': None,
        'auth_type': 'api_key',
        'auth_header': 'X-Api-Key',
        'credential_required': True,
        'credential_fallbacks': ['SAM_API_KEY', 'SAMGOV_KEY'],
        'rate_limit': {
            'calls': 1000,
            'period': 3600  # per hour
        },
        'cache_ttl': 30,  # minutes
        'supports': ['search', 'details'],
        'description': 'Federal contract opportunities from SAM.gov',
        'endpoints': {
            'search': '/search',
            'details': '/opportunities/{id}'
        },
        'params': {
            'limit': 100,
            'api_version': 'v2',
            'postedFrom': None,  # YYYY-MM-DD format
            'postedTo': None,
            'type': 'o',  # opportunities
            'ptype': 'k'  # procurement type
        },
        'error_handling': {
            'retry_codes': [429, 502, 503, 504],
            'max_retries': 3,
            'backoff_factor': 2
        }
    },
    
    'sam_gov_entity': {
        'name': 'SAM.gov Entity Management API',
        'enabled': False,  # Requires API key
        'base_url': 'https://api.sam.gov/entity-information/v3',
        'api_key_env': 'SAM_GOV_API_KEY',
        'api_key': None,
        'auth_type': 'api_key',
        'auth_header': 'X-Api-Key',
        'credential_required': True,
        'credential_fallbacks': ['SAM_API_KEY', 'SAMGOV_KEY'],
        'rate_limit': {
            'calls': 1000,
            'period': 3600
        },
        'cache_ttl': 240,  # 4 hours - entity data changes less frequently
        'supports': ['search', 'details', 'entity_profiles'],
        'description': 'Entity registration data from SAM.gov',
        'endpoints': {
            'search': '/entities',
            'details': '/entities/{id}'
        },
        'params': {
            'limit': 100,
            'api_version': 'v3',
            'includeSections': 'entityRegistration,coreData',
            'format': 'json'
        },
        'error_handling': {
            'retry_codes': [429, 502, 503, 504],
            'max_retries': 3,
            'backoff_factor': 2
        }
    },
    
    'michigan_socrata': {
        'name': 'Michigan.gov Socrata API',
        'enabled': False,  # Depends on available datasets
        'base_url': 'https://data.michigan.gov/api',
        'api_key_env': 'MICHIGAN_SOCRATA_API_KEY',
        'api_key': None,
        'auth_type': 'app_token',  # Socrata uses app_token
        'auth_header': 'X-App-Token',
        'credential_required': False,  # Public API but rate limited without token
        'credential_fallbacks': ['SOCRATA_APP_TOKEN', 'MICHIGAN_API_KEY'],
        'rate_limit': {
            'calls': 1000,  # With app token
            'period': 3600,
            'unauthenticated_calls': 100,  # Without app token
            'unauthenticated_period': 3600
        },
        'cache_ttl': 60,
        'supports': ['search', 'datasets'],
        'description': 'Michigan state open data and grant information',
        'endpoints': {
            'search': '/views/{dataset_id}.json',
            'datasets': '/views.json'
        },
        'params': {
            '$limit': 100,
            '$offset': 0,
            '$order': ':updated_at DESC',
            '$query': None  # SoQL query
        },
        'datasets': {
            'grants': os.environ.get('MICHIGAN_GRANTS_DATASET_ID', 'michigan-grants-dataset-id'),
            'funding': os.environ.get('MICHIGAN_FUNDING_DATASET_ID', 'michigan-funding-dataset-id'),
            'contracts': os.environ.get('MICHIGAN_CONTRACTS_DATASET_ID', 'michigan-contracts-dataset-id')
        },
        'error_handling': {
            'retry_codes': [429, 502, 503, 504],
            'max_retries': 2,
            'backoff_factor': 1.5
        }
    },
    
    'zyte_api': {
        'name': 'Zyte API (Web Scraping)',
        'enabled': False,  # Requires paid subscription
        'base_url': 'https://api.zyte.com/v1',
        'api_key_env': 'ZYTE_API_KEY',
        'api_key': None,
        'auth_type': 'basic_auth',  # Zyte uses HTTP Basic Auth
        'auth_header': 'Authorization',
        'credential_required': True,
        'credential_fallbacks': ['SCRAPINGHUB_API_KEY', 'ZYTE_KEY'],
        'rate_limit': {
            'calls': 100,  # Conservative limit for scraping
            'period': 3600,
            'concurrent_requests': 5
        },
        'cache_ttl': 1440,  # 24 hours for scraped content
        'supports': ['scrape', 'extract'],
        'description': 'Professional web scraping service for grant websites',
        'endpoints': {
            'extract': '/extract',
            'browser': '/browser'
        },
        'params': {
            'browserHtml': True,
            'screenshot': False,
            'actions': None,  # List of actions to perform
            'geolocation': 'US'
        },
        'scraping_targets': {
            'foundation_sites': [
                'foundationcenter.org',
                'guidestar.org',
                'philanthropy.com'
            ],
            'government_portals': [
                'grants.gov',
                'usaspending.gov'
            ]
        },
        'error_handling': {
            'retry_codes': [429, 502, 503, 504, 520, 521, 522, 524],
            'max_retries': 2,
            'backoff_factor': 3
        }
    },
    
    # Department-specific scraping sources
    'hhs_grants': {
        'name': 'HHS Grants Scraper',
        'enabled': True,  # Public data source
        'base_url': 'https://www.hhs.gov/grants',
        'api_key': None,
        'auth_type': None,
        'credential_required': False,
        'rate_limit': {
            'calls': 50,
            'period': 3600
        },
        'cache_ttl': 240,  # 4 hours
        'supports': ['scrape', 'rss'],
        'description': 'Health and Human Services grant opportunities',
        'endpoints': {
            'rss': '/grants/rss.xml',
            'search': '/grants/search'
        },
        'scraping_config': {
            'user_agent': 'Mozilla/5.0 (compatible; PinkLemonade/1.0)',
            'timeout': 30,
            'follow_redirects': True,
            'max_pages': 10
        }
    },
    
    'ed_grants': {
        'name': 'Department of Education Grants',
        'enabled': True,
        'base_url': 'https://www.ed.gov/grants',
        'api_key': None,
        'auth_type': None,
        'credential_required': False,
        'rate_limit': {
            'calls': 50,
            'period': 3600
        },
        'cache_ttl': 240,
        'supports': ['scrape', 'rss'],
        'description': 'Department of Education funding opportunities',
        'endpoints': {
            'rss': '/news/rss.xml',
            'search': '/grants'
        },
        'scraping_config': {
            'user_agent': 'Mozilla/5.0 (compatible; PinkLemonade/1.0)',
            'timeout': 30,
            'follow_redirects': True,
            'max_pages': 5
        }
    },
    
    'nsf_grants': {
        'name': 'National Science Foundation',
        'enabled': True,
        'base_url': 'https://www.nsf.gov/funding',
        'api_key': None,
        'auth_type': None,
        'credential_required': False,
        'rate_limit': {
            'calls': 100,
            'period': 3600
        },
        'cache_ttl': 360,  # 6 hours
        'supports': ['scrape', 'rss'],
        'description': 'National Science Foundation research funding',
        'endpoints': {
            'rss': '/news/news_rss.xml',
            'search': '/funding/search'
        },
        'scraping_config': {
            'user_agent': 'Mozilla/5.0 (compatible; PinkLemonade/1.0)',
            'timeout': 30,
            'follow_redirects': True,
            'max_pages': 8
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

# Enhanced data standardization mappings for new sources
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
    'sam_gov_opportunities': {
        'title': 'title',
        'funder': 'fullParentPathName',
        'amount_min': 'awardFloor',
        'amount_max': 'awardCeiling',
        'deadline': 'responseDeadLine',
        'description': 'description',
        'eligibility': 'additionalInfoOnEligibility',
        'opportunity_id': 'opportunityId',
        'notice_type': 'type'
    },
    'sam_gov_entity': {
        'entity_name': 'legalBusinessName',
        'duns': 'dunsNumber',
        'uei': 'ueiSAM',
        'cage_code': 'cageCode',
        'address': 'physicalAddress',
        'registration_date': 'registrationDate',
        'expiration_date': 'expirationDate'
    },
    'michigan_socrata': {
        'title': 'title',
        'description': 'description',
        'amount': 'amount',
        'deadline': 'deadline',
        'category': 'category',
        'department': 'department'
    },
    'zyte_api': {
        'extracted_text': 'html',
        'title': 'title',
        'links': 'links',
        'metadata': 'metadata'
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
    """Enhanced API Configuration Manager with Flexible Credential Management"""
    
    def __init__(self):
        self.sources = API_SOURCES
        self.filters = SEARCH_FILTERS
        self.field_mappings = FIELD_MAPPINGS
        self._load_environment_keys()
        self._auto_enable_sources()
    
    def _load_environment_keys(self):
        """Load API keys from environment variables with fallback support"""
        for source_id, config in self.sources.items():
            # Try primary environment variable
            primary_env = config.get('api_key_env', f"{source_id.upper()}_API_KEY")
            api_key = os.environ.get(primary_env)
            
            # Try fallback environment variables if primary not found
            if not api_key and 'credential_fallbacks' in config:
                for fallback_env in config['credential_fallbacks']:
                    api_key = os.environ.get(fallback_env)
                    if api_key:
                        logger.info(f"Loaded {source_id} credentials from fallback: {fallback_env}")
                        break
            
            # Set the API key if found
            if api_key:
                config['api_key'] = api_key
                logger.info(f"Loaded credentials for {source_id}")
            elif config.get('credential_required', False):
                logger.warning(f"Missing required credentials for {source_id}. Source will be disabled.")
    
    def _auto_enable_sources(self):
        """Automatically enable sources based on credential availability"""
        for source_id, config in self.sources.items():
            # Skip if already explicitly enabled
            if config.get('enabled', False):
                continue
            
            credential_required = config.get('credential_required', False)
            has_credentials = bool(config.get('api_key'))
            
            # Enable if no credentials required OR credentials are available
            if not credential_required or has_credentials:
                config['enabled'] = True
                logger.info(f"Auto-enabled source: {source_id}")
            else:
                config['enabled'] = False
                logger.debug(f"Source {source_id} disabled due to missing credentials")
    
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
                logger.info(f"Added API key and enabled source: {source_id}")
    
    def get_credential_status(self) -> Dict[str, Dict[str, Any]]:
        """Get credential status for all sources"""
        status = {}
        for source_id, config in self.sources.items():
            status[source_id] = {
                'name': config.get('name', source_id),
                'enabled': config.get('enabled', False),
                'credential_required': config.get('credential_required', False),
                'has_credentials': bool(config.get('api_key')),
                'primary_env_var': config.get('api_key_env', f"{source_id.upper()}_API_KEY"),
                'fallback_env_vars': config.get('credential_fallbacks', []),
                'auth_type': config.get('auth_type'),
                'description': config.get('description', '')
            }
        return status
    
    def check_source_health(self, source_id: str) -> Dict[str, Any]:
        """Check if a source is properly configured and available"""
        if source_id not in self.sources:
            return {'healthy': False, 'error': 'Source not found'}
        
        config = self.sources[source_id]
        health_status = {
            'healthy': True,
            'enabled': config.get('enabled', False),
            'errors': [],
            'warnings': []
        }
        
        # Check credentials
        if config.get('credential_required', False) and not config.get('api_key'):
            health_status['healthy'] = False
            health_status['errors'].append('Missing required credentials')
        
        # Check required configuration
        if not config.get('base_url'):
            health_status['healthy'] = False
            health_status['errors'].append('Missing base URL')
        
        # Check rate limiting configuration
        if not config.get('rate_limit'):
            health_status['warnings'].append('No rate limiting configured')
        
        return health_status
    
    def get_sources_by_capability(self, capability: str) -> List[str]:
        """Get all enabled sources that support a specific capability"""
        matching_sources = []
        for source_id, config in self.sources.items():
            if (config.get('enabled', False) and 
                capability in config.get('supports', [])):
                matching_sources.append(source_id)
        return matching_sources
    
    def get_rate_limit_info(self, source_id: str) -> Dict[str, Any]:
        """Get rate limiting information for a source"""
        if source_id not in self.sources:
            return {}
        
        config = self.sources[source_id]
        rate_limit = config.get('rate_limit', {})
        
        return {
            'calls_per_period': rate_limit.get('calls', 0),
            'period_seconds': rate_limit.get('period', 3600),
            'concurrent_requests': rate_limit.get('concurrent_requests', 1),
            'unauthenticated_calls': rate_limit.get('unauthenticated_calls'),
            'backoff_factor': config.get('error_handling', {}).get('backoff_factor', 1)
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the entire configuration and return status report"""
        report = {
            'total_sources': len(self.sources),
            'enabled_sources': 0,
            'sources_with_credentials': 0,
            'sources_requiring_credentials': 0,
            'healthy_sources': 0,
            'issues': []
        }
        
        for source_id, config in self.sources.items():
            if config.get('enabled', False):
                report['enabled_sources'] += 1
            
            if config.get('credential_required', False):
                report['sources_requiring_credentials'] += 1
            
            if config.get('api_key'):
                report['sources_with_credentials'] += 1
            
            health = self.check_source_health(source_id)
            if health['healthy']:
                report['healthy_sources'] += 1
            else:
                report['issues'].extend([
                    f"{source_id}: {error}" for error in health['errors']
                ])
        
        return report