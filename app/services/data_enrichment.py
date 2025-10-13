"""
Data Enrichment & Quality Service
"""
import re
from datetime import datetime
from typing import Dict, Optional

class DataEnrichmentService:

    @staticmethod
    def calculate_quality_score(grant: Dict) -> int:
        """Calculate grant data quality score (0-100)"""
        score = 0

        # Essential fields (40 points)
        if grant.get('title') and len(grant['title']) > 10:
            score += 15
        if grant.get('funder'):
            score += 15
        if grant.get('description') and len(grant.get('description', '')) > 50:
            score += 10

        # Important fields (30 points)
        if grant.get('deadline'):
            score += 15
        if grant.get('amount_min') or grant.get('amount_max'):
            score += 10
        if grant.get('eligibility'):
            score += 5

        # Nice to have (30 points)
        if grant.get('contact_email'):
            score += 10
        if grant.get('contact_phone'):
            score += 5
        if grant.get('source_url'):
            score += 10
        if grant.get('geography'):
            score += 5

        return min(score, 100)

    @staticmethod
    def extract_contact_email(text: str) -> Optional[str]:
        """Extract email from text"""
        if not text:
            return None

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None

    @staticmethod
    def extract_contact_phone(text: str) -> Optional[str]:
        """Extract phone from text"""
        if not text:
            return None

        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        matches = re.findall(phone_pattern, text)
        return matches[0] if matches else None

    @staticmethod
    def enrich_grant(grant: Dict) -> Dict:
        """Enrich grant data with extracted information"""
        description = grant.get('description', '')

        # Extract contact info if missing
        if not grant.get('contact_email'):
            grant['contact_email'] = DataEnrichmentService.extract_contact_email(description)

        if not grant.get('contact_phone'):
            grant['contact_phone'] = DataEnrichmentService.extract_contact_phone(description)

        # Calculate quality score
        grant['quality_score'] = DataEnrichmentService.calculate_quality_score(grant)

        return grant