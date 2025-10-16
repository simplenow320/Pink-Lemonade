"""
Enhanced AI Grant Matching System
Industry's most accurate grant matching with multi-dimensional scoring
"""
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from app import db
from app.models import Grant, Organization
from app.services.ai_service import AIService
from app.services.reacto_prompts import ReactoPrompts

logger = logging.getLogger(__name__)

class EnhancedAIGrantMatcher:
    """
    Next-generation grant matching with multi-dimensional scoring
    Quality over quantity approach
    """
    
    # Confidence thresholds for different organization types
    QUALITY_THRESHOLDS = {
        'startup': 60,      # New nonprofits (< 2 years)
        'growing': 70,      # Growing orgs (2-5 years)
        'established': 75,   # Established (5-10 years)
        'enterprise': 85     # Large/mature (10+ years)
    }
    
    # Scoring weights for different dimensions
    DIMENSION_WEIGHTS = {
        'mission_alignment': 0.25,
        'capacity_fit': 0.20,
        'funder_fit': 0.20,
        'competition_level': 0.15,
        'timing_fit': 0.10,
        'relationship_potential': 0.10
    }
    
    def __init__(self):
        self.ai_service = AIService()
        
    def match_grants_with_excellence(self, org_id: int, limit: int = 10) -> List[Dict]:
        """
        Enhanced matching that returns only high-quality matches
        
        Args:
            org_id: Organization ID
            limit: Maximum number of grants to return (quality-filtered)
            
        Returns:
            List of grant matches with multi-dimensional scoring
        """
        try:
            # Get organization profile
            org = Organization.query.get(org_id)
            if not org:
                logger.error(f"Organization {org_id} not found")
                return []
            
            # Get all available grants
            all_grants = Grant.query.filter_by(org_id=org_id).all()
            logger.info(f"Processing {len(all_grants)} grants for enhanced matching")
            
            # Process each grant through enhanced scoring
            scored_grants = []
            for grant in all_grants:
                match_result = self._calculate_enhanced_match(org, grant)
                
                # Only include if meets quality threshold
                org_type = self._determine_org_type(org)
                threshold = self.QUALITY_THRESHOLDS.get(org_type, 70)
                
                if match_result['composite_score'] >= threshold:
                    scored_grants.append(match_result)
            
            # Sort by composite score
            scored_grants.sort(key=lambda x: x['composite_score'], reverse=True)
            
            # Apply intelligent limits
            capacity_limit = self._calculate_capacity_limit(org)
            final_limit = min(limit, capacity_limit)
            
            # Return only the best matches
            top_matches = scored_grants[:final_limit]
            
            logger.info(f"Returning {len(top_matches)} high-quality matches from {len(all_grants)} total")
            return top_matches
            
        except Exception as e:
            logger.error(f"Enhanced matching failed: {str(e)}")
            return []
    
    def _calculate_enhanced_match(self, org: Organization, grant: Grant) -> Dict:
        """
        Calculate multi-dimensional match score
        """
        result = {
            'grant_id': grant.id,
            'grant': grant.to_dict(),
            'dimensions': {},
            'composite_score': 0,
            'confidence_level': 'low',
            'match_explanation': '',
            'success_probability': 0,
            'recommended_action': ''
        }
        
        try:
            # 1. Check hard eligibility (pass/fail)
            eligibility = self._check_eligibility(org, grant)
            if not eligibility['eligible']:
                result['composite_score'] = 0
                result['match_explanation'] = eligibility['reason']
                return result
            
            # 2. Calculate dimension scores
            dimensions = {
                'mission_alignment': self._score_mission_alignment(org, grant),
                'capacity_fit': self._score_capacity_fit(org, grant),
                'funder_fit': self._score_funder_fit(org, grant),
                'competition_level': self._score_competition_level(grant),
                'timing_fit': self._score_timing_fit(org, grant),
                'relationship_potential': self._score_relationship_potential(org, grant)
            }
            result['dimensions'] = dimensions
            
            # 3. Calculate weighted composite score
            composite = sum(
                score * self.DIMENSION_WEIGHTS[dim] 
                for dim, score in dimensions.items()
            )
            result['composite_score'] = round(composite, 1)
            
            # 4. Determine confidence level
            if composite >= 85:
                result['confidence_level'] = 'high'
                result['recommended_action'] = 'Apply Now - Strong Match'
            elif composite >= 70:
                result['confidence_level'] = 'medium'
                result['recommended_action'] = 'Worth Exploring'
            else:
                result['confidence_level'] = 'low'
                result['recommended_action'] = 'Review Carefully'
            
            # 5. Generate detailed explanation
            result['match_explanation'] = self._generate_match_explanation(
                org, grant, dimensions, composite
            )
            
            # 6. Predict success probability
            result['success_probability'] = self._predict_success_rate(
                org, grant, dimensions
            )
            
        except Exception as e:
            logger.error(f"Error calculating enhanced match: {str(e)}")
            
        return result
    
    def _check_eligibility(self, org: Organization, grant: Grant) -> Dict:
        """Check hard eligibility requirements"""
        # Entity type check
        if grant.eligibility and '501(c)(3)' in grant.eligibility:
            if not org.org_type or '501c3' not in org.org_type.lower():
                return {'eligible': False, 'reason': 'Requires 501(c)(3) status'}
        
        # Geographic check
        org_location = f"{org.primary_city or ''}, {org.primary_state or ''}".strip(', ')
        if grant.geography and org_location:
            if grant.geography.lower() not in org_location.lower():
                # Check if it's national/unrestricted
                if 'national' not in grant.geography.lower() and 'unrestricted' not in grant.geography.lower():
                    return {'eligible': False, 'reason': f'Geographic mismatch: requires {grant.geography}'}
        
        # Deadline check (must have at least 14 days)
        if grant.deadline:
            days_until = (grant.deadline - datetime.now().date()).days
            if days_until < 14:
                return {'eligible': False, 'reason': f'Deadline too soon: {days_until} days'}
        
        # Capacity check (grant can't be > 50% of annual budget)
        if grant.amount_max and org.annual_budget:
            try:
                max_amount = float(grant.amount_max)
                budget = float(org.annual_budget)
                if max_amount > budget * 0.5:
                    return {'eligible': False, 'reason': 'Grant size exceeds organizational capacity'}
            except:
                pass
        
        return {'eligible': True, 'reason': 'All requirements met'}
    
    def _score_mission_alignment(self, org: Organization, grant: Grant) -> float:
        """Score mission and program alignment using AI"""
        try:
            prompt = f"""
            Score the mission alignment between this organization and grant (0-100):
            
            ORGANIZATION:
            Mission: {org.mission}
            Programs: {org.programs_services}
            Focus Areas: {org.focus_areas}
            
            GRANT:
            Title: {grant.title}
            Funder: {grant.funder}
            Description: {grant.eligibility}
            
            Consider:
            1. Direct keyword matches
            2. Conceptual alignment
            3. Outcome compatibility
            4. Values alignment
            
            Return only a number 0-100.
            """
            
            response = self.ai_service.generate_text(prompt, max_tokens=10)
            score = float(response.strip())
            return min(100, max(0, score))
        except:
            return 50.0  # Default middle score on error
    
    def _score_capacity_fit(self, org: Organization, grant: Grant) -> float:
        """Score organizational capacity to handle grant"""
        score = 100.0
        
        # Check grant size vs budget
        if grant.amount_max and org.annual_budget:
            try:
                max_amount = float(grant.amount_max)
                budget = float(org.annual_budget)
                ratio = max_amount / budget
                
                if ratio < 0.1:  # Grant is less than 10% of budget
                    score = 90  # Good fit
                elif ratio < 0.3:  # 10-30% of budget
                    score = 100  # Perfect fit
                elif ratio < 0.5:  # 30-50% of budget
                    score = 70  # Stretching capacity
                else:
                    score = 30  # Too large
            except:
                pass
        
        # Factor in organizational age/maturity
        if org.year_established:
            try:
                years_old = datetime.now().year - int(org.year_established)
                if years_old < 2:
                    score *= 0.7  # New orgs have less capacity
                elif years_old > 10:
                    score *= 1.1  # Mature orgs have more capacity
            except:
                pass
        
        return min(100, score)
    
    def _score_funder_fit(self, org: Organization, grant: Grant) -> float:
        """Score how well org fits funder's giving patterns"""
        # This would ideally analyze historical giving data
        # For now, use AI to assess fit
        try:
            prompt = f"""
            Score how well this organization fits the funder's likely preferences (0-100):
            
            FUNDER: {grant.funder}
            Grant Focus: {grant.title}
            
            ORGANIZATION:
            Type: {org.focus_areas}
            Size: {org.annual_budget}
            Location: {org.primary_city}, {org.primary_state}
            
            Consider typical foundation giving patterns.
            Return only a number 0-100.
            """
            
            response = self.ai_service.generate_text(prompt, max_tokens=10)
            score = float(response.strip())
            return min(100, max(0, score))
        except:
            return 60.0
    
    def _score_competition_level(self, grant: Grant) -> float:
        """Estimate competition level (inverse score - less competition = higher score)"""
        # Federal grants typically have high competition
        if grant.source_name and 'federal' in grant.source_name.lower():
            return 40.0
        
        # Foundation grants have medium competition
        if grant.source_name and 'foundation' in grant.source_name.lower():
            return 60.0
        
        # Local/state grants have lower competition
        if grant.geography and any(word in grant.geography.lower() for word in ['city', 'county', 'state']):
            return 80.0
        
        return 50.0  # Default medium competition
    
    def _score_timing_fit(self, org: Organization, grant: Grant) -> float:
        """Score timing alignment"""
        if not grant.deadline:
            return 70.0  # Unknown deadline, neutral score
        
        days_until = (grant.deadline - datetime.now().date()).days
        
        if days_until < 14:
            return 20.0  # Too rushed
        elif days_until < 30:
            return 60.0  # Tight but doable
        elif days_until < 60:
            return 100.0  # Perfect timing
        elif days_until < 90:
            return 90.0  # Good timing
        else:
            return 70.0  # Far out, may forget
    
    def _score_relationship_potential(self, org: Organization, grant: Grant) -> float:
        """Score potential for building funder relationship"""
        score = 50.0  # Base score
        
        # Local funders offer better relationship potential
        org_location = f"{org.primary_city or ''} {org.primary_state or ''}".strip()
        if grant.geography and org_location:
            if any(loc in grant.geography.lower() for loc in org_location.lower().split()):
                score += 30
        
        # Smaller grants often lead to larger ones
        if grant.amount_max:
            try:
                amount = float(grant.amount_max)
                if amount < 100000:  # Under 100K
                    score += 20  # Good for relationship building
            except:
                pass
        
        return min(100, score)
    
    def _generate_match_explanation(self, org: Organization, grant: Grant, 
                                   dimensions: Dict, composite: float) -> str:
        """Generate human-readable explanation of match quality"""
        
        # Find strongest and weakest dimensions
        sorted_dims = sorted(dimensions.items(), key=lambda x: x[1], reverse=True)
        strongest = sorted_dims[0]
        weakest = sorted_dims[-1]
        
        explanation = f"Overall Match: {composite:.0f}%\n\n"
        
        # Highlight strengths
        explanation += "STRENGTHS:\n"
        for dim, score in sorted_dims[:3]:
            if score >= 70:
                dim_name = dim.replace('_', ' ').title()
                explanation += f"✅ {dim_name}: {score:.0f}%\n"
        
        # Note concerns if any
        if weakest[1] < 50:
            explanation += "\nCONSIDERATIONS:\n"
            for dim, score in sorted_dims:
                if score < 50:
                    dim_name = dim.replace('_', ' ').title()
                    explanation += f"⚠️ {dim_name}: {score:.0f}%\n"
        
        return explanation
    
    def _predict_success_rate(self, org: Organization, grant: Grant, dimensions: Dict) -> float:
        """Predict probability of winning grant"""
        # Simple model based on dimension scores
        # In production, this would use ML trained on historical outcomes
        
        base_probability = 0.15  # Average grant success rate
        
        # Adjust based on match quality
        if dimensions['mission_alignment'] > 80:
            base_probability *= 2.0
        if dimensions['capacity_fit'] > 80:
            base_probability *= 1.5
        if dimensions['competition_level'] > 70:
            base_probability *= 1.3
        
        return min(0.95, base_probability)
    
    def _determine_org_type(self, org: Organization) -> str:
        """Determine organization maturity level"""
        if not org.year_established:
            return 'growing'
        
        try:
            years = datetime.now().year - int(org.year_established)
            if years < 2:
                return 'startup'
            elif years < 5:
                return 'growing'
            elif years < 10:
                return 'established'
            else:
                return 'enterprise'
        except:
            return 'growing'
    
    def _calculate_capacity_limit(self, org: Organization) -> int:
        """Calculate how many grants org can realistically pursue"""
        # Base on staff size and grant experience
        base_capacity = 5  # Default
        
        # Adjust based on staff size
        if org.staff_size:
            if 'Full-time' in org.staff_size:
                try:
                    # Extract number from "X Full-time, Y Part-time"
                    ft_count = int(org.staff_size.split()[0])
                    base_capacity = min(15, ft_count * 3)
                except:
                    pass
        
        # Never show more than 15 even for large orgs
        return min(15, base_capacity)