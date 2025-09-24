# app/services/scraper_service.py
from __future__ import annotations

import os
import logging
from datetime import datetime, date
from typing import Dict, Any, Iterable, List, Optional

import requests
from sqlalchemy import and_

from app import db
from app.models import Grant, Watchlist, WatchlistSource
from app.services.mode import is_live

log = logging.getLogger(__name__)

# ------------------------------
# Configuration (env-overridable)
# ------------------------------
GRANTSGOV_BASE = os.getenv("GRANTSGOV_BASE", "https://www.grants.gov/grantsws/rest/opportunities/search")
GRANTSGOV_PAGE_SIZE = int(os.getenv("GRANTSGOV_PAGE_SIZE", "50"))
HTTP_TIMEOUT = int(os.getenv("SCRAPER_HTTP_TIMEOUT", "25"))  # seconds
USER_AGENT = os.getenv("SCRAPER_UA", "PinkLemonade/1.0 (+contact admin)")

# ------------------------------
# Public entry points
# ------------------------------
def scheduled_scraping_job() -> None:
    """
    Runs on a schedule (e.g., daily at 05:00).
    - In LIVE mode: fetches from real connectors and upserts results.
    - In DEMO mode: skip (never fabricate data).
    """
    if not is_live():
        log.info("scheduled_scraping_job: DEMO mode detected; skipping live scraping.")
        return

    try:
        total = run_all_connectors_for_all_orgs()
        log.info("scheduled_scraping_job: finished. upserted_or_updated=%s", total)
    except Exception:
        log.exception("scheduled_scraping_job: unexpected error")


def run_now_for_org(org_id: int, query: Optional[str] = None) -> int:
    """
    Manual trigger (e.g., 'Run Now' button). Returns number of upserted/updated records.
    """

    return run_all_connectors_for_org(org_id=org_id, query=query)

# ------------------------------
# Core orchestration
# ------------------------------
def run_all_connectors_for_all_orgs() -> int:
    """
    Iterate orgs that have watchlists and run all enabled connectors.
    """
    count = 0
    org_ids = [row[0] for row in db.session.query(Watchlist.org_id).distinct().all()]
    for org_id in org_ids:
        try:
            count += run_all_connectors_for_org(org_id)
        except Exception:
            log.exception("run_all_connectors_for_all_orgs: failure for org_id=%s", org_id)
    return count


def run_all_connectors_for_org(org_id: int, query: Optional[str] = None) -> int:
    """
    Pulls enabled sources for the org's watchlists and upserts results.
    """
    total = 0
    watchlists: List[Watchlist] = Watchlist.query.filter_by(org_id=org_id).all()

    # Build simple terms from watchlists (e.g., cities)
    cities = [w.city for w in watchlists if (w.city or "").strip()]
    if query:
        # explicit query overrides city terms
        cities = [query]

    # Multiple data sources: Grants.gov, Federal Register, USAspending
    for term in cities or ["nonprofit"]:
        try:
            # 1. Grants.gov (fixed API)
            records = fetch_from_grants_gov(search_term=term, limit=GRANTSGOV_PAGE_SIZE)
            total += upsert_many(records, org_id=org_id)
            
            # 2. Federal Register
            federal_records = fetch_from_federal_register(search_term=term, limit=25)
            total += upsert_many(federal_records, org_id=org_id)
            
            # 3. USAspending
            usa_records = fetch_from_usaspending(search_term=term, limit=25)
            total += upsert_many(usa_records, org_id=org_id)
            
        except Exception:
            log.exception("run_all_connectors_for_org: connector failed for org_id=%s term=%s", org_id, term)

    # Example: custom WatchlistSource URLs (future adapters)
    # sources = (db.session.query(WatchlistSource)
    #            .join(Watchlist, WatchlistSource.watchlist_id == Watchlist.id)
    #            .filter(Watchlist.org_id == org_id, WatchlistSource.enabled.is_(True))
    #            .all())
    # for src in sources:
    #     try:
    #         # normalize vendor by src.name, call matching adapter here
    #         pass
    #     except Exception:
    #         log.exception("Adapter error for source %s (%s)", src.name, src.url)

    return total

# ------------------------------
# Connectors
# ------------------------------
def fetch_from_grants_gov(search_term: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Fixed Grants.gov search using working GSA Search API client.
    """
    try:
        # Use the working GrantsGovClient instead of broken direct API calls
        from app.services.grants_gov_client import get_grants_gov_client
        
        client = get_grants_gov_client()
        payload = {
            "keywords": [search_term],
            "limit": min(max(1, limit), 100),
            "offset": offset
        }
        
        opportunities = client.search_opportunities(payload)
        results: List[Dict[str, Any]] = []

        for item in opportunities:
            results.append(normalize_grant_record({
                "title": item.get("title", "Untitled Opportunity"),
                "funder": item.get("funder", "Unknown Agency"),
                "link": item.get("link", ""),
                "deadline": item.get("deadline"),
                "amount_min": item.get("amount_min"),
                "amount_max": item.get("amount_max"),
                "geography": item.get("geography", "US"),
                "eligibility": item.get("eligibility", ""),
                "source_name": "Grants.gov",
                "source_url": "https://www.grants.gov"
            }))

        log.info("fetch_from_grants_gov: term=%s fetched=%s grants (FIXED API)", search_term, len(results))
        return results

    except Exception as e:
        log.error("fetch_from_grants_gov: error with working client for term=%s: %s", search_term, e)
        return []


def fetch_from_federal_register(search_term: str, limit: int = 25) -> List[Dict[str, Any]]:
    """
    Fetch grant notices from Federal Register API
    """
    try:
        from app.services.federal_register_client import FederalRegisterClient
        
        client = FederalRegisterClient()
        notices = client.search_grant_notices(keywords=search_term, days_back=60)
        
        results: List[Dict[str, Any]] = []
        for notice in notices[:limit]:
            results.append(normalize_grant_record({
                "title": notice.get("title", ""),
                "funder": notice.get("funder", "Federal Register"),
                "link": notice.get("link", ""),
                "deadline": notice.get("deadline"),
                "amount_min": None,
                "amount_max": None,
                "geography": "US",
                "eligibility": notice.get("eligibility", ""),
                "source_name": "Federal Register",
                "source_url": "https://federalregister.gov"
            }))
        
        log.info("fetch_from_federal_register: term=%s fetched=%s grants", search_term, len(results))
        return results
        
    except Exception as e:
        log.error("fetch_from_federal_register: error for term=%s: %s", search_term, e)
        return []


def fetch_from_usaspending(search_term: str, limit: int = 25) -> List[Dict[str, Any]]:
    """
    Fetch grant awards from USAspending API
    """
    try:
        from app.services.usaspending_client import get_usaspending_client
        
        client = get_usaspending_client()
        awards = client.search_assistance_listings(keywords=search_term)
        
        results: List[Dict[str, Any]] = []
        for award in awards[:limit]:
            results.append(normalize_grant_record({
                "title": award.get("title", ""),
                "funder": award.get("funder", "USAspending"),
                "link": award.get("link", ""),
                "deadline": award.get("deadline"),
                "amount_min": award.get("amount_min"),
                "amount_max": award.get("amount_max"),
                "geography": award.get("geography", "US"),
                "eligibility": award.get("eligibility", ""),
                "source_name": "USAspending",
                "source_url": "https://usaspending.gov"
            }))
        
        log.info("fetch_from_usaspending: term=%s fetched=%s grants", search_term, len(results))
        return results
        
    except Exception as e:
        log.error("fetch_from_usaspending: error for term=%s: %s", search_term, e)
        return []

# ------------------------------
# Normalization & Upsert
# ------------------------------
def normalize_grant_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure a consistent schema for upsert_grant().
    """
    norm = {
        "title": (rec.get("title") or "").strip(),
        "funder": (rec.get("funder") or "").strip(),
        "link": rec.get("link"),
        "amount_min": _to_decimal(rec.get("amount_min")),
        "amount_max": _to_decimal(rec.get("amount_max")),
        "deadline": _to_iso_date(rec.get("deadline")),
        "geography": rec.get("geography"),
        "eligibility": rec.get("eligibility"),
        "source_name": rec.get("source_name") or "Unknown",
        "source_url": rec.get("source_url"),
    }
    return norm


def upsert_many(records: Iterable[Dict[str, Any]], org_id: Optional[int] = None) -> int:
    count = 0
    for r in records:
        if upsert_grant(r, org_id=org_id):
            count += 1
    return count


def upsert_grant(record: Dict[str, Any], org_id: Optional[int] = None) -> Optional[Grant]:
    """
    Insert or update a grant using a dedupe key of (title, funder, deadline).
    record fields (normalized): title, funder, link, amount_min, amount_max, deadline(ISO), geography, eligibility, source_name, source_url
    """
    try:
        if not record.get("title"):
            log.debug("upsert_grant: skipped record with empty title: %s", record)
            return None

        deadline_date: Optional[date] = None
        if record.get("deadline"):
            deadline_date = _parse_date(record["deadline"])

        existing = Grant.query.filter(
            and_(
                Grant.title == record["title"],
                Grant.funder == (record.get("funder") or None),
                Grant.deadline == deadline_date
            )
        ).first()

        if existing:
            existing.amount_min = record.get("amount_min")
            existing.amount_max = record.get("amount_max")
            existing.source_name = record.get("source_name")
            existing.source_url = record.get("source_url")
            existing.link = record.get("link")
            existing.geography = record.get("geography")
            existing.eligibility = record.get("eligibility")
            db.session.commit()
            return existing

        g = Grant()
        g.org_id = org_id
        g.title = record["title"] 
        g.funder = record.get("funder")
        g.link = record.get("link")
        g.amount_min = record.get("amount_min")
        g.amount_max = record.get("amount_max")
        g.deadline = deadline_date
        g.geography = record.get("geography")
        g.eligibility = record.get("eligibility")
        g.source_name = record.get("source_name")
        g.source_url = record.get("source_url")
        g.status = "idea"
        db.session.add(g)
        db.session.commit()
        return g

    except Exception:
        db.session.rollback()
        log.exception("upsert_grant: failed for record=%s", record)
        return None

# ------------------------------
# Helpers
# ------------------------------
def _to_iso_date(val: Any) -> Optional[str]:
    """Accepts ISO-like strings or date/datetime and returns YYYY-MM-DD or None."""
    if not val:
        return None
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, datetime):
        return val.date().isoformat()
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except Exception:
            continue
    # last resort: try python fromisoformat
    try:
        return datetime.fromisoformat(s).date().isoformat()
    except Exception:
        return None


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        pass
    # try common alt formats
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    return None


def _to_decimal(val: Any) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except Exception:
        return None


# ------------------------------
# Legacy API compatibility functions
# ------------------------------
def run_scraping_job(org_id: int = 1) -> Dict[str, Any]:
    """Legacy function for backward compatibility with existing API"""
    count = run_now_for_org(org_id)
    return {
        "status": "completed",
        "grants_discovered": count,
        "message": f"Upserted {count} grants for org {org_id}"
    }


def scrape_grants(source_url: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility with existing API"""

    
    # Use a default search term if none provided
    search_term = "nonprofit"
    if source_url:
        # Extract search term from URL if possible
        search_term = source_url
    
    records = fetch_from_grants_gov(search_term=search_term, limit=limit)
    return records