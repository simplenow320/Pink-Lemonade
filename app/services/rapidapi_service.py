"""
Grants.gov API Service for fetching real federal grant data
"""
import requests
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import os
from app.services.mode import is_live

logger = logging.getLogger(__name__)

class GrantsGovAPIService:
    """Service for fetching grants from Grants.gov free API"""
    
    def __init__(self):
        self.base_url = 'https://api.grants.gov/v1/api'
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def search_grants(self, keywords: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for grants using keywords via Grants.gov API
        
        Args:
            keywords: List of keywords to search for
            limit: Maximum number of results
            
        Returns:
            List of grant dictionaries
        """
        try:
            # Join keywords with spaces
            keywords_str = ' '.join(keywords)
            
            # Build the search request
            url = f"{self.base_url}/search2"
            search_data = {
                "keyword": keywords_str,
                "rows": min(limit, 50)  # Grants.gov has a max of 50
            }
            
            logger.info(f"Searching Grants.gov with keywords: {keywords_str}")
            
            response = requests.post(url, headers=self.headers, json=search_data, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract grants from response
            grants = []
            
            # Handle Grants.gov response format - actual format is data.oppHits[]
            if isinstance(data, dict) and 'data' in data and 'oppHits' in data['data']:
                opportunities = data['data']['oppHits']
            elif isinstance(data, dict) and 'oppHits' in data:
                opportunities = data['oppHits']  
            elif isinstance(data, list):
                opportunities = data
            else:
                logger.warning(f"Unexpected Grants.gov response format. Available keys: {data.keys() if isinstance(data, dict) else type(data)}")
                return []
            
            # Convert grants to our format
            for opp in opportunities[:limit]:
                grant = self._convert_grants_gov_opportunity(opp)
                if grant:
                    grants.append(grant)
            
            logger.info(f"Found {len(grants)} grants from Grants.gov")
            return grants
            
        except requests.exceptions.RequestException as e:
            if is_live():
                logger.error(f"LIVE MODE: Network error fetching grants from Grants.gov: {str(e)}")
                logger.error("GUIDANCE: Check internet connection and Grants.gov API availability. No mock data will be provided in LIVE mode.")
            else:
                logger.warning(f"DEMO MODE: Network error simulated for Grants.gov: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            if is_live():
                logger.error(f"LIVE MODE: JSON decode error from Grants.gov: {str(e)}")
                logger.error("GUIDANCE: Grants.gov API response format may have changed. No fallback data available in LIVE mode.")
            else:
                logger.warning(f"DEMO MODE: JSON decode error simulated for Grants.gov: {str(e)}")
            return []
        except Exception as e:
            if is_live():
                logger.error(f"LIVE MODE: Unexpected error fetching grants from Grants.gov: {str(e)}")
                logger.error("GUIDANCE: API may be temporarily unavailable. Try again later or contact support. No synthetic data will be provided.")
            else:
                logger.warning(f"DEMO MODE: Error simulated for Grants.gov: {str(e)}")
            return []
    
    def get_faith_based_grants(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Get grants specifically relevant to faith-based organizations
        
        Returns:
            List of faith-based grant dictionaries
        """
        faith_keywords = [
            'nonprofit', 'community', 'faith', 'ministry', 'church', 
            'social services', 'youth development', 'education',
            'mental health', 'family services', 'community development'
        ]
        
        return self.search_grants(faith_keywords, limit=limit)
    
    def get_tech_ai_grants(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get AI and technology grants for nonprofits
        
        Returns:
            List of tech/AI grant dictionaries
        """
        tech_keywords = [
            'artificial intelligence', 'AI', 'technology', 'digital', 
            'innovation', 'software', 'data science', 'machine learning',
            'tech nonprofit', 'digital transformation'
        ]
        
        return self.search_grants(tech_keywords, limit=limit)
    
    def get_arts_grants(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get arts and cultural grants
        
        Returns:
            List of arts grant dictionaries
        """
        arts_keywords = [
            'arts', 'culture', 'creative', 'music', 'visual arts',
            'performing arts', 'theater', 'dance', 'artistic expression',
            'cultural programs', 'community arts'
        ]
        
        return self.search_grants(arts_keywords, limit=limit)
    
    def get_mental_health_grants(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get mental health focused grants
        
        Returns:
            List of mental health grant dictionaries
        """
        health_keywords = [
            'mental health', 'behavioral health', 'wellness', 'counseling',
            'therapy', 'psychological services', 'emotional support',
            'trauma care', 'crisis intervention', 'mental wellness'
        ]
        
        return self.search_grants(health_keywords, limit=limit)
    
    def get_community_grants(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get community-focused grants
        
        Returns:
            List of community grant dictionaries  
        """
        community_keywords = [
            'community development', 'urban ministry', 'neighborhood',
            'social services', 'outreach', 'empowerment',
            'capacity building', 'leadership development'
        ]
        
        return self.search_grants(community_keywords, limit=limit)
    
    def _convert_grants_gov_opportunity(self, opp: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert Grants.gov opportunity format to our internal format
        
        Args:
            opp: Raw opportunity data from Grants.gov
            
        Returns:
            Converted grant dictionary or None if invalid
        """
        try:
            # Extract basic fields
            title = opp.get('title', 'Unknown Grant')
            
            # Handle agency/funder
            agency = opp.get('agency', 'Unknown Agency')
            agency_code = opp.get('agencyCode', '')
            funder = f"{agency} ({agency_code})" if agency_code else agency
            
            # Extract description
            description = (opp.get('description') or 
                         opp.get('synopsis') or 
                         opp.get('summary') or 
                         'No description available')
            
            # Handle opportunity number for website
            opp_number = opp.get('number', '')
            website = f"https://www.grants.gov/search-results-detail/{opp.get('id')}" if opp.get('id') else None
            
            # Handle eligibility
            eligibility = (opp.get('eligibilityInstructions') or 
                          opp.get('eligibilities') or
                          'Check grant details for eligibility requirements')
            
            # Handle dates - convert from YYYY-MM-DD format
            due_date = None
            close_date = opp.get('closeDt')
            if close_date:
                try:
                    # Handle different date formats
                    if 'T' in close_date:
                        due_date = close_date.split('T')[0]
                    else:
                        due_date = close_date
                except Exception:
                    due_date = None
            
            # Handle funding information
            amount = None
            if opp.get('totalCost'):
                try:
                    amount = float(opp.get('totalCost'))
                except (ValueError, TypeError):
                    pass
            elif opp.get('awardCeiling'):
                try:
                    amount = float(opp.get('awardCeiling'))
                except (ValueError, TypeError):
                    pass
            
            # Extract focus areas from categories
            focus_areas = []
            if opp.get('fundingCategories'):
                if isinstance(opp['fundingCategories'], list):
                    focus_areas.extend([cat.get('description', cat) if isinstance(cat, dict) else str(cat) 
                                      for cat in opp['fundingCategories']])
                else:
                    focus_areas.append(str(opp['fundingCategories']))
            
            if opp.get('fundingInstruments'):
                if isinstance(opp['fundingInstruments'], list):
                    focus_areas.extend([inst.get('description', inst) if isinstance(inst, dict) else str(inst) 
                                      for inst in opp['fundingInstruments']])
                else:
                    focus_areas.append(str(opp['fundingInstruments']))
            
            # Build the grant object
            grant = {
                'title': title,
                'funder': funder,
                'description': description[:1000] if description else '',  # Limit description length
                'amount': amount,
                'due_date': due_date,
                'website': website,
                'eligibility': eligibility[:500] if eligibility else '',  # Limit eligibility text
                'focus_areas': focus_areas[:10],  # Limit focus areas
                'contact_email': opp.get('contactEmail'),
                'contact_name': opp.get('contactName'),
                'contact_phone': opp.get('contactPhone'),
                'source': 'Grants.gov API',
                'discovery_method': 'api-search',
                'is_scraped': False,
                'opportunity_number': opp_number
            }
            
            # Only return if we have minimum required fields
            if title and title != 'Unknown Grant' and funder and funder != 'Unknown Agency':
                return grant
            else:
                logger.warning(f"Skipping grant with insufficient data: {title} from {funder}")
                return None
                
        except Exception as e:
            logger.error(f"Error converting Grants.gov opportunity: {str(e)}")
            return None

# Global instance
grants_gov_service = GrantsGovAPIService()