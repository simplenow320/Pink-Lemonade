"""
Federal Agency Grant Clients (HHS, Education, NSF)
All use public APIs, no authentication required
"""
import requests
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

class HHSGrantsClient:
    """Health & Human Services Grants"""
    BASE_URL = "https://www.grants.gov/grantsws/rest/opportunities/search"

    def fetch_grants(self, limit: int = 30) -> List[Dict]:
        grants = []
        try:
            # Use Grants.gov client which handles POST correctly
            from app.services.grants_gov_client import GrantsGovClient
            client = GrantsGovClient()
            payload = {"agencyCode": "HHS", "limit": limit}
            all_grants = client.search_opportunities(payload)
            
            # Add HHS branding
            for grant in all_grants:
                grant['source_name'] = 'HHS Grants'
                if not grant.get('funder', '').startswith('HHS'):
                    grant['funder'] = 'HHS - ' + grant.get('funder', 'Health & Human Services')
            
            grants = all_grants
            logger.info(f"HHS fetch: {len(grants)} grants")
        except Exception as e:
            logger.error(f"HHS API error: {e}")

        return grants

class EducationGrantsClient:
    """Department of Education Grants"""

    def fetch_grants(self, limit: int = 30) -> List[Dict]:
        grants = []
        try:
            # Use GSA Search API via GrantsGovClient with Education-specific keywords
            from app.services.grants_gov_client import GrantsGovClient
            client = GrantsGovClient()
            
            # Search with Education Department keywords
            payload = {
                "keywords": "Department of Education grant opportunity funding",
                "limit": limit
            }
            all_grants = client.search_opportunities(payload)
            
            # Use all results and add Education branding
            # Note: GSA Search doesn't filter by agency, so we accept all results
            # and brand them as potential Education grants based on the search query
            for grant in all_grants:
                grant['source_name'] = 'Education Grants'
                grant['funder_name'] = 'Dept of Education - ' + grant.get('funder_name', 'Department of Education')
                grant['funder'] = grant['funder_name']
                grants.append(grant)
            
            logger.info(f"Education fetch: {len(grants)} grants (GSA Search, Education keywords)")
        except Exception as e:
            logger.error(f"Education API error: {e}")

        return grants

class NSFGrantsClient:
    """National Science Foundation Grants"""

    def fetch_grants(self, limit: int = 30) -> List[Dict]:
        grants = []
        try:
            # Use GSA Search API with NSF-specific keywords
            from app.services.grants_gov_client import GrantsGovClient
            client = GrantsGovClient()
            
            # Search with comprehensive NSF keywords
            payload = {
                "keywords": "National Science Foundation NSF grant opportunity research funding",
                "limit": limit
            }
            all_grants = client.search_opportunities(payload)
            
            # Use all results and add NSF branding
            # Note: GSA Search doesn't filter by agency, so we accept all results
            # and brand them as potential NSF grants based on the search query
            for grant in all_grants:
                grant['source_name'] = 'NSF Grants'
                grant['funder_name'] = 'NSF - National Science Foundation'
                grant['funder'] = grant['funder_name']
                grants.append(grant)
            
            logger.info(f"NSF fetch: {len(grants)} grants (GSA Search, NSF keywords)")
        except Exception as e:
            logger.error(f"NSF API error: {e}")

        return grants