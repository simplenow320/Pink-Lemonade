"""
Funder Intelligence Service - Gathers comprehensive information about grant funders
"""
import logging
import requests
from typing import Dict, List, Optional

# Import with fallbacks
try:
    from app.services.ai_service import ai_service
    HAS_AI_SERVICE = True
except ImportError:
    HAS_AI_SERVICE = False

try:
    from app.services.comprehensive_grant_scraper import comprehensive_scraper
    HAS_SCRAPER = True
except ImportError:
    HAS_SCRAPER = False

logger = logging.getLogger(__name__)

class FunderIntelligenceService:
    """
    Service to gather comprehensive intelligence about grant funders
    """
    
    def __init__(self):
        self.funder_database = {}  # Cache for funder information
    
    def get_funder_profile(self, funder_name: str, grant_url: str = None) -> Dict:
        """
        Get comprehensive profile of a funder including:
        - Contact information
        - Funding priorities
        - Decision makers
        - Application preferences
        - Success factors
        """
        
        # Check cache first
        if funder_name in self.funder_database:
            return self.funder_database[funder_name]
        
        profile = {
            'name': funder_name,
            'type': self._classify_funder_type(funder_name),
            'contact_info': {},
            'funding_priorities': [],
            'decision_makers': [],
            'application_preferences': {},
            'success_factors': [],
            'typical_grant_amounts': {},
            'review_timeline': '',
            'past_grantees': [],
            'geographic_focus': '',
            'exclusions': []
        }
        
        # Enhance with different strategies based on funder type
        if profile['type'] == 'federal':
            profile = self._enhance_federal_funder_profile(profile, grant_url)
        elif profile['type'] == 'foundation':
            profile = self._enhance_foundation_profile(profile)
        elif profile['type'] == 'corporate':
            profile = self._enhance_corporate_profile(profile)
        elif profile['type'] == 'state_local':
            profile = self._enhance_state_local_profile(profile)
        
        # Cache the profile
        self.funder_database[funder_name] = profile
        
        return profile
    
    def _classify_funder_type(self, funder_name: str) -> str:
        """
        Classify the type of funder
        """
        name_lower = funder_name.lower()
        
        federal_keywords = [
            'department of', 'agency', 'administration', 'bureau', 'service',
            'national science foundation', 'environmental protection', 'health and human services'
        ]
        
        foundation_keywords = [
            'foundation', 'fund', 'trust', 'charitable', 'philanthropic', 'endowment'
        ]
        
        corporate_keywords = [
            'corporation', 'company', 'inc.', 'llc', 'ltd.', 'bank', 'group'
        ]
        
        if any(keyword in name_lower for keyword in federal_keywords):
            return 'federal'
        elif any(keyword in name_lower for keyword in foundation_keywords):
            return 'foundation'
        elif any(keyword in name_lower for keyword in corporate_keywords):
            return 'corporate'
        else:
            return 'state_local'
    
    def _enhance_federal_funder_profile(self, profile: Dict, grant_url: str) -> Dict:
        """
        Enhance profile for federal funders using government databases
        """
        try:
            # Use Federal Program Inventory API if available
            federal_programs = self._query_federal_program_inventory(profile['name'])
            
            if federal_programs:
                profile.update({
                    'annual_budget': federal_programs.get('budget', ''),
                    'funding_priorities': federal_programs.get('priorities', []),
                    'contact_info': federal_programs.get('contacts', {}),
                    'review_timeline': federal_programs.get('review_timeline', '')
                })
            
            # Extract from grant URL if provided
            if grant_url and HAS_SCRAPER:
                scraped_info = comprehensive_scraper.extract_full_grant_details(grant_url)
                if scraped_info.get('funder_profile'):
                    profile.update(scraped_info['funder_profile'])
            
            # Add federal-specific success factors
            profile['success_factors'] = [
                'Strong alignment with federal priorities',
                'Detailed evaluation metrics',
                'Compliance with federal regulations',
                'Clear project timeline and milestones',
                'Demonstrated organizational capacity'
            ]
            
            # Federal application preferences
            profile['application_preferences'] = {
                'submission_platform': 'Grants.gov',
                'prefers_detailed_budgets': True,
                'requires_indirect_cost_negotiation': True,
                'evaluation_criteria_weighted': True,
                'peer_review_process': True
            }
            
        except Exception as e:
            logger.error(f"Error enhancing federal funder profile: {e}")
        
        return profile
    
    def _enhance_foundation_profile(self, profile: Dict) -> Dict:
        """
        Enhance profile for private foundations
        """
        try:
            # Query Foundation Directory API (if available)
            foundation_data = self._query_foundation_directory(profile['name'])
            
            if foundation_data:
                profile.update(foundation_data)
            
            # Add foundation-specific success factors
            profile['success_factors'] = [
                'Clear mission alignment',
                'Strong community impact',
                'Innovative approach',
                'Sustainability plan',
                'Board engagement'
            ]
            
            # Foundation application preferences
            profile['application_preferences'] = {
                'prefers_brief_proposals': True,
                'values_relationships': True,
                'site_visits_common': True,
                'multi_year_funding_available': True,
                'capacity_building_supported': True
            }
            
        except Exception as e:
            logger.error(f"Error enhancing foundation profile: {e}")
        
        return profile
    
    def _enhance_corporate_profile(self, profile: Dict) -> Dict:
        """
        Enhance profile for corporate funders
        """
        try:
            # Corporate funders often have CSR pages
            corporate_info = self._research_corporate_giving(profile['name'])
            
            if corporate_info:
                profile.update(corporate_info)
            
            # Add corporate-specific success factors
            profile['success_factors'] = [
                'Business case for social impact',
                'Employee volunteer opportunities',
                'Brand alignment',
                'Measurable outcomes',
                'Geographic relevance to business'
            ]
            
            # Corporate application preferences
            profile['application_preferences'] = {
                'prefers_brief_proposals': True,
                'values_employee_engagement': True,
                'brand_visibility_important': True,
                'quarterly_reporting_preferred': True,
                'partnership_opportunities': True
            }
            
        except Exception as e:
            logger.error(f"Error enhancing corporate profile: {e}")
        
        return profile
    
    def _enhance_state_local_profile(self, profile: Dict) -> Dict:
        """
        Enhance profile for state and local funders
        """
        try:
            # State and local funders vary widely
            profile['success_factors'] = [
                'Local community impact',
                'Compliance with state regulations',
                'Collaboration with other organizations',
                'Demonstrated local support',
                'Cost-effectiveness'
            ]
            
            profile['application_preferences'] = {
                'local_partnerships_valued': True,
                'community_engagement_important': True,
                'budget_transparency_required': True,
                'regular_reporting_expected': True
            }
            
        except Exception as e:
            logger.error(f"Error enhancing state/local profile: {e}")
        
        return profile
    
    def _query_federal_program_inventory(self, agency_name: str) -> Optional[Dict]:
        """
        Query federal program databases for funder information
        """
        try:
            # This would integrate with APIs like:
            # - Federal Program Inventory
            # - USAspending.gov API
            # - SAM.gov API
            
            # For now, return basic structure
            return {
                'budget': 'Information not available',
                'priorities': ['Education', 'Community Development', 'Health'],
                'contacts': {},
                'review_timeline': '3-6 months'
            }
            
        except Exception as e:
            logger.error(f"Error querying federal program inventory: {e}")
            return None
    
    def _query_foundation_directory(self, foundation_name: str) -> Optional[Dict]:
        """
        Query Foundation Directory Online (if API access available)
        """
        try:
            # This would integrate with Foundation Directory Online API
            # Requires subscription and API key
            
            return {
                'annual_giving': 'Information not available',
                'focus_areas': [],
                'geographic_focus': '',
                'grant_range': '',
                'decision_makers': []
            }
            
        except Exception as e:
            logger.error(f"Error querying foundation directory: {e}")
            return None
    
    def _research_corporate_giving(self, company_name: str) -> Optional[Dict]:
        """
        Research corporate giving programs
        """
        try:
            # This could scrape corporate CSR pages or use business APIs
            return {
                'giving_focus': [],
                'annual_giving': 'Information not available',
                'application_process': '',
                'contact_info': {}
            }
            
        except Exception as e:
            logger.error(f"Error researching corporate giving: {e}")
            return None
    
    def get_funder_contact_strategy(self, funder_name: str) -> Dict:
        """
        Get recommended contact strategy for a specific funder
        """
        profile = self.get_funder_profile(funder_name)
        
        strategy = {
            'recommended_approach': '',
            'best_contact_method': '',
            'timing_recommendations': '',
            'key_talking_points': [],
            'questions_to_ask': [],
            'materials_to_prepare': []
        }
        
        if profile['type'] == 'federal':
            strategy.update({
                'recommended_approach': 'Formal application through official channels',
                'best_contact_method': 'Program officer via official email',
                'timing_recommendations': 'Contact 30-60 days before deadline',
                'key_talking_points': [
                    'Alignment with federal priorities',
                    'Demonstrated capacity',
                    'Measurable outcomes'
                ],
                'questions_to_ask': [
                    'Clarification on eligibility requirements',
                    'Evaluation criteria weighting',
                    'Technical assistance availability'
                ]
            })
        elif profile['type'] == 'foundation':
            strategy.update({
                'recommended_approach': 'Relationship building followed by formal proposal',
                'best_contact_method': 'Program officer via phone or email',
                'timing_recommendations': 'Initial contact 6+ months before need',
                'key_talking_points': [
                    'Mission alignment',
                    'Community impact',
                    'Sustainability'
                ],
                'questions_to_ask': [
                    'Foundation priorities for the year',
                    'Application timeline preferences',
                    'Site visit interest'
                ]
            })
        
        return strategy

# Initialize the funder intelligence service
funder_intelligence = FunderIntelligenceService()