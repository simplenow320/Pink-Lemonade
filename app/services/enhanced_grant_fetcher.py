"""
Enhanced grant fetcher that collects comprehensive data for robust AI analysis
"""
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)

class EnhancedGrantFetcher:
    """
    Enhanced grant fetcher that gathers comprehensive grant data including:
    - Detailed eligibility criteria
    - Application requirements
    - Funding priorities
    - Geographic restrictions
    - Contact information
    - Application deadlines and processes
    """
    
    def __init__(self):
        self.sources = {
            'federal_register': self.fetch_federal_register_detailed,
            'usaspending': self.fetch_usaspending_detailed,
            'foundation_directory': self.fetch_foundation_opportunities,
            'state_grants': self.fetch_state_grant_opportunities
        }
    
    def fetch_comprehensive_grants(self, keyword: str = 'nonprofit', limit: int = 20) -> List[Dict]:
        """
        Fetch grants with comprehensive details from multiple sources
        """
        all_grants = []
        
        for source_name, fetch_func in self.sources.items():
            try:
                logger.info(f"Fetching from {source_name}...")
                grants = fetch_func(keyword, limit // len(self.sources))
                for grant in grants:
                    grant['source'] = source_name
                all_grants.extend(grants)
            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {e}")
                continue
        
        return all_grants[:limit]
    
    def fetch_federal_register_detailed(self, keyword: str, limit: int) -> List[Dict]:
        """
        Fetch detailed federal grant information including full eligibility criteria
        """
        url = 'https://www.federalregister.gov/api/v1/documents'
        
        params = {
            'conditions[term]': f'{keyword} grant funding',
            'conditions[type][]': ['NOTICE', 'RULE'],
            'conditions[agencies][]': [
                'education-department',
                'health-and-human-services-department', 
                'agriculture-department',
                'housing-and-urban-development-department',
                'justice-department'
            ],
            'per_page': limit,
            'order': 'newest',
            'fields[]': ['title', 'abstract', 'agencies', 'publication_date', 'html_url', 'body_html_url']
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            detailed_grants = []
            for doc in data.get('results', []):
                # Fetch detailed content for each grant
                detailed_grant = self._extract_detailed_federal_grant(doc)
                if detailed_grant:
                    detailed_grants.append(detailed_grant)
            
            return detailed_grants
            
        except Exception as e:
            logger.error(f"Error fetching Federal Register grants: {e}")
            return []
    
    def _extract_detailed_federal_grant(self, doc: Dict) -> Optional[Dict]:
        """
        Extract comprehensive details from a federal grant notice
        """
        try:
            title = doc.get('title', '')
            abstract = doc.get('abstract', '') or ''
            
            # Skip if not actually a grant opportunity
            grant_keywords = ['grant', 'funding', 'award', 'assistance', 'opportunity', 'application']
            if not any(keyword.lower() in title.lower() or keyword.lower() in abstract.lower() 
                      for keyword in grant_keywords):
                return None
            
            agencies = doc.get('agencies', [])
            funder = agencies[0].get('name', 'Federal Agency') if agencies else 'Federal Agency'
            
            # Extract key information using patterns
            amount_info = self._extract_funding_amounts(abstract)
            deadline_info = self._extract_deadlines(abstract)
            eligibility_info = self._extract_eligibility(abstract)
            requirements_info = self._extract_requirements(abstract)
            
            return {
                'title': title,
                'funder': funder,
                'description': abstract[:1000],  # First 1000 chars
                'link': doc.get('html_url', ''),
                'publication_date': doc.get('publication_date'),
                'deadline': deadline_info.get('deadline'),
                'amount_min': amount_info.get('min_amount'),
                'amount_max': amount_info.get('max_amount'),
                'total_funding': amount_info.get('total_funding'),
                'eligibility_criteria': eligibility_info,
                'application_requirements': requirements_info,
                'agency_contact': self._extract_contact_info(abstract),
                'cfda_number': self._extract_cfda_number(abstract),
                'geographic_scope': self._extract_geographic_scope(abstract),
                'program_areas': self._extract_program_areas(abstract, title),
                'match_required': self._extract_match_requirements(abstract),
                'application_deadline_type': deadline_info.get('deadline_type', 'Not specified')
            }
            
        except Exception as e:
            logger.error(f"Error extracting grant details: {e}")
            return None
    
    def _extract_funding_amounts(self, text: str) -> Dict:
        """Extract funding amounts from grant text"""
        amounts = {'min_amount': None, 'max_amount': None, 'total_funding': None}
        
        # Pattern for dollar amounts
        amount_patterns = [
            r'\$([0-9,]+(?:\.[0-9]{2})?)\s*(?:million|mil)?',
            r'([0-9,]+)\s*dollars?',
            r'up\s+to\s+\$([0-9,]+)',
            r'maximum\s+(?:of\s+)?\$([0-9,]+)',
            r'total\s+funding\s+(?:of\s+)?\$([0-9,]+)'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    amount = float(matches[0].replace(',', ''))
                    if 'million' in text.lower():
                        amount *= 1000000
                    if not amounts['max_amount'] or amount > amounts['max_amount']:
                        amounts['max_amount'] = amount
                    if not amounts['min_amount'] or amount < amounts['min_amount']:
                        amounts['min_amount'] = amount
                except:
                    continue
        
        return amounts
    
    def _extract_deadlines(self, text: str) -> Dict:
        """Extract deadline information"""
        deadline_info = {'deadline': None, 'deadline_type': 'Not specified'}
        
        # Look for date patterns
        date_patterns = [
            r'deadline[:\s]+([A-Za-z]+\s+\d{1,2},\s+\d{4})',
            r'due[:\s]+([A-Za-z]+\s+\d{1,2},\s+\d{4})',
            r'by\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    date_str = matches[0]
                    # Try to parse the date
                    if '/' in date_str:
                        deadline = datetime.strptime(date_str, '%m/%d/%Y').date()
                    elif '-' in date_str:
                        deadline = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        deadline = datetime.strptime(date_str, '%B %d, %Y').date()
                    
                    deadline_info['deadline'] = deadline.isoformat()
                    deadline_info['deadline_type'] = 'Application deadline'
                    break
                except:
                    continue
        
        return deadline_info
    
    def _extract_eligibility(self, text: str) -> str:
        """Extract eligibility criteria"""
        eligibility_patterns = [
            r'eligib(?:le|ility)[^.]*?[.!?]',
            r'applicants?\s+must[^.]*?[.!?]',
            r'qualified\s+(?:organizations?|entities?)[^.]*?[.!?]',
            r'501\(c\)\(3\)[^.]*?[.!?]'
        ]
        
        eligibility_info = []
        for pattern in eligibility_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            eligibility_info.extend(matches)
        
        return ' '.join(eligibility_info[:3])  # First 3 relevant sentences
    
    def _extract_requirements(self, text: str) -> str:
        """Extract application requirements"""
        requirement_patterns = [
            r'require(?:ments?|d)[^.]*?[.!?]',
            r'must\s+(?:submit|provide|include)[^.]*?[.!?]',
            r'application[^.]*?[.!?]',
            r'proposal[^.]*?[.!?]'
        ]
        
        requirements = []
        for pattern in requirement_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            requirements.extend(matches)
        
        return ' '.join(requirements[:3])  # First 3 relevant sentences
    
    def _extract_contact_info(self, text: str) -> str:
        """Extract contact information"""
        contact_patterns = [
            r'contact[^.]*?[.!?]',
            r'(?:email|e-mail)[^.]*?[.!?]',
            r'phone[^.]*?[.!?]'
        ]
        
        contact_info = []
        for pattern in contact_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            contact_info.extend(matches)
        
        return ' '.join(contact_info[:2])
    
    def _extract_cfda_number(self, text: str) -> Optional[str]:
        """Extract CFDA catalog number"""
        cfda_pattern = r'CFDA\s*(?:Number)?[:\s]*([0-9]{2}\.[0-9]{3})'
        matches = re.findall(cfda_pattern, text, re.IGNORECASE)
        return matches[0] if matches else None
    
    def _extract_geographic_scope(self, text: str) -> str:
        """Extract geographic scope/restrictions"""
        geo_patterns = [
            r'state(?:s)?\s+of[^.]*?[.!?]',
            r'geographic[^.]*?[.!?]',
            r'nationwide|national|local|regional',
            r'rural|urban|tribal'
        ]
        
        geo_info = []
        for pattern in geo_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            geo_info.extend(matches)
        
        return ' '.join(geo_info[:2])
    
    def _extract_program_areas(self, text: str, title: str) -> str:
        """Extract program focus areas"""
        program_keywords = [
            'education', 'health', 'housing', 'environment', 'arts', 'technology',
            'workforce', 'community', 'youth', 'seniors', 'disability', 'mental health',
            'substance abuse', 'homelessness', 'food security', 'transportation'
        ]
        
        found_areas = []
        combined_text = f"{title} {text}".lower()
        
        for keyword in program_keywords:
            if keyword in combined_text:
                found_areas.append(keyword.title())
        
        return ', '.join(found_areas[:5])
    
    def _extract_match_requirements(self, text: str) -> bool:
        """Extract if matching funds are required"""
        match_patterns = [
            r'match(?:ing)?\s+(?:funds?|requirement)',
            r'cost\s+shar(?:e|ing)',
            r'local\s+match'
        ]
        
        for pattern in match_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def fetch_usaspending_detailed(self, keyword: str, limit: int) -> List[Dict]:
        """
        Fetch detailed information from USAspending API
        This provides historical funding data and patterns
        """
        # Implementation for USAspending detailed fetch
        return []
    
    def fetch_foundation_opportunities(self, keyword: str, limit: int) -> List[Dict]:
        """
        Fetch foundation grant opportunities (would need Foundation Directory API access)
        """
        # Placeholder for foundation directory integration
        return []
    
    def fetch_state_grant_opportunities(self, keyword: str, limit: int) -> List[Dict]:
        """
        Fetch state-level grant opportunities
        """
        # Placeholder for state grant databases
        return []

# Initialize the enhanced fetcher
enhanced_grant_fetcher = EnhancedGrantFetcher()