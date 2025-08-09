"""
AI Service Layer for Grant Management
Handles all OpenAI API interactions for matching, extraction, and narrative generation
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIService:
    """Central AI service for grant-related AI operations"""
    
    def __init__(self):
        """Initialize AI service with API key from environment"""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.client = None
        self.model = "gpt-4o"  # Latest OpenAI model as of 2024
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info("AI Service initialized with API key")
        else:
            logger.warning("AI Service initialized without API key - AI features disabled")
    
    def is_enabled(self) -> bool:
        """Check if AI service is enabled (has API key)"""
        return self.client is not None
    
    def _make_request(self, messages: List[Dict], 
                     response_format: Optional[Dict] = None,
                     max_tokens: int = 1000) -> Optional[Dict]:
        """Make request to OpenAI with retry logic"""
        if not self.client:
            logger.warning("AI Service not enabled - no API key")
            return None
        
        for attempt in range(self.max_retries):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
                
                if response_format:
                    kwargs["response_format"] = response_format
                
                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                
                # Parse JSON if response format was JSON
                if response_format and response_format.get("type") == "json_object":
                    return json.loads(content)
                return {"content": content}
                
            except Exception as e:
                logger.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    return None
        
        return None
    
    def match_grant(self, org_profile: Dict, grant: Dict) -> Tuple[Optional[int], Optional[str]]:
        """
        Match a grant to an organization profile
        Returns: (fit_score: 1-5, reason: str) or (None, None) if disabled
        """
        if not self.is_enabled():
            return None, None
        
        # Build prompt
        prompt = f"""Analyze the fit between this organization and grant opportunity.

Organization Profile:
- Name: {org_profile.get('name', 'Unknown')}
- Mission: {org_profile.get('mission', 'Not specified')}
- Focus Areas: {', '.join(org_profile.get('focus_areas', []))}
- Keywords: {', '.join(org_profile.get('keywords', []))}
- Geographic Focus: {org_profile.get('geographic_focus', 'Not specified')}
- Target Population: {org_profile.get('target_population', 'Not specified')}

Grant Opportunity:
- Title: {grant.get('title', 'Unknown')}
- Funder: {grant.get('funder', 'Unknown')}
- Description: {grant.get('description', 'Not specified')}
- Focus Areas: {grant.get('focus_areas', 'Not specified')}
- Amount Range: ${grant.get('amount_min', 0):,} - ${grant.get('amount_max', 0):,}
- Deadline: {grant.get('deadline', 'Not specified')}
- Eligibility: {grant.get('eligibility_criteria', 'Not specified')}

Provide a JSON response with:
1. "fit_score": integer from 1-5 (1=poor fit, 5=excellent fit)
2. "reason": one concise sentence explaining the score
3. "explanation": 2-3 sentences with specific details about alignment or gaps

Focus on mission alignment, geographic match, focus area overlap, and eligibility requirements."""

        messages = [
            {"role": "system", "content": "You are an expert grant advisor analyzing grant-organization fit."},
            {"role": "user", "content": prompt}
        ]
        
        result = self._make_request(
            messages, 
            response_format={"type": "json_object"},
            max_tokens=500
        )
        
        if result:
            try:
                score = max(1, min(5, result.get("fit_score", 3)))  # Clamp to 1-5
                reason = result.get("reason", "Unable to determine fit")
                explanation = result.get("explanation", reason)
                
                # Store explanation in result for future reference
                result["full_explanation"] = explanation
                
                return score, reason
            except Exception as e:
                logger.error(f"Error parsing match result: {e}")
                return None, None
        
        return None, None
    
    def explain_match(self, org_profile: Dict, grant: Dict) -> Optional[str]:
        """Get detailed explanation of grant match"""
        if not self.is_enabled():
            return None
        
        # Try to get cached explanation from last match
        score, reason = self.match_grant(org_profile, grant)
        if score:
            # Make another request for detailed explanation
            prompt = f"""Provide a detailed 2-3 sentence explanation of why this organization 
            (mission: {org_profile.get('mission', 'Unknown')}) 
            is a fit score {score} for this grant ({grant.get('title', 'Unknown')}).
            Focus on specific alignment points or gaps."""
            
            messages = [
                {"role": "system", "content": "You are an expert grant advisor."},
                {"role": "user", "content": prompt}
            ]
            
            result = self._make_request(messages, max_tokens=200)
            if result:
                return result.get("content", reason)
        
        return None
    
    def extract_grant_from_text(self, text: str, url: Optional[str] = None) -> Optional[Dict]:
        """
        Extract structured grant information from text or URL content
        Returns: Dictionary with grant fields or None if extraction fails
        """
        if not self.is_enabled():
            return None
        
        prompt = f"""Extract grant opportunity information from the following text.
        
{text[:4000]}  # Limit text to avoid token limits

Extract and return a JSON object with these fields:
- "title": Grant program name
- "funder": Organization offering the grant
- "description": Brief description (1-2 sentences)
- "amount_min": Minimum award amount (number, 0 if not specified)
- "amount_max": Maximum award amount (number, 0 if not specified)  
- "deadline": Application deadline (ISO date format if possible, or text)
- "eligibility_criteria": Who can apply (1-2 sentences)
- "focus_areas": Main focus areas or priorities (comma-separated)
- "geography": Geographic restrictions or preferences
- "link": Application URL (use provided URL if given: {url})
- "contact_name": Contact person if mentioned
- "contact_email": Contact email if provided
- "contact_phone": Contact phone if provided

If information is not available for a field, use null or empty string as appropriate."""

        messages = [
            {"role": "system", "content": "You are an expert at extracting structured grant information from unstructured text."},
            {"role": "user", "content": prompt}
        ]
        
        result = self._make_request(
            messages,
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        if result:
            try:
                # Clean and validate the extracted data
                grant_data = {
                    "title": result.get("title", "Untitled Grant"),
                    "funder": result.get("funder", "Unknown Funder"),
                    "description": result.get("description", ""),
                    "amount_min": int(result.get("amount_min", 0)) if result.get("amount_min") else 0,
                    "amount_max": int(result.get("amount_max", 0)) if result.get("amount_max") else 0,
                    "deadline": result.get("deadline", ""),
                    "eligibility_criteria": result.get("eligibility_criteria", ""),
                    "focus_areas": result.get("focus_areas", ""),
                    "geography": result.get("geography", ""),
                    "link": result.get("link", url or ""),
                    "contact_name": result.get("contact_name", ""),
                    "contact_email": result.get("contact_email", ""),
                    "contact_phone": result.get("contact_phone", ""),
                    "source_name": "AI Extraction",
                    "discovered_at": datetime.now().isoformat()
                }
                
                return grant_data
                
            except Exception as e:
                logger.error(f"Error parsing extraction result: {e}")
                return None
        
        return None
    
    def generate_narrative(self, grant: Dict, org_profile: Dict, 
                          sections: List[str]) -> Optional[Dict]:
        """
        Generate narrative sections for a grant proposal
        Returns: Dictionary with section content or None if generation fails
        """
        if not self.is_enabled():
            return None
        
        # Map section names to prompts
        section_prompts = {
            "need": "Write a compelling statement of need that demonstrates why this project is necessary",
            "program": "Describe the program approach and activities that will address the need", 
            "outcomes": "Explain the expected outcomes, impact metrics, and evaluation methods",
            "budget_rationale": "Provide a budget narrative explaining how funds will be used effectively"
        }
        
        narratives = {}
        
        for section in sections:
            if section not in section_prompts:
                continue
            
            prompt = f"""Generate a grant proposal section for the following:

Grant: {grant.get('title', 'Unknown Grant')}
Funder: {grant.get('funder', 'Unknown Funder')}
Amount: ${grant.get('amount_max', 0):,}
Focus: {grant.get('focus_areas', 'General')}

Organization: {org_profile.get('name', 'Unknown Organization')}
Mission: {org_profile.get('mission', 'Not specified')}
Focus Areas: {', '.join(org_profile.get('focus_areas', []))}
Target Population: {org_profile.get('target_population', 'Not specified')}

Section to write: {section_prompts[section]}

Write in a professional, compelling grant proposal style. Be specific to this organization's mission and the grant's priorities. 
Limit response to 2-3 paragraphs."""

            messages = [
                {"role": "system", "content": "You are an expert grant writer creating compelling proposal narratives."},
                {"role": "user", "content": prompt}
            ]
            
            result = self._make_request(messages, max_tokens=800)
            
            if result:
                narratives[section] = {
                    "content": result.get("content", ""),
                    "generated_at": datetime.now().isoformat(),
                    "version": 1
                }
        
        if narratives:
            return {
                "grant_id": grant.get("id"),
                "sections": narratives,
                "created_at": datetime.now().isoformat(),
                "is_draft": True
            }
        
        return None
    
    def batch_match_grants(self, org_profile: Dict, grants: List[Dict]) -> List[Dict]:
        """
        Match multiple grants efficiently
        Returns: List of grants with fit_score and reason added
        """
        if not self.is_enabled():
            # Return grants unchanged if AI is disabled
            return [{**g, "fit_score": None, "fit_reason": None} for g in grants]
        
        results = []
        for grant in grants:
            score, reason = self.match_grant(org_profile, grant)
            results.append({
                **grant,
                "fit_score": score,
                "fit_reason": reason
            })
        
        return results


# Singleton instance
ai_service = AIService()