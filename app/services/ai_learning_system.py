"""
AI Learning System for Continuous Improvement
Implements feedback learning, pattern recognition, and adaptive matching
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app import db
from app.models import Organization, Grant, Analytics, User
from app.services.ai_reasoning_engine import AIReasoningEngine

logger = logging.getLogger(__name__)

class AILearningSystem:
    """
    Advanced learning system that:
    - Learns from user feedback and decisions
    - Analyzes historical success patterns
    - Adapts matching algorithms based on outcomes
    - Improves organization-specific recommendations
    """
    
    def __init__(self):
        self.reasoning_engine = AIReasoningEngine()
        self.learning_cache = {}
        self.pattern_library = {}
        self.success_factors = {}
        
    def record_user_decision(self, user_id: int, grant_id: int, decision: str, 
                            reasoning: Dict = None) -> bool:
        """
        Record user decision on a grant recommendation
        
        Args:
            user_id: User making the decision
            grant_id: Grant being decided on
            decision: 'applied', 'saved', 'rejected', 'ignored'
            reasoning: Optional reasoning provided by user
        """
        try:
            # Create analytics entry
            analytics_entry = Analytics()
            analytics_entry.event_type = 'grant_decision'
            analytics_entry.event_data = {
                'user_id': user_id,
                'grant_id': grant_id,
                'decision': decision,
                'reasoning': reasoning,
                'timestamp': datetime.utcnow().isoformat()
            }
            analytics_entry.created_at = datetime.utcnow()
            
            db.session.add(analytics_entry)
            db.session.commit()
            
            # Update learning patterns
            self._update_decision_patterns(user_id, grant_id, decision)
            
            logger.info(f"Recorded decision: {decision} for grant {grant_id} by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording user decision: {e}")
            db.session.rollback()
            return False
    
    def record_application_outcome(self, org_id: int, grant_id: int, 
                                  outcome: str, details: Dict = None) -> bool:
        """
        Record the outcome of a grant application
        
        Args:
            org_id: Organization that applied
            grant_id: Grant applied for
            outcome: 'awarded', 'rejected', 'pending', 'withdrawn'
            details: Additional details about the outcome
        """
        try:
            # Create outcome record
            analytics_entry = Analytics()
            analytics_entry.event_type = 'application_outcome'
            analytics_entry.event_data = {
                'org_id': org_id,
                'grant_id': grant_id,
                'outcome': outcome,
                'details': details,
                'timestamp': datetime.utcnow().isoformat()
            }
            analytics_entry.created_at = datetime.utcnow()
            
            db.session.add(analytics_entry)
            db.session.commit()
            
            # Learn from outcome
            self._learn_from_outcome(org_id, grant_id, outcome, details)
            
            # Update organization success metrics
            self._update_org_success_metrics(org_id, outcome)
            
            logger.info(f"Recorded outcome: {outcome} for grant {grant_id}, org {org_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording application outcome: {e}")
            db.session.rollback()
            return False
    
    def get_personalized_insights(self, org_id: int) -> Dict:
        """
        Generate personalized insights based on organization's history
        
        Returns:
            Dict containing insights, recommendations, and success factors
        """
        try:
            org = Organization.query.get(org_id)
            if not org:
                return {'error': 'Organization not found'}
            
            # Analyze historical patterns
            success_patterns = self._analyze_success_patterns(org_id)
            failure_patterns = self._analyze_failure_patterns(org_id)
            
            # Generate insights
            insights = {
                'success_rate': self._calculate_success_rate(org_id),
                'strongest_areas': self._identify_strong_areas(org_id, success_patterns),
                'improvement_areas': self._identify_improvement_areas(org_id, failure_patterns),
                'recommended_focus': self._recommend_focus_areas(org_id),
                'optimal_grant_size': self._determine_optimal_grant_size(org_id),
                'best_funders': self._identify_best_funders(org_id),
                'timing_insights': self._analyze_timing_patterns(org_id),
                'competitive_advantage': self._identify_competitive_advantages(org)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating personalized insights: {e}")
            return {'error': str(e)}
    
    def improve_matching_algorithm(self, org_id: int) -> Dict:
        """
        Improve matching algorithm based on organization's specific patterns
        
        Returns:
            Updated matching parameters and weights
        """
        try:
            # Get organization's historical data
            history = self._get_org_history(org_id)
            
            # Analyze what factors led to success
            success_factors = self._extract_success_factors(history)
            
            # Adjust weights based on patterns
            updated_weights = {
                'mission_alignment': 0.30,  # Default
                'capacity_fit': 0.20,
                'geographic_match': 0.20,
                'financial_alignment': 0.20,
                'historical_success': 0.10
            }
            
            # Adjust based on what works for this org
            if success_factors.get('mission_critical', False):
                updated_weights['mission_alignment'] = 0.40
                updated_weights['capacity_fit'] = 0.15
            
            if success_factors.get('location_flexible', False):
                updated_weights['geographic_match'] = 0.10
                updated_weights['financial_alignment'] = 0.30
            
            # Store updated weights for future use
            self._store_org_weights(org_id, updated_weights)
            
            return {
                'weights': updated_weights,
                'factors': success_factors,
                'confidence': self._calculate_confidence(history)
            }
            
        except Exception as e:
            logger.error(f"Error improving matching algorithm: {e}")
            return {}
    
    def _update_decision_patterns(self, user_id: int, grant_id: int, decision: str):
        """Update patterns based on user decisions"""
        try:
            # Get grant details
            grant = Grant.query.get(grant_id)
            if not grant:
                return
            
            # Extract features from grant
            features = {
                'amount_range': grant.amount_max,
                'focus_area': grant.focus_area,
                'funder_type': grant.funder_type,
                'deadline_days': (grant.deadline - datetime.utcnow()).days if grant.deadline else None
            }
            
            # Update pattern library
            pattern_key = f"user_{user_id}_patterns"
            if pattern_key not in self.pattern_library:
                self.pattern_library[pattern_key] = {
                    'applied': [],
                    'saved': [],
                    'rejected': []
                }
            
            if decision in self.pattern_library[pattern_key]:
                self.pattern_library[pattern_key][decision].append(features)
            
        except Exception as e:
            logger.error(f"Error updating decision patterns: {e}")
    
    def _learn_from_outcome(self, org_id: int, grant_id: int, outcome: str, details: Dict):
        """Learn from application outcomes"""
        try:
            # Get grant and org details
            grant = Grant.query.get(grant_id)
            org = Organization.query.get(org_id)
            
            if not grant or not org:
                return
            
            # Extract learning features
            learning_data = {
                'outcome': outcome,
                'grant_features': {
                    'amount': grant.amount_max,
                    'focus_area': grant.focus_area,
                    'funder': grant.funder
                },
                'org_features': {
                    'budget': org.annual_budget_range,
                    'staff_size': org.staff_size,
                    'focus_areas': org.primary_focus_areas
                },
                'match_score': details.get('original_match_score') if details else None
            }
            
            # Update success factors
            if outcome == 'awarded':
                self._update_success_factors(org_id, learning_data)
            elif outcome == 'rejected':
                self._update_failure_factors(org_id, learning_data)
            
            # Adjust reasoning engine based on outcome
            self.reasoning_engine.learn_from_outcome(org_id, grant_id, outcome, learning_data)
            
        except Exception as e:
            logger.error(f"Error learning from outcome: {e}")
    
    def _update_org_success_metrics(self, org_id: int, outcome: str):
        """Update organization's success metrics"""
        try:
            org = Organization.query.get(org_id)
            if not org:
                return
            
            # Get all outcomes for this org
            outcomes = Analytics.query.filter(
                Analytics.event_type == 'application_outcome',
                Analytics.event_data['org_id'].astext == str(org_id)
            ).all()
            
            # Calculate success rate
            total = len(outcomes)
            if total > 0:
                awarded = sum(1 for o in outcomes 
                            if o.event_data.get('outcome') == 'awarded')
                org.grant_success_rate = awarded / total
                db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating org success metrics: {e}")
    
    def _analyze_success_patterns(self, org_id: int) -> Dict:
        """Analyze patterns in successful applications"""
        try:
            # Get successful applications
            successes = Analytics.query.filter(
                Analytics.event_type == 'application_outcome',
                Analytics.event_data['org_id'].astext == str(org_id),
                Analytics.event_data['outcome'].astext == 'awarded'
            ).all()
            
            patterns = {
                'common_focus_areas': {},
                'amount_ranges': [],
                'funders': {},
                'timing': []
            }
            
            for success in successes:
                data = success.event_data
                
                # Analyze focus areas
                if 'grant_features' in data:
                    focus = data['grant_features'].get('focus_area')
                    if focus:
                        patterns['common_focus_areas'][focus] = \
                            patterns['common_focus_areas'].get(focus, 0) + 1
                
                # Analyze amounts
                if 'grant_features' in data:
                    amount = data['grant_features'].get('amount')
                    if amount:
                        patterns['amount_ranges'].append(amount)
                
                # Analyze funders
                if 'grant_features' in data:
                    funder = data['grant_features'].get('funder')
                    if funder:
                        patterns['funders'][funder] = patterns['funders'].get(funder, 0) + 1
                
                # Analyze timing
                if success.created_at:
                    patterns['timing'].append(success.created_at.month)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing success patterns: {e}")
            return {}
    
    def _analyze_failure_patterns(self, org_id: int) -> Dict:
        """Analyze patterns in failed applications"""
        try:
            # Get failed applications
            failures = Analytics.query.filter(
                Analytics.event_type == 'application_outcome',
                Analytics.event_data['org_id'].astext == str(org_id),
                Analytics.event_data['outcome'].astext == 'rejected'
            ).all()
            
            patterns = {
                'common_issues': [],
                'mismatch_areas': {},
                'amount_misalignment': []
            }
            
            for failure in failures:
                data = failure.event_data
                
                # Extract failure reasons if available
                if 'details' in data and data['details']:
                    if 'reason' in data['details']:
                        patterns['common_issues'].append(data['details']['reason'])
                
                # Analyze mismatches
                if 'grant_features' in data:
                    focus = data['grant_features'].get('focus_area')
                    if focus:
                        patterns['mismatch_areas'][focus] = \
                            patterns['mismatch_areas'].get(focus, 0) + 1
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing failure patterns: {e}")
            return {}
    
    def _calculate_success_rate(self, org_id: int) -> float:
        """Calculate organization's overall success rate"""
        try:
            outcomes = Analytics.query.filter(
                Analytics.event_type == 'application_outcome',
                Analytics.event_data['org_id'].astext == str(org_id)
            ).all()
            
            if not outcomes:
                return 0.0
            
            awarded = sum(1 for o in outcomes 
                        if o.event_data.get('outcome') == 'awarded')
            
            return awarded / len(outcomes)
            
        except Exception as e:
            logger.error(f"Error calculating success rate: {e}")
            return 0.0
    
    def _identify_strong_areas(self, org_id: int, patterns: Dict) -> List[str]:
        """Identify organization's strongest areas"""
        strong_areas = []
        
        # Find most successful focus areas
        if patterns.get('common_focus_areas'):
            sorted_areas = sorted(patterns['common_focus_areas'].items(), 
                                key=lambda x: x[1], reverse=True)
            strong_areas.extend([area for area, _ in sorted_areas[:3]])
        
        return strong_areas
    
    def _identify_improvement_areas(self, org_id: int, patterns: Dict) -> List[str]:
        """Identify areas needing improvement"""
        improvements = []
        
        # Analyze common failure reasons
        if patterns.get('common_issues'):
            issue_counts = {}
            for issue in patterns['common_issues']:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            # Get top issues
            sorted_issues = sorted(issue_counts.items(), 
                                 key=lambda x: x[1], reverse=True)
            improvements.extend([issue for issue, _ in sorted_issues[:3]])
        
        return improvements
    
    def _recommend_focus_areas(self, org_id: int) -> List[str]:
        """Recommend focus areas based on success patterns"""
        try:
            patterns = self._analyze_success_patterns(org_id)
            
            # Get organization's current focus areas
            org = Organization.query.get(org_id)
            if not org:
                return []
            
            current_areas = set(org.primary_focus_areas or [])
            successful_areas = set(patterns.get('common_focus_areas', {}).keys())
            
            # Recommend intersection of current and successful
            recommended = list(current_areas.intersection(successful_areas))
            
            # Add new promising areas
            for area in successful_areas - current_areas:
                if patterns['common_focus_areas'][area] >= 2:  # At least 2 successes
                    recommended.append(area)
            
            return recommended[:5]  # Top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error recommending focus areas: {e}")
            return []
    
    def _determine_optimal_grant_size(self, org_id: int) -> str:
        """Determine optimal grant size based on history"""
        try:
            patterns = self._analyze_success_patterns(org_id)
            amounts = patterns.get('amount_ranges', [])
            
            if not amounts:
                return "$10k-50k"  # Default
            
            # Calculate average successful amount
            avg_amount = sum(amounts) / len(amounts)
            
            if avg_amount < 10000:
                return "<$10k"
            elif avg_amount < 25000:
                return "$10k-25k"
            elif avg_amount < 50000:
                return "$25k-50k"
            elif avg_amount < 100000:
                return "$50k-100k"
            elif avg_amount < 500000:
                return "$100k-500k"
            else:
                return "$500k+"
                
        except Exception as e:
            logger.error(f"Error determining optimal grant size: {e}")
            return "$10k-50k"
    
    def _identify_best_funders(self, org_id: int) -> List[str]:
        """Identify best funders based on success history"""
        try:
            patterns = self._analyze_success_patterns(org_id)
            funders = patterns.get('funders', {})
            
            if not funders:
                return []
            
            # Sort by success count
            sorted_funders = sorted(funders.items(), 
                                  key=lambda x: x[1], reverse=True)
            
            return [funder for funder, _ in sorted_funders[:5]]
            
        except Exception as e:
            logger.error(f"Error identifying best funders: {e}")
            return []
    
    def _analyze_timing_patterns(self, org_id: int) -> Dict:
        """Analyze timing patterns for applications"""
        try:
            patterns = self._analyze_success_patterns(org_id)
            timing = patterns.get('timing', [])
            
            if not timing:
                return {'best_months': [], 'recommendation': 'No timing data available'}
            
            # Count successes by month
            month_counts = {}
            for month in timing:
                month_counts[month] = month_counts.get(month, 0) + 1
            
            # Find best months
            sorted_months = sorted(month_counts.items(), 
                                 key=lambda x: x[1], reverse=True)
            best_months = [month for month, _ in sorted_months[:3]]
            
            # Generate recommendation
            month_names = {
                1: 'January', 2: 'February', 3: 'March', 4: 'April',
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            }
            
            best_month_names = [month_names[m] for m in best_months]
            
            return {
                'best_months': best_month_names,
                'recommendation': f"Historical success highest in: {', '.join(best_month_names)}"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing timing patterns: {e}")
            return {}
    
    def _identify_competitive_advantages(self, org: Organization) -> List[str]:
        """Identify organization's competitive advantages"""
        advantages = []
        
        try:
            # Check special characteristics
            if org.faith_based:
                advantages.append("Faith-based organization with values alignment")
            if org.minority_led:
                advantages.append("Minority-led organization promoting diversity")
            if org.woman_led:
                advantages.append("Woman-led organization advancing gender equity")
            if org.veteran_led:
                advantages.append("Veteran-led organization with military experience")
            
            # Check unique capabilities
            if org.unique_capabilities:
                advantages.append(f"Unique strength: {org.unique_capabilities[:100]}")
            
            # Check track record
            if org.grant_success_rate and org.grant_success_rate > 0.5:
                advantages.append(f"Strong track record: {org.grant_success_rate*100:.0f}% success rate")
            
            # Check partnerships
            if org.partnership_interests:
                advantages.append("Open to collaborative partnerships")
            
            return advantages
            
        except Exception as e:
            logger.error(f"Error identifying competitive advantages: {e}")
            return []
    
    def _get_org_history(self, org_id: int) -> List[Dict]:
        """Get organization's complete history"""
        try:
            history = []
            
            # Get all analytics events for this org
            events = Analytics.query.filter(
                db.or_(
                    Analytics.event_data['org_id'].astext == str(org_id),
                    Analytics.event_type.in_(['grant_decision', 'application_outcome'])
                )
            ).order_by(Analytics.created_at.desc()).limit(100).all()
            
            for event in events:
                history.append({
                    'type': event.event_type,
                    'data': event.event_data,
                    'timestamp': event.created_at
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting org history: {e}")
            return []
    
    def _extract_success_factors(self, history: List[Dict]) -> Dict:
        """Extract factors that lead to success"""
        factors = {
            'mission_critical': False,
            'location_flexible': False,
            'amount_sensitive': False,
            'timing_important': False
        }
        
        try:
            # Analyze patterns in history
            successes = [h for h in history 
                        if h['type'] == 'application_outcome' 
                        and h['data'].get('outcome') == 'awarded']
            
            if len(successes) >= 3:
                # Check if mission alignment is critical
                mission_scores = []
                for s in successes:
                    if 'match_score' in s['data']:
                        mission_scores.append(s['data']['match_score'])
                
                if mission_scores and sum(mission_scores)/len(mission_scores) > 80:
                    factors['mission_critical'] = True
                
                # Check if location matters
                locations = set()
                for s in successes:
                    if 'grant_features' in s['data']:
                        loc = s['data']['grant_features'].get('location')
                        if loc:
                            locations.add(loc)
                
                if len(locations) > 3:  # Success across multiple locations
                    factors['location_flexible'] = True
            
            return factors
            
        except Exception as e:
            logger.error(f"Error extracting success factors: {e}")
            return factors
    
    def _calculate_confidence(self, history: List[Dict]) -> str:
        """Calculate confidence level based on data availability"""
        if len(history) >= 50:
            return 'high'
        elif len(history) >= 20:
            return 'medium'
        else:
            return 'low'
    
    def _store_org_weights(self, org_id: int, weights: Dict):
        """Store organization-specific weights for future use"""
        try:
            # Store in cache for quick access
            self.learning_cache[f"org_{org_id}_weights"] = {
                'weights': weights,
                'updated': datetime.utcnow().isoformat()
            }
            
            # Also persist to database
            analytics_entry = Analytics()
            analytics_entry.event_type = 'weight_update'
            analytics_entry.event_data = {
                'org_id': org_id,
                'weights': weights,
                'timestamp': datetime.utcnow().isoformat()
            }
            analytics_entry.created_at = datetime.utcnow()
            
            db.session.add(analytics_entry)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error storing org weights: {e}")
            db.session.rollback()
    
    def _update_success_factors(self, org_id: int, learning_data: Dict):
        """Update success factors based on new success"""
        key = f"org_{org_id}_success"
        
        if key not in self.success_factors:
            self.success_factors[key] = []
        
        self.success_factors[key].append(learning_data)
        
        # Keep only recent data (last 50 successes)
        if len(self.success_factors[key]) > 50:
            self.success_factors[key] = self.success_factors[key][-50:]
    
    def _update_failure_factors(self, org_id: int, learning_data: Dict):
        """Update failure factors based on new failure"""
        key = f"org_{org_id}_failure"
        
        if key not in self.success_factors:
            self.success_factors[key] = []
        
        self.success_factors[key].append(learning_data)
        
        # Keep only recent data (last 50 failures)
        if len(self.success_factors[key]) > 50:
            self.success_factors[key] = self.success_factors[key][-50:]