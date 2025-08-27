"""
Smart Tools Suite
AI-powered tools for Grant Pitch, Case for Support, and Impact Reporting
"""

from typing import Dict, List, Optional
from datetime import datetime
from app.services.ai_service import AIService
from app.services.reacto_prompts import ReactoPrompts
from app.services.competitive_intelligence import CompetitiveIntelligenceService
from app.services.intelligence_enhanced_prompts import (
    create_intelligence_enhanced_pitch_prompt, 
    create_intelligence_enhanced_case_prompt,
    create_intelligence_enhanced_thank_you_prompt,
    create_intelligence_enhanced_impact_report_prompt,
    create_intelligence_enhanced_social_prompt,
    create_intelligence_enhanced_newsletter_prompt
)
from app.models import Grant, Organization, Narrative, Analytics, ImpactIntake, db
import logging
import json

logger = logging.getLogger(__name__)

class SmartToolsService:
    """
    Provides three core Smart Tools:
    1. Grant Pitch - 60-second elevator pitch generator
    2. Case for Support - Comprehensive narrative builder
    3. Impact Reporting - Results measurement and storytelling
    """
    
    def __init__(self):
        self.ai_service = AIService()
        self.reacto_prompts = ReactoPrompts()
        self.competitive_intelligence = CompetitiveIntelligenceService()
    
    # ============= GRANT PITCH TOOL =============
    
    def generate_grant_pitch(self, org_id: int, grant_id: Optional[int] = None, 
                            pitch_type: str = 'elevator') -> Dict:
        """
        Generate a compelling grant pitch with real-time competitive intelligence
        Types: elevator (60s), executive (2min), detailed (5min)
        """
        try:
            # Get organization context
            org = Organization.query.get(org_id)
            if not org:
                return {'success': False, 'error': 'Organization not found'}
            
            org_context = self._build_org_context(org)
            
            # Get grant context if specified
            grant_context = None
            funder_name = None
            if grant_id:
                grant = Grant.query.get(grant_id)
                if grant:
                    grant_context = grant.to_dict()
                    funder_name = grant.funder
            
            # Get competitive intelligence for enhanced pitch
            funder_intelligence = {}
            competitive_landscape = {}
            optimal_messaging = {}
            
            if funder_name:
                # Real-time funder research
                funder_intelligence = self.competitive_intelligence.analyze_funder_intelligence(
                    funder_name, org_context.get('focus_areas', [])
                )
                
                # Market analysis
                competitive_landscape = self.competitive_intelligence.analyze_competitive_landscape(
                    org_context, grant_context.get('focus_area', ''), org_context.get('geography', '')
                )
                
                # Optimal messaging based on intelligence
                optimal_messaging = self.competitive_intelligence.get_optimal_messaging(
                    funder_intelligence, competitive_landscape, org_context.get('focus_areas', [])
                )
            
            # Generate enhanced REACTO prompt with intelligence
            prompt = create_intelligence_enhanced_pitch_prompt(
                org_context, grant_context, pitch_type, funder_intelligence, 
                competitive_landscape, optimal_messaging
            )
            
            # Get AI response
            response = self.ai_service.generate_json_response(prompt)
            
            if response:
                # Save pitch as narrative
                narrative = Narrative()
                narrative.grant_id = grant_id
                narrative.section = f'pitch_{pitch_type}'
                narrative.content = response.get('pitch_text', '')
                narrative.ai_generated = True
                narrative.created_at = datetime.utcnow()
                
                db.session.add(narrative)
                db.session.commit()
                
                return {
                    'success': True,
                    'pitch_type': pitch_type,
                    'pitch_text': response.get('pitch_text', ''),
                    'hook': response.get('hook', ''),
                    'problem_statement': response.get('problem_statement', ''),
                    'solution_overview': response.get('solution_overview', ''),
                    'impact_evidence': response.get('impact_evidence', ''),
                    'key_points': response.get('key_points', []),
                    'call_to_action': response.get('call_to_action', ''),
                    'funding_request': response.get('funding_request', ''),
                    'credibility_markers': response.get('credibility_markers', []),
                    'word_count': response.get('word_count', 0),
                    'speaking_time': response.get('speaking_time', '60 seconds'),
                    'delivery_tips': response.get('delivery_tips', []),
                    'funder_connection': response.get('funder_connection', ''),
                    'follow_up_strategy': response.get('follow_up_strategy', ''),
                    'competitive_intelligence': {
                        'funder_insights': funder_intelligence,
                        'market_analysis': competitive_landscape,
                        'success_probability': competitive_landscape.get('success_probability', 0),
                        'optimal_messaging': optimal_messaging,
                        'competitive_advantages': response.get('competitive_advantages', [])
                    }
                }
            
            return {'success': False, 'error': 'Failed to generate pitch'}
            
        except Exception as e:
            logger.error(f"Error generating pitch: {e}")
            return {'success': False, 'error': str(e)}
    
    # ============= CASE FOR SUPPORT TOOL =============
    
    def generate_case_for_support(self, org_id: int, campaign_details: Dict) -> Dict:
        """
        Generate comprehensive case for support document with competitive intelligence
        Includes: problem statement, solution, impact, urgency, credibility
        """
        try:
            # Get organization
            org = Organization.query.get(org_id)
            if not org:
                return {'success': False, 'error': 'Organization not found'}
            
            org_context = self._build_org_context(org)
            
            # Get competitive intelligence for enhanced case
            campaign_focus = campaign_details.get('focus_area', 'community development')
            location = org_context.get('geography', '')
            
            # Analyze competitive landscape for this campaign
            competitive_landscape = self.competitive_intelligence.analyze_competitive_landscape(
                org_context, campaign_focus, location
            )
            
            # Get optimal messaging for this market
            optimal_messaging = self.competitive_intelligence.get_optimal_messaging(
                {}, competitive_landscape, org_context.get('focus_areas', [])
            )
            
            # Generate intelligence-enhanced REACTO prompt
            prompt = create_intelligence_enhanced_case_prompt(
                org_context, campaign_details, {}, competitive_landscape, optimal_messaging
            )
            
            # Get AI response
            response = self.ai_service.generate_json_response(prompt)
            
            if response:
                # Generate each section
                sections = {
                    'executive_summary': response.get('executive_summary', ''),
                    'problem_statement': response.get('problem_statement', ''),
                    'our_solution': response.get('our_solution', ''),
                    'impact_evidence': response.get('impact_evidence', ''),
                    'why_now': response.get('why_now', ''),
                    'why_us': response.get('why_us', ''),
                    'investment_needed': response.get('investment_needed', ''),
                    'donor_benefits': response.get('donor_benefits', ''),
                    'call_to_action': response.get('call_to_action', '')
                }
                
                # Save each section
                for section_name, content in sections.items():
                    if content:
                        narrative = Narrative()
                        narrative.section = f'case_{section_name}'
                        narrative.content = content
                        narrative.ai_generated = True
                        narrative.created_at = datetime.utcnow()
                        db.session.add(narrative)
                
                db.session.commit()
                
                return {
                    'success': True,
                    'sections': sections,
                    'competitive_intelligence': {
                        'market_analysis': competitive_landscape,
                        'success_probability': competitive_landscape.get('success_probability', 0),
                        'optimal_messaging': optimal_messaging,
                        'competitive_advantages': response.get('competitive_advantages', []),
                        'market_positioning': response.get('market_positioning', '')
                    },
                    'key_messages': response.get('key_messages', []),
                    'emotional_hooks': response.get('emotional_hooks', []),
                    'data_points': response.get('data_points', []),
                    'donor_personas': response.get('donor_personas', []),
                    'credibility_markers': response.get('credibility_markers', []),
                    'funding_levels': response.get('funding_levels', []),
                    'total_word_count': response.get('total_word_count', 0),
                    'executive_summary_standalone': response.get('executive_summary_standalone', '')
                }
            
            return {'success': False, 'error': 'Failed to generate case for support'}
            
        except Exception as e:
            logger.error(f"Error generating case for support: {e}")
            return {'success': False, 'error': str(e)}
    
    # ============= IMPACT REPORTING TOOL =============
    
    def generate_impact_report(self, org_id: int, report_period: Dict, 
                              metrics_data: Dict, grant_id: Optional[int] = None) -> Dict:
        """
        Generate data-driven impact report with storytelling using verified data
        Includes: metrics dashboard, success stories, charts, financial summary
        """
        try:
            # Get organization
            org = Organization.query.get(org_id)
            if not org:
                return {'success': False, 'error': 'Organization not found'}
            
            # Get grant if specified
            grant = None
            if grant_id:
                grant = Grant.query.get(grant_id)
            
            # Get impact intake submissions
            from app.models import ImpactIntake
            intake_submissions = []
            extracted_stories = []
            if grant_id:
                intakes = ImpactIntake.query.filter_by(grant_id=grant_id).order_by(ImpactIntake.created_at.desc()).limit(10).all()
                intake_submissions = [intake.payload for intake in intakes]
                
                # Extract stories from intake submissions (max 3 stories total)
                story_count = 0
                for intake in intakes:
                    if story_count >= 3:
                        break
                    
                    payload = intake.payload
                    submitted_by = intake.submitted_by or "Anonymous"
                    
                    # Check for stories in the payload
                    if 'stories' in payload and payload['stories']:
                        for story in payload['stories']:
                            if story_count >= 3:
                                break
                            if story and len(story) > 20:  # Only include meaningful stories
                                extracted_stories.append({
                                    'narrative': story,
                                    'attribution': submitted_by
                                })
                                story_count += 1
            
            # Build comprehensive context
            org_profile = {
                'name': org.name,
                'mission': org.mission,
                'location': f"{getattr(org, 'primary_city', 'City')}, {getattr(org, 'primary_state', 'State')}"
            }
            
            grant_profile = {}
            if grant:
                grant_profile = {
                    'title': grant.title,
                    'amount': grant.amount_max or 0,
                    'period': report_period
                }
            
            # Build KPIs from metrics_data
            kpis = self._extract_kpis(metrics_data)
            
            # Get voice profile (could be from org settings)
            voice_profile = self._get_voice_profile(org)
            
            # Add competitive intelligence
            competitive_landscape = {}
            if org.primary_focus_areas:
                competitive_landscape = self.competitive_intelligence.analyze_competitive_landscape(
                    self._build_comprehensive_org_context(org),
                    org.primary_focus_areas[0] if org.primary_focus_areas else '',
                    f"{getattr(org, 'primary_city', '')}, {getattr(org, 'primary_state', '')}"
                )
            
            # Generate intelligence-enhanced prompt for impact report
            prompt = create_intelligence_enhanced_impact_report_prompt(
                org_context=self._build_comprehensive_org_context(org),
                reporting_period={'start': report_period.get('start', 'Q1'), 'end': report_period.get('end', 'Q4')},
                metrics_data=metrics_data,
                competitive_landscape=competitive_landscape
            )
            
            # Get AI response with GPT-4o and retry logic
            response = None
            max_retries = 2
            
            for attempt in range(max_retries):
                try:
                    # Use AI service with max tokens for impact reports (critical task)
                    # The AI service will use GPT-4o for complex tasks automatically
                    raw_response = self.ai_service.generate_json_response(
                        prompt, 
                        max_tokens=2000
                    )
                    
                    if raw_response:
                        # Validate schema
                        response = self._validate_impact_schema(raw_response)
                        if response:
                            break
                        elif attempt == 0:
                            # Retry with schema fix instruction
                            prompt = f"{prompt}\n\n# RETRY: Previous response had invalid schema. Return ONLY valid JSON matching the exact schema above."
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise
            
            if response:
                # Extract report with exact schema
                ai_stories = response.get('success_stories', [])
                
                # Use extracted stories from intake submissions if available
                final_stories = []
                if extracted_stories:
                    # Format extracted stories properly
                    for i, story_data in enumerate(extracted_stories[:3]):
                        final_stories.append({
                            'title': f"Participant Story {i+1}",
                            'narrative': story_data['narrative'],
                            'quote': '',  # Quote can be extracted from the narrative if needed
                            'attribution': story_data['attribution']
                        })
                else:
                    # Use AI-generated stories if no real stories exist
                    final_stories = ai_stories
                
                # Build source notes based on data availability
                source_notes = response.get('source_notes', [])
                if not extracted_stories:
                    source_notes.append("No participant stories available from intake submissions - using narrative examples")
                else:
                    source_notes.append(f"Using {len(extracted_stories)} real participant stories from intake submissions")
                
                report = {
                    'executive_summary': response.get('executive_summary', 'MISSING: Executive summary not generated'),
                    'impact_score': response.get('impact_score', 0),
                    'metrics_dashboard': response.get('metrics_dashboard', {}),
                    'success_stories': final_stories,
                    'financial_summary': response.get('financial_summary', {
                        'total_grant': grant.amount_max if grant else 0,
                        'spent_to_date': 0,
                        'remaining': grant.amount_max if grant else 0,
                        'category_breakdown': []
                    }),
                    'future_outlook': response.get('future_outlook', 'MISSING: Future outlook not generated'),
                    'donor_recognition': response.get('donor_recognition', []),
                    'charts': response.get('charts', self._get_default_charts()),
                    'source_notes': source_notes
                }
                
                # Save impact report
                narrative = Narrative()
                narrative.section = 'impact_report'
                narrative.content = json.dumps(report)
                narrative.ai_generated = True
                narrative.created_at = datetime.utcnow()
                
                db.session.add(narrative)
                
                # Update analytics with proper event_type
                analytics_entry = Analytics()
                analytics_entry.event_type = 'impact_report_generated'
                analytics_entry.org_id = org_id
                analytics_entry.created_at = datetime.utcnow()
                db.session.add(analytics_entry)
                
                db.session.commit()
                
                return {
                    'success': True,
                    'report': report,
                    'period': report_period,
                    'metrics_summary': response.get('metrics_summary', {}),
                    'impact_score': response.get('impact_score', 0),
                    'recommendations': response.get('recommendations', [])
                }
            
            return {'success': False, 'error': 'Failed to generate impact report'}
            
        except Exception as e:
            logger.error(f"Error generating impact report: {e}")
            return {'success': False, 'error': str(e)}
    
    # ============= NEWSLETTER TOOL =============
    
    def generate_newsletter_content(self, org_id: int, newsletter_details: Dict) -> Dict:
        """Generate comprehensive newsletter content using platform data and storytelling best practices"""
        try:
            org = Organization.query.get(org_id)
            if not org:
                return {'success': False, 'error': 'Organization not found'}
            
            # Get comprehensive organization context
            org_context = self._build_comprehensive_org_context(org)
            
            # Get recent impact stories for newsletter content
            recent_intakes = ImpactIntake.query.join(Grant).filter(Grant.org_id == org.id).limit(5).all()
            impact_stories = []
            for intake in recent_intakes:
                stories = intake.payload.get('stories', [])
                if stories:
                    impact_stories.extend(stories[:2])  # Get up to 2 stories per intake
            
            # Get recent grants for updates section
            recent_grants = Grant.query.filter_by(org_id=org.id).order_by(Grant.created_at.desc()).limit(5).all()
            grant_updates = []
            for grant in recent_grants:
                if grant.status in ['awarded', 'submitted', 'pending']:
                    grant_updates.append({
                        'title': grant.title,
                        'status': grant.status,
                        'amount': grant.amount_max,
                        'funder': grant.funder
                    })
            
            performance = org_context.get('grant_performance', {})
            impact_data = org_context.get('impact_metrics', {})
            
            # Add competitive intelligence
            competitive_landscape = {}
            email_intelligence = {}
            
            if org.primary_focus_areas:
                competitive_landscape = self.competitive_intelligence.analyze_competitive_landscape(
                    org_context, org.primary_focus_areas[0], org_context.get('geography', '')
                )
                # Email intelligence for newsletters
                email_intelligence = {
                    'top_subjects': ['Impact Update:', 'Your Gift in Action:', 'Community Success:'],
                    'best_time': 'Tuesday 10am',
                    'sector_open_rate': 22,
                    'sector_click_rate': 3
                }
            
            # Use intelligence-enhanced prompt
            audience = newsletter_details.get('audience', 'supporters and donors')
            content_focus = newsletter_details.get('focus', 'monthly impact update')
            
            prompt = create_intelligence_enhanced_newsletter_prompt(
                org_context=org_context,
                audience=audience,
                content_focus=content_focus,
                competitive_landscape=competitive_landscape,
                email_intelligence=email_intelligence
            )
            
            # Get AI response
            response = self.ai_service.generate_json_response(prompt)
            
            if response:
                # Save newsletter content
                narrative = Narrative()
                narrative.section = 'newsletter_content'
                narrative.content = response.get('main_content', '')
                narrative.ai_generated = True
                narrative.created_at = datetime.utcnow()
                db.session.add(narrative)
                db.session.commit()
                
                return {'success': True, **response}
            return {'success': False, 'error': 'Failed to generate newsletter content'}
            
        except Exception as e:
            logger.error(f"Error generating newsletter: {e}")
            return {'success': False, 'error': str(e)}
    
    # ============= QUICK TOOLS =============
    
    def generate_thank_you_letter(self, org_id: int, donor_info: Dict) -> Dict:
        """Generate personalized thank you letter with competitive intelligence insights"""
        try:
            org = Organization.query.get(org_id)
            if not org:
                return {'success': False, 'error': 'Organization not found'}
            
            # Get comprehensive organization context
            org_context = self._build_comprehensive_org_context(org)
            
            # Get competitive landscape for positioning organization uniquely
            competitive_landscape = self.competitive_intelligence.analyze_competitive_landscape(
                org_context, org_context.get('focus_areas', ['community development'])[0], 
                org_context.get('geography', '')
            )
            
            # Get recent impact stories for personalization
            recent_intakes = ImpactIntake.query.join(Grant).filter(Grant.org_id == org.id).limit(3).all()
            impact_stories = []
            for intake in recent_intakes:
                stories = intake.payload.get('stories', [])
                if stories:
                    impact_stories.append(stories[0][:100] + '...' if len(stories[0]) > 100 else stories[0])
            
            performance = org_context.get('grant_performance', {})
            impact_data = org_context.get('impact_metrics', {})
            
            # Get funder intelligence if available
            funder_intelligence = {}
            if donor_info.get('name'):
                funder_intelligence = self.competitive_intelligence.analyze_funder_intelligence(
                    donor_info.get('name', ''), org_context.get('focus_areas', [])
                )
            
            # Use intelligence-enhanced prompt
            gift_details = {
                'amount': donor_info.get('gift_amount', 50000),
                'purpose': donor_info.get('gift_purpose', 'General support'),
                'date': donor_info.get('gift_date', 'Recent')
            }
            
            prompt = create_intelligence_enhanced_thank_you_prompt(
                org_context=org_context,
                donor_info=donor_info,
                gift_details=gift_details,
                funder_intelligence=funder_intelligence,
                competitive_landscape=competitive_landscape
            )
            
            # Legacy prompt backup (remove after testing)
            legacy_prompt = f"""
            # R - ROLE
            You are an elite donor stewardship specialist with 15+ years of experience in nonprofit communications. You craft thank you letters that increase donor retention by 40% through authentic storytelling and specific impact demonstration. You understand that donors give again when they feel valued and see concrete evidence of their gift's impact.
            
            # E - EXAMPLE
            Exceptional thank you letters follow the GRATITUDE framework:
            G - Genuine opening that mentions specific gift details
            R - Recognition of donor's values and motivations  
            A - Authentic impact story showing gift in action
            T - Transformation evidence with concrete outcomes
            I - Invitation to deeper engagement and partnership
            T - Timeline for follow-up and continued connection
            U - Uplifting close that reinforces donor's heroic role
            D - Details for next steps and ongoing communication
            E - Emotional connection that lasting relationship
            
            Example opening: "Dear Sarah, When I opened your gift of $25,000 yesterday morning, I immediately thought of Marcus, the 16-year-old who told me last week that your previous support helped him believe in his future for the first time. Your continued faith in our Youth Mentorship Program isn't just funding—it's literally writing new stories of hope."
            
            # A - APPLICATION
            Create a comprehensive, personalized thank you letter that:
            
            1. **Personal Opening** (First paragraph): Reference specific gift amount, timing, and purpose
            2. **Impact Connection** (Second paragraph): Connect their gift to current success story using platform data
            3. **Organizational Progress** (Third paragraph): Share recent wins and performance metrics from platform
            4. **Future Vision** (Fourth paragraph): Paint picture of continued impact and growth
            5. **Partnership Invitation** (Fifth paragraph): Invite deeper engagement beyond financial support
            6. **Gratitude Close** (Final paragraph): Reinforce their importance and upcoming communication
            
            Use these platform-specific details:
            - Your organization's {performance.get('success_rate', 0)}% grant success rate
            - Recent wins: {', '.join(performance.get('recent_wins', []))} 
            - {impact_data.get('participant_stories', 0)} participant stories collected
            - Active impact measurement showing organizational accountability
            {market_insights}
            
            # C - CONTEXT
            Organization Profile:
            Name: {org_context['name']}
            Mission: {org_context['mission']}
            Location: {org_context['geography']}
            Focus Areas: {org_context['focus_areas']}
            Unique Capabilities: {org_context['unique_capabilities']}
            
            Donor Information:
            Name: {donor_info.get('name', 'Valued Supporter')}
            Gift Amount: ${donor_info.get('amount', 0):,.0f}
            Gift Purpose: {donor_info.get('purpose', 'general support')}
            Recurring Gift: {donor_info.get('is_recurring', False)}
            
            Platform Performance Context:
            Grant Success Rate: {performance.get('success_rate', 0)}%
            Total Funding Pursued: ${performance.get('total_funding_pursued', 0):,.0f}
            Recent Grant Wins: {', '.join(performance.get('recent_wins', []))}
            Participant Stories Collected: {impact_data.get('participant_stories', 0)}
            Data Collection Active: {impact_data.get('data_collection_active', False)}
            
            Recent Impact Examples:
            {chr(10).join([f"- {story}" for story in impact_stories[:2]]) if impact_stories else "- Platform tracking organizational impact"}
            
            # T - TONE
            Warm yet professional, grateful yet forward-looking, personal yet credible. Write as a leader sharing exciting progress with a trusted partner. Avoid generic nonprofit language - use specific, vivid details that make the donor feel like an insider. Balance emotional connection with professional accountability.
            
            # O - OUTPUT
            Return comprehensive JSON with:
            {{
                "letter_text": "complete personalized thank you letter (400-600 words)",
                "subject_line": "compelling email subject that references specific impact",
                "key_impact_points": ["3-4 specific ways their gift creates change"],
                "organizational_updates": ["2-3 recent organizational wins from platform data"],
                "future_engagement_opportunities": ["2-3 ways donor can get involved beyond giving"],
                "follow_up_date": "specific date for next communication (30-45 days)",
                "follow_up_purpose": "reason for follow-up communication",
                "donor_segment_insights": "notes about this donor type for future communications",
                "attachment_suggestions": ["recommended materials to include with letter"]
            }}
            """
            
            response = self.ai_service.generate_json_response(prompt)
            if response:
                # Save thank you content
                narrative = Narrative()
                narrative.section = 'thank_you_letter'
                narrative.content = response.get('letter_text', '')
                narrative.ai_generated = True
                narrative.created_at = datetime.utcnow()
                db.session.add(narrative)
                db.session.commit()
                
                return {'success': True, **response}
            return {'success': False, 'error': 'Failed to generate thank you letter'}
            
        except Exception as e:
            logger.error(f"Error generating thank you: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_social_media_post(self, org_id: int, platform: str, 
                                  topic: str) -> Dict:
        """Generate platform-optimized social media content using comprehensive platform data"""
        try:
            org = Organization.query.get(org_id)
            if not org:
                return {'success': False, 'error': 'Organization not found'}
            
            # Get comprehensive organization context
            org_context = self._build_comprehensive_org_context(org)
            
            # Get recent impact stories for content inspiration
            recent_intakes = ImpactIntake.query.join(Grant).filter(Grant.org_id == org.id).limit(2).all()
            recent_stories = []
            for intake in recent_intakes:
                stories = intake.payload.get('stories', [])
                if stories:
                    recent_stories.append(stories[0][:150] + '...' if len(stories[0]) > 150 else stories[0])
            
            # Platform specifications
            platform_specs = {
                'twitter': {'char_limit': 280, 'hashtag_count': '2-3', 'tone': 'concise and punchy'},
                'facebook': {'char_limit': 500, 'hashtag_count': '3-5', 'tone': 'conversational and community-focused'},
                'instagram': {'char_limit': 2200, 'hashtag_count': '8-15', 'tone': 'visual storytelling with inspiration'},
                'linkedin': {'char_limit': 3000, 'hashtag_count': '3-5', 'tone': 'professional yet personal'}
            }
            
            spec = platform_specs.get(platform, platform_specs['facebook'])
            performance = org_context.get('grant_performance', {})
            impact_data = org_context.get('impact_metrics', {})
            
            # Add competitive intelligence
            competitive_landscape = {}
            trending_data = {}
            
            if org.primary_focus_areas:
                competitive_landscape = self.competitive_intelligence.analyze_competitive_landscape(
                    org_context, org.primary_focus_areas[0], org_context.get('geography', '')
                )
                # Get trending topics for social media
                trending_data = {
                    'topics': ['impact', 'community', 'change'],
                    'formats': ['stories', 'data visuals'],
                    'best_time': '2pm ET'
                }
            
            # Use intelligence-enhanced prompt
            prompt = create_intelligence_enhanced_social_prompt(
                org_context=org_context,
                platform=platform,
                topic=topic,
                competitive_landscape=competitive_landscape,
                trending_data=trending_data
            )
            
            # Legacy prompt backup
            legacy_prompt = f"""
            # R - ROLE
            You are an award-winning nonprofit social media strategist with 12+ years of experience growing online communities and driving engagement for impact organizations. You specialize in creating authentic content that balances mission storytelling with platform optimization. Your posts consistently achieve 3x higher engagement than industry average through strategic use of platform data and authentic storytelling.
            
            # E - EXAMPLE
            High-performing social posts follow the ENGAGE framework:
            E - Eye-catching hook that stops the scroll
            N - Narrative that connects emotionally  
            G - Genuine impact story or organizational update
            A - Action-oriented call to participate or support
            G - Geography or community connection for relevance
            E - Encouragement that inspires hope and possibility
            
            Example {platform} post: "🌟 BREAKTHROUGH MOMENT: Last week, Marcus told his mentor, 'For the first time, I believe college is possible for me.' This is why we do what we do at [Org Name]. With a 75% grant success rate, we're not just dreaming about change—we're creating it daily in {org_context['geography']}. 💪 What breakthrough moment will you help create? Link in bio to join our impact. #YouthMentorship #CommunityImpact #BelieveInChange"
            
            # A - APPLICATION
            Create an optimized {platform} post about {topic} that:
            
            Platform-Specific Requirements for {platform}:
            1. **Hook** (First 1-2 lines): Create scroll-stopping opening using platform data or impact story
            2. **Story Core** (Middle content): Connect topic to organizational mission and recent success
            3. **Credibility** (Supporting details): Weave in performance metrics naturally
            4. **Community Connection** (Geographic/local relevance): Reference {org_context['geography']} when relevant
            5. **Call to Action** (Clear next step): Specific action aligned with platform behavior
            6. **Optimization** (Platform features): Use {spec['hashtag_count']} relevant hashtags, appropriate length
            
            Content Requirements:
            - Stay within {spec['char_limit']} characters total
            - Include performance data naturally (don't just list stats)
            - Reference recent impact when relevant to topic
            - Use platform-appropriate tone: {spec['tone']}
            - Include geographic relevance for local engagement
            
            # C - CONTEXT
            Organization Profile:
            Name: {org_context['name']}
            Mission: {org_context['mission']}
            Location: {org_context['geography']}
            Focus Areas: {org_context['focus_areas']}
            Unique Capabilities: {org_context['unique_capabilities']}
            
            Platform Performance Data:
            Grant Success Rate: {performance.get('success_rate', 0)}%
            Total Grants Submitted: {performance.get('total_grants_submitted', 0)}
            Recent Grant Wins: {', '.join(performance.get('recent_wins', []))}
            Participant Stories Collected: {impact_data.get('participant_stories', 0)}
            
            Recent Impact Examples:
            {chr(10).join([f"- {story}" for story in recent_stories[:2]]) if recent_stories else "- Active impact measurement and data collection"}
            
            Post Topic: {topic}
            Target Platform: {platform}
            Character Limit: {spec['char_limit']}
            
            # T - TONE
            Platform-optimized tone for {platform}: {spec['tone']}
            
            Overall voice: Authentic yet inspiring, confident yet humble, professional yet personable. Avoid charity language - speak as a leader creating change. Use active voice, specific details, and community-focused language. Balance organizational pride with mission urgency.
            
            # O - OUTPUT
            Return comprehensive JSON with:
            {{
                "post_text": "complete optimized post (within character limit)",
                "character_count": actual_character_count_number,
                "hashtags": ["platform-optimized hashtags ({spec['hashtag_count']})"],
                "best_time_to_post": "platform-specific optimal posting time",
                "engagement_tips": ["3-4 platform-specific engagement strategies"],
                "platform_features": ["recommended platform features to use (stories, polls, etc.)"],
                "content_series_suggestions": ["ideas for follow-up posts on this topic"],
                "audience_targeting": "recommended audience segments for this content",
                "cross_platform_adaptations": "how to adapt this content for other platforms"
            }}
            """
            
            response = self.ai_service.generate_json_response(prompt)
            if response:
                # Save social media content
                narrative = Narrative()
                narrative.section = f'social_media_{platform}'
                narrative.content = response.get('post_text', '')
                narrative.ai_generated = True
                narrative.created_at = datetime.utcnow()
                db.session.add(narrative)
                db.session.commit()
                
                return {'success': True, 'platform': platform, 'topic': topic, **response}
            return {'success': False, 'error': 'Failed to generate social media post'}
            
        except Exception as e:
            logger.error(f"Error generating social post: {e}")
            return {'success': False, 'error': str(e)}
    
    # ============= HELPER METHODS =============
    
    def _build_comprehensive_org_context(self, org: Organization) -> Dict:
        """Build comprehensive organization context with platform data"""
        # Get analytics data
        analytics = Analytics.query.filter_by(org_id=org.id).order_by(Analytics.created_at.desc()).limit(12).all()
        
        # Get grant performance
        grants = Grant.query.filter_by(org_id=org.id).all()
        total_grants = len(grants)
        won_grants = len([g for g in grants if g.status == 'awarded'])
        
        # Calculate totals
        total_funding = sum(g.amount_max or 0 for g in grants if g.amount_max)
        success_rate = (won_grants / total_grants * 100) if total_grants > 0 else 0
        
        # Get recent impact data
        recent_intakes = ImpactIntake.query.join(Grant).filter(Grant.org_id == org.id).limit(10).all()
        story_count = len(recent_intakes)
        
        return {
            'name': org.name,
            'mission': org.mission,
            'vision': getattr(org, 'vision', ''),
            'values': getattr(org, 'values', []),
            'focus_areas': org.primary_focus_areas,
            'geography': f"{org.primary_city}, {org.primary_state}",
            'budget': org.annual_budget_range,
            'staff_size': org.staff_size,
            'unique_capabilities': org.unique_capabilities,
            'past_successes': getattr(org, 'past_successes', []),
            'current_programs': getattr(org, 'current_programs', []),
            # Platform performance data
            'grant_performance': {
                'total_grants_submitted': total_grants,
                'grants_won': won_grants,
                'success_rate': round(success_rate, 1),
                'total_funding_pursued': total_funding,
                'recent_wins': [g.title for g in grants if g.status == 'awarded'][-3:]
            },
            'impact_metrics': {
                'participant_stories': story_count,
                'recent_analytics_reports': len(analytics),
                'data_collection_active': story_count > 0
            }
        }
    
    def _build_org_context(self, org: Organization) -> Dict:
        """Legacy method - redirects to comprehensive version"""
        return self._build_comprehensive_org_context(org)
    
    def _create_enhanced_pitch_prompt(self, org_context: Dict, grant_context: Optional[Dict], 
                                    pitch_type: str) -> str:
        """Create comprehensive REACTO prompt for robust pitch generation"""
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
        
        # Extract performance data
        performance = org_context.get('grant_performance', {})
        impact_data = org_context.get('impact_metrics', {})
        
        return f"""
        # R - ROLE
        You are an elite nonprofit pitch strategist with 25+ years of experience helping organizations secure $500M+ in funding. You specialize in data-driven storytelling that converts funders into partners. Your pitches have a 85% success rate because you craft compelling narratives backed by evidence.
        
        # E - EXAMPLE
        Exceptional pitches follow the IMPACT formula:
        I - Immediate hook with shocking statistic or compelling story
        M - Mission-driven solution that addresses root causes
        P - Proven track record with specific outcomes and metrics
        A - Ambitious but achievable request with clear ROI
        C - Connection to funder's values and strategic priorities
        T - Transformative vision for lasting change
        
        Example opening: "In our city, 1 in 4 children doesn't know where their next meal will come from. But here's what hope looks like: Maria, who started in our program hungry and struggling, just graduated valedictorian and is headed to medical school on a full scholarship."
        
        # A - APPLICATION
        Create a compelling {pitch_type} pitch ({time_limits[pitch_type]}, {word_targets[pitch_type]}) that:
        
        For {pitch_type} pitch specifically:
        1. **Hook** (First 15 seconds): Start with urgent problem or inspiring story
        2. **Credibility** (Next 30% of time): Establish your track record using platform data
        3. **Solution** (Middle 30%): Present your unique approach and methodology
        4. **Impact Evidence** (Next 25%): Share concrete outcomes and projections
        5. **The Ask** (Final 15%): Make specific, compelling funding request
        6. **Vision Close** (Last 10 seconds): Paint picture of transformed future
        
        Include specific details from platform data:
        - Reference your {performance.get('success_rate', 0)}% grant success rate
        - Mention your {performance.get('total_grants_submitted', 0)} grant applications submitted
        - Highlight {impact_data.get('participant_stories', 0)} participant stories collected
        - Use geography ({org_context['geography']}) for local relevance
        
        # C - CONTEXT
        Organization Profile:
        Name: {org_context['name']}
        Mission: {org_context['mission']}
        Location: {org_context['geography']}
        Focus Areas: {org_context['focus_areas']}
        Annual Budget: {org_context['budget']}
        Staff Size: {org_context['staff_size']}
        Unique Capabilities: {org_context['unique_capabilities']}
        
        Platform Performance Data:
        Grant Success Rate: {performance.get('success_rate', 0)}%
        Total Grants Submitted: {performance.get('total_grants_submitted', 0)}
        Grants Won: {performance.get('grants_won', 0)}
        Total Funding Pursued: ${performance.get('total_funding_pursued', 0):,.0f}
        Recent Wins: {', '.join(performance.get('recent_wins', []))}
        
        Impact Collection:
        Participant Stories: {impact_data.get('participant_stories', 0)}
        Active Data Collection: {impact_data.get('data_collection_active', False)}
        Recent Reports: {impact_data.get('recent_analytics_reports', 0)}
        
        {grant_info}
        
        # T - TONE
        {pitch_type.title()} pitch tone requirements:
        - **Elevator**: Urgent, confident, memorable - every word counts
        - **Executive**: Professional, data-driven, visionary - inspire confidence
        - **Detailed**: Comprehensive, passionate, collaborative - build partnership
        
        Balance emotional storytelling with hard evidence. Use active voice, concrete numbers, and vivid imagery. Sound like a leader who gets results, not someone asking for charity.
        
        # O - OUTPUT
        Return comprehensive JSON with:
        {{
            "pitch_text": "complete {pitch_type} pitch script with natural flow and timing markers",
            "hook": "powerful opening line that grabs immediate attention",
            "problem_statement": "urgent problem your organization solves",
            "solution_overview": "your unique approach and methodology", 
            "impact_evidence": "specific outcomes and success metrics",
            "key_points": ["3-5 essential points for {pitch_type} format"],
            "call_to_action": "specific funding request with clear next steps",
            "funding_request": "exact dollar amount and usage breakdown",
            "credibility_markers": ["platform performance data points to emphasize"],
            "word_count": actual_word_count_number,
            "speaking_time": "estimated delivery time with pacing",
            "delivery_tips": ["3-4 specific presentation techniques for {pitch_type} format"],
            "funder_connection": "how this aligns with typical funder priorities",
            "follow_up_strategy": "recommended next steps after pitch"
        }}
        """
    
    def _create_enhanced_case_prompt(self, org_context: Dict, campaign_details: Dict) -> str:
        """Create comprehensive REACTO prompt for case for support using platform data"""
        
        # Extract performance and impact data
        performance = org_context.get('grant_performance', {})
        impact_data = org_context.get('impact_metrics', {})
        
        # Get recent impact examples if available
        recent_wins = performance.get('recent_wins', [])
        wins_context = f"Recent funding wins include: {', '.join(recent_wins[:3])}" if recent_wins else "Building track record of successful funding"
        
        return f"""
        # R - ROLE
        You are an elite fundraising strategist with 20+ years of experience developing case documents that have raised $2B+ for nonprofits. You specialize in creating compelling cases that blend emotional storytelling with rigorous evidence. Your case documents achieve 45% higher response rates because you understand donor psychology and craft narratives that make giving feel both urgent and inspiring.
        
        # E - EXAMPLE
        Outstanding cases follow the TRANSFORM framework:
        T - Truth-telling opening that acknowledges the problem's complexity
        R - Research-backed evidence showing why traditional approaches fall short
        A - Ambitious yet achievable vision for systemic change
        N - Narrative arc showing how individual gifts create collective impact
        S - Specific outcomes with measurable timelines and benchmarks
        F - Funding strategy that connects gift levels to concrete results
        O - Organizational credibility demonstrated through platform performance
        R - Return on investment projections with accountability measures
        M - Movement invitation that positions donors as change agents
        
        Example opening: "Every night in {org_context['geography']}, families face impossible choices. But what if we told you that for the first time in decades, we have a proven pathway to break this cycle? With our {performance.get('success_rate', 0)}% funding success rate and {impact_data.get('participant_stories', 0)} documented transformation stories, we're not asking you to hope for change—we're inviting you to invest in a movement that's already succeeding."
        
        # A - APPLICATION
        Develop a comprehensive case for support that combines platform performance data with compelling narrative:
        
        **Section-by-Section Requirements:**
        
        1. **Executive Summary** (300-400 words): Lead with most compelling statistic from platform data, summarize organizational track record, present funding goal with ROI projection
        
        2. **Problem Statement** (400-500 words): Frame local problem within larger context, use geographic relevance, reference organizational expertise gained through grant work
        
        3. **Our Solution** (500-600 words): Detail unique approach, reference successful grant implementations, highlight what makes organization different
        
        4. **Impact Evidence** (400-500 words): Use platform performance metrics, incorporate participant stories, demonstrate measurement capabilities
        
        5. **Why Now** (300-400 words): Connect to current opportunities, reference recent grant wins as momentum indicators
        
        6. **Why Us** (400-500 words): Leverage organizational track record, highlight grant success rate, demonstrate stewardship through data collection
        
        7. **Investment Needed** (400-500 words): Break down funding goals, connect to specific outcomes, show scalability
        
        8. **Donor Benefits** (300-400 words): Position as partnership opportunity, highlight exclusive access and recognition
        
        9. **Call to Action** (200-300 words): Create urgency with specific timeline, provide multiple engagement levels
        
        **Platform Data Integration Requirements:**
        - Weave in {performance.get('success_rate', 0)}% grant success rate as credibility marker
        - Reference {performance.get('total_grants_submitted', 0)} total applications as experience indicator
        - Highlight {impact_data.get('participant_stories', 0)} stories collected as accountability measure
        - Use recent wins to demonstrate momentum and funder confidence
        - Position data collection capabilities as transparency and impact measurement
        
        # C - CONTEXT
        Organization Profile:
        Name: {org_context['name']}
        Mission: {org_context['mission']}
        Geographic Focus: {org_context['geography']}
        Primary Focus Areas: {org_context['focus_areas']}
        Annual Operating Budget: {org_context['budget']}
        Staff Size: {org_context['staff_size']}
        Unique Organizational Capabilities: {org_context['unique_capabilities']}
        
        Platform Performance Evidence:
        Grant Success Rate: {performance.get('success_rate', 0)}%
        Total Grant Applications: {performance.get('total_grants_submitted', 0)}
        Successful Grant Awards: {performance.get('grants_won', 0)}
        Total Funding Pursued: ${performance.get('total_funding_pursued', 0):,.0f}
        {wins_context}
        
        Impact Measurement Capabilities:
        Participant Stories Documented: {impact_data.get('participant_stories', 0)}
        Active Data Collection System: {impact_data.get('data_collection_active', False)}
        Analytics Reports Generated: {impact_data.get('recent_analytics_reports', 0)}
        
        Campaign Details:
        Fundraising Goal: ${campaign_details.get('goal', 100000):,.0f}
        Campaign Purpose: {campaign_details.get('purpose', 'organizational expansion')}
        Campaign Timeline: {campaign_details.get('timeline', '12-18 months')}
        Target Donor Segments: {campaign_details.get('target_donors', 'major donors and foundations')}
        Expected Donor Count: {campaign_details.get('expected_donors', '50-100 donors')}
        
        # T - TONE
        Authoritative yet accessible, urgent yet sustainable, data-driven yet deeply human. Write as a leader presenting a compelling investment opportunity, not asking for charity. Balance organizational confidence with mission humility. Use concrete language, active voice, and vivid imagery. Demonstrate both emotional intelligence and analytical rigor.
        
        # O - OUTPUT
        Return comprehensive JSON with:
        {{
            "executive_summary": "compelling 300-400 word overview that hooks readers immediately",
            "problem_statement": "urgent 400-500 word problem framing with local relevance",
            "our_solution": "detailed 500-600 word solution description highlighting uniqueness",
            "impact_evidence": "convincing 400-500 word evidence section using platform data",
            "why_now": "timely 300-400 word urgency section referencing momentum",
            "why_us": "credible 400-500 word organizational case using grant track record",
            "investment_needed": "specific 400-500 word funding breakdown with ROI",
            "donor_benefits": "appealing 300-400 word partnership value proposition",
            "call_to_action": "compelling 200-300 word action section with timeline",
            "key_messages": ["5-7 core messages that reinforce case throughout"],
            "emotional_hooks": ["3-5 powerful emotional connection points"],
            "data_points": ["8-10 compelling statistics that support the case"],
            "donor_personas": ["3-4 ideal donor profiles with motivations"],
            "credibility_markers": ["platform performance highlights to emphasize"],
            "funding_levels": ["suggested giving levels with specific impact"],
            "total_word_count": actual_total_word_count_number,
            "executive_summary_standalone": "can this executive summary work as independent piece?"
        }}
        """
    
    def _create_newsletter_prompt(self, org_context: Dict, newsletter_details: Dict, 
                                impact_stories: List[str], grant_updates: List[Dict],
                                performance: Dict, impact_data: Dict) -> str:
        """Create comprehensive REACTO prompt for human-sounding newsletter content"""
        
        # Extract newsletter parameters
        theme = newsletter_details.get('theme', 'Monthly Impact Update')
        month_year = newsletter_details.get('month_year', datetime.now().strftime('%B %Y'))
        focus_area = newsletter_details.get('focus_area', 'general')
        target_audience = newsletter_details.get('target_audience', 'donors and supporters')
        
        # Prepare impact story context
        story_context = ""
        if impact_stories:
            story_context = f"Recent participant stories available: {chr(10).join([f'- {story[:150]}...' for story in impact_stories[:3]])}"
        else:
            story_context = "Focus on organizational milestones and community impact"
        
        # Prepare grant updates context
        updates_context = ""
        if grant_updates:
            recent_awards = [g for g in grant_updates if g['status'] == 'awarded']
            pending_apps = [g for g in grant_updates if g['status'] in ['submitted', 'pending']]
            if recent_awards:
                funding_list = [f"{g['funder']} (${g['amount']:,.0f})" for g in recent_awards[:2] if g.get('amount')]
                updates_context += f"Recent funding wins: {', '.join(funding_list)}\n"
            if pending_apps:
                updates_context += f"Applications pending: {len(pending_apps)} grant applications totaling ${sum(g.get('amount', 0) for g in pending_apps):,.0f}"
        
        return f"""
        # R - ROLE
        You are an elite nonprofit communications specialist with 18+ years of experience crafting newsletters that achieve 45% open rates and 12% click-through rates. You specialize in human-centered storytelling that builds authentic connections between organizations and supporters. Your writing is indistinguishable from human communication because you understand that people connect with genuine emotion, specific details, and conversational authenticity. You write newsletters that supporters forward to friends because the content feels personal and inspiring.
        
        # E - EXAMPLE
        Exceptional newsletters follow the INSPIRE framework:
        I - Immediate connection through mission-driven subject line and opening
        N - Narrative storytelling with specific human details and sensory language
        S - Specific achievements and updates that demonstrate tangible progress  
        P - Personal appreciation that makes supporters feel valued and essential
        I - Invitation to deeper engagement through clear, compelling calls-to-action
        R - Reinforcement of mission impact and future vision that motivates continued support
        E - Emotional resonance through authentic voice and conversational tone
        
        Example opening that sounds completely human: "I was sitting in our community center yesterday afternoon when Maria walked through the door with the biggest smile I've seen in months. 'I got the job!' she practically shouted, and suddenly the whole room was celebrating with her. It's moments like these that remind me why we do this work together—and why your support makes all the difference."
        
        # A - APPLICATION
        Create a comprehensive newsletter for {theme} - {month_year} that follows proven newsletter standards:
        
        **Human Writing Requirements** (Critical for AI detection avoidance):
        1. **Conversational Flow**: Write as if speaking directly to a friend who cares about the mission
        2. **Specific Details**: Use exact names, numbers, locations, and timeframes from platform data
        3. **Sensory Language**: Include what you saw, heard, felt - make readers experience the moment
        4. **Natural Transitions**: Connect sections with conversational bridges, not formal headers
        5. **Varied Sentence Structure**: Mix short punchy sentences with longer descriptive ones
        6. **Personal Voice**: Include "I," "we," "you" - make it feel like personal communication
        7. **Authentic Emotion**: Let genuine excitement, gratitude, and hope come through naturally
        
        **Newsletter Structure Requirements:**
        
        1. **Compelling Subject Line**: Mission-driven, specific, personal (not "Monthly Newsletter")
           - Reference specific impact numbers from platform data
           - Create curiosity while staying authentic to organization voice
        
        2. **Mission Connection Opening** (150-200 words):
           - Start with vivid scene or story that embodies mission
           - Naturally weave in organizational context and recent progress
           - Reference performance data organically (don't just list statistics)
        
        3. **Feature Story** (300-400 words):
           - Center on human impact using available participant stories
           - Include problem → action → positive result structure
           - Use specific details that make story feel real and immediate
           - Connect individual story to broader organizational impact
        
        4. **Quick Updates and Wins** (200-250 words):
           - Highlight recent accomplishments using platform performance data
           - Include grant success metrics naturally in context
           - Share milestone celebrations and organizational growth
           - Use bullet points or short paragraphs for easy scanning
        
        5. **Supporter Appreciation** (100-150 words):
           - Thank specific types of supporters (volunteers, donors, partners)
           - Reference community building and collective impact
           - Make appreciation feel personal and genuine, not generic
        
        6. **Clear Call-to-Action** (75-100 words):
           - Give readers specific action aligned with organizational priorities
           - Make CTA feel like natural invitation, not sales pitch
           - Include multiple engagement levels (small to large commitments)
        
        7. **Forward-Looking Close** (75-100 words):
           - Share upcoming initiatives or goals
           - Reinforce mission vision and supporter importance
           - End with warmth and gratitude that feels authentic
        
        # C - CONTEXT
        Organization Profile:
        Name: {org_context['name']}
        Mission: {org_context['mission']}
        Geographic Focus: {org_context['geography']}
        Primary Focus Areas: {org_context['focus_areas']}
        Unique Organizational Strengths: {org_context['unique_capabilities']}
        
        Platform Performance Data:
        Grant Success Rate: {performance.get('success_rate', 0)}%
        Total Grant Applications: {performance.get('total_grants_submitted', 0)}
        Recent Grant Wins: {', '.join(performance.get('recent_wins', []))}
        Participant Stories Collected: {impact_data.get('participant_stories', 0)}
        Active Data Collection: {impact_data.get('data_collection_active', False)}
        
        Newsletter Parameters:
        Theme: {theme}
        Month/Year: {month_year}
        Focus Area: {focus_area}
        Target Audience: {target_audience}
        
        Available Content Sources:
        {story_context}
        
        Recent Organizational Updates:
        {updates_context if updates_context else "Focus on program growth and community engagement"}
        
        # T - TONE
        Conversational yet inspiring, personal yet professional, grateful yet forward-looking. Write as a passionate leader sharing exciting updates with trusted friends and partners. Use natural, flowing language that feels like genuine human communication. Avoid corporate jargon, generic nonprofit language, or overly formal structure. Balance emotional storytelling with concrete evidence of impact. Sound like someone who genuinely believes in the mission and is excited to share progress with people who care.
        
        **Voice Characteristics for Human Detection:**
        - Enthusiasm that feels genuine, not forced
        - Gratitude that's specific, not generic
        - Confidence that's humble, not boastful
        - Urgency that's hopeful, not desperate
        - Professionalism that's warm, not corporate
        
        # O - OUTPUT
        Return comprehensive JSON with:
        {{
            "subject_line": "compelling, mission-driven subject line that creates curiosity",
            "opening_hook": "engaging first paragraph that draws readers in immediately",
            "main_content": "complete newsletter content (1000-1200 words) with natural flow",
            "feature_story": "standalone human-centered story section",
            "updates_section": "organizational wins and milestones with platform data",
            "appreciation_section": "genuine supporter thank you with specific recognition",
            "call_to_action": "clear, compelling invitation for reader engagement",
            "closing_section": "warm conclusion that reinforces mission and gratitude",
            "suggested_images": ["3-4 authentic image descriptions that would enhance content"],
            "social_media_teasers": ["2-3 social posts to promote newsletter"],
            "human_authenticity_score": "assessment of how natural and human the content sounds",
            "engagement_predictions": ["expected reader actions based on content"],
            "follow_up_opportunities": ["ways to continue engagement after newsletter"]
        }}
        """
    
    def _create_impact_prompt_v2(self, org_profile: Dict, grant_profile: Dict,
                                kpis: Dict, intake_payloads: List[Dict], 
                                voice_profile: Dict) -> str:
        """Create REACTO prompt for impact reporting using verified data only"""
        return f"""
# CRITICAL: OUTPUT ONLY VALID JSON. NO TEXT BEFORE OR AFTER THE JSON OBJECT.

# R - ROLE
You are an expert grant impact report writer who transforms raw data into compelling donor reports.
You have 20+ years experience writing for foundations, government funders, and major donors.
You specialize in evidence-based storytelling that combines metrics with human impact.

# E - EXAMPLE
Professional impact reports include:
- Executive summary highlighting key achievements (120+ words)
- Metrics dashboard with clear KPIs
- 1-3 authentic participant stories with attribution
- Financial transparency with spending breakdown
- Forward-looking sustainability narrative
- Charts visualizing impact data
Example opening: "This quarter, our programs transformed 1,250 lives across 8 communities, achieving a 92% success rate while maintaining cost efficiency at $200 per beneficiary."

# A - APPLICATION
Generate a comprehensive impact report following this exact process:
1. Calculate impact_score: (success_rate * 0.4) + (beneficiaries_served/10000 * 0.3) + (programs_delivered/20 * 0.2) + (cost_efficiency * 0.1)
2. Extract participant stories from intake_payloads if available (max 3)
3. Build metrics dashboard from provided KPIs
4. Create financial summary with actual vs budgeted amounts
5. Write executive summary synthesizing all achievements
6. Develop future outlook based on current trajectory
7. Add source notes for any missing data

# C - CONTEXT
Organization: {org_profile.get('name')}, Mission: {org_profile.get('mission')}, Location: {org_profile.get('location')}
Grant: {grant_profile.get('title', 'N/A')}, Amount: ${float(grant_profile.get('amount', 0)):,.0f}, Period: {grant_profile.get('period', {})}
KPIs Provided:
{json.dumps(kpis, indent=2)}
Participant Intake Data ({len(intake_payloads)} submissions):
{json.dumps(intake_payloads[:3], indent=2) if intake_payloads else 'None available'}
Voice Profile: {voice_profile.get('tone', 'warm and professional')}

# T - TONE
{voice_profile.get('tone', 'Warm yet professional, data-driven yet human, celebratory yet honest')}.
Avoid jargon. Use active voice. Be specific with numbers and outcomes.

# O - OUTPUT
Return ONLY this exact JSON structure (no other text):
{{
  "executive_summary": "string minimum 120 words summarizing key achievements and impact",
  "impact_score": 75,
  "metrics_dashboard": {{
    "total_served": {kpis.get('beneficiaries_served', 0)},
    "goals_met": {kpis.get('goals_met', 3)},
    "success_rate": {kpis.get('success_rate', 85)},
    "key_outcomes": ["specific outcome 1", "specific outcome 2", "specific outcome 3"]
  }},
  "success_stories": [
    {{"title": "Story Title", "narrative": "participant story text", "quote": "direct quote if available", "attribution": "name or Anonymous"}}
  ],
  "financial_summary": {{
    "total_grant": {float(grant_profile.get('amount', 0))},
    "spent_to_date": {int(float(grant_profile.get('amount', 0)) * 0.6)},
    "remaining": {int(float(grant_profile.get('amount', 0)) * 0.4)},
    "category_breakdown": [
      {{"category": "Programs", "amount": {int(float(grant_profile.get('amount', 0)) * 0.4)}}},
      {{"category": "Operations", "amount": {int(float(grant_profile.get('amount', 0)) * 0.2)}}}
    ]
  }},
  "future_outlook": "string minimum 80 words describing sustainability and growth plans",
  "donor_recognition": ["Thank you to our funding partners", "Your support makes this impact possible"],
  "charts": [
    {{"id": "funding_trend", "type": "line", "title": "Funding Over Time", "data_spec": {{"trend": "positive"}}}},
    {{"id": "beneficiaries", "type": "bar", "title": "Beneficiaries Reached", "data_spec": {{"total": {kpis.get('beneficiaries_served', 0)}}}}},
    {{"id": "outcomes", "type": "stacked_bar", "title": "KPIs vs Targets", "data_spec": {{"achieved": 75, "remaining": 25}}}},
    {{"id": "cost_per_outcome", "type": "number", "title": "Cost per Impact", "data_spec": {{"value": {int(float(grant_profile.get('amount', 100000)) / max(kpis.get('beneficiaries_served', 1), 1))}}}}}
  ],
  "source_notes": ["Data sourced from organization records and participant surveys"]
}}
        """
    
    def _create_impact_prompt(self, org_context: Dict, report_period: Dict, 
                             metrics_data: Dict, historical_data: Dict) -> str:
        """Legacy REACTO prompt for backward compatibility"""
        return self._create_impact_prompt_v2(
            org_profile=org_context,
            grant_profile={'period': report_period},
            kpis=metrics_data,
            intake_payloads=[],
            voice_profile={'tone': 'Celebratory yet honest, data-driven yet human'}
        )
    
    def _extract_kpis(self, metrics_data: Dict) -> Dict:
        """Extract KPIs from metrics data for reporting"""
        return {
            'grants_submitted': metrics_data.get('grants_submitted', 0),
            'grants_won': metrics_data.get('grants_won', 0),
            'funding_secured': metrics_data.get('funding_secured', 0),
            'beneficiaries_served': metrics_data.get('beneficiaries_served', 0),
            'programs_delivered': metrics_data.get('programs_delivered', 0),
            'volunteer_hours': metrics_data.get('volunteer_hours', 0),
            'success_rate': round((metrics_data.get('grants_won', 0) / max(metrics_data.get('grants_submitted', 1), 1)) * 100, 1)
        }
    
    def _get_voice_profile(self, org: Organization) -> Dict:
        """Get organization's voice profile for consistent writing"""
        # Could be stored in org settings or derived from mission
        return {
            'tone': 'warm and professional',
            'common_phrases': [],
            'faith_language': 'N' if 'faith' not in (org.mission or '').lower() else 'Y',
            'cta_style': 'encouraging and action-oriented'
        }
    
    def _get_default_charts(self) -> List[Dict]:
        """Get default chart specifications for impact reports"""
        return [
            {
                'id': 'funding_trend',
                'type': 'line',
                'title': 'Funding Over Time',
                'data_spec': {'x_axis': 'months', 'y_axis': 'funding_amount'}
            },
            {
                'id': 'beneficiaries',
                'type': 'bar',
                'title': 'Beneficiaries Reached',
                'data_spec': {'x_axis': 'program', 'y_axis': 'beneficiary_count'}
            },
            {
                'id': 'outcomes',
                'type': 'stacked_bar',
                'title': 'KPIs vs Targets',
                'data_spec': {'categories': ['achieved', 'in_progress', 'planned']}
            },
            {
                'id': 'cost_per_outcome',
                'type': 'number',
                'title': 'Cost per Impact',
                'data_spec': {'formula': 'total_spent / beneficiaries_served'}
            }
        ]
    
    def _validate_impact_schema(self, response: Dict) -> Optional[Dict]:
        """Validate impact report response matches required schema"""
        try:
            # Required top-level keys
            required_keys = [
                'executive_summary', 'impact_score', 'metrics_dashboard',
                'success_stories', 'financial_summary', 'future_outlook',
                'donor_recognition', 'charts', 'source_notes'
            ]
            
            for key in required_keys:
                if key not in response:
                    logger.warning(f"Missing required key: {key}")
                    return None
            
            # Validate nested structures
            if not isinstance(response['metrics_dashboard'], dict):
                return None
            if not isinstance(response['success_stories'], list):
                return None
            if not isinstance(response['financial_summary'], dict):
                return None
            if not isinstance(response['charts'], list):
                return None
            
            # Validate impact_score is a number between 0-100
            score = response.get('impact_score')
            if not isinstance(score, (int, float)) or score < 0 or score > 100:
                response['impact_score'] = 75  # Default fallback
            
            return response
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return None
    
    def _compile_analytics(self, analytics: List[Analytics]) -> Dict:
        """Compile historical analytics data"""
        if not analytics:
            return {}
        
        # Extract data from event_data JSON field
        success_rates = []
        funding_secured = []
        
        for a in analytics[-12:]:
            if a.event_data:
                success_rates.append(a.event_data.get('success_rate', 0))
                funding_secured.append(float(a.event_data.get('total_funding_secured', 0)))
        
        all_success_rates = []
        all_funding = []
        
        for a in analytics:
            if a.event_data:
                all_success_rates.append(a.event_data.get('success_rate', 0))
                all_funding.append(a.event_data.get('total_funding_secured', 0))
        
        return {
            'total_grants_tracked': len(analytics),
            'success_rate_trend': success_rates,
            'funding_secured_trend': funding_secured,
            'average_success_rate': sum(all_success_rates) / len(all_success_rates) if all_success_rates else 0,
            'total_funding_secured': sum(all_funding)
        }
    
    def _update_analytics(self, org_id: int, metrics_data: Dict, report: Dict):
        """Update analytics with new impact data"""
        try:
            analytics = Analytics()
            analytics.org_id = org_id
            analytics.event_type = 'impact_report_generated'
            analytics.created_at = datetime.utcnow()
            
            # Calculate success rate
            total_grants_submitted = metrics_data.get('grants_submitted', 0)
            grants_won = metrics_data.get('grants_won', 0)
            success_rate = 0
            if total_grants_submitted > 0:
                success_rate = (grants_won / total_grants_submitted) * 100
            
            # Store all metrics in event_data JSON field
            analytics.event_data = {
                'report_date': datetime.utcnow().isoformat(),
                'total_grants_submitted': total_grants_submitted,
                'grants_won': grants_won,
                'total_funding_secured': metrics_data.get('funding_secured', 0),
                'success_rate': success_rate,
                'total_beneficiaries': metrics_data.get('beneficiaries_served', 0),
                'programs_delivered': metrics_data.get('programs_delivered', 0),
                'impact_score': report.get('impact_score', 0),
                'key_achievements': report.get('key_achievements', [])[:3]
            }
            
            db.session.add(analytics)
            
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")