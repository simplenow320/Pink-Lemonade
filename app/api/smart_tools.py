"""
Smart Tools API Endpoints
AI-powered tools for grant writing and impact reporting
"""

from flask import Blueprint, jsonify, request
from app.services.smart_tools import SmartToolsService
from app.models import Organization, Grant, db
import logging

logger = logging.getLogger(__name__)

smart_tools_bp = Blueprint('smart_tools', __name__, url_prefix='/api/smart-tools')
smart_tools = SmartToolsService()

# ============= GRANT PITCH ENDPOINTS =============

@smart_tools_bp.route('/pitch/generate', methods=['POST'])
def generate_pitch():
    """Generate a grant pitch (elevator, executive, or detailed)"""
    try:
        data = request.get_json() or {}
        org_id = data.get('org_id')
        grant_id = data.get('grant_id')
        pitch_type = data.get('pitch_type', 'elevator')
        
        if not org_id:
            return jsonify({
                'success': False,
                'error': 'org_id is required'
            }), 400
        
        if pitch_type not in ['elevator', 'executive', 'detailed']:
            return jsonify({
                'success': False,
                'error': 'Invalid pitch_type. Use: elevator, executive, or detailed'
            }), 400
        
        result = smart_tools.generate_grant_pitch(org_id, grant_id, pitch_type)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error generating pitch: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============= CASE FOR SUPPORT ENDPOINTS =============

@smart_tools_bp.route('/case/generate', methods=['POST'])
def generate_case():
    """Generate a comprehensive case for support"""
    try:
        data = request.get_json() or {}
        org_id = data.get('org_id')
        campaign_details = {
            'goal': data.get('campaign_goal', 100000),
            'purpose': data.get('campaign_purpose', 'general support'),
            'timeline': data.get('timeline', '12 months'),
            'target_donors': data.get('target_donors', 'major donors')
        }
        
        if not org_id:
            return jsonify({
                'success': False,
                'error': 'org_id is required'
            }), 400
        
        result = smart_tools.generate_case_for_support(org_id, campaign_details)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error generating case: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============= IMPACT REPORTING ENDPOINTS =============

@smart_tools_bp.route('/impact/generate', methods=['POST'])
def generate_impact_report():
    """Generate an impact report with metrics and stories from verified data"""
    try:
        data = request.get_json() or {}
        org_id = data.get('org_id')
        grant_id = data.get('grant_id')  # Optional - uses intake data if provided
        report_period = {
            'start': data.get('period_start', '2024-01-01'),
            'end': data.get('period_end', '2024-12-31')
        }
        metrics_data = data.get('metrics', {
            'grants_submitted': 10,
            'grants_won': 3,
            'funding_secured': 250000,
            'beneficiaries_served': 500,
            'programs_delivered': 5,
            'volunteer_hours': 0
        })
        
        if not org_id:
            return jsonify({
                'success': False,
                'error': 'org_id is required'
            }), 400
        
        result = smart_tools.generate_impact_report(
            org_id, 
            report_period, 
            metrics_data,
            grant_id=grant_id  # Pass grant_id to fetch intake data
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error generating impact report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============= QUICK TOOLS ENDPOINTS =============

@smart_tools_bp.route('/thank-you/generate', methods=['POST'])
def generate_thank_you():
    """Generate a personalized thank you letter"""
    try:
        data = request.get_json() or {}
        org_id = data.get('org_id')
        donor_info = {
            'name': data.get('donor_name', 'Valued Supporter'),
            'amount': data.get('donation_amount', 0),
            'purpose': data.get('donation_purpose', 'general support'),
            'is_recurring': data.get('is_recurring', False)
        }
        
        if not org_id:
            return jsonify({
                'success': False,
                'error': 'org_id is required'
            }), 400
        
        result = smart_tools.generate_thank_you_letter(org_id, donor_info)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error generating thank you: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tools_bp.route('/social/generate', methods=['POST'])
def generate_social_post():
    """Generate platform-optimized social media content"""
    try:
        data = request.get_json() or {}
        org_id = data.get('org_id')
        platform = data.get('platform', 'twitter')
        topic = data.get('topic', 'impact story')
        
        if not org_id:
            return jsonify({
                'success': False,
                'error': 'org_id is required'
            }), 400
        
        if platform not in ['twitter', 'facebook', 'instagram', 'linkedin']:
            return jsonify({
                'success': False,
                'error': 'Invalid platform. Use: twitter, facebook, instagram, or linkedin'
            }), 400
        
        result = smart_tools.generate_social_media_post(org_id, platform, topic)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error generating social post: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tools_bp.route('/newsletter/generate', methods=['POST'])
def generate_newsletter():
    """Generate comprehensive newsletter content with human-like writing"""
    try:
        data = request.get_json() or {}
        org_id = data.get('org_id')
        newsletter_details = {
            'theme': data.get('theme', 'Monthly Impact Update'),
            'month_year': data.get('month_year'),
            'focus_area': data.get('focus_area', 'general'),
            'target_audience': data.get('target_audience', 'donors and supporters')
        }
        
        if not org_id:
            return jsonify({
                'success': False,
                'error': 'org_id is required'
            }), 400
        
        result = smart_tools.generate_newsletter_content(org_id, newsletter_details)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error generating newsletter: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============= TOOL INFORMATION ENDPOINTS =============

@smart_tools_bp.route('/tools', methods=['GET'])
def get_available_tools():
    """Get list of all available Smart Tools"""
    try:
        tools = [
            {
                'id': 'grant_pitch',
                'name': 'Grant Pitch Generator',
                'description': 'Create compelling elevator, executive, or detailed pitches',
                'endpoint': '/api/smart-tools/pitch/generate',
                'icon': '🎯',
                'categories': ['fundraising', 'communication'],
                'time_to_generate': '10-15 seconds'
            },
            {
                'id': 'case_for_support',
                'name': 'Case for Support Builder',
                'description': 'Generate comprehensive fundraising case documents',
                'endpoint': '/api/smart-tools/case/generate',
                'icon': '📋',
                'categories': ['fundraising', 'strategy'],
                'time_to_generate': '20-30 seconds'
            },
            {
                'id': 'impact_report',
                'name': 'Impact Report Creator',
                'description': 'Transform metrics into compelling impact stories',
                'endpoint': '/api/smart-tools/impact/generate',
                'icon': '📊',
                'categories': ['reporting', 'evaluation'],
                'time_to_generate': '15-20 seconds'
            },
            {
                'id': 'thank_you_letter',
                'name': 'Thank You Letter Writer',
                'description': 'Personalized donor appreciation messages',
                'endpoint': '/api/smart-tools/thank-you/generate',
                'icon': '💌',
                'categories': ['stewardship', 'communication'],
                'time_to_generate': '5-10 seconds'
            },
            {
                'id': 'social_media',
                'name': 'Social Media Post Creator',
                'description': 'Platform-optimized social content',
                'endpoint': '/api/smart-tools/social/generate',
                'icon': '📱',
                'categories': ['marketing', 'communication'],
                'time_to_generate': '5-10 seconds'
            },
            {
                'id': 'newsletter',
                'name': 'Newsletter Content Creator',
                'description': 'Human-sounding newsletter content with storytelling',
                'endpoint': '/api/smart-tools/newsletter/generate',
                'icon': '📧',
                'categories': ['communication', 'stewardship'],
                'time_to_generate': '15-25 seconds'
            }
        ]
        
        return jsonify({
            'success': True,
            'tools': tools,
            'total': len(tools)
        })
        
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tools_bp.route('/stats/<int:org_id>', methods=['GET'])
def get_tool_usage_stats(org_id):
    """Get Smart Tools usage statistics for an organization"""
    try:
        from app.models import Narrative
        
        # Get usage counts by tool type
        narratives = Narrative.query.filter_by(
            org_id=org_id,
            ai_generated=True
        ).all()
        
        tool_usage = {
            'pitches': len([n for n in narratives if 'pitch' in n.section]),
            'cases': len([n for n in narratives if 'case' in n.section]),
            'reports': len([n for n in narratives if 'impact' in n.section]),
            'thank_yous': len([n for n in narratives if 'thank' in n.section]),
            'newsletters': len([n for n in narratives if 'newsletter' in n.section]),
            'social_posts': len([n for n in narratives if 'social_media' in n.section]),
            'total_generated': len(narratives)
        }
        
        # Calculate time saved (estimate 2 hours per document)
        time_saved_hours = tool_usage['total_generated'] * 2
        
        return jsonify({
            'success': True,
            'org_id': org_id,
            'usage': tool_usage,
            'time_saved_hours': time_saved_hours,
            'time_saved_days': round(time_saved_hours / 8, 1)
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500