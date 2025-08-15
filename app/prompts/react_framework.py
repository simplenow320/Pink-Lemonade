"""
REACT Framework Implementation
Role, Example, Application, Context, Tone, Output framework for enhanced prompting
"""

from typing import Dict, Any, Optional, List

class REACTFramework:
    """Enhanced prompting using REACT methodology"""
    
    @staticmethod
    def build_enhanced_prompt(
        task_type: str,
        base_prompt: str,
        context: Dict[str, Any],
        examples: Optional[List[str]] = None,
        tone: str = "professional",
        output_format: str = "structured"
    ) -> Dict[str, str]:
        """
        Build enhanced prompt using REACT framework
        
        Args:
            task_type: Type of task (matching, writing, analysis, etc.)
            base_prompt: Original prompt text
            context: Contextual information
            examples: Example outputs (optional)
            tone: Desired response tone
            output_format: Expected output structure
            
        Returns:
            Dictionary with system and user prompts
        """
        
        # ROLE: Define expert persona
        roles = {
            "grant_matching": {
                "title": "Senior Grant Strategy Consultant",
                "expertise": "15+ years analyzing nonprofit-funder alignment",
                "specialties": "mission alignment, capacity assessment, strategic fit analysis"
            },
            "narrative_writing": {
                "title": "Expert Grant Writer", 
                "expertise": "20+ years crafting winning proposals",
                "specialties": "compelling storytelling, evidence-based arguments, funder psychology"
            },
            "data_extraction": {
                "title": "Data Intelligence Specialist",
                "expertise": "10+ years in grant opportunity analysis",
                "specialties": "accurate data extraction, source verification, systematic analysis"
            },
            "impact_analysis": {
                "title": "Impact Measurement Expert",
                "expertise": "12+ years in outcome evaluation",
                "specialties": "metrics development, evaluation design, results interpretation"
            },
            "strategic_analysis": {
                "title": "Nonprofit Strategy Advisor",
                "expertise": "18+ years in organizational development",
                "specialties": "strategic planning, capacity building, sustainability planning"
            }
        }
        
        role_info = roles.get(task_type, {
            "title": "AI Grant Management Specialist",
            "expertise": "Comprehensive nonprofit support",
            "specialties": "grant management, strategic guidance, operational efficiency"
        })
        
        # EXAMPLE: Provide sample outputs
        example_outputs = {
            "grant_matching": """
            Example Response:
            {
              "fit_score": 4,
              "reason": "Strong mission alignment with youth development focus and established program track record",
              "explanation": "Organization's 5-year youth mentorship program directly aligns with funder's education initiative priorities...",
              "strengths": ["Proven program model", "Target demographic match", "Geographic alignment"],
              "considerations": ["Budget justification needed", "Evaluation plan required"]
            }""",
            "narrative_writing": """
            Example Opening:
            "For over a decade, [Organization] has transformed lives in [Community] through innovative programs that address [Specific Need]. Our evidence-based approach has yielded measurable results: [Specific Metric]. This proposal outlines how [Grant] will amplify our impact..."
            """,
            "data_extraction": """
            Example Output:
            {
              "title": "Community Health Initiative Grant",
              "funder": "XYZ Foundation", 
              "amount_max": 50000,
              "deadline": "2024-03-15",
              "eligibility": "501(c)(3) nonprofits serving underserved communities"
            }"""
        }
        
        # APPLICATION: Specific use case guidance
        applications = {
            "grant_matching": "Analyze strategic fit between nonprofit organization and funding opportunity, providing actionable intelligence for pursuit decisions",
            "narrative_writing": "Create compelling, evidence-based narratives that align organizational strengths with funder priorities",
            "data_extraction": "Extract accurate, structured information from grant announcements and funding notices",
            "impact_analysis": "Evaluate program outcomes and develop metrics for demonstrating organizational impact",
            "strategic_analysis": "Provide strategic recommendations for organizational development and capacity building"
        }
        
        # CONTEXT: Build comprehensive background
        context_elements = []
        if context.get("organization"):
            context_elements.append(f"Organization Profile: {context['organization']}")
        if context.get("grant_opportunity"):
            context_elements.append(f"Grant Opportunity: {context['grant_opportunity']}")
        if context.get("funder_info"):
            context_elements.append(f"Funder Intelligence: {context['funder_info']}")
        if context.get("constraints"):
            context_elements.append(f"Constraints & Requirements: {context['constraints']}")
        if context.get("goals"):
            context_elements.append(f"Desired Outcomes: {context['goals']}")
        
        # TONE: Communication style
        tone_guidelines = {
            "professional": "Maintain formal, business-appropriate language with expertise and authority",
            "consultative": "Provide advisory guidance with strategic insights and recommendations", 
            "analytical": "Use data-driven language with logical reasoning and evidence-based conclusions",
            "persuasive": "Employ compelling language that builds strong cases and arguments",
            "collaborative": "Use inclusive language that suggests partnership and shared goals"
        }
        
        # OUTPUT: Structure requirements
        output_structures = {
            "json": "Provide response in valid JSON format with specified fields",
            "structured": "Use clear headings, bullet points, and organized sections",
            "narrative": "Provide flowing, paragraph-based content with logical progression",
            "bulleted": "Use concise bullet points with clear, actionable items",
            "analytical": "Present findings with evidence, reasoning, and conclusions"
        }
        
        # Build system prompt
        system_prompt = f"""ROLE: You are a {role_info['title']} with {role_info['expertise']}. Your specialties include {role_info['specialties']}.

APPLICATION: {applications.get(task_type, 'Provide expert assistance with grant management tasks')}

CONTEXT AWARENESS:
{chr(10).join(context_elements) if context_elements else 'Operating with general grant management context'}

COMMUNICATION STANDARDS:
- Tone: {tone_guidelines.get(tone, tone_guidelines['professional'])}
- Accuracy: Use only verified information from provided sources
- Completeness: Address all aspects of the request thoroughly
- Actionability: Provide specific, implementable guidance

GLOBAL GUARDRAILS:
- Never fabricate contact information, dates, or funding amounts
- Base all recommendations on factual data from provided sources
- Maintain nonprofit sector best practices and ethical standards
- Ensure compliance with grant application requirements and funder guidelines"""

        # Build user prompt with chain of thought
        user_prompt = f"""TASK: {base_prompt}

THINKING PROCESS:
Please approach this systematically:
1. ANALYZE: First, review all provided information and identify key elements
2. EVALUATE: Then, assess the strategic implications and relevant factors  
3. SYNTHESIZE: Next, integrate insights to form comprehensive understanding
4. RECOMMEND: Finally, provide clear, actionable guidance or output

{example_outputs.get(task_type, '') if examples is None else chr(10).join(examples)}

OUTPUT REQUIREMENTS:
{output_structures.get(output_format, output_structures['structured'])}

Please proceed with your analysis and response:"""

        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    @staticmethod
    def get_chain_of_thought_structure(complexity_level: str) -> str:
        """Get appropriate chain of thought structure based on complexity"""
        
        structures = {
            "simple": """
            1. Identify key requirements
            2. Apply relevant criteria
            3. Provide clear answer""",
            
            "moderate": """
            1. Analyze the context and requirements
            2. Evaluate available options or factors
            3. Apply expert judgment and best practices
            4. Synthesize findings into recommendation""",
            
            "complex": """
            1. Comprehensively analyze all provided information
            2. Identify strategic factors and constraints
            3. Evaluate multiple dimensions and trade-offs
            4. Apply expert knowledge and industry best practices
            5. Synthesize insights into actionable recommendations
            6. Validate recommendations against success criteria"""
        }
        
        return structures.get(complexity_level, structures["moderate"])
    
    @staticmethod 
    def enhance_existing_prompt(original_prompt: str, task_type: str, 
                              quality_level: str = "high") -> str:
        """
        Enhance an existing prompt with REACT elements
        
        Args:
            original_prompt: The existing prompt to enhance
            task_type: Type of task for role selection
            quality_level: Desired quality level (basic, high, premium)
            
        Returns:
            Enhanced prompt string
        """
        
        # Quality-based enhancements
        quality_additions = {
            "basic": "Please provide a clear and helpful response.",
            "high": "Please provide a comprehensive response with specific examples and actionable insights.",
            "premium": "Please provide an expert-level response with detailed analysis, strategic insights, and implementable recommendations that demonstrate deep understanding of nonprofit best practices."
        }
        
        role_context = {
            "grant_matching": "As a grant strategy expert,",
            "narrative_writing": "As a professional grant writer,", 
            "data_extraction": "As a data intelligence specialist,",
            "analysis": "As a strategic advisor,"
        }
        
        enhanced_prompt = f"""{role_context.get(task_type, 'As a nonprofit expert,')} {original_prompt}

Please approach this systematically and {quality_additions.get(quality_level, quality_additions['high'])}"""

        return enhanced_prompt