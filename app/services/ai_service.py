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
                
                # Combine reason and explanation for better detail
                full_reason = f"{reason} {explanation}" if explanation != reason else reason
                return score, full_reason
            except Exception as e:
                logger.error(f"Error parsing match result: {e}")
                return 3, "Unable to determine fit score"
        
        return None, None
    
    def analyze_text(self, prompt: str) -> Optional[Dict]:
        """
        General text analysis method for AI extraction and analysis tasks
        Returns structured JSON response or None if analysis fails
        """
        if not self.is_enabled():
            return None
        
        messages = [
            {"role": "system", "content": "You are an expert grant analyst. Always provide clear, structured JSON responses with real data only. Never fabricate contact information, dates, or specific details not present in the source material."},
            {"role": "user", "content": prompt}
        ]
        
        result = self._make_request(
            messages,
            response_format={"type": "json_object"},
            max_tokens=1500
        )
        
        return result if result else {}
    
    def extract_grant_info(self, text: str) -> Optional[Dict]:
        """
        Extract grant information from text or webpage content
        Returns structured grant data or None if extraction fails
        """
        if not self.is_enabled():
            return None
        
        prompt = f"""Extract grant opportunity information from the following text.
        
Text:
{text[:6000]}  # Limit to prevent token overflow

Extract and return a JSON object with these fields (use null if not found):
- "title": grant title
- "funder": organization offering the grant
- "description": brief description of the grant purpose
- "amount_min": minimum grant amount (number only)
- "amount_max": maximum grant amount (number only)
- "deadline": deadline date (ISO format YYYY-MM-DD if possible)
- "eligibility_criteria": who can apply
- "focus_areas": comma-separated list of focus areas
- "application_url": URL to apply or learn more
- "contact_email": contact email if provided
- "contact_phone": contact phone if provided

Be thorough but only include information explicitly stated in the text."""

        messages = [
            {"role": "system", "content": "You are an expert at extracting structured grant information from text."},
            {"role": "user", "content": prompt}
        ]
        
        result = self._make_request(
            messages,
            response_format={"type": "json_object"},
            max_tokens=800
        )
        
        if result:
            # Clean up the amounts to be numbers
            try:
                if result.get("amount_min"):
                    result["amount_min"] = float(str(result["amount_min"]).replace(",", "").replace("$", ""))
                if result.get("amount_max"):
                    result["amount_max"] = float(str(result["amount_max"]).replace(",", "").replace("$", ""))
            except:
                pass
            
            return result
        
        return None
    
    def generate_grant_narrative(self, org_profile: Dict, grant: Optional[Dict], 
                                 section: str, custom_instructions: str = "") -> Optional[str]:
        """
        Generate grant proposal narrative for a specific section
        """
        if not self.is_enabled():
            return None
        
        # Section templates
        section_prompts = {
            "executive_summary": "Write a compelling executive summary for a grant proposal",
            "statement_of_need": "Write a statement of need that demonstrates the problem and urgency",
            "project_description": "Describe the project, its goals, objectives, and implementation plan",
            "evaluation_plan": "Describe how the project's success will be measured and evaluated",
            "budget_narrative": "Provide a budget narrative explaining how funds will be used",
            "organizational_capacity": "Describe the organization's capacity to execute the project",
            "sustainability": "Explain how the project will be sustained after grant funding ends"
        }
        
        base_prompt = section_prompts.get(section, "Write a grant proposal section")
        
        prompt = f"""{base_prompt}

Organization Information:
- Name: {org_profile.get('name', 'Organization')}
- Mission: {org_profile.get('mission', 'Not specified')}
- Website: {org_profile.get('website', 'Not specified')}
- Focus Areas: {org_profile.get('focus_areas', 'Not specified')}
- Programs: {org_profile.get('programs', 'Not specified')}
- Achievements: {org_profile.get('achievements', 'Not specified')}
"""

        if grant:
            prompt += f"""
Grant Opportunity:
- Title: {grant.get('title', 'Not specified')}
- Funder: {grant.get('funder', 'Not specified')}
- Focus: {grant.get('focus_areas', 'Not specified')}
- Amount Range: ${grant.get('amount_min', 0):,} - ${grant.get('amount_max', 0):,}
"""

        if custom_instructions:
            prompt += f"\nAdditional Instructions: {custom_instructions}"

        prompt += """

Write a professional, compelling narrative (300-500 words) that:
1. Aligns with the funder's priorities
2. Uses specific examples and data where possible
3. Maintains a confident but not boastful tone
4. Focuses on impact and outcomes
5. Is ready for submission with minimal editing"""

        messages = [
            {"role": "system", "content": "You are an expert grant writer with 20 years of experience writing successful proposals."},
            {"role": "user", "content": prompt}
        ]
        
        result = self._make_request(messages, max_tokens=1500)
        
        return result.get("content") if result else None
    
    def improve_text(self, text: str, improvement_type: str) -> Optional[str]:
        """
        Improve or rewrite text based on the specified type
        """
        if not self.is_enabled():
            return None
        
        improvement_prompts = {
            "clarity": "Rewrite this text to be clearer and easier to understand",
            "professional": "Rewrite this text to be more professional and formal",
            "concise": "Make this text more concise while keeping all key information",
            "expand": "Expand this text with more detail and examples",
            "persuasive": "Make this text more persuasive and compelling"
        }
        
        prompt = f"""{improvement_prompts.get(improvement_type, 'Improve this text')}:

{text}

Maintain the same key points but improve the writing quality."""

        messages = [
            {"role": "system", "content": "You are an expert editor and writer."},
            {"role": "user", "content": prompt}
        ]
        
        result = self._make_request(messages, max_tokens=1000)
        
        return result.get("content") if result else None
    
    def analyze_grant_success_factors(self, grant_data: Dict, org_data: Dict) -> Optional[Dict]:
        """
        Analyze factors that contribute to grant success or failure
        """
        if not self.is_enabled():
            return None
        
        prompt = f"""Analyze the following grant application and provide insights:

Grant: {grant_data}
Organization: {org_data}

Provide a JSON analysis with:
- "strengths": list of 3-5 key strengths
- "weaknesses": list of 3-5 areas for improvement
- "recommendations": list of 3-5 specific recommendations
- "success_probability": estimated chance of success (low/medium/high)
- "key_factors": top 3 factors that will determine success"""

        messages = [
            {"role": "system", "content": "You are a grant evaluation expert."},
            {"role": "user", "content": prompt}
        ]
        
        result = self._make_request(
            messages,
            response_format={"type": "json_object"},
            max_tokens=800
        )
        
        return result


# Initialize global AI service instance
ai_service = AIService()
