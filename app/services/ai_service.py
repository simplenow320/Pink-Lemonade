"""
AI Service Layer for Grant Management
Handles all OpenAI API interactions for matching, extraction, and narrative generation
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import openai
from openai import OpenAI
from app.services.ai_optimizer_service import ai_optimizer, TaskComplexity
from app.services.mock_ai_service import MockAIService
import threading

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Circuit breaker pattern to prevent cascading failures"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, reset_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.Lock()
        
    def call(self, func, *args, **kwargs):
        """Call function through circuit breaker"""
        with self.lock:
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                    logger.info("Circuit breaker attempting reset")
                else:
                    logger.warning("Circuit breaker is OPEN - rejecting call")
                    return None
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise e
                
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return bool(self.last_failure_time and 
                    datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.reset_timeout))
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = 'CLOSED'
        
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")

class AIService:
    """Central AI service for grant-related AI operations with intelligent model routing and circuit breaker"""
    
    def __init__(self):
        """Initialize AI service with API key from environment, optimizer, and circuit breaker"""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.client = None
        self.model = "gpt-3.5-turbo-1106"  # Use fastest model by default
        self.max_retries = 1  # Reduced to speed up failures
        self.retry_delay = 0.5  # Reduced from 1 seconds to speed up retries
        self.optimizer = ai_optimizer  # Use intelligent model routing
        self.use_mock = os.environ.get("USE_MOCK_AI", "false").lower() == "true"
        self.mock_service = MockAIService()
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30, reset_timeout=15)
        self.request_timeout = 10  # Maximum 10 seconds per request for speed
        self.prompt_reduction_enabled = True
        
        if self.use_mock:
            logger.info("AI Service using MOCK responses (USE_MOCK_AI=true)")
        elif self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info("AI Service initialized with API key and cost optimizer")
        else:
            logger.warning("AI Service initialized without API key - will use mock responses")
    
    def is_enabled(self) -> bool:
        """Check if AI service is enabled (has API key)"""
        return bool(self.client is not None)
    
    def generate_text(self, prompt: str, max_tokens: int = 200) -> str:
        """
        Generate simple text response from AI
        Returns text string or empty string on failure
        """
        if not self.is_enabled():
            return ""
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Provide concise, accurate responses."},
            {"role": "user", "content": prompt}
        ]
        
        result = self._make_request(messages, max_tokens=max_tokens, task_type="text_generation")
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            return str(result.get('content', ''))
        return ""
    
    def _make_request(self, messages: List[Dict], 
                     response_format: Optional[Dict] = None,
                     max_tokens: int = 200,
                     task_type: str = "general") -> Optional[Dict]:
        """Make request to OpenAI with intelligent model routing via optimizer"""
        if not self.client:
            logger.warning("AI Service not enabled - no API key")
            return None
        
        # Use optimizer for intelligent model routing with speed optimizations
        prompt = messages[-1]["content"] if messages else ""
        context = {
            "max_tokens": 200,  # Reduced for speed
            "temperature": 0,  # Deterministic for speed
            "json_output": response_format and response_format.get("type") == "json_object",
            "top_p": 1,  # Faster generation
            "stream": False  # No streaming for speed
        }
        
        # Use optimizer with direct execution - avoid signal-based timeouts in gunicorn workers
        try:
            # Direct call without signal-based timeout (incompatible with gunicorn)
            result = self.optimizer.optimize_request(
                task_type=task_type,
                prompt=prompt,
                context=context
            )
        except Exception as e:
            logger.warning(f"OpenAI API error - using fallback response: {e}")
            return self._get_error_fallback_response()
        
        if result.get("success"):
            logger.info(f"AI request successful: {result.get('explanation')}")
            return result.get("content")
        else:
            # Fallback to direct API call if optimizer fails
            logger.warning(f"Optimizer failed, using direct API call: {result.get('error')}")
            for attempt in range(self.max_retries):
                try:
                    kwargs = {
                        "model": "gpt-3.5-turbo-1106",  # Use fastest model
                        "messages": messages,
                        "max_tokens": 200,  # Reduced for speed
                        "temperature": 0,  # Deterministic for speed
                        "stream": False,  # Explicit no streaming
                        "top_p": 1  # Faster generation
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
                        time.sleep(self.retry_delay)
                    else:
                        return self._get_error_fallback_response()
        
        return None
    
    def _get_fallback_match_score(self, org_profile: Optional[Dict] = None, grant: Optional[Dict] = None) -> Dict:
        """
        Calculate a basic match score using keyword matching when AI is unavailable.
        This ensures the system always returns results even without AI.
        """
        logger.info("Using fallback keyword-based scoring mechanism")
        
        # Initialize scoring components
        score_points = 0
        max_points = 100
        matches_found = []
        
        # Safe data extraction with defaults
        org_profile = org_profile or {}
        grant = grant or {}
        
        # 1. Focus Areas Matching (30 points max)
        org_focus = set()
        if org_profile.get('primary_focus_areas'):
            org_focus.update([f.lower() for f in org_profile.get('primary_focus_areas', [])])
        if org_profile.get('secondary_focus_areas'):
            org_focus.update([f.lower() for f in org_profile.get('secondary_focus_areas', [])])
        if org_profile.get('keywords'):
            org_focus.update([k.lower() for k in org_profile.get('keywords', [])])
        
        grant_focus = set()
        if grant.get('focus_areas'):
            focus = grant.get('focus_areas')
            if isinstance(focus, list):
                grant_focus.update([f.lower() for f in focus])
            elif isinstance(focus, str):
                grant_focus.update([f.lower() for f in focus.split(',')])
        
        # Check for focus area matches
        if org_focus and grant_focus:
            common_focus = org_focus & grant_focus
            if common_focus:
                score_points += min(30, len(common_focus) * 10)
                matches_found.append(f"Matching focus areas: {', '.join(list(common_focus)[:3])}")
        
        # 2. Geographic Alignment (25 points max)
        org_state = org_profile.get('primary_state', '').lower()
        org_city = org_profile.get('primary_city', '').lower()
        org_service_area = org_profile.get('service_area_type', '').lower()
        
        grant_location = grant.get('location', '').lower()
        grant_desc = grant.get('description', '').lower()
        grant_title = grant.get('title', '').lower()
        
        # Check geographic matches
        geographic_match = False
        if org_state and (org_state in grant_location or org_state in grant_desc):
            score_points += 15
            geographic_match = True
            matches_found.append(f"State match: {org_state}")
        
        if org_city and (org_city in grant_location or org_city in grant_desc):
            score_points += 10
            geographic_match = True
            matches_found.append(f"City match: {org_city}")
        
        # Check for national/regional scope
        if 'national' in org_service_area or 'national' in grant_desc or 'nationwide' in grant_desc:
            if not geographic_match:
                score_points += 10
                matches_found.append("National scope alignment")
        
        # 3. Budget Range Compatibility (25 points max)
        org_budget = org_profile.get('annual_budget_range', '')
        grant_min = grant.get('amount_min', 0)
        grant_max = grant.get('amount_max', 0)
        
        # Simple budget compatibility check
        if org_budget and (grant_min or grant_max):
            # Extract budget range from string (e.g., "$100,000-$500,000")
            budget_compatible = True  # Default to compatible if we can't parse
            
            if '$' in org_budget:
                # Try to extract max budget from org
                import re
                numbers = re.findall(r'\$?([\d,]+)', org_budget)
                if numbers:
                    try:
                        max_budget = int(numbers[-1].replace(',', ''))
                        # Grant should be less than 50% of annual budget for safety
                        if grant_max and grant_max < max_budget * 0.5:
                            score_points += 25
                            matches_found.append("Budget range compatible")
                        elif grant_max and grant_max < max_budget:
                            score_points += 15
                            matches_found.append("Budget range potentially compatible")
                    except:
                        score_points += 10  # Give some points if we can't parse
            else:
                score_points += 10  # Give partial points if budget info exists
        
        # 4. Keyword Matching in Mission/Description (20 points max)
        org_mission = (org_profile.get('mission', '') + ' ' + org_profile.get('vision', '')).lower()
        org_programs = org_profile.get('programs_services', '').lower()
        
        # Common grant keywords to look for
        keyword_matches = 0
        keywords = ['education', 'health', 'community', 'youth', 'senior', 'technology', 
                   'environment', 'arts', 'culture', 'social', 'justice', 'equity']
        
        for keyword in keywords:
            if keyword in org_mission or keyword in org_programs:
                if keyword in grant_desc or keyword in grant_title:
                    keyword_matches += 1
        
        if keyword_matches > 0:
            score_points += min(20, keyword_matches * 5)
            matches_found.append(f"{keyword_matches} keyword matches found")
        
        # Calculate final score (1-5) and percentage
        match_percentage = int((score_points / max_points) * 100)
        
        # Convert to 1-5 scale
        if match_percentage >= 80:
            match_score = 5
            verdict = "Strong potential match"
            recommendation = "This grant appears well-aligned based on keyword analysis. Manual review strongly recommended to confirm fit."
        elif match_percentage >= 60:
            match_score = 4
            verdict = "Good potential match"
            recommendation = "Several alignment indicators found. Review this grant for potential application."
        elif match_percentage >= 40:
            match_score = 3
            verdict = "Moderate potential match"
            recommendation = "Some alignment detected. Further review needed to determine fit."
        elif match_percentage >= 20:
            match_score = 2
            verdict = "Weak potential match"
            recommendation = "Limited alignment found. Review carefully before pursuing."
        else:
            match_score = 1
            verdict = "Poor potential match"
            recommendation = "Minimal alignment detected. Consider other opportunities unless specific factors apply."
        
        # Build response matching expected JSON structure
        return {
            "match_score": match_score,
            "match_percentage": match_percentage,
            "verdict": verdict,
            "recommendation": recommendation,
            "key_alignments": matches_found if matches_found else ["Basic keyword analysis performed"],
            "potential_challenges": ["AI analysis unavailable - keyword matching only"],
            "next_steps": ["Manual review recommended", "Verify alignment details"],
            "application_tips": "This score is based on keyword matching. Please review grant details carefully.",
            "confidence_note": "Fallback scoring - manual review recommended",
            "system_status": "fallback_scoring_active"
        }
    
    def _get_timeout_fallback_response(self, org_profile: Optional[Dict] = None, grant: Optional[Dict] = None) -> Dict:
        """Get fallback response for timeout scenarios - uses keyword matching"""
        logger.warning("AI timeout - using keyword-based fallback scoring")
        
        # Use keyword-based scoring as fallback
        fallback_result = self._get_fallback_match_score(org_profile, grant)
        
        # Add timeout-specific information
        fallback_result["system_status"] = "timeout_fallback"
        fallback_result["confidence_note"] = "AI timeout - using fallback keyword scoring"
        
        return fallback_result
    
    def _get_error_fallback_response(self, org_profile: Optional[Dict] = None, grant: Optional[Dict] = None) -> Dict:
        """Get fallback response for error scenarios - uses keyword matching"""
        logger.warning("AI error - using keyword-based fallback scoring")
        
        # Use keyword-based scoring as fallback
        fallback_result = self._get_fallback_match_score(org_profile, grant)
        
        # Add error-specific information
        fallback_result["system_status"] = "error_fallback"
        fallback_result["confidence_note"] = "AI error - using fallback keyword scoring"
        
        return fallback_result
    
    def _reduce_prompt_intelligently(self, prompt: str, reduction_factor: float = 0.5) -> str:
        """Reduce prompt size intelligently for faster processing"""
        if not self.prompt_reduction_enabled or len(prompt) < 1000:
            return prompt
        
        logger.info(f"Reducing prompt size from {len(prompt)} characters")
        
        # Split prompt into sections
        lines = prompt.split('\n')
        
        # Keep essential sections, reduce detailed sections
        reduced_lines = []
        skip_until_next_section = False
        
        for line in lines:
            # Always keep section headers and essential info
            if any(keyword in line.upper() for keyword in ['===', 'ORGANIZATION:', 'GRANT:', 'ANALYZE', 'REQUIRED:']):
                reduced_lines.append(line)
                skip_until_next_section = False
            elif skip_until_next_section:
                continue
            elif len(line) > 200:  # Reduce very long lines
                reduced_lines.append(line[:200] + "...")
                skip_until_next_section = True
            else:
                reduced_lines.append(line)
        
        reduced_prompt = '\n'.join(reduced_lines)
        logger.info(f"Reduced prompt to {len(reduced_prompt)} characters ({reduction_factor:.1%} reduction)")
        return reduced_prompt
    
    def generate_json_response(self, prompt: str, max_tokens: int = 200, context: Optional[Dict] = None) -> Optional[Dict]:
        """Generate a JSON response from a prompt with circuit breaker protection and fallback support"""
        # Use mock if enabled or no client available
        if self.use_mock or not self.client:
            logger.info("Using mock AI response")
            # Detect the type of request from prompt and return appropriate mock
            if "match" in prompt.lower() or "fit" in prompt.lower() or "score" in prompt.lower():
                return self.mock_service.get_mock_grant_match()
            elif "pitch" in prompt.lower():
                return self.mock_service.get_mock_pitch()
            elif "impact" in prompt.lower() or "report" in prompt.lower():
                return self.mock_service.get_mock_impact_report()
            elif "case" in prompt.lower() or "support" in prompt.lower():
                return self.mock_service.get_mock_case_support()
            else:
                # Generic mock response
                return {
                    "success": True,
                    "content": "Mock AI response for testing",
                    "data": {"status": "operational", "mock": True}
                }
        
        # Try to extract context from prompt if not provided (for grant matching)
        org_profile = None
        grant_data = None
        
        if context:
            org_profile = context.get('org_profile')
            grant_data = context.get('grant_data')
        elif "match" in prompt.lower() or "fit" in prompt.lower():
            # Try to extract org/grant data from prompt for fallback
            # This is a best-effort extraction for backward compatibility
            try:
                import re
                # Look for organization context
                org_match = re.search(r'ORGANIZATION.*?(?=GRANT|===|\Z)', prompt, re.DOTALL)
                grant_match = re.search(r'GRANT.*?(?=STRATEGIC|ANALYSIS|===|\Z)', prompt, re.DOTALL)
                
                if org_match or grant_match:
                    # Create basic context for fallback
                    org_profile = {}
                    grant_data = {}
                    logger.debug("Extracting context from prompt for fallback scoring")
            except:
                pass
        
        # Apply intelligent prompt reduction if prompt is too long
        original_length = len(prompt)
        if original_length > 2000:  # Reduce prompts over 2000 chars
            prompt = self._reduce_prompt_intelligently(prompt, 0.6)
            logger.info(f"Prompt reduced from {original_length} to {len(prompt)} characters for performance")
        
        messages = [
            {"role": "system", "content": "You are an expert grant analyst. Always respond with valid json format."},
            {"role": "user", "content": f"{prompt}\n\nPlease provide your response in json format."}
        ]
        
        def _make_ai_request():
            return self._make_request(
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=max_tokens
            )
        
        # Use circuit breaker for resilience
        try:
            result = self.circuit_breaker.call(_make_ai_request)
            if result:
                return result
            else:
                logger.warning("Circuit breaker returned None - using timeout fallback")
                # Use enhanced fallback with context if available
                if "match" in prompt.lower() or "fit" in prompt.lower() or "score" in prompt.lower():
                    return self._get_timeout_fallback_response(org_profile, grant_data)
                else:
                    return self._get_timeout_fallback_response()
        except Exception as e:
            logger.error(f"Circuit breaker caught exception: {e}")
            # Use enhanced fallback with context if available
            if "match" in prompt.lower() or "fit" in prompt.lower() or "score" in prompt.lower():
                return self._get_error_fallback_response(org_profile, grant_data)
            else:
                return self._get_error_fallback_response()
    
    def match_grant(self, org_profile: Dict, grant: Dict, funder_profile: Optional[Dict] = None) -> Tuple[Optional[int], Optional[str]]:
        """
        Enhanced grant matching with comprehensive organization data and authentic funder intelligence
        Returns: (fit_score: 1-5, reason: str) or (None, None) if disabled
        With fallback to keyword matching when AI is unavailable
        """
        # If AI is disabled, use fallback scoring directly
        if not self.is_enabled():
            logger.info("AI not enabled - using fallback keyword scoring")
            fallback_result = self._get_fallback_match_score(org_profile, grant)
            return fallback_result.get("match_score", 3), fallback_result.get("recommendation", "Manual review recommended")
        
        try:
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
                max_tokens=500,
                task_type="score_grant_match"  # Critical task - uses GPT-4o
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
                    # Use fallback if parsing fails
                    fallback_result = self._get_fallback_match_score(org_profile, grant)
                    return fallback_result.get("match_score", 3), fallback_result.get("recommendation", "Unable to determine fit score")
            else:
                # No result from AI - use fallback
                logger.warning("No AI result - using fallback keyword scoring")
                fallback_result = self._get_fallback_match_score(org_profile, grant)
                return fallback_result.get("match_score", 3), fallback_result.get("recommendation", "Manual review recommended")
                
        except Exception as e:
            # Any error - use fallback
            logger.error(f"Error in match_grant: {e} - using fallback")
            fallback_result = self._get_fallback_match_score(org_profile, grant)
            return fallback_result.get("match_score", 3), fallback_result.get("recommendation", "Error occurred - manual review recommended")
    
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
    
    def _build_grant_context_with_funder_intelligence(self, grant: Dict, funder_profile: Optional[Dict] = None) -> str:
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
        
        return result or {}
    
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
        
        if result:
            # Handle both string and dict responses
            if isinstance(result, dict):
                return result.get("content")
            else:
                return result
        return None
    
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
