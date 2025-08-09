"""
AI Data Reader Service - Read-only data fetcher for building AI prompt data packs
Collects organizational data safely for AI context while respecting privacy boundaries
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app import db
from app.models import (
    Org, OrgVoiceProfile, OrgAsset, Grant, 
    OrgModule, Module, Watchlist
)
import logging

logger = logging.getLogger(__name__)

class AIDataReader:
    """Read-only service to build data packs for AI prompts"""
    
    def __init__(self, org_id: int):
        self.org_id = org_id
        self.org = Org.query.get(org_id)
        if not self.org:
            raise ValueError(f"Organization {org_id} not found")
    
    def build_data_pack(self, include_sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Build comprehensive data pack for AI prompts
        
        Args:
            include_sections: Optional list to limit sections included
                            ['profile', 'voice', 'assets', 'performance', 'grants', 'modules']
        """
        data_pack = {
            "org_id": self.org_id,
            "generated_at": datetime.utcnow().isoformat(),
            "data_version": "1.0"
        }
        
        # Define available sections
        all_sections = ['profile', 'voice', 'assets', 'performance', 'grants', 'modules']
        sections_to_include = include_sections if include_sections else all_sections
        
        try:
            # Core organization profile
            if 'profile' in sections_to_include:
                data_pack['organization'] = self._get_org_profile()
            
            # Voice and communication profile
            if 'voice' in sections_to_include:
                data_pack['voice_profile'] = self._get_voice_profile()
            
            # Approved assets and documents
            if 'assets' in sections_to_include:
                data_pack['assets'] = self._get_approved_assets()
            
            # Performance metrics and KPIs
            if 'performance' in sections_to_include:
                data_pack['performance'] = self._get_performance_metrics()
            
            # Grant history and preferences
            if 'grants' in sections_to_include:
                data_pack['grants'] = self._get_grant_context()
            
            # Enabled modules and capabilities
            if 'modules' in sections_to_include:
                data_pack['modules'] = self._get_enabled_modules()
                
        except Exception as e:
            logger.error(f"Error building data pack for org {self.org_id}: {str(e)}")
            data_pack['error'] = f"Partial data pack due to error: {str(e)}"
        
        return data_pack
    
    def _get_org_profile(self) -> Dict[str, Any]:
        """Get core organization profile information"""
        if not self.org:
            return {"error": "Organization not found"}
            
        return {
            "name": self.org.name,
            "mission": self.org.mission,
            "created_at": self.org.created_at.isoformat() if self.org.created_at else None,
            "profile_completeness": self._calculate_profile_completeness()
        }
    
    def _get_voice_profile(self) -> Dict[str, Any]:
        """Get organization voice and communication profile"""
        voice_profile = OrgVoiceProfile.query.filter_by(org_id=self.org_id).first()
        
        if not voice_profile:
            return {
                "status": "not_configured",
                "default_guidelines": "Professional, clear, mission-focused communication"
            }
        
        return {
            "status": "configured",
            "reading_level": voice_profile.reading_level,
            "formality": voice_profile.formality,
            "faith_language": voice_profile.faith_language,
            "sentence_length": voice_profile.sentence_length,
            "cta_style": voice_profile.cta_style,
            "common_phrases": voice_profile.common_phrases or [],
            "preferred_proof_points": voice_profile.preferred_proof_points or [],
            "last_updated": voice_profile.updated_at.isoformat() if voice_profile.updated_at else None
        }
    
    def _get_approved_assets(self) -> Dict[str, Any]:
        """Get approved organizational assets for AI context"""
        assets = OrgAsset.query.filter_by(
            org_id=self.org_id, 
            approved=True
        ).all()
        
        asset_summary = {
            "total_approved": len(assets),
            "by_type": {},
            "recent_additions": []
        }
        
        # Categorize assets
        for asset in assets:
            asset_type = asset.type or 'unknown'
            if asset_type not in asset_summary["by_type"]:
                asset_summary["by_type"][asset_type] = 0
            asset_summary["by_type"][asset_type] += 1
            
            # Include recent assets (last 30 days)
            if asset.added_at and asset.added_at > datetime.utcnow() - timedelta(days=30):
                asset_summary["recent_additions"].append({
                    "title": asset.title,
                    "type": asset.type,
                    "added_at": asset.added_at.isoformat()
                })
        
        return asset_summary
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics and KPIs"""
        # Grant success metrics
        total_grants = Grant.query.filter_by(org_id=self.org_id).count()
        awarded_grants = Grant.query.filter_by(org_id=self.org_id, status='awarded').count()
        active_applications = Grant.query.filter_by(org_id=self.org_id, status='submitted').count()
        
        # Recent activity (last 90 days)
        recent_cutoff = datetime.utcnow() - timedelta(days=90)
        recent_grants = Grant.query.filter(
            Grant.org_id == self.org_id,
            Grant.created_at >= recent_cutoff
        ).count()
        
        return {
            "grant_metrics": {
                "total_tracked": total_grants,
                "awarded": awarded_grants,
                "success_rate": round((awarded_grants / total_grants * 100), 1) if total_grants > 0 else 0,
                "active_applications": active_applications,
                "recent_activity_90d": recent_grants
            },
            "engagement_level": self._assess_engagement_level(recent_grants),
            "last_calculated": datetime.utcnow().isoformat()
        }
    
    def _get_grant_context(self) -> Dict[str, Any]:
        """Get grant history and preferences context"""
        # Get recent successful grants for pattern analysis
        successful_grants = Grant.query.filter_by(
            org_id=self.org_id, 
            status='awarded'
        ).order_by(Grant.updated_at.desc()).limit(5).all()
        
        # Get active watchlists for interest areas
        watchlists = Watchlist.query.filter_by(org_id=self.org_id).all()
        
        grant_context = {
            "recent_successes": [],
            "focus_areas": [],
            "funding_interests": []
        }
        
        # Analyze successful grants
        for grant in successful_grants:
            grant_context["recent_successes"].append({
                "title": grant.title,
                "funder": grant.funder,
                "amount_range": f"{grant.amount_min}-{grant.amount_max}" if grant.amount_min else "Not specified",
                "awarded_date": grant.updated_at.isoformat() if grant.updated_at else None
            })
        
        # Include watchlist interests
        for watchlist in watchlists:
            grant_context["focus_areas"].append({
                "name": watchlist.name,
                "description": getattr(watchlist, 'description', ''),
                "keywords": getattr(watchlist, 'keywords', [])
            })
        
        return grant_context
    
    def _get_enabled_modules(self) -> Dict[str, Any]:
        """Get enabled modules and organizational capabilities"""
        org_modules = db.session.query(OrgModule, Module).join(
            Module, OrgModule.module_key == Module.key
        ).filter(
            OrgModule.org_id == self.org_id,
            OrgModule.enabled == True
        ).all()
        
        enabled_capabilities = []
        for org_module, module in org_modules:
            enabled_capabilities.append({
                "key": module.key,
                "name": module.name,
                "description": module.description,
                "enabled_since": org_module.created_at.isoformat() if org_module.created_at else None
            })
        
        return {
            "enabled_count": len(enabled_capabilities),
            "capabilities": enabled_capabilities
        }
    
    def _calculate_profile_completeness(self) -> Dict[str, Any]:
        """Calculate organization profile completeness"""
        if not self.org:
            return {"score": 0, "error": "Organization not found"}
            
        required_fields = ['name', 'mission']
        completed_fields = sum(1 for field in required_fields if getattr(self.org, field))
        
        # Check for additional profile elements
        has_voice_profile = OrgVoiceProfile.query.filter_by(org_id=self.org_id).first() is not None
        has_assets = OrgAsset.query.filter_by(org_id=self.org_id, approved=True).count() > 0
        has_grants = Grant.query.filter_by(org_id=self.org_id).count() > 0
        
        completeness_score = (
            (completed_fields / len(required_fields) * 40) +  # 40% for basic info
            (20 if has_voice_profile else 0) +                 # 20% for voice profile
            (20 if has_assets else 0) +                        # 20% for assets
            (20 if has_grants else 0)                          # 20% for grant activity
        )
        
        return {
            "score": round(completeness_score, 1),
            "basic_info": completed_fields == len(required_fields),
            "voice_configured": has_voice_profile,
            "assets_uploaded": has_assets,
            "grant_activity": has_grants
        }
    
    def _assess_engagement_level(self, recent_activity: int) -> str:
        """Assess organization engagement level based on recent activity"""
        if recent_activity >= 10:
            return "high"
        elif recent_activity >= 3:
            return "moderate"
        elif recent_activity >= 1:
            return "low"
        else:
            return "inactive"

def build_org_data_pack(org_id: int, include_sections: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Convenience function to build data pack for an organization
    
    Args:
        org_id: Organization ID
        include_sections: Optional list of sections to include
        
    Returns:
        Complete data pack dictionary
    """
    try:
        reader = AIDataReader(org_id)
        return reader.build_data_pack(include_sections)
    except Exception as e:
        logger.error(f"Failed to build data pack for org {org_id}: {str(e)}")
        return {
            "org_id": org_id,
            "error": str(e),
            "generated_at": datetime.utcnow().isoformat()
        }