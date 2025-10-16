"""
Grant Discovery Service V2 - Consolidated and Robust
Single source of truth for grant discovery, persistence, and AI scoring
Handles failures gracefully and ensures data accessibility for Smart Tools
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import or_, and_

from app import db
from app.models import Grant, Organization
from app.services.org_tokens import get_org_tokens

logger = logging.getLogger(__name__)


class GrantDiscoveryServiceV2:
    """
    Consolidated grant discovery pipeline:
    1. Fetch from multiple sources (with graceful fallbacks)
    2. Persist to database with deduplication
    3. Apply AI scoring when available
    4. Ensure data is accessible for Smart Tools
    """
    
    def __init__(self):
        self.matching_service = None
        self.ai_matcher = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize services with fallback support"""
        try:
            from app.services.matching_service import MatchingService
            self.matching_service = MatchingService()
        except Exception as e:
            logger.warning(f"MatchingService not available: {e}")
        
        try:
            from app.services.ai_grant_matcher import AIGrantMatcher
            self.ai_matcher = AIGrantMatcher()
        except Exception as e:
            logger.warning(f"AIGrantMatcher not available: {e}")
    
    def discover_and_persist(self, org_id: int, limit: int = 50, force_refresh: bool = False) -> Dict:
        """
        Complete discovery pipeline with robust error handling
        
        Args:
            org_id: Organization ID
            limit: Maximum grants to return
            force_refresh: Force refresh even if recent data exists
            
        Returns:
            Comprehensive results with grants, stats, and metadata
        """
        pipeline_start = datetime.utcnow()
        results = {
            'success': False,
            'organization': None,
            'grants': [],
            'discovery_stats': {
                'total_discovered': 0,
                'newly_added': 0,
                'updated': 0,
                'from_cache': 0,
                'ai_scored': 0,
                'sources_checked': [],
                'sources_failed': []
            },
            'errors': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # Step 1: Get organization (with error handling)
            org = self._get_organization(org_id)
            if not org:
                results['errors'].append(f'Organization {org_id} not found')
                return results
            
            results['organization'] = org.name
            
            # Step 2: Check for recent cached data unless force refresh
            if not force_refresh:
                cached_grants = self._get_recent_grants(org_id, limit)
                if cached_grants:
                    results['grants'] = [g.to_dict() for g in cached_grants]
                    results['discovery_stats']['from_cache'] = len(cached_grants)
                    results['success'] = True
                    logger.info(f"✅ Returning {len(cached_grants)} cached grants for org {org_id}")
                    return results
            
            # Step 3: Discover from external sources
            discovery_results = self._discover_from_sources(org_id)
            results['discovery_stats']['sources_checked'] = discovery_results['sources_checked']
            results['discovery_stats']['sources_failed'] = discovery_results['sources_failed']
            
            # Step 4: Persist discovered grants
            if discovery_results['grants']:
                persist_stats = self._persist_grants(org_id, discovery_results['grants'])
                results['discovery_stats'].update(persist_stats)
                
                # Step 5: Apply AI scoring (optional, with fallback)
                grant_ids = persist_stats.get('grant_ids', [])
                if grant_ids and self.ai_matcher:
                    scored_grants = self._apply_ai_scoring(org_id, grant_ids, limit)
                    results['grants'] = scored_grants
                    results['discovery_stats']['ai_scored'] = len([g for g in scored_grants if g.get('match_score', 0) > 0])
                else:
                    # Return grants without AI scoring
                    grants = Grant.query.filter(Grant.id.in_(grant_ids)).limit(limit).all()
                    results['grants'] = [g.to_dict() for g in grants]
            else:
                # No new discoveries, return existing grants
                existing_grants = self._get_recent_grants(org_id, limit)
                results['grants'] = [g.to_dict() for g in existing_grants]
                results['discovery_stats']['from_cache'] = len(existing_grants)
            
            results['success'] = True
            
            # Log performance
            duration = (datetime.utcnow() - pipeline_start).total_seconds()
            logger.info(f"✅ Discovery pipeline completed in {duration:.2f}s for org {org_id}")
            
        except Exception as e:
            logger.error(f"Error in discovery pipeline: {str(e)}")
            results['errors'].append(str(e))
            # Try to return cached data as fallback
            try:
                fallback_grants = self._get_recent_grants(org_id, limit)
                results['grants'] = [g.to_dict() for g in fallback_grants]
                results['discovery_stats']['from_cache'] = len(fallback_grants)
                results['success'] = True
                results['errors'].append('Using cached data due to discovery error')
            except:
                pass
        
        return results
    
    def _get_organization(self, org_id: int) -> Optional[Organization]:
        """Get organization with error handling"""
        try:
            return db.session.query(Organization).filter_by(id=org_id).first()
        except Exception as e:
            logger.error(f"Error getting organization {org_id}: {e}")
            return None
    
    def _get_recent_grants(self, org_id: int, limit: int) -> List[Grant]:
        """Get recently discovered grants for organization"""
        try:
            # Check if we have recent grants (last 24 hours)
            cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_grants = Grant.query.filter(
                Grant.org_id == org_id,
                Grant.updated_at >= cutoff
            ).order_by(Grant.match_score.desc().nullsfirst(), Grant.created_at.desc()).limit(limit).all()
            
            if len(recent_grants) >= 10:  # Enough cached data
                return recent_grants
            
            # Otherwise return any grants we have
            return Grant.query.filter_by(org_id=org_id)\
                .order_by(Grant.match_score.desc().nullsfirst(), Grant.created_at.desc())\
                .limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent grants: {e}")
            return []
    
    def _discover_from_sources(self, org_id: int) -> Dict:
        """
        Discover grants from all available sources
        Handles failures gracefully - if one source fails, others continue
        """
        results = {
            'grants': [],
            'sources_checked': [],
            'sources_failed': []
        }
        
        # Try to use MatchingService
        if self.matching_service:
            try:
                logger.info(f"🔍 Fetching from external sources for org {org_id}")
                external_results = self.matching_service.assemble(org_id, limit=30)
                
                # Collect grants from all sources
                for source_type in ['news', 'federal', 'foundation']:
                    if source_type in external_results:
                        source_grants = external_results.get(source_type, [])
                        if source_grants:
                            results['sources_checked'].append(source_type)
                            for grant_data in source_grants:
                                grant_data['source_type'] = source_type
                                results['grants'].append(grant_data)
                        else:
                            results['sources_checked'].append(source_type)
                            
            except Exception as e:
                logger.warning(f"MatchingService failed: {e}")
                results['sources_failed'].append('matching_service')
        
        # Fallback: Try to get from database if external fetch failed
        if not results['grants']:
            try:
                logger.info("Using database as fallback source")
                db_grants = Grant.query.filter_by(org_id=org_id).limit(20).all()
                for grant in db_grants:
                    grant_dict = grant.to_dict()
                    grant_dict['source_type'] = 'database'
                    results['grants'].append(grant_dict)
                results['sources_checked'].append('database')
            except Exception as e:
                logger.error(f"Database fallback failed: {e}")
                results['sources_failed'].append('database')
        
        logger.info(f"Discovery complete: {len(results['grants'])} grants from {results['sources_checked']}")
        return results
    
    def _persist_grants(self, org_id: int, grant_data_list: List[Dict]) -> Dict:
        """
        Persist grants to database with deduplication
        Returns stats and list of grant IDs for AI scoring
        """
        stats = {
            'total_discovered': len(grant_data_list),
            'newly_added': 0,
            'updated': 0,
            'duplicates': 0,
            'grant_ids': []
        }
        
        try:
            for grant_data in grant_data_list:
                source_type = grant_data.get('source_type', 'unknown')
                
                # Extract key fields based on source type
                if source_type == 'news':
                    title = grant_data.get('title', 'Untitled')
                    funder = grant_data.get('funder_name') or grant_data.get('publisher', 'Unknown')
                    url = grant_data.get('url', '')
                    description = grant_data.get('content', '')[:1000]
                    source_name = 'Candid News'
                elif source_type == 'federal':
                    title = grant_data.get('title', 'Federal Grant')
                    funder = grant_data.get('agency_name', 'Federal Agency')
                    url = grant_data.get('url', '')
                    description = grant_data.get('description', '')[:1000]
                    source_name = 'Grants.gov'
                elif source_type == 'foundation':
                    title = grant_data.get('title', 'Foundation Grant')
                    funder = grant_data.get('funder', 'Foundation')
                    url = grant_data.get('url', '')
                    description = grant_data.get('description', '')[:1000]
                    source_name = 'Foundation Directory'
                else:
                    # Database or unknown source
                    continue
                
                # Check for existing grant
                existing = None
                if url:
                    existing = Grant.query.filter_by(
                        org_id=org_id,
                        source_url=url
                    ).first()
                
                if not existing and title:
                    # Also check by title and funder
                    existing = Grant.query.filter_by(
                        org_id=org_id,
                        title=title,
                        funder=funder
                    ).first()
                
                if existing:
                    # Update if data changed
                    if existing.title != title or existing.updated_at < datetime.utcnow() - timedelta(days=1):
                        existing.title = title
                        existing.funder = funder
                        existing.updated_at = datetime.utcnow()
                        stats['updated'] += 1
                        stats['grant_ids'].append(existing.id)
                    else:
                        stats['duplicates'] += 1
                        # Still add to grant_ids for duplicates so they can be returned
                        stats['grant_ids'].append(existing.id)
                else:
                    # Create new grant
                    grant = Grant()
                    grant.org_id = org_id
                    grant.title = title
                    grant.funder = funder
                    grant.link = url
                    grant.source_url = url
                    grant.source_name = source_name
                    grant.eligibility = description
                    grant.status = 'discovery'
                    grant.application_stage = 'discovery'
                    grant.amount_min = grant_data.get('amount_min', 0)
                    grant.amount_max = grant_data.get('amount_max', 0)
                    grant.deadline = self._parse_deadline(grant_data.get('deadline') or grant_data.get('close_date'))
                    grant.geography = grant_data.get('region', '')
                    grant.created_at = datetime.utcnow()
                    grant.updated_at = datetime.utcnow()
                    
                    db.session.add(grant)
                    db.session.flush()  # Get the ID
                    stats['newly_added'] += 1
                    stats['grant_ids'].append(grant.id)
            
            db.session.commit()
            logger.info(f"Persisted grants: {stats}")
            
        except Exception as e:
            logger.error(f"Error persisting grants: {e}")
            db.session.rollback()
        
        return stats
    
    def _apply_ai_scoring(self, org_id: int, grant_ids: List[int], limit: int) -> List[Dict]:
        """Apply AI scoring with timeout protection"""
        try:
            # Limit scoring to prevent timeouts
            ids_to_score = grant_ids[:min(len(grant_ids), 15)]
            
            logger.info(f"🤖 AI scoring {len(ids_to_score)} grants for org {org_id}")
            scored = self.ai_matcher.match_grants_for_organization(
                org_id, 
                limit=limit, 
                grant_ids=ids_to_score
            )
            
            # If we got scored results, use them
            if scored:
                return scored
            
            # Otherwise return unscored grants
            grants = Grant.query.filter(Grant.id.in_(grant_ids)).limit(limit).all()
            return [g.to_dict() for g in grants]
            
        except Exception as e:
            logger.warning(f"AI scoring failed, returning unscored grants: {e}")
            grants = Grant.query.filter(Grant.id.in_(grant_ids)).limit(limit).all()
            return [g.to_dict() for g in grants]
    
    def _parse_deadline(self, deadline_str: Optional[str]) -> Optional[datetime]:
        """Parse deadline string to datetime"""
        if not deadline_str:
            return None
        
        try:
            # Handle ISO format
            if 'T' in deadline_str:
                return datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
            # Handle date only
            return datetime.strptime(deadline_str, '%Y-%m-%d')
        except:
            return None
    
    def get_grants_for_smart_tools(self, org_id: int, limit: int = 100) -> List[Dict]:
        """
        Get grants for Smart Tools usage
        Returns persisted grants with all necessary data
        """
        try:
            grants = Grant.query.filter_by(org_id=org_id)\
                .order_by(Grant.match_score.desc().nullsfirst(), Grant.created_at.desc())\
                .limit(limit).all()
            
            return [g.to_dict() for g in grants]
        except Exception as e:
            logger.error(f"Error getting grants for smart tools: {e}")
            return []