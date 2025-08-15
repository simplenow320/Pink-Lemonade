"""
PHASE 1: World-Class Grant Matching Engine
Multi-factor scoring with real data from all 5 sources
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import all data source clients
from app.services.federal_register_client import FederalRegisterClient
from app.services.usaspending_client import USAspendingClient
from app.services.candid_grants_client import CandidGrantsClient
from app.services.candid_news_client import CandidNewsClient
from app.services.foundation_aggregator import FoundationAggregator
from app.services.ai_service import ai_service
from app.models import db, Organization, Grant

logger = logging.getLogger(__name__)

class Phase1MatchingEngine:
    """Advanced multi-factor grant matching engine"""
    
    # Scoring weights for different factors
    SCORING_WEIGHTS = {
        'mission_alignment': 0.25,      # How well grant aligns with org mission
        'geographic_match': 0.20,       # Location compatibility
        'budget_fit': 0.15,            # Grant size vs org capacity
        'focus_area_match': 0.20,      # Program area alignment
        'eligibility_score': 0.10,     # Basic eligibility requirements
        'timing_score': 0.05,          # Deadline and readiness
        'funder_fit': 0.05            # Past relationship or similar orgs funded
    }
    
    def __init__(self):
        """Initialize all data source clients"""
        self.federal_client = FederalRegisterClient()
        self.usaspending_client = USAspendingClient()
        self.candid_grants_client = CandidGrantsClient()
        self.candid_news_client = CandidNewsClient()
        self.foundation_client = FoundationAggregator()
        
    def get_all_opportunities(self, organization: Organization) -> List[Dict]:
        """
        Fetch opportunities from all 5 data sources in parallel
        
        Args:
            organization: Organization profile for contextual searching
            
        Returns:
            Combined list of opportunities from all sources
        """
        all_opportunities = []
        
        # Build search context from organization
        search_context = self._build_search_context(organization)
        
        # Fetch from all sources in parallel for speed
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._fetch_federal_grants, search_context): 'federal',
                executor.submit(self._fetch_usaspending_data, search_context): 'usaspending',
                executor.submit(self._fetch_candid_grants, search_context): 'candid_grants',
                executor.submit(self._fetch_candid_news, search_context): 'candid_news',
                executor.submit(self._fetch_foundation_grants, search_context): 'foundations'
            }
            
            for future in as_completed(futures):
                source = futures[future]
                try:
                    opportunities = future.result(timeout=10)
                    logger.info(f"Retrieved {len(opportunities)} opportunities from {source}")
                    all_opportunities.extend(opportunities)
                except Exception as e:
                    logger.error(f"Error fetching from {source}: {e}")
        
        return all_opportunities
    
    def match_and_score(self, organization: Organization, limit: int = 50) -> List[Dict]:
        """
        Get all opportunities and score them for the organization
        
        Args:
            organization: Organization to match for
            limit: Maximum number of results to return
            
        Returns:
            Sorted list of scored opportunities
        """
        try:
            # Get all opportunities
            opportunities = self.get_all_opportunities(organization)
            logger.info(f"Processing {len(opportunities)} total opportunities for matching")
            
            # Score each opportunity
            scored_opportunities = []
            for opp in opportunities:
                score, reasoning = self._calculate_match_score(organization, opp)
                opp['match_score'] = score
                opp['match_reasoning'] = reasoning
                opp['match_factors'] = self._get_match_factors(organization, opp)
                scored_opportunities.append(opp)
            
            # Sort by score descending
            scored_opportunities.sort(key=lambda x: x['match_score'], reverse=True)
            
            # Return top matches
            return scored_opportunities[:limit]
            
        except Exception as e:
            logger.error(f"Error in match_and_score: {e}")
            return []
    
    def _build_search_context(self, org: Organization) -> Dict:
        """Build search parameters from organization profile"""
        context = {
            'keywords': [],
            'location': {
                'city': org.primary_city,
                'state': org.primary_state,
                'zip': org.primary_zip
            },
            'focus_areas': org.primary_focus_areas or [],
            'budget_range': org.annual_budget_range,
            'organization_type': org.org_type
        }
        
        # Extract keywords from mission and programs
        if org.mission:
            # Simple keyword extraction (could use AI for better results)
            words = re.findall(r'\b[a-z]+\b', org.mission.lower())
            important_words = [w for w in words if len(w) > 4 and w not in 
                             ['through', 'provide', 'support', 'community', 'program']]
            context['keywords'].extend(important_words[:10])
        
        # Add custom field keywords
        if org.custom_fields:
            for key, value in org.custom_fields.items():
                if isinstance(value, str) and len(value) > 3:
                    context['keywords'].append(value.lower())
        
        return context
    
    def _fetch_federal_grants(self, context: Dict) -> List[Dict]:
        """Fetch grants from Federal Register API"""
        try:
            grants = []
            
            # Search by keywords
            for keyword in context['keywords'][:3]:  # Limit to avoid too many requests
                results = self.federal_client.search_documents(
                    query=keyword,
                    per_page=5
                )
                for notice in results[:5]:
                    grants.append({
                        'source': 'Federal Register',
                        'title': notice.get('title', ''),
                        'funder': notice.get('agencies', ['Federal Government'])[0] if notice.get('agencies') else 'Federal Government',
                        'description': notice.get('abstract', ''),
                        'deadline': notice.get('comment_end_date'),
                        'url': notice.get('html_url'),
                        'amount_range': 'Varies',
                        'type': 'federal'
                    })
            
            return grants
        except Exception as e:
            logger.error(f"Error fetching federal grants: {e}")
            return []
    
    def _fetch_usaspending_data(self, context: Dict) -> List[Dict]:
        """Fetch historical award data from USAspending"""
        try:
            grants = []
            
            # Get historical awards for context
            awards = self.usaspending_client.search_assistance_listings(
                keywords=' '.join(context['keywords'][:2])
            )
            
            for award in awards[:10]:
                grants.append({
                    'source': 'USAspending.gov',
                    'title': award.get('title', ''),
                    'funder': award.get('agency', 'Federal Agency'),
                    'description': award.get('description', 'Historical grant award data'),
                    'amount_range': award.get('amount', 'Varies'),
                    'url': award.get('url', 'https://www.usaspending.gov'),
                    'type': 'historical'
                })
            
            return grants
        except Exception as e:
            logger.error(f"Error fetching USAspending data: {e}")
            return []
    
    def _fetch_candid_grants(self, context: Dict) -> List[Dict]:
        """Fetch grants from Candid API"""
        try:
            grants = []
            
            # Get Candid summary data
            summary = self.candid_grants_client.get_summary()
            
            if summary:
                # Create opportunity from summary data
                grants.append({
                    'source': 'Candid',
                    'title': f"Grant Opportunities Database",
                    'funder': 'Multiple Foundations',
                    'description': f"Access to comprehensive grant database with historical data",
                    'amount_range': 'Varies by foundation',
                    'url': 'https://candid.org',
                    'type': 'aggregated',
                    'metadata': summary
                })
            
            # Try to search specific grants if available
            search_query = ' '.join(context['focus_areas'][:2]) if context['focus_areas'] else ''
            if search_query:
                results = self.candid_grants_client.search_grants(
                    recipient_name=search_query,
                    recipient_state=context['location'].get('state', '')
                )
                
                for grant in results[:5]:
                    grants.append({
                        'source': 'Candid Grants',
                        'title': grant.get('grant_description', 'Grant Opportunity'),
                        'funder': grant.get('funder_name', 'Foundation'),
                        'description': grant.get('description', ''),
                        'amount_range': f"${grant.get('amount', 0):,.0f}" if grant.get('amount') else 'Varies',
                        'url': 'https://candid.org',
                        'type': 'foundation'
                    })
            
            return grants
        except Exception as e:
            logger.error(f"Error fetching Candid grants: {e}")
            return []
    
    def _fetch_candid_news(self, context: Dict) -> List[Dict]:
        """Fetch grant news from Candid News API"""
        try:
            grants = []
            
            # Search for grant-related news
            search_terms = ' '.join(context['keywords'][:2]) + ' grants' if context['keywords'] else 'grants'
            news_results = self.candid_news_client.search_news(
                search_terms=search_terms,
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            )
            
            articles = news_results.get('data', {}).get('articles', [])
            for article in articles[:5]:
                if 'grant' in article.get('title', '').lower():
                    grants.append({
                        'source': 'Candid News',
                        'title': article.get('title', ''),
                        'funder': article.get('publisher', 'Unknown'),
                        'description': article.get('summary', ''),
                        'deadline': 'See article',
                        'url': article.get('url', '#'),
                        'type': 'news'
                    })
            
            return grants
        except Exception as e:
            logger.error(f"Error fetching Candid news: {e}")
            return []
    
    def _fetch_foundation_grants(self, context: Dict) -> List[Dict]:
        """Fetch grants from major foundations"""
        try:
            grants = []
            
            # Get all foundation data
            foundations = self.foundation_client.get_all_foundations()
            
            for foundation in foundations[:8]:  # Top 8 foundations
                # Check if foundation matches focus areas
                focus_match = False
                if context['focus_areas'] and foundation.get('focus_areas'):
                    for area in context['focus_areas']:
                        if any(area.lower() in f.lower() for f in foundation['focus_areas']):
                            focus_match = True
                            break
                
                if focus_match or not context['focus_areas']:
                    grants.append({
                        'source': 'Foundation Directory',
                        'title': f"{foundation['name']} Grant Opportunities",
                        'funder': foundation['name'],
                        'description': foundation.get('description', ''),
                        'deadline': foundation.get('deadline', 'Rolling'),
                        'amount_range': foundation.get('typical_grant', 'Varies'),
                        'url': foundation.get('website', '#'),
                        'eligibility': foundation.get('eligibility', {}),
                        'type': 'foundation'
                    })
            
            return grants
        except Exception as e:
            logger.error(f"Error fetching foundation grants: {e}")
            return []
    
    def _calculate_match_score(self, org: Organization, opportunity: Dict) -> Tuple[int, str]:
        """
        Calculate comprehensive match score for an opportunity
        
        Returns:
            Tuple of (score 0-100, reasoning text)
        """
        scores = {}
        reasoning_parts = []
        
        # 1. Mission Alignment
        mission_score = self._score_mission_alignment(org, opportunity)
        scores['mission_alignment'] = mission_score
        if mission_score >= 80:
            reasoning_parts.append("Strong mission alignment")
        
        # 2. Geographic Match
        geo_score = self._score_geographic_match(org, opportunity)
        scores['geographic_match'] = geo_score
        if geo_score >= 80:
            reasoning_parts.append("Geographic eligibility confirmed")
        
        # 3. Budget Fit
        budget_score = self._score_budget_fit(org, opportunity)
        scores['budget_fit'] = budget_score
        if budget_score >= 80:
            reasoning_parts.append("Grant size appropriate for organization")
        
        # 4. Focus Area Match
        focus_score = self._score_focus_area_match(org, opportunity)
        scores['focus_area_match'] = focus_score
        if focus_score >= 80:
            reasoning_parts.append("Program areas align well")
        
        # 5. Eligibility Score
        eligibility_score = self._score_eligibility(org, opportunity)
        scores['eligibility_score'] = eligibility_score
        
        # 6. Timing Score
        timing_score = self._score_timing(org, opportunity)
        scores['timing_score'] = timing_score
        
        # 7. Funder Fit
        funder_score = self._score_funder_fit(org, opportunity)
        scores['funder_fit'] = funder_score
        
        # Calculate weighted total
        total_score = 0
        for factor, weight in self.SCORING_WEIGHTS.items():
            total_score += scores.get(factor, 50) * weight
        
        # Generate reasoning
        if not reasoning_parts:
            if total_score >= 70:
                reasoning_parts.append("Good overall compatibility")
            elif total_score >= 50:
                reasoning_parts.append("Moderate compatibility")
            else:
                reasoning_parts.append("Limited compatibility")
        
        reasoning = ". ".join(reasoning_parts)
        
        return int(total_score), reasoning
    
    def _score_mission_alignment(self, org: Organization, opp: Dict) -> int:
        """Score how well opportunity aligns with organization mission"""
        if not org.mission:
            return 50
        
        # Simple keyword matching (could use AI for semantic similarity)
        mission_words = set(org.mission.lower().split())
        opp_text = f"{opp.get('title', '')} {opp.get('description', '')}".lower()
        opp_words = set(opp_text.split())
        
        common_words = mission_words.intersection(opp_words)
        if len(common_words) > 5:
            return 90
        elif len(common_words) > 3:
            return 70
        elif len(common_words) > 1:
            return 50
        return 30
    
    def _score_geographic_match(self, org: Organization, opp: Dict) -> int:
        """Score geographic compatibility"""
        # Check if opportunity has geographic restrictions
        opp_text = f"{opp.get('title', '')} {opp.get('description', '')}".lower()
        
        # National grants score high for everyone
        if 'national' in opp_text or 'nationwide' in opp_text:
            return 90
        
        # Check state match
        if org.primary_state and org.primary_state.lower() in opp_text:
            return 85
        
        # Check city match
        if org.primary_city and org.primary_city.lower() in opp_text:
            return 80
        
        # Default moderate score if no geographic info
        return 60
    
    def _score_budget_fit(self, org: Organization, opp: Dict) -> int:
        """Score if grant amount fits organization budget"""
        if not org.annual_budget_range:
            return 50
        
        # Parse organization budget
        org_budget = 500000  # Default
        if '<$100k' in org.annual_budget_range:
            org_budget = 50000
        elif '$100k-500k' in org.annual_budget_range:
            org_budget = 300000
        elif '$500k-$1m' in org.annual_budget_range:
            org_budget = 750000
        elif '$1m-$5m' in org.annual_budget_range:
            org_budget = 2500000
        
        # Parse grant amount
        amount_str = opp.get('amount_range', '')
        if not amount_str or amount_str == 'Varies':
            return 60  # Unknown amount gets moderate score
        
        # Extract number from amount string
        import re
        numbers = re.findall(r'[\d,]+', amount_str.replace('$', ''))
        if numbers:
            grant_amount = int(numbers[0].replace(',', ''))
            
            # Score based on proportion to budget
            proportion = grant_amount / org_budget
            if 0.05 <= proportion <= 0.3:  # 5-30% of budget is ideal
                return 90
            elif 0.03 <= proportion <= 0.5:  # 3-50% is good
                return 70
            elif proportion < 0.01:  # Too small
                return 30
            elif proportion > 1:  # Too large
                return 40
        
        return 50
    
    def _score_focus_area_match(self, org: Organization, opp: Dict) -> int:
        """Score program area alignment"""
        if not org.primary_focus_areas:
            return 50
        
        opp_text = f"{opp.get('title', '')} {opp.get('description', '')}".lower()
        
        matches = 0
        for focus_area in org.primary_focus_areas:
            if focus_area.lower() in opp_text:
                matches += 1
        
        if matches >= 2:
            return 95
        elif matches == 1:
            return 75
        
        # Check secondary focus areas
        if org.secondary_focus_areas:
            for focus_area in org.secondary_focus_areas:
                if focus_area.lower() in opp_text:
                    return 60
        
        return 40
    
    def _score_eligibility(self, org: Organization, opp: Dict) -> int:
        """Score basic eligibility requirements"""
        eligibility = opp.get('eligibility', {})
        
        if not eligibility:
            return 70  # No restrictions = moderate score
        
        score = 100
        
        # Check organization type
        if 'org_types' in eligibility:
            if org.org_type not in eligibility['org_types']:
                score -= 50
        
        # Check special characteristics
        if eligibility.get('faith_based_only') and not org.faith_based:
            score -= 30
        
        return max(score, 20)
    
    def _score_timing(self, org: Organization, opp: Dict) -> int:
        """Score based on deadline and readiness"""
        deadline = opp.get('deadline')
        
        if not deadline or deadline == 'See article':
            return 50
        
        # Parse deadline
        try:
            if isinstance(deadline, str):
                deadline_date = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                days_until = (deadline_date - datetime.now()).days
                
                if days_until < 7:
                    return 30  # Too soon
                elif days_until < 30:
                    return 60  # Tight timeline
                elif days_until < 90:
                    return 90  # Ideal timeline
                else:
                    return 70  # Plenty of time
        except:
            pass
        
        return 50
    
    def _score_funder_fit(self, org: Organization, opp: Dict) -> int:
        """Score based on funder history and preferences"""
        funder = opp.get('funder', '')
        
        # Check if previously funded by this funder
        if org.previous_funders:
            for prev_funder in org.previous_funders:
                if prev_funder.lower() in funder.lower():
                    return 95  # Previous relationship
        
        # Check funder type preferences
        if 'foundation' in funder.lower() and 'foundation' in (org.preferred_grant_types or []):
            return 70
        elif 'federal' in funder.lower() and 'government' in (org.preferred_grant_types or []):
            return 70
        
        return 50
    
    def _get_match_factors(self, org: Organization, opp: Dict) -> Dict:
        """Get detailed match factors for display"""
        return {
            'mission_alignment': self._score_mission_alignment(org, opp),
            'geographic_match': self._score_geographic_match(org, opp),
            'budget_fit': self._score_budget_fit(org, opp),
            'focus_area_match': self._score_focus_area_match(org, opp),
            'eligibility': self._score_eligibility(org, opp),
            'timing': self._score_timing(org, opp),
            'funder_fit': self._score_funder_fit(org, opp)
        }
    
    def get_funder_intelligence(self, funder_name: str) -> Dict:
        """
        Get comprehensive intelligence about a funder
        
        Args:
            funder_name: Name of the funder
            
        Returns:
            Detailed funder profile and insights
        """
        intelligence = {
            'name': funder_name,
            'giving_history': [],
            'focus_areas': [],
            'typical_grant_size': 'Unknown',
            'application_process': 'Standard',
            'success_tips': [],
            'contact_info': {}
        }
        
        try:
            # Search Candid for funder info
            candid_data = self.candid_grants_client.get_summary()
            
            if candid_data:
                intelligence['typical_grant_size'] = "Varies by program"
                intelligence['total_giving'] = "See foundation website"
                intelligence['grant_count'] = "Multiple opportunities"
            
            # Get news about funder
            news = self.candid_news_client.search_news(
                search_terms=funder_name,
                start_date=(datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            )
            
            articles = news.get('data', {}).get('articles', [])
            intelligence['recent_news'] = [
                {
                    'title': article.get('title'),
                    'date': article.get('published_date'),
                    'url': article.get('url')
                }
                for article in articles[:3]
            ]
            
            # Add success tips based on funder type
            if 'foundation' in funder_name.lower():
                intelligence['success_tips'] = [
                    "Research the foundation's giving history",
                    "Align your proposal with their stated priorities",
                    "Include clear metrics and evaluation plans"
                ]
            elif 'federal' in funder_name.lower() or 'government' in funder_name.lower():
                intelligence['success_tips'] = [
                    "Follow all formatting requirements exactly",
                    "Address all review criteria explicitly",
                    "Include detailed budget justification"
                ]
            
        except Exception as e:
            logger.error(f"Error getting funder intelligence: {e}")
        
        return intelligence

# Singleton instance
phase1_engine = Phase1MatchingEngine()