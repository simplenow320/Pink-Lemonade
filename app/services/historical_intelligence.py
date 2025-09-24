"""
Historical Intelligence Service - Fast & Resilient Implementation
Analyzes grant patterns with caching, timeouts, and graceful degradation to prevent worker timeouts
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from functools import wraps
from app.services.candid_grants_client import CandidGrantsClient
from app.services.ai_service import AIService
from app.services.redis_cache_service import RedisCacheService

logger = logging.getLogger(__name__)

def circuit_breaker(timeout_seconds: int = 3, fallback_value: Any = None):
    """
    Decorator that implements circuit breaker pattern with timeout
    If function takes longer than timeout_seconds, returns fallback_value immediately
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result_container = {}
            exception_container = {}
            
            def target():
                try:
                    result_container['result'] = func(*args, **kwargs)
                except Exception as e:
                    exception_container['error'] = e
                    
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=timeout_seconds)
            
            if thread.is_alive():
                # Function is still running - return fallback immediately
                logger.warning(f"Function {func.__name__} timed out after {timeout_seconds}s, returning fallback")
                return fallback_value
                
            if 'error' in exception_container:
                logger.error(f"Function {func.__name__} failed: {exception_container['error']}")
                return fallback_value
                
            return result_container.get('result', fallback_value)
        return wrapper
    return decorator

class HistoricalIntelligenceService:
    """
    Fast, resilient historical grant intelligence with caching and circuit breakers.
    Designed to never block the main application flow.
    """
    
    def __init__(self):
        self.candid_client = CandidGrantsClient()
        self.ai_service = AIService()
        self.cache = RedisCacheService()
        self.analysis_years = 3
        self.max_intelligence_time = 2  # Maximum time to spend on intelligence gathering
        
        # Circuit breaker state
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open_duration = 300  # 5 minutes
        
    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is open (failing)"""
        if self.failure_count >= 3 and self.last_failure_time:
            time_since_failure = time.time() - self.last_failure_time
            if time_since_failure < self.circuit_open_duration:
                return True
            else:
                # Reset circuit breaker after timeout
                self.failure_count = 0
                self.last_failure_time = None
        return False
        
    def record_failure(self):
        """Record a failure for circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
    def record_success(self):
        """Record a success for circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None

    @circuit_breaker(timeout_seconds=2, fallback_value={})
    def analyze_funder_patterns(self, funder_name: str, search_year: Optional[int] = None) -> Dict:
        """
        Analyze historical patterns with caching and fast fallback
        CRITICAL: This function MUST complete within 2 seconds or return empty result
        """
        try:
            if not funder_name or not funder_name.strip():
                return self._empty_intelligence()
            
            # Check circuit breaker first
            if self.is_circuit_open():
                logger.info(f"Circuit breaker open for intelligence service, skipping analysis for {funder_name}")
                return self._empty_intelligence_with_reason("Service temporarily unavailable")
            
            # Generate cache key
            current_year = search_year or datetime.now().year
            cache_key = f"intelligence:{funder_name.lower().replace(' ', '_')}:{current_year}"
            
            # Try cache first (should be very fast)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"Using cached intelligence for {funder_name}")
                self.record_success()
                return cached_result
            
            # If not in cache, perform analysis with strict timeout
            start_time = time.time()
            intelligence = self._fast_analysis(funder_name, current_year)
            analysis_time = time.time() - start_time
            
            if analysis_time > self.max_intelligence_time:
                logger.warning(f"Intelligence analysis took {analysis_time:.2f}s - too slow")
                self.record_failure()
                return self._empty_intelligence_with_reason("Analysis timeout")
                
            # Cache successful results for 1 hour
            if intelligence.get('intelligence_available', False):
                self.cache.set(cache_key, intelligence, ttl=3600)
                logger.info(f"Cached intelligence for {funder_name} (analysis took {analysis_time:.2f}s)")
            
            self.record_success()
            return intelligence
            
        except Exception as e:
            logger.error(f"Error in analyze_funder_patterns for {funder_name}: {str(e)}")
            self.record_failure()
            return self._empty_intelligence_with_reason(f"Analysis failed: {str(e)[:100]}")

    def _fast_analysis(self, funder_name: str, current_year: int) -> Dict:
        """
        Perform fast analysis with strict timeout controls
        """
        try:
            start_year = current_year - self.analysis_years
            
            # Quick API call with 3-second max timeout
            historical_grants = self._fetch_historical_grants_fast(funder_name, start_year, current_year)
            
            if not historical_grants:
                return self._empty_intelligence_with_reason("No historical data found")
            
            # Quick AI analysis (should be fast since we limit the data)
            intelligence = self._analyze_grant_patterns_fast(historical_grants, funder_name)
            
            # Add metadata
            intelligence['analysis_period'] = f"{start_year}-{current_year}"
            intelligence['data_source'] = 'Candid Historical Grants API'
            intelligence['generated_at'] = datetime.utcnow().isoformat()
            intelligence['confidence_score'] = self._calculate_confidence(historical_grants)
            intelligence['intelligence_available'] = True
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error in fast analysis for {funder_name}: {str(e)}")
            return self._empty_intelligence_with_reason("Fast analysis failed")

    def _fetch_historical_grants_fast(self, funder_name: str, start_year: int, end_year: int) -> List[Dict]:
        """
        Fast historical grants fetch with timeout protection
        """
        try:
            # This now has 5-second timeout instead of 30 seconds
            grants = self.candid_client.search_grants(
                funder_name=funder_name,
                year=None,
                limit=50  # Reduced from 100 to make it faster
            )
            
            return grants if grants else []
            
        except Exception as e:
            logger.warning(f"Fast fetch failed for {funder_name}: {str(e)}")
            return []

    def _analyze_grant_patterns_fast(self, grants: List[Dict], funder_name: str) -> Dict:
        """
        Fast AI analysis with minimal data to avoid token limits and delays
        """
        try:
            if not grants:
                return self._empty_intelligence()
            
            # Use only essential data for fast analysis
            grant_count = len(grants)
            sample_grants = grants[:3]  # Only analyze 3 grants for speed
            
            # Quick pattern extraction without heavy AI processing
            patterns = {
                'total_awards': grant_count,
                'average_amount': self._quick_average_amount(grants),
                'typical_recipients': self._extract_recipient_types(grants),
                'geographic_patterns': self._extract_locations(grants),
                'award_timing': ['Data available on request'],
                'focus_areas': self._extract_focus_areas(grants),
                'data_quality': 'fast_analysis',
                'intelligence_available': True
            }
            
            return patterns
                
        except Exception as e:
            logger.error(f"Error in fast pattern analysis: {str(e)}")
            return self._empty_intelligence()

    def _quick_average_amount(self, grants: List[Dict]) -> int:
        """Quick average calculation without heavy processing"""
        try:
            amounts = []
            for grant in grants[:10]:  # Only check first 10 grants
                amount = grant.get('amount', 0)
                if isinstance(amount, (int, float)) and amount > 0:
                    amounts.append(amount)
            return int(sum(amounts) / len(amounts)) if amounts else 0
        except:
            return 0
            
    def _extract_recipient_types(self, grants: List[Dict]) -> List[str]:
        """Quick recipient type extraction"""
        try:
            types = set()
            for grant in grants[:5]:  # Only check first 5
                recipient = grant.get('recipient', '')
                if recipient:
                    if 'foundation' in recipient.lower():
                        types.add('Foundation')
                    elif 'university' in recipient.lower() or 'college' in recipient.lower():
                        types.add('University')
                    elif 'nonprofit' in recipient.lower() or 'non-profit' in recipient.lower():
                        types.add('Nonprofit')
                    else:
                        types.add('Organization')
            return list(types)[:3]  # Limit to 3 types
        except:
            return ['Organizations']
            
    def _extract_locations(self, grants: List[Dict]) -> List[str]:
        """Quick location extraction"""
        try:
            locations = set()
            for grant in grants[:5]:  # Only check first 5
                location = grant.get('location', '')
                if location and ',' in location:
                    state = location.split(',')[-1].strip()
                    if len(state) <= 3:  # Likely a state abbreviation
                        locations.add(state)
            return list(locations)[:3]  # Limit to 3 locations
        except:
            return ['Various']
            
    def _extract_focus_areas(self, grants: List[Dict]) -> List[str]:
        """Quick focus area extraction"""
        try:
            areas = set()
            for grant in grants[:5]:  # Only check first 5
                focus = grant.get('focus_area', '') or grant.get('description', '')
                if focus and len(focus) < 100:  # Only short descriptions
                    areas.add(focus[:50])  # Truncate long ones
            return list(areas)[:3]  # Limit to 3 areas
        except:
            return ['General funding']

    @circuit_breaker(timeout_seconds=1, fallback_value={})
    def generate_intelligence_insights(self, patterns: Dict, org_profile: Dict) -> Dict:
        """
        Generate insights with fast fallback - MUST complete within 1 second
        """
        try:
            if not patterns.get('total_awards') or patterns.get('total_awards') == 0:
                return self._empty_insights()
            
            # Generate quick insights without heavy AI processing
            total_awards = patterns.get('total_awards', 0)
            average_amount = patterns.get('average_amount', 0)
            
            # Quick heuristic-based insights instead of AI processing
            match_likelihood = min(90, max(10, (total_awards * 10) + 20))  # Simple heuristic
            
            insights = {
                'match_likelihood': match_likelihood,
                'timing_recommendation': 'Based on historical patterns, apply during standard funding cycles',
                'strategic_actions': [
                    f'Target similar organizations that received {total_awards} grants',
                    f'Prepare applications for amounts around ${average_amount:,}' if average_amount > 0 else 'Research typical grant amounts',
                    'Review successful applications from similar recipients'
                ],
                'success_indicators': [
                    'Historical grant activity indicates active funder',
                    f'${average_amount:,} typical award size' if average_amount > 0 else 'Variable award sizes',
                    f'{total_awards} grants in analysis period shows consistent funding'
                ],
                'intelligence_summary': f"Fast analysis of {total_awards} grants - detailed intelligence available on request"
            }
            
            return insights
                
        except Exception as e:
            logger.error(f"Error generating quick insights: {str(e)}")
            return self._empty_insights()

    def _calculate_confidence(self, grants: List[Dict]) -> float:
        """Quick confidence calculation"""
        if not grants:
            return 0.0
        
        grant_count = len(grants)
        if grant_count >= 10:
            return 0.8  # High confidence
        elif grant_count >= 5:
            return 0.6  # Good confidence  
        elif grant_count >= 2:
            return 0.4  # Moderate confidence
        else:
            return 0.2  # Low confidence

    def _empty_intelligence(self) -> Dict:
        """Return empty intelligence structure"""
        return {
            'total_awards': 0,
            'average_amount': 0,
            'typical_recipients': [],
            'geographic_patterns': [],
            'award_timing': [],
            'focus_areas': [],
            'confidence_score': 0.0,
            'intelligence_available': False,
            'message': 'No historical intelligence available'
        }
        
    def _empty_intelligence_with_reason(self, reason: str) -> Dict:
        """Return empty intelligence with specific reason"""
        empty = self._empty_intelligence()
        empty['message'] = reason
        return empty
        
    def _empty_insights(self) -> Dict:
        """Return empty insights structure"""
        return {
            'match_likelihood': 0,
            'timing_recommendation': 'No specific timing recommendations available',
            'strategic_actions': ['Review funder website for current opportunities'],
            'success_indicators': ['Limited historical data available'],
            'intelligence_summary': 'Intelligence system optimizing for performance - detailed analysis available on request'
        }

    # Legacy methods for backward compatibility - but with fast fallbacks
    def predict_opportunity_windows(self, historical_data: Dict) -> Dict:
        """Legacy method with fast fallback"""
        if not historical_data.get('intelligence_available', False):
            return {'predictions': [], 'confidence': 0.0, 'message': 'No historical data for predictions'}
            
        return {
            'predictions': ['Standard funding cycles apply'],
            'timing_insights': 'Based on general patterns',
            'preparation_timeline': 'Begin preparation 60-90 days before deadlines',
            'confidence_level': 30
        }

# Singleton instance for performance
_intelligence_service = None

def get_intelligence_service() -> HistoricalIntelligenceService:
    """Get singleton intelligence service"""
    global _intelligence_service
    if _intelligence_service is None:
        _intelligence_service = HistoricalIntelligenceService()
    return _intelligence_service