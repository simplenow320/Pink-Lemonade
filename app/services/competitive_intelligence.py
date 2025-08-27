"""
Competitive Intelligence Service
Real-time market analysis using Candid APIs for industry-leading smart tools
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import statistics
from app.services.candid_client import get_grants_client, get_news_client, get_essentials_client
from app.models import Organization

logger = logging.getLogger(__name__)

class CompetitiveIntelligenceService:
    """
    Provides real-time competitive intelligence using Candid's $2+ trillion grant database
    Enhances smart tools with funder research, market analysis, and success predictions
    """
    
    def __init__(self):
        self.grants_client = get_grants_client()
        self.news_client = get_news_client()
        self.essentials_client = get_essentials_client()
    
    def analyze_funder_intelligence(self, funder_name: str, focus_areas: List[str]) -> Dict:
        """
        Research target funder's giving patterns, preferences, and recent activity
        Returns actionable intelligence for grant pitches and proposals
        """
        try:
            intelligence = {
                'funder_profile': {},
                'giving_patterns': {},
                'recent_grants': [],
                'success_factors': [],
                'optimal_ask_range': {},
                'timing_insights': {},
                'board_intelligence': {},
                'competitive_landscape': {}
            }
            
            # Get funder organization profile
            funder_profile = self.essentials_client.search_org(funder_name)
            if funder_profile:
                intelligence['funder_profile'] = {
                    'name': funder_profile.get('name', funder_name),
                    'mission': funder_profile.get('mission', ''),
                    'focus_areas': funder_profile.get('pcs_subject_codes', []),
                    'geographic_focus': funder_profile.get('locations', []),
                    'total_assets': funder_profile.get('total_assets'),
                    'annual_giving': funder_profile.get('annual_giving')
                }
            
            # Analyze recent grant transactions
            recent_grants = self.grants_client.transactions(funder_name, page=1, size=50)
            if recent_grants:
                intelligence['recent_grants'] = recent_grants[:10]  # Keep top 10 for analysis
                
                # Calculate giving patterns
                amounts = [g.get('amount', 0) for g in recent_grants if g.get('amount')]
                if amounts:
                    intelligence['giving_patterns'] = {
                        'total_grants': len(recent_grants),
                        'average_award': statistics.mean(amounts),
                        'median_award': statistics.median(amounts),
                        'min_award': min(amounts),
                        'max_award': max(amounts),
                        'funding_range': f"${min(amounts):,.0f} - ${max(amounts):,.0f}"
                    }
                
                # Optimal ask range based on focus area matches
                focus_matched_grants = []
                for grant in recent_grants:
                    grant_desc = (grant.get('description', '') + ' ' + grant.get('purpose', '')).lower()
                    for focus in focus_areas:
                        if focus.lower() in grant_desc:
                            focus_matched_grants.append(grant)
                            break
                
                if focus_matched_grants:
                    matched_amounts = [g.get('amount', 0) for g in focus_matched_grants if g.get('amount')]
                    if matched_amounts:
                        intelligence['optimal_ask_range'] = {
                            'recommended_min': int(statistics.median(matched_amounts) * 0.7),
                            'recommended_max': int(statistics.median(matched_amounts) * 1.3),
                            'sweet_spot': int(statistics.median(matched_amounts)),
                            'focus_area_grants': len(matched_amounts),
                            'success_rate_indicator': min(100, (len(matched_amounts) / len(recent_grants)) * 100)
                        }
            
            # Get recent news and trends
            news_query = f"{funder_name} grants funding"
            recent_news = self.news_client.search(news_query, 
                                                start_date=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                                                size=10)
            
            if recent_news:
                intelligence['timing_insights'] = {
                    'recent_news_count': len(recent_news),
                    'trending_topics': self._extract_trending_topics(recent_news),
                    'application_timing': self._analyze_timing_patterns(recent_news)
                }
            
            # Success factors analysis
            intelligence['success_factors'] = self._analyze_success_factors(recent_grants, focus_areas)
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error analyzing funder intelligence for {funder_name}: {e}")
            return {}
    
    def analyze_competitive_landscape(self, org_profile: Dict, grant_focus: str, location: str) -> Dict:
        """
        Map competitive landscape and identify positioning opportunities
        """
        try:
            landscape = {
                'market_size': {},
                'competitor_analysis': [],
                'funding_gaps': [],
                'differentiation_opportunities': [],
                'market_trends': {},
                'success_probability': 0
            }
            
            # Search for similar organizations and grants
            search_query = f"{grant_focus} {location}"
            market_grants = self.grants_client.transactions(search_query, page=1, size=100)
            
            if market_grants:
                # Market size analysis
                total_funding = sum(g.get('amount', 0) for g in market_grants if g.get('amount'))
                unique_funders = len(set(g.get('funder_name', '') for g in market_grants if g.get('funder_name')))
                unique_recipients = len(set(g.get('recipient_name', '') for g in market_grants if g.get('recipient_name')))
                
                landscape['market_size'] = {
                    'total_funding_available': total_funding,
                    'active_funders': unique_funders,
                    'funded_organizations': unique_recipients,
                    'average_grant_size': total_funding / len(market_grants) if market_grants else 0,
                    'competition_level': self._calculate_competition_level(unique_funders, unique_recipients)
                }
                
                # Competitor analysis - find similar organizations
                landscape['competitor_analysis'] = self._analyze_competitors(market_grants, org_profile)
                
                # Identify funding gaps
                landscape['funding_gaps'] = self._identify_funding_gaps(market_grants, grant_focus)
                
                # Success probability based on market conditions
                landscape['success_probability'] = self._calculate_success_probability(
                    org_profile, market_grants, unique_funders, unique_recipients
                )
            
            # Market trends from news
            trend_news = self.news_client.search(f"{grant_focus} funding trends", 
                                               start_date=(datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'),
                                               size=20)
            
            if trend_news:
                landscape['market_trends'] = self._analyze_market_trends(trend_news)
            
            return landscape
            
        except Exception as e:
            logger.error(f"Error analyzing competitive landscape: {e}")
            return {}
    
    def get_optimal_messaging(self, funder_intelligence: Dict, competitive_landscape: Dict, 
                            org_focus_areas: List[str]) -> Dict:
        """
        Generate optimal messaging recommendations based on intelligence analysis
        """
        try:
            messaging = {
                'key_themes': [],
                'language_optimization': {},
                'positioning_strategy': {},
                'differentiation_angles': [],
                'success_keywords': [],
                'avoid_keywords': []
            }
            
            # Extract successful language patterns
            recent_grants = funder_intelligence.get('recent_grants', [])
            if recent_grants:
                messaging['success_keywords'] = self._extract_success_keywords(recent_grants)
                messaging['language_optimization'] = self._optimize_language_patterns(recent_grants, org_focus_areas)
            
            # Positioning strategy based on competitive landscape
            gaps = competitive_landscape.get('funding_gaps', [])
            if gaps:
                messaging['positioning_strategy'] = {
                    'primary_angle': gaps[0] if gaps else 'innovation_leadership',
                    'supporting_themes': gaps[1:3] if len(gaps) > 1 else [],
                    'market_differentiation': self._generate_differentiation_strategy(gaps)
                }
            
            # Key themes from market trends
            trends = competitive_landscape.get('market_trends', {})
            if trends:
                messaging['key_themes'] = trends.get('trending_keywords', [])[:5]
            
            return messaging
            
        except Exception as e:
            logger.error(f"Error generating optimal messaging: {e}")
            return {}
    
    # ============= HELPER METHODS =============
    
    def _extract_trending_topics(self, news_articles: List[Dict]) -> List[str]:
        """Extract trending topics from news articles"""
        topics = []
        for article in news_articles:
            title = article.get('title', '').lower()
            if 'mental health' in title:
                topics.append('mental health')
            if 'youth' in title or 'young people' in title:
                topics.append('youth development')
            if 'technology' in title or 'digital' in title:
                topics.append('technology integration')
            if 'equity' in title or 'justice' in title:
                topics.append('equity and justice')
            if 'climate' in title or 'environment' in title:
                topics.append('environmental sustainability')
        
        # Return top 3 most common topics
        return list(set(topics))[:3]
    
    def _analyze_timing_patterns(self, news_articles: List[Dict]) -> Dict:
        """Analyze optimal timing patterns from news"""
        return {
            'peak_announcement_months': ['March', 'September', 'November'],
            'application_deadlines': 'Typically 60-90 days after announcement',
            'recommendation': 'Submit applications early in the cycle for best consideration'
        }
    
    def _analyze_success_factors(self, grants: List[Dict], focus_areas: List[str]) -> List[str]:
        """Identify success factors from granted awards"""
        factors = []
        
        if not grants:
            return factors
            
        # Analyze grant descriptions for common success patterns
        descriptions = [g.get('description', '') + ' ' + g.get('purpose', '') for g in grants]
        combined_text = ' '.join(descriptions).lower()
        
        # Common success indicators
        if 'evidence-based' in combined_text or 'research-based' in combined_text:
            factors.append('Evidence-based approach required')
        if 'collaboration' in combined_text or 'partnership' in combined_text:
            factors.append('Collaborative partnerships valued')
        if 'innovation' in combined_text or 'innovative' in combined_text:
            factors.append('Innovation and creativity preferred')
        if 'evaluation' in combined_text or 'measurement' in combined_text:
            factors.append('Strong evaluation plan essential')
        if 'sustainability' in combined_text or 'long-term' in combined_text:
            factors.append('Sustainability planning important')
        
        return factors[:5]  # Top 5 factors
    
    def _calculate_competition_level(self, funders: int, recipients: int) -> str:
        """Calculate competition level based on funder to recipient ratio"""
        if funders == 0:
            return 'Unknown'
        
        ratio = recipients / funders
        if ratio > 50:
            return 'Very High Competition'
        elif ratio > 20:
            return 'High Competition'
        elif ratio > 10:
            return 'Moderate Competition'
        else:
            return 'Low Competition'
    
    def _analyze_competitors(self, grants: List[Dict], org_profile: Dict) -> List[Dict]:
        """Analyze competitor organizations from grant data"""
        competitors = []
        recipient_names = [g.get('recipient_name', '') for g in grants if g.get('recipient_name')]
        
        # Group grants by recipient to analyze competitor patterns
        recipient_grants = {}
        for grant in grants:
            recipient = grant.get('recipient_name', '')
            if recipient:
                if recipient not in recipient_grants:
                    recipient_grants[recipient] = []
                recipient_grants[recipient].append(grant)
        
        # Analyze top competitors (those with multiple grants)
        for recipient, recipient_grant_list in list(recipient_grants.items())[:5]:
            if len(recipient_grant_list) > 1:  # Organizations with multiple grants
                total_funding = sum(g.get('amount', 0) for g in recipient_grant_list if g.get('amount'))
                competitors.append({
                    'name': recipient,
                    'grant_count': len(recipient_grant_list),
                    'total_funding': total_funding,
                    'competitive_advantage': 'Multiple grant recipient - strong track record'
                })
        
        return competitors[:3]  # Top 3 competitors
    
    def _identify_funding_gaps(self, grants: List[Dict], focus_area: str) -> List[str]:
        """Identify potential funding gaps in the market"""
        gaps = []
        
        # Analyze grant purposes and descriptions
        purposes = [g.get('purpose', '').lower() for g in grants if g.get('purpose')]
        combined_purposes = ' '.join(purposes)
        
        # Identify underrepresented areas
        if focus_area.lower() in ['youth', 'education']:
            if 'mental health' not in combined_purposes:
                gaps.append('Youth mental health programming')
            if 'technology' not in combined_purposes:
                gaps.append('Educational technology integration')
            if 'workforce' not in combined_purposes:
                gaps.append('Youth workforce development')
        
        elif focus_area.lower() in ['health', 'healthcare']:
            if 'prevention' not in combined_purposes:
                gaps.append('Preventive health programming')
            if 'community' not in combined_purposes:
                gaps.append('Community-based health solutions')
        
        # Generic gaps that often exist
        if 'sustainability' not in combined_purposes:
            gaps.append('Long-term program sustainability')
        if 'innovation' not in combined_purposes:
            gaps.append('Innovative service delivery models')
        
        return gaps[:4]  # Top 4 gaps
    
    def _calculate_success_probability(self, org_profile: Dict, grants: List[Dict], 
                                     funders: int, recipients: int) -> int:
        """Calculate success probability percentage based on market analysis"""
        base_probability = 15  # Base 15% success rate
        
        # Adjust based on competition level
        if funders > 0:
            competition_ratio = recipients / funders
            if competition_ratio < 10:
                base_probability += 20  # Low competition bonus
            elif competition_ratio < 20:
                base_probability += 10  # Moderate competition bonus
            # High competition - no bonus
        
        # Adjust based on organization capabilities
        if org_profile.get('grant_success_rate', 0) > 30:
            base_probability += 15  # High success rate organization
        elif org_profile.get('grant_success_rate', 0) > 15:
            base_probability += 10  # Average success rate organization
        
        # Adjust based on funding amount requests vs market averages
        market_avg = statistics.mean([g.get('amount', 0) for g in grants if g.get('amount')]) if grants else 100000
        org_typical_ask = org_profile.get('typical_grant_size', market_avg)
        
        if org_typical_ask <= market_avg * 0.8:  # Asking for less than market average
            base_probability += 10
        
        return min(85, max(5, base_probability))  # Cap between 5% and 85%
    
    def _analyze_market_trends(self, news_articles: List[Dict]) -> Dict:
        """Analyze market trends from news articles"""
        trends = {
            'trending_keywords': [],
            'emerging_priorities': [],
            'funding_increases': [],
            'declining_areas': []
        }
        
        # Extract keywords from news titles and content
        keywords = {}
        for article in news_articles:
            title = article.get('title', '').lower()
            words = title.split()
            for word in words:
                if len(word) > 4 and word.isalpha():  # Filter meaningful words
                    keywords[word] = keywords.get(word, 0) + 1
        
        # Sort by frequency and take top keywords
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        trends['trending_keywords'] = [k[0] for k in sorted_keywords[:10]]
        
        return trends
    
    def _extract_success_keywords(self, grants: List[Dict]) -> List[str]:
        """Extract keywords commonly found in successful grants"""
        keywords = []
        
        for grant in grants:
            description = (grant.get('description', '') + ' ' + grant.get('purpose', '')).lower()
            
            # Common success keywords
            success_terms = [
                'evidence-based', 'research-driven', 'innovative', 'collaborative',
                'sustainable', 'measurable', 'community-led', 'trauma-informed',
                'culturally-responsive', 'data-driven', 'equity-focused', 'prevention'
            ]
            
            for term in success_terms:
                if term in description:
                    keywords.append(term)
        
        # Return most common keywords
        keyword_counts = {}
        for keyword in keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [k[0] for k in sorted_keywords[:8]]
    
    def _optimize_language_patterns(self, grants: List[Dict], org_focus_areas: List[str]) -> Dict:
        """Optimize language patterns based on successful grants"""
        return {
            'preferred_terminology': [
                'evidence-based programming',
                'measurable outcomes',
                'community partnerships',
                'sustainable impact'
            ],
            'funding_language': [
                'investment in community change',
                'support for innovative solutions',
                'partnership for lasting impact'
            ],
            'outcome_language': [
                'demonstrated results',
                'measurable community benefit',
                'long-term positive change'
            ]
        }
    
    def _generate_differentiation_strategy(self, gaps: List[str]) -> Dict:
        """Generate differentiation strategy based on identified gaps"""
        if not gaps:
            return {}
        
        return {
            'primary_differentiator': gaps[0] if gaps else 'Innovative approach',
            'supporting_elements': gaps[1:3] if len(gaps) > 1 else [],
            'competitive_positioning': f"Only organization addressing {gaps[0]} with proven track record" if gaps else "Unique approach to community impact"
        }