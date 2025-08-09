"""
Live Grant Data Sources Integration
Connects to real grant APIs and feeds
"""
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import xml.etree.ElementTree as ET
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

class LiveGrantSources:
    """Integrates with multiple live grant data sources"""
    
    def __init__(self):
        self.sources = {
            'grants_gov': {
                'name': 'Grants.gov',
                'base_url': 'https://www.grants.gov/api/v2',
                'rate_limit': 100,  # calls per hour
                'enabled': True
            },
            'federal_register': {
                'name': 'Federal Register',
                'base_url': 'https://www.federalregister.gov/api/v1',
                'rate_limit': 1000,  # calls per hour
                'enabled': True
            },
            'govinfo': {
                'name': 'GovInfo',
                'base_url': 'https://api.govinfo.gov',
                'rate_limit': 1000,  # calls per hour
                'enabled': True
            },
            'pnd': {
                'name': 'Philanthropy News Digest',
                'base_url': 'https://philanthropynewsdigest.org/rfps/feed',
                'rate_limit': 60,  # calls per hour
                'enabled': True
            }
        }
    
    def fetch_grants_gov(self, keywords: List[str] = None, days_back: int = 30) -> List[Dict]:
        """
        Fetch grants from Grants.gov REST API
        """
        grants = []
        try:
            # Build search parameters
            params = {
                'format': 'json',
                'rows': 100,
                'start': 0,
                'postdatestart': (datetime.now() - timedelta(days=days_back)).strftime('%m/%d/%Y'),
                'postdateend': datetime.now().strftime('%m/%d/%Y')
            }
            
            if keywords:
                params['keyword'] = ' '.join(keywords)
            
            # Make API request
            response = requests.get(
                f"{self.sources['grants_gov']['base_url']}/opportunities/search",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                opportunities = data.get('opportunities', [])
                
                for opp in opportunities:
                    grant = {
                        'title': opp.get('title', ''),
                        'funder': opp.get('agencyName', ''),
                        'description': opp.get('description', ''),
                        'amount_min': 0,
                        'amount_max': float(opp.get('awardCeiling', 0)) if opp.get('awardCeiling') else 0,
                        'deadline': opp.get('closeDate', ''),
                        'eligibility_criteria': opp.get('eligibility', ''),
                        'focus_areas': ', '.join(opp.get('categories', [])),
                        'geography': 'United States',
                        'link': f"https://www.grants.gov/search-results-detail/{opp.get('id')}",
                        'source_name': 'Grants.gov',
                        'discovered_at': datetime.now().isoformat()
                    }
                    grants.append(grant)
                    
                logger.info(f"Fetched {len(grants)} grants from Grants.gov")
            else:
                logger.error(f"Grants.gov API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching from Grants.gov: {e}")
            
        return grants
    
    def fetch_federal_register(self, keywords: List[str] = None, days_back: int = 30) -> List[Dict]:
        """
        Fetch funding opportunities from Federal Register API
        """
        grants = []
        try:
            # Build search parameters
            params = {
                'format': 'json',
                'per_page': 100,
                'order': 'newest',
                'conditions[type]': 'NOTICE',
                'conditions[term]': 'grant opportunity',
                'conditions[publication_date][gte]': (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            }
            
            if keywords:
                params['conditions[term]'] = ' '.join(keywords + ['grant'])
            
            # Make API request
            response = requests.get(
                f"{self.sources['federal_register']['base_url']}/documents",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get('results', [])
                
                for doc in documents:
                    if 'grant' in doc.get('title', '').lower() or 'funding' in doc.get('title', '').lower():
                        grant = {
                            'title': doc.get('title', ''),
                            'funder': ', '.join(doc.get('agencies', [])),
                            'description': doc.get('abstract', ''),
                            'amount_min': 0,
                            'amount_max': 0,  # Not typically specified
                            'deadline': doc.get('comments_close_on', ''),
                            'eligibility_criteria': 'See document for details',
                            'focus_areas': ', '.join(doc.get('topics', [])),
                            'geography': 'United States',
                            'link': doc.get('html_url', ''),
                            'source_name': 'Federal Register',
                            'discovered_at': datetime.now().isoformat()
                        }
                        grants.append(grant)
                        
                logger.info(f"Fetched {len(grants)} grants from Federal Register")
            else:
                logger.error(f"Federal Register API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching from Federal Register: {e}")
            
        return grants
    
    def fetch_govinfo(self, keywords: List[str] = None, days_back: int = 30) -> List[Dict]:
        """
        Fetch grant opportunities from GovInfo API
        """
        grants = []
        try:
            # Build search query
            query_parts = ['grant', 'opportunity', 'funding', 'NOFO']
            if keywords:
                query_parts.extend(keywords)
            
            params = {
                'api_key': 'DEMO_KEY',  # Public demo key
                'query': ' OR '.join(query_parts),
                'pageSize': 100,
                'offsetMark': '*',
                'publishedSince': (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%dT00:00:00Z')
            }
            
            # Make API request
            response = requests.get(
                f"{self.sources['govinfo']['base_url']}/search",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                packages = data.get('packages', [])
                
                for pkg in packages:
                    if 'grant' in pkg.get('title', '').lower() or 'funding' in pkg.get('title', '').lower():
                        grant = {
                            'title': pkg.get('title', ''),
                            'funder': pkg.get('governmentAuthor', ['Unknown'])[0] if pkg.get('governmentAuthor') else 'Unknown',
                            'description': pkg.get('summary', ''),
                            'amount_min': 0,
                            'amount_max': 0,
                            'deadline': '',
                            'eligibility_criteria': 'See document for details',
                            'focus_areas': '',
                            'geography': 'United States',
                            'link': pkg.get('detailsLink', ''),
                            'source_name': 'GovInfo',
                            'discovered_at': datetime.now().isoformat()
                        }
                        grants.append(grant)
                        
                logger.info(f"Fetched {len(grants)} grants from GovInfo")
            else:
                logger.error(f"GovInfo API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching from GovInfo: {e}")
            
        return grants
    
    def fetch_pnd_rss(self) -> List[Dict]:
        """
        Fetch foundation grants from Philanthropy News Digest RSS feed
        """
        grants = []
        try:
            # Fetch RSS feed
            response = requests.get(
                self.sources['pnd']['base_url'],
                timeout=30
            )
            
            if response.status_code == 200:
                # Parse XML
                root = ET.fromstring(response.content)
                
                # Find all items in the RSS feed
                for item in root.findall('.//item'):
                    title = item.find('title').text if item.find('title') is not None else ''
                    description = item.find('description').text if item.find('description') is not None else ''
                    link = item.find('link').text if item.find('link') is not None else ''
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                    
                    # Extract grant details from description using AI
                    if ai_service.is_enabled() and description:
                        extracted = ai_service.extract_grant_from_text(description, link)
                        if extracted:
                            extracted['source_name'] = 'Philanthropy News Digest'
                            grants.append(extracted)
                    else:
                        # Fallback to basic extraction
                        grant = {
                            'title': title,
                            'funder': 'Various Foundations',
                            'description': description[:500] if description else '',
                            'amount_min': 0,
                            'amount_max': 0,
                            'deadline': '',
                            'eligibility_criteria': 'See announcement for details',
                            'focus_areas': '',
                            'geography': 'United States',
                            'link': link,
                            'source_name': 'Philanthropy News Digest',
                            'discovered_at': datetime.now().isoformat()
                        }
                        grants.append(grant)
                        
                logger.info(f"Fetched {len(grants)} grants from PND RSS")
            else:
                logger.error(f"PND RSS error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching from PND RSS: {e}")
            
        return grants
    
    def fetch_all_sources(self, keywords: List[str] = None, days_back: int = 30) -> Dict[str, List[Dict]]:
        """
        Fetch grants from all enabled sources
        """
        all_grants = {}
        
        if self.sources['grants_gov']['enabled']:
            all_grants['grants_gov'] = self.fetch_grants_gov(keywords, days_back)
            
        if self.sources['federal_register']['enabled']:
            all_grants['federal_register'] = self.fetch_federal_register(keywords, days_back)
            
        if self.sources['govinfo']['enabled']:
            all_grants['govinfo'] = self.fetch_govinfo(keywords, days_back)
            
        if self.sources['pnd']['enabled']:
            all_grants['pnd'] = self.fetch_pnd_rss()
            
        # Log summary
        total = sum(len(grants) for grants in all_grants.values())
        logger.info(f"Fetched {total} total grants from {len(all_grants)} sources")
        
        return all_grants
    
    def process_and_score_grants(self, grants: List[Dict], org_profile: Dict) -> List[Dict]:
        """
        Process grants with AI scoring and match explanations
        """
        processed = []
        
        for grant in grants:
            # Add AI match scoring if available
            if ai_service.is_enabled():
                score, reason = ai_service.match_grant(org_profile, grant)
                grant['fit_score'] = score
                grant['fit_reason'] = reason
            else:
                grant['fit_score'] = 0
                grant['fit_reason'] = 'AI scoring unavailable'
                
            processed.append(grant)
            
        # Sort by fit score
        processed.sort(key=lambda x: x.get('fit_score', 0), reverse=True)
        
        return processed

# Singleton instance
live_sources = LiveGrantSources()