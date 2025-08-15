"""
Enhanced AI Service
Backward-compatible wrapper that adds optimization while preserving existing functionality
"""

import logging
from typing import Dict, List, Optional, Any, Tuple

# Import existing services
try:
    from app.services.ai_service import AIService
    from app.services.ai_optimization_service import AIOptimizationService
    HAS_OPTIMIZATION = True
except ImportError:
    HAS_OPTIMIZATION = False
    AIOptimizationService = None

logger = logging.getLogger(__name__)

class EnhancedAIService:
    """
    Enhanced AI service that provides backward compatibility
    Gradually introduces optimization features without breaking existing code
    """
    
    def __init__(self, enable_optimization: bool = True):
        """Initialize with optional optimization"""
        self.original_service = AIService()
        
        # Try to enable optimization features
        self.optimization_enabled = enable_optimization and HAS_OPTIMIZATION
        self.optimization_service = None
        
        if self.optimization_enabled:
            try:
                self.optimization_service = AIOptimizationService()
                logger.info("Enhanced AI Service initialized with optimization")
            except Exception as e:
                logger.warning(f"Could not initialize optimization service: {e}")
                self.optimization_enabled = False
        
        if not self.optimization_enabled:
            logger.info("Enhanced AI Service running in compatibility mode")
    
    def is_enabled(self) -> bool:
        """Check if AI services are enabled"""
        return self.original_service.is_enabled()
    
    def match_grant(self, org_profile: Dict, grant: Dict, funder_profile: Dict = None) -> Tuple[Optional[int], Optional[str]]:
        """
        Grant matching with optional optimization
        Falls back gracefully to original service
        """
        if self.optimization_enabled and self.optimization_service:
            try:
                # Try optimized version
                return self.optimization_service.optimized_match_grant(org_profile, grant, funder_profile)
            except Exception as e:
                logger.warning(f"Optimized grant matching failed, using original: {e}")
        
        # Use original service
        return self.original_service.match_grant(org_profile, grant, funder_profile)
    
    def generate_grant_narrative(self, org_profile: Dict, grant: Optional[Dict],
                                section: str, custom_instructions: str = "") -> Optional[str]:
        """
        Narrative generation with optional optimization
        Falls back gracefully to original service
        """
        if self.optimization_enabled and self.optimization_service:
            try:
                # Try optimized version
                return self.optimization_service.optimized_generate_narrative(
                    org_profile, grant, section, custom_instructions
                )
            except Exception as e:
                logger.warning(f"Optimized narrative generation failed, using original: {e}")
        
        # Use original service
        return self.original_service.generate_grant_narrative(org_profile, grant, section, custom_instructions)
    
    def extract_grant_info(self, text: str) -> Optional[Dict]:
        """
        Grant info extraction with optional optimization
        Falls back gracefully to original service
        """
        if self.optimization_enabled and self.optimization_service:
            try:
                # Try optimized version
                return self.optimization_service.optimized_extract_grant_info(text)
            except Exception as e:
                logger.warning(f"Optimized grant extraction failed, using original: {e}")
        
        # Use original service
        return self.original_service.extract_grant_info(text)
    
    def analyze_text(self, prompt: str) -> Optional[Dict]:
        """Analyze text using original service (no optimization needed)"""
        return self.original_service.analyze_text(prompt)
    
    def improve_text(self, text: str, improvement_type: str) -> Optional[str]:
        """Improve text using original service"""
        return self.original_service.improve_text(text, improvement_type)
    
    def analyze_grant_success_factors(self, grant_data: Dict, org_data: Dict) -> Optional[Dict]:
        """Analyze grant success factors using original service"""
        return self.original_service.analyze_grant_success_factors(grant_data, org_data)
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics if available"""
        if self.optimization_enabled and self.optimization_service:
            try:
                return self.optimization_service.get_optimization_stats()
            except Exception as e:
                logger.error(f"Could not get optimization stats: {e}")
        
        return {
            "optimization_enabled": self.optimization_enabled,
            "message": "Optimization not available or disabled"
        }