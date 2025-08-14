"""
Matching Service for Grant and News Feed Scoring
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
from functools import lru_cache

from app.services.candid_client import get_candid_client
from app.services.grants_gov_client import get_grants_gov_client
from app.services.candid_insights import transactions_snapshot

def build_tokens(org_id: int) -> Dict:
    """
    Build search tokens from organization profile
    
    Returns dict with keywords, geo, populations
    Falls back to safe defaults if org not found
    """
    try:
        from app import db
        from app.models import Organization
        
        org = db.session.query(Organization).filter_by(id=org_id).first()
        
        if org:
            # Extract keywords from various fields
            keywords = []
            
            # Add focus areas
            if org.primary_focus_areas:
                keywords.extend(org.primary_focus_areas if isinstance(org.primary_focus_areas, list) else [])
            
            # Add keywords from mission
            if org.keywords:
                keywords.extend([kw.strip() for kw in org.keywords.split(',') if kw.strip()])
                
            # Extract geo from location or state  
            geo = ""
            if org.primary_state:
                geo = org.primary_state
            elif org.primary_city:
                geo = org.primary_city
                
            # Extract populations served  
            populations = []
            if org.target_demographics:
                populations = org.target_demographics if isinstance(org.target_demographics, list) else []
                
            return {
                "keywords": keywords or ["nonprofit", "community"],
                "geo": geo or "United States",
                "populations": populations or []
            }
        else:
            print(f"Warning: Organization {org_id} not found, using defaults")
            
    except Exception as e:
        print(f"Error building tokens: {e}")
    
    # Safe defaults
    return {
        "keywords": ["nonprofit", "community"],
        "geo": "United States",
        "populations": []
    }

def news_feed(tokens: Dict) -> List[Dict]:
    """
    Get news feed from Candid API
    
    Searches for RFPs and grant opportunities matching keywords
    Filters to last 30-60 days
    """
    try:
        client = get_candid_client()
        
        # Build query
        base_query = 'RFP OR "grant opportunity" OR "call for proposals"'
        if tokens.get("keywords"):
            keyword_str = " OR ".join(tokens["keywords"][:3])  # Limit keywords
            query = f'({base_query}) AND ({keyword_str})'
        else:
            query = base_query
            
        # Set date range (last 60 days)
        start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        
        # Search news
        result = client.search_news(
            query=query,
            start_date=start_date,
            region=tokens.get("geo", ""),
            page=1,
            size=50
        )
        
        # Extract and normalize articles
        news_items = []
        if "articles" in result:
            for article in result["articles"]:
                item = {
                    "source": "candid_news",
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "publisher": article.get("publisher", ""),
                    "published_at": article.get("published_date", article.get("date", "")),
                }
                if article.get("summary"):
                    item["summary"] = article["summary"]
                news_items.append(item)
                
        return news_items
        
    except Exception as e:
        print(f"Error fetching news feed: {e}")
        return []

def federal_feed(tokens: Dict) -> List[Dict]:
    """
    Get federal opportunities from Grants.gov
    
    Searches for recent posted/forecasted opportunities
    """
    try:
        client = get_grants_gov_client()
        
        # Build search payload
        payload = {
            "keyword": " ".join(tokens.get("keywords", ["nonprofit"])[:3]),
            "oppStatuses": ["posted", "forecasted"],
        }
        
        # Add date range (last 45 days)
        posted_from = (datetime.now() - timedelta(days=45)).strftime("%m/%d/%Y")
        posted_to = datetime.now().strftime("%m/%d/%Y")
        payload["postedFrom"] = posted_from
        payload["postedTo"] = posted_to
        
        # Search opportunities
        opportunities = client.search_opportunities(payload)
        
        # Sort by closing date
        for opp in opportunities:
            # Parse close date for sorting
            close_date_str = opp.get("close_date", "")
            try:
                if close_date_str:
                    opp["_close_date"] = datetime.strptime(close_date_str, "%m/%d/%Y")
                else:
                    opp["_close_date"] = datetime.max
            except:
                opp["_close_date"] = datetime.max
                
        opportunities.sort(key=lambda x: x.get("_close_date", datetime.max))
        
        # Remove sorting field
        for opp in opportunities:
            opp.pop("_close_date", None)
            
        return opportunities
        
    except Exception as e:
        print(f"Error fetching federal feed: {e}")
        return []

def context_snapshot(tokens: Dict) -> Optional[Dict]:
    """
    Get funding context snapshot from Candid
    
    Returns award statistics for the primary topic and geography
    """
    try:
        # Use first keyword as primary topic
        topic = tokens.get("keywords", [""])[0] if tokens.get("keywords") else ""
        geo = tokens.get("geo", "")
        
        if not topic and not geo:
            return None
            
        snapshot = transactions_snapshot(topic, geo)
        return snapshot
        
    except Exception as e:
        print(f"Error getting context snapshot: {e}")
        return None

def score_item(item: Dict, tokens: Dict, snapshot: Optional[Dict]) -> Dict:
    """
    Score an item (grant or news) based on tokens and context
    
    Returns score (0-100), reasons, and flags
    """
    score = 0
    reasons = []
    flags = []
    
    # 1. Subject/keyword overlap (0-40 points)
    keywords = [kw.lower() for kw in tokens.get("keywords", [])]
    title = item.get("title", "").lower()
    summary = item.get("summary", "").lower() if item.get("summary") else ""
    content = f"{title} {summary}"
    
    keyword_matches = sum(1 for kw in keywords if kw in content)
    if keyword_matches:
        keyword_score = min(40, keyword_matches * 15)
        score += keyword_score
        reasons.append(f"Keywords matched: {keyword_matches}")
    
    # 2. Geography match (0-20 points)
    geo = tokens.get("geo", "").lower()
    if geo and geo != "united states":
        item_geo = f"{item.get('agency', '')} {item.get('eligibility_text', '')} {item.get('publisher', '')}".lower()
        if geo in item_geo:
            score += 20
            reasons.append(f"Geography match: {geo}")
    
    # 3. Eligibility for nonprofits (0-15 points)
    eligibility = item.get("eligibility_text", "").lower()
    if any(term in eligibility for term in ["nonprofit", "501(c)(3)", "501c3", "non-profit"]):
        score += 15
        reasons.append("Nonprofit eligible")
    
    # 4. Award amount alignment (0-15 points)
    if snapshot and snapshot.get("median_award"):
        median = snapshot["median_award"]
        floor = item.get("award_floor")
        ceiling = item.get("award_ceiling")
        
        if floor and ceiling:
            # Check if median is in range
            if floor <= median <= ceiling:
                score += 15
                reasons.append(f"Award range aligns with median ${median:,.0f}")
        elif floor or ceiling:
            # Partial match
            score += 7
            reasons.append("Partial award information")
    
    # 5. Recency (0-10 points)
    now = datetime.now()
    
    # For news items
    if item.get("published_at"):
        try:
            pub_date = datetime.strptime(item["published_at"], "%Y-%m-%d")
            days_old = (now - pub_date).days
            if days_old <= 30:
                score += 10
                reasons.append(f"Recent: {days_old} days old")
        except:
            pass
    
    # For federal opportunities
    if item.get("close_date"):
        try:
            close_date = datetime.strptime(item["close_date"], "%m/%d/%Y")
            days_until = (close_date - now).days
            if 0 < days_until <= 60:
                score += 10
                reasons.append(f"Closing soon: {days_until} days")
        except:
            pass
    
    # Add flags for missing data
    if not item.get("title"):
        flags.append("Missing title")
    if item.get("source") == "grants_gov" and not item.get("agency"):
        flags.append("Missing agency")
    if not keywords:
        flags.append("No org keywords")
        
    return {
        "score": min(100, score),
        "reasons": reasons,
        "flags": flags
    }

def assemble_results(tokens: Dict) -> Dict:
    """
    Assemble all results with scoring
    
    Returns federal opportunities, news items, and context snapshot
    """
    # Get feeds
    federal = federal_feed(tokens)
    news = news_feed(tokens)
    snap = context_snapshot(tokens)
    
    # Score federal opportunities
    for item in federal:
        scoring = score_item(item, tokens, snap)
        item["score"] = scoring["score"]
        item["reasons"] = scoring["reasons"]
        item["flags"] = scoring["flags"]
    
    # Sort federal by score desc, then by date
    federal.sort(key=lambda x: (-x["score"], x.get("close_date", "")))
    
    # Score news items
    for item in news:
        scoring = score_item(item, tokens, snap)
        item["score"] = scoring["score"]
        item["reasons"] = scoring["reasons"]
        item["flags"] = scoring["flags"]
    
    # Sort news by score desc, then by date desc
    news.sort(key=lambda x: (-x["score"], x.get("published_at", "")), reverse=False)
    
    return {
        "federal": federal,
        "news": news,
        "context": snap
    }