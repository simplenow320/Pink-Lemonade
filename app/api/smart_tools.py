"""Smart Tools API endpoints"""
from flask import Blueprint, jsonify, request, session
from app.services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('smart_tools', __name__, url_prefix='/api')

# Initialize services
ai_service = AIService()

@bp.route('/ai/generate-pitch', methods=['POST'])
def generate_pitch():
    """Generate grant pitch using AI"""
    try:
        data = request.get_json()
        org_data = data.get('org_data', {})
        grant_data = data.get('grant_data', {})
        
        # Generate pitch using AI service
        pitch = ai_service.generate_grant_narrative(
            org_profile=org_data,
            grant=grant_data,
            section='executive_summary'
        )
        
        result = {
            'pitch': pitch,
            'org_name': org_data.get('name'),
            'grant_title': grant_data.get('title')
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error generating pitch: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/ai/generate-case-support', methods=['POST'])
def generate_case_support():
    """Generate case for support using AI"""
    try:
        data = request.get_json()
        org_data = data.get('org_data', {})
        
        # Generate case for support
        case_statement = ai_service.generate_grant_narrative(
            org_profile=org_data,
            grant=None,
            section='statement_of_need'
        )
        
        result = {
            'case_statement': case_statement,
            'org_name': org_data.get('name')
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error generating case for support: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/ai/generate-impact-report', methods=['POST'])
def generate_impact_report():
    """Generate impact report using AI"""
    try:
        data = request.get_json()
        org_data = data.get('org_data', {})
        program_data = data.get('program_data', {})
        
        # Generate impact report with program data
        org_with_program = {**org_data}
        org_with_program['program_name'] = program_data.get('name', 'Program')
        org_with_program['program_description'] = program_data.get('description', '')
        org_with_program['beneficiaries'] = program_data.get('beneficiaries', '')
        
        report = ai_service.generate_grant_narrative(
            org_profile=org_with_program,
            grant=None,
            section='project_description'
        )
        
        result = {
            'report': report,
            'program_name': program_data.get('name')
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error generating impact report: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/ai/improve-text', methods=['POST'])
def improve_text():
    """Improve text using AI writing assistant"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        improvement_type = data.get('improvement_type', 'general')
        
        # Improve text using AI
        improved_text = ai_service.improve_text(text, improvement_type)
        
        return jsonify({
            'original': text,
            'improved': improved_text,
            'improvement_type': improvement_type
        }), 200
        
    except Exception as e:
        logger.error(f"Error improving text: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/smart-tools/templates', methods=['GET'])
def get_templates():
    """Get available Smart Tools templates"""
    return jsonify({
        'templates': [
            {
                'id': 'grant_pitch',
                'name': 'Grant Pitch',
                'description': 'Create compelling grant pitches tailored to specific opportunities',
                'icon': '💡'
            },
            {
                'id': 'case_support',
                'name': 'Case for Support',
                'description': 'Build comprehensive case statements for your organization',
                'icon': '📋'
            },
            {
                'id': 'impact_report',
                'name': 'Impact Report',
                'description': 'Generate data-driven impact reports for funders',
                'icon': '📊'
            },
            {
                'id': 'writing_assistant',
                'name': 'Writing Assistant',
                'description': 'Improve and refine your grant narratives',
                'icon': '✍️'
            },
            {
                'id': 'analytics',
                'name': 'Analytics Dashboard',
                'description': 'Track success rates and funding trends',
                'icon': '📈'
            },
            {
                'id': 'smart_reports',
                'name': 'Smart Reports',
                'description': 'Generate automated reports with AI insights',
                'icon': '🤖'
            }
        ]
    }), 200