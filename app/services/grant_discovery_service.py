"""
Grant Discovery Service - The Missing Bridge
Connects API Discovery → Database Persistence → AI Scoring
This is the critical service that completes the platform to 100%
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import or_, and_

from app import db
from app.models import Grant, Organization
from app.services.org_tokens import get_org_tokens
from app.services.matching_service import MatchingService
from app.services.ai_grant_matcher import AIGrantMatcher

logger = logging.getLogger(__name__)


class GrantDiscoveryService:
    """
    Orchestrates the complete grant discovery pipeline:
    1. Fetch from all external sources (Candid, Grants.gov, etc.)
    2. Persist to database with deduplication
    3. Apply AI scoring with REACTO system
    4. Return comprehensive, scored results
    """
    
    def __init__(self):
        self.matching_service = MatchingService()
        self.ai_matcher = AIGrantMatcher()
        
    def discover_and_persist(self, org_id: int, limit: int = 50) -> Dict:
        """
        Complete discovery pipeline for an organization
        
        Args:
            org_id: Organization ID
            limit: Max grants to return
            
        Returns:
            Dict with discovery stats and scored grants
        """
        # Start timing instrumentation
        pipeline_start = datetime.utcnow()
        timing_metrics = {}
        
        try:
            # Get fresh organization instance to avoid stale references
            # Use a new query to ensure we're not using a deleted object
            org = db.session.query(Organization).filter_by(id=org_id).first()
            if not org:
                logger.warning(f"Organization {org_id} not found - may have been deleted")
                return {
                    'success': False,
                    'error': f'Organization {org_id} not found'
                }
            
            # Step 1: Get org tokens for matching
            tokens_start = datetime.utcnow()
            tokens = get_org_tokens(org_id)
            timing_metrics['tokens_ms'] = (datetime.utcnow() - tokens_start).total_seconds() * 1000
            
            # Step 2: Fetch from all external APIs with timing
            logger.info(f"🌐 DISCOVERY STARTING for org {org_id}: {org.name} (limit={limit})")
            fetch_start = datetime.utcnow()
            external_results = self.matching_service.assemble(org_id, limit=min(limit, 20))  # Cap external fetch
            fetch_duration = (datetime.utcnow() - fetch_start).total_seconds()
            timing_metrics['external_fetch_ms'] = fetch_duration * 1000
            
            # Log fetch results
            news_count = len(external_results.get('news', []))
            federal_count = len(external_results.get('federal', []))
            foundation_count = len(external_results.get('foundation', []))
            logger.info(f"📊 EXTERNAL FETCH COMPLETED in {fetch_duration:.2f}s: {news_count} news, {federal_count} federal, {foundation_count} foundation")
            
            # Step 3: Persist discovered grants with timing
            persist_start = datetime.utcnow()
            stats = self._persist_grants(org_id, external_results)
            persist_duration = (datetime.utcnow() - persist_start).total_seconds()
            timing_metrics['persist_ms'] = persist_duration * 1000
            
            logger.info(f"💾 PERSISTENCE COMPLETED in {persist_duration:.2f}s: {stats}")
            
            # Step 4: DEFENSIVE AI SCORING - Skip if no new grants discovered
            discovered_grant_ids = stats.get('grant_ids_for_ai', [])
            
            if not discovered_grant_ids:
                # NO NEW GRANTS: Skip AI scoring entirely to prevent legacy fallback timeout
                logger.info(f"⏭️ SKIPPING AI SCORING: No new grants discovered for org {org_id} - returning recent grants")
                recent_grants = Grant.query.filter_by(org_id=org_id).order_by(Grant.created_at.desc()).limit(limit).all()
                scored_grants = [grant.to_dict() for grant in recent_grants]
                ai_status = 'skipped_no_new_discoveries'
                timing_metrics['ai_scoring_ms'] = 0
            else:
                # Cap AI scoring to prevent timeouts
                grants_to_score = discovered_grant_ids[:min(len(discovered_grant_ids), 20)]  # Hard cap at 20
                logger.info(f"🤖 AI SCORING STARTING: {len(grants_to_score)} grants (capped from {len(discovered_grant_ids)}) for org {org_id}")
                
                try:
                    ai_start = datetime.utcnow()
                    scored_grants = self.ai_matcher.match_grants_for_organization(
                        org_id, limit=limit, grant_ids=grants_to_score
                    )
                    
                    ai_duration = (datetime.utcnow() - ai_start).total_seconds()
                    timing_metrics['ai_scoring_ms'] = ai_duration * 1000
                    logger.info(f"✅ AI SCORING COMPLETED in {ai_duration:.2f}s for org {org_id}: {len(scored_grants)} grants scored")
                    ai_status = 'completed'
                except Exception as e:
                    logger.warning(f"⚠️ AI scoring failed, returning discovered grants without AI analysis: {e}")
                    # Fallback: return discovered grants without AI scoring
                    fallback_grants = Grant.query.filter(Grant.id.in_(grants_to_score)).all()
                    scored_grants = [grant.to_dict() for grant in fallback_grants]
                    ai_status = 'skipped_due_to_error'
                    timing_metrics['ai_scoring_ms'] = 0
            
            # Calculate total pipeline time
            pipeline_duration = (datetime.utcnow() - pipeline_start).total_seconds()
            timing_metrics['total_pipeline_ms'] = pipeline_duration * 1000
            
            # Step 5: Return comprehensive results with performance metrics
            logger.info(f"🏁 DISCOVERY PIPELINE COMPLETED in {pipeline_duration:.2f}s for org {org_id}")
            logger.info(f"⏱️ TIMING BREAKDOWN: External={timing_metrics['external_fetch_ms']:.0f}ms, Persist={timing_metrics['persist_ms']:.0f}ms, AI={timing_metrics['ai_scoring_ms']:.0f}ms")
            
            return {
                'success': True,
                'organization': org.name,
                'discovery_stats': stats,
                'top_matches': scored_grants,
                'ai_status': ai_status,
                'performance_metrics': {
                    'grants_discovered': stats.get('total_discovered', 0),
                    'grants_scored': len(discovered_grant_ids),
                    'optimization_active': len(discovered_grant_ids) > 0,
                    'timing_ms': timing_metrics
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in discover_and_persist for org {org_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _persist_grants(self, org_id: int, external_results: Dict) -> Dict:
        """
        Persist discovered grants to database with deduplication
        
        Args:
            org_id: Organization ID
            external_results: Results from MatchingService.assemble()
            
        Returns:
            Stats about persisted grants plus list of grant IDs for AI scoring
        """
        stats = {
            'total_discovered': 0,
            'newly_added': 0,
            'updated': 0,
            'duplicates_avoided': 0,
            'grant_ids_for_ai': []  # Track grants that need AI scoring
        }
        
        try:
            # Process news opportunities
            for item in external_results.get('news', []):
                grant = self._create_or_update_grant_from_news(item, org_id)
                if grant:
                    if grant['status'] == 'created':
                        stats['newly_added'] += 1
                        stats['grant_ids_for_ai'].append(grant['grant'].id)
                    elif grant['status'] == 'updated':
                        stats['updated'] += 1
                        stats['grant_ids_for_ai'].append(grant['grant'].id)
                    else:
                        stats['duplicates_avoided'] += 1
                    stats['total_discovered'] += 1
            
            # Process federal opportunities
            for item in external_results.get('federal', []):
                grant = self._create_or_update_grant_from_federal(item, org_id)
                if grant:
                    if grant['status'] == 'created':
                        stats['newly_added'] += 1
                        stats['grant_ids_for_ai'].append(grant['grant'].id)
                    elif grant['status'] == 'updated':
                        stats['updated'] += 1
                        stats['grant_ids_for_ai'].append(grant['grant'].id)
                    else:
                        stats['duplicates_avoided'] += 1
                    stats['total_discovered'] += 1
            
            # Process foundation opportunities
            for item in external_results.get('foundation', []):
                grant = self._create_or_update_grant_from_foundation(item, org_id)
                if grant:
                    if grant['status'] == 'created':
                        stats['newly_added'] += 1
                        stats['grant_ids_for_ai'].append(grant['grant'].id)
                    elif grant['status'] == 'updated':
                        stats['updated'] += 1
                        stats['grant_ids_for_ai'].append(grant['grant'].id)
                    else:
                        stats['duplicates_avoided'] += 1
                    stats['total_discovered'] += 1
            
            db.session.commit()
            logger.info(f"Persisted grants for org {org_id}: {stats}")
            logger.info(f"Grant IDs for AI scoring: {len(stats['grant_ids_for_ai'])} grants")
            
        except Exception as e:
            logger.error(f"Error persisting grants: {str(e)}")
            db.session.rollback()
            
        return stats
    
    def _create_or_update_grant_from_news(self, item: Dict, org_id: int) -> Optional[Dict]:
        """
        Create or update grant from Candid News item
        """
        try:
            # Extract key fields
            title = item.get('title', 'Untitled Opportunity')
            funder = item.get('funder_name') or item.get('publisher') or 'Unknown Funder'
            url = item.get('url', '')
            
            # Check for existing grant by URL and org
            existing = Grant.query.filter_by(
                source_url=url,
                org_id=org_id
            ).first()
            
            if existing:
                # Update if data changed
                if existing.title != title or existing.funder != funder:
                    existing.title = title
                    existing.funder = funder
                    existing.updated_at = datetime.utcnow()
                    return {'grant': existing, 'status': 'updated'}
                return {'grant': existing, 'status': 'duplicate'}
            
            # Create new grant
            grant = Grant()
            grant.org_id = org_id
            grant.title = title
            grant.funder = funder
            grant.link = url
            grant.source_url = url
            grant.source_name = 'Candid News'
            grant.amount_min = item.get('amount_min', 0)
            grant.amount_max = item.get('amount_max', 0)
            grant.deadline = self._parse_deadline(item.get('deadline'))
            grant.geography = item.get('region', '')
            grant.eligibility = item.get('description', '')[:1000] if item.get('description') else ''
            grant.status = 'discovery'
            grant.application_stage = 'discovery'
            grant.created_at = datetime.utcnow()
            grant.updated_at = datetime.utcnow()
            
            db.session.add(grant)
            return {'grant': grant, 'status': 'created'}
            
        except Exception as e:
            logger.error(f"Error creating grant from news: {str(e)}")
            return None
    
    def _create_or_update_grant_from_federal(self, item: Dict, org_id: int) -> Optional[Dict]:
        """
        Create or update grant from Grants.gov item
        """
        try:
            # Extract key fields
            title = item.get('title', 'Untitled Federal Grant')
            funder = item.get('agency_name', 'Federal Agency')
            opp_number = item.get('opportunity_number', '')
            
            # Check for existing grant by opportunity number
            existing = Grant.query.filter_by(
                source_name='Grants.gov',
                org_id=org_id
            ).filter(
                Grant.eligibility.contains(opp_number) if opp_number else Grant.id > 0
            ).first()
            
            if existing:
                # Update if data changed
                if existing.title != title:
                    existing.title = title
                    existing.updated_at = datetime.utcnow()
                    return {'grant': existing, 'status': 'updated'}
                return {'grant': existing, 'status': 'duplicate'}
            
            # Create new grant
            grant = Grant()
            grant.org_id = org_id
            grant.title = title
            grant.funder = funder
            grant.link = item.get('url', '')
            grant.source_url = item.get('url', '')
            grant.source_name = 'Grants.gov'
            grant.amount_min = item.get('award_floor', 0)
            grant.amount_max = item.get('award_ceiling', 0)
            grant.deadline = self._parse_deadline(item.get('close_date'))
            grant.geography = 'United States'
            grant.eligibility = f"Opportunity #{opp_number}. {item.get('description', '')[:900]}"
            grant.status = 'discovery'
            grant.application_stage = 'discovery'
            grant.created_at = datetime.utcnow()
            grant.updated_at = datetime.utcnow()
            
            db.session.add(grant)
            return {'grant': grant, 'status': 'created'}
            
        except Exception as e:
            logger.error(f"Error creating grant from federal: {str(e)}")
            return None
    
    def _create_or_update_grant_from_foundation(self, item: Dict, org_id: int) -> Optional[Dict]:
        """
        Create or update grant from foundation directory
        """
        try:
            # Extract key fields
            title = item.get('title', 'Foundation Grant Opportunity')
            funder = item.get('foundation_name', 'Foundation')
            url = item.get('website', '')
            
            # Check for existing grant
            existing = Grant.query.filter_by(
                funder=funder,
                org_id=org_id,
                source_name='Foundation Directory'
            ).first()
            
            if existing:
                return {'grant': existing, 'status': 'duplicate'}
            
            # Create new grant
            grant = Grant()
            grant.org_id = org_id
            grant.title = title
            grant.funder = funder
            grant.link = url
            grant.source_url = url
            grant.source_name = 'Foundation Directory'
            grant.amount_min = item.get('typical_grant_min', 0)
            grant.amount_max = item.get('typical_grant_max', 0)
            grant.deadline = None  # Foundations often have rolling deadlines
            grant.geography = item.get('geographic_focus', '')
            grant.eligibility = item.get('focus_areas', '')[:1000] if item.get('focus_areas') else ''
            grant.status = 'discovery'
            grant.application_stage = 'discovery'
            grant.created_at = datetime.utcnow()
            grant.updated_at = datetime.utcnow()
            
            db.session.add(grant)
            return {'grant': grant, 'status': 'created'}
            
        except Exception as e:
            logger.error(f"Error creating grant from foundation: {str(e)}")
            return None
    
    def _parse_deadline(self, deadline_str: Optional[str]) -> Optional[datetime]:
        """
        Parse deadline string to datetime
        """
        if not deadline_str:
            return None
            
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                try:
                    return datetime.strptime(deadline_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    def refresh_all_organizations(self) -> Dict:
        """
        Refresh grants for all active organizations (for background job)
        """
        try:
            # Get all organizations with names (basic filter)
            # Use fresh query to avoid stale references
            org_ids = db.session.query(Organization.id).filter(Organization.name != None).all()
            
            results = {
                'total_orgs': len(org_ids),
                'successful': 0,
                'failed': 0,
                'total_grants_discovered': 0,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            for (org_id,) in org_ids:
                try:
                    # Verify organization still exists before processing
                    org_exists = db.session.query(Organization.id).filter_by(id=org_id).first()
                    if not org_exists:
                        logger.warning(f"Skipping org {org_id} - no longer exists")
                        results['failed'] += 1
                        continue
                        
                    result = self.discover_and_persist(org_id, limit=30)
                    if result.get('success'):
                        results['successful'] += 1
                        results['total_grants_discovered'] += result['discovery_stats'].get('newly_added', 0)
                    else:
                        results['failed'] += 1
                except Exception as e:
                    logger.error(f"Error refreshing org {org_id}: {str(e)}")
                    results['failed'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error in refresh_all_organizations: {str(e)}")
            return {'error': str(e)}


# Singleton instance for background jobs
discovery_service = GrantDiscoveryService()