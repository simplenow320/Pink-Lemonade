"""
Grant Intelligence Service
Provides AI-powered analysis and data extraction for grant opportunities
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.services.ai_service import AIService
from app.models import Grant, db

logger = logging.getLogger(__name__)

class GrantIntelligenceService:
    """Service for extracting and analyzing grant intelligence using AI"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    def analyze_grant(self, grant_id: int, org_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive AI analysis of a grant opportunity
        
        Args:
            grant_id: Database ID of the grant to analyze
            org_context: Organization information for context
        
        Returns:
            Dict containing analysis results and metadata
        """
        try:
            grant = Grant.query.get_or_404(grant_id)
            
            # Extract data from grant sources
            grant_text = self._gather_grant_information(grant)
            
            # Perform AI extraction
            extraction_result = self._extract_grant_details(grant, grant_text)
            
            # Perform strategic analysis
            analysis_result = self._analyze_grant_strategy(grant, extraction_result, org_context)
            
            # Update database with intelligence
            self._update_grant_intelligence(grant, extraction_result, analysis_result)
            
            return {
                'success': True,
                'grant_id': grant_id,
                'extraction': extraction_result,
                'analysis': analysis_result,
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Grant analysis failed for ID {grant_id}: {str(e)}")
            return {
                'success': False,
                'grant_id': grant_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _gather_grant_information(self, grant: Grant) -> str:
        """
        Gather available text information about the grant
        
        Args:
            grant: Grant model instance
        
        Returns:
            Combined text content for analysis
        """
        info_parts = []
        
        # Basic grant information
        info_parts.append(f"Grant Title: {grant.title}")
        info_parts.append(f"Funder: {grant.funder}")
        
        if grant.eligibility:
            info_parts.append(f"Eligibility: {grant.eligibility}")
        
        if grant.geography:
            info_parts.append(f"Geography: {grant.geography}")
        
        # Amount information
        if grant.amount_min and grant.amount_max:
            info_parts.append(f"Award Range: ${grant.amount_min:,.0f} - ${grant.amount_max:,.0f}")
        elif grant.amount_max:
            info_parts.append(f"Maximum Award: ${grant.amount_max:,.0f}")
        
        # Deadline information
        if grant.deadline:
            info_parts.append(f"Deadline: {grant.deadline}")
        
        # Try to fetch additional content from URLs
        if grant.link:
            web_content = self._fetch_web_content(grant.link)
            if web_content:
                info_parts.append(f"Additional Information from {grant.link}:")
                info_parts.append(web_content[:5000])  # Limit to first 5000 chars
        
        if grant.source_url and grant.source_url != grant.link:
            web_content = self._fetch_web_content(grant.source_url)
            if web_content:
                info_parts.append(f"Source Information from {grant.source_url}:")
                info_parts.append(web_content[:3000])  # Limit to first 3000 chars
        
        return "\n\n".join(info_parts)
    
    def _fetch_web_content(self, url: str, timeout: int = 10) -> Optional[str]:
        """
        Safely fetch and extract text content from a web page
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
        
        Returns:
            Extracted text content or None if failed
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                logger.warning(f"Invalid URL format: {url}")
                return None
            
            # Set headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML and extract text
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # Extract text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines()]
            text = '\n'.join(line for line in lines if line)
            
            return text
            
        except Exception as e:
            logger.warning(f"Failed to fetch content from {url}: {str(e)}")
            return None
    
    def _extract_grant_details(self, grant: Grant, grant_text: str) -> Dict[str, Any]:
        """
        Use AI to extract structured details from grant information
        
        Args:
            grant: Grant model instance
            grant_text: Combined text content for analysis
        
        Returns:
            Structured extraction results
        """
        try:
            prompt_data = {
                'grant_text': grant_text,
                'grant_title': grant.title,
                'grant_funder': grant.funder,
                'source_url': grant.link or grant.source_url or 'Not provided'
            }
            
            # Use text analysis for now - will enhance with full prompt system later
            extraction_prompt = f"""
Extract key information from this grant:
Title: {prompt_data['grant_title']}
Funder: {prompt_data['grant_funder']}
Content: {prompt_data['grant_text'][:2000]}

Return JSON with: contact_info, deadlines, requirements, complexity_score (1-5)
"""
            result = self.ai_service.analyze_text(extraction_prompt)
            
            return result if isinstance(result, dict) else {}
            
        except Exception as e:
            logger.error(f"Grant extraction failed: {str(e)}")
            return {
                'error': f"Extraction failed: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _analyze_grant_strategy(self, grant: Grant, extraction_data: Dict[str, Any], org_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Use AI to perform strategic analysis of grant opportunity
        
        Args:
            grant: Grant model instance
            extraction_data: Results from detail extraction
            org_context: Organization context for analysis
        
        Returns:
            Strategic analysis results
        """
        try:
            # Default organization context if not provided
            if not org_context:
                org_context = {
                    'org_name': 'Nitrogen Network',
                    'org_mission': 'Urban ministry and community development',
                    'org_programs': 'After-school programs, community workshops, mentoring services',
                    'org_audience': 'At-risk youth and urban families',
                    'org_needs': 'Program expansion and community outreach funding'
                }
            
            prompt_data = {
                **org_context,
                'grant_title': grant.title,
                'grant_funder': grant.funder,
                'amount_min': grant.amount_min or 0,
                'amount_max': grant.amount_max or 0,
                'deadline': grant.deadline.isoformat() if grant.deadline else 'Not specified',
                'requirements': extraction_data.get('requirements', {}).get('eligibility_summary', 'See extraction data'),
                'contact_info': json.dumps(extraction_data.get('contact_info', {})),
                'complexity_score': extraction_data.get('application_details', {}).get('complexity_score', 'Not assessed')
            }
            
            # Use text analysis for strategic assessment
            analysis_prompt = f"""
Analyze this grant for {prompt_data['org_name']}:
Grant: {prompt_data['grant_title']} from {prompt_data['grant_funder']}
Amount: ${prompt_data['amount_min']}-${prompt_data['amount_max']}
Deadline: {prompt_data['deadline']}
Org Mission: {prompt_data['org_mission']}

Provide mission alignment (1-5 score), priority level (High/Medium/Low), and 3 specific next actions.
Format as JSON.
"""
            result = self.ai_service.analyze_text(analysis_prompt)
            
            return result if isinstance(result, dict) else {}
            
        except Exception as e:
            logger.error(f"Grant analysis failed: {str(e)}")
            return {
                'error': f"Analysis failed: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _update_grant_intelligence(self, grant: Grant, extraction_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> None:
        """
        Update the grant record with intelligence data
        
        Args:
            grant: Grant model instance
            extraction_data: Extraction results
            analysis_data: Analysis results
        """
        try:
            # Update contact information
            if 'contact_info' in extraction_data:
                grant.contact_info = extraction_data['contact_info']
            
            # Update requirements summary
            requirements = extraction_data.get('requirements', {})
            if requirements.get('eligibility_summary'):
                grant.requirements_summary = requirements['eligibility_summary']
            
            # Update complexity score
            app_details = extraction_data.get('application_details', {})
            if app_details.get('complexity_score'):
                grant.application_complexity = app_details['complexity_score']
            
            # Update AI summary from analysis
            if 'mission_alignment' in analysis_data:
                alignment = analysis_data['mission_alignment']
                summary_parts = []
                
                if alignment.get('alignment_summary'):
                    summary_parts.append(f"Fit Score: {alignment.get('fit_score', 'N/A')}/5")
                    summary_parts.append(alignment['alignment_summary'])
                
                if 'strategic_assessment' in analysis_data:
                    strategic = analysis_data['strategic_assessment']
                    if strategic.get('priority_level'):
                        summary_parts.append(f"Priority: {strategic['priority_level']}")
                    if strategic.get('effort_vs_reward'):
                        summary_parts.append(strategic['effort_vs_reward'])
                
                grant.ai_summary = ' | '.join(summary_parts) if summary_parts else None
            
            # Update timestamp
            grant.last_intelligence_update = datetime.utcnow()
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update grant intelligence: {str(e)}")
            db.session.rollback()
            raise
    
    def bulk_analyze_grants(self, org_context: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze multiple grants in bulk
        
        Args:
            org_context: Organization context for analysis
            limit: Maximum number of grants to analyze
        
        Returns:
            Bulk analysis results
        """
        try:
            # Get grants that need intelligence updates
            query = Grant.query.filter(
                (Grant.last_intelligence_update.is_(None)) |
                (Grant.ai_summary.is_(None))
            ).order_by(Grant.deadline.asc().nullslast())
            
            if limit:
                query = query.limit(limit)
            
            grants = query.all()
            
            results = {
                'total_analyzed': 0,
                'successful': 0,
                'failed': 0,
                'results': []
            }
            
            for grant in grants:
                result = self.analyze_grant(grant.id, org_context)
                results['results'].append(result)
                results['total_analyzed'] += 1
                
                if result.get('success'):
                    results['successful'] += 1
                else:
                    results['failed'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk analysis failed: {str(e)}")
            return {
                'total_analyzed': 0,
                'successful': 0,
                'failed': 1,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }