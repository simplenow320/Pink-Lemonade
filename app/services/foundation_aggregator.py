"""
Foundation Grant Aggregator - Multiple Sources
Combines data from various foundation and grant sources
"""
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)

class FoundationAggregator:
    """Aggregates foundation grant data from multiple sources"""
    
    def __init__(self):
        self.timeout = 30
        
    def get_all_foundation_opportunities(self, search_term: str = "") -> List[Dict]:
        """
        Aggregate foundation opportunities from all available sources
        
        Returns:
            Combined list of foundation opportunities
        """
        all_opportunities = []
        
        # 1. Try Chronicle of Philanthropy
        try:
            chronicle_opps = self._get_chronicle_opportunities(search_term)
            all_opportunities.extend(chronicle_opps)
            logger.info(f"Chronicle: Found {len(chronicle_opps)} opportunities")
        except Exception as e:
            logger.error(f"Chronicle error: {e}")
        
        # 2. Try Inside Philanthropy
        try:
            inside_opps = self._get_inside_philanthropy(search_term)
            all_opportunities.extend(inside_opps)
            logger.info(f"Inside Philanthropy: Found {len(inside_opps)} opportunities")
        except Exception as e:
            logger.error(f"Inside Philanthropy error: {e}")
        
        # 3. Try GrantSpace
        try:
            grantspace_opps = self._get_grantspace_opportunities(search_term)
            all_opportunities.extend(grantspace_opps)
            logger.info(f"GrantSpace: Found {len(grantspace_opps)} opportunities")
        except Exception as e:
            logger.error(f"GrantSpace error: {e}")
        
        # 4. Add major foundation websites directly
        major_foundations = self._get_major_foundations()
        all_opportunities.extend(major_foundations)
        
        return all_opportunities
    
    def _get_chronicle_opportunities(self, search_term: str) -> List[Dict]:
        """Get opportunities from Chronicle of Philanthropy (if available)"""
        opportunities = []
        try:
            # Chronicle has a public grants database
            url = f"https://www.philanthropy.com/grants?q={urllib.parse.quote(search_term or 'grant')}"
            # This would require web scraping or API access
            # For now, return empty list
        except:
            pass
        return opportunities
    
    def _get_inside_philanthropy(self, search_term: str) -> List[Dict]:
        """Get data from Inside Philanthropy"""
        opportunities = []
        try:
            # Inside Philanthropy tracks major foundation giving
            # This would require their API or web scraping
            pass
        except:
            pass
        return opportunities
    
    def _get_grantspace_opportunities(self, search_term: str) -> List[Dict]:
        """Get opportunities from GrantSpace (Candid's free resource)"""
        opportunities = []
        try:
            # GrantSpace provides free grant information
            # This is Candid's free public resource
            pass
        except:
            pass
        return opportunities
    
    def _get_major_foundations(self) -> List[Dict]:
        """
        Return information about major foundations with active grant programs
        These are well-known foundations with public application processes
        """
        major_foundations = [
            {
                'source': 'foundation_directory',
                'source_type': 'Foundation',
                'source_name': 'Major Foundations',
                'title': 'Bill & Melinda Gates Foundation - Global Health Grants',
                'funder': 'Bill & Melinda Gates Foundation',
                'description': 'Supporting innovative solutions in global health, development, and education. Focus areas include vaccine development, maternal health, and educational technology.',
                'website': 'https://www.gatesfoundation.org/about/how-we-work/grants',
                'focus_areas': ['Health', 'Education', 'Global Development'],
                'grant_type': 'Foundation Grant',
                'typical_amount': '$100,000 - $2,000,000'
            },
            {
                'source': 'foundation_directory',
                'source_type': 'Foundation',
                'source_name': 'Major Foundations',
                'title': 'Ford Foundation - Building Institutions and Networks',
                'funder': 'Ford Foundation',
                'description': 'Advancing human dignity and social justice globally. Focus on inequality, civic engagement, and creativity.',
                'website': 'https://www.fordfoundation.org/work/our-grants/',
                'focus_areas': ['Social Justice', 'Economic Equity', 'Civic Engagement'],
                'grant_type': 'Foundation Grant',
                'typical_amount': '$50,000 - $500,000'
            },
            {
                'source': 'foundation_directory',
                'source_type': 'Foundation',
                'source_name': 'Major Foundations',
                'title': 'Robert Wood Johnson Foundation - Health Equity Grants',
                'funder': 'Robert Wood Johnson Foundation',
                'description': 'Building a Culture of Health where everyone has a fair opportunity for health and well-being.',
                'website': 'https://www.rwjf.org/en/grants.html',
                'focus_areas': ['Public Health', 'Health Equity', 'Community Development'],
                'grant_type': 'Foundation Grant',
                'typical_amount': '$25,000 - $250,000'
            },
            {
                'source': 'foundation_directory',
                'source_type': 'Foundation',
                'source_name': 'Major Foundations',
                'title': 'MacArthur Foundation - Community and Economic Development',
                'funder': 'John D. and Catherine T. MacArthur Foundation',
                'description': 'Supporting creative people, effective institutions, and influential networks building a more just and peaceful world.',
                'website': 'https://www.macfound.org/info-grantseekers/',
                'focus_areas': ['Criminal Justice', 'Climate Change', 'Nuclear Risk'],
                'grant_type': 'Foundation Grant',
                'typical_amount': '$100,000 - $1,000,000'
            },
            {
                'source': 'foundation_directory',
                'source_type': 'Foundation',
                'source_name': 'Major Foundations',
                'title': 'W.K. Kellogg Foundation - Racial Equity Grants',
                'funder': 'W.K. Kellogg Foundation',
                'description': 'Supporting children, families, and communities to strengthen and create conditions for vulnerable children.',
                'website': 'https://www.wkkf.org/grants',
                'focus_areas': ['Racial Equity', 'Community Engagement', 'Youth Development'],
                'grant_type': 'Foundation Grant',
                'typical_amount': '$30,000 - $300,000'
            },
            {
                'source': 'foundation_directory',
                'source_type': 'Foundation',
                'source_name': 'Major Foundations',
                'title': 'Andrew W. Mellon Foundation - Arts and Culture',
                'funder': 'Andrew W. Mellon Foundation',
                'description': 'Supporting excellence in the arts and humanities, higher education, and cultural preservation.',
                'website': 'https://mellon.org/grants/',
                'focus_areas': ['Arts', 'Humanities', 'Higher Education'],
                'grant_type': 'Foundation Grant',
                'typical_amount': '$50,000 - $750,000'
            },
            {
                'source': 'foundation_directory',
                'source_type': 'Foundation',
                'source_name': 'Major Foundations',
                'title': 'Lilly Endowment - Community Development',
                'funder': 'Lilly Endowment Inc.',
                'description': 'Supporting religion, education, and community development, primarily in Indiana.',
                'website': 'https://www.lillyendowment.org/',
                'focus_areas': ['Religion', 'Education', 'Community Development'],
                'grant_type': 'Foundation Grant',
                'typical_amount': '$25,000 - $500,000'
            },
            {
                'source': 'foundation_directory',
                'source_type': 'Foundation',
                'source_name': 'Major Foundations',
                'title': 'Walton Family Foundation - Education Reform',
                'funder': 'Walton Family Foundation',
                'description': 'Creating opportunity through education, environmental conservation, and improving quality of life.',
                'website': 'https://www.waltonfamilyfoundation.org/grants',
                'focus_areas': ['K-12 Education', 'Environment', 'Economic Development'],
                'grant_type': 'Foundation Grant',
                'typical_amount': '$50,000 - $1,000,000'
            }
        ]
        
        return major_foundations

# Singleton instance
_aggregator = None

def get_foundation_aggregator() -> FoundationAggregator:
    """Get singleton foundation aggregator instance"""
    global _aggregator
    if _aggregator is None:
        _aggregator = FoundationAggregator()
    return _aggregator