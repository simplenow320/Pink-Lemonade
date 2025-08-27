"""
Intelligence-Enhanced Prompts for Smart Tools
Integrates competitive intelligence with REACTO framework
"""

from typing import Dict, Optional

def create_intelligence_enhanced_pitch_prompt(org_context: Dict, grant_context: Optional[Dict], 
                                            pitch_type: str, funder_intelligence: Dict, 
                                            competitive_landscape: Dict, optimal_messaging: Dict) -> str:
    """Create industry-leading pitch prompt with real-time competitive intelligence"""
    
    # Dynamically adjust content based on pitch type
    pitch_specs = {
        'elevator': {'words': 150, 'focus': 'hook and impact', 'time': '30 seconds'},
        'executive': {'words': 500, 'focus': 'strategy and outcomes', 'time': '2 minutes'}, 
        'detailed': {'words': 1500, 'focus': 'comprehensive case', 'time': '5 minutes'}
    }
    spec = pitch_specs[pitch_type]
    
    # Build funder intelligence insights
    funder_insights = ""
    if funder_intelligence and funder_intelligence.get('recent_grants'):
        recent_grants = funder_intelligence['recent_grants'][:3]
        avg_amount = funder_intelligence.get('average_grant_size', 50000)
        focus_areas = funder_intelligence.get('focus_areas', [])
        decision_factors = funder_intelligence.get('decision_factors', [])
        
        funder_insights = f"""
        
        🎯 FUNDER INTELLIGENCE (Real-time from Candid API):
        Recent Grants: {', '.join([f"${g.get('amount', 0):,.0f} to {g.get('recipient', 'Unknown')}" for g in recent_grants])}
        Average Grant Size: ${avg_amount:,.0f}
        Priority Areas: {', '.join(focus_areas[:5])}
        Key Decision Factors: {', '.join(decision_factors[:3])}
        """
    
    # Build grant-specific context
    grant_details = ""
    if grant_context:
        grant_details = f"""
        Grant Opportunity:
        Title: {grant_context.get('title', 'Untitled')}
        Funder: {grant_context.get('funder', 'Unknown')}
        Amount: ${grant_context.get('amount_max', 0):,.0f}
        Focus: {grant_context.get('focus_area', 'General')}
        Deadline: {grant_context.get('deadline', 'Open')}
        Requirements: {grant_context.get('requirements', 'Standard')}
        """
    else:
        grant_details = "General pitch (no specific grant targeted)"
    
    # Market intelligence insights
    market_insights = ""
    if competitive_landscape:
        market_size = competitive_landscape.get('market_size', {})
        competitors = competitive_landscape.get('competitor_analysis', [])
        gaps = competitive_landscape.get('funding_gaps', [])
        success_prob = competitive_landscape.get('success_probability', 0)
        
        market_insights = f"""
        
        📊 COMPETITIVE LANDSCAPE ANALYSIS:
        Market Size: ${market_size.get('total_funding_available', 0):,.0f} available, {market_size.get('active_funders', 0)} active funders
        Competition Level: {market_size.get('competition_level', 'Moderate')}
        Your Success Probability: {success_prob}%
        Funding Gaps to Exploit: {', '.join(gaps[:3])}
        Key Differentiators Needed: {', '.join([comp.get('competitive_advantage', '') for comp in competitors[:2]])}
        """
    
    # Optimal messaging strategy
    messaging_guidance = ""
    if optimal_messaging:
        power_words = optimal_messaging.get('power_words', [])
        avoid_words = optimal_messaging.get('avoid_words', [])
        winning_themes = optimal_messaging.get('winning_themes', [])
        
        messaging_guidance = f"""
        
        💬 OPTIMAL MESSAGING STRATEGY:
        Power Words to Use: {', '.join(power_words[:8])}
        Words to Avoid: {', '.join(avoid_words[:5])}
        Winning Themes: {', '.join(winning_themes[:3])}
        """
    
    return f"""Create an {pitch_type} grant pitch using the IMPACT framework with competitive intelligence.

    # R - ROLE
    You are the #1 grant pitch strategist who has analyzed $2+ trillion in grants from 259,000+ foundations. You craft pitches that consistently outperform industry averages by 3-5x using real-time market intelligence and proven messaging strategies that have won over $100M in funding.
    
    # E - EXAMPLE
    Top 1% pitches share these intelligence-driven characteristics:
    - Open with a data-backed hook that positions uniquely in the market
    - Demonstrate clear competitive advantages over other applicants
    - Use funder's own language and priorities from their recent grants
    - Quantify impact using metrics that exceed industry benchmarks
    - Show market understanding and identify untapped opportunities
    - Close with specific, optimized ask based on funder capacity
    
    # A - APPLICATION
    Create a {spec['words']}-word {pitch_type} pitch using the IMPACT framework:
    
    I - Irresistible Hook: Open with market intelligence that makes you stand out
    M - Mission Alignment: Connect to funder's proven priorities from recent grants
    P - Proven Impact: Highlight results that exceed market benchmarks
    A - Achievable Ask: Request amount optimized to funder's giving patterns
    C - Competitive Advantage: Clearly differentiate from other applicants
    T - Timeline to Transform: Show rapid results based on market timing
    
    # C - CONTEXT
    Organization:
    Name: {org_context['name']}
    Mission: {org_context['mission']}
    Focus Areas: {org_context['focus_areas']}
    Track Record: {org_context.get('impact_metrics', 'Strong track record')}
    Budget: {org_context.get('budget', 'Appropriate scale')}
    
    {grant_details}
    
    Platform Performance:
    Success Rate: {org_context.get('grant_performance', {}).get('success_rate', 0)}% (vs 15% industry average)
    Total Funding Secured: ${org_context.get('grant_performance', {}).get('total_funding_pursued', 0):,.0f}
    Recent Wins: {', '.join(org_context.get('grant_performance', {}).get('recent_wins', [])[:3])}
    
    {funder_insights}
    {market_insights}
    {messaging_guidance}
    
    # T - TONE
    Confident market leader backed by intelligence. Data-driven yet emotionally compelling. Competitive positioning without arrogance. Demonstrate deep market understanding while maintaining authentic mission focus. Every word optimized for funder psychology.
    
    # O - OUTPUT
    Generate a {spec['words']}-word pitch ({spec['time']} delivery) that:
    1. Opens with intelligence-backed hook
    2. Positions uniquely in competitive landscape
    3. Uses funder's proven language patterns
    4. Quantifies impact beyond industry standards
    5. Makes optimized ask based on giving patterns
    
    Return ONLY a valid JSON object:
    {{
        "pitch_text": "complete {spec['words']}-word pitch using IMPACT framework",
        "word_count": actual_word_count,
        "impact_score": 1-10_rating,
        "competitive_advantages": ["advantage1", "advantage2", "advantage3"],
        "funder_alignment_points": ["alignment1", "alignment2", "alignment3"],
        "success_probability": percentage_based_on_intelligence,
        "optimization_notes": "how intelligence improved this pitch"
    }}
    """

def create_intelligence_enhanced_case_prompt(org_context: Dict, campaign_details: Dict, 
                                           funder_intelligence: Dict, competitive_landscape: Dict, 
                                           optimal_messaging: Dict) -> str:
    """Create industry-leading case for support with competitive intelligence"""
    
    # Market analysis
    market_analysis = ""
    if competitive_landscape:
        market_size = competitive_landscape.get('market_size', {})
        gaps = competitive_landscape.get('funding_gaps', [])
        success_prob = competitive_landscape.get('success_probability', 0)
        
        market_analysis = f"""
        Market Intelligence:
        - Total Market Size: ${market_size.get('total_funding_available', 0):,.0f}
        - Competition Level: {market_size.get('competition_level', 'Moderate')}
        - Success Probability: {success_prob}%
        - Identified Gaps: {', '.join(gaps[:3])}
        """
    
    # Funder landscape analysis
    funder_analysis = ""
    if funder_intelligence:
        top_prospects = funder_intelligence.get('top_prospects', [])
        giving_trends = funder_intelligence.get('giving_trends', {})
        
        funder_analysis = f"""
        Funder Landscape:
        - Top Prospects: {', '.join([p.get('name', '') for p in top_prospects[:5]])}
        - Trending Up: {giving_trends.get('increasing_areas', [])}
        - Average Gifts: ${funder_intelligence.get('average_grant_size', 0):,.0f}
        """
    
    # Messaging optimization
    messaging_strategy = ""
    if optimal_messaging:
        messaging_strategy = f"""
        Messaging Strategy:
        - Power Themes: {', '.join(optimal_messaging.get('winning_themes', [])[:3])}
        - Key Words: {', '.join(optimal_messaging.get('power_words', [])[:5])}
        - Avoid: {', '.join(optimal_messaging.get('avoid_words', [])[:3])}
        """
    
    # Platform performance data
    performance = org_context.get('grant_performance', {})
    
    return f"""Create a comprehensive Case for Support using the TRANSFORM framework with competitive intelligence.

    # R - ROLE
    You are the industry's leading case development strategist with access to real-time intelligence on $2+ trillion in grant funding. You craft cases that consistently win by leveraging market insights, funder intelligence, and competitive positioning that others miss.
    
    # E - EXAMPLE
    Winning cases in the top 1% share these intelligence-driven elements:
    - Position organization as the clear market leader
    - Identify and fill specific gaps competitors miss
    - Use data to demonstrate superior ROI vs alternatives
    - Align perfectly with funder priorities from recent grants
    - Present investment opportunity, not charity request
    - Quantify competitive advantages throughout
    
    # A - APPLICATION
    Create a 2,500-word Case for Support using the TRANSFORM framework:
    
    T - Transformative Vision: Paint future state with market leadership
    R - Rigorous Evidence: Prove superiority with competitive benchmarks
    A - Achievable Roadmap: Show path optimized by market intelligence
    N - Necessary Urgency: Explain why now based on market timing
    S - Strategic Partnerships: Position as the optimal investment
    F - Financial Clarity: Present data-driven investment case
    O - Outcomes Guaranteed: Promise results exceeding market standards
    R - Return on Investment: Quantify value beyond competitors
    M - Movement Building: Show how you'll lead the sector
    
    # C - CONTEXT
    Organization Profile:
    Name: {org_context['name']}
    Mission: {org_context['mission']}
    Focus Areas: {org_context['focus_areas']}
    Geography: {org_context['geography']}
    
    Campaign Details:
    Title: {campaign_details.get('title', 'Transformative Initiative')}
    Goal: ${campaign_details.get('funding_goal', 500000):,.0f}
    Timeline: {campaign_details.get('timeline', '3 years')}
    Target Audience: {campaign_details.get('target_audience', 'Major donors and foundations')}
    
    Platform Performance:
    Success Rate: {performance.get('success_rate', 0)}% (vs 15% average)
    Funding Secured: ${performance.get('total_funding_secured', 0):,.0f}
    
    {market_analysis}
    {funder_analysis}
    {messaging_strategy}
    
    # T - TONE
    Authoritative yet approachable, data-driven yet emotionally compelling, competitive yet collaborative. Position as the clear market leader while acknowledging the competitive landscape. Use intelligence to build unshakeable credibility while maintaining human connection.
    
    # O - OUTPUT
    Return ONLY a valid JSON object with these exact fields:
    {{
        "executive_summary": "200-word summary with competitive positioning",
        "problem_statement": "300-word problem with market context",
        "our_solution": "350-word solution with competitive advantages",
        "impact_evidence": "400-word evidence with market benchmarks",
        "why_now": "200-word urgency with market trends",
        "why_us": "300-word credentials with differentiation",
        "investment_needed": "250-word ask with funder optimization",
        "expected_outcomes": "300-word outcomes with market positioning",
        "partnership_opportunity": "150-word invitation with funder intelligence",
        "competitive_advantages": ["advantage 1", "advantage 2", "advantage 3"],
        "market_positioning": "how this case positions uniquely vs competitors",
        "success_probability_factors": ["factor 1", "factor 2", "factor 3"],
        "funding_strategy": "optimized approach based on funder intelligence",
        "word_count": 2450,
        "target_amount": "{campaign_details.get('funding_goal', 500000)}",
        "roi_analysis": "return on investment with market context"
    }}
    """

def create_intelligence_enhanced_thank_you_prompt(org_context: Dict, donor_info: Dict,
                                                gift_details: Dict, funder_intelligence: Dict,
                                                competitive_landscape: Dict) -> str:
    """Create intelligence-enhanced thank you letter with GRATITUDE framework"""
    
    # Donor intelligence insights
    donor_insights = ""
    if funder_intelligence:
        giving_history = funder_intelligence.get('giving_history', [])
        interests = funder_intelligence.get('focus_areas', [])
        avg_gift = funder_intelligence.get('average_grant_size', 0)
        
        donor_insights = f"""
        Donor Intelligence:
        - Giving History: {len(giving_history)} grants totaling ${sum(g.get('amount', 0) for g in giving_history):,.0f}
        - Key Interests: {', '.join(interests[:3])}
        - Average Gift: ${avg_gift:,.0f}
        - Giving Trend: {funder_intelligence.get('trend', 'Stable')}
        """
    
    # Market positioning
    market_position = ""
    if competitive_landscape:
        market_position = f"""
        Market Context:
        - Your gift ranks in top {competitive_landscape.get('gift_percentile', 10)}% of sector
        - Funding gap filled: {competitive_landscape.get('gap_addressed', 'Critical need')}
        - Competitive advantage enabled: {competitive_landscape.get('advantage_enabled', 'Market leadership')}
        """
    
    return f"""Create a personalized thank you letter using the GRATITUDE framework with donor intelligence.

    # R - ROLE
    You are an expert in donor stewardship who uses intelligence to create thank you letters that deepen relationships and inspire continued giving. Your letters consistently achieve 40% higher retention rates by showing donors their unique impact in the competitive landscape.
    
    # E - EXAMPLE
    Top-performing thank you letters:
    - Reference donor's specific giving patterns and interests
    - Position their gift's impact in market context
    - Show how they're helping you outperform competitors
    - Connect to their proven philanthropic priorities
    - Demonstrate superior ROI compared to alternatives
    
    # A - APPLICATION
    Create a thank you letter using the GRATITUDE framework:
    
    G - Genuine appreciation with personal connection
    R - Recognize specific impact in market context
    A - Articulate competitive advantages enabled
    T - Tell story of transformation possible
    I - Illustrate future partnership opportunities
    T - Thank again with specific next steps
    U - Update on measurable progress
    D - Demonstrate superior stewardship
    E - Engage for continued relationship
    
    # C - CONTEXT
    Organization: {org_context['name']}
    Mission: {org_context['mission']}
    
    Donor Information:
    Name: {donor_info.get('name', 'Valued Partner')}
    Type: {donor_info.get('type', 'Foundation')}
    Relationship: {donor_info.get('relationship_length', 'New')}
    
    Gift Details:
    Amount: ${gift_details.get('amount', 50000):,.0f}
    Purpose: {gift_details.get('purpose', 'General support')}
    Date: {gift_details.get('date', 'Recent')}
    
    {donor_insights}
    {market_position}
    
    # T - TONE
    Warm yet professional, personal yet data-informed, grateful yet confident. Show deep understanding of donor's giving philosophy while positioning as the optimal investment. Balance emotional connection with intelligent insights.
    
    # O - OUTPUT
    Return ONLY valid JSON:
    {{
        "letter_text": "complete thank you letter using GRATITUDE framework",
        "word_count": 400,
        "personalization_elements": ["element1", "element2", "element3"],
        "intelligence_insights_used": ["insight1", "insight2"],
        "competitive_positioning": "how gift positions in market",
        "retention_strategy": "approach to maintain relationship",
        "next_engagement": "suggested follow-up based on intelligence"
    }}
    """

def create_intelligence_enhanced_impact_report_prompt(org_context: Dict, reporting_period: Dict,
                                                    metrics_data: Dict, competitive_landscape: Dict) -> str:
    """Create intelligence-enhanced impact report with market benchmarking"""
    
    # Competitive benchmarking
    benchmarks = ""
    if competitive_landscape:
        peer_performance = competitive_landscape.get('peer_performance', {})
        market_position = competitive_landscape.get('market_position', 'Top quartile')
        
        benchmarks = f"""
        Market Benchmarks:
        - Your Performance vs Sector: {market_position}
        - Cost per Outcome: ${metrics_data.get('cost_per_outcome', 100)} (Sector avg: ${peer_performance.get('avg_cost', 150)})
        - ROI: {metrics_data.get('roi', 400)}% (Sector avg: {peer_performance.get('avg_roi', 250)}%)
        - Efficiency Rating: {competitive_landscape.get('efficiency_percentile', 85)}th percentile
        """
    
    return f"""Create a data-rich impact report that positions our organization as a market leader.

    # R - ROLE
    You are an impact measurement expert who creates reports that demonstrate superior performance through competitive benchmarking and market intelligence.
    
    # E - EXAMPLE
    Leading impact reports:
    - Compare outcomes to sector benchmarks
    - Show cost-effectiveness vs alternatives
    - Position as best-in-class performer
    - Use data visualization recommendations
    - Highlight competitive advantages
    
    # A - APPLICATION
    Create comprehensive impact report with:
    1. Executive summary with market position
    2. Key metrics vs benchmarks
    3. Program outcomes analysis
    4. Cost-effectiveness comparison
    5. Success stories with data
    6. Future projections based on trends
    
    # C - CONTEXT
    Organization: {org_context['name']}
    Period: {reporting_period.get('start')} to {reporting_period.get('end')}
    
    Metrics:
    - Beneficiaries: {metrics_data.get('beneficiaries_served', 1000)}
    - Programs: {metrics_data.get('programs_delivered', 10)}
    - Success Rate: {metrics_data.get('success_rate', 85)}%
    - Funding Efficiency: {metrics_data.get('efficiency_ratio', 0.85)}
    
    {benchmarks}
    
    # T - TONE
    Authoritative, data-driven, confident. Position as sector leader while maintaining humility about continued growth.
    
    # O - OUTPUT
    Return ONLY valid JSON:
    {{
        "executive_summary": "200-word summary with market position",
        "key_metrics": {{"beneficiaries": 0, "programs": 0, "efficiency": 0}},
        "competitive_analysis": "position vs sector",
        "program_outcomes": ["outcome1", "outcome2", "outcome3"],
        "success_stories": ["story1", "story2"],
        "cost_effectiveness": "analysis vs benchmarks",
        "future_projections": "data-driven forecast",
        "improvement_areas": ["area1", "area2"],
        "visual_recommendations": ["chart1", "graph2"],
        "market_leadership_evidence": ["evidence1", "evidence2", "evidence3"]
    }}
    """

def create_intelligence_enhanced_social_prompt(org_context: Dict, platform: str, topic: str,
                                             competitive_landscape: Dict, trending_data: Dict) -> str:
    """Create intelligence-enhanced social media using ENGAGE framework"""
    
    # Platform optimization
    platform_specs = {
        'twitter': {'limit': 280, 'hashtags': 2-3, 'style': 'punchy'},
        'linkedin': {'limit': 1300, 'hashtags': 3-5, 'style': 'professional'},
        'facebook': {'limit': 500, 'hashtags': 1-2, 'style': 'conversational'},
        'instagram': {'limit': 2200, 'hashtags': 10-15, 'style': 'visual'}
    }
    spec = platform_specs.get(platform, platform_specs['twitter'])
    
    # Trending insights
    trends = ""
    if trending_data:
        trends = f"""
        Trending Now:
        - Hot Topics: {', '.join(trending_data.get('topics', [])[:3])}
        - Viral Formats: {', '.join(trending_data.get('formats', [])[:2])}
        - Peak Engagement: {trending_data.get('best_time', '2pm ET')}
        """
    
    # Competitive content analysis
    competition = ""
    if competitive_landscape:
        competition = f"""
        Content Intelligence:
        - Top Performing Posts: {competitive_landscape.get('top_content_themes', [])}
        - Engagement Rate to Beat: {competitive_landscape.get('avg_engagement', 2)}%
        - Content Gaps: {', '.join(competitive_landscape.get('content_gaps', [])[:2])}
        """
    
    return f"""Create {platform} content using the ENGAGE framework with viral intelligence.

    # R - ROLE
    You are a social media strategist who uses real-time intelligence to create content that consistently outperforms sector averages by 3-5x.
    
    # E - EXAMPLE
    Top 1% posts share:
    - Hook that leverages trending topics
    - Data that positions as leader
    - Call-to-action optimized for platform
    - Hashtags based on current performance
    
    # A - APPLICATION
    Create {platform} post using ENGAGE framework:
    
    E - Emotional hook using trending angle
    N - Numbers that show leadership
    G - Generate curiosity with intelligence
    A - Action that drives engagement
    G - Gratitude to community
    E - Extend conversation strategically
    
    # C - CONTEXT
    Organization: {org_context['name']}
    Topic: {topic}
    Platform: {platform}
    Character Limit: {spec['limit']}
    
    {trends}
    {competition}
    
    # T - TONE
    {spec['style']} tone optimized for {platform}. Position as thought leader using intelligence insights.
    
    # O - OUTPUT
    Return ONLY valid JSON:
    {{
        "post_text": "complete post within {spec['limit']} characters",
        "hashtags": ["optimized", "hashtags"],
        "best_time_to_post": "based on intelligence",
        "expected_engagement": "percentage based on analysis",
        "competitive_angle": "how this beats competition",
        "trending_elements": ["element1", "element2"],
        "call_to_action": "optimized CTA"
    }}
    """

def create_intelligence_enhanced_newsletter_prompt(org_context: Dict, audience: str,
                                                 content_focus: str, competitive_landscape: Dict,
                                                 email_intelligence: Dict) -> str:
    """Create intelligence-enhanced newsletter using INSPIRE framework"""
    
    # Email performance intelligence
    email_insights = ""
    if email_intelligence:
        email_insights = f"""
        Email Intelligence:
        - Optimal Subject Lines: {', '.join(email_intelligence.get('top_subjects', [])[:3])}
        - Best Send Time: {email_intelligence.get('best_time', 'Tuesday 10am')}
        - Avg Open Rate to Beat: {email_intelligence.get('sector_open_rate', 22)}%
        - Click Rate Target: {email_intelligence.get('sector_click_rate', 3)}%
        """
    
    # Content competition
    content_analysis = ""
    if competitive_landscape:
        content_analysis = f"""
        Newsletter Benchmarks:
        - Top Performing Topics: {', '.join(competitive_landscape.get('top_topics', [])[:3])}
        - Optimal Length: {competitive_landscape.get('optimal_length', '500-700')} words
        - Must-Include Elements: {', '.join(competitive_landscape.get('key_elements', [])[:3])}
        """
    
    return f"""Create newsletter content using the INSPIRE framework with email intelligence.

    # R - ROLE
    You are an email marketing expert who uses intelligence to create newsletters that achieve open rates 2x above sector average.
    
    # E - EXAMPLE
    Top newsletters feature:
    - Subject lines proven to drive opens
    - Content that beats competitor newsletters
    - Personalization based on audience data
    - Calls-to-action optimized for clicks
    
    # A - APPLICATION
    Create newsletter using INSPIRE framework:
    
    I - Intriguing subject using intelligence
    N - News that positions as leader
    S - Stories that outperform competition
    P - Personalized based on audience data
    I - Insights exclusive to subscribers
    R - Resources that add unique value
    E - Engagement optimized for action
    
    # C - CONTEXT
    Organization: {org_context['name']}
    Audience: {audience}
    Focus: {content_focus}
    
    {email_insights}
    {content_analysis}
    
    # T - TONE
    Informative yet personal, authoritative yet accessible. Position as the must-read newsletter in the sector.
    
    # O - OUTPUT
    Return ONLY valid JSON:
    {{
        "subject_line": "intelligence-optimized subject",
        "preview_text": "compelling preview",
        "main_content": "500-700 word newsletter body",
        "call_to_action": "primary CTA",
        "secondary_ctas": ["cta1", "cta2"],
        "personalization_tokens": ["token1", "token2"],
        "expected_open_rate": "percentage based on intelligence",
        "competitive_advantages": ["advantage1", "advantage2"],
        "send_time_recommendation": "optimal time from data"
    }}
    """