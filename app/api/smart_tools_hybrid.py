"""
Smart Tools Hybrid API
Provides both traditional (full AI) and hybrid (template + minimal AI) endpoints
Allows A/B testing and gradual migration
"""

from flask import Blueprint, request, jsonify
from app.api.auth import login_required, get_current_user
import logging

from app.models import Organization
from app.services.smart_tools_hybrid import SmartToolsHybridService
from app.services.smart_tools import SmartToolsService  # Original service
from app.services.case_for_support_hybrid import CaseForSupportHybridService
from app.services.impact_reporting_hybrid import ImpactReportingHybridService

logger = logging.getLogger(__name__)

smart_tools_hybrid_bp = Blueprint('smart_tools_hybrid', __name__)

# Initialize services
hybrid_service = SmartToolsHybridService()
original_service = SmartToolsService()
case_hybrid_service = CaseForSupportHybridService()
impact_hybrid_service = ImpactReportingHybridService()

@smart_tools_hybrid_bp.route('/compare', methods=['GET'])
def compare_approaches():
    """Compare traditional vs hybrid approach costs and performance"""
    return jsonify({
        'success': True,
        'comparison': {
            'traditional_ai': {
                'description': 'Full AI generation using GPT-3.5/GPT-4',
                'cost_per_generation': {
                    'thank_you': '$0.10-0.15',
                    'social_media': '$0.05-0.08',
                    'grant_pitch': '$0.20-0.50',
                    'newsletter': '$0.30-0.60'
                },
                'time_to_generate': '10-30 seconds',
                'consistency': 'Variable',
                'pros': ['Highly creative', 'Unique every time', 'Handles edge cases'],
                'cons': ['Expensive', 'Slow', 'Unpredictable output', 'AI hallucination risk']
            },
            'hybrid_approach': {
                'description': 'Templates (80%) + Minimal AI (20%)',
                'cost_per_generation': {
                    'thank_you': '$0.001-0.002',
                    'social_media': '$0-0.001',
                    'grant_pitch': '$0.01-0.05',
                    'newsletter': '$0.02-0.05'
                },
                'time_to_generate': '2-5 seconds',
                'consistency': 'High',
                'pros': ['95% cost reduction', '80% faster', 'Predictable output', 'Reusable components'],
                'cons': ['Less creative variety', 'Need template maintenance', 'Initial setup effort']
            },
            'recommendation': 'Start with hybrid for common tools (thank you, social), use AI for complex/custom needs'
        }
    })

@smart_tools_hybrid_bp.route('/thank-you/generate/hybrid', methods=['POST'])
@login_required
def generate_thank_you_hybrid():
    """Generate thank you letter using hybrid approach"""
    try:
        data = request.get_json()
        
        # Get current user
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get user's organization
        org_id = user.org_id
        if not org_id:
            return jsonify({'error': 'No organization associated with user'}), 400
        
        # Extract parameters
        donor_name = data.get('donor_name', 'Friend')
        donation_amount = data.get('donation_amount', '$100')
        donation_purpose = data.get('donation_purpose', '')
        donation_type = data.get('donation_type', 'contribution')
        additional_context = data.get('additional_context', '')
        
        # Generate using hybrid approach
        result = hybrid_service.generate_thank_you_letter(
            org_id=org_id,
            donor_name=donor_name,
            donation_amount=donation_amount,
            donation_purpose=donation_purpose,
            donation_type=donation_type,
            additional_context=additional_context
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating hybrid thank you letter: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tools_hybrid_bp.route('/thank-you/generate/compare', methods=['POST'])
@login_required
def compare_thank_you_generation():
    """Generate thank you letter using both methods for comparison"""
    try:
        data = request.get_json()
        
        # Get user's organization
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        org_id = user.org_id
        if not org_id:
            return jsonify({'error': 'No organization associated with user'}), 400
        
        # Extract parameters
        donor_name = data.get('donor_name', 'Friend')
        donation_amount = data.get('donation_amount', '$100')
        donation_purpose = data.get('donation_purpose', '')
        
        # Generate using hybrid approach
        import time
        
        # Hybrid generation
        start_hybrid = time.time()
        hybrid_result = hybrid_service.generate_thank_you_letter(
            org_id=org_id,
            donor_name=donor_name,
            donation_amount=donation_amount,
            donation_purpose=donation_purpose
        )
        hybrid_time = time.time() - start_hybrid
        
        # Traditional generation (if requested)
        traditional_result = None
        traditional_time = 0
        if data.get('include_traditional', False):
            start_traditional = time.time()
            traditional_result = original_service.generate_thank_you_letter(
                org_id=org_id,
                data={
                    'donor_name': donor_name,
                    'donation_amount': donation_amount,
                    'donation_purpose': donation_purpose
                }
            )
            traditional_time = time.time() - start_traditional
        
        return jsonify({
            'success': True,
            'hybrid': {
                'content': hybrid_result.get('content'),
                'generation_time': f"{hybrid_time:.2f} seconds",
                'estimated_cost': hybrid_result.get('estimated_cost', 0.002),
                'method': 'Template + Minimal AI'
            },
            'traditional': {
                'content': traditional_result.get('letter') if traditional_result else None,
                'generation_time': f"{traditional_time:.2f} seconds" if traditional_result else 'Not generated',
                'estimated_cost': 0.15,
                'method': 'Full AI Generation'
            } if traditional_result else None,
            'comparison': {
                'time_saved': f"{traditional_time - hybrid_time:.2f} seconds" if traditional_result else 'N/A',
                'cost_saved': f"${0.15 - hybrid_result.get('estimated_cost', 0.002):.3f}" if traditional_result else 'N/A',
                'speed_improvement': f"{traditional_time / hybrid_time:.1f}x faster" if traditional_result and hybrid_time > 0 else 'N/A'
            }
        })
        
    except Exception as e:
        logger.error(f"Error in comparison: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tools_hybrid_bp.route('/social/generate/hybrid', methods=['POST'])
@login_required
def generate_social_hybrid():
    """Generate social media post using hybrid approach"""
    try:
        data = request.get_json()
        
        # Get user's organization
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        org_id = user.org_id
        if not org_id:
            return jsonify({'error': 'No organization associated with user'}), 400
        
        # Extract parameters
        platform = data.get('platform', 'twitter')
        topic = data.get('topic', 'impact')
        post_type = data.get('post_type', 'impact')
        custom_message = data.get('custom_message', '')
        
        # Generate using hybrid approach
        result = hybrid_service.generate_social_media_post(
            org_id=org_id,
            platform=platform,
            topic=topic,
            post_type=post_type,
            custom_message=custom_message
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating hybrid social post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tools_hybrid_bp.route('/pitch/generate/hybrid', methods=['POST'])
@login_required
def generate_pitch_hybrid():
    """Generate grant pitch using hybrid approach"""
    try:
        data = request.get_json()
        
        # Get user's organization
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        org_id = user.org_id
        if not org_id:
            return jsonify({'error': 'No organization associated with user'}), 400
        
        # Extract parameters
        pitch_type = data.get('pitch_type', 'elevator')
        funder_name = data.get('funder_name')
        amount = data.get('funding_amount')
        grant_id = data.get('grant_id')
        funder_priorities = data.get('funder_priorities')
        
        # Generate using hybrid approach
        result = hybrid_service.generate_grant_pitch(
            org_id=org_id,
            pitch_type=pitch_type,
            funder_name=funder_name,
            amount=amount,
            grant_id=grant_id,
            funder_priorities=funder_priorities
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating hybrid pitch: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tools_hybrid_bp.route('/templates/library', methods=['GET'])
@login_required
def get_template_library():
    """Get available templates for user to preview"""
    try:
        from app.services.content_library import ContentLibrary
        library = ContentLibrary()
        
        return jsonify({
            'success': True,
            'templates': {
                'thank_you': library.get_thank_you_templates(),
                'grant_pitch': library.get_grant_pitch_frameworks(),
                'social_media': library.get_social_media_templates(),
                'newsletter': library.get_newsletter_sections()
            },
            'total_templates': {
                'thank_you': 3,  # first_time, recurring, major_gift
                'grant_pitch': 3,  # problem_solution, track_record, alignment_focused
                'social_media': 15,  # Various platform/type combinations
                'newsletter': 20   # Multiple section templates
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting template library: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tools_hybrid_bp.route('/settings/preference', methods=['POST'])
@login_required
def set_generation_preference():
    """Set user preference for generation method"""
    try:
        data = request.get_json()
        preference = data.get('preference', 'hybrid')  # 'hybrid', 'traditional', or 'auto'
        
        # Store preference (in production, save to user settings)
        # For now, just return confirmation
        return jsonify({
            'success': True,
            'preference_set': preference,
            'description': {
                'hybrid': 'Using templates with minimal AI for 95% cost savings',
                'traditional': 'Using full AI generation for maximum creativity',
                'auto': 'System chooses best method based on task complexity'
            }.get(preference, 'Unknown preference')
        })
        
    except Exception as e:
        logger.error(f"Error setting preference: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tools_hybrid_bp.route('/analytics/cost-savings', methods=['GET'])
@login_required
def get_cost_savings():
    """Calculate cost savings from using hybrid approach"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        org_id = user.org_id
        
        # Get usage statistics (mock data for demonstration)
        # In production, query actual usage from database
        usage_stats = {
            'thank_you_letters': 50,
            'social_posts': 200,
            'grant_pitches': 20,
            'newsletters': 12
        }
        
        # Calculate savings
        traditional_cost = (
            usage_stats['thank_you_letters'] * 0.15 +
            usage_stats['social_posts'] * 0.06 +
            usage_stats['grant_pitches'] * 0.35 +
            usage_stats['newsletters'] * 0.45
        )
        
        hybrid_cost = (
            usage_stats['thank_you_letters'] * 0.002 +
            usage_stats['social_posts'] * 0.001 +
            usage_stats['grant_pitches'] * 0.03 +
            usage_stats['newsletters'] * 0.04
        )
        
        savings = traditional_cost - hybrid_cost
        savings_percentage = (savings / traditional_cost * 100) if traditional_cost > 0 else 0
        
        return jsonify({
            'success': True,
            'usage': usage_stats,
            'costs': {
                'traditional_approach': f"${traditional_cost:.2f}",
                'hybrid_approach': f"${hybrid_cost:.2f}",
                'total_saved': f"${savings:.2f}",
                'savings_percentage': f"{savings_percentage:.0f}%"
            },
            'projection': {
                'monthly_savings': f"${savings:.2f}",
                'annual_savings': f"${savings * 12:.2f}"
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating savings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============= CASE FOR SUPPORT HYBRID ENDPOINTS =============

@smart_tools_hybrid_bp.route('/case/generate/<quality_level>', methods=['POST'])
@login_required
def generate_case_for_support(quality_level):
    """
    Generate consultant-quality Case for Support with deep personalization
    
    Quality levels:
    - template: Fast, basic structure with org data ($0.01)
    - consultant: Template + org data + minimal AI polish ($0.05) - RECOMMENDED
    - premium: Full AI customization for VIP campaigns ($0.50)
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get user's organization
        org_id = user.org_id
        if not org_id:
            return jsonify({'error': 'No organization associated with user'}), 400
        
        # Validate quality level
        if quality_level not in ['template', 'consultant', 'premium']:
            return jsonify({
                'error': 'Invalid quality level. Use: template, consultant, or premium'
            }), 400
        
        data = request.get_json() or {}
        
        # Extract campaign details
        campaign_details = {
            'goal': data.get('goal', 100000),
            'purpose': data.get('purpose', 'program expansion'),
            'timeline': data.get('timeline', '12 months'),
            'target_donors': data.get('target_donors', 'major donors'),
            'donor_type': data.get('donor_type', 'foundation'),  # foundation, corporate, individual
            'focus_area': data.get('focus_area', ''),
            'urgency_factor': data.get('urgency_factor', 'medium'),
            'specific_outcomes': data.get('specific_outcomes', []),
            'budget_breakdown': data.get('budget_breakdown', {}),
        }
        
        # Generate case for support
        result = case_hybrid_service.generate_case_for_support(
            org_id=org_id,
            campaign_details=campaign_details,
            quality_level=quality_level
        )
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error generating case for support: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============= IMPACT REPORTING HYBRID ENDPOINTS =============

@smart_tools_hybrid_bp.route('/impact/generate/<quality_level>', methods=['POST'])
@login_required
def generate_impact_report(quality_level):
    """
    Generate consultant-quality Impact Report using REAL beneficiary survey data
    
    Quality levels:
    - template: Data aggregation only ($0.01)
    - consultant: Template + real data + minimal AI storytelling ($0.05) - RECOMMENDED
    - premium: Full AI narrative analysis ($0.50)
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get user's organization
        org_id = user.org_id
        if not org_id:
            return jsonify({'error': 'No organization associated with user'}), 400
        
        # Validate quality level
        if quality_level not in ['template', 'consultant', 'premium']:
            return jsonify({
                'error': 'Invalid quality level. Use: template, consultant, or premium'
            }), 400
        
        data = request.get_json() or {}
        
        # Extract report parameters
        report_params = {
            'program_name': data.get('program_name'),  # Optional: specific program
            'date_range': data.get('date_range', 'last_quarter'),  # last_month, last_quarter, last_year
            'include_stories': data.get('include_stories', True),
            'include_visualizations': data.get('include_visualizations', True),
            'funder_name': data.get('funder_name'),  # Optional: customize for specific funder
        }
        
        # Generate impact report using real beneficiary data
        result = impact_hybrid_service.generate_impact_report(
            org_id=org_id,
            report_params=report_params,
            quality_level=quality_level
        )
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error generating impact report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500