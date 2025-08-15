"""
Candid News API v1 Client - Foundation and Grant News
"""
import os
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class CandidNewsClient:
    """Client for Candid News API v1 - WORKING"""
    
    BASE_URL = "https://api.candid.org/news/v1"
    
    def __init__(self):
        # Use the working News API keys
        self.primary_key = os.environ.get('CANDID_NEWS_KEY', '7647f9fe2d9645d48def7a04b6835083')
        self.secondary_key = '0da558d408e74654baa000836cb88bef'
        self.timeout = 30
        
    def search_news(self, 
                   search_terms: str = "",
                   organizations: List[str] = None,
                   eins: List[str] = None,
                   locations: List[str] = None,
                   start_date: str = None,
                   end_date: str = None,
                   page: int = 1,
                   page_size: int = 25) -> Dict:
        """
        Search for grant and foundation news
        
        Args:
            search_terms: Keywords to search
            organizations: List of organization names
            eins: List of EINs
            locations: List of locations
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            page: Page number
            page_size: Results per page
            
        Returns:
            Dict with news articles and metadata
        """
        try:
            # Start with base URL - News API doesn't require parameters
            url = f"{self.BASE_URL}/search"
            
            # Only add parameters if they're provided
            params = {}
            if search_terms:
                params['search_terms'] = search_terms
            if page and page > 1:
                params['page'] = str(page)
            if page_size and page_size != 25:
                params['page_size'] = str(page_size)
                
            if params:
                url += '?' + urllib.parse.urlencode(params)
            
            headers = {
                'Subscription-Key': self.primary_key,
                'accept': 'application/json'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get('meta', {}).get('code') == 200:
                    logger.info(f"Candid News: Found {data.get('meta', {}).get('article_count', 0)} articles")
                    return data
                    
        except Exception as e:
            logger.error(f"Candid news search error: {e}")
            
        return {'meta': {}, 'data': {'articles': []}}
    
    def get_grant_news_opportunities(self, keyword: str = "grant opportunity") -> List[Dict]:
        """
        Get news articles about grant opportunities
        
        Args:
            keyword: Search keyword for grant news
            
        Returns:
            List of grant opportunity news formatted as opportunities
        """
        try:
            # Search for recent grant news
            news_data = self.search_news(
                search_terms=keyword,
                page_size=10
            )
            
            opportunities = []
            articles = news_data.get('data', {}).get('articles', [])
            
            for article in articles:
                opportunity = self._format_news_as_opportunity(article)
                if opportunity:
                    opportunities.append(opportunity)
                    
            return opportunities
            
        except Exception as e:
            logger.error(f"Error fetching grant news: {e}")
            return []
    
    def _format_news_as_opportunity(self, article: Dict) -> Optional[Dict]:
        """Format a news article as a grant opportunity"""
        try:
            # Extract key information from article
            title = article.get('title', '')
            description = article.get('description', article.get('summary', ''))
            published = article.get('published_date', '')
            source = article.get('source', '')
            url = article.get('url', '')
            
            # Extract organizations mentioned
            orgs = article.get('organizations', [])
            funder = orgs[0] if orgs else 'Various Foundations'
            
            return {
                'source': 'candid_news',
                'source_type': 'News',
                'source_name': f'Candid News - {source}',
                'title': title[:200] if title else 'Grant Opportunity News',
                'funder': funder,
                'description': description[:500] if description else '',
                'published_date': published,
                'news_url': url,
                'grant_type': 'Foundation News',
                'keywords': article.get('keywords', [])
            }
            
        except Exception as e:
            logger.error(f"Error formatting news article: {e}")
            return None

# Singleton instance
_client = None

def get_candid_news_client() -> CandidNewsClient:
    """Get singleton Candid News client instance"""
    global _client
    if _client is None:
        _client = CandidNewsClient()
    return _client