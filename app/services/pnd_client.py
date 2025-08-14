"""
Philanthropy News Digest Client - Free Foundation Grant News
"""
import json
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class PNDClient:
    """Client for Philanthropy News Digest RSS Feed - no auth needed"""
    
    RSS_URL = "https://philanthropynewsdigest.org/feed/rfps"
    
    def __init__(self):
        self.timeout = 30
        
    def get_foundation_opportunities(self) -> List[Dict]:
        """
        Fetch foundation grant opportunities from PND RSS feed
        
        Returns:
            List of normalized foundation opportunities
        """
        try:
            # Fetch RSS feed
            req = urllib.request.Request(
                self.RSS_URL,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                xml_data = response.read().decode('utf-8')
                
            # Parse XML
            root = ET.fromstring(xml_data)
            
            opportunities = []
            # Find all items in the RSS feed
            for item in root.findall('.//item'):
                opp = self._parse_rss_item(item)
                if opp:
                    opportunities.append(opp)
                    
            logger.info(f"PND: Found {len(opportunities)} foundation opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"PND RSS feed error: {e}")
            return []
    
    def _parse_rss_item(self, item) -> Optional[Dict]:
        """Parse an RSS item into opportunity format"""
        try:
            # Extract text from XML elements
            title = item.find('title').text if item.find('title') is not None else ''
            description = item.find('description').text if item.find('description') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
            
            # Parse deadline from description if available
            deadline = self._extract_deadline(description)
            funder = self._extract_funder(title, description)
            
            return {
                'source': 'pnd',
                'source_type': 'Foundation',
                'source_name': 'Philanthropy News Digest',
                'title': title,
                'funder': funder,
                'description': description[:500] if description else '',  # Limit description length
                'url': link,
                'published_date': self._parse_date(pub_date),
                'deadline': deadline,
                'grant_type': 'Foundation RFP'
            }
        except Exception as e:
            logger.error(f"Error parsing RSS item: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> str:
        """Parse RSS date format to ISO format"""
        try:
            # RSS dates are like: Mon, 04 Mar 2024 00:00:00 GMT
            dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            return dt.strftime('%Y-%m-%d')
        except:
            return date_str
    
    def _extract_deadline(self, description: str) -> str:
        """Try to extract deadline from description"""
        # Common deadline patterns
        deadline_keywords = ['deadline:', 'due:', 'by:', 'before:', 'closes:']
        desc_lower = description.lower()
        
        for keyword in deadline_keywords:
            if keyword in desc_lower:
                # Try to extract date after keyword
                idx = desc_lower.index(keyword)
                # Get next 50 characters and try to find a date
                snippet = description[idx:idx+50]
                # This is simplified - in production you'd use better date parsing
                return snippet.split('\n')[0].split('.')[0].strip()
        return ''
    
    def _extract_funder(self, title: str, description: str) -> str:
        """Try to extract funder name from title or description"""
        # Often the funder is at the beginning of the title
        if ':' in title:
            return title.split(':')[0].strip()
        elif '-' in title:
            return title.split('-')[0].strip()
        else:
            # Take first few words as funder name
            words = title.split()[:3]
            return ' '.join(words)

# Singleton instance
_client = None

def get_pnd_client() -> PNDClient:
    """Get singleton PND client instance"""
    global _client
    if _client is None:
        _client = PNDClient()
    return _client