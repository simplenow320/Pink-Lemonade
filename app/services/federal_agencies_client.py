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
    BASE_URL = "https://www.grants.gov/grantsws/rest/opportunities/search"

    def fetch_grants(self, limit: int = 30) -> List[Dict]:
        grants = []
        try:
            # Use Grants.gov client which handles POST correctly
            from app.services.grants_gov_client import GrantsGovClient
            client = GrantsGovClient()
            payload = {"agencyCode": "ED", "limit": limit}
            all_grants = client.search_opportunities(payload)
            
            # Add Education branding
            for grant in all_grants:
                grant['source_name'] = 'Education Grants'
                if not grant.get('funder', '').startswith('Dept of Education'):
                    grant['funder'] = 'Dept of Education - ' + grant.get('funder', 'Department of Education')
            
            grants = all_grants
            logger.info(f"Education fetch: {len(grants)} grants")
        except Exception as e:
            logger.error(f"Education API error: {e}")

        return grants

class NSFGrantsClient:
    """National Science Foundation Grants"""
    BASE_URL = "https://www.nsf.gov/awardsearch/download.jsp"

    def fetch_grants(self, limit: int = 30) -> List[Dict]:
        grants = []
        try:
            # NSF uses a different API structure
            params = {
                'DownloadFileName': 'NSF_Funding',
                'All': 'true',
                'Order': 'Date',
                'Zip': 'false'
            }

            # Note: NSF API returns CSV, would need parsing
            # For now, use Grants.gov with NSF filter
            from app.services.grants_gov_client import GrantsGovClient
            client = GrantsGovClient()
            payload = {"keywords": "NSF National Science", "limit": limit}
            all_grants = client.search_opportunities(payload)
            grants = [g for g in all_grants if 'NSF' in g.get('funder', '')]

        except Exception as e:
            logger.error(f"NSF API error: {e}")

        return grants