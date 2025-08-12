"""
Writing Assistant Service for GrantFlow

This service provides AI-powered writing assistance for grant proposals.
"""

import logging
import os
from openai import OpenAI

# Set up logger
logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Define proposal section types
SECTION_TYPES = {
    "project_summary": "A concise overview of the project",
    "problem_statement": "Description of the problem being addressed",
    "goals_objectives": "Clear, measurable goals and objectives",
    "methodology": "Approach and methods to achieve the goals",
    "evaluation_plan": "How success will be measured",
    "sustainability": "How the project will continue after funding ends",
    "organizational_background": "History and capacity of the organization",
    "budget_justification": "Explanation of the requested budget items"
}

def generate_section_content(section_type, grant_info, org_info, inputs=None):
    """
    Generate content for a specific section of a grant proposal
    
    Args:
        section_type (str): Type of proposal section
        grant_info (dict): Information about the grant
        org_info (dict): Information about the organization
        inputs (dict, optional): Additional user inputs specific to the section
        
    Returns:
        dict: Generated content and related guidance
    """
    try:
        # Validate section type
        if section_type not in SECTION_TYPES:
            return {
                "success": False,
                "error": f"Invalid section type. Choose from: {', '.join(SECTION_TYPES.keys())}"
            }
            
        # Construct prompt based on section type and available information
        prompt = _construct_section_prompt(section_type, grant_info, org_info, inputs)
        
        # Generate content using OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": "You are an expert grant writer helping a nonprofit craft compelling grant proposal sections."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extract generated content
        content = response.choices[0].message.content
        generated_content = content.strip() if content else ""
        
        # Get writing tips for this section type
        writing_tips = _get_section_writing_tips(section_type)
        
        return {
            "success": True,
            "section_type": section_type,
            "section_description": SECTION_TYPES[section_type],
            "content": generated_content,
            "writing_tips": writing_tips
        }
        
    except Exception as e:
        logger.error(f"Error generating {section_type} content: {str(e)}")
        return {
            "success": False,
            "error": f"Error generating content: {str(e)}"
        }

def improve_section_content(section_type, current_content, feedback):
    """
    Improve existing content based on user feedback
    
    Args:
        section_type (str): Type of proposal section
        current_content (str): Existing section content
        feedback (str): User feedback for improvements
        
    Returns:
        dict: Improved content and feedback
    """
    try:
        # Validate section type
        if section_type not in SECTION_TYPES:
            return {
                "success": False,
                "error": f"Invalid section type. Choose from: {', '.join(SECTION_TYPES.keys())}"
            }
        
        # Construct prompt for content improvement
        prompt = f"""
        I need to improve the following {section_type} section in my grant proposal:
        
        --- CURRENT CONTENT ---
        {current_content}
        
        --- USER FEEDBACK ---
        {feedback}
        
        Please rewrite this section, addressing the feedback. Keep the same general structure
        but enhance the content as requested. Focus on clarity, impact, and persuasiveness.
        """
        
        # Generate improved content
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": "You are an expert grant writer helping a nonprofit revise and improve grant proposal sections."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extract generated content
        content = response.choices[0].message.content
        improved_content = content.strip() if content else ""
        
        return {
            "success": True,
            "section_type": section_type,
            "content": improved_content,
            "original_content": current_content,
            "feedback_addressed": feedback
        }
        
    except Exception as e:
        logger.error(f"Error improving {section_type} content: {str(e)}")
        return {
            "success": False,
            "error": f"Error improving content: {str(e)}"
        }

def generate_section_outline(section_type, grant_info, org_info):
    """
    Generate an outline/structure for a specific proposal section
    
    Args:
        section_type (str): Type of proposal section
        grant_info (dict): Information about the grant
        org_info (dict): Information about the organization
        
    Returns:
        dict: Outline with suggested points to cover
    """
    try:
        # Validate section type
        if section_type not in SECTION_TYPES:
            return {
                "success": False, 
                "error": f"Invalid section type. Choose from: {', '.join(SECTION_TYPES.keys())}"
            }
        
        # Construct prompt for outline generation
        prompt = f"""
        Generate a detailed outline for the {section_type} section of a grant proposal.
        
        --- GRANT INFORMATION ---
        Title: {grant_info.get('title', 'N/A')}
        Funder: {grant_info.get('funder', 'N/A')}
        Amount: ${grant_info.get('amount', 'N/A')}
        Focus Areas: {', '.join(grant_info.get('focus_areas', ['N/A']))}
        
        --- ORGANIZATION INFORMATION ---
        Name: {org_info.get('name', 'N/A')}
        Mission: {org_info.get('mission', 'N/A')}
        
        The outline should include:
        1. Key components that should be included in this section
        2. Suggested structure with subsections
        3. Important points to emphasize
        4. Potential pitfalls to avoid
        
        Format the output as a structured, easy-to-follow outline with bullet points.
        """
        
        # Generate outline
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": "You are an expert grant writing consultant who specializes in proposal structure and organization."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        # Extract generated outline
        content = response.choices[0].message.content
        outline = content.strip() if content else ""
        
        return {
            "success": True,
            "section_type": section_type,
            "section_description": SECTION_TYPES[section_type],
            "outline": outline
        }
        
    except Exception as e:
        logger.error(f"Error generating {section_type} outline: {str(e)}")
        return {
            "success": False,
            "error": f"Error generating outline: {str(e)}"
        }

def _construct_section_prompt(section_type, grant_info, org_info, inputs=None, funder_profile=None):
    """
    Enhanced prompt construction using comprehensive organization data and authentic funder intelligence
    
    Args:
        section_type (str): Type of proposal section
        grant_info (dict): Information about the grant
        org_info (dict): Comprehensive organization profile (30+ fields)
        inputs (dict, optional): Additional user inputs
        funder_profile (dict, optional): Authentic funder intelligence
        
    Returns:
        str: Enhanced strategic prompt
    """
    # Build comprehensive organization context
    org_context = _build_comprehensive_org_context_for_writing(org_info)
    
    # Build grant context with funder intelligence
    grant_context = _build_grant_context_for_writing(grant_info, funder_profile)
    
    # Enhanced strategic prompt
    prompt = f"""
    Write a strategic, compelling {section_type} section for a grant proposal that leverages comprehensive organizational intelligence and authentic funder data.
    
    {org_context}
    
    {grant_context}
    
    STRATEGIC WRITING REQUIREMENTS:
    1. Leverage the organization's unique strengths and capabilities
    2. Demonstrate clear alignment between organizational mission and grant purpose
    3. Use specific organizational achievements and data points
    4. Address funder's authentic priorities and success factors
    5. Show how organizational capacity matches grant requirements
    6. Integrate geographic alignment and service area compatibility
    7. Reference relevant previous funding experience and success rates
    """
    
    # Add section-specific instructions
    if section_type == "project_summary":
        prompt += """
        For the project summary:
        - Keep it concise (250-300 words)
        - Clearly state the problem, solution, and expected impact
        - Make it engaging and compelling from the first sentence
        - Include the funding amount requested and timeline
        - Emphasize alignment with funder's priorities
        """
        
    elif section_type == "problem_statement":
        prompt += """
        For the problem statement:
        - Use data and statistics to establish the significance of the problem
        - Connect the problem to the organization's mission
        - Explain why this problem needs to be addressed now
        - Show how the problem affects the specific community served
        - Cite relevant research or studies where appropriate
        """
        
    elif section_type == "goals_objectives":
        prompt += """
        For the goals and objectives section:
        - Create 2-3 overarching goals
        - For each goal, develop 2-3 SMART objectives (Specific, Measurable, Achievable, Relevant, Time-bound)
        - Connect objectives to addressing the problem statement
        - Include quantifiable metrics for measuring success
        - Show alignment with funder's priorities
        """
        
    elif section_type == "methodology":
        prompt += """
        For the methodology section:
        - Describe the approach and activities in detail
        - Explain why this approach was chosen (evidence-based, best practices)
        - Include a timeline for implementation
        - Identify key staff roles and responsibilities
        - Address potential challenges and how they'll be mitigated
        """
        
    elif section_type == "evaluation_plan":
        prompt += """
        For the evaluation plan:
        - Define clear success metrics for each objective
        - Describe data collection methods and tools
        - Explain how results will be analyzed and reported
        - Include both quantitative and qualitative measures
        - Describe how evaluation findings will inform future work
        """
        
    elif section_type == "sustainability":
        prompt += """
        For the sustainability section:
        - Explain how the project will continue after grant funding ends
        - Describe other funding sources (secured or planned)
        - Highlight organizational capacity to maintain the project
        - Show how the project builds lasting infrastructure or systems
        - Explain how success will be leveraged for future support
        """
        
    elif section_type == "organizational_background":
        prompt += """
        For the organizational background:
        - Briefly describe the organization's history and founding
        - Highlight key achievements and impact to date
        - Demonstrate expertise related to the proposed project
        - Include relevant partnerships and collaborations
        - Describe leadership capacity and qualifications
        """
        
    elif section_type == "budget_justification":
        prompt += """
        For the budget justification:
        - Provide clear rationale for each major budget item
        - Explain how costs were determined
        - Show that the budget is realistic and appropriate
        - Highlight any cost-sharing or leveraged resources
        - Connect budget items directly to project activities
        """
    
    # Add user inputs if provided
    if inputs:
        prompt += "\n\n--- ADDITIONAL INFORMATION ---\n"
        for key, value in inputs.items():
            prompt += f"{key}: {value}\n"
    
    # Final instructions
    prompt += """
    Write in a professional, clear, and compelling style. Use active voice and concrete examples.
    Focus on impact and outcomes rather than just activities. Avoid jargon unless it's necessary.
    Keep the funder's interests and priorities in mind throughout.
    """
    
    return prompt

def _build_comprehensive_org_context_for_writing(org_info):
    """Build comprehensive organization context for Smart Tools writing"""
    
    context_parts = []
    context_parts.append("=== COMPREHENSIVE ORGANIZATION PROFILE ===")
    
    # Core Identity
    if org_info.get('name'):
        context_parts.append(f"Organization: {org_info.get('name')}")
    if org_info.get('legal_name') and org_info.get('legal_name') != org_info.get('name'):
        context_parts.append(f"Legal Name: {org_info.get('legal_name')}")
    if org_info.get('org_type'):
        context_parts.append(f"Organization Type: {org_info.get('org_type')}")
    if org_info.get('year_founded'):
        context_parts.append(f"Founded: {org_info.get('year_founded')}")
    
    # Mission, Vision & Values
    if org_info.get('mission'):
        context_parts.append(f"Mission: {org_info.get('mission')}")
    if org_info.get('vision'):
        context_parts.append(f"Vision: {org_info.get('vision')}")
    if org_info.get('values'):
        context_parts.append(f"Core Values: {org_info.get('values')}")
    
    # Program Focus & Services
    primary_focus = org_info.get('primary_focus_areas', [])
    if primary_focus:
        context_parts.append(f"Primary Focus Areas: {', '.join(primary_focus)}")
    
    if org_info.get('programs_services'):
        context_parts.append(f"Programs & Services: {org_info.get('programs_services')}")
    
    target_demos = org_info.get('target_demographics', [])
    if target_demos:
        context_parts.append(f"Target Demographics: {', '.join(target_demos)}")
    
    age_groups = org_info.get('age_groups_served', [])
    if age_groups:
        context_parts.append(f"Age Groups Served: {', '.join(age_groups)}")
    
    # Geographic Scope
    if org_info.get('service_area_type'):
        context_parts.append(f"Service Area: {org_info.get('service_area_type')}")
    
    location_parts = []
    if org_info.get('primary_city'):
        location_parts.append(org_info.get('primary_city'))
    if org_info.get('primary_state'):
        location_parts.append(org_info.get('primary_state'))
    if location_parts:
        context_parts.append(f"Primary Location: {', '.join(location_parts)}")
    
    # Organizational Capacity
    if org_info.get('annual_budget_range'):
        context_parts.append(f"Annual Budget: {org_info.get('annual_budget_range')}")
    if org_info.get('staff_size'):
        context_parts.append(f"Staff Size: {org_info.get('staff_size')}")
    if org_info.get('people_served_annually'):
        context_parts.append(f"People Served Annually: {org_info.get('people_served_annually')}")
    
    # Track Record & Achievements
    if org_info.get('key_achievements'):
        context_parts.append(f"Key Achievements: {org_info.get('key_achievements')}")
    if org_info.get('previous_funders'):
        funders = org_info.get('previous_funders', [])
        context_parts.append(f"Previous Funders: {', '.join(funders[:3])}")
    if org_info.get('grant_success_rate'):
        context_parts.append(f"Grant Success Rate: {org_info.get('grant_success_rate')}%")
    
    # Special Characteristics
    special_chars = []
    if org_info.get('faith_based'):
        special_chars.append('Faith-based')
    if org_info.get('minority_led'):
        special_chars.append('Minority-led')
    if org_info.get('woman_led'):
        special_chars.append('Woman-led')
    if special_chars:
        context_parts.append(f"Special Characteristics: {', '.join(special_chars)}")
    
    # Unique Capabilities
    if org_info.get('unique_capabilities'):
        context_parts.append(f"Unique Capabilities: {org_info.get('unique_capabilities')}")
    
    return '\n'.join(context_parts)

def _build_grant_context_for_writing(grant_info, funder_profile=None):
    """Build enhanced grant context with authentic funder intelligence"""
    
    context_parts = []
    context_parts.append("=== GRANT OPPORTUNITY ANALYSIS ===")
    
    # Basic Grant Details
    context_parts.append(f"Grant Title: {grant_info.get('title', 'Not specified')}")
    context_parts.append(f"Funder: {grant_info.get('funder', 'Not specified')}")
    
    if grant_info.get('description'):
        context_parts.append(f"Description: {grant_info.get('description')}")
    
    # Financial Details
    amount_min = grant_info.get('amount_min', 0)
    amount_max = grant_info.get('amount_max', 0)
    if amount_min or amount_max:
        if amount_min == amount_max:
            context_parts.append(f"Grant Amount: ${amount_max:,}")
        else:
            context_parts.append(f"Amount Range: ${amount_min:,} - ${amount_max:,}")
    
    if grant_info.get('deadline'):
        context_parts.append(f"Deadline: {grant_info.get('deadline')}")
    
    focus_areas = grant_info.get('focus_areas', [])
    if focus_areas:
        if isinstance(focus_areas, list):
            context_parts.append(f"Focus Areas: {', '.join(focus_areas)}")
        else:
            context_parts.append(f"Focus Areas: {focus_areas}")
    
    # Authentic Funder Intelligence (if available)
    if funder_profile:
        context_parts.append("\n=== AUTHENTIC FUNDER INTELLIGENCE ===")
        
        if funder_profile.get('verified_overview'):
            context_parts.append(f"Funder Mission: {funder_profile.get('verified_overview')}")
        
        if funder_profile.get('funding_priorities'):
            priorities = funder_profile.get('funding_priorities', [])
            context_parts.append(f"Funding Priorities: {', '.join(priorities)}")
        
        if funder_profile.get('success_factors'):
            factors = funder_profile.get('success_factors', [])
            context_parts.append(f"Success Factors: {', '.join(factors[:3])}")
        
        if funder_profile.get('typical_grant_amounts'):
            context_parts.append(f"Typical Grant Range: {funder_profile.get('typical_grant_amounts')}")
        
        if funder_profile.get('geographic_focus'):
            context_parts.append(f"Geographic Focus: {funder_profile.get('geographic_focus')}")
    
    return '\n'.join(context_parts)

def generate_narrative(grant, org_profile, section):
    """
    Generate a narrative section for a grant proposal
    
    Args:
        grant (dict): The grant information
        org_profile (dict): The organization profile
        section (str): The name of the section to write
        
    Returns:
        str: Generated narrative section
    """
    try:
        # Check if OpenAI client is available
        if not openai_client:
            logger.error("OpenAI API key not configured")
            return "OpenAI API key not configured. Please provide an API key to use this feature."
        
        # System prompt for OpenAI
        system_prompt = """You are a grant writing assistant. Input:
1. grant: an object with title, summary, due_date, amount, eligibility_criteria
2. org_profile: an object with mission, focus_areas, funding_priorities
3. section: the name of the section to write, for example 'Need Statement'
Write a clear, persuasive section of about 200 words in a friendly and professional tone. Return plain text."""
        
        # Prepare data for API call
        data = {
            "grant": grant,
            "org_profile": org_profile,
            "section": section
        }
        
        # Make API call to OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": str(data)}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        # Return the generated text
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating narrative section: {str(e)}")
        return f"Error generating narrative section: {str(e)}"

def _get_section_writing_tips(section_type):
    """
    Get writing tips for a specific section type
    
    Args:
        section_type (str): Type of proposal section
        
    Returns:
        list: Writing tips for the section
    """
    # Common tips for all sections
    common_tips = [
        "Use active voice rather than passive voice",
        "Be specific and concrete rather than vague or abstract",
        "Address the funder's priorities and interests",
        "Use data and evidence to support your points",
        "Avoid jargon and acronyms unless they're well-explained"
    ]
    
    # Section-specific tips
    section_tips = {
        "project_summary": [
            "Start with a compelling hook to grab attention",
            "Include the funding amount requested and project duration",
            "Briefly address the problem, solution, and impact",
            "Write this section last, after completing other sections",
            "Keep it under 300 words for readability"
        ],
        "problem_statement": [
            "Use statistics and data to establish significance",
            "Focus on the problem you can solve, not the entire issue",
            "Connect to your organization's mission and expertise",
            "Cite credible sources for your data and research",
            "Show the consequences of not addressing the problem"
        ],
        "goals_objectives": [
            "Make objectives SMART (Specific, Measurable, Achievable, Relevant, Time-bound)",
            "Align objectives with the problem statement",
            "Limit to 2-3 main goals with 2-3 objectives each",
            "Use action verbs like 'increase,' 'reduce,' 'improve'",
            "Include baseline data when available"
        ],
        "methodology": [
            "Describe activities in chronological order or by goal",
            "Explain why you chose this approach (evidence-based, best practices)",
            "Include a timeline or implementation schedule",
            "Address potential challenges and how you'll overcome them",
            "Connect methods directly to your objectives"
        ],
        "evaluation_plan": [
            "Include both process and outcome measures",
            "Specify data collection methods and frequency",
            "Identify who will be responsible for evaluation",
            "Describe how results will be used to improve the project",
            "Include both quantitative and qualitative measures"
        ],
        "sustainability": [
            "Be specific about future funding sources",
            "Describe how the project builds lasting capacity",
            "Explain how you'll share results and lessons learned",
            "Highlight organizational commitment to continuing the work",
            "Address both financial and programmatic sustainability"
        ],
        "organizational_background": [
            "Focus on relevant experience and expertise",
            "Highlight successful similar projects",
            "Include qualifications of key staff members",
            "Mention relevant partnerships and collaborations",
            "Keep it focused on capacity related to this project"
        ],
        "budget_justification": [
            "Connect each budget item to specific activities",
            "Explain how costs were calculated",
            "Highlight cost-effectiveness and efficiency",
            "Mention any in-kind or matching contributions",
            "Ensure all major expenses are justified"
        ]
    }
    
    # Combine common tips with section-specific tips
    return section_tips.get(section_type, []) + common_tips