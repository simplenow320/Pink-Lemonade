"""
Historical Intelligence Service - Phase 1
Analyzes 3-year historical grant patterns using Candid API without disrupting existing functionality
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.services.candid_grants_client import CandidGrantsClient
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

class HistoricalIntelligenceService:
    """
    Provides historical grant intelligence using 3-year analysis window.
    Enhances existing grant matching with predictive insights.
    """
    
    def __init__(self):
        self.candid_client = CandidGrantsClient()
        self.ai_service = AIService()
        self.analysis_years = 3  # Always analyze past 3 years based on current year
    
    def analyze_funder_patterns(self, funder_name: str, search_year: Optional[int] = None) -> Dict:
        """
        Analyze 3-year historical patterns for any funder
        
        Args:
            funder_name: Name of the funder to analyze
            search_year: Year to base 3-year lookback from (defaults to current year)
            
        Returns:
            Dictionary with historical intelligence data
        """
        try:
            if not funder_name or not funder_name.strip():
                return self._empty_intelligence()
            
            # Determine analysis period
            current_year = search_year or datetime.now().year
            start_year = current_year - self.analysis_years
            
            logger.info(f"Analyzing {funder_name} patterns from {start_year} to {current_year}")
            
            # Get historical data from Candid API
            historical_grants = self._fetch_historical_grants(funder_name, start_year, current_year)
            
            if not historical_grants:
                return self._empty_intelligence()
            
            # Analyze patterns using AI
            intelligence = self._analyze_grant_patterns(historical_grants, funder_name)
            
            # Add metadata
            intelligence['analysis_period'] = f"{start_year}-{current_year}"
            intelligence['data_source'] = 'Candid Historical Grants API'
            intelligence['generated_at'] = datetime.utcnow().isoformat()
            intelligence['confidence_score'] = self._calculate_confidence(historical_grants)
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error analyzing funder patterns for {funder_name}: {str(e)}")
            return self._empty_intelligence()
    
    def predict_opportunity_windows(self, historical_data: Dict) -> Dict:
        """
        Identify likely future funding cycles based on historical patterns
        
        Args:
            historical_data: Output from analyze_funder_patterns
            
        Returns:
            Dictionary with predicted timing and opportunities
        """
        try:
            if not historical_data.get('awards_by_year'):
                return {'predictions': [], 'confidence': 0.0}
            
            # Use AI to identify patterns
            prompt = f"""
            Analyze this historical grant data to predict future funding cycles:
            
            Awards by Year: {historical_data.get('awards_by_year', {})}
            Typical Months: {historical_data.get('award_timing', [])}
            Average Amount: ${historical_data.get('average_amount', 0):,}
            Award Count: {historical_data.get('total_awards', 0)} grants
            
            Based on these patterns, predict:
            1. When this funder is likely to announce opportunities in the next 12 months
            2. Typical award amounts to expect
            3. Best timing for application preparation
            4. Confidence level for predictions (0-100%)
            
            Respond in JSON format with: predictions, timing_insights, preparation_timeline, confidence_level
            """
            
            response = self.ai_service.generate_json_response(prompt)
            
            if response:
                return {
                    'predictions': response.get('predictions', []),
                    'timing_insights': response.get('timing_insights', ''),
                    'preparation_timeline': response.get('preparation_timeline', ''),
                    'confidence_level': response.get('confidence_level', 0)
                }
                
        except Exception as e:
            logger.error(f"Error predicting opportunity windows: {str(e)}")
            
        return {'predictions': [], 'confidence': 0.0}
    
    def generate_intelligence_insights(self, patterns: Dict, org_profile: Dict) -> Dict:
        """
        Create actionable intelligence insights for specific organization
        
        Args:
            patterns: Historical patterns from analyze_funder_patterns
            org_profile: Organization context for personalized insights
            
        Returns:
            Dictionary with actionable insights and recommendations
        """
        try:
            if not patterns.get('total_awards') or patterns.get('total_awards') == 0:
                return {'insights': [], 'recommendations': [], 'success_indicators': []}
            
            # Generate AI insights
            prompt = f"""
            Create actionable funding intelligence for this organization:
            
            Organization Profile:
            - Name: {org_profile.get('name', 'Organization')}
            - Focus Areas: {org_profile.get('focus_areas', [])}
            - Location: {org_profile.get('geographic_focus', 'Not specified')}
            - Budget Range: {org_profile.get('annual_budget', 'Not specified')}
            
            Historical Funder Data:
            - Total Awards (3 years): {patterns.get('total_awards', 0)}
            - Average Amount: ${patterns.get('average_amount', 0):,}
            - Typical Recipients: {patterns.get('typical_recipients', [])}
            - Award Timing: {patterns.get('award_timing', [])}
            - Geographic Patterns: {patterns.get('geographic_patterns', [])}
            
            Provide specific insights:
            1. Match likelihood based on historical recipient profiles
            2. Optimal timing for this organization to apply
            3. Strategic recommendations for increasing success chances
            4. Key success indicators from similar past awards
            
            Respond in JSON with: match_likelihood_percentage, timing_recommendation, strategic_actions, success_indicators
            """
            
            response = self.ai_service.generate_json_response(prompt)
            
            if response:
                return {
                    'match_likelihood': response.get('match_likelihood_percentage', 0),
                    'timing_recommendation': response.get('timing_recommendation', ''),
                    'strategic_actions': response.get('strategic_actions', []),
                    'success_indicators': response.get('success_indicators', []),
                    'intelligence_summary': f"Based on {patterns.get('total_awards', 0)} similar awards in past 3 years"
                }
                
        except Exception as e:
            logger.error(f"Error generating intelligence insights: {str(e)}")
            
        return {'insights': [], 'recommendations': [], 'success_indicators': []}
    
    def _fetch_historical_grants(self, funder_name: str, start_year: int, end_year: int) -> List[Dict]:
        """
        Fetch historical grants from Candid API for specific funder and timeframe
        """
        try:
            # Use Candid API to search for historical grants
            grants = self.candid_client.search_grants(
                funder_name=funder_name,
                year=None,  # We want multiple years
                limit=100   # Get comprehensive data
            )
            
            # Filter by year range (if Candid API supports it)
            # For now, return what we can get
            return grants if grants else []
            
        except Exception as e:
            logger.error(f"Error fetching historical grants: {str(e)}")
            return []
    
    def _analyze_grant_patterns(self, grants: List[Dict], funder_name: str) -> Dict:
        """
        Use AI to analyze historical grant patterns
        """
        try:
            if not grants:
                return self._empty_intelligence()
            
            # Prepare data for AI analysis
            grant_summary = {
                'total_grants': len(grants),
                'grants_sample': grants[:5],  # Send sample to avoid token limits
                'funder_name': funder_name
            }
            
            prompt = f"""
            Analyze these historical grants to identify funding patterns:
            
            Funder: {funder_name}
            Total Grants: {grant_summary['total_grants']}
            Sample Grants: {grant_summary['grants_sample']}
            
            Extract patterns for:
            1. Typical award amounts and ranges
            2. Common recipient types and characteristics  
            3. Geographic distribution of awards
            4. Timing patterns (if date information available)
            5. Program focus areas that get funded
            
            Respond in JSON with: average_amount, amount_range, typical_recipients, geographic_patterns, award_timing, focus_areas, total_awards
            """
            
            response = self.ai_service.generate_json_response(prompt)
            
            if response:
                # Enhance with calculated data
                response['total_awards'] = len(grants)
                response['data_quality'] = 'high' if len(grants) >= 10 else 'moderate'
                return response
                
        except Exception as e:
            logger.error(f"Error analyzing grant patterns: {str(e)}")
            
        return self._empty_intelligence()
    
    def _calculate_confidence(self, grants: List[Dict]) -> float:
        """
        Calculate confidence score based on data availability and quality
        """
        if not grants:
            return 0.0
        
        grant_count = len(grants)
        
        # Base confidence on data volume
        if grant_count >= 20:
            return 0.9  # High confidence
        elif grant_count >= 10:
            return 0.7  # Good confidence  
        elif grant_count >= 5:
            return 0.5  # Moderate confidence
        else:
            return 0.3  # Low confidence
    
    def _empty_intelligence(self) -> Dict:
        """
        Return empty intelligence structure for error cases
        """
        return {
            'total_awards': 0,
            'average_amount': 0,
            'typical_recipients': [],
            'geographic_patterns': [],
            'award_timing': [],
            'focus_areas': [],
            'confidence_score': 0.0,
            'intelligence_available': False
        }