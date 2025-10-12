"""
Production Grant Fetcher Service
Fetches real grant data from multiple sources
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from app import db
from app.models import Grant, Organization, ScraperSource
from app.services.federal_register_client import FederalRegisterClient
from app.services.usaspending_client import USAspendingClient
from app.services.candid_client import GrantsClient
from app.services.geoname_mapping import get_geoname_id, STATE_GEONAME_IDS
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

class GrantFetcher:
    """Production service for fetching and storing real grant data"""
    
    def __init__(self):
        self.federal_client = FederalRegisterClient()
        self.usaspending_client = USAspendingClient()
        self.candid_client = GrantsClient()
        self.ai_service = AIService()
        
        # Track fetch statistics
        self.stats = {
            'total_fetched': 0,
            'federal_register': 0,
            'usaspending': 0,
            'candid': 0,
            'errors': 0
        }
    
    def fetch_all_grants(self, limit: int = 100) -> Dict:
        """Fetch grants from all available sources"""
        logger.info("Starting comprehensive grant fetch")
        grants = []
        
        # Fetch from Federal Register
        try:
            federal_grants = self.fetch_federal_register_grants(limit//3)
            grants.extend(federal_grants)
            self.stats['federal_register'] = len(federal_grants)
            logger.info(f"Fetched {len(federal_grants)} from Federal Register")
        except Exception as e:
            logger.error(f"Federal Register fetch failed: {e}")
            self.stats['errors'] += 1
        
        # Fetch from USAspending
        try:
            usa_grants = self.fetch_usaspending_grants(limit//3)
            grants.extend(usa_grants)
            self.stats['usaspending'] = len(usa_grants)
            logger.info(f"Fetched {len(usa_grants)} from USAspending")
        except Exception as e:
            logger.error(f"USAspending fetch failed: {e}")
            self.stats['errors'] += 1
        
        # Fetch from Candid (if API key available)
        if os.environ.get('CANDID_GRANTS_KEYS'):
            try:
                candid_grants = self.fetch_candid_grants(limit//3)
                grants.extend(candid_grants)
                self.stats['candid'] = len(candid_grants)
                logger.info(f"Fetched {len(candid_grants)} from Candid")
            except Exception as e:
                logger.error(f"Candid fetch failed: {e}")
                self.stats['errors'] += 1
        
        self.stats['total_fetched'] = len(grants)
        
        # Store grants in database
        stored_count = self.store_grants(grants)
        
        return {
            'success': True,
            'fetched': len(grants),
            'stored': stored_count,
            'stats': self.stats
        }
    
    def fetch_federal_register_grants(self, limit: int = 30) -> List[Dict]:
        """Fetch grant opportunities from Federal Register"""
        grants = []
        
        # Search for grant-related documents
        params = {
            'conditions[term]': 'grant opportunity',
            'conditions[agencies][]': ['health-and-human-services-department',
                                       'education-department',
                                       'national-science-foundation'],
            'conditions[type][]': 'NOTICE',
            'per_page': limit,
            'order': 'newest'
        }
        
        try:
            response = requests.get(
                'https://www.federalregister.gov/api/v1/documents',
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for doc in data.get('results', []):
                    grant = self.parse_federal_register_grant(doc)
                    if grant:
                        grants.append(grant)
        except Exception as e:
            logger.error(f"Federal Register API error: {e}")
        
        return grants
    
    def parse_federal_register_grant(self, doc: Dict) -> Optional[Dict]:
        """Parse Federal Register document into grant format"""
        try:
            # Extract deadline from document
            deadline = None
            if doc.get('dates'):
                deadline = doc['dates']
            elif doc.get('publication_date'):
                # Default to 60 days from publication
                pub_date = datetime.strptime(doc['publication_date'], '%Y-%m-%d')
                deadline = (pub_date + timedelta(days=60)).strftime('%Y-%m-%d')
            
            # Handle agencies field which might be list of dicts
            agencies = doc.get('agencies', [])
            if isinstance(agencies, list) and agencies:
                if isinstance(agencies[0], dict):
                    funder_name = ', '.join([a.get('name', 'Federal Agency') for a in agencies])
                else:
                    funder_name = ', '.join(agencies)
            else:
                funder_name = 'Federal Agency'
            
            return {
                'title': doc.get('title', 'Untitled Grant'),
                'description': doc.get('abstract', doc.get('title', '')),
                'funder_name': funder_name,
                'amount': self.extract_amount_from_text(doc.get('abstract', '')),
                'deadline': deadline,
                'source_name': 'Federal Register',
                'source_url': doc.get('html_url', ''),
                'eligibility': self.extract_eligibility(doc.get('abstract', '')),
                'focus_area': self.categorize_grant(doc.get('title', '') + ' ' + doc.get('abstract', '')),
                'match_score': None,  # Will be calculated later
                'status': 'active'
            }
        except Exception as e:
            logger.error(f"Error parsing Federal Register grant: {e}")
            return None
    
    def fetch_usaspending_grants(self, limit: int = 30) -> List[Dict]:
        """Fetch grant opportunities from USAspending"""
        grants = []
        
        # API endpoint for assistance listings
        url = 'https://api.usaspending.gov/api/v2/assistance/awards/'
        
        payload = {
            'filters': {
                'award_type_codes': ['02', '03', '04', '05'],  # Grant types
                'time_period': [{
                    'start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'end_date': datetime.now().strftime('%Y-%m-%d')
                }]
            },
            'limit': limit,
            'page': 1
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for award in data.get('results', []):
                    grant = self.parse_usaspending_grant(award)
                    if grant:
                        grants.append(grant)
        except Exception as e:
            logger.error(f"USAspending API error: {e}")
        
        return grants
    
    def parse_usaspending_grant(self, award: Dict) -> Optional[Dict]:
        """Parse USAspending award into grant format"""
        try:
            return {
                'title': award.get('award_description', 'Federal Grant Opportunity'),
                'description': award.get('award_description', ''),
                'funder_name': award.get('awarding_agency_name', 'Federal Agency'),
                'amount': float(award.get('total_obligation', 0)),
                'deadline': None,  # USAspending doesn't provide deadlines
                'source_name': 'USAspending',
                'source_url': f"https://www.usaspending.gov/award/{award.get('generated_unique_award_id', '')}",
                'eligibility': award.get('recipient_name', ''),
                'focus_area': award.get('cfda_title', 'General'),
                'match_score': None,
                'status': 'active'
            }
        except Exception as e:
            logger.error(f"Error parsing USAspending grant: {e}")
            return None
    
    def fetch_candid_grants(self, limit: int = 30, state: Optional[str] = None) -> List[Dict]:
        """Fetch grants from Candid API using transactions endpoint"""
        if not self.candid_client:
            return []
        
        grants = []
        
        try:
            # Use proper transactions method with geoname ID for location
            location_id = None
            if state:
                location_id = get_geoname_id(state)
            
            # Search with different keywords to get variety
            keywords = ['nonprofit', 'community', 'education', 'health', 'youth']
            for keyword in keywords[:2]:  # Limit to avoid too many API calls
                # Use the transactions method with proper parameters
                results = self.candid_client.transactions(
                    query=keyword,
                    location=location_id,  # Pass geoname ID if we have state
                    page=1
                )
                
                # Parse the results
                if isinstance(results, list):
                    for result in results[:limit//2]:  # Split limit across keywords
                        grant = self.parse_candid_grant(result)
                        if grant:
                            grants.append(grant)
                            if len(grants) >= limit:
                                break
                
                if len(grants) >= limit:
                    break
                    
        except Exception as e:
            logger.error(f"Candid API error: {e}")
        
        return grants[:limit]
    
    def parse_candid_grant(self, result: Dict) -> Optional[Dict]:
        """Parse Candid grant transaction into standard format - NULL SAFE"""
        try:
            # Safely extract funder name
            funder = result.get('funder_name')
            if not funder and result.get('funder'):
                # Handle case where funder is a dict or object
                funder_obj = result.get('funder')
                if isinstance(funder_obj, dict):
                    funder = funder_obj.get('name', 'Private Foundation')
                else:
                    funder = str(funder_obj)
            if not funder:
                funder = 'Private Foundation'
            
            # Safely extract description/title with fallback
            title = result.get('description') or result.get('title') or 'Foundation Grant'
            
            return {
                'title': title,
                'description': result.get('description', ''),
                'funder_name': funder,
                'amount': result.get('amount') or result.get('amount_awarded') or 0,
                'deadline': result.get('deadline') or result.get('grant_date'),
                'source_name': 'Candid',
                'source_url': result.get('url') or result.get('link') or '',
                'eligibility': result.get('eligibility_description') or result.get('recipient_name') or '',
                'focus_area': (result.get('focus_area') or result.get('description') or 'General')[:100],
                'match_score': None,
                'status': 'active'
            }
        except Exception as e:
            logger.error(f"Error parsing Candid grant: {e}")
            logger.debug(f"Problematic result data: {result}")
            return None
    
    def extract_amount_from_text(self, text: str) -> Optional[float]:
        """Extract grant amount from text using patterns"""
        import re
        
        # Look for dollar amounts
        patterns = [
            r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|M))?',
            r'[\d,]+(?:\.\d{2})?\s*(?:USD|dollars?)',
            r'up to \$[\d,]+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group()
                # Clean and convert
                amount_str = amount_str.replace('$', '').replace(',', '').replace('USD', '').strip()
                
                if 'million' in amount_str.lower() or 'M' in amount_str:
                    amount_str = amount_str.replace('million', '').replace('M', '').strip()
                    return float(amount_str) * 1000000
                
                try:
                    return float(amount_str)
                except:
                    pass
        
        return None
    
    def extract_eligibility(self, text: str) -> str:
        """Extract eligibility information from text"""
        keywords = ['nonprofit', '501(c)(3)', 'eligible', 'must be', 'required', 
                   'qualification', 'criteria']
        
        sentences = text.split('.')
        relevant = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                relevant.append(sentence.strip())
        
        return '. '.join(relevant[:2]) if relevant else 'See full announcement for eligibility'
    
    def categorize_grant(self, text: str) -> str:
        """Categorize grant based on text content"""
        categories = {
            'Education': ['education', 'school', 'student', 'learning', 'academic'],
            'Health': ['health', 'medical', 'hospital', 'clinic', 'wellness'],
            'Community': ['community', 'neighborhood', 'local', 'civic'],
            'Arts': ['arts', 'culture', 'museum', 'performance', 'creative'],
            'Environment': ['environment', 'climate', 'conservation', 'green'],
            'Technology': ['technology', 'digital', 'innovation', 'STEM'],
            'Social Services': ['social', 'welfare', 'homeless', 'poverty'],
            'Youth': ['youth', 'children', 'adolescent', 'teen']
        }
        
        text_lower = text.lower()
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'General'
    def extract_deadline_from_text(self, text: str) -> Optional[str]:
        """Extract deadline dates from grant description text using AI or regex"""
        import re
        from datetime import datetime

        if not text:
            return None

        # Pattern 1: Month Day, Year (e.g., "December 31, 2025")
        pattern1 = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'

        # Pattern 2: MM/DD/YYYY or MM-DD-YYYY
        pattern2 = r'\d{1,2}[/-]\d{1,2}[/-]\d{4}'

        # Pattern 3: "due by" or "deadline" followed by date
        deadline_keywords = r'(?:deadline|due by|submit by|closing date|application due)[\s:]+([^\n\.]{1,50})'

        patterns = [pattern1, pattern2, deadline_keywords]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return first match, cleaned
                date_str = matches[0].strip() if isinstance(matches[0], str) else matches[0][0].strip()
                return date_str[:50]  # Limit length

        return None
    
    def parse_flexible_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date with multiple format support"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        # Try different date formats
        formats = [
            '%Y-%m-%d',           # 2025-10-12
            '%Y/%m/%d',           # 2025/10/12
            '%m/%d/%Y',           # 10/12/2025
            '%Y-%m-%dT%H:%M:%S',  # ISO format with time
            '%Y'                  # Year only (2003)
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # If year-only, use December 31st of that year
                if fmt == '%Y':
                    return date(dt.year, 12, 31)
                return dt.date()
            except ValueError:
                continue
        
        # If all formats fail, log and return None
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def store_grants(self, grants: List[Dict]) -> int:
        """Store grants in database"""
        stored = 0
        
        for grant_data in grants:
            try:
                # Check if grant already exists
                existing = db.session.query(Grant).filter_by(
                    title=grant_data['title'],
                    funder=grant_data['funder_name']
                ).first()
                
                if not existing:
                    amount = grant_data.get('amount')
                    deadline_str = grant_data.get('deadline')
                    
                    # Create grant object
                    grant = Grant()
                    grant.title = grant_data['title']
                    grant.funder = grant_data['funder_name']
                    grant.amount_min = amount if amount else None
                    grant.amount_max = amount if amount else None
                    grant.deadline = self.parse_flexible_date(deadline_str)
                    grant.source_name = grant_data.get('source_name')
                    grant.source_url = grant_data.get('source_url')
                    grant.eligibility = grant_data.get('eligibility')
                    grant.geography = grant_data.get('geography', 'National')
                    grant.status = 'active'
                    grant.created_at = datetime.utcnow()
                    
                    db.session.add(grant)
                    stored += 1
            except Exception as e:
                logger.error(f"Error storing grant: {e}")
                db.session.rollback()
        
        try:
            db.session.commit()
            logger.info(f"Stored {stored} new grants in database")
        except Exception as e:
            logger.error(f"Error committing grants: {e}")
            db.session.rollback()
        
        return stored
    
    def calculate_match_scores(self, org_id: Optional[int] = None):
        """Calculate match scores for all grants"""
        try:
            grants = db.session.query(Grant).filter_by(status='active').all()
            
            if org_id:
                org = db.session.query(Organization).get(org_id)
                if org and self.ai_service.is_enabled():
                    for grant in grants:
                        score, explanation = self.ai_service.match_grant(
                            org.to_dict(),
                            grant.to_dict()
                        )
                        grant.match_score = score
                        grant.match_reason = explanation
            
            db.session.commit()
            logger.info(f"Calculated match scores for {len(grants)} grants")
        except Exception as e:
            logger.error(f"Error calculating match scores: {e}")
            db.session.rollback()