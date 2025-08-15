"""
PHASE 4: AI Writing Assistant
Comprehensive AI-powered grant writing support using GPT-4o
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import json
import os
from app.models import db, Grant, Organization, User
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

class Phase4AIWriter:
    """AI-powered writing assistant for grant applications"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def generate_narrative(self, user_id: int, grant_id: int, narrative_type: str) -> Dict:
        """
        Generate comprehensive grant narrative
        
        Args:
            user_id: User ID
            grant_id: Grant ID
            narrative_type: Type of narrative (mission, need, impact, etc.)
            
        Returns:
            Generated narrative with metadata
        """
        try:
            # Get grant and organization data
            grant = Grant.query.filter_by(id=grant_id, user_id=user_id).first()
            if not grant:
                return {'success': False, 'error': 'Grant not found'}
            
            org = Organization.query.filter_by(user_id=user_id).first()
            if not org:
                return {'success': False, 'error': 'Organization profile not found'}
            
            # Build context from real data
            context = self._build_context(grant, org)
            
            # Generate narrative based on type
            if narrative_type == 'mission_alignment':
                narrative = self._generate_mission_alignment(context)
            elif narrative_type == 'need_statement':
                narrative = self._generate_need_statement(context)
            elif narrative_type == 'impact':
                narrative = self._generate_impact_statement(context)
            elif narrative_type == 'sustainability':
                narrative = self._generate_sustainability_plan(context)
            elif narrative_type == 'budget':
                narrative = self._generate_budget_narrative(context)
            else:
                return {'success': False, 'error': f'Unknown narrative type: {narrative_type}'}
            
            # Calculate quality metrics
            quality_score = self._assess_quality(narrative)
            word_count = len(narrative.split())
            
            return {
                'success': True,
                'narrative': narrative,
                'type': narrative_type,
                'word_count': word_count,
                'quality_score': quality_score,
                'grant_title': grant.title,
                'organization': org.name,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating narrative: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_executive_summary(self, user_id: int, grant_id: int, max_words: int = 250) -> Dict:
        """
        Create concise executive summary
        
        Args:
            user_id: User ID
            grant_id: Grant ID
            max_words: Maximum word count
            
        Returns:
            Executive summary with metadata
        """
        try:
            grant = Grant.query.filter_by(id=grant_id, user_id=user_id).first()
            if not grant:
                return {'success': False, 'error': 'Grant not found'}
            
            org = Organization.query.filter_by(user_id=user_id).first()
            if not org:
                return {'success': False, 'error': 'Organization profile not found'}
            
            context = self._build_context(grant, org)
            
            prompt = f"""
            Create a compelling executive summary for a grant application with these details:
            
            Organization: {org.name}
            Mission: {org.mission}
            Grant: {grant.title}
            Funder: {grant.funding_organization}
            Amount Requested: ${grant.grant_amount or 'TBD'}
            
            Focus Areas: {json.dumps(org.focus_areas) if org.focus_areas else 'General'}
            Programs: {json.dumps(org.programs) if org.programs else 'Various'}
            
            Requirements:
            - Maximum {max_words} words
            - Professional, compelling tone
            - Clear problem statement
            - Specific solution approach
            - Measurable outcomes
            - Direct connection to funder priorities
            
            Write the executive summary:
            """
            
            summary = ai_service.generate_response(prompt, max_tokens=500)
            
            # Ensure word count compliance
            words = summary.split()
            if len(words) > max_words:
                summary = ' '.join(words[:max_words])
            
            return {
                'success': True,
                'executive_summary': summary,
                'word_count': len(summary.split()),
                'max_words': max_words,
                'grant_title': grant.title,
                'quality_score': self._assess_quality(summary)
            }
            
        except Exception as e:
            logger.error(f"Error creating executive summary: {e}")
            return {'success': False, 'error': str(e)}
    
    def write_impact_statement(self, user_id: int, data: Dict) -> Dict:
        """
        Generate compelling impact statement
        
        Args:
            user_id: User ID
            data: Impact data (beneficiaries, outcomes, metrics)
            
        Returns:
            Impact statement with metrics
        """
        try:
            org = Organization.query.filter_by(user_id=user_id).first()
            if not org:
                return {'success': False, 'error': 'Organization profile not found'}
            
            beneficiaries = data.get('beneficiaries', 'community members')
            outcomes = data.get('outcomes', [])
            metrics = data.get('metrics', [])
            timeline = data.get('timeline', '12 months')
            
            prompt = f"""
            Create a powerful impact statement for {org.name} that demonstrates:
            
            Organization Mission: {org.mission}
            Target Beneficiaries: {beneficiaries}
            Expected Outcomes: {json.dumps(outcomes)}
            Success Metrics: {json.dumps(metrics)}
            Timeline: {timeline}
            
            Requirements:
            - Use specific, quantifiable metrics
            - Include both immediate and long-term impact
            - Connect to broader community benefits
            - Professional yet compelling tone
            - Evidence-based projections
            
            Write the impact statement:
            """
            
            impact_statement = ai_service.generate_response(prompt, max_tokens=600)
            
            return {
                'success': True,
                'impact_statement': impact_statement,
                'beneficiaries': beneficiaries,
                'timeline': timeline,
                'word_count': len(impact_statement.split()),
                'quality_score': self._assess_quality(impact_statement)
            }
            
        except Exception as e:
            logger.error(f"Error writing impact statement: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_budget_narrative(self, user_id: int, budget_data: Dict) -> Dict:
        """
        Create detailed budget narrative
        
        Args:
            user_id: User ID
            budget_data: Budget breakdown and details
            
        Returns:
            Budget narrative with justifications
        """
        try:
            org = Organization.query.filter_by(user_id=user_id).first()
            if not org:
                return {'success': False, 'error': 'Organization profile not found'}
            
            total_budget = budget_data.get('total', 0)
            categories = budget_data.get('categories', {})
            
            prompt = f"""
            Create a comprehensive budget narrative for {org.name}:
            
            Total Budget: ${total_budget:,.2f}
            
            Budget Categories:
            {json.dumps(categories, indent=2)}
            
            Organization Context:
            - Annual Budget: {org.annual_budget}
            - Staff Size: {org.staff_size}
            
            Requirements:
            - Justify each budget category
            - Explain cost-effectiveness
            - Show responsible fiscal management
            - Connect expenses to outcomes
            - Professional, detailed tone
            
            Write the budget narrative:
            """
            
            narrative = ai_service.generate_response(prompt, max_tokens=700)
            
            return {
                'success': True,
                'budget_narrative': narrative,
                'total_budget': total_budget,
                'categories': categories,
                'word_count': len(narrative.split()),
                'quality_score': self._assess_quality(narrative)
            }
            
        except Exception as e:
            logger.error(f"Error generating budget narrative: {e}")
            return {'success': False, 'error': str(e)}
    
    def optimize_content(self, content: str, optimization_type: str, target: Optional[Any] = None) -> Dict:
        """
        Optimize existing content
        
        Args:
            content: Original content
            optimization_type: Type of optimization (tone, length, clarity)
            target: Target parameter (word count, tone type, etc.)
            
        Returns:
            Optimized content with changes
        """
        try:
            if optimization_type == 'tone':
                optimized = self._adjust_tone(content, target or 'professional')
            elif optimization_type == 'length':
                optimized = self._adjust_length(content, target or 500)
            elif optimization_type == 'clarity':
                optimized = self._improve_clarity(content)
            elif optimization_type == 'compliance':
                optimized = self._ensure_compliance(content, target)
            else:
                return {'success': False, 'error': f'Unknown optimization type: {optimization_type}'}
            
            changes = self._identify_changes(content, optimized)
            
            return {
                'success': True,
                'original': content,
                'optimized': optimized,
                'optimization_type': optimization_type,
                'changes_made': changes,
                'original_word_count': len(content.split()),
                'optimized_word_count': len(optimized.split()),
                'quality_improvement': self._calculate_improvement(content, optimized)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing content: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_templates(self, template_type: Optional[str] = None) -> Dict:
        """
        Get document templates
        
        Args:
            template_type: Specific template type or None for all
            
        Returns:
            Available templates
        """
        try:
            if template_type:
                template = self.templates.get(template_type)
                if not template:
                    return {'success': False, 'error': f'Template not found: {template_type}'}
                return {
                    'success': True,
                    'template': template,
                    'type': template_type
                }
            
            return {
                'success': True,
                'templates': self.templates,
                'available_types': list(self.templates.keys())
            }
            
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return {'success': False, 'error': str(e)}
    
    # Helper methods
    def _build_context(self, grant: Grant, org: Organization) -> Dict:
        """Build context from grant and organization data"""
        return {
            'grant_title': grant.title,
            'grant_amount': grant.grant_amount,
            'funder': grant.funding_organization,
            'deadline': grant.submission_deadline.isoformat() if grant.submission_deadline else None,
            'requirements': grant.requirements,
            'org_name': org.name,
            'org_mission': org.mission,
            'org_ein': org.ein,
            'focus_areas': org.focus_areas,
            'programs': org.programs,
            'annual_budget': org.annual_budget,
            'staff_size': org.staff_size,
            'geographic_scope': org.geographic_scope
        }
    
    def _generate_mission_alignment(self, context: Dict) -> str:
        """Generate mission alignment narrative"""
        prompt = f"""
        Write a compelling mission alignment narrative that connects:
        
        Organization: {context['org_name']}
        Mission: {context['org_mission']}
        
        With Grant: {context['grant_title']}
        From Funder: {context['funder']}
        
        Focus Areas: {json.dumps(context['focus_areas'])}
        Programs: {json.dumps(context['programs'])}
        
        Requirements:
        - Clear connection between mission and grant purpose
        - Specific examples of alignment
        - Evidence of capacity and experience
        - Professional, persuasive tone
        - 300-500 words
        
        Write the mission alignment narrative:
        """
        
        return ai_service.generate_response(prompt, max_tokens=600)
    
    def _generate_need_statement(self, context: Dict) -> str:
        """Generate need statement"""
        prompt = f"""
        Create a compelling need statement for {context['org_name']}:
        
        Mission: {context['org_mission']}
        Grant Opportunity: {context['grant_title']}
        Focus Areas: {json.dumps(context['focus_areas'])}
        
        Requirements:
        - Clear problem definition
        - Supporting data and evidence
        - Urgency and importance
        - Target population affected
        - Gap in current services
        - 400-600 words
        
        Write the need statement:
        """
        
        return ai_service.generate_response(prompt, max_tokens=700)
    
    def _generate_impact_statement(self, context: Dict) -> str:
        """Generate impact statement"""
        prompt = f"""
        Create an impact statement for {context['org_name']}:
        
        Mission: {context['org_mission']}
        Programs: {json.dumps(context['programs'])}
        Grant Amount: ${context['grant_amount'] or 'TBD'}
        
        Requirements:
        - Specific, measurable outcomes
        - Short-term and long-term impact
        - Number of beneficiaries
        - Community-wide benefits
        - Success metrics
        - 350-500 words
        
        Write the impact statement:
        """
        
        return ai_service.generate_response(prompt, max_tokens=600)
    
    def _generate_sustainability_plan(self, context: Dict) -> str:
        """Generate sustainability plan"""
        prompt = f"""
        Create a sustainability plan for {context['org_name']}:
        
        Organization Budget: {context['annual_budget']}
        Staff Size: {context['staff_size']}
        Grant Amount: ${context['grant_amount'] or 'TBD'}
        
        Requirements:
        - Funding diversification strategy
        - Capacity building plans
        - Partnership development
        - Revenue generation ideas
        - Long-term viability
        - 400-550 words
        
        Write the sustainability plan:
        """
        
        return ai_service.generate_response(prompt, max_tokens=650)
    
    def _assess_quality(self, text: str) -> float:
        """Assess content quality (0-100)"""
        # Simple quality metrics
        word_count = len(text.split())
        sentence_count = text.count('.') + text.count('!') + text.count('?')
        
        # Basic scoring
        score = 70  # Base score
        
        # Word count bonus
        if 200 <= word_count <= 800:
            score += 10
        
        # Sentence variety bonus
        if sentence_count > 5:
            avg_sentence_length = word_count / sentence_count
            if 15 <= avg_sentence_length <= 25:
                score += 10
        
        # Professional language bonus
        professional_terms = ['strategic', 'impact', 'outcomes', 'sustainability', 'implementation']
        for term in professional_terms:
            if term.lower() in text.lower():
                score += 2
        
        return min(score, 100)
    
    def _adjust_tone(self, content: str, target_tone: str) -> str:
        """Adjust content tone"""
        prompt = f"""
        Adjust the following content to have a {target_tone} tone:
        
        Original content:
        {content}
        
        Requirements:
        - Maintain all factual information
        - Keep the same general structure
        - Adjust language and style to be {target_tone}
        - Preserve key messages
        
        Rewritten content:
        """
        
        return ai_service.generate_response(prompt, max_tokens=800)
    
    def _adjust_length(self, content: str, target_words: int) -> str:
        """Adjust content length"""
        current_words = len(content.split())
        
        if current_words > target_words:
            action = "condense and shorten"
        else:
            action = "expand with more detail"
        
        prompt = f"""
        Please {action} the following content to approximately {target_words} words:
        
        Current word count: {current_words}
        Target word count: {target_words}
        
        Content:
        {content}
        
        Requirements:
        - Maintain all key points
        - {action} to reach target length
        - Keep professional tone
        - Preserve important information
        
        Adjusted content:
        """
        
        return ai_service.generate_response(prompt, max_tokens=1000)
    
    def _improve_clarity(self, content: str) -> str:
        """Improve content clarity"""
        prompt = f"""
        Improve the clarity of the following content:
        
        Original:
        {content}
        
        Requirements:
        - Simplify complex sentences
        - Remove jargon where possible
        - Improve logical flow
        - Make key points more prominent
        - Maintain professional tone
        
        Improved content:
        """
        
        return ai_service.generate_response(prompt, max_tokens=800)
    
    def _ensure_compliance(self, content: str, requirements: Dict) -> str:
        """Ensure content meets requirements"""
        prompt = f"""
        Ensure the following content meets these requirements:
        
        Requirements:
        {json.dumps(requirements, indent=2)}
        
        Content to check:
        {content}
        
        Please revise to ensure full compliance with all requirements:
        """
        
        return ai_service.generate_response(prompt, max_tokens=800)
    
    def _identify_changes(self, original: str, optimized: str) -> List[str]:
        """Identify key changes made"""
        changes = []
        
        orig_words = len(original.split())
        opt_words = len(optimized.split())
        
        if abs(orig_words - opt_words) > 10:
            if opt_words > orig_words:
                changes.append(f"Expanded content by {opt_words - orig_words} words")
            else:
                changes.append(f"Reduced content by {orig_words - opt_words} words")
        
        # Check for tone indicators
        formal_indicators = ['therefore', 'furthermore', 'consequently']
        informal_indicators = ["we're", "you'll", "let's"]
        
        orig_formal = sum(1 for word in formal_indicators if word in original.lower())
        opt_formal = sum(1 for word in formal_indicators if word in optimized.lower())
        
        if opt_formal > orig_formal:
            changes.append("Increased formal tone")
        elif opt_formal < orig_formal:
            changes.append("Reduced formality")
        
        if not changes:
            changes.append("Minor adjustments for clarity")
        
        return changes
    
    def _calculate_improvement(self, original: str, optimized: str) -> float:
        """Calculate quality improvement percentage"""
        orig_score = self._assess_quality(original)
        opt_score = self._assess_quality(optimized)
        
        if orig_score == 0:
            return 100.0
        
        improvement = ((opt_score - orig_score) / orig_score) * 100
        return round(improvement, 1)
    
    def _load_templates(self) -> Dict:
        """Load document templates"""
        return {
            'letter_of_support': """
[Your Organization Letterhead]

[Date]

[Funder Name]
[Funder Address]

Dear [Grant Review Committee/Program Officer],

I am writing to express strong support for [Organization Name]'s application for [Grant Name]. As [Your Title] of [Your Organization], I have witnessed firsthand the impact of their work in [Area of Impact].

[Paragraph about partnership/collaboration history]

[Paragraph about organization's strengths and capabilities]

[Paragraph about project importance and expected outcomes]

We are committed to supporting this initiative through [Specific support commitments].

Sincerely,
[Your Name]
[Your Title]
[Contact Information]
            """,
            
            'board_resolution': """
BOARD RESOLUTION

[Organization Name]
[Date]

WHEREAS, [Organization Name] has identified an opportunity to apply for [Grant Name] from [Funder Name]; and

WHEREAS, this grant aligns with our organization's mission to [Mission Statement]; and

WHEREAS, the Board of Directors has reviewed the grant requirements and project proposal;

NOW, THEREFORE, BE IT RESOLVED that:

1. The Board authorizes [Executive Director/CEO Name] to submit the grant application for [Grant Amount].

2. The Board commits to providing necessary matching funds of [Amount] if required.

3. The Board authorizes [Executive Director/CEO Name] to execute all necessary documents related to this grant.

CERTIFIED as a true and correct copy of a resolution adopted at a meeting of the Board of Directors held on [Date].

_______________________
Board Secretary
[Date]
            """,
            
            'evaluation_plan': """
EVALUATION PLAN

Project: [Project Name]
Organization: [Organization Name]
Grant Period: [Start Date] - [End Date]

1. EVALUATION OBJECTIVES
   - [Objective 1]
   - [Objective 2]
   - [Objective 3]

2. KEY PERFORMANCE INDICATORS
   Output Metrics:
   - [Metric 1]: Target: [Number]
   - [Metric 2]: Target: [Number]
   
   Outcome Metrics:
   - [Metric 1]: Target: [Percentage/Number]
   - [Metric 2]: Target: [Percentage/Number]

3. DATA COLLECTION METHODS
   - [Method 1]: [Frequency]
   - [Method 2]: [Frequency]

4. EVALUATION TIMELINE
   - Baseline Data: [Date]
   - Quarterly Reports: [Dates]
   - Final Evaluation: [Date]

5. RESPONSIBLE PARTIES
   - Evaluation Lead: [Name/Title]
   - Data Collection: [Name/Title]
   - Report Preparation: [Name/Title]
            """
        }

# Singleton instance
phase4_writer = Phase4AIWriter()