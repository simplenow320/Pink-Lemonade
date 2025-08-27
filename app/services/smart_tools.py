"""
Smart Tools Suite
AI-powered tools for Grant Pitch, Case for Support, and Impact Reporting
"""

from typing import Dict, List, Optional
from datetime import datetime
from app.services.ai_service import AIService
from app.services.reacto_prompts import ReactoPrompts
from app.models import Grant, Organization, Narrative, Analytics, db
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
    
    # ============= GRANT PITCH TOOL =============
    
    def generate_grant_pitch(self, org_id: int, grant_id: Optional[int] = None, 
                            pitch_type: str = 'elevator') -> Dict:
        """
        Generate a compelling grant pitch
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
            if grant_id:
                grant = Grant.query.get(grant_id)
                if grant:
                    grant_context = grant.to_dict()
            
            # Generate REACTO prompt for pitch
            prompt = self._create_pitch_prompt(org_context, grant_context, pitch_type)
            
            # Get AI response
            response = self.ai_service.generate_json_response(prompt)
            
            if response:
                # Save pitch as narrative
                narrative = Narrative()
                narrative.org_id = org_id
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
                    'key_points': response.get('key_points', []),
                    'call_to_action': response.get('call_to_action', ''),
                    'word_count': response.get('word_count', 0),
                    'speaking_time': response.get('speaking_time', '60 seconds'),
                    'tips': response.get('delivery_tips', [])
                }
            
            return {'success': False, 'error': 'Failed to generate pitch'}
            
        except Exception as e:
            logger.error(f"Error generating pitch: {e}")
            return {'success': False, 'error': str(e)}
    
    # ============= CASE FOR SUPPORT TOOL =============
    
    def generate_case_for_support(self, org_id: int, campaign_details: Dict) -> Dict:
        """
        Generate comprehensive case for support document
        Includes: problem statement, solution, impact, urgency, credibility
        """
        try:
            # Get organization
            org = Organization.query.get(org_id)
            if not org:
                return {'success': False, 'error': 'Organization not found'}
            
            org_context = self._build_org_context(org)
            
            # Generate REACTO prompt for case
            prompt = self._create_case_prompt(org_context, campaign_details)
            
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
                        narrative.org_id = org_id
                        narrative.section = f'case_{section_name}'
                        narrative.content = content
                        narrative.ai_generated = True
                        narrative.created_at = datetime.utcnow()
                        db.session.add(narrative)
                
                db.session.commit()
                
                return {
                    'success': True,
                    'sections': sections,
                    'key_messages': response.get('key_messages', []),
                    'emotional_hooks': response.get('emotional_hooks', []),
                    'data_points': response.get('data_points', []),
                    'donor_personas': response.get('donor_personas', []),
                    'total_word_count': response.get('total_word_count', 0)
                }
            
            return {'success': False, 'error': 'Failed to generate case for support'}
            
        except Exception as e:
            logger.error(f"Error generating case for support: {e}")
            return {'success': False, 'error': str(e)}
    
    # ============= IMPACT REPORTING TOOL =============
    
    def generate_impact_report(self, org_id: int, report_period: Dict, 
                              metrics_data: Dict) -> Dict:
        """
        Generate data-driven impact report with storytelling
        Includes: metrics visualization, success stories, outcomes
        """
        try:
            # Get organization
            org = Organization.query.get(org_id)
            if not org:
                return {'success': False, 'error': 'Organization not found'}
            
            org_context = self._build_org_context(org)
            
            # Get historical analytics
            analytics = Analytics.query.filter_by(org_id=org_id).all()
            historical_data = self._compile_analytics(analytics)
            
            # Generate REACTO prompt for impact report
            prompt = self._create_impact_prompt(
                org_context, 
                report_period, 
                metrics_data,
                historical_data
            )
            
            # Get AI response
            response = self.ai_service.generate_json_response(prompt)
            
            if response:
                # Save report sections
                report = {
                    'executive_summary': response.get('executive_summary', ''),
                    'key_achievements': response.get('key_achievements', []),
                    'metrics_analysis': response.get('metrics_analysis', {}),
                    'success_stories': response.get('success_stories', []),
                    'challenges_overcome': response.get('challenges_overcome', []),
                    'lessons_learned': response.get('lessons_learned', []),
                    'future_outlook': response.get('future_outlook', ''),
                    'donor_recognition': response.get('donor_recognition', ''),
                    'financial_summary': response.get('financial_summary', {}),
                    'visualizations': response.get('recommended_charts', [])
                }
                
                # Save impact report
                narrative = Narrative()
                narrative.org_id = org_id
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
    
    # ============= QUICK TOOLS =============
    
    def generate_thank_you_letter(self, org_id: int, donor_info: Dict) -> Dict:
        """Generate personalized thank you letter"""
        try:
            org = Organization.query.get(org_id)
            if not org:
                return {'success': False, 'error': 'Organization not found'}
            
            prompt = f"""
            # R - ROLE
            You are a nonprofit communications expert specializing in donor stewardship.
            
            # E - EXAMPLE
            A heartfelt thank you that makes the donor feel like a hero, not just a checkbook.
            
            # A - APPLICATION
            Generate a personalized thank you letter that:
            1. Opens with specific gratitude
            2. Shows immediate impact of their gift
            3. Shares a brief success story
            4. Looks forward to continued partnership
            5. Closes with personal touch
            
            # C - CONTEXT
            Organization: {org.name}
            Mission: {org.mission}
            Donor: {donor_info.get('name', 'Valued Supporter')}
            Gift Amount: ${donor_info.get('amount', 0):,.0f}
            Gift Purpose: {donor_info.get('purpose', 'general support')}
            
            # T - TONE
            Warm, genuine, personal. Not corporate or generic.
            
            # O - OUTPUT
            Return JSON:
            {{
                "letter_text": "complete letter",
                "subject_line": "email subject",
                "key_impact_points": ["point1", "point2"],
                "follow_up_date": "suggested date"
            }}
            """
            
            response = self.ai_service.generate_json_response(prompt)
            return {'success': True, **response} if response else {'success': False}
            
        except Exception as e:
            logger.error(f"Error generating thank you: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_social_media_post(self, org_id: int, platform: str, 
                                  topic: str) -> Dict:
        """Generate platform-optimized social media content"""
        try:
            org = Organization.query.get(org_id)
            if not org:
                return {'success': False, 'error': 'Organization not found'}
            
            char_limits = {
                'twitter': 280,
                'facebook': 500,
                'instagram': 2200,
                'linkedin': 3000
            }
            
            prompt = f"""
            # R - ROLE
            You are a nonprofit social media strategist.
            
            # E - EXAMPLE
            Engaging posts that inspire action and build community.
            
            # A - APPLICATION
            Create {platform} post about {topic} that:
            1. Grabs attention immediately
            2. Tells a micro-story or shares impact
            3. Includes clear call-to-action
            4. Uses platform best practices
            5. Stays under {char_limits.get(platform, 500)} characters
            
            # C - CONTEXT
            Organization: {org.name}
            Mission: {org.mission}
            Topic: {topic}
            
            # T - TONE
            Authentic, hopeful, action-oriented.
            
            # O - OUTPUT
            Return JSON:
            {{
                "post_text": "complete post",
                "hashtags": ["tag1", "tag2"],
                "best_time_to_post": "time suggestion",
                "engagement_tips": ["tip1", "tip2"]
            }}
            """
            
            response = self.ai_service.generate_json_response(prompt)
            return {'success': True, 'platform': platform, **response} if response else {'success': False}
            
        except Exception as e:
            logger.error(f"Error generating social post: {e}")
            return {'success': False, 'error': str(e)}
    
    # ============= HELPER METHODS =============
    
    def _build_org_context(self, org: Organization) -> Dict:
        """Build comprehensive organization context"""
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
            'current_programs': getattr(org, 'current_programs', [])
        }
    
    def _create_pitch_prompt(self, org_context: Dict, grant_context: Optional[Dict], 
                           pitch_type: str) -> str:
        """Create REACTO prompt for pitch generation"""
        time_limits = {
            'elevator': '60 seconds',
            'executive': '2 minutes',
            'detailed': '5 minutes'
        }
        
        grant_info = ""
        if grant_context:
            grant_info = f"""
            Grant Opportunity: {grant_context.get('title', 'Grant')}
            Funder: {grant_context.get('funder', 'Funder')}
            Focus: {grant_context.get('focus_area', 'General')}
            Amount: ${grant_context.get('amount_max', 50000):,.0f}
            """
        
        return f"""
        # R - ROLE
        You are a master grant pitch coach with 20 years of experience helping nonprofits win funding.
        
        # E - EXAMPLE
        The best pitches tell a story: Problem → Solution → Impact → Ask.
        Example opening: "Every night, 500 children in our city go to bed hungry. We're changing that."
        
        # A - APPLICATION
        Create a {pitch_type} pitch ({time_limits[pitch_type]}) that:
        1. Opens with compelling hook (first 10 seconds crucial)
        2. Clearly states the problem and its urgency
        3. Presents your unique solution
        4. Demonstrates proven or projected impact
        5. Makes specific, actionable ask
        6. Closes with memorable call-to-action
        
        # C - CONTEXT
        Organization: {org_context['name']}
        Mission: {org_context['mission']}
        Focus Areas: {org_context['focus_areas']}
        Unique Strengths: {org_context['unique_capabilities']}
        {grant_info}
        
        # T - TONE
        Confident, passionate, data-informed but human-centered. 
        Balance emotional appeal with credibility.
        
        # O - OUTPUT
        Return JSON with:
        {{
            "pitch_text": "complete pitch script",
            "hook": "opening attention grabber",
            "key_points": ["point1", "point2", "point3"],
            "call_to_action": "specific ask",
            "word_count": number,
            "speaking_time": "estimated time",
            "delivery_tips": ["tip1", "tip2"]
        }}
        """
    
    def _create_case_prompt(self, org_context: Dict, campaign_details: Dict) -> str:
        """Create REACTO prompt for case for support"""
        return f"""
        # R - ROLE
        You are a fundraising consultant specializing in major gift campaigns and case development.
        
        # E - EXAMPLE
        Successful cases combine compelling narrative with concrete evidence.
        Example: "We don't just feed people; we restore dignity and rebuild lives."
        
        # A - APPLICATION
        Develop comprehensive case for support with:
        1. Executive Summary - One-page overview
        2. Problem Statement - Why this matters now
        3. Our Solution - How we uniquely address this
        4. Impact Evidence - Proof we can deliver
        5. Why Now - Urgency and opportunity
        6. Why Us - Our unique position to succeed
        7. Investment Needed - Specific funding goals
        8. Donor Benefits - What supporters receive
        9. Call to Action - Clear next steps
        
        # C - CONTEXT
        Organization: {org_context['name']}
        Mission: {org_context['mission']}
        Campaign Goal: ${campaign_details.get('goal', 100000):,.0f}
        Campaign Purpose: {campaign_details.get('purpose', 'expansion')}
        Timeline: {campaign_details.get('timeline', '12 months')}
        Target Donors: {campaign_details.get('target_donors', 'major donors')}
        
        # T - TONE
        Inspiring yet practical, urgent yet sustainable, professional yet personal.
        
        # O - OUTPUT
        Return JSON with all sections plus:
        {{
            "executive_summary": "text",
            "problem_statement": "text",
            "our_solution": "text",
            "impact_evidence": "text",
            "why_now": "text",
            "why_us": "text",
            "investment_needed": "text",
            "donor_benefits": "text",
            "call_to_action": "text",
            "key_messages": ["msg1", "msg2"],
            "emotional_hooks": ["hook1", "hook2"],
            "data_points": ["data1", "data2"],
            "donor_personas": ["persona1", "persona2"],
            "total_word_count": number
        }}
        """
    
    def _create_impact_prompt(self, org_context: Dict, report_period: Dict, 
                             metrics_data: Dict, historical_data: Dict) -> str:
        """Create REACTO prompt for impact reporting"""
        return f"""
        # R - ROLE
        You are an impact measurement expert and data storyteller for nonprofits.
        
        # E - EXAMPLE
        Great impact reports blend numbers with narratives.
        Example: "This year, 1,247 students graduated - but behind each number is a story of transformation."
        
        # A - APPLICATION
        Generate impact report that:
        1. Leads with most impressive achievements
        2. Visualizes data meaningfully
        3. Tells representative success stories
        4. Acknowledges challenges honestly
        5. Demonstrates learning and adaptation
        6. Shows financial stewardship
        7. Recognizes supporters appropriately
        8. Projects future with confidence
        
        # C - CONTEXT
        Organization: {org_context['name']}
        Report Period: {report_period.get('start')} to {report_period.get('end')}
        
        Key Metrics:
        {json.dumps(metrics_data, indent=2)}
        
        Historical Trends:
        {json.dumps(historical_data, indent=2) if historical_data else 'First report'}
        
        # T - TONE
        Celebratory yet honest, data-driven yet human, grateful yet forward-looking.
        
        # O - OUTPUT
        Return comprehensive JSON with all sections, metrics analysis, and recommendations.
        Include specific data visualizations to create.
        """
    
    def _compile_analytics(self, analytics: List[Analytics]) -> Dict:
        """Compile historical analytics data"""
        if not analytics:
            return {}
        
        return {
            'total_grants_tracked': len(analytics),
            'success_rate_trend': [a.success_rate for a in analytics[-12:]],
            'funding_secured_trend': [float(a.total_funding_secured) for a in analytics[-12:]],
            'average_success_rate': sum(a.success_rate for a in analytics) / len(analytics),
            'total_funding_secured': sum(a.total_funding_secured for a in analytics)
        }
    
    def _update_analytics(self, org_id: int, metrics_data: Dict, report: Dict):
        """Update analytics with new impact data"""
        try:
            analytics = Analytics()
            analytics.org_id = org_id
            analytics.report_date = datetime.utcnow()
            
            # Extract key metrics
            analytics.total_grants_submitted = metrics_data.get('grants_submitted', 0)
            analytics.grants_won = metrics_data.get('grants_won', 0)
            analytics.total_funding_secured = metrics_data.get('funding_secured', 0)
            
            # Calculate success rate
            if analytics.total_grants_submitted > 0:
                analytics.success_rate = (analytics.grants_won / analytics.total_grants_submitted) * 100
            else:
                analytics.success_rate = 0
            
            # Store impact metrics
            analytics.total_beneficiaries = metrics_data.get('beneficiaries_served', 0)
            analytics.programs_delivered = metrics_data.get('programs_delivered', 0)
            
            # Store report reference
            analytics.report_data = json.dumps({
                'impact_score': report.get('impact_score', 0),
                'key_achievements': report.get('key_achievements', [])[:3]
            })
            
            db.session.add(analytics)
            
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")