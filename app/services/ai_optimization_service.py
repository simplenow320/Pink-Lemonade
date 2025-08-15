"""
AI Optimization Service
Integrates smart model selection with existing AI services for cost optimization
Maintains backward compatibility while adding enhanced capabilities
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from app.services.ai_model_selector import AIModelSelector
from app.services.ai_service import AIService
from app.prompts.react_framework import REACTFramework

logger = logging.getLogger(__name__)

class AIOptimizationService:
    """
    Service that wraps existing AI functionality with cost optimization
    Maintains full backward compatibility while adding smart model selection
    """
    
    def __init__(self):
        """Initialize with both original and optimized AI services"""
        self.original_ai = AIService()  # Fallback to existing service
        self.model_selector = AIModelSelector()
        self.react_framework = REACTFramework()
        
        # Feature flags for gradual rollout
        self.optimization_enabled = True
        self.react_enhancement_enabled = True
        self.cost_tracking_enabled = True
        
        logger.info("AI Optimization Service initialized with backward compatibility")
    
    def is_enabled(self) -> bool:
        """Check if AI services are enabled"""
        return self.original_ai.is_enabled()
    
    def optimized_match_grant(self, org_profile: Dict, grant: Dict, 
                            funder_profile: Dict = None) -> Tuple[Optional[int], Optional[str]]:
        """
        Enhanced grant matching with cost optimization
        Maintains exact same interface as original AIService.match_grant()
        """
        if not self.is_enabled():
            return None, None
        
        try:
            if self.optimization_enabled:
                # Use optimized approach with smart model selection
                context = {
                    "organization": org_profile,
                    "grant_opportunity": grant,
                    "funder_info": funder_profile
                }
                
                # Build comprehensive context
                org_context = self._build_comprehensive_org_context(org_profile)
                grant_context = self._build_grant_context_with_funder_intelligence(grant, funder_profile)
                
                if self.react_enhancement_enabled:
                    # Enhanced prompt with REACT framework
                    base_prompt = f"""Analyze the strategic fit between this nonprofit organization and grant opportunity.

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
                    
                    enhanced_prompts = self.react_framework.build_enhanced_prompt(
                        task_type="grant_matching",
                        base_prompt=base_prompt,
                        context=context,
                        tone="analytical",
                        output_format="json"
                    )
                    
                    messages = [
                        {"role": "system", "content": enhanced_prompts["system"]},
                        {"role": "user", "content": enhanced_prompts["user"]}
                    ]
                else:
                    # Use original prompt format
                    messages = [
                        {"role": "system", "content": "You are an expert grant advisor analyzing grant-organization fit."},
                        {"role": "user", "content": base_prompt}
                    ]
                
                # Make optimized request (GPT-3.5 for matching scores)
                result = self.model_selector.make_optimized_request(
                    messages=messages,
                    task_type="grant_matching_score",  # Simple scoring task -> GPT-3.5
                    complexity_score=0.4,  # Medium complexity
                    response_format={"type": "json_object"},
                    max_tokens=500
                )
                
                if result:
                    try:
                        fit_score = int(result.get("fit_score", 3))
                        reason = result.get("reason", "Standard grant analysis completed")
                        
                        # Log cost optimization
                        model_used = result.get("_model_used", "unknown")
                        logger.info(f"Grant matching completed using {model_used}")
                        
                        return fit_score, reason
                    except (ValueError, KeyError):
                        logger.warning("Could not parse optimized grant matching result, falling back")
                        
        except Exception as e:
            logger.error(f"Optimized grant matching failed: {e}, falling back to original service")
        
        # Fallback to original service
        return self.original_ai.match_grant(org_profile, grant, funder_profile)
    
    def optimized_generate_narrative(self, org_profile: Dict, grant: Optional[Dict],
                                   section: str, custom_instructions: str = "") -> Optional[str]:
        """
        Enhanced narrative generation with cost optimization
        Maintains exact same interface as original AIService.generate_grant_narrative()
        """
        if not self.is_enabled():
            return None
        
        try:
            if self.optimization_enabled:
                # Complex writing task -> Use GPT-4o for quality
                context = {
                    "organization": org_profile,
                    "grant_opportunity": grant,
                    "section": section,
                    "instructions": custom_instructions
                }
                
                if self.react_enhancement_enabled:
                    # Enhanced prompt with REACT framework
                    base_prompt = f"""Generate a professional grant proposal narrative for the {section} section.

Organization Information:
- Name: {org_profile.get('name', 'Organization')}
- Mission: {org_profile.get('mission', 'Not specified')}
- Website: {org_profile.get('website', 'Not specified')}
- Focus Areas: {org_profile.get('focus_areas', 'Not specified')}
- Programs: {org_profile.get('programs', 'Not specified')}
- Achievements: {org_profile.get('achievements', 'Not specified')}"""

                    if grant:
                        base_prompt += f"""

Grant Opportunity:
- Title: {grant.get('title', 'Not specified')}
- Funder: {grant.get('funder', 'Not specified')}
- Focus: {grant.get('focus_areas', 'Not specified')}
- Amount Range: ${grant.get('amount_min', 0):,} - ${grant.get('amount_max', 0):,}"""

                    if custom_instructions:
                        base_prompt += f"\nAdditional Instructions: {custom_instructions}"

                    base_prompt += """

Write a professional, compelling narrative (300-500 words) that:
1. Aligns with the funder's priorities
2. Uses specific examples and data where possible
3. Maintains a confident but not boastful tone
4. Focuses on impact and outcomes
5. Is ready for submission with minimal editing"""
                    
                    enhanced_prompts = self.react_framework.build_enhanced_prompt(
                        task_type="narrative_writing",
                        base_prompt=base_prompt,
                        context=context,
                        tone="persuasive",
                        output_format="narrative"
                    )
                    
                    messages = [
                        {"role": "system", "content": enhanced_prompts["system"]},
                        {"role": "user", "content": enhanced_prompts["user"]}
                    ]
                else:
                    # Use original format
                    messages = [
                        {"role": "system", "content": "You are an expert grant writer with 20 years of experience writing successful proposals."},
                        {"role": "user", "content": base_prompt}
                    ]
                
                # Use GPT-4o for complex writing tasks
                result = self.model_selector.make_optimized_request(
                    messages=messages,
                    task_type="narrative_generation",  # Complex writing -> GPT-4o
                    complexity_score=0.8,
                    max_tokens=1500,
                    require_quality=True  # Force GPT-4o for writing
                )
                
                if result:
                    content = result.get("content", "")
                    model_used = result.get("_model_used", "unknown")
                    logger.info(f"Narrative generation completed using {model_used}")
                    return content
                        
        except Exception as e:
            logger.error(f"Optimized narrative generation failed: {e}, falling back to original service")
        
        # Fallback to original service
        return self.original_ai.generate_grant_narrative(org_profile, grant, section, custom_instructions)
    
    def optimized_extract_grant_info(self, text: str) -> Optional[Dict]:
        """
        Enhanced grant info extraction with cost optimization
        Maintains exact same interface as original AIService.extract_grant_info()
        """
        if not self.is_enabled():
            return None
        
        try:
            if self.optimization_enabled:
                # Data extraction task -> Use GPT-3.5 for efficiency
                base_prompt = f"""Extract grant opportunity information from the following text.
        
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

                if self.react_enhancement_enabled:
                    context = {"source_text": text[:1000] + "..."}
                    enhanced_prompts = self.react_framework.build_enhanced_prompt(
                        task_type="data_extraction",
                        base_prompt=base_prompt,
                        context=context,
                        tone="analytical",
                        output_format="json"
                    )
                    
                    messages = [
                        {"role": "system", "content": enhanced_prompts["system"]},
                        {"role": "user", "content": enhanced_prompts["user"]}
                    ]
                else:
                    messages = [
                        {"role": "system", "content": "You are an expert at extracting structured grant information from text."},
                        {"role": "user", "content": base_prompt}
                    ]
                
                # Use GPT-3.5 for data extraction
                result = self.model_selector.make_optimized_request(
                    messages=messages,
                    task_type="data_extraction",  # Simple extraction -> GPT-3.5
                    complexity_score=0.3,
                    response_format={"type": "json_object"},
                    max_tokens=800
                )
                
                if result:
                    # Clean up amounts like original service
                    try:
                        if result.get("amount_min"):
                            result["amount_min"] = float(str(result["amount_min"]).replace(",", "").replace("$", ""))
                        if result.get("amount_max"):
                            result["amount_max"] = float(str(result["amount_max"]).replace(",", "").replace("$", ""))
                    except:
                        pass
                    
                    model_used = result.get("_model_used", "unknown")
                    logger.info(f"Grant extraction completed using {model_used}")
                    
                    # Remove optimization metadata before returning
                    result.pop("_model_used", None)
                    result.pop("_processing_time", None)
                    return result
                        
        except Exception as e:
            logger.error(f"Optimized grant extraction failed: {e}, falling back to original service")
        
        # Fallback to original service
        return self.original_ai.extract_grant_info(text)
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics and cost analysis"""
        if self.cost_tracking_enabled and self.model_selector:
            return self.model_selector.get_cost_analysis()
        return {"optimization_disabled": True}
    
    def _build_comprehensive_org_context(self, org_profile: Dict) -> str:
        """Build comprehensive organization context (copied from original AIService)"""
        context_parts = []
        
        # Basic information
        if org_profile.get('name'):
            context_parts.append(f"ORGANIZATION: {org_profile['name']}")
        
        if org_profile.get('mission'):
            context_parts.append(f"MISSION: {org_profile['mission']}")
        
        # Operational details
        if org_profile.get('website'):
            context_parts.append(f"Website: {org_profile['website']}")
        
        if org_profile.get('budget_range'):
            context_parts.append(f"Annual Budget: {org_profile['budget_range']}")
        
        # Geographic and demographic info
        if org_profile.get('service_areas'):
            if isinstance(org_profile['service_areas'], list):
                areas = ', '.join(org_profile['service_areas'])
            else:
                areas = org_profile['service_areas']
            context_parts.append(f"Service Areas: {areas}")
        
        if org_profile.get('target_demographics'):
            context_parts.append(f"Target Demographics: {org_profile['target_demographics']}")
        
        # Programs and focus areas
        if org_profile.get('programs'):
            context_parts.append(f"Programs/Services: {org_profile['programs']}")
        
        # Handle focus areas (can be list or comma-separated string)
        focus_areas = org_profile.get('focus_areas', [])
        if focus_areas:
            if isinstance(focus_areas, list):
                primary_focus = [area for area in focus_areas if area][:5]  # Limit to top 5
            else:
                primary_focus = [area.strip() for area in str(focus_areas).split(',') if area.strip()][:5]
            
            if primary_focus:
                context_parts.append(f"Primary Focus Areas: {', '.join(primary_focus)}")
        
        return "\n".join(context_parts)
    
    def _build_grant_context_with_funder_intelligence(self, grant: Dict, funder_profile: Dict = None) -> str:
        """Build grant context with funder intelligence (copied from original AIService)"""
        context_parts = []
        
        # Grant basic info
        if grant.get('title'):
            context_parts.append(f"GRANT OPPORTUNITY: {grant['title']}")
        
        if grant.get('funder'):
            context_parts.append(f"FUNDER: {grant['funder']}")
        
        if grant.get('description'):
            description = grant['description'][:500] + "..." if len(grant.get('description', '')) > 500 else grant.get('description', '')
            context_parts.append(f"Description: {description}")
        
        # Financial details
        amount_info = []
        if grant.get('amount_min') and grant.get('amount_max'):
            amount_info.append(f"Amount: ${grant['amount_min']:,} - ${grant['amount_max']:,}")
        elif grant.get('amount_max'):
            amount_info.append(f"Maximum Amount: ${grant['amount_max']:,}")
        elif grant.get('amount_min'):
            amount_info.append(f"Minimum Amount: ${grant['amount_min']:,}")
        
        if amount_info:
            context_parts.append(amount_info[0])
        
        # Requirements and focus
        if grant.get('focus_areas'):
            context_parts.append(f"Focus Areas: {grant['focus_areas']}")
        
        if grant.get('eligibility_criteria'):
            context_parts.append(f"Eligibility: {grant['eligibility_criteria']}")
        
        if grant.get('deadline'):
            context_parts.append(f"Deadline: {grant['deadline']}")
        
        # Geographic info
        if grant.get('geographic_focus'):
            context_parts.append(f"Geographic Focus: {grant['geographic_focus']}")
        
        # Add funder intelligence if available
        if funder_profile:
            context_parts.append("\nFUNDER INTELLIGENCE:")
            if funder_profile.get('giving_history'):
                context_parts.append(f"Giving History: {funder_profile['giving_history']}")
            if funder_profile.get('preferred_causes'):
                context_parts.append(f"Preferred Causes: {funder_profile['preferred_causes']}")
            if funder_profile.get('application_tips'):
                context_parts.append(f"Success Tips: {funder_profile['application_tips']}")
        
        return "\n".join(context_parts)