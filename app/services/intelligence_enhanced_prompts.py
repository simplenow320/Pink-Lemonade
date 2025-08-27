"""
Intelligence-Enhanced Prompt Methods
Creates industry-leading prompts with real-time competitive intelligence
"""

from typing import Dict, List, Optional

def create_intelligence_enhanced_pitch_prompt(org_context: Dict, grant_context: Optional[Dict], 
                                            pitch_type: str, funder_intelligence: Dict, 
                                            competitive_landscape: Dict, optimal_messaging: Dict) -> str:
    """Create industry-leading pitch prompt with real-time competitive intelligence"""
    
    time_limits = {
        'elevator': '60 seconds',
        'executive': '2 minutes',
        'detailed': '5 minutes'
    }
    
    word_targets = {
        'elevator': '80-120 words',
        'executive': '150-200 words',  
        'detailed': '300-400 words'
    }
    
    # Build comprehensive context
    grant_info = ""
    if grant_context:
        grant_info = f"""
        Target Grant: {grant_context.get('title', 'Grant Opportunity')}
        Funder: {grant_context.get('funder', 'Foundation')}
        Focus Area: {grant_context.get('focus_area', 'Community Impact')}
        Funding Range: ${grant_context.get('amount_max', 50000):,.0f}
        Deadline: {grant_context.get('deadline', 'Upcoming')}
        """
    
    # Extract competitive intelligence insights
    funder_insights = ""
    if funder_intelligence:
        giving_patterns = funder_intelligence.get('giving_patterns', {})
        recent_grants = funder_intelligence.get('recent_grants', [])[:3]
        success_factors = funder_intelligence.get('success_factors', [])
        optimal_range = funder_intelligence.get('optimal_ask_range', {})
        
        funder_insights = f"""
        
        🎯 REAL-TIME FUNDER INTELLIGENCE:
        Recent Activity: {giving_patterns.get('total_grants', 0)} grants awarded, median ${giving_patterns.get('median_award', 0):,.0f}
        Optimal Ask Range: ${optimal_range.get('recommended_min', 0):,.0f} - ${optimal_range.get('recommended_max', 0):,.0f}
        Success Factors: {', '.join(success_factors[:3])}
        Recent Grants Example: {recent_grants[0].get('purpose', 'Similar programming') if recent_grants else 'Focus on measurable impact'}
        Success Rate Indicator: {optimal_range.get('success_rate_indicator', 15):.0f}% probability for similar organizations
        """
    
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
    
    # Optimal messaging insights
    messaging_insights = ""
    if optimal_messaging:
        key_themes = optimal_messaging.get('key_themes', [])
        success_keywords = optimal_messaging.get('success_keywords', [])
        positioning = optimal_messaging.get('positioning_strategy', {})
        
        messaging_insights = f"""
        
        💡 OPTIMAL MESSAGING STRATEGY:
        Trending Keywords: {', '.join(success_keywords[:5])}
        Key Themes to Emphasize: {', '.join(key_themes[:3])}
        Primary Positioning Angle: {positioning.get('primary_angle', 'Innovation leadership')}
        Language Optimization: Use terms like "{', '.join(success_keywords[:3])}" that appear in 78% of successful grants
        """
    
    # Extract performance data
    performance = org_context.get('grant_performance', {})
    impact_data = org_context.get('impact_metrics', {})
    
    return f"""
    # R - ROLE
    You are an elite nonprofit pitch strategist with 25+ years of experience helping organizations secure $500M+ in funding. You specialize in data-driven storytelling that converts funders into partners with REAL-TIME competitive intelligence. Your pitches have a 85% success rate because you craft compelling narratives backed by evidence AND market intelligence.
    
    # E - EXAMPLE
    Industry-leading pitches follow the IMPACT formula enhanced with competitive intelligence:
    I - Immediate hook with shocking statistic or compelling story that differentiates from competitors
    M - Mission-driven solution that addresses identified market gaps
    P - Proven track record with specific outcomes and metrics that outperform market averages
    A - Ambitious but achievable request optimized for funder's giving patterns
    C - Connection to funder's values and strategic priorities based on recent grant analysis
    T - Transformative vision that positions organization uniquely in competitive landscape
    
    Example intelligence-enhanced opening: "While 73% of youth programs in our area focus on traditional mentoring, we discovered that trauma-informed technology integration increases success rates by 340% - exactly what funders like [Foundation Name] prioritized in their recent $2.3M investment in similar programming."
    
    # A - APPLICATION
    Create a compelling {pitch_type} pitch ({time_limits[pitch_type]}, {word_targets[pitch_type]}) using REAL-TIME competitive intelligence that:
    
    For {pitch_type} pitch specifically:
    1. **Intelligence-Enhanced Hook** (First 15 seconds): Use market gap or funder insight to immediately differentiate
    2. **Competitive Positioning** (Next 20 seconds): Position uniquely against identified competitors using funding gaps
    3. **Evidence-Based Impact** (Core section): Use platform metrics + market benchmarks to prove superiority
    4. **Optimized Ask** (Final section): Request amount based on funder's giving patterns and success probability
    5. **Strategic Close** (Last 10 seconds): Connect to funder's recent priorities and competitive advantages
    
    CRITICAL INTELLIGENCE INTEGRATION:
    - Use funder intelligence to customize language and positioning
    - Reference competitive gaps to position uniquely
    - Optimize ask amount based on funder patterns
    - Include success probability and market advantages
    - Use trending keywords that appear in successful grants
    
    # C - CONTEXT
    Organization Profile:
    Name: {org_context['name']}
    Mission: {org_context['mission']}
    Location: {org_context['geography']}
    Focus Areas: {org_context['focus_areas']}
    Unique Capabilities: {org_context['unique_capabilities']}
    
    Grant Details:{grant_info}
    
    Platform Performance Context:
    Grant Success Rate: {performance.get('success_rate', 0)}%
    Total Funding Pursued: ${performance.get('total_funding_pursued', 0):,.0f}
    Recent Wins: {', '.join(performance.get('recent_wins', []))}
    Success Rate vs Market Average: {performance.get('success_rate', 0) - 15}% above average
    
    Impact Metrics:
    Participant Stories Collected: {impact_data.get('participant_stories', 0)}
    Total Beneficiaries Served: {impact_data.get('total_beneficiaries', 0)}
    Programs Active: {impact_data.get('active_programs', 0)}
    {funder_insights}
    {market_insights}
    {messaging_insights}
    
    # T - TONE
    Confident yet humble, data-driven yet human, competitive yet collaborative. Speak as the market leader who understands the competitive landscape and leverages intelligence for strategic advantage. Balance authority with authenticity, using specific intelligence to build credibility while maintaining emotional connection.
    
    # O - OUTPUT
    Return ONLY a valid JSON object with these exact fields:
    {{
        "pitch_text": "complete {pitch_type} pitch text optimized with competitive intelligence",
        "hook": "opening hook that uses funder/market intelligence for differentiation",
        "problem_statement": "problem framed with market gaps and competitive landscape",
        "solution_overview": "solution positioned uniquely against competitors using intelligence",
        "impact_evidence": "evidence enhanced with market benchmarks and competitive advantages",
        "key_points": ["point 1 with intelligence backing", "point 2 with market positioning", "point 3 with funder alignment"],
        "call_to_action": "specific ask optimized for funder patterns and success probability",
        "funding_request": "exact amount based on funder intelligence: ${optimal_range.get('sweet_spot', grant_context.get('amount_max', 50000) if grant_context else 50000):,.0f}",
        "credibility_markers": ["credential 1 with market context", "credential 2 with competitive advantage"],
        "word_count": {len(word_targets[pitch_type].split('-')[0])},
        "speaking_time": "{time_limits[pitch_type]}",
        "delivery_tips": ["tip 1 for this funder type", "tip 2 for competitive positioning"],
        "funder_connection": "specific connection to funder's recent activity and priorities",
        "follow_up_strategy": "next steps optimized for this funder's decision timeline",
        "competitive_advantages": ["advantage 1 vs market", "advantage 2 vs competitors", "advantage 3 from intelligence"],
        "success_probability_factors": ["factor 1 increasing success", "factor 2 from funder analysis"],
        "market_positioning": "how this pitch positions organization uniquely in competitive landscape"
    }}
    """

def create_intelligence_enhanced_case_prompt(org_context: Dict, campaign_details: Dict, 
                                           funder_intelligence: Dict, competitive_landscape: Dict, 
                                           optimal_messaging: Dict) -> str:
    """Create industry-leading case for support with competitive intelligence"""
    
    # Extract competitive intelligence insights
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
    
    funder_analysis = ""
    if funder_intelligence:
        giving_patterns = funder_intelligence.get('giving_patterns', {})
        success_factors = funder_intelligence.get('success_factors', [])
        
        funder_analysis = f"""
        Funder Intelligence:
        - Average Award: ${giving_patterns.get('average_award', 0):,.0f}
        - Success Factors: {', '.join(success_factors[:3])}
        - Recent Activity: {giving_patterns.get('total_grants', 0)} grants
        """
    
    messaging_strategy = ""
    if optimal_messaging:
        keywords = optimal_messaging.get('success_keywords', [])
        positioning = optimal_messaging.get('positioning_strategy', {})
        
        messaging_strategy = f"""
        Optimal Messaging:
        - Success Keywords: {', '.join(keywords[:5])}
        - Primary Positioning: {positioning.get('primary_angle', 'Innovation')}
        """
    
    performance = org_context.get('grant_performance', {})
    impact_data = org_context.get('impact_metrics', {})
    
    return f"""
    # R - ROLE
    You are an elite fundraising consultant with 20+ years of experience creating cases for support that have secured $1B+ in funding. You specialize in competitive positioning and market intelligence to create cases that stand out in crowded funding landscapes. Your cases have a 92% success rate because you leverage real-time market data and funder intelligence.
    
    # E - EXAMPLE
    Industry-leading cases follow the TRANSFORM framework with competitive intelligence:
    T - Truth about the problem with market context and competitive gaps
    R - Revolutionary solution that exploits identified funding gaps
    A - Authentic story enhanced with competitive differentiation
    N - Need urgency backed by market analysis and funder priorities
    S - Solution uniqueness proven through competitive landscape research
    F - Funding strategy optimized with funder intelligence and success probability
    O - Outcomes vision that positions organization as market leader
    R - Return on investment with market benchmarks and competitive advantages
    M - Movement building that leverages competitive positioning
    
    # A - APPLICATION
    Create a comprehensive case for support with 9 sections, each enhanced with competitive intelligence:
    
    1. **Executive Summary** (200 words): Problem + solution + competitive advantage + optimized ask
    2. **Problem Statement** (300 words): Issue framed with market gaps and competitive context
    3. **Our Solution** (350 words): Approach positioned uniquely using competitive intelligence
    4. **Impact Evidence** (400 words): Results with market benchmarks and competitive advantages
    5. **Why Now** (200 words): Urgency backed by market trends and funder priorities
    6. **Why Us** (300 words): Credentials enhanced with competitive differentiation
    7. **Investment Needed** (250 words): Ask optimized with funder patterns and ROI analysis
    8. **Expected Outcomes** (300 words): Vision with market positioning and competitive advantages
    9. **Partnership Opportunity** (150 words): Invitation leveraging funder intelligence
    
    INTELLIGENCE INTEGRATION REQUIREMENTS:
    - Reference competitive gaps in every section
    - Use funder intelligence to optimize language and positioning
    - Include market benchmarks to prove superiority
    - Position against competitors using identified advantages
    - Use success keywords from funder analysis
    
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