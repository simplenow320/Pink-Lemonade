"""
Matching Service for Grant and News Feed Scoring
Integrates Candid News, Grants, and Federal opportunities with intelligent scoring
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re

from app.services.candid_client import NewsClient, GrantsClient
from app.services.org_tokens import get_org_tokens

# Optional import - skip federal feed if not available
try:
    from app.services.grants_gov_client import GrantsGovClient
    FEDERAL_AVAILABLE = True
except ImportError:
    GrantsGovClient = None
    FEDERAL_AVAILABLE = False


def build_query_terms(tokens: Dict) -> Dict:
    """
    Build query terms from organization tokens
    
    Args:
        tokens: Output from get_org_tokens() with pcs codes, locations, keywords
        
    Returns:
        Dict with news_query, date window, region, transactions_query
    """
    # Base news query for opportunity detection
    news_query = 'RFP OR "grant opportunity" OR "call for proposals" OR "accepting applications"'
    
    # Add top 2 subject keywords if available
    keywords = tokens.get('keywords', [])
    if keywords:
        top_keywords = keywords[:2]
        keyword_terms = ' OR '.join([f'"{kw}"' for kw in top_keywords])
        news_query += f' OR ({keyword_terms})'
    
    # Date window: last 45 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=45)
    
    # Primary location from tokens
    locations = tokens.get('locations', [])
    primary_location = locations[0] if locations else ""
    
    # Build transactions query
    primary_subject = ""
    if tokens.get('pcs_subject_codes'):
        # Use PCS codes if available - but for text search, use keywords
        primary_subject = keywords[0] if keywords else ""
    elif keywords:
        primary_subject = keywords[0]
    
    # Construct transactions query and clean double spaces
    transactions_query = f'{primary_subject} AND {primary_location}'.strip()
    transactions_query = re.sub(r'\s+', ' ', transactions_query).strip(' AND')
    
    return {
        'news_query': news_query,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'region': primary_location,
        'transactions_query': transactions_query,
        'keywords': keywords[:3]  # Top 3 for federal search
    }


class MatchingService:
    """
    Main service for matching organizations to grant opportunities
    """
    
    def __init__(self):
        # Check DEMO_MODE and CANDID_ENABLED to avoid burning API quotas
        import os
        demo_mode = os.environ.get('DEMO_MODE', 'false').lower() == 'true'
        candid_disabled = os.environ.get('CANDID_ENABLED', 'true').lower() == 'false'
        
        if demo_mode or candid_disabled:
            # Use demo-safe mock clients that don't call external APIs
            self.news = None  # Disable Candid News API
            self.grants = None  # Disable Candid Grants API
        else:
            self.news = NewsClient()
            self.grants = GrantsClient()
            
        self.federal_client = None
        
        if FEDERAL_AVAILABLE and GrantsGovClient is not None:
            try:
                self.federal_client = GrantsGovClient()
            except Exception:
                self.federal_client = None
    
    def news_feed(self, tokens: Dict) -> List[Dict]:
        """
        Get filtered news feed from Candid News API
        
        Args:
            tokens: Organization tokens with PCS codes and keywords
            
        Returns:
            List of opportunity-focused news items
        """
        # Return empty list in demo mode (Candid disabled)
        if self.news is None:
            return []
            
        try:
            query_terms = build_query_terms(tokens)
            
            # Search Candid News API
            results = self.news.search(
                query=query_terms['news_query'],
                start_date=query_terms['start_date'],
                pcs_subject_codes=tokens.get('pcs_subject_codes', []),
                pcs_population_codes=tokens.get('pcs_population_codes', []),
                region=query_terms['region']
            )
            
            # Handle both dict and list responses
            articles_list = []
            if isinstance(results, list):
                articles_list = results
            elif isinstance(results, dict):
                articles_list = results.get('articles', results.get('data', results.get('results', [])))
            
            # Filter to opportunity items only
            opportunities = []
            for item in articles_list:
                if not isinstance(item, dict):
                    continue
                    
                content_lower = (item.get('content', '') + ' ' + item.get('title', '')).lower()
                
                # Primary filter: RFP mentioned
                if item.get('rfp_mentioned', False):
                    opportunities.append(item)
                # Secondary filter: grant mentioned + action words
                elif item.get('grant_mentioned', False):
                    action_words = ['apply', 'application', 'accepting', 'deadline']
                    if any(word in content_lower for word in action_words):
                        opportunities.append(item)
                # Filter out staff changes unless they mention opportunities
                elif item.get('staff_change_mentioned', False):
                    # Only include if opportunity keywords present
                    opp_keywords = ['rfp', 'apply', 'application', 'accepting', 'deadline', 'grant opportunity']
                    if not any(keyword in content_lower for keyword in opp_keywords):
                        continue  # Skip staff changes without opportunities
                    opportunities.append(item)
            
            return opportunities
            
        except Exception as e:
            # Don't log full exception details to avoid secrets leakage
            import logging
            logging.warning(f"News feed error: {type(e).__name__}")
            return []
    
    def federal_feed(self, tokens: Dict) -> List[Dict]:
        """
        Get federal opportunities from Grants.gov if available
        
        Args:
            tokens: Organization tokens
            
        Returns:
            List of federal grant opportunities or empty list if unavailable
        """
        if not self.federal_client:
            return []
        
        try:
            query_terms = build_query_terms(tokens)
            
            # Use first keyword for federal search
            search_keyword = query_terms['keywords'][0] if query_terms['keywords'] else 'grant'
            
            # Search with 45-day window
            payload = {
                'keywords': [search_keyword],
                'oppStatuses': ['posted'],  # Active opportunities
                'sortBy': 'openDate|desc'
            }
            
            opportunities = self.federal_client.search_opportunities(payload)
            
            # Filter to recent opportunities (45 days)
            cutoff_date = datetime.now() - timedelta(days=45)
            recent_opportunities = []
            
            for opp in opportunities:
                posted_date_str = opp.get('posted_date', '')
                if posted_date_str:
                    try:
                        posted_date = datetime.strptime(posted_date_str, '%Y-%m-%d')
                        if posted_date >= cutoff_date:
                            recent_opportunities.append(opp)
                    except (ValueError, TypeError):
                        # Include if date parsing fails (don't lose opportunities)
                        recent_opportunities.append(opp)
                else:
                    recent_opportunities.append(opp)
            
            return recent_opportunities
            
        except Exception as e:
            import logging
            logging.warning(f"Federal feed error: {type(e).__name__}")
            return []
    
    def context_snapshot(self, tokens: Dict) -> Dict:
        """
        Get funding context snapshot from Candid Grants API
        Returns empty context in demo mode to avoid API calls
        
        Args:
            tokens: Organization tokens
            
        Returns:
            Dict with award_count, median_award, recent_funders, query_used
        """
        # Return empty context in demo mode (Candid disabled)
        if self.grants is None:
            return {
                'award_count': 0,
                'median_award': None,
                'query_used': 'Demo mode - Candid APIs disabled',
                'recent_funders': [],
                'sourceNotes': {
                    'api': 'demo.mode',
                    'endpoint': 'disabled',
                    'query': 'Candid APIs disabled in demo mode'
                }
            }
            
        try:
            query_terms = build_query_terms(tokens)
            query = query_terms['transactions_query']
            location = query_terms['region']
            
            # Get transactions snapshot
            snapshot = self.grants.snapshot_for(query, location)
            
            # Add query used for transparency
            if isinstance(snapshot, dict):
                snapshot['query_used'] = query
            else:
                snapshot = {'query_used': query, 'award_count': 0, 'median_award': None, 'recent_funders': []}
            
            return snapshot
            
        except Exception as e:
            import logging
            logging.warning(f"Context snapshot error: {type(e).__name__}")
            return {'query_used': '', 'award_count': 0, 'median_award': None, 'recent_funders': []}
    
    def score_item(self, item: Dict, tokens: Dict, snapshot: Dict) -> Dict:
        """
        Score an opportunity item from 0-100 with detailed reasoning
        
        Args:
            item: Grant/news opportunity item
            tokens: Organization tokens  
            snapshot: Funding context from grants data
            
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
        
        # Check PCS subject codes first
        pcs_subjects = tokens.get('pcs_subject_codes', [])
        if pcs_subjects:
            for pcs_code in pcs_subjects:
                if pcs_code.lower() in item_text:
                    subject_score = 40
                    reasons.append(f"Strong subject match: {pcs_code}")
                    break
        
        # Fall back to keyword matching
        if subject_score == 0:
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
        
        # Eligibility match (15 points max)
        eligibility_score = 0
        eligibility_text = item.get('eligibility', '').lower()
        if eligibility_text:
            nonprofit_terms = ['nonprofit', '501(c)(3)', 'charitable', 'tax-exempt']
            if any(term in eligibility_text for term in nonprofit_terms):
                eligibility_score = 15
                reasons.append("Nonprofit eligibility confirmed")
            elif 'organization' in eligibility_text:
                eligibility_score = 8
                reasons.append("General organization eligibility")
        
        score += eligibility_score
        
        # Amount alignment (15 points max)
        amount_score = 0
        item_amount = None
        
        # Extract amount from various fields
        for field in ['award_ceiling', 'amount', 'award_floor']:
            if item.get(field):
                try:
                    item_amount = float(str(item[field]).replace(',', '').replace('$', ''))
                    break
                except (ValueError, TypeError):
                    continue
        
        if item_amount and snapshot.get('median_award'):
            try:
                median_award = float(snapshot['median_award'])
                ratio = item_amount / median_award
                if 0.5 <= ratio <= 2.0:  # Within reasonable range
                    amount_score = 15
                    reasons.append(f"Amount aligns with median: ${int(item_amount):,} vs ${int(median_award):,}")
                elif ratio < 0.5:
                    amount_score = 8
                    reasons.append("Below median award amount")
                else:
                    amount_score = 5
                    flags.append("Above typical award range")
            except (ValueError, TypeError):
                pass
        
        score += amount_score
        
        # Recency (10 points max)
        recency_score = 0
        current_date = datetime.now()
        
        # Check various date fields
        for date_field in ['publication_date', 'posted_date', 'close_date']:
            date_str = item.get(date_field)
            if date_str:
                try:
                    item_date = datetime.strptime(date_str[:10], '%Y-%m-%d')  # Handle ISO format
                    days_old = (current_date - item_date).days
                    
                    if days_old <= 7:
                        recency_score = 10
                        reasons.append("Very recent (within 7 days)")
                    elif days_old <= 30:
                        recency_score = 7
                        reasons.append("Recent (within 30 days)")
                    elif days_old <= 45:
                        recency_score = 4
                        reasons.append("Moderately recent")
                    break
                except (ValueError, TypeError):
                    continue
        
        score += recency_score
        
        # Add flags for important notices
        if item.get('close_date'):
            try:
                close_date = datetime.strptime(item['close_date'][:10], '%Y-%m-%d')
                days_to_close = (close_date - current_date).days
                if days_to_close <= 7:
                    flags.append("Deadline within 7 days")
                elif days_to_close <= 14:
                    flags.append("Deadline within 2 weeks")
            except (ValueError, TypeError):
                pass
        
        return {
            'score': min(score, 100),  # Cap at 100
            'reasons': reasons,
            'flags': flags
        }
    
    def assemble(self, org_id: int, limit: int = 25) -> Dict:
        """
        Assemble complete matching results for organization
        
        Args:
            org_id: Organization ID
            limit: Max items per feed
            
        Returns:
            Complete matching results with scores and context
        """
        from datetime import datetime
        import logging
        logger = logging.getLogger(__name__)
        
        # Start timing instrumentation  
        assemble_start = datetime.utcnow()
        timing_metrics = {}
        
        try:
            # DEFENSIVE CAPS: Prevent over-fetching to reduce external API load
            per_source_limit = min(limit, 15)  # Cap each source at 15 items max
            logger.info(f"🔍 ASSEMBLE STARTING for org {org_id}: limit={limit}, per_source_limit={per_source_limit}")
            
            # Get organization tokens with timing
            tokens_start = datetime.utcnow()
            tokens = get_org_tokens(org_id)
            timing_metrics['tokens_ms'] = (datetime.utcnow() - tokens_start).total_seconds() * 1000
            
            # Get funding context with timing  
            context_start = datetime.utcnow()
            snapshot = self.context_snapshot(tokens)
            timing_metrics['context_ms'] = (datetime.utcnow() - context_start).total_seconds() * 1000
            
            # Get news opportunities with timing and defensive caps
            news_start = datetime.utcnow()
            news_items = self.news_feed(tokens)
            # Apply defensive cap BEFORE scoring to reduce processing load
            news_items = news_items[:per_source_limit] if news_items else []
            timing_metrics['news_fetch_ms'] = (datetime.utcnow() - news_start).total_seconds() * 1000
            
            # Score news items with timing
            news_scoring_start = datetime.utcnow()
            scored_news = []
            for item in news_items:
                scoring = self.score_item(item, tokens, snapshot)
                item_with_score = item.copy()
                item_with_score.update(scoring)
                item_with_score['sourceNotes'] = {
                    "api": "candid.news",
                    "query": build_query_terms(tokens)['news_query'],
                    "window": "45d"
                }
                scored_news.append(item_with_score)
            timing_metrics['news_scoring_ms'] = (datetime.utcnow() - news_scoring_start).total_seconds() * 1000
            
            # Sort by score desc, then date asc
            scored_news.sort(key=lambda x: (-x['score'], x.get('publication_date', '9999-12-31')))
            
            # Get federal opportunities with timing and defensive caps
            federal_start = datetime.utcnow()
            federal_items = self.federal_feed(tokens)
            # Apply defensive cap BEFORE scoring to reduce processing load
            federal_items = federal_items[:per_source_limit] if federal_items else []
            timing_metrics['federal_fetch_ms'] = (datetime.utcnow() - federal_start).total_seconds() * 1000
            
            # Score federal items with timing
            federal_scoring_start = datetime.utcnow()
            scored_federal = []
            for item in federal_items:
                scoring = self.score_item(item, tokens, snapshot)
                item_with_score = item.copy()
                item_with_score.update(scoring)
                item_with_score['sourceNotes'] = {
                    "api": "grants.gov",
                    "endpoint": "search2", 
                    "window": "45d"
                }
                scored_federal.append(item_with_score)
            timing_metrics['federal_scoring_ms'] = (datetime.utcnow() - federal_scoring_start).total_seconds() * 1000
            
            # Sort federal items
            scored_federal.sort(key=lambda x: (-x['score'], x.get('posted_date', '9999-12-31')))
            
            # Calculate total assemble time
            assemble_duration = (datetime.utcnow() - assemble_start).total_seconds()
            timing_metrics['total_assemble_ms'] = assemble_duration * 1000
            
            # Log comprehensive timing breakdown
            news_final_count = len(scored_news[:limit])
            federal_final_count = len(scored_federal[:limit])
            logger.info(f"✅ ASSEMBLE COMPLETED in {assemble_duration:.2f}s for org {org_id}: {news_final_count} news, {federal_final_count} federal")
            logger.info(f"⏱️ ASSEMBLE TIMING: Tokens={timing_metrics['tokens_ms']:.0f}ms, Context={timing_metrics['context_ms']:.0f}ms, News={timing_metrics['news_fetch_ms']:.0f}ms+{timing_metrics['news_scoring_ms']:.0f}ms, Federal={timing_metrics['federal_fetch_ms']:.0f}ms+{timing_metrics['federal_scoring_ms']:.0f}ms")
            
            return {
                "tokens": tokens,
                "context": {
                    **snapshot,
                    "sourceNotes": {
                        "api": "candid.grants",
                        "endpoint": "transactions", 
                        "query": snapshot.get("query_used", "")
                    }
                },
                "news": scored_news[:limit],
                "federal": scored_federal[:limit],
                "foundation": [],  # Add foundation support for future
                "performance_timing": timing_metrics
            }
            
        except Exception as e:
            assemble_duration = (datetime.utcnow() - assemble_start).total_seconds()
            logger.error(f"❌ ASSEMBLE FAILED in {assemble_duration:.2f}s for org {org_id}: {e}")
            return {
                "tokens": {},
                "context": {"error": str(e)},
                "news": [],
                "federal": [],
                "foundation": []
            }


# Legacy compatibility functions for existing API endpoints
def build_tokens(org_id: int) -> Dict:
    """
    Legacy compatibility for build_tokens function.
    
    Args:
        org_id: Organization ID
        
    Returns:
        Dict with keywords, geo, populations (old format)
    """
    try:
        tokens = get_org_tokens(org_id)
        
        # Convert new format to legacy format
        return {
            "keywords": tokens.get('keywords', ['nonprofit', 'community']),
            "geo": tokens.get('locations', ['United States'])[0] if tokens.get('locations') else 'United States',
            "populations": tokens.get('pcs_population_codes', [])
        }
    except Exception:
        return {
            "keywords": ["nonprofit", "community"],
            "geo": "United States", 
            "populations": []
        }


def assemble_results(org_id: int, limit: int = 25) -> Dict:
    """
    Legacy compatibility for assemble_results function.
    
    Args:
        org_id: Organization ID
        limit: Result limit
        
    Returns:
        Results in legacy format
    """
    try:
        service = MatchingService()
        return service.assemble(org_id, limit)
    except Exception as e:
        return {
            "error": str(e),
            "opportunities": []
        }