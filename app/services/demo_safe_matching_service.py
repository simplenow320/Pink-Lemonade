"""
Demo-Safe Matching Service - Uses Only Free Government APIs
Provides real grant data without consuming paid API quotas
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re

from app.services.org_tokens import get_org_tokens

# Import free government API clients
try:
    from app.services.federal_register_client import FederalRegisterClient
    FEDERAL_REGISTER_AVAILABLE = True
except ImportError:
    FederalRegisterClient = None
    FEDERAL_REGISTER_AVAILABLE = False

try:
    from app.services.grants_gov_client import GrantsGovClient
    GRANTS_GOV_AVAILABLE = True
except ImportError:
    GrantsGovClient = None
    GRANTS_GOV_AVAILABLE = False


def is_demo_mode() -> bool:
    """Check if app is running in demo mode"""
    return os.environ.get('DEMO_MODE', 'false').lower() == 'true'


class DemoSafeMatchingService:
    """
    Demo-safe matching service that only uses free government APIs
    Provides real grant data without paid API quotas
    """
    
    def __init__(self):
        # Only initialize free government API clients
        self.federal_register = None
        self.grants_gov = None
        
        if FEDERAL_REGISTER_AVAILABLE and FederalRegisterClient is not None:
            try:
                self.federal_register = FederalRegisterClient()
            except Exception:
                self.federal_register = None
                
        if GRANTS_GOV_AVAILABLE and GrantsGovClient is not None:
            try:
                self.grants_gov = GrantsGovClient()
            except Exception:
                self.grants_gov = None
    
    def federal_register_feed(self, tokens: Dict) -> List[Dict]:
        """
        Get grant notices from Federal Register (100% free)
        
        Args:
            tokens: Organization tokens
            
        Returns:
            List of federal grant notices
        """
        if not self.federal_register:
            return []
        
        try:
            keywords = tokens.get('keywords', ['grant'])
            search_terms = ' OR '.join(keywords[:3])  # Top 3 keywords
            
            notices = self.federal_register.search_grant_notices(
                keywords=search_terms,
                days_back=45
            )
            
            return notices
            
        except Exception as e:
            import logging
            logging.warning(f"Federal Register feed error: {type(e).__name__}")
            return []
    
    def grants_gov_feed(self, tokens: Dict) -> List[Dict]:
        """
        Get opportunities from Grants.gov using free GSA Search API
        
        Args:
            tokens: Organization tokens
            
        Returns:
            List of federal grant opportunities
        """
        if not self.grants_gov:
            return []
        
        try:
            keywords = tokens.get('keywords', ['grant'])
            search_keyword = keywords[0] if keywords else 'grant'
            
            payload = {
                'keywords': [search_keyword],
                'limit': 20
            }
            
            opportunities = self.grants_gov.search_opportunities(payload)
            
            # Filter to recent opportunities (45 days)
            cutoff_date = datetime.now() - timedelta(days=45)
            recent_opportunities = []
            
            for opp in opportunities:
                posted_date_str = opp.get('published_date', '')
                if posted_date_str:
                    try:
                        posted_date = datetime.strptime(posted_date_str[:10], '%Y-%m-%d')
                        if posted_date >= cutoff_date:
                            recent_opportunities.append(opp)
                    except (ValueError, TypeError):
                        # Include if date parsing fails
                        recent_opportunities.append(opp)
                else:
                    recent_opportunities.append(opp)
            
            return recent_opportunities
            
        except Exception as e:
            import logging
            logging.warning(f"Grants.gov feed error: {type(e).__name__}")
            return []
    
    def score_item(self, item: Dict, tokens: Dict) -> Dict:
        """
        Score an opportunity item from 0-100 with detailed reasoning
        
        Args:
            item: Grant opportunity item
            tokens: Organization tokens  
            
        Returns:
            Dict with score, reasons[], flags[]
        """
        score = 0
        reasons = []
        flags = []
        
        # Subject match (40 points max)
        subject_score = 0
        item_text = (item.get('title', '') + ' ' + item.get('description', '') + ' ' + 
                    item.get('content', '')).lower()
        
        # Keyword matching
        keywords = tokens.get('keywords', [])
        matched_keywords = [kw for kw in keywords if kw.lower() in item_text]
        if matched_keywords:
            subject_score = min(len(matched_keywords) * 15, 40)  # Max 40
            reasons.append(f"Keyword matches: {', '.join(matched_keywords[:3])}")
        
        score += subject_score
        
        # Geography match (20 points max)
        geo_score = 0
        locations = tokens.get('locations', [])
        for location in locations:
            if location.lower() in item_text:
                geo_score = 20
                reasons.append(f"Geographic match: {location}")
                break
        
        if geo_score == 0 and locations:
            # Partial geographic match
            for location in locations:
                # Check for state abbreviations or partial matches
                if len(location) == 2 and location.upper() in item_text.upper():
                    geo_score = 10
                    reasons.append(f"State match: {location}")
                    break
        
        score += geo_score
        
        # Source bonus (federal sources are valuable) (15 points)
        source_score = 0
        if item.get('source') in ['federal_register', 'grants_gov']:
            source_score = 15
            reasons.append("Federal funding source")
        
        score += source_score
        
        # Recency (25 points max)
        recency_score = 0
        current_date = datetime.now()
        
        # Check various date fields
        for date_field in ['publication_date', 'published_date', 'posted_date']:
            date_str = item.get(date_field)
            if date_str:
                try:
                    item_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                    days_old = (current_date - item_date).days
                    
                    if days_old <= 7:
                        recency_score = 25
                        reasons.append("Very recent (within 7 days)")
                    elif days_old <= 14:
                        recency_score = 20
                        reasons.append("Recent (within 2 weeks)")
                    elif days_old <= 30:
                        recency_score = 15
                        reasons.append("Recent (within 30 days)")
                    elif days_old <= 45:
                        recency_score = 10
                        reasons.append("Moderately recent")
                    break
                except (ValueError, TypeError):
                    continue
        
        score += recency_score
        
        # Add demo mode indicator
        flags.append("🎯 Demo Mode - Free Government Data Only")
        
        return {
            'score': min(score, 100),  # Cap at 100
            'reasons': reasons,
            'flags': flags
        }
    
    def assemble_demo_results(self, org_id: int, limit: int = 25) -> Dict:
        """
        Assemble demo-safe results using only free government APIs
        
        Args:
            org_id: Organization ID
            limit: Max items per feed
            
        Returns:
            Demo-safe matching results with scores and context
        """
        try:
            # Get organization tokens
            tokens = get_org_tokens(org_id)
            
            # Get Federal Register opportunities (free)
            federal_register_items = self.federal_register_feed(tokens)
            scored_federal_register = []
            for item in federal_register_items:
                scoring = self.score_item(item, tokens)
                item_with_score = item.copy()
                item_with_score.update(scoring)
                item_with_score['sourceNotes'] = {
                    "api": "federal_register",
                    "cost": "FREE",
                    "window": "45d"
                }
                scored_federal_register.append(item_with_score)
            
            # Sort by score desc, then date desc
            scored_federal_register.sort(key=lambda x: (-x['score'], x.get('published_date', '0000-01-01')))
            
            # Get Grants.gov opportunities (free GSA Search API)
            grants_gov_items = self.grants_gov_feed(tokens)
            scored_grants_gov = []
            for item in grants_gov_items:
                scoring = self.score_item(item, tokens)
                item_with_score = item.copy()
                item_with_score.update(scoring)
                item_with_score['sourceNotes'] = {
                    "api": "grants_gov_gsa_search",
                    "cost": "FREE",
                    "window": "45d"
                }
                scored_grants_gov.append(item_with_score)
            
            # Sort grants.gov items
            scored_grants_gov.sort(key=lambda x: (-x['score'], x.get('published_date', '0000-01-01')))
            
            return {
                "demo_mode": True,
                "tokens": tokens,
                "context": {
                    "message": "Demo Mode - Using FREE government APIs only",
                    "sources": ["Federal Register", "Grants.gov GSA Search"],
                    "cost": "FREE",
                    "quota_safe": True
                },
                "federal_register": scored_federal_register[:limit],
                "grants_gov": scored_grants_gov[:limit],
                "total_opportunities": len(scored_federal_register) + len(scored_grants_gov)
            }
            
        except Exception as e:
            import logging
            logging.error(f"Error in demo assemble: {e}")
            return {
                "demo_mode": True,
                "tokens": {},
                "context": {"error": str(e), "cost": "FREE"},
                "federal_register": [],
                "grants_gov": [],
                "total_opportunities": 0
            }


# Demo-safe functions for API endpoints
def get_demo_safe_service():
    """Get demo-safe matching service instance"""
    return DemoSafeMatchingService()


def assemble_demo_results(org_id: int, limit: int = 25) -> Dict:
    """
    Demo-safe version of assemble_results that uses only free APIs
    
    Args:
        org_id: Organization ID
        limit: Result limit
        
    Returns:
        Demo-safe results using only free government APIs
    """
    try:
        service = DemoSafeMatchingService()
        return service.assemble_demo_results(org_id, limit)
    except Exception as e:
        return {
            "demo_mode": True,
            "error": str(e),
            "opportunities": [],
            "context": {"cost": "FREE"}
        }