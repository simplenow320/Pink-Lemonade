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
    
    def generate_json_response(self, prompt: str, max_tokens: int = 2000) -> Optional[Dict]:
        """Generate a JSON response from a prompt"""
        if not self.client:
            logger.warning("AI Service not enabled - no API key")
            return None
        
        messages = [
            {"role": "system", "content": "You are an expert grant analyst. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        return self._make_request(
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=max_tokens
        )
    
    def match_grant(self, org_profile: Dict, grant: Dict, funder_profile: Dict = None) -> Tuple[Optional[int], Optional[str]]:
        """
        Enhanced grant matching with comprehensive organization data and authentic funder intelligence
        Returns: (fit_score: 1-5, reason: str) or (None, None) if disabled
        """
        if not self.is_enabled():
            return None, None
        
        # Build comprehensive organization profile
        org_context = self._build_comprehensive_org_context(org_profile)
        
        # Build grant context with authentic funder intelligence
        grant_context = self._build_grant_context_with_funder_intelligence(grant, funder_profile)
        
        # Enhanced prompt with rich data
        prompt = f"""Analyze the strategic fit between this nonprofit organization and grant opportunity using comprehensive data.

{org_context}

{grant_context}

STRATEGIC ANALYSIS REQUIRED:
1. Mission & Values Alignment: How well do organizational missions align?
2. Program Focus Match: Do the organization's programs directly serve this grant's purpose?
3. Geographic Compatibility: Does service area align with funder's geographic priorities?
4. Organizational Capacity: Can this organization successfully manage this grant size and requirements?
5. Target Population Fit: Do beneficiaries match funder's intended recipients?
6. Funder History: Does the organization's profile match this funder's typical grantees?
7. Strategic Advantage: What unique strengths does this organization bring?

Provide detailed JSON response:
1. "fit_score": integer 1-5 (1=poor fit, 5=excellent strategic match)
2. "reason": Strategic summary in one compelling sentence
3. "explanation": 3-4 sentences with specific strategic rationale
4. "strengths": List of 3 key organizational advantages for this grant
5. "considerations": List of 2-3 factors to address in application
6. "strategic_approach": Recommended application strategy"""

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
                strengths = result.get("strengths", [])
                considerations = result.get("considerations", [])
                strategy = result.get("strategic_approach", "")
                
                # Build comprehensive response
                full_reason = f"{reason} {explanation}"
                if strengths:
                    full_reason += f"\nKey Strengths: {'; '.join(strengths[:3])}"
                if considerations:
                    full_reason += f"\nConsiderations: {'; '.join(considerations[:2])}"
                if strategy:
                    full_reason += f"\nStrategy: {strategy}"
                
                return score, full_reason
            except Exception as e:
                logger.error(f"Error parsing enhanced match result: {e}")
                return 3, "Unable to determine fit score"
        
        return None, None
    
    def _build_comprehensive_org_context(self, org_profile: Dict) -> str:
        """Build comprehensive organization context using all available profile data"""
        
        context_parts = []
        
        # Core Identity
        context_parts.append("=== ORGANIZATION PROFILE ===")
        context_parts.append(f"Organization: {org_profile.get('name', 'Unknown')}")
        
        if org_profile.get('legal_name') and org_profile.get('legal_name') != org_profile.get('name'):
            context_parts.append(f"Legal Name: {org_profile.get('legal_name')}")
        
        if org_profile.get('org_type'):
            context_parts.append(f"Organization Type: {org_profile.get('org_type')}")
        
        if org_profile.get('ein'):
            context_parts.append(f"EIN: {org_profile.get('ein')}")
        
        # Mission & Vision
        if org_profile.get('mission'):
            context_parts.append(f"Mission: {org_profile.get('mission')}")
        
        if org_profile.get('vision'):
            context_parts.append(f"Vision: {org_profile.get('vision')}")
        
        # Program Focus
        primary_focus = org_profile.get('primary_focus_areas', [])
        if primary_focus:
            context_parts.append(f"Primary Focus Areas: {', '.join(primary_focus)}")
        
        secondary_focus = org_profile.get('secondary_focus_areas', [])
        if secondary_focus:
            context_parts.append(f"Secondary Focus Areas: {', '.join(secondary_focus)}")
        
        if org_profile.get('programs_services'):
            context_parts.append(f"Programs & Services: {org_profile.get('programs_services')}")
        
        target_demos = org_profile.get('target_demographics', [])
        if target_demos:
            context_parts.append(f"Target Demographics: {', '.join(target_demos)}")
        
        age_groups = org_profile.get('age_groups_served', [])
        if age_groups:
            context_parts.append(f"Age Groups Served: {', '.join(age_groups)}")
        
        # Geographic Scope
        if org_profile.get('service_area_type'):
            context_parts.append(f"Service Area: {org_profile.get('service_area_type')}")
        
        location_parts = []
        if org_profile.get('primary_city'):
            location_parts.append(org_profile.get('primary_city'))
        if org_profile.get('primary_state'):
            location_parts.append(org_profile.get('primary_state'))
        if location_parts:
            context_parts.append(f"Primary Location: {', '.join(location_parts)}")
        
        counties = org_profile.get('counties_served', [])
        if counties:
            context_parts.append(f"Counties Served: {', '.join(counties)}")
        
        # Organizational Capacity
        if org_profile.get('annual_budget_range'):
            context_parts.append(f"Annual Budget: {org_profile.get('annual_budget_range')}")
        
        if org_profile.get('staff_size'):
            context_parts.append(f"Staff Size: {org_profile.get('staff_size')}")
        
        if org_profile.get('people_served_annually'):
            context_parts.append(f"People Served Annually: {org_profile.get('people_served_annually')}")
        
        # Grant History & Experience
        if org_profile.get('previous_funders'):
            funders = org_profile.get('previous_funders', [])
            context_parts.append(f"Previous Funders: {', '.join(funders[:5])}")  # Limit to top 5
        
        if org_profile.get('typical_grant_size'):
            context_parts.append(f"Typical Grant Size: {org_profile.get('typical_grant_size')}")
        
        if org_profile.get('grant_success_rate'):
            context_parts.append(f"Grant Success Rate: {org_profile.get('grant_success_rate')}%")
        
        preferred_types = org_profile.get('preferred_grant_types', [])
        if preferred_types:
            context_parts.append(f"Preferred Grant Types: {', '.join(preferred_types)}")
        
        # Special Characteristics
        special_chars = []
        if org_profile.get('faith_based'):
            special_chars.append('Faith-based')
        if org_profile.get('minority_led'):
            special_chars.append('Minority-led')
        if org_profile.get('woman_led'):
            special_chars.append('Woman-led')
        if org_profile.get('lgbtq_led'):
            special_chars.append('LGBTQ+-led')
        if org_profile.get('veteran_led'):
            special_chars.append('Veteran-led')
        
        if special_chars:
            context_parts.append(f"Special Characteristics: {', '.join(special_chars)}")
        
        # Impact & Achievements
        if org_profile.get('key_achievements'):
            context_parts.append(f"Key Achievements: {org_profile.get('key_achievements')}")
        
        if org_profile.get('unique_capabilities'):
            context_parts.append(f"Unique Capabilities: {org_profile.get('unique_capabilities')}")
        
        # Keywords for matching
        keywords = org_profile.get('keywords', [])
        if keywords:
            context_parts.append(f"Keywords: {', '.join(keywords)}")
        
        return '\n'.join(context_parts)
    
    def _build_grant_context_with_funder_intelligence(self, grant: Dict, funder_profile: Dict = None) -> str:
        """Build grant context enhanced with authentic funder intelligence"""
        
        context_parts = []
        context_parts.append("=== GRANT OPPORTUNITY ===")
        
        # Basic Grant Info
        context_parts.append(f"Grant Title: {grant.get('title', 'Unknown')}")
        context_parts.append(f"Funder: {grant.get('funder', 'Unknown')}")
        
        if grant.get('description'):
            context_parts.append(f"Description: {grant.get('description')}")
        
        # Program Overview (from authentic data)
        if grant.get('program_overview'):
            context_parts.append(f"Program Overview: {grant.get('program_overview')}")
        
        # Financial Details
        amount_min = grant.get('amount_min', 0)
        amount_max = grant.get('amount_max', 0)
        if amount_min or amount_max:
            if amount_min == amount_max:
                context_parts.append(f"Grant Amount: ${amount_max:,}")
            else:
                context_parts.append(f"Amount Range: ${amount_min:,} - ${amount_max:,}")
        
        # Grant Details
        if grant.get('deadline'):
            context_parts.append(f"Deadline: {grant.get('deadline')}")
        
        focus_areas = grant.get('focus_areas', [])
        if focus_areas:
            if isinstance(focus_areas, list):
                context_parts.append(f"Focus Areas: {', '.join(focus_areas)}")
            else:
                context_parts.append(f"Focus Areas: {focus_areas}")
        
        if grant.get('eligibility_criteria'):
            context_parts.append(f"Eligibility: {grant.get('eligibility_criteria')}")
        
        # Enhanced Funder Intelligence (Authentic Data Only)
        if funder_profile:
            context_parts.append("\n=== AUTHENTIC FUNDER INTELLIGENCE ===")
            
            if funder_profile.get('verified_overview'):
                context_parts.append(f"Funder Overview: {funder_profile.get('verified_overview')}")
            
            if funder_profile.get('official_website'):
                context_parts.append(f"Official Website: {funder_profile.get('official_website')}")
            
            if funder_profile.get('funding_priorities'):
                priorities = funder_profile.get('funding_priorities', [])
                context_parts.append(f"Funding Priorities: {', '.join(priorities)}")
            
            if funder_profile.get('typical_grant_amounts'):
                amounts = funder_profile.get('typical_grant_amounts')
                context_parts.append(f"Typical Grant Range: {amounts}")
            
            if funder_profile.get('success_factors'):
                factors = funder_profile.get('success_factors', [])
                context_parts.append(f"Success Factors: {', '.join(factors[:3])}")  # Top 3
            
            if funder_profile.get('geographic_focus'):
                context_parts.append(f"Geographic Focus: {funder_profile.get('geographic_focus')}")
            
            if funder_profile.get('data_source'):
                context_parts.append(f"Data Source: {funder_profile.get('data_source')}")
        
        return '\n'.join(context_parts)
    
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
    
    def generate_grant_match(self, org_profile: dict, grant: dict) -> tuple:
        """Legacy method for backward compatibility - alias for match_grant"""
        return self.match_grant(org_profile, grant)


# Initialize global AI service instance
ai_service = AIService()
