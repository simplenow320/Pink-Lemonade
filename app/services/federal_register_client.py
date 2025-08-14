"""
Federal Register API Client - Free government grant notices
"""
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class FederalRegisterClient:
    """Client for Federal Register API - no auth needed"""
    
    BASE_URL = "https://www.federalregister.gov/api/v1"
    
    def __init__(self):
        self.timeout = 30
        
    def search_grant_notices(self, keywords: str = "grant", days_back: int = 30) -> List[Dict]:
        """
        Search for grant-related notices in Federal Register
        
        Args:
            keywords: Search terms
            days_back: How many days back to search
            
        Returns:
            List of normalized grant notices
        """
        try:
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            params = {
                'conditions[term]': keywords,
                'conditions[publication_date][gte]': start_date,
                'per_page': 100,
                'format': 'json'
            }
            
            url = f"{self.BASE_URL}/documents?{urllib.parse.urlencode(params)}"
            
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                notices = []
                for doc in data.get('results', []):
                    normalized = self._normalize_document(doc)
                    if normalized:
                        notices.append(normalized)
                        
                logger.info(f"Federal Register: Found {len(notices)} grant notices")
                return notices
                
        except Exception as e:
            logger.error(f"Federal Register search error: {e}")
            return []
    
    def _normalize_document(self, doc: Dict) -> Optional[Dict]:
        """Normalize Federal Register document to opportunity format"""
        try:
            # Extract agencies
            agencies = doc.get('agencies', [])
            agency_names = [a.get('name', '') for a in agencies if a.get('name')]
            
            return {
                'source': 'federal_register',
                'source_type': 'Federal',
                'source_name': 'Federal Register',
                'title': doc.get('title', ''),
                'funder': ', '.join(agency_names) if agency_names else 'Federal Agency',
                'description': doc.get('abstract', ''),
                'url': doc.get('html_url', ''),
                'published_date': doc.get('publication_date', ''),
                'document_type': doc.get('type', ''),
                'docket_id': doc.get('docket_id', ''),
                'cfr_references': doc.get('cfr_references', [])
            }
        except Exception as e:
            logger.error(f"Error normalizing document: {e}")
            return None

# Singleton instance
_client = None

def get_federal_register_client() -> FederalRegisterClient:
    """Get singleton Federal Register client instance"""
    global _client
    if _client is None:
        _client = FederalRegisterClient()
    return _client