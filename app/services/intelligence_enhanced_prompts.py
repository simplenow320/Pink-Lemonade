"""
Intelligence-Enhanced Prompts for Smart Tools
$1000/hour consultant-level quality with deep personalization and website context integration
"""

from typing import Dict, Optional, List

def create_intelligence_enhanced_pitch_prompt(org_context: Dict, grant_context: Optional[Dict], 
                                            pitch_type: str, funder_intelligence: Dict, 
                                            competitive_landscape: Dict, optimal_messaging: Dict,
                                            website_context: Optional[Dict] = None) -> str:
    """Create $1000 consultant-level pitch prompt with deep personalization"""
    
    # Dynamically adjust content based on pitch type
    pitch_specs = {
        'elevator': {'words': 150, 'focus': 'emotional hook + urgent need', 'time': '30 seconds'},
        'executive': {'words': 500, 'focus': 'strategy + proven impact', 'time': '2 minutes'}, 
        'detailed': {'words': 1500, 'focus': 'comprehensive evidence + ROI', 'time': '5 minutes'}
    }
    spec = pitch_specs[pitch_type]
    
    # Extract deep website context
    org_voice = ""
    if website_context:
        voice = website_context.get('organization_voice', {})
        mission = website_context.get('mission_vision', {})
        programs = website_context.get('programs', [])
        team = website_context.get('team_leadership', {})
        testimonials = website_context.get('testimonials', [])
        awards = website_context.get('awards_recognition', [])
        impact_stories = website_context.get('impact_stories', [])
        key_stats = website_context.get('key_statistics', {})
        unique_props = website_context.get('unique_value_props', [])
        donation_lang = website_context.get('donation_language', {})
        
        org_voice = f"""
        
        🎯 DEEP ORGANIZATIONAL CONTEXT (From Website Analysis):
        
        Voice & Tone Profile:
        - Primary Tone: {voice.get('tone', 'professional')} - must match exactly
        - Writing Style: {voice.get('style', 'informative')} - maintain throughout
        - Formality Level: {voice.get('formality', 'formal')} - critical for authenticity
        - Emotional Register: {voice.get('emotion', 'passionate')} - infuse appropriately
        - Key Phrases They Use: {', '.join(voice.get('key_phrases', [])[:3])}
        
        Mission & Vision (Use Their Exact Language):
        - Mission Statement: {mission.get('mission', 'Not specified')[:200]}
        - Vision: {mission.get('vision', 'Not specified')[:200]}
        - Core Values: {', '.join(mission.get('values', [])[:5])}
        - Tagline: "{mission.get('tagline', '')}"
        
        Flagship Programs (Reference By Name):
        {chr(10).join([f"- {prog.get('name', 'Program')}: {prog.get('description', '')[:100]}" for prog in programs[:3]])}
        
        Leadership Credibility (Name-Drop When Appropriate):
        {chr(10).join([f"- {leader.get('name', 'Leader')}, {leader.get('title', 'Title')}: {leader.get('bio', '')[:100]}" for leader in team.get('leaders', [])[:2]])}
        
        Recent Awards & Recognition (Weave Into Credibility):
        {chr(10).join([f"- {award[:100]}" for award in awards[:3]])}
        
        Proven Impact Stories (Use Real Examples):
        {chr(10).join([f"- {story.get('title', 'Story')}: {story.get('summary', '')[:150]}" for story in impact_stories[:2]])}
        
        Key Statistics (Use Exact Numbers):
        - People Served: {key_stats.get('beneficiaries_served', 'N/A')}
        - Success Rate: {key_stats.get('success_rate', 'N/A')}
        - Years of Service: {key_stats.get('years_active', 'N/A')}
        - Geographic Reach: {key_stats.get('geographic_reach', 'N/A')}
        
        Unique Value Propositions (Emphasize These):
        {chr(10).join([f"- {prop[:100]}" for prop in unique_props[:3]])}
        
        Testimonials (Quote When Powerful):
        {chr(10).join([f'- "{test.get("quote", "")[:150]}" - {test.get("author", "")}' for test in testimonials[:2]])}
        
        Donation Language They Use:
        - CTA Style: {donation_lang.get('cta_style', 'Support our mission')}
        - Urgency Words: {', '.join(donation_lang.get('urgency_words', [])[:5])}
        - Impact Phrases: {', '.join(donation_lang.get('impact_phrases', [])[:3])}
        """
    
    # Build funder intelligence insights
    funder_insights = ""
    if funder_intelligence and funder_intelligence.get('recent_grants'):
        recent_grants = funder_intelligence['recent_grants'][:5]
        avg_amount = funder_intelligence.get('average_grant_size', 50000)
        focus_areas = funder_intelligence.get('focus_areas', [])
        decision_factors = funder_intelligence.get('decision_factors', [])
        giving_patterns = funder_intelligence.get('giving_patterns', {})
        board_members = funder_intelligence.get('board_members', [])
        funding_priorities = funder_intelligence.get('current_priorities', [])
        
        funder_insights = f"""
        
        🎯 FUNDER DEEP INTELLIGENCE (Candid + Research):
        
        Recent Grant Activity (Last 12 Months):
        {chr(10).join([f"- ${g.get('amount', 0):,.0f} to {g.get('recipient', 'Unknown')} for {g.get('purpose', 'general support')}" for g in recent_grants])}
        
        Funding Sweet Spot: ${avg_amount:,.0f} (target your ask here)
        
        Proven Interest Areas (Align Your Programs):
        {', '.join(focus_areas[:5])}
        
        Decision Factors They Value Most:
        {chr(10).join([f"- {factor}" for factor in decision_factors[:5]])}
        
        Giving Patterns & Preferences:
        - Prefers: {giving_patterns.get('prefers', 'multi-year commitments')}
        - Avoids: {giving_patterns.get('avoids', 'one-time events')}
        - Grant Cycle: {giving_patterns.get('cycle', 'Quarterly')}
        - Relationship Style: {giving_patterns.get('relationship', 'Hands-on partner')}
        
        Key Decision Makers:
        {chr(10).join([f"- {member.get('name', '')}, {member.get('title', '')}: {member.get('interests', '')}" for member in board_members[:3]])}
        
        Current Funding Priorities:
        {chr(10).join([f"- {priority}" for priority in funding_priorities[:3]])}
        """
    
    # Build grant-specific context
    grant_details = ""
    if grant_context:
        grant_details = f"""
        
        📋 SPECIFIC GRANT OPPORTUNITY:
        Title: {grant_context.get('title', 'Untitled')}
        Funder: {grant_context.get('funder', 'Unknown')}
        Amount Range: ${grant_context.get('amount_min', 0):,.0f} - ${grant_context.get('amount_max', 0):,.0f}
        Focus Area: {grant_context.get('focus_area', 'General')}
        Deadline: {grant_context.get('deadline', 'Open')}
        
        Eligibility Requirements:
        {grant_context.get('requirements', 'Standard nonprofit requirements')}
        
        What They're Looking For:
        {grant_context.get('priorities', 'Innovative, sustainable programs with measurable impact')}
        
        Application Components:
        {grant_context.get('components', 'LOI, full proposal, budget, board list')}
        
        Past Winners (Your Competition):
        {grant_context.get('past_recipients', 'Similar organizations in your sector')}
        """
    else:
        grant_details = "General pitch (no specific grant targeted) - Position for future opportunities"
    
    # Market intelligence insights with deeper analysis
    market_insights = ""
    if competitive_landscape:
        market_size = competitive_landscape.get('market_size', {})
        competitors = competitive_landscape.get('competitor_analysis', [])
        gaps = competitive_landscape.get('funding_gaps', [])
        success_prob = competitive_landscape.get('success_probability', 0)
        trends = competitive_landscape.get('market_trends', [])
        
        market_insights = f"""
        
        📊 COMPETITIVE LANDSCAPE INTELLIGENCE:
        
        Market Reality Check:
        - Total Funding Available: ${market_size.get('total_funding_available', 0):,.0f}
        - Active Funders in Your Space: {market_size.get('active_funders', 0)}
        - Competition Level: {market_size.get('competition_level', 'Moderate')} ({market_size.get('applications_per_grant', 50)} applications per grant)
        - Your Success Probability: {success_prob}% (vs 15% average)
        
        Critical Funding Gaps You Can Fill:
        {chr(10).join([f"- {gap}" for gap in gaps[:3]])}
        
        Your Top Competitors & Their Weaknesses:
        {chr(10).join([f"- {comp.get('name', 'Competitor')}: Weak on {comp.get('weakness', 'innovation')}, you're stronger on {comp.get('your_advantage', 'community engagement')}" for comp in competitors[:3]])}
        
        Market Trends to Leverage:
        {chr(10).join([f"- {trend}" for trend in trends[:3]])}
        
        Differentiation Strategy:
        Position as the only organization that {competitive_landscape.get('unique_position', 'combines direct service with systemic change')}
        """
    
    # Optimal messaging strategy with psychological insights
    messaging_guidance = ""
    if optimal_messaging:
        power_words = optimal_messaging.get('power_words', [])
        avoid_words = optimal_messaging.get('avoid_words', [])
        winning_themes = optimal_messaging.get('winning_themes', [])
        emotional_triggers = optimal_messaging.get('emotional_triggers', [])
        proven_frameworks = optimal_messaging.get('proven_frameworks', [])
        
        messaging_guidance = f"""
        
        💬 PSYCHOLOGICAL MESSAGING OPTIMIZATION:
        
        Power Words That Convert (Use 3-5):
        {', '.join(power_words[:10])}
        
        Fatal Words to Avoid (Never Use):
        {', '.join(avoid_words[:5])}
        
        Winning Narrative Themes (Pick One Primary):
        {chr(10).join([f"- {theme}" for theme in winning_themes[:3]])}
        
        Emotional Triggers That Work:
        {chr(10).join([f"- {trigger}" for trigger in emotional_triggers[:3]])}
        
        Proven Story Frameworks:
        {chr(10).join([f"- {framework}" for framework in proven_frameworks[:2]])}
        
        Psychological Principles to Apply:
        - Reciprocity: Show what you've already given
        - Social Proof: Reference other major funders
        - Authority: Cite endorsements and credentials
        - Scarcity: Limited opportunity to make impact
        - Unity: Shared values and vision
        """
    
    # Organization's actual data and credentials
    org_data = f"""
    
    📈 YOUR ORGANIZATION'S ACTUAL DATA:
    
    Organizational Profile:
    - Legal Name: {org_context.get('name', 'Organization')}
    - Founded: {org_context.get('founded_year', 'N/A')}
    - Tax Status: {org_context.get('tax_status', '501(c)(3)')}
    - EIN: {org_context.get('ein', 'XX-XXXXXXX')}
    - Annual Budget: ${org_context.get('annual_budget', 0):,.0f}
    - Staff Size: {org_context.get('staff_size', 0)} FTE
    - Board Members: {org_context.get('board_size', 0)}
    - Location: {org_context.get('location', 'City, State')}
    
    Proven Impact Metrics:
    - Total Beneficiaries Served: {org_context.get('total_beneficiaries', 0):,}
    - Programs Delivered: {org_context.get('programs_count', 0)}
    - Success Rate: {org_context.get('success_rate', 0)}%
    - Cost Per Outcome: ${org_context.get('cost_per_outcome', 0):,.0f}
    - ROI: {org_context.get('roi', 0)}:1
    
    Recent Achievements:
    {chr(10).join([f"- {achievement}" for achievement in org_context.get('recent_achievements', [])[:3]])}
    
    Current Initiatives:
    {chr(10).join([f"- {initiative}" for initiative in org_context.get('current_initiatives', [])[:3]])}
    
    Funding Track Record:
    - Grants Won (Last Year): {org_context.get('grants_won', 0)}
    - Total Secured: ${org_context.get('total_funding_secured', 0):,.0f}
    - Success Rate: {org_context.get('grant_success_rate', 0)}%
    - Average Grant Size: ${org_context.get('average_grant_size', 0):,.0f}
    - Renewal Rate: {org_context.get('renewal_rate', 0)}%
    
    Major Funders (Social Proof):
    {', '.join(org_context.get('major_funders', [])[:5])}
    """
    
    return f"""You are a $1000/hour fundraising consultant who has worked exclusively with {org_context.get('name', 'this organization')} for the past 5 years. You know every program, every success story, every staff member, and exactly how to position them for maximum funding success. Create an {pitch_type} grant pitch that sounds like it was written by their Executive Director after their best day ever.

    # R - ROLE
    You are not just any grant writer - you are {org_context.get('name')}'s secret weapon, their insider advocate who knows their organization better than they know themselves. You've helped them secure ${org_context.get('total_funding_secured', 0):,.0f} in funding with a {org_context.get('grant_success_rate', 25)}% success rate (vs 15% industry average). You know their voice, their stories, their data, and exactly what makes funders say yes.
    
    # E - EXAMPLE
    Your previous pitches for {org_context.get('name')} have won grants from {', '.join(org_context.get('major_funders', ['major foundations'])[:3])}. These winning pitches all:
    - Opened with a specific story about a real person they've helped
    - Used their exact voice and terminology (never generic nonprofit speak)
    - Positioned them as the ONLY organization that could solve this problem
    - Included precise data that proved ROI better than any alternative
    - Made the funder feel like a partner, not a ATM
    - Closed with an ask that felt inevitable, not pushy
    
    # A - APPLICATION  
    Create a {spec['words']}-word {pitch_type} pitch ({spec['time']} delivery) using the IMPACT framework customized for {org_context.get('name')}:
    
    I - Irresistible Hook: Open with {org_context.get('name')}'s most powerful story or statistic
    M - Mission Alignment: Connect YOUR specific programs to THEIR proven priorities  
    P - Proven Impact: Share real success metrics that beat sector benchmarks
    A - Achievable Ask: Request the exact amount they typically give
    C - Competitive Advantage: Explain why only {org_context.get('name')} can do this
    T - Timeline to Transform: Show quick wins (30 days) and long-term change (1 year)
    
    # C - CONTEXT
    {org_data}
    {org_voice}
    {grant_details}
    {funder_insights}
    {market_insights}
    {messaging_guidance}
    
    # T - TONE
    Write in {org_context.get('name')}'s authentic voice: {voice.get('tone', 'professional')} tone, {voice.get('style', 'informative')} style, {voice.get('formality', 'formal')} formality level. Include at least 2 of their key phrases. Reference at least 1 real program by name. Quote at least 1 actual testimonial. Mention at least 1 specific leader or board member. Sound like their Executive Director at their most persuasive, not like a generic grant writer.
    
    # O - OUTPUT
    Generate a pitch that {org_context.get('name')}'s own team would think they wrote. It must:
    1. Sound exactly like their website and materials
    2. Include specific names, programs, and numbers
    3. Reference their actual achievements and recognition
    4. Use their proven donation language
    5. Feel personal and authentic, not templated
    
    Return ONLY a valid JSON object:
    {{
        "pitch_text": "[Complete {spec['words']}-word pitch written in {org_context.get('name')}'s exact voice]",
        "hook": "[Opening line that makes them lean forward]",
        "programs_referenced": ["actual program 1", "actual program 2"],
        "statistics_used": ["real metric 1", "real metric 2", "real metric 3"],
        "testimonial_included": "[Actual quote from real person]",
        "ask_amount": {grant_context.get('amount_max', 50000) if grant_context else avg_amount if funder_intelligence else 50000},
        "competitive_advantages": ["unique advantage 1", "unique advantage 2", "unique advantage 3"],
        "funder_alignment_points": ["alignment 1", "alignment 2", "alignment 3"],
        "success_probability": {success_prob if competitive_landscape else 35},
        "word_count": {spec['words']},
        "delivery_time": "{spec['time']}",
        "voice_match_score": "[1-10 how well this matches their actual voice]",
        "personalization_elements": ["website element 1", "website element 2", "website element 3"]
    }}
    """

def create_intelligence_enhanced_case_prompt(org_context: Dict, campaign_details: Dict, 
                                           funder_intelligence: Dict, competitive_landscape: Dict, 
                                           optimal_messaging: Dict, website_context: Optional[Dict] = None) -> str:
    """Create $1000 consultant-level case for support with deep personalization"""
    
    # Extract comprehensive website context
    website_insights = ""
    if website_context:
        voice = website_context.get('organization_voice', {})
        mission = website_context.get('mission_vision', {})
        programs = website_context.get('programs', [])
        impact = website_context.get('impact_stories', [])
        testimonials = website_context.get('testimonials', [])
        team = website_context.get('team_leadership', {})
        awards = website_context.get('awards_recognition', [])
        partners = website_context.get('partners_funders', [])
        media = website_context.get('media_mentions', [])
        stats = website_context.get('key_statistics', {})
        
        website_insights = f"""
        
        🏆 COMPREHENSIVE ORGANIZATIONAL INTELLIGENCE:
        
        Writing DNA (Match Exactly):
        - Voice: {voice.get('tone', 'professional')} and {voice.get('emotion', 'passionate')}
        - Style: {voice.get('style', 'informative')} with {voice.get('formality', 'formal')} language
        - Signature Phrases: {chr(10).join(voice.get('key_phrases', [])[:5])}
        
        Core Identity (Weave Throughout):
        - Mission: {mission.get('mission', '')[:300]}
        - Vision: {mission.get('vision', '')[:300]}
        - Values: {', '.join(mission.get('values', [])[:7])}
        - Tagline: "{mission.get('tagline', '')}"
        
        Program Portfolio (Reference Specifically):
        {chr(10).join([f"- {prog.get('name', 'Program')}: {prog.get('description', '')[:150]} | Impact: {prog.get('outcomes', 'Strong results')}" for prog in programs[:5]])}
        
        Proven Impact Stories (Tell These Stories):
        {chr(10).join([f"- {story.get('title', 'Story')}: {story.get('summary', '')[:200]}" for story in impact[:4]])}
        
        Powerful Testimonials (Quote Liberally):
        {chr(10).join([f'"{test.get("quote", "")[:200]}" - {test.get("author", "")}, {test.get("role", "")}' for test in testimonials[:4]])}
        
        Leadership & Credibility:
        {chr(10).join([f"- {leader.get('name', '')}, {leader.get('title', '')}: {leader.get('credentials', '')}" for leader in team.get('leaders', [])[:4]])}
        
        Recognition & Validation:
        {chr(10).join([f"- {award[:150]}" for award in awards[:5]])}
        
        Media Coverage & Third-Party Validation:
        {chr(10).join([f"- {mention[:150]}" for mention in media[:4]])}
        
        Key Performance Indicators:
        - Total Served: {stats.get('beneficiaries_served', 'Thousands')}
        - Success Rate: {stats.get('success_rate', '85')}%
        - Geographic Reach: {stats.get('geographic_reach', 'Regional')}
        - Cost Efficiency: ${stats.get('cost_per_outcome', '100')} per outcome
        - Years Active: {stats.get('years_active', '10+')}
        
        Current Partners & Funders:
        {', '.join([str(p) for p in partners[:10]])}
        """
    
    # Deep campaign strategy
    campaign_strategy = f"""
    
    📋 CAMPAIGN STRATEGY & POSITIONING:
    
    Campaign Specifications:
    - Campaign Name: {campaign_details.get('title', 'Transformative Initiative')}
    - Funding Goal: ${campaign_details.get('funding_goal', 500000):,.0f}
    - Timeline: {campaign_details.get('timeline', '3 years')}
    - Use of Funds: {campaign_details.get('use_of_funds', '70% programs, 20% capacity, 10% evaluation')}
    
    Target Audience Segmentation:
    - Primary: {campaign_details.get('primary_audience', 'Major foundations ($50K+)')}
    - Secondary: {campaign_details.get('secondary_audience', 'Corporate partners')}
    - Tertiary: {campaign_details.get('tertiary_audience', 'Individual major donors')}
    
    Campaign Pillars:
    {chr(10).join([f"- Pillar {i+1}: {pillar}" for i, pillar in enumerate(campaign_details.get('pillars', ['Direct Service', 'Advocacy', 'Capacity Building'])[:3])])}
    
    Expected Outcomes:
    {chr(10).join([f"- {outcome}" for outcome in campaign_details.get('expected_outcomes', ['3x increase in beneficiaries', '50% cost reduction', 'Sustainable model'])[:5]])}
    
    Risk Mitigation:
    {chr(10).join([f"- Risk: {risk.get('description', '')} | Mitigation: {risk.get('mitigation', '')}" for risk in campaign_details.get('risks', [])[:3]])}
    """
    
    # Market and competitive analysis
    market_analysis = ""
    if competitive_landscape:
        market_size = competitive_landscape.get('market_size', {})
        gaps = competitive_landscape.get('funding_gaps', [])
        success_prob = competitive_landscape.get('success_probability', 0)
        competitors = competitive_landscape.get('competitor_analysis', [])
        
        market_analysis = f"""
        
        📈 MARKET POSITIONING & OPPORTUNITY:
        
        Market Opportunity:
        - Total Addressable Funding: ${market_size.get('total_funding_available', 0):,.0f}
        - Funders Aligned with Mission: {market_size.get('aligned_funders', 0)}
        - Competition Intensity: {market_size.get('competition_level', 'Moderate')}
        - Success Probability: {success_prob}% (2.3x industry average)
        
        Critical Gaps We Fill:
        {chr(10).join([f"- {gap} (Worth ${competitive_landscape.get('gap_values', {}).get(gap, 100000):,.0f} in funding)" for gap in gaps[:4]])}
        
        Competitive Advantages:
        {chr(10).join([f"- vs. {comp.get('name', 'Competitor')}: We're superior on {comp.get('your_advantage', 'innovation and scale')}" for comp in competitors[:3]])}
        
        Market Timing Factors:
        - Why Now: {competitive_landscape.get('timing_factors', ['Policy window', 'Increased awareness', 'Funding availability'])}
        - Urgency Drivers: {competitive_landscape.get('urgency_factors', ['Growing need', 'Limited window', 'First-mover advantage'])}
        """
    
    # Funder landscape intelligence
    funder_analysis = ""
    if funder_intelligence:
        top_prospects = funder_intelligence.get('top_prospects', [])
        giving_trends = funder_intelligence.get('giving_trends', {})
        decision_timeline = funder_intelligence.get('decision_timeline', {})
        
        funder_analysis = f"""
        
        💰 FUNDER LANDSCAPE INTELLIGENCE:
        
        Top Funding Prospects:
        {chr(10).join([f"- {p.get('name', '')}: ${p.get('typical_grant', 0):,.0f} | Interest: {p.get('alignment_score', 0)}% | Contact: {p.get('key_contact', 'Program Officer')}" for p in top_prospects[:7]])}
        
        Funding Trends & Insights:
        - Hot Topics: {', '.join(giving_trends.get('increasing_areas', [])[:5])}
        - Declining Areas: {', '.join(giving_trends.get('decreasing_areas', [])[:3])}
        - Average Grant Size (Trend): {giving_trends.get('average_trajectory', 'Increasing 10% annually')}
        
        Decision Timeline:
        - Initial Review: {decision_timeline.get('initial_review', '2-4 weeks')}
        - Due Diligence: {decision_timeline.get('due_diligence', '4-6 weeks')}
        - Board Decision: {decision_timeline.get('board_decision', 'Quarterly')}
        - Funding Disbursement: {decision_timeline.get('disbursement', '30 days after approval')}
        """
    
    # Messaging optimization
    messaging_strategy = ""
    if optimal_messaging:
        messaging_strategy = f"""
        
        🎯 MESSAGING OPTIMIZATION STRATEGY:
        
        Core Narrative Arc:
        {optimal_messaging.get('narrative_arc', 'Problem → Solution → Impact → Scale → Sustainability')}
        
        Emotional Journey:
        {optimal_messaging.get('emotional_journey', 'Concern → Hope → Excitement → Commitment → Partnership')}
        
        Power Language:
        - Hero Words: {', '.join(optimal_messaging.get('power_words', [])[:10])}
        - Proof Words: {', '.join(optimal_messaging.get('proof_words', ['proven', 'validated', 'demonstrated'])[:5])}
        - Impact Words: {', '.join(optimal_messaging.get('impact_words', ['transform', 'revolutionize', 'catalyze'])[:5])}
        
        Winning Themes:
        {chr(10).join([f"- {theme}: {optimal_messaging.get('theme_descriptions', {}).get(theme, '')}" for theme in optimal_messaging.get('winning_themes', [])[:4]])}
        
        Credibility Builders:
        {chr(10).join(optimal_messaging.get('credibility_elements', ['Third-party validation', 'Data and metrics', 'Success stories', 'Partner endorsements'])[:5])}
        """
    
    return f"""You are a $1000/hour senior fundraising strategist who has been embedded with {org_context.get('name', 'this organization')} for 5 years. You've written cases that have raised over $50 million for similar organizations. You know {org_context.get('name')}'s story better than anyone and can articulate their value proposition in a way that makes funding feel inevitable, not optional.

    # R - ROLE
    You are {org_context.get('name')}'s Chief Development Strategist, ghostwriting for their Executive Director and Board Chair. You have intimate knowledge of every program, every success story, every metric, and every relationship. You've studied what makes their funders say yes and you know exactly how to position them as the best investment, not just a good cause.
    
    # E - EXAMPLE  
    Your previous Cases for Support have:
    - Secured ${org_context.get('largest_grant', 500000):,.0f} from {org_context.get('largest_funder', 'a major foundation')}
    - Achieved a {org_context.get('case_success_rate', 65)}% funding success rate
    - Generated {org_context.get('roi_from_cases', 15)}:1 ROI on case development investment
    - Won competitive grants against organizations 5x their size
    - Created lasting funder partnerships, not just transactions
    
    Winning cases you've written always:
    - Open with a story that makes the reader feel the problem viscerally
    - Present the organization as the only logical solution
    - Include data that proves ROI better than any alternative investment
    - Build trust through third-party validation and social proof
    - Make the ask feel like an opportunity, not an obligation
    - Close with a vision of the world the funder can help create
    
    # A - APPLICATION
    Create a comprehensive 2,500-word Case for Support using the TRANSFORM framework customized for {org_context.get('name')}:
    
    T - Transformative Vision: Paint the world {org_context.get('name')} is creating
    R - Rigorous Evidence: Prove impact with {org_context.get('name')}'s actual data
    A - Achievable Roadmap: Show {org_context.get('name')}'s specific implementation plan
    N - Necessary Urgency: Explain why {org_context.get('name')} must act now
    S - Strategic Partnerships: Position funders as partners in {org_context.get('name')}'s mission
    F - Financial Clarity: Present {org_context.get('name')}'s budget and ROI transparently
    O - Outcomes Guaranteed: Promise specific results {org_context.get('name')} will deliver
    R - Return on Investment: Quantify social ROI of investing in {org_context.get('name')}
    M - Movement Building: Show how {org_context.get('name')} is leading sector transformation
    
    # C - CONTEXT
    
    Organization Reality:
    - Name: {org_context.get('name')}
    - Years Active: {org_context.get('years_active', 10)}
    - Annual Budget: ${org_context.get('annual_budget', 1000000):,.0f}
    - Total Beneficiaries Served: {org_context.get('total_beneficiaries', 10000):,}
    - Cost Per Outcome: ${org_context.get('cost_per_outcome', 100):,.0f}
    - Success Rate: {org_context.get('success_rate', 85)}%
    
    {website_insights}
    {campaign_strategy}
    {market_analysis}
    {funder_analysis}
    {messaging_strategy}
    
    # T - TONE
    Write in {org_context.get('name')}'s authentic voice - {website_context.get('organization_voice', {}).get('tone', 'professional')} yet {website_context.get('organization_voice', {}).get('emotion', 'passionate')}, with {website_context.get('organization_voice', {}).get('formality', 'formal')} language. Use their actual program names, quote their real testimonials, reference their specific achievements. This should read like it was written by someone who bleeds {org_context.get('name')}'s colors, not a hired consultant.
    
    # O - OUTPUT
    Create a Case for Support that {org_context.get('name')}'s board would approve unanimously and funders would fund immediately.
    
    Return ONLY a valid JSON object with these exact fields:
    {{
        "executive_summary": "[200 words - The entire case in miniature, with compelling hook]",
        "problem_statement": "[300 words - The urgent problem only {org_context.get('name')} can solve]",
        "our_solution": "[350 words - {org_context.get('name')}'s unique approach and programs]", 
        "proven_impact": "[400 words - Specific evidence of {org_context.get('name')}'s success]",
        "theory_of_change": "[200 words - How {org_context.get('name')} creates lasting change]",
        "strategic_objectives": "[250 words - {campaign_details.get('title')}'s specific goals]",
        "implementation_plan": "[300 words - Detailed timeline and milestones]",
        "budget_narrative": "[250 words - Where the ${campaign_details.get('funding_goal', 500000):,.0f} goes]",
        "evaluation_framework": "[200 words - How {org_context.get('name')} measures success]",
        "sustainability_plan": "[200 words - Long-term viability beyond this campaign]",
        "partnership_opportunity": "[150 words - What funders gain by joining {org_context.get('name')}]",
        "call_to_action": "[100 words - The specific ask and next steps]",
        "appendix_items": ["Board list", "Audited financials", "Program evaluations", "Media coverage"],
        "testimonials_included": ["testimonial 1", "testimonial 2", "testimonial 3"],
        "programs_featured": ["program 1", "program 2", "program 3"],
        "metrics_highlighted": {{"beneficiaries": 0, "success_rate": 0, "cost_efficiency": 0, "roi": 0}},
        "competitive_positioning": "[How this positions {org_context.get('name')} vs competitors]",
        "funder_alignment_map": {{"funder_1": "alignment points", "funder_2": "alignment points"}},
        "word_count": 2500,
        "reading_time": "10 minutes",
        "emotional_arc": "[Description of emotional journey through document]",
        "credibility_score": "[1-10 based on evidence and validation included]"
    }}
    """

def create_intelligence_enhanced_impact_report_prompt(org_context: Dict, reporting_period: Dict,
                                                    metrics_data: Dict, competitive_landscape: Dict,
                                                    participant_stories: Optional[List] = None,
                                                    website_context: Optional[Dict] = None) -> str:
    """Create $1000 consultant-level impact report with real stories and data"""
    
    # Real participant stories and testimonials
    stories_section = ""
    if participant_stories:
        stories_section = f"""
        
        📖 REAL PARTICIPANT STORIES (Use These Exact Stories):
        {chr(10).join([f'''
        Story {i+1}: {story.get('participant_name', 'Participant')}
        - Background: {story.get('background', 'Came to us seeking help')}
        - Challenge: {story.get('challenge', 'Faced significant obstacles')}
        - Our Support: {story.get('support_provided', 'Comprehensive assistance')}
        - Outcome: {story.get('outcome', 'Transformative results')}
        - Quote: "{story.get('quote', 'This program changed my life')}"
        - Data Point: {story.get('metrics', 'Measurable improvement')}
        ''' for i, story in enumerate(participant_stories[:5])])}
        """
    
    # Website context for report styling
    report_style = ""
    if website_context:
        voice = website_context.get('organization_voice', {})
        impact = website_context.get('impact_stories', [])
        stats = website_context.get('key_statistics', {})
        
        report_style = f"""
        
        📊 ORGANIZATIONAL REPORTING STYLE:
        
        Voice for Reports:
        - Tone: {voice.get('tone', 'professional')} and data-driven
        - Emotion Level: {voice.get('emotion', 'passionate')} but factual
        - Technical Level: {voice.get('formality', 'formal')} with accessibility
        
        Historical Impact Context:
        {chr(10).join([f"- {story.get('title', '')}: {story.get('metrics', '')}" for story in impact[:3]])}
        
        Baseline Performance Metrics:
        - Historical Success Rate: {stats.get('success_rate', '85')}%
        - Cost Per Outcome Trend: ${stats.get('cost_per_outcome', '100')} (decreasing)
        - Geographic Reach: {stats.get('geographic_reach', 'Regional')}
        - Total Served to Date: {stats.get('beneficiaries_served', 'Thousands')}
        """
    
    # Comprehensive metrics analysis
    metrics_analysis = f"""
    
    📈 REPORTING PERIOD METRICS:
    
    Core Performance Indicators:
    - Beneficiaries Served: {metrics_data.get('beneficiaries_served', 1000):,} ({metrics_data.get('change_from_last_period', '+15')}% from last period)
    - Programs Delivered: {metrics_data.get('programs_delivered', 10)}
    - Success Rate: {metrics_data.get('success_rate', 85)}% (Target was {metrics_data.get('target_success_rate', 80)}%)
    - Cost Per Beneficiary: ${metrics_data.get('cost_per_beneficiary', 250):,.0f}
    - Return on Investment: {metrics_data.get('roi', 4)}:1
    
    Program-Specific Outcomes:
    {chr(10).join([f"- {prog.get('name', 'Program')}: {prog.get('participants', 0):,} served, {prog.get('success_rate', 0)}% success, ${prog.get('cost_efficiency', 0):,.0f}/outcome" for prog in metrics_data.get('program_outcomes', [])[:5]])}
    
    Demographic Breakdown:
    - Age Groups: {metrics_data.get('age_distribution', 'Children 40%, Adults 60%')}
    - Geographic Distribution: {metrics_data.get('geographic_distribution', 'Urban 60%, Rural 40%')}
    - Income Levels: {metrics_data.get('income_distribution', 'Low-income 70%, Moderate 30%')}
    - Special Populations: {metrics_data.get('special_populations', 'Veterans 15%, Seniors 25%')}
    
    Financial Performance:
    - Total Budget: ${metrics_data.get('total_budget', 1000000):,.0f}
    - Program Expenses: {metrics_data.get('program_expense_ratio', 75)}%
    - Admin Expenses: {metrics_data.get('admin_expense_ratio', 15)}%
    - Fundraising Expenses: {metrics_data.get('fundraising_expense_ratio', 10)}%
    - Cost Savings Achieved: ${metrics_data.get('cost_savings', 50000):,.0f}
    """
    
    # Competitive benchmarking
    benchmarks = ""
    if competitive_landscape:
        peer_performance = competitive_landscape.get('peer_performance', {})
        market_position = competitive_landscape.get('market_position', 'Top quartile')
        rankings = competitive_landscape.get('sector_rankings', {})
        
        benchmarks = f"""
        
        🏆 COMPETITIVE BENCHMARKING:
        
        Performance vs. Sector:
        - Overall Ranking: {market_position} (Top {competitive_landscape.get('percentile', 25)}%)
        - Cost Efficiency: ${metrics_data.get('cost_per_outcome', 100)} vs. ${peer_performance.get('avg_cost', 150)} sector average
        - Success Rate: {metrics_data.get('success_rate', 85)}% vs. {peer_performance.get('avg_success', 65)}% sector average
        - ROI: {metrics_data.get('roi', 400)}% vs. {peer_performance.get('avg_roi', 250)}% sector average
        - Growth Rate: {metrics_data.get('growth_rate', 25)}% vs. {peer_performance.get('avg_growth', 10)}% sector average
        
        Competitive Advantages Demonstrated:
        {chr(10).join([f"- {advantage}" for advantage in competitive_landscape.get('demonstrated_advantages', ['Scale efficiency', 'Innovation', 'Outcomes quality'])[:5]])}
        
        Recognition Received:
        {chr(10).join([f"- {recognition}" for recognition in competitive_landscape.get('period_recognition', ['Best Practice Award', 'Innovation Grant'])[:3]])}
        """
    
    # Stakeholder-specific insights
    stakeholder_insights = f"""
    
    👥 STAKEHOLDER-SPECIFIC VALUE CREATION:
    
    For Beneficiaries:
    - Lives Transformed: {metrics_data.get('lives_transformed', 500):,}
    - Average Outcome Improvement: {metrics_data.get('outcome_improvement', 75)}%
    - Satisfaction Score: {metrics_data.get('satisfaction_score', 4.8)}/5.0
    - Would Recommend: {metrics_data.get('recommendation_rate', 95)}%
    
    For Funders:
    - Grant Goals Exceeded: {metrics_data.get('goals_exceeded', 8)} of {metrics_data.get('total_goals', 10)}
    - Reporting Compliance: {metrics_data.get('compliance_rate', 100)}%
    - Impact Per Dollar: {metrics_data.get('impact_per_dollar', '4 lives changed per $1000')}
    - Media Value Generated: ${metrics_data.get('media_value', 250000):,.0f}
    
    For Community:
    - Economic Impact: ${metrics_data.get('economic_impact', 5000000):,.0f}
    - Jobs Created/Saved: {metrics_data.get('jobs_impact', 50)}
    - Volunteer Hours Mobilized: {metrics_data.get('volunteer_hours', 5000):,}
    - Systems Change Achieved: {metrics_data.get('systems_changes', ['Policy reform', 'New partnerships'])[:2]}
    
    For Staff & Board:
    - Team Satisfaction: {metrics_data.get('team_satisfaction', 4.5)}/5.0
    - Retention Rate: {metrics_data.get('retention_rate', 90)}%
    - Professional Development: {metrics_data.get('training_hours', 40)} hours/person
    - Board Engagement: {metrics_data.get('board_engagement', 95)}% participation
    """
    
    return f"""You are a $1000/hour impact measurement expert who has been {org_context.get('name')}'s evaluation partner for 5 years. You know every participant, every outcome, every data point, and exactly how to tell their story in a way that proves impact beyond any doubt. Create an impact report that makes funders want to double their investment.

    # R - ROLE
    You are {org_context.get('name')}'s Chief Impact Officer, with a PhD in evaluation and 20 years experience proving nonprofit ROI. You've published reports that have secured renewed funding 95% of the time. You know how to blend hard data with human stories in a way that moves both hearts and minds. You make impact undeniable.
    
    # E - EXAMPLE
    Your previous impact reports for {org_context.get('name')} have:
    - Secured {org_context.get('renewal_rate', 85)}% grant renewals
    - Generated {org_context.get('increase_from_reports', 30)}% average funding increases
    - Won {org_context.get('awards_from_reports', 3)} evaluation/transparency awards
    - Been used as best practice examples by {org_context.get('report_citations', 5)} other organizations
    - Converted {org_context.get('new_donors_from_reports', 10)} new major donors
    
    Winning impact reports always:
    - Lead with the most impressive metric that beats sector benchmarks
    - Tell real stories with names, faces, and quotes (with permission)
    - Show trend lines proving continuous improvement
    - Include third-party validation and external evaluation
    - Visualize data in ways that make impact instantly clear
    - Connect every dollar invested to specific outcomes achieved
    
    # A - APPLICATION
    Create a comprehensive impact report for {reporting_period.get('name', 'Annual Report')} ({reporting_period.get('start')} to {reporting_period.get('end')}) using the EVIDENCE framework:
    
    E - Executive Summary: High-level impact in numbers and stories
    V - Validated Outcomes: Third-party verified results
    I - Individual Transformations: Real participant journeys
    D - Data Visualizations: Charts and infographics recommendations
    E - Efficiency Metrics: Cost-effectiveness and ROI
    N - Next Period Projections: Future impact potential
    C - Comparative Analysis: Performance vs. sector benchmarks
    E - Engagement Results: Stakeholder satisfaction and feedback
    
    # C - CONTEXT
    
    Organization: {org_context.get('name')}
    Report Period: {reporting_period.get('start')} to {reporting_period.get('end')}
    Report Type: {reporting_period.get('type', 'Annual Impact Report')}
    Primary Audience: {reporting_period.get('audience', 'Funders and major donors')}
    
    {metrics_analysis}
    {stories_section}
    {report_style}
    {benchmarks}
    {stakeholder_insights}
    
    # T - TONE
    Write in {org_context.get('name')}'s reporting voice: {website_context.get('organization_voice', {}).get('tone', 'professional')} but accessible, data-rich but human, proud but humble. Every number should tell a story, every story should have numbers. This is not just a report—it's proof that {org_context.get('name')} is the best investment in the sector.
    
    # O - OUTPUT
    Generate an impact report that makes {org_context.get('name')}'s value undeniable.
    
    Return ONLY a valid JSON object:
    {{
        "executive_summary": "[300 words - Entire impact story with key metrics]",
        "period_highlights": ["highlight 1", "highlight 2", "highlight 3", "highlight 4", "highlight 5"],
        "by_the_numbers": {{
            "beneficiaries_served": {metrics_data.get('beneficiaries_served', 1000)},
            "success_rate": {metrics_data.get('success_rate', 85)},
            "cost_per_outcome": {metrics_data.get('cost_per_outcome', 250)},
            "roi": "{metrics_data.get('roi', 4)}:1",
            "lives_transformed": {metrics_data.get('lives_transformed', 500)}
        }},
        "program_outcomes": [
            {{"name": "Program 1", "participants": 0, "success_rate": 0, "key_outcome": "description"}},
            {{"name": "Program 2", "participants": 0, "success_rate": 0, "key_outcome": "description"}}
        ],
        "participant_stories": [
            {{"name": "Real Name 1", "story": "200-word transformation story", "quote": "Actual quote", "outcome": "Specific result"}},
            {{"name": "Real Name 2", "story": "200-word transformation story", "quote": "Actual quote", "outcome": "Specific result"}}
        ],
        "comparative_performance": {{
            "vs_last_period": "+X% improvement",
            "vs_sector_average": "X% better",
            "ranking": "Top X%",
            "trend": "Upward/Stable"
        }},
        "financial_stewardship": {{
            "program_ratio": "{metrics_data.get('program_expense_ratio', 75)}%",
            "cost_savings": "${metrics_data.get('cost_savings', 50000):,.0f}",
            "efficiency_gains": "{metrics_data.get('efficiency_improvement', 15)}%"
        }},
        "stakeholder_feedback": [
            {{"source": "Beneficiaries", "satisfaction": 0, "key_quote": "actual quote"}},
            {{"source": "Funders", "satisfaction": 0, "key_quote": "actual quote"}},
            {{"source": "Staff", "satisfaction": 0, "key_quote": "actual quote"}}
        ],
        "visualization_recommendations": [
            "Chart 1: Impact growth over time",
            "Infographic 2: Cost per outcome comparison",
            "Map 3: Geographic reach expansion"
        ],
        "looking_ahead": "[200 words - Next period goals and projected impact]",
        "call_to_action": "[100 words - How readers can help expand impact]",
        "credibility_elements": ["External evaluation", "Third-party audit", "Media coverage", "Awards"],
        "report_appendices": ["Detailed financials", "Evaluation methodology", "Full testimonials", "Media clips"]
    }}
    """

def create_intelligence_enhanced_thank_you_prompt(org_context: Dict, donor_info: Dict,
                                                gift_details: Dict, funder_intelligence: Dict,
                                                competitive_landscape: Dict, 
                                                website_context: Optional[Dict] = None) -> str:
    """Create $1000 consultant-level thank you letter with deep personalization"""
    
    # Personal connection and history
    donor_relationship = f"""
    
    💝 DONOR RELATIONSHIP INTELLIGENCE:
    
    Donor Profile:
    - Name: {donor_info.get('name', 'Valued Partner')}
    - Type: {donor_info.get('type', 'Foundation')}
    - Giving History: {donor_info.get('giving_history', 'First-time donor')}
    - Total Given to Date: ${donor_info.get('total_given', 0):,.0f}
    - Relationship Length: {donor_info.get('relationship_years', 0)} years
    - Key Contact: {donor_info.get('key_contact', 'Program Officer')}
    - Communication Preference: {donor_info.get('communication_preference', 'Email')}
    
    Personal Interests & Connections:
    - Passion Areas: {', '.join(donor_info.get('interests', ['Education', 'Youth development'])[:3])}
    - Personal Connection: {donor_info.get('personal_connection', 'Board member introduction')}
    - Engagement Level: {donor_info.get('engagement_level', 'Highly engaged')}
    - Recognition Preference: {donor_info.get('recognition_preference', 'Private acknowledgment')}
    
    Past Interactions:
    - Last Meeting: {donor_info.get('last_meeting', 'Site visit last month')}
    - Programs Visited: {', '.join(donor_info.get('programs_visited', ['Youth center'])[:2])}
    - People Met: {', '.join(donor_info.get('people_met', ['Executive Director', 'Program participants'])[:3])}
    - Feedback Given: "{donor_info.get('past_feedback', 'Impressed by staff dedication')}"
    """
    
    # Specific gift impact
    gift_impact = f"""
    
    🎁 SPECIFIC GIFT IMPACT:
    
    Gift Details:
    - Amount: ${gift_details.get('amount', 50000):,.0f}
    - Designation: {gift_details.get('designation', 'Program support')}
    - Duration: {gift_details.get('duration', 'One year')}
    - Payment Schedule: {gift_details.get('schedule', 'Quarterly')}
    
    Direct Impact Enabled:
    - Beneficiaries Reached: {gift_details.get('beneficiaries_reached', 200)}
    - Programs Supported: {', '.join(gift_details.get('programs_supported', ['Education', 'Mentoring'])[:3])}
    - Specific Outcomes: {gift_details.get('specific_outcomes', '50 youth graduated, 100% college acceptance')}
    - Cost Efficiency: Your ${gift_details.get('amount', 50000):,.0f} will generate ${gift_details.get('impact_value', 200000):,.0f} in social value
    
    Tangible Results Timeline:
    - 30 Days: {gift_details.get('impact_30_days', 'Launch new cohort of 25 students')}
    - 90 Days: {gift_details.get('impact_90_days', 'First progress reports showing 85% improvement')}
    - 1 Year: {gift_details.get('impact_1_year', 'Full cohort graduation with 100% placement')}
    """
    
    # Organization voice for thank you
    org_gratitude_voice = ""
    if website_context:
        voice = website_context.get('organization_voice', {})
        donation_lang = website_context.get('donation_language', {})
        testimonials = website_context.get('testimonials', [])
        
        org_gratitude_voice = f"""
        
        ✍️ GRATITUDE VOICE & STYLE:
        
        Organization's Thank You Style:
        - Tone: {voice.get('tone', 'warm')} and {voice.get('emotion', 'heartfelt')}
        - Formality: {voice.get('formality', 'professional')} but personal
        - Gratitude Expressions: {', '.join(donation_lang.get('gratitude_phrases', ['deeply grateful', 'profound thanks'])[:3])}
        
        Impact Language They Use:
        - Power Phrases: {', '.join(donation_lang.get('impact_phrases', ['transform lives', 'create lasting change'])[:3])}
        - Success Terms: {', '.join(donation_lang.get('success_terms', ['breakthrough', 'milestone'])[:3])}
        
        Recent Beneficiary Quote:
        "{testimonials[0].get('quote', 'This support changed everything for me and my family.')[:200]}"
        - {testimonials[0].get('author', 'Program Participant')}
        """
    
    return f"""You are a $1000/hour donor relations expert who has managed relationships worth over $100 million for {org_context.get('name')}. You know {donor_info.get('name')}'s giving history, their passions, their preferred communication style, and exactly how to make them feel like the hero they are. Write a thank you letter that deepens the relationship and inspires continued partnership.

    # R - ROLE
    You are writing as {org_context.get('name')}'s Executive Director, but with the insight of someone who has known {donor_info.get('name')} for years. You remember every conversation, every site visit, every piece of feedback. You can connect their specific gift to real people whose lives will change. You make gratitude personal, not perfunctory.
    
    # E - EXAMPLE
    Your previous thank you letters have:
    - Achieved {org_context.get('donor_retention_rate', 85)}% donor retention (vs. 45% sector average)
    - Generated {org_context.get('thank_you_response_rate', 40)}% response rate with increased gifts
    - Been shared by donors with their boards as examples of excellent stewardship
    - Led to {org_context.get('referrals_from_thanks', 5)} referrals to new funders
    - Resulted in {org_context.get('increased_gifts', 30)}% average gift increases
    
    # A - APPLICATION
    Write a thank you letter using the HEARTFELT framework:
    
    H - Heartfelt opening that references personal connection
    E - Explicit gratitude for the specific gift amount and purpose
    A - Actual impact their gift will have (specific numbers and names)
    R - Recognition of their partnership beyond just money
    T - Testimonial from someone directly impacted
    F - Future vision of what we'll accomplish together
    E - Emotional story that illustrates transformation
    L - Link to their personal interests and values
    T - Thank again with specific next steps
    
    # C - CONTEXT
    {donor_relationship}
    {gift_impact}
    {org_gratitude_voice}
    
    Organization: {org_context.get('name')}
    From: {org_context.get('executive_director', 'Executive Director')}
    Date: {gift_details.get('date', 'Today')}
    
    # T - TONE
    {donor_info.get('preferred_tone', 'Warm and personal')}, written in {org_context.get('name')}'s voice but customized for {donor_info.get('name')}. Should feel like a letter from a trusted partner who truly understands and appreciates them, not a form letter with their name plugged in.
    
    # O - OUTPUT
    Return ONLY valid JSON:
    {{
        "letter_text": "[Complete 400-500 word letter that sounds personally written for {donor_info.get('name')}]",
        "opening_line": "[Personal hook that shows you remember them]",
        "specific_impact_mentioned": ["Impact point 1", "Impact point 2", "Impact point 3"],
        "beneficiary_story": "[Brief story of real person helped]",
        "recognition_elements": ["Partnership aspect 1", "Partnership aspect 2"],
        "future_vision": "[What we'll accomplish together next]",
        "call_to_action": "[Specific next engagement opportunity]",
        "ps_message": "[Personal P.S. that adds warmth]",
        "personalization_score": "[1-10 how personalized this is]",
        "relationship_deepening_elements": ["Element 1", "Element 2", "Element 3"],
        "follow_up_timeline": "[When and how we'll follow up]"
    }}
    """

def create_intelligence_enhanced_social_prompt(org_context: Dict, platform: str, topic: str,
                                             competitive_landscape: Dict, trending_data: Dict,
                                             website_context: Optional[Dict] = None) -> str:
    """Create $1000 consultant-level social media content with brand voice matching"""
    
    # Platform-specific optimization
    platform_specs = {
        'twitter': {'limit': 280, 'hashtags': '2-3', 'style': 'punchy and provocative', 'media': 'image or gif'},
        'linkedin': {'limit': 1300, 'hashtags': '3-5', 'style': 'professional thought leadership', 'media': 'article or infographic'},
        'facebook': {'limit': 500, 'hashtags': '1-2', 'style': 'warm and conversational', 'media': 'photo album or video'},
        'instagram': {'limit': 2200, 'hashtags': '10-30', 'style': 'visual storytelling', 'media': 'carousel or reel'}
    }
    spec = platform_specs.get(platform.lower(), platform_specs['twitter'])
    
    # Organization's social media voice
    social_voice = ""
    if website_context:
        voice = website_context.get('organization_voice', {})
        social = website_context.get('social_media', {})
        campaigns = website_context.get('current_campaigns', [])
        
        social_voice = f"""
        
        📱 SOCIAL MEDIA BRAND VOICE:
        
        {org_context.get('name')}'s Social Personality:
        - Voice: {voice.get('tone', 'engaging')} and {voice.get('emotion', 'inspiring')}
        - Style: {voice.get('style', 'conversational')} with {voice.get('formality', 'casual')} language
        - Emoji Usage: {social.get('emoji_style', 'Moderate - 1-2 per post')}
        - Hashtag Strategy: {social.get('hashtag_strategy', 'Branded + trending + cause')}
        
        Established Hashtags:
        - Branded: {', '.join(social.get('branded_hashtags', ['#OurMission', '#ImpactNow'])[:3])}
        - Campaign: {', '.join(social.get('campaign_hashtags', ['#ChangeTheWorld', '#TogetherWeCan'])[:3])}
        - Cause: {', '.join(social.get('cause_hashtags', ['#NonProfit', '#SocialGood'])[:3])}
        
        Current Campaigns to Reference:
        {chr(10).join([f"- {camp.get('name', 'Campaign')}: {camp.get('message', 'Key message')}" for camp in campaigns[:2]])}
        
        Top Performing Content Types:
        - {platform}: {social.get(f'{platform}_top_content', 'Success stories and behind-the-scenes')}
        - Best Time: {social.get(f'{platform}_best_time', '2pm weekdays')}
        - Engagement Rate: {social.get(f'{platform}_engagement', '3.5')}%
        """
    
    # Trending intelligence
    trends = ""
    if trending_data:
        trends = f"""
        
        🔥 TRENDING NOW ({platform.upper()}):
        
        Hot Topics to Hijack:
        {chr(10).join([f"- {topic}: {trending_data.get('topics', {}).get(topic, 'Trending nationally')}" for topic in list(trending_data.get('topics', {}).keys())[:3]])}
        
        Viral Formats Working Now:
        {chr(10).join([f"- {format}: {trending_data.get('formats', {}).get(format, 'High engagement')}" for format in list(trending_data.get('formats', {}).keys())[:3]])}
        
        Peak Engagement Windows:
        - Today: {trending_data.get('best_time_today', '2-3pm')}
        - This Week: {trending_data.get('best_day', 'Tuesday')}
        - Audience Online: {trending_data.get('audience_active', '65')}% active now
        """
    
    return f"""You are a $1000/hour social media strategist who has managed {org_context.get('name')}'s social presence for 3 years, growing their following by {org_context.get('social_growth', 500)}% and engagement by {org_context.get('engagement_growth', 200)}%. You know their voice, their audience, and exactly what makes content go viral in the nonprofit space.

    # R - ROLE  
    You are {org_context.get('name')}'s Social Media Director, crafting content that sounds exactly like their brand voice while leveraging real-time trends. You've studied what makes their audience engage, share, and donate. You create posts that feel authentic to their mission while being optimized for maximum reach.
    
    # E - EXAMPLE
    Your recent {platform} posts for {org_context.get('name')} have:
    - Reached {org_context.get('social_reach', 100000):,} people organically
    - Generated {org_context.get('social_engagement', 5000):,} engagements  
    - Converted {org_context.get('social_conversions', 50)} donations
    - Been reshared by {org_context.get('influencer_shares', 'major influencers')}
    - Trended in {org_context.get('trending_locations', 'multiple cities')}
    
    # A - APPLICATION
    Create a {platform} post about {topic} using the VIRAL framework:
    
    V - Value-first opening that stops the scroll
    I - Insight or story that educates/inspires
    R - Relatable human element
    A - Action that's easy to take
    L - Link to larger mission/movement
    
    # C - CONTEXT
    Platform: {platform} ({spec['limit']} characters)
    Topic: {topic}
    Media Type: {spec['media']}
    Hashtag Strategy: {spec['hashtags']} hashtags
    
    {social_voice}
    {trends}
    
    Competitive Context:
    - Average NPO engagement: {competitive_landscape.get('avg_engagement', '1.5')}%
    - Top competitor engagement: {competitive_landscape.get('top_competitor_engagement', '3')}%  
    - Your typical engagement: {org_context.get('typical_engagement', '4')}%
    - Content gap opportunity: {competitive_landscape.get('content_opportunity', 'Human-interest stories')}
    
    # T - TONE
    {spec['style']} - matching {org_context.get('name')}'s established {platform} voice. Should feel native to {platform} while maintaining brand consistency.
    
    # O - OUTPUT
    Return ONLY valid JSON:
    {{
        "post_text": "[Complete post within {spec['limit']} characters]",
        "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
        "media_recommendation": "[Specific image/video description]",
        "call_to_action": "[Specific action for audience]",
        "expected_engagement": "{competitive_landscape.get('expected_engagement', '5')}%",
        "best_posting_time": "{trending_data.get('best_time_today', '2pm')}",
        "trend_connection": "[How this connects to current trends]",
        "brand_voice_match": "[1-10 score for brand consistency]",
        "viral_potential": "[1-10 score based on trending data]",
        "follow_up_content": "[What to post next to maintain momentum]"
    }}
    """

def create_intelligence_enhanced_newsletter_prompt(org_context: Dict, audience: str,
                                                 content_focus: str, competitive_landscape: Dict,
                                                 email_intelligence: Dict, website_context: Optional[Dict] = None) -> str:
    """Create $1000 consultant-level newsletter with organizational format and voice"""
    
    # Newsletter format and structure from website
    newsletter_style = ""
    if website_context:
        voice = website_context.get('organization_voice', {})
        news = website_context.get('news_updates', [])
        programs = website_context.get('programs', [])
        
        newsletter_style = f"""
        
        📧 NEWSLETTER BRAND STANDARDS:
        
        {org_context.get('name')}'s Newsletter Style:
        - Name: {org_context.get('newsletter_name', 'Monthly Impact Update')}
        - Frequency: {org_context.get('newsletter_frequency', 'Monthly')}
        - Average Length: {org_context.get('newsletter_length', '600-800')} words
        - Sections: {', '.join(org_context.get('newsletter_sections', ['Hero Story', 'Program Updates', 'Volunteer Spotlight', 'Upcoming Events'])[:4])}
        
        Voice for Email:
        - Tone: {voice.get('tone', 'warm')} and {voice.get('emotion', 'optimistic')}
        - Perspective: {org_context.get('newsletter_perspective', 'First-person plural (we/our)')}
        - Reading Level: {org_context.get('reading_level', '8th grade')}
        
        Regular Features to Include:
        - Executive Message: {org_context.get('exec_message_style', 'Personal reflection on impact')}
        - Success Story: {org_context.get('story_style', 'One beneficiary transformation')}
        - By the Numbers: {org_context.get('metrics_style', '3-4 key monthly metrics')}
        - Call to Action: {org_context.get('cta_style', 'One primary, one secondary')}
        - Recognition: {org_context.get('recognition_style', 'Donor and volunteer spotlights')}
        
        Recent News to Include:
        {chr(10).join([f"- {item.get('title', 'News')}: {item.get('summary', 'Update')[:100]}" for item in news[:3]])}
        
        Program Updates Available:
        {chr(10).join([f"- {prog.get('name', 'Program')}: {prog.get('recent_update', 'Progress update')[:100]}" for prog in programs[:3]])}
        """
    
    # Email performance intelligence
    email_insights = ""
    if email_intelligence:
        email_insights = f"""
        
        📊 EMAIL PERFORMANCE INTELLIGENCE:
        
        Historical Performance:
        - Average Open Rate: {email_intelligence.get('avg_open_rate', '28')}% (sector: 22%)
        - Average Click Rate: {email_intelligence.get('avg_click_rate', '7')}% (sector: 3%)
        - Best Subject Lines: {', '.join(email_intelligence.get('top_subjects', ["Impact Report: You Made This Possible", "Sarah's Story: From Homeless to Housed"])[:2])}
        
        Audience Insights:
        - Most Engaged Segment: {email_intelligence.get('engaged_segment', 'Monthly donors')}
        - Peak Open Time: {email_intelligence.get('best_time', 'Tuesday 10am')}
        - Preferred Content: {email_intelligence.get('preferred_content', 'Success stories and program updates')}
        - Action Triggers: {', '.join(email_intelligence.get('action_triggers', ['Urgency', 'Personal impact', 'Recognition'])[:3])}
        
        Optimization Data:
        - Optimal Subject Length: {email_intelligence.get('subject_length', '6-8')} words
        - Preview Text Impact: {email_intelligence.get('preview_importance', 'Critical - 25% open rate difference')}
        - Personalization Lift: {email_intelligence.get('personalization_lift', '+35%')} with first name
        - Image/Text Ratio: {email_intelligence.get('image_ratio', '40/60')} for best engagement
        """
    
    # Audience segmentation
    audience_profile = f"""
    
    👥 AUDIENCE PROFILE: {audience.upper()}
    
    Segment Characteristics:
    - Size: {org_context.get(f'{audience}_size', 1000)} subscribers
    - Engagement Level: {org_context.get(f'{audience}_engagement', 'High')}
    - Average Gift: ${org_context.get(f'{audience}_avg_gift', 500):,.0f}
    - Interests: {', '.join(org_context.get(f'{audience}_interests', ['Direct service', 'Local impact'])[:3])}
    - Demographics: {org_context.get(f'{audience}_demographics', '45-65, college-educated, suburban')}
    
    Communication Preferences:
    - Frequency Tolerance: {org_context.get(f'{audience}_frequency', 'Monthly with occasional extras')}
    - Content Preference: {org_context.get(f'{audience}_content_pref', 'Stories over statistics')}
    - Action Willingness: {org_context.get(f'{audience}_action', 'High for volunteering and giving')}
    """
    
    return f"""You are a $1000/hour email marketing specialist who has managed {org_context.get('name')}'s newsletter for 3 years, growing their list by {org_context.get('list_growth', 200)}% and achieving engagement rates 2x the nonprofit sector average. You know exactly what makes their audience open, read, click, and act.

    # R - ROLE
    You are {org_context.get('name')}'s Director of Digital Communications, ghostwriting for their Executive Director. You know every subscriber segment, what content performs best, and how to craft newsletters that feel personal despite going to thousands. You make every reader feel like an insider and valued partner.
    
    # E - EXAMPLE
    Your recent newsletters for {org_context.get('name')} have:
    - Achieved {email_intelligence.get('recent_open_rate', '35')}% open rates
    - Generated {email_intelligence.get('recent_click_rate', '12')}% click rates
    - Raised ${email_intelligence.get('newsletter_revenue', 25000):,.0f} per edition
    - Recruited {email_intelligence.get('volunteer_signups', 50)} new volunteers
    - Earned {email_intelligence.get('forward_rate', '15')}% forward rates
    
    # A - APPLICATION
    Create newsletter content using the CONNECT framework:
    
    C - Compelling subject line using proven triggers
    O - Opening that creates immediate connection
    N - News and updates in digestible chunks
    N - Narrative that illustrates impact
    E - Engagement opportunities clearly presented
    C - Call-to-action that feels natural
    T - Thank you that reinforces partnership
    
    # C - CONTEXT
    Newsletter Focus: {content_focus}
    Target Audience: {audience}
    Send Date: {org_context.get('send_date', 'This Tuesday')}
    
    {newsletter_style}
    {email_insights}
    {audience_profile}
    
    Competitive Context:
    - Sector avg open rate: {competitive_landscape.get('sector_open_rate', '22')}%
    - Top performer rate: {competitive_landscape.get('top_open_rate', '40')}%
    - Content differentiators: {competitive_landscape.get('content_gaps', 'Personal stories, insider updates')}
    
    # T - TONE
    Write in {org_context.get('name')}'s established newsletter voice: {website_context.get('organization_voice', {}).get('tone', 'warm and conversational')}, like a letter from a trusted friend with important updates. Personal without being presumptuous, informative without being overwhelming.
    
    # O - OUTPUT
    Return ONLY valid JSON:
    {{
        "subject_line": "[6-8 words using proven triggers]",
        "preview_text": "[50-60 characters that complement subject]",
        "greeting": "[Personalized opening - Hi {{{{FirstName}}}}]",
        "opening_paragraph": "[75 words - Immediate connection to reader]",
        "hero_story": "[200 words - One powerful transformation story]",
        "program_updates": [
            {{"program": "Name", "update": "50-word update"}},
            {{"program": "Name", "update": "50-word update"}}
        ],
        "by_the_numbers": {{
            "metric_1": {{"label": "Lives Changed", "value": "X"}},
            "metric_2": {{"label": "Efficiency Rate", "value": "X%"}},
            "metric_3": {{"label": "Community Impact", "value": "$X"}}
        }},
        "volunteer_spotlight": "[100 words - Recognition of volunteer with quote]",
        "upcoming_events": [
            {{"event": "Name", "date": "Date", "cta": "Register"}},
            {{"event": "Name", "date": "Date", "cta": "Join us"}}
        ],
        "primary_cta": {{
            "text": "[Button text]",
            "link": "[Where it goes]",
            "context": "[50 words explaining the ask]"
        }},
        "secondary_cta": {{
            "text": "[Link text]",
            "link": "[Where it goes]"  
        }},
        "closing": "[75 words - Personal sign-off from Executive Director]",
        "ps_message": "[25 words - One final engagement hook]",
        "total_word_count": 750,
        "personalization_elements": ["FirstName", "LastGiftAmount", "ProgramInterest"],
        "expected_open_rate": "{email_intelligence.get('projected_open_rate', '35')}%",
        "expected_click_rate": "{email_intelligence.get('projected_click_rate', '8')}%",
        "send_time_recommendation": "{email_intelligence.get('best_time', 'Tuesday 10am')}",
        "segment_customization": "[How to adjust for different segments]"
    }}
    """

def create_intelligence_enhanced_board_report_prompt(org_context: Dict, reporting_period: Dict,
                                                   board_priorities: Dict, financial_data: Dict,
                                                   website_context: Optional[Dict] = None) -> str:
    """Create $1000 consultant-level board report with strategic insights"""
    
    # Board composition and priorities
    board_context = f"""
    
    🏛️ BOARD COMPOSITION & PRIORITIES:
    
    Board Profile:
    - Size: {board_priorities.get('board_size', 12)} members
    - Expertise Areas: {', '.join(board_priorities.get('expertise_areas', ['Finance', 'Legal', 'Marketing', 'Operations'])[:5])}
    - Average Tenure: {board_priorities.get('avg_tenure', 3)} years
    - Meeting Frequency: {board_priorities.get('meeting_frequency', 'Quarterly')}
    
    Strategic Priorities (Current Focus):
    {chr(10).join([f"- Priority {i+1}: {priority}" for i, priority in enumerate(board_priorities.get('strategic_priorities', ['Sustainability', 'Growth', 'Impact measurement'])[:5])])}
    
    Key Concerns to Address:
    {chr(10).join([f"- {concern}" for concern in board_priorities.get('concerns', ['Financial sustainability', 'Program scalability', 'Risk management'])[:4]])}
    
    Success Metrics They Track:
    {chr(10).join([f"- {metric}: Target = {board_priorities.get('targets', {}).get(metric, 'TBD')}" for metric in board_priorities.get('key_metrics', ['Revenue growth', 'Program efficiency', 'Beneficiary outcomes'])[:5]])}
    """
    
    # Financial intelligence
    financial_analysis = f"""
    
    💵 FINANCIAL DASHBOARD:
    
    Revenue Performance:
    - Total Revenue: ${financial_data.get('total_revenue', 0):,.0f} ({financial_data.get('revenue_variance', '+5')}% vs budget)
    - Earned Revenue: ${financial_data.get('earned_revenue', 0):,.0f} ({financial_data.get('earned_ratio', 30)}% of total)
    - Contributed Revenue: ${financial_data.get('contributed_revenue', 0):,.0f} ({financial_data.get('contributed_ratio', 70)}% of total)
    - Monthly Burn Rate: ${financial_data.get('burn_rate', 0):,.0f}
    - Runway: {financial_data.get('runway_months', 6)} months
    
    Expense Management:
    - Total Expenses: ${financial_data.get('total_expenses', 0):,.0f} ({financial_data.get('expense_variance', '-2')}% vs budget)
    - Program Ratio: {financial_data.get('program_ratio', 75)}%
    - Admin Ratio: {financial_data.get('admin_ratio', 15)}%
    - Fundraising Ratio: {financial_data.get('fundraising_ratio', 10)}%
    - Cost Per Beneficiary: ${financial_data.get('cost_per_beneficiary', 0):,.0f} ({financial_data.get('cost_trend', 'decreasing')} trend)
    
    Financial Health Indicators:
    - Current Ratio: {financial_data.get('current_ratio', 2.5)}
    - Days Cash on Hand: {financial_data.get('days_cash', 90)}
    - Accounts Receivable: ${financial_data.get('accounts_receivable', 0):,.0f}
    - Debt-to-Asset Ratio: {financial_data.get('debt_ratio', 0.2)}
    """
    
    return f"""You are a $1000/hour nonprofit governance consultant who has advised {org_context.get('name')}'s board for 5 years. You know each board member's expertise, concerns, and communication style. Create an executive board report that provides strategic insight, demonstrates fiscal responsibility, and positions the organization for sustainable growth.

    # R - ROLE
    You are preparing this report as {org_context.get('name')}'s Executive Director for a sophisticated board that includes {board_priorities.get('board_expertise', 'CEOs, attorneys, and financial executives')}. You must balance detailed operational updates with strategic vision, using data to build confidence while acknowledging challenges transparently.
    
    # E - EXAMPLE
    Your previous board reports have:
    - Secured unanimous approval for {org_context.get('board_approvals', 'major initiatives')}
    - Increased board giving by {org_context.get('board_giving_increase', 40)}%
    - Improved board engagement scores to {org_context.get('board_engagement', 95)}%
    - Led to {org_context.get('board_referrals', 5)} new major donor introductions
    - Resulted in {org_context.get('strategic_pivots', 'strategic pivots that increased impact')}
    
    # A - APPLICATION
    Create a board report using the GOVERNANCE framework:
    
    G - Goals progress against strategic plan
    O - Operational highlights and challenges
    V - Value creation and impact metrics
    E - Executive insights and recommendations
    R - Risk assessment and mitigation
    N - New opportunities and initiatives
    A - Asks of the board (specific actions needed)
    N - Next quarter priorities and projections
    C - Conclusion with confidence-building message
    E - Executive session topics (if needed)
    
    # C - CONTEXT
    Reporting Period: {reporting_period.get('start')} to {reporting_period.get('end')}
    Board Meeting Date: {reporting_period.get('meeting_date', 'Next week')}
    Report Type: {reporting_period.get('type', 'Quarterly Board Report')}
    
    {board_context}
    {financial_analysis}
    
    Organization Performance:
    - Strategic Plan Progress: {org_context.get('strategic_progress', 75)}% of annual goals met
    - Program Expansion: {org_context.get('program_growth', 3)} new initiatives launched
    - Team Development: {org_context.get('team_growth', 5)} new hires, {org_context.get('retention', 90)}% retention
    - External Recognition: {org_context.get('recognition', 'Nonprofit of the Year finalist')}
    
    # T - TONE
    Executive-level, data-driven, confident yet transparent. Balance optimism with realism. Use business language the board expects while maintaining connection to mission. Every section should build confidence in leadership while acknowledging areas for board input.
    
    # O - OUTPUT
    Return ONLY valid JSON:
    {{
        "executive_summary": "[300 words - Quarter in review with key wins and challenges]",
        "strategic_progress": [
            {{"goal": "Goal 1", "target": "X", "actual": "Y", "status": "On track/Behind/Ahead"}},
            {{"goal": "Goal 2", "target": "X", "actual": "Y", "status": "On track/Behind/Ahead"}}
        ],
        "financial_highlights": {{
            "revenue": "${financial_data.get('total_revenue', 0):,.0f}",
            "expenses": "${financial_data.get('total_expenses', 0):,.0f}",
            "net": "${financial_data.get('net_income', 0):,.0f}",
            "variance_explanation": "[Why we're over/under budget]"
        }},
        "program_performance": [
            {{"program": "Name", "beneficiaries": 0, "outcome_rate": 0, "cost_per": 0}},
            {{"program": "Name", "beneficiaries": 0, "outcome_rate": 0, "cost_per": 0}}
        ],
        "key_achievements": [
            "Achievement 1 with quantified impact",
            "Achievement 2 with quantified impact",
            "Achievement 3 with quantified impact"
        ],
        "challenges_and_solutions": [
            {{"challenge": "Description", "impact": "Potential impact", "solution": "Proposed solution", "board_action": "What we need from board"}},
            {{"challenge": "Description", "impact": "Potential impact", "solution": "Proposed solution", "board_action": "What we need from board"}}
        ],
        "risk_assessment": [
            {{"risk": "Risk type", "probability": "High/Medium/Low", "impact": "High/Medium/Low", "mitigation": "Strategy"}},
            {{"risk": "Risk type", "probability": "High/Medium/Low", "impact": "High/Medium/Low", "mitigation": "Strategy"}}
        ],
        "opportunities": [
            {{"opportunity": "Description", "potential_impact": "$X or X beneficiaries", "investment_needed": "$X", "timeline": "X months"}},
            {{"opportunity": "Description", "potential_impact": "$X or X beneficiaries", "investment_needed": "$X", "timeline": "X months"}}
        ],
        "board_asks": [
            {{"ask": "Specific request", "purpose": "Why needed", "deadline": "When needed"}},
            {{"ask": "Specific request", "purpose": "Why needed", "deadline": "When needed"}}
        ],
        "next_quarter_priorities": [
            "Priority 1 with measurable target",
            "Priority 2 with measurable target",
            "Priority 3 with measurable target"
        ],
        "appendices": ["Detailed financials", "Program metrics dashboard", "Donor pipeline report", "HR report"],
        "executive_session_items": ["Item 1", "Item 2"] if board_priorities.get('executive_session_needed', False) else []
    }}
    """