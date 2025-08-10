"""
Advanced AI Reasoning Engine for Multi-Step Grant Analysis
Implements sophisticated chain of reasoning and context analysis
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from app.services.ai_service import AIService
from app.models import Organization, Grant, Analytics

logger = logging.getLogger(__name__)

class AIReasoningEngine:
    """
    Advanced reasoning engine that implements:
    - Multi-step reasoning chains
    - Contextual analysis with decision trees
    - Confidence scoring with explanations
    - Learning from historical patterns
    """
    
    def __init__(self):
        self.ai_service = AIService()
        self.reasoning_steps = []
        self.confidence_factors = {}
        self.decision_tree = {}
        
    def analyze_grant_match(self, organization: Organization, grant: Dict) -> Dict:
        """
        Perform deep multi-step reasoning for grant matching
        Returns comprehensive analysis with confidence scores and reasoning chains
        """
        try:
            # Step 1: Initialize reasoning context
            context = self._build_organization_context(organization)
            grant_context = self._extract_grant_features(grant)
            
            # Step 2: Execute multi-step reasoning chain
            reasoning_chain = []
            
            # Step 2a: Mission Alignment Analysis
            mission_analysis = self._analyze_mission_alignment(context, grant_context)
            reasoning_chain.append({
                'step': 'Mission Alignment',
                'score': mission_analysis['score'],
                'reasoning': mission_analysis['reasoning'],
                'confidence': mission_analysis['confidence']
            })
            
            # Step 2b: Capacity Assessment
            capacity_analysis = self._assess_organizational_capacity(context, grant_context)
            reasoning_chain.append({
                'step': 'Capacity Assessment',
                'score': capacity_analysis['score'],
                'reasoning': capacity_analysis['reasoning'],
                'confidence': capacity_analysis['confidence']
            })
            
            # Step 2c: Geographic Fit Analysis
            geographic_analysis = self._analyze_geographic_fit(context, grant_context)
            reasoning_chain.append({
                'step': 'Geographic Fit',
                'score': geographic_analysis['score'],
                'reasoning': geographic_analysis['reasoning'],
                'confidence': geographic_analysis['confidence']
            })
            
            # Step 2d: Financial Alignment
            financial_analysis = self._analyze_financial_alignment(context, grant_context)
            reasoning_chain.append({
                'step': 'Financial Alignment',
                'score': financial_analysis['score'],
                'reasoning': financial_analysis['reasoning'],
                'confidence': financial_analysis['confidence']
            })
            
            # Step 2e: Historical Success Pattern
            historical_analysis = self._analyze_historical_patterns(organization, grant_context)
            reasoning_chain.append({
                'step': 'Historical Patterns',
                'score': historical_analysis['score'],
                'reasoning': historical_analysis['reasoning'],
                'confidence': historical_analysis['confidence']
            })
            
            # Step 3: Synthesize overall recommendation
            overall_score, confidence, recommendation = self._synthesize_recommendation(reasoning_chain)
            
            # Step 4: Generate actionable insights
            insights = self._generate_actionable_insights(reasoning_chain, context, grant_context)
            
            return {
                'match_score': overall_score,
                'confidence': confidence,
                'recommendation': recommendation,
                'reasoning_chain': reasoning_chain,
                'insights': insights,
                'decision_factors': self._extract_key_decision_factors(reasoning_chain),
                'next_steps': self._recommend_next_steps(overall_score, insights),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in grant match analysis: {e}")
            return {
                'match_score': 0,
                'confidence': 'low',
                'error': str(e)
            }
    
    def _build_organization_context(self, org: Organization) -> Dict:
        """Build comprehensive organization context for analysis"""
        return {
            'mission': org.mission,
            'focus_areas': org.primary_focus_areas or [],
            'secondary_areas': org.secondary_focus_areas or [],
            'capacity': {
                'budget': org.annual_budget_range,
                'staff': org.staff_size,
                'grant_writing': org.grant_writing_capacity
            },
            'location': {
                'city': org.primary_city,
                'state': org.primary_state,
                'service_area': org.service_area_type
            },
            'history': {
                'previous_funders': org.previous_funders or [],
                'typical_grant_size': org.typical_grant_size,
                'success_rate': org.grant_success_rate
            },
            'characteristics': {
                'faith_based': org.faith_based,
                'minority_led': org.minority_led,
                'woman_led': org.woman_led
            },
            'unique_value': org.unique_capabilities,
            'keywords': org.keywords or []
        }
    
    def _extract_grant_features(self, grant: Dict) -> Dict:
        """Extract key features from grant for analysis"""
        return {
            'title': grant.get('title', ''),
            'funder': grant.get('funder', ''),
            'amount_range': {
                'min': grant.get('amount_min', 0),
                'max': grant.get('amount_max', 0)
            },
            'focus_areas': grant.get('focus_areas', []),
            'requirements': grant.get('requirements', {}),
            'geographic_scope': grant.get('geographic_scope', ''),
            'deadline': grant.get('deadline', ''),
            'description': grant.get('description', ''),
            'eligibility': grant.get('eligibility', []),
            'priorities': grant.get('funder_priorities', [])
        }
    
    def _analyze_mission_alignment(self, org_context: Dict, grant_context: Dict) -> Dict:
        """Deep analysis of mission alignment"""
        score = 0
        reasoning = []
        confidence_level = 'medium'
        
        # Analyze primary focus area overlap
        org_areas = set(org_context['focus_areas'])
        grant_areas = set(grant_context['focus_areas'])
        overlap = org_areas.intersection(grant_areas)
        
        if overlap:
            score += 40
            reasoning.append(f"Strong alignment in {len(overlap)} focus areas: {', '.join(overlap)}")
            if len(overlap) >= 3:
                confidence_level = 'high'
        
        # Check secondary areas
        secondary_overlap = set(org_context['secondary_areas']).intersection(grant_areas)
        if secondary_overlap:
            score += 20
            reasoning.append(f"Additional alignment in secondary areas: {', '.join(secondary_overlap)}")
        
        # Keyword matching in description
        keyword_matches = sum(1 for kw in org_context['keywords'] 
                             if kw.lower() in grant_context['description'].lower())
        if keyword_matches > 0:
            score += min(20, keyword_matches * 5)
            reasoning.append(f"Found {keyword_matches} keyword matches in grant description")
        
        # Special characteristics bonus
        if org_context['characteristics']['faith_based'] and 'faith' in grant_context['description'].lower():
            score += 10
            reasoning.append("Faith-based alignment identified")
        
        if org_context['characteristics']['minority_led'] and 'minority' in grant_context['description'].lower():
            score += 10
            reasoning.append("Minority-led organization preference matched")
        
        return {
            'score': min(100, score),
            'reasoning': reasoning,
            'confidence': confidence_level
        }
    
    def _assess_organizational_capacity(self, org_context: Dict, grant_context: Dict) -> Dict:
        """Assess if organization has capacity to handle grant"""
        score = 0
        reasoning = []
        confidence_level = 'medium'
        
        # Budget size alignment
        grant_max = grant_context['amount_range']['max']
        org_budget = org_context['capacity']['budget']
        
        if org_budget:
            if '$100k-500k' in org_budget and grant_max <= 500000:
                score += 30
                reasoning.append("Grant size aligns with organizational budget capacity")
            elif '$500k-1M' in org_budget and grant_max <= 1000000:
                score += 30
                reasoning.append("Organization has proven capacity for this grant size")
                confidence_level = 'high'
        
        # Staff capacity
        if org_context['capacity']['staff']:
            if 'small grant' in grant_context['description'].lower() and '1-5' in org_context['capacity']['staff']:
                score += 20
                reasoning.append("Small grant appropriate for small staff size")
            elif '11-25' in org_context['capacity']['staff'] or '26+' in org_context['capacity']['staff']:
                score += 25
                reasoning.append("Adequate staff capacity for grant management")
        
        # Grant writing capacity
        if org_context['capacity']['grant_writing'] in ['internal', 'both']:
            score += 25
            reasoning.append("Internal grant writing capacity available")
            confidence_level = 'high' if score > 60 else confidence_level
        
        # Previous experience with similar amounts
        if org_context['history']['typical_grant_size']:
            typical_size = org_context['history']['typical_grant_size']
            if self._is_grant_size_compatible(typical_size, grant_max):
                score += 20
                reasoning.append(f"Previous experience with similar grant sizes ({typical_size})")
        
        return {
            'score': min(100, score),
            'reasoning': reasoning,
            'confidence': confidence_level
        }
    
    def _analyze_geographic_fit(self, org_context: Dict, grant_context: Dict) -> Dict:
        """Analyze geographic alignment"""
        score = 0
        reasoning = []
        confidence_level = 'high'  # Geographic matching is usually clear
        
        grant_scope = grant_context.get('geographic_scope', '').lower()
        org_location = org_context['location']
        
        # Check for national grants
        if 'national' in grant_scope or 'nationwide' in grant_scope:
            score = 100
            reasoning.append("National grant - geographic location not restrictive")
        
        # State-level matching
        elif org_location['state'] and org_location['state'].lower() in grant_scope:
            score = 100
            reasoning.append(f"Perfect state match: {org_location['state']}")
        
        # City-level matching
        elif org_location['city'] and org_location['city'].lower() in grant_scope:
            score = 100
            reasoning.append(f"Perfect city match: {org_location['city']}")
        
        # Regional matching
        elif org_location['service_area'] == 'regional' and 'regional' in grant_scope:
            score = 80
            reasoning.append("Regional service area matches grant scope")
        
        # No clear geographic restrictions
        elif not grant_scope or grant_scope == 'unspecified':
            score = 70
            reasoning.append("No geographic restrictions identified")
            confidence_level = 'medium'
        
        else:
            score = 20
            reasoning.append("Geographic mismatch - may still be eligible with justification")
            confidence_level = 'low'
        
        return {
            'score': score,
            'reasoning': reasoning,
            'confidence': confidence_level
        }
    
    def _analyze_financial_alignment(self, org_context: Dict, grant_context: Dict) -> Dict:
        """Analyze financial fit between grant and organization"""
        score = 0
        reasoning = []
        confidence_level = 'medium'
        
        grant_min = grant_context['amount_range']['min']
        grant_max = grant_context['amount_range']['max']
        
        # Check if grant size matches historical patterns
        if org_context['history']['typical_grant_size']:
            if self._is_grant_size_compatible(org_context['history']['typical_grant_size'], grant_max):
                score += 40
                reasoning.append("Grant amount aligns with historical funding patterns")
                confidence_level = 'high'
        
        # Analyze if grant is too small or too large
        if grant_max < 10000:
            if '1-5' in org_context['capacity'].get('staff', ''):
                score += 30
                reasoning.append("Small grant appropriate for organization size")
            else:
                score += 10
                reasoning.append("Grant may be too small to justify effort")
                confidence_level = 'low'
        
        elif grant_max > 100000:
            if org_context['capacity']['budget'] in ['$500k-1M', '$1M+']:
                score += 30
                reasoning.append("Organization has capacity for large grants")
            else:
                score += 15
                reasoning.append("Large grant may require capacity building")
        
        else:  # Mid-range grant
            score += 30
            reasoning.append("Grant size in optimal range for most organizations")
        
        return {
            'score': min(100, score),
            'reasoning': reasoning,
            'confidence': confidence_level
        }
    
    def _analyze_historical_patterns(self, org: Organization, grant_context: Dict) -> Dict:
        """Analyze based on historical success patterns"""
        score = 50  # Baseline
        reasoning = []
        confidence_level = 'low'  # Default when no history
        
        try:
            # Check for previous funders similarity
            if org.previous_funders:
                for funder in org.previous_funders:
                    if funder.lower() in grant_context['funder'].lower():
                        score = 90
                        reasoning.append(f"Previous successful relationship with {funder}")
                        confidence_level = 'very_high'
                        break
            
            # Check success rate
            if org.grant_success_rate:
                if org.grant_success_rate > 0.7:
                    score += 20
                    reasoning.append(f"High historical success rate: {org.grant_success_rate*100:.0f}%")
                    confidence_level = 'high'
                elif org.grant_success_rate > 0.4:
                    score += 10
                    reasoning.append(f"Moderate success rate: {org.grant_success_rate*100:.0f}%")
                    confidence_level = 'medium'
            
            # Look for similar grant types in history
            if org.preferred_grant_types:
                grant_type_match = any(gt in grant_context['title'].lower() 
                                      for gt in org.preferred_grant_types)
                if grant_type_match:
                    score += 15
                    reasoning.append("Grant type matches organization's preferred types")
            
            if not reasoning:
                reasoning.append("Limited historical data available for pattern analysis")
                
        except Exception as e:
            logger.error(f"Error in historical analysis: {e}")
            reasoning.append("Unable to complete historical analysis")
        
        return {
            'score': min(100, score),
            'reasoning': reasoning,
            'confidence': confidence_level
        }
    
    def _synthesize_recommendation(self, reasoning_chain: List[Dict]) -> Tuple[float, str, str]:
        """Synthesize overall recommendation from reasoning chain"""
        
        # Calculate weighted average score
        weights = {
            'Mission Alignment': 0.30,
            'Capacity Assessment': 0.20,
            'Geographic Fit': 0.20,
            'Financial Alignment': 0.20,
            'Historical Patterns': 0.10
        }
        
        total_score = 0
        total_weight = 0
        confidence_scores = []
        
        for step in reasoning_chain:
            step_name = step['step']
            if step_name in weights:
                total_score += step['score'] * weights[step_name]
                total_weight += weights[step_name]
                
                # Convert confidence to numeric
                conf_map = {'low': 1, 'medium': 2, 'high': 3, 'very_high': 4}
                confidence_scores.append(conf_map.get(step['confidence'], 2))
        
        # Calculate overall score
        overall_score = total_score / total_weight if total_weight > 0 else 0
        
        # Determine confidence level
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 2
        if avg_confidence >= 3:
            confidence = 'high'
        elif avg_confidence >= 2:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        # Generate recommendation
        if overall_score >= 80:
            recommendation = "STRONGLY RECOMMENDED - This grant is an excellent match. Prioritize application."
        elif overall_score >= 60:
            recommendation = "RECOMMENDED - Good alignment. Worth pursuing with proper preparation."
        elif overall_score >= 40:
            recommendation = "CONSIDER - Moderate fit. Evaluate capacity and competition before applying."
        else:
            recommendation = "NOT RECOMMENDED - Poor alignment. Focus efforts on better matches."
        
        return overall_score, confidence, recommendation
    
    def _generate_actionable_insights(self, reasoning_chain: List[Dict], 
                                     org_context: Dict, grant_context: Dict) -> List[str]:
        """Generate specific actionable insights"""
        insights = []
        
        # Analyze strengths
        strong_areas = [step for step in reasoning_chain if step['score'] >= 70]
        if strong_areas:
            insights.append(f"Key strengths: {', '.join([s['step'] for s in strong_areas])}")
        
        # Identify gaps
        weak_areas = [step for step in reasoning_chain if step['score'] < 50]
        for area in weak_areas:
            if area['step'] == 'Capacity Assessment':
                insights.append("Consider partnering or hiring consultant to strengthen capacity")
            elif area['step'] == 'Mission Alignment':
                insights.append("Emphasize transferable skills and indirect alignment in application")
        
        # Timeline insights
        if grant_context.get('deadline'):
            insights.append(f"Application deadline: {grant_context['deadline']} - Plan accordingly")
        
        # Competition insights
        if org_context['characteristics']['minority_led'] or org_context['characteristics']['woman_led']:
            insights.append("Leverage diversity characteristics if funder prioritizes equity")
        
        return insights
    
    def _extract_key_decision_factors(self, reasoning_chain: List[Dict]) -> List[Dict]:
        """Extract the most important decision factors"""
        factors = []
        
        for step in reasoning_chain:
            if step['score'] >= 80:
                factors.append({
                    'factor': step['step'],
                    'impact': 'positive',
                    'weight': 'high',
                    'reason': step['reasoning'][0] if step['reasoning'] else ''
                })
            elif step['score'] <= 30:
                factors.append({
                    'factor': step['step'],
                    'impact': 'negative',
                    'weight': 'high',
                    'reason': step['reasoning'][0] if step['reasoning'] else ''
                })
        
        return factors[:3]  # Top 3 factors
    
    def _recommend_next_steps(self, score: float, insights: List[str]) -> List[str]:
        """Recommend specific next steps based on analysis"""
        steps = []
        
        if score >= 60:
            steps.append("Review grant guidelines in detail")
            steps.append("Gather required documentation")
            steps.append("Start drafting narrative with AI assistance")
            steps.append("Identify and reach out to partners if needed")
        elif score >= 40:
            steps.append("Assess whether gaps can be addressed")
            steps.append("Consider reaching out to funder for clarification")
            steps.append("Evaluate ROI of application effort")
        else:
            steps.append("Archive this opportunity")
            steps.append("Focus on better-aligned grants")
        
        return steps
    
    def _is_grant_size_compatible(self, typical_size: str, grant_amount: float) -> bool:
        """Check if grant size is compatible with typical amounts"""
        size_ranges = {
            '<$10k': (0, 10000),
            '$10k-25k': (10000, 25000),
            '$25k-50k': (25000, 50000),
            '$50k-100k': (50000, 100000),
            '$100k-500k': (100000, 500000),
            '$500k+': (500000, float('inf'))
        }
        
        if typical_size in size_ranges:
            min_amt, max_amt = size_ranges[typical_size]
            return min_amt <= grant_amount <= max_amt * 2  # Allow some flexibility
        
        return True  # Default to compatible if unknown
    
    def learn_from_outcome(self, org_id: int, grant_id: int, outcome: str, feedback: Dict):
        """Learn from grant application outcomes to improve future predictions"""
        try:
            # Store learning data
            learning_entry = {
                'org_id': org_id,
                'grant_id': grant_id,
                'outcome': outcome,  # 'won', 'lost', 'withdrawn'
                'feedback': feedback,
                'timestamp': datetime.utcnow()
            }
            
            # Update organization's success patterns
            # This would be stored in a learning database
            logger.info(f"Learning from outcome: {outcome} for org {org_id}, grant {grant_id}")
            
            # Adjust confidence weights based on outcome
            if outcome == 'won':
                # Increase weight of factors that led to success
                pass
            elif outcome == 'lost':
                # Analyze why and adjust reasoning weights
                pass
            
        except Exception as e:
            logger.error(f"Error in learning from outcome: {e}")