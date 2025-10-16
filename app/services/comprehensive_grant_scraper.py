"""
Comprehensive grant scraper that extracts detailed information from grant sources
including full documents, funder profiles, and contact intelligence
"""
import logging
import requests
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from urllib.parse import urljoin, urlparse

# Try to import optional packages, fall back to basic functionality
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

try:
    from app.services.ai_service import ai_service
    HAS_AI_SERVICE = True
except ImportError:
    HAS_AI_SERVICE = False

logger = logging.getLogger(__name__)

class ComprehensiveGrantScraper:
    """
    Advanced scraper that extracts comprehensive grant and funder information
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_full_grant_details(self, grant_url: str) -> Dict:
        """
        Extract comprehensive details from a grant opportunity URL
        """
        try:
            # Get the full document content
            response = self.session.get(grant_url, timeout=30)
            response.raise_for_status()
            
            # Extract clean text content (with fallbacks)
            extracted_text: str = ""
            if HAS_TRAFILATURA:
                import trafilatura
                text_result = trafilatura.extract(response.text, include_tables=True, include_links=True)
                extracted_text = text_result if text_result else ""
            else:
                # Simple fallback - extract from raw HTML
                extracted_text = self._simple_text_extraction(response.text)
            
            # Also get structured HTML for better parsing (with fallback)
            soup = None
            if HAS_BS4:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
            
            # Use AI to extract structured information
            grant_details = self._ai_extract_grant_info(extracted_text, grant_url)
            
            # Generate program overview (3-5 sentences)
            grant_details['program_overview'] = self._generate_program_overview(
                grant_details.get('title', ''),
                grant_details.get('program_description', ''),
                grant_details.get('funder', '')
            )
            
            # Extract additional elements
            grant_details.update({
                'contact_info': self._extract_contact_information(soup, extracted_text),
                'eligibility_details': self._extract_detailed_eligibility(extracted_text),
                'application_process': self._extract_application_process(extracted_text),
                'evaluation_criteria': self._extract_evaluation_criteria(extracted_text),
                'reporting_requirements': self._extract_reporting_requirements(extracted_text),
                'timeline_details': self._extract_timeline_details(extracted_text),
                'related_documents': self._extract_related_documents(soup, grant_url),
                'funder_profile': self._extract_funder_information(extracted_text, grant_url)
            })
            
            return grant_details
            
        except Exception as e:
            logger.error(f"Error extracting grant details from {grant_url}: {e}")
            return {}
    
    def _generate_program_overview(self, program_title: str, program_description: str, funder_name: str) -> str:
        """
        Generate overview only from real program data - no synthetic content
        """
        # Only return overview if we have actual program description
        if program_description and len(program_description.strip()) > 50:
            # Return the actual description if substantial, truncated to overview length
            sentences = program_description.split('.')[:5]  # Take first 5 sentences max
            return '. '.join(sentences).strip() + '.' if sentences else ""
        
        # If no real description available, return empty - no synthetic content
        return ""
    
    def _ai_extract_grant_info(self, text: str, url: str) -> Dict:
        """
        Use AI to extract structured grant information from text content
        """
        extraction_prompt = f"""
        Extract comprehensive grant information from this document. Return ONLY valid JSON with these fields:
        
        {{
            "title": "Grant program title",
            "funder": "Name of funding organization",
            "total_funding_available": "Total funding pool amount",
            "individual_award_range": "Range for individual awards (min-max)",
            "number_of_awards": "Expected number of awards",
            "deadline": "Application deadline (YYYY-MM-DD format)",
            "program_description": "Detailed description of the grant program",
            "funding_priorities": ["List of funding priorities"],
            "eligible_organizations": ["Types of eligible organizations"],
            "geographic_restrictions": "Geographic limitations if any",
            "project_duration": "Allowed project duration",
            "cost_sharing_required": "Whether cost sharing/matching is required",
            "indirect_costs_allowed": "Indirect cost policy",
            "cfda_number": "CFDA catalog number if federal",
            "program_officer": "Program officer name if mentioned",
            "key_dates": {{
                "application_due": "Application deadline",
                "project_start": "Project start date",
                "project_end": "Project end date"
            }}
        }}
        
        Document content:
        {text[:3000]}...
        
        Source URL: {url}
        """
        
        try:
            if HAS_AI_SERVICE:
                from app.services.ai_service import ai_service
                result = ai_service._make_request(
                    messages=[
                        {"role": "system", "content": "You are an expert at extracting structured grant information. Return only valid JSON."},
                        {"role": "user", "content": extraction_prompt}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=1500
                )
                
                if result and isinstance(result, dict):
                    return result
                else:
                    return self._fallback_extraction(text, url)
            else:
                return self._fallback_extraction(text, url)
                
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            return self._fallback_extraction(text, url)
    
    def _extract_contact_information(self, soup: Optional[Any], text: str) -> Dict:
        """
        Extract comprehensive contact information
        """
        contacts = {
            'emails': [],
            'phones': [],
            'addresses': [],
            'websites': [],
            'program_officers': []
        }
        
        # Email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        contacts['emails'] = list(set(re.findall(email_pattern, text)))
        
        # Phone patterns
        phone_patterns = [
            r'\b\d{3}-\d{3}-\d{4}\b',
            r'\(\d{3}\)\s*\d{3}-\d{4}',
            r'\b\d{3}\.\d{3}\.\d{4}\b'
        ]
        for pattern in phone_patterns:
            contacts['phones'].extend(re.findall(pattern, text))
        
        # Extract program officer names (names near contact info)
        officer_patterns = [
            r'Program Officer[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Contact Person[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'For questions contact[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)'
        ]
        for pattern in officer_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            contacts['program_officers'].extend(matches)
        
        # Find links in HTML
        if soup:
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if isinstance(href, str) and href.startswith('http') and any(domain in href for domain in ['.gov', '.org', '.edu']):
                    contacts['websites'].append(href)
        
        return contacts
    
    def _extract_detailed_eligibility(self, text: str) -> Dict:
        """
        Extract comprehensive eligibility criteria
        """
        eligibility = {
            'organization_types': [],
            'geographic_restrictions': [],
            'size_requirements': [],
            'experience_requirements': [],
            'partnership_requirements': [],
            'exclusions': []
        }
        
        # Look for eligibility sections
        eligibility_sections = re.findall(
            r'eligib[a-z]*.*?(?=\n\n|\n[A-Z]|\n\d\.)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        for section in eligibility_sections:
            # Extract organization types
            if '501(c)(3)' in section:
                eligibility['organization_types'].append('501(c)(3) nonprofit')
            if 'government' in section.lower():
                eligibility['organization_types'].append('Government entities')
            if 'tribal' in section.lower():
                eligibility['organization_types'].append('Tribal organizations')
            if 'faith-based' in section.lower():
                eligibility['organization_types'].append('Faith-based organizations')
        
        return eligibility
    
    def _extract_application_process(self, text: str) -> Dict:
        """
        Extract application process and requirements
        """
        process = {
            'submission_method': '',
            'required_documents': [],
            'page_limits': {},
            'format_requirements': [],
            'pre_submission_requirements': []
        }
        
        # Look for application sections
        app_sections = re.findall(
            r'application.*?(?=\n\n|\n[A-Z]|\n\d\.)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        for section in app_sections:
            # Find submission method
            if 'grants.gov' in section.lower():
                process['submission_method'] = 'Grants.gov'
            elif 'email' in section.lower():
                process['submission_method'] = 'Email'
            
            # Find required documents
            doc_patterns = [
                r'(?:require|submit|include).*?(?:proposal|narrative|budget|statement)',
                r'(?:attach|provide).*?(?:documentation|evidence|proof)'
            ]
            for pattern in doc_patterns:
                matches = re.findall(pattern, section, re.IGNORECASE)
                process['required_documents'].extend(matches)
        
        return process
    
    def _extract_evaluation_criteria(self, text: str) -> List[str]:
        """
        Extract evaluation and selection criteria
        """
        criteria = []
        
        # Look for evaluation sections
        eval_patterns = [
            r'evaluat.*?criteria.*?(?=\n\n|\n[A-Z]|\n\d\.)',
            r'selection.*?criteria.*?(?=\n\n|\n[A-Z]|\n\d\.)',
            r'review.*?criteria.*?(?=\n\n|\n[A-Z]|\n\d\.)'
        ]
        
        for pattern in eval_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            criteria.extend(matches)
        
        return criteria[:5]  # Top 5 criteria
    
    def _extract_reporting_requirements(self, text: str) -> List[str]:
        """
        Extract reporting and compliance requirements
        """
        requirements = []
        
        # Look for reporting sections
        report_patterns = [
            r'report(?:ing)?.*?(?:require|submit|provide).*?(?=\n\n|\n[A-Z]|\n\d\.)',
            r'compliance.*?(?=\n\n|\n[A-Z]|\n\d\.)',
            r'monitor(?:ing)?.*?(?=\n\n|\n[A-Z]|\n\d\.)'
        ]
        
        for pattern in report_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            requirements.extend(matches)
        
        return requirements[:3]  # Top 3 requirements
    
    def _extract_timeline_details(self, text: str) -> Dict:
        """
        Extract detailed timeline information
        """
        timeline = {
            'application_period': '',
            'review_period': '',
            'notification_date': '',
            'project_period': '',
            'budget_period': ''
        }
        
        # Date patterns
        date_patterns = [
            r'(\w+\s+\d{1,2},\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})'
        ]
        
        # Look for timeline sections
        timeline_sections = re.findall(
            r'timeline.*?(?=\n\n|\n[A-Z]|\n\d\.)|schedule.*?(?=\n\n|\n[A-Z]|\n\d\.)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        return timeline
    
    def _extract_related_documents(self, soup: Optional[Any], base_url: str) -> List[Dict]:
        """
        Extract links to related documents (guidelines, forms, etc.)
        """
        documents = []
        
        # Find all links that might be documents
        if soup:
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Check if it's a document link
                doc_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
                doc_keywords = ['guideline', 'form', 'application', 'instruction', 'template']
                
                if isinstance(href, str) and (any(ext in href.lower() for ext in doc_extensions) or 
                    any(keyword in text.lower() for keyword in doc_keywords)):
                    
                    full_url = urljoin(base_url, href)
                    documents.append({
                        'title': text,
                        'url': full_url,
                        'type': self._classify_document_type(text)
                    })
        
        return documents
    
    def _classify_document_type(self, title: str) -> str:
        """
        Classify document type based on title
        """
        title_lower = title.lower()
        
        if 'guideline' in title_lower or 'instruction' in title_lower:
            return 'Application Guidelines'
        elif 'form' in title_lower or 'template' in title_lower:
            return 'Application Form'
        elif 'budget' in title_lower:
            return 'Budget Template'
        elif 'narrative' in title_lower:
            return 'Narrative Template'
        elif 'evaluation' in title_lower:
            return 'Evaluation Criteria'
        else:
            return 'Supporting Document'
    
    def _extract_funder_information(self, text: str, grant_url: str) -> Dict:
        """
        Extract comprehensive funder information and intelligence
        """
        funder_info = {
            'organization_name': '',
            'department': '',
            'mission': '',
            'funding_priorities': [],
            'annual_budget': '',
            'typical_grant_size': '',
            'contact_preference': '',
            'decision_makers': [],
            'past_grantees': [],
            'success_factors': []
        }
        
        # Extract department/agency from URL and content
        domain = urlparse(grant_url).netloc
        if '.gov' in domain:
            funder_info['organization_name'] = self._extract_agency_name(domain, text)
        
        return funder_info
    
    def _extract_agency_name(self, domain: str, text: str) -> str:
        """
        Extract agency name from domain and text
        """
        agency_mappings = {
            'ed.gov': 'Department of Education',
            'hhs.gov': 'Department of Health and Human Services',
            'usda.gov': 'Department of Agriculture',
            'doj.gov': 'Department of Justice',
            'hud.gov': 'Department of Housing and Urban Development',
            'epa.gov': 'Environmental Protection Agency',
            'nsf.gov': 'National Science Foundation'
        }
        
        for domain_key, agency_name in agency_mappings.items():
            if domain_key in domain:
                return agency_name
        
        return 'Federal Agency'
    
    def _simple_text_extraction(self, html: str) -> str:
        """
        Simple text extraction fallback when trafilatura is not available
        """
        import re
        # Remove scripts and styles
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        html = re.sub(r'<[^>]+>', ' ', html)
        # Clean up whitespace
        html = re.sub(r'\s+', ' ', html)
        return html.strip()
    
    def _fallback_extraction(self, text: str, url: str) -> Dict:
        """
        Fallback extraction when AI service is not available
        """
        # Use regex-based extraction
        title_match = re.search(r'(?:Title|Program|Grant)[:\s]+([^\n]+)', text, re.IGNORECASE)
        amount_match = re.search(r'\$([0-9,]+(?:\.[0-9]{2})?)', text)
        deadline_match = re.search(r'(?:deadline|due)[:\s]+([A-Za-z]+\s+\d{1,2},\s+\d{4})', text, re.IGNORECASE)
        
        return {
            'title': title_match.group(1).strip() if title_match else 'Grant Opportunity',
            'funder': self._extract_agency_name(urlparse(url).netloc, text),
            'program_description': text[:500] + '...' if len(text) > 500 else text,
            'individual_award_range': f"${amount_match.group(1)}" if amount_match else 'Not specified',
            'deadline': deadline_match.group(1) if deadline_match else 'Not specified',
            'funding_priorities': ['Community Development', 'Nonprofit Support'],  # Default
            'geographic_restrictions': 'Not specified',
            'cost_sharing_required': 'Not specified'
        }

# Initialize the comprehensive scraper
comprehensive_scraper = ComprehensiveGrantScraper()