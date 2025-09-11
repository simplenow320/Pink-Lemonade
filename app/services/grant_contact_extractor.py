"""
Grant Contact Information Extraction Service
Extracts phone numbers, emails, contact names, and application links from grant data
"""

import re
import json
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
import urllib.parse

logger = logging.getLogger(__name__)

class GrantContactExtractor:
    """Extract and enrich grant data with contact information"""
    
    def __init__(self):
        # Email pattern - comprehensive
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Phone pattern - supports various formats
        self.phone_pattern = re.compile(
            r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})(?:\s?(?:ext|x|extension)\.?\s?(\d+))?'
        )
        
        # URL pattern for websites and application links
        self.url_pattern = re.compile(
            r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        )
        
        # Contact name patterns
        self.contact_patterns = [
            re.compile(r'(?:contact|program officer|grant administrator|point of contact):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', re.IGNORECASE),
            re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*,?\s*(?:Program Officer|Grant Administrator|Contact)', re.IGNORECASE),
            re.compile(r'(?:please contact|for information contact|contact person):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', re.IGNORECASE)
        ]
        
        # Department patterns
        self.dept_patterns = [
            re.compile(r'(?:department|division|office|bureau) of ([A-Za-z\s]+?)(?:\.|,|;|$)', re.IGNORECASE),
            re.compile(r'([A-Za-z\s]+?)(?:department|division|office|bureau)', re.IGNORECASE)
        ]
    
    def extract_from_grant(self, grant: Dict) -> Dict:
        """
        Extract contact information from a grant record
        
        Args:
            grant: Grant dictionary with various fields
            
        Returns:
            Dictionary with extracted contact information
        """
        contact_info = {
            'contact_name': None,
            'contact_email': None,
            'contact_phone': None,
            'contact_department': None,
            'organization_website': None,
            'application_url': None,
            'alternate_contact': {},
            'contact_confidence': 'low',
            'contact_verified_date': None
        }
        
        # Combine all text fields for searching
        search_text = self._combine_text_fields(grant)
        
        # Extract emails
        emails = self._extract_emails(search_text)
        if emails:
            contact_info['contact_email'] = emails[0]  # Primary email
            if len(emails) > 1:
                contact_info['alternate_contact']['email'] = emails[1]
        
        # Extract phone numbers
        phones = self._extract_phones(search_text)
        if phones:
            contact_info['contact_phone'] = phones[0]  # Primary phone
            if len(phones) > 1:
                contact_info['alternate_contact']['phone'] = phones[1]
        
        # Extract contact names
        names = self._extract_contact_names(search_text)
        if names:
            contact_info['contact_name'] = names[0]
            if len(names) > 1:
                contact_info['alternate_contact']['name'] = names[1]
        
        # Extract department
        dept = self._extract_department(search_text)
        if dept:
            contact_info['contact_department'] = dept
        
        # Extract URLs
        urls = self._extract_urls(search_text)
        contact_info['organization_website'], contact_info['application_url'] = self._classify_urls(urls, grant)
        
        # Process source-specific data
        contact_info = self._process_source_specific(grant, contact_info)
        
        # Calculate confidence score
        contact_info['contact_confidence'] = self._calculate_confidence(contact_info)
        
        # Set verification date if we found any contact info
        if any([contact_info['contact_email'], contact_info['contact_phone'], contact_info['contact_name']]):
            contact_info['contact_verified_date'] = datetime.utcnow()
        
        return contact_info
    
    def _combine_text_fields(self, grant: Dict) -> str:
        """Combine all text fields from grant for searching"""
        text_fields = []
        
        # Add standard fields
        for field in ['description', 'eligibility', 'requirements_summary', 'ai_summary', 
                     'funder', 'title', 'source_url', 'link']:
            if field in grant and grant[field]:
                text_fields.append(str(grant[field]))
        
        # Add JSON fields if they exist
        if 'contact_info' in grant and grant['contact_info']:
            if isinstance(grant['contact_info'], dict):
                text_fields.append(json.dumps(grant['contact_info']))
            else:
                text_fields.append(str(grant['contact_info']))
        
        return ' '.join(text_fields)
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        emails = self.email_pattern.findall(text)
        # Filter out common non-contact emails
        filtered = []
        for email in emails:
            lower_email = email.lower()
            if not any(skip in lower_email for skip in ['noreply', 'donotreply', 'example.com', 'test.com']):
                filtered.append(email)
        return list(set(filtered))[:2]  # Return up to 2 unique emails
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        phones = []
        matches = self.phone_pattern.finditer(text)
        for match in matches:
            area, exchange, number = match.groups()[:3]
            ext = match.group(4)
            
            # Format phone number
            phone = f"({area}) {exchange}-{number}"
            if ext:
                phone += f" ext. {ext}"
            phones.append(phone)
        
        return list(set(phones))[:2]  # Return up to 2 unique phones
    
    def _extract_contact_names(self, text: str) -> List[str]:
        """Extract contact person names from text"""
        names = []
        for pattern in self.contact_patterns:
            matches = pattern.findall(text)
            names.extend(matches)
        
        # Filter and clean names
        cleaned_names = []
        for name in names:
            # Remove common false positives
            if len(name.split()) >= 2 and len(name) < 50:
                if not any(skip in name.lower() for skip in ['grant', 'program', 'office', 'department']):
                    cleaned_names.append(name.strip())
        
        return list(set(cleaned_names))[:2]  # Return up to 2 unique names
    
    def _extract_department(self, text: str) -> Optional[str]:
        """Extract department or division name"""
        for pattern in self.dept_patterns:
            match = pattern.search(text)
            if match:
                dept = match.group(1).strip()
                # Clean up and validate
                if len(dept) > 3 and len(dept) < 100:
                    return dept
        return None
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        urls = self.url_pattern.findall(text)
        # Remove duplicates and limit
        return list(set(urls))[:5]
    
    def _classify_urls(self, urls: List[str], grant: Dict) -> tuple:
        """Classify URLs as organization website or application link"""
        org_website = None
        app_url = None
        
        for url in urls:
            lower_url = url.lower()
            
            # Check for application-specific keywords
            if any(keyword in lower_url for keyword in ['apply', 'application', 'submit', 'portal', 'register']):
                if not app_url:  # Take first application URL
                    app_url = url
            # Check for organization website patterns
            elif any(keyword in lower_url for keyword in ['.gov', '.org', '.edu']) and not app_url:
                if not org_website:  # Take first org website
                    org_website = url
        
        # If we have a source_url or link in grant, use it
        if not app_url and 'link' in grant and grant['link']:
            app_url = grant['link']
        if not app_url and 'source_url' in grant and grant['source_url']:
            app_url = grant['source_url']
        
        return org_website, app_url
    
    def _process_source_specific(self, grant: Dict, contact_info: Dict) -> Dict:
        """Process source-specific contact information"""
        source = grant.get('source_name', '').lower()
        
        if 'federal' in source or 'grants.gov' in source:
            # Federal grants often have standard contact patterns
            if grant.get('funder'):
                contact_info['contact_department'] = contact_info['contact_department'] or grant['funder']
            # Federal grants usually have grants.gov as application portal
            if not contact_info['application_url']:
                contact_info['application_url'] = 'https://www.grants.gov'
        
        elif 'candid' in source or 'foundation' in source:
            # Foundation grants may have different patterns
            if grant.get('funder'):
                org_name = grant['funder']
                if not contact_info['organization_website']:
                    # Try to construct foundation website
                    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', org_name.lower())
                    clean_name = clean_name.replace(' foundation', '').replace(' trust', '').strip()
                    clean_name = clean_name.replace(' ', '')
                    contact_info['organization_website'] = f"https://www.{clean_name}.org"
        
        return contact_info
    
    def _calculate_confidence(self, contact_info: Dict) -> str:
        """Calculate confidence score for extracted contact information"""
        score = 0
        
        # Score based on what we found
        if contact_info['contact_email']:
            score += 3
        if contact_info['contact_phone']:
            score += 2
        if contact_info['contact_name']:
            score += 2
        if contact_info['application_url']:
            score += 1
        if contact_info['organization_website']:
            score += 1
        if contact_info['contact_department']:
            score += 1
        
        # Determine confidence level
        if score >= 7:
            return 'high'
        elif score >= 4:
            return 'medium'
        else:
            return 'low'
    
    def extract_with_ai(self, grant: Dict, ai_service: Any) -> Dict:
        """
        Use AI to extract contact information when pattern matching fails
        
        Args:
            grant: Grant dictionary
            ai_service: AI service instance for intelligent extraction
            
        Returns:
            Enhanced contact information
        """
        # First try pattern-based extraction
        contact_info = self.extract_from_grant(grant)
        
        # If confidence is low, try AI extraction
        if contact_info['contact_confidence'] == 'low' and ai_service:
            try:
                # Prepare prompt for AI
                prompt = f"""
                Extract contact information from this grant:
                Title: {grant.get('title', '')}
                Funder: {grant.get('funder', '')}
                Description: {grant.get('description', '')[:500]}
                
                Please extract:
                1. Contact person name
                2. Contact email
                3. Contact phone number
                4. Department or office
                5. Organization website
                6. Application submission link
                
                Format as JSON with keys: contact_name, contact_email, contact_phone, 
                contact_department, organization_website, application_url
                """
                
                ai_response = ai_service.extract_structured_data(prompt)
                if ai_response:
                    # Merge AI results with pattern results
                    for key, value in ai_response.items():
                        if value and not contact_info.get(key):
                            contact_info[key] = value
                    
                    # Recalculate confidence
                    contact_info['contact_confidence'] = self._calculate_confidence(contact_info)
                    
            except Exception as e:
                logger.warning(f"AI extraction failed: {e}")
        
        return contact_info
    
    def batch_extract(self, grants: List[Dict], ai_service: Optional[Any] = None) -> List[Dict]:
        """
        Extract contact information from multiple grants
        
        Args:
            grants: List of grant dictionaries
            ai_service: Optional AI service for enhanced extraction
            
        Returns:
            List of grants with enhanced contact information
        """
        enhanced_grants = []
        
        for grant in grants:
            # Extract contact info
            if ai_service:
                contact_info = self.extract_with_ai(grant, ai_service)
            else:
                contact_info = self.extract_from_grant(grant)
            
            # Merge contact info into grant
            for key, value in contact_info.items():
                if value is not None:
                    grant[key] = value
            
            enhanced_grants.append(grant)
            
            logger.debug(f"Extracted contact info for grant: {grant.get('title', 'Unknown')[:50]}")
        
        logger.info(f"Processed {len(enhanced_grants)} grants for contact information")
        return enhanced_grants


# Singleton instance
_extractor_instance = None

def get_contact_extractor():
    """Get singleton instance of GrantContactExtractor"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = GrantContactExtractor()
    return _extractor_instance