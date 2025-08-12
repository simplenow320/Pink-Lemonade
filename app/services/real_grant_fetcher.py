"""
Real Grant Fetcher - ONLY real data, no mocks
"""
import logging
import requests
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class RealGrantFetcher:
    """Fetches ONLY real grant data from confirmed working sources"""
    
    def fetch_federal_register_grants(self, keyword: str = "grant opportunity", limit: int = 20) -> List[Dict]:
        """
        Fetch real grant notices from Federal Register API
        CONFIRMED WORKING - returns actual government funding notices
        """
        grants = []
        try:
            # This endpoint is confirmed working
            url = "https://www.federalregister.gov/api/v1/documents"
            
            params = {
                'conditions[term]': keyword,
                'conditions[type][]': 'NOTICE',  # Funding notices
                'per_page': limit,
                'order': 'newest'
            }
            
            response = requests.get(url, params=params, timeout=10)
            logger.info(f"Federal Register API response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                for doc in data.get('results', []):
                    # Only include if it looks like a grant opportunity
                    title = doc.get('title', '').lower()
                    abstract = (doc.get('abstract') or '').lower()
                    
                    if any(term in title + abstract for term in ['grant', 'funding', 'opportunity', 'solicitation', 'award']):
                        # Safely extract agency names
                        agencies = doc.get('agencies', [])
                        if agencies:
                            funder = ', '.join([agency.get('name', 'Federal Agency') for agency in agencies if isinstance(agency, dict)])
                        else:
                            funder = 'Federal Agency'
                            
                        grant = {
                            'title': doc.get('title'),
                            'funder': funder,
                            'description': doc.get('abstract', ''),
                            'link': doc.get('html_url'),
                            'pdf_url': doc.get('pdf_url'),
                            'deadline': doc.get('publication_date'),
                            'source': 'Federal Register',
                            'source_id': doc.get('document_number'),
                            'type': 'Federal Notice',
                            'is_real': True  # Mark as real data
                        }
                        grants.append(grant)
                
                logger.info(f"Fetched {len(grants)} real grants from Federal Register")
        
        except Exception as e:
            logger.error(f"Error fetching from Federal Register: {e}")
        
        return grants
    
    def fetch_sam_gov_grants(self, keyword: str = "nonprofit", limit: int = 20) -> List[Dict]:
        """
        Fetch real grants from SAM.gov (beta.SAM.gov API)
        This is the new unified government contracting/grants system
        """
        grants = []
        try:
            # SAM.gov public API endpoint
            url = "https://api.sam.gov/opportunities/v2/search"
            
            params = {
                'q': keyword,
                'postedFrom': '01/01/2025',  # Recent opportunities
                'limit': limit,
                'api_key': 'DEMO_KEY'  # Public demo key
            }
            
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'PinkLemonade/1.0'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            logger.info(f"SAM.gov API response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                for opp in data.get('opportunitiesData', []):
                    grant = {
                        'title': opp.get('title'),
                        'funder': opp.get('department', 'Federal Agency'),
                        'description': opp.get('description', ''),
                        'link': f"https://sam.gov/opp/{opp.get('noticeId')}/view",
                        'deadline': opp.get('responseDeadLine'),
                        'type': opp.get('type', 'Grant'),
                        'naics_codes': opp.get('naicsCode', ''),
                        'source': 'SAM.gov',
                        'source_id': opp.get('noticeId'),
                        'posted_date': opp.get('postedDate'),
                        'is_real': True
                    }
                    grants.append(grant)
                    
                logger.info(f"Fetched {len(grants)} real grants from SAM.gov")
                
        except Exception as e:
            logger.error(f"Error fetching from SAM.gov: {e}")
        
        return grants
    
    def fetch_usaspending_grants(self, keyword: str = "nonprofit", limit: int = 20) -> List[Dict]:
        """
        Fetch grant data from USAspending.gov API
        This shows actual awarded federal grants
        """
        grants = []
        try:
            # USAspending.gov API endpoint for awards
            url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
            
            payload = {
                "filters": {
                    "award_type_codes": ["02", "03", "04", "05"],  # Grant types
                    "keywords": [keyword],
                    "time_period": [
                        {
                            "start_date": "2025-01-01",
                            "end_date": "2025-12-31"
                        }
                    ]
                },
                "fields": ["Award ID", "Recipient Name", "Description", "Award Amount", "Awarding Agency"],
                "page": 1,
                "limit": limit,
                "sort": "Award Amount",
                "order": "desc"
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            logger.info(f"USAspending API response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                for result in data.get('results', []):
                    grant = {
                        'title': result.get('Description', 'Federal Grant Award'),
                        'funder': result.get('Awarding Agency', 'Federal Agency'),
                        'recipient': result.get('Recipient Name'),
                        'amount': result.get('Award Amount'),
                        'award_id': result.get('Award ID'),
                        'source': 'USAspending.gov',
                        'type': 'Awarded Grant',
                        'is_real': True,
                        'note': 'This is an already-awarded grant for reference'
                    }
                    grants.append(grant)
                    
                logger.info(f"Fetched {len(grants)} real awarded grants from USAspending")
                
        except Exception as e:
            logger.error(f"Error fetching from USAspending: {e}")
        
        return grants
    
    def fetch_all_real_grants(self, keyword: str = "nonprofit") -> List[Dict]:
        """
        Fetch grants from ALL working sources
        Returns ONLY real data
        """
        all_grants = []
        
        # Federal Register - confirmed working
        all_grants.extend(self.fetch_federal_register_grants(keyword))
        
        # SAM.gov - try to fetch
        all_grants.extend(self.fetch_sam_gov_grants(keyword))
        
        # USAspending - for reference of awarded grants
        # all_grants.extend(self.fetch_usaspending_grants(keyword))
        
        logger.info(f"Total real grants fetched: {len(all_grants)}")
        return all_grants

# Create singleton instance
real_grant_fetcher = RealGrantFetcher()