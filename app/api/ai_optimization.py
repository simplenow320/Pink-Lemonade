"""
AI Optimization API Endpoints
Provides endpoints for monitoring and controlling AI cost optimization
"""

from flask import Blueprint, jsonify, request, current_app
import logging

# Import enhanced AI service
try:
    from app.services.enhanced_ai_service import EnhancedAIService
    HAS_ENHANCED_AI = True
except ImportError:
    HAS_ENHANCED_AI = False

logger = logging.getLogger(__name__)

# Create blueprint
ai_optimization_bp = Blueprint('ai_optimization', __name__)

# Global AI service instance (will be initialized on first use)
enhanced_ai_service = None

def get_enhanced_ai_service():
    """Get or create enhanced AI service instance"""
    global enhanced_ai_service
    if enhanced_ai_service is None and HAS_ENHANCED_AI:
        try:
            enhanced_ai_service = EnhancedAIService(enable_optimization=True)
        except Exception as e:
            logger.error(f"Could not initialize enhanced AI service: {e}")
    return enhanced_ai_service

@ai_optimization_bp.route('/api/ai-optimization/status', methods=['GET'])
def get_optimization_status():
    """Get AI optimization status and statistics"""
    try:
        service = get_enhanced_ai_service()
        if not service:
            return jsonify({
                "status": "disabled",
                "message": "AI optimization not available",
                "features": {
                    "smart_model_selection": False,
                    "react_prompts": False,
                    "cost_tracking": False
                }
            }), 200
        
        stats = service.get_optimization_stats()
        
        return jsonify({
            "status": "active" if service.optimization_enabled else "disabled",
            "message": "AI optimization running" if service.optimization_enabled else "Using original AI service",
            "features": {
                "smart_model_selection": service.optimization_enabled,
                "react_prompts": service.optimization_enabled,
                "cost_tracking": service.optimization_enabled
            },
            "statistics": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting optimization status: {e}")
        return jsonify({
            "status": "error",
            "message": f"Could not get optimization status: {str(e)}"
        }), 500

@ai_optimization_bp.route('/api/ai-optimization/cost-analysis', methods=['GET'])
def get_cost_analysis():
    """Get detailed cost analysis and savings report"""
    try:
        service = get_enhanced_ai_service()
        if not service or not service.optimization_enabled:
            return jsonify({
                "message": "Cost analysis not available - optimization disabled",
                "cost_analysis": None
            }), 200
        
        stats = service.get_optimization_stats()
        
        # Format for frontend display
        analysis = {
            "summary": {
                "total_requests": stats.get("total_requests", 0),
                "total_cost": f"${stats.get('total_cost', 0):.4f}",
                "cost_savings": stats.get("cost_savings", {}),
                "optimization_ratio": stats.get("optimization_ratio", {})
            },
            "model_breakdown": stats.get("model_breakdown", {}),
            "recommendations": []
        }
        
        # Add recommendations based on usage patterns
        if stats.get("optimization_ratio", {}).get("gpt_35_ratio", 0) < 0.6:
            analysis["recommendations"].append("Consider routing more simple tasks to GPT-3.5-turbo for additional savings")
        
        if stats.get("cost_savings", {}).get("percentage_saved", 0) < 50:
            analysis["recommendations"].append("Review task complexity scoring to optimize model selection")
        
        return jsonify({
            "message": "Cost analysis retrieved successfully",
            "cost_analysis": analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting cost analysis: {e}")
        return jsonify({
            "error": f"Could not get cost analysis: {str(e)}"
        }), 500

@ai_optimization_bp.route('/api/ai-optimization/test-prompt', methods=['POST'])
def test_optimized_prompt():
    """Test endpoint for comparing optimized vs original AI responses"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        service = get_enhanced_ai_service()
        if not service:
            return jsonify({"error": "AI optimization service not available"}), 503
        
        test_org = data.get('organization', {
            'name': 'Test Organization',
            'mission': 'Test mission',
            'focus_areas': ['education', 'youth development']
        })
        
        test_grant = data.get('grant', {
            'title': 'Test Grant',
            'funder': 'Test Funder',
            'focus_areas': 'education',
            'amount_max': 50000
        })
        
        # Test grant matching
        fit_score, reason = service.match_grant(test_org, test_grant)
        
        return jsonify({
            "message": "AI optimization test completed",
            "test_results": {
                "grant_matching": {
                    "fit_score": fit_score,
                    "reason": reason
                }
            },
            "optimization_active": service.optimization_enabled
        }), 200
        
    except Exception as e:
        logger.error(f"Error in optimization test: {e}")
        return jsonify({
            "error": f"Optimization test failed: {str(e)}"
        }), 500

@ai_optimization_bp.route('/api/ai-optimization/settings', methods=['GET', 'POST'])
def optimization_settings():
    """Get or update optimization settings"""
    try:
        service = get_enhanced_ai_service()
        if not service:
            return jsonify({"error": "AI optimization service not available"}), 503
        
        if request.method == 'GET':
            # Return current settings
            settings = {
                "optimization_enabled": service.optimization_enabled,
                "features": {
                    "smart_model_selection": True,
                    "react_framework": True,
                    "cost_tracking": True,
                    "fallback_protection": True
                },
                "model_preferences": {
                    "simple_tasks": "gpt-3.5-turbo",
                    "complex_tasks": "gpt-4o",
                    "target_cost_reduction": "60%"
                }
            }
            return jsonify(settings), 200
        
        elif request.method == 'POST':
            # Update settings (for future implementation)
            return jsonify({
                "message": "Settings update not yet implemented",
                "note": "Current settings are optimized for best cost/quality balance"
            }), 200
            
    except Exception as e:
        logger.error(f"Error handling optimization settings: {e}")
        return jsonify({
            "error": f"Could not handle settings request: {str(e)}"
        }), 500

# Health check endpoint
@ai_optimization_bp.route('/api/ai-optimization/health', methods=['GET'])
def health_check():
    """Health check for AI optimization service"""
    try:
        service = get_enhanced_ai_service()
        
        health_status = {
            "service_available": service is not None,
            "optimization_enabled": service.optimization_enabled if service else False,
            "ai_service_enabled": service.is_enabled() if service else False,
            "timestamp": "2025-08-15T03:00:00Z"
        }
        
        if service and service.is_enabled():
            return jsonify({
                "status": "healthy",
                "details": health_status
            }), 200
        else:
            return jsonify({
                "status": "degraded",
                "details": health_status,
                "message": "AI services not fully available"
            }), 200
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500