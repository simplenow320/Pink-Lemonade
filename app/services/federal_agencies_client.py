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
            params = {
                'oppNum': '',
                'cfda': '',
                'oppStatus': 'forecasted|posted',
                'agencyCode': 'HHS',
                'rows': limit
            }

            response = requests.get(self.BASE_URL, params=params, timeout=20)
            if response.status_code == 200:
                data = response.json()
                for opp in data.get('opportunitiesList', []):
                    grants.append({
                        'title': opp.get('opportunityTitle'),
                        'funder': 'HHS - ' + opp.get('agencyName', 'Unknown'),
                        'description': opp.get('description', ''),
                        'deadline': opp.get('closeDate'),
                        'source_name': 'HHS Grants',
                        'source_url': f"https://www.grants.gov/web/grants/view-opportunity.html?oppId={opp.get('opportunityId')}"
                    })
        except Exception as e:
            logger.error(f"HHS API error: {e}")

        return grants

class EducationGrantsClient:
    """Department of Education Grants"""
    BASE_URL = "https://www.grants.gov/grantsws/rest/opportunities/search"

    def fetch_grants(self, limit: int = 30) -> List[Dict]:
        grants = []
        try:
            params = {
                'oppStatus': 'forecasted|posted',
                'agencyCode': 'ED',
                'rows': limit
            }

            response = requests.get(self.BASE_URL, params=params, timeout=20)
            if response.status_code == 200:
                data = response.json()
                for opp in data.get('opportunitiesList', []):
                    grants.append({
                        'title': opp.get('opportunityTitle'),
                        'funder': 'Dept of Education - ' + opp.get('agencyName', ''),
                        'description': opp.get('description', ''),
                        'deadline': opp.get('closeDate'),
                        'source_name': 'Education Grants',
                        'source_url': f"https://www.grants.gov/web/grants/view-opportunity.html?oppId={opp.get('opportunityId')}"
                    })
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