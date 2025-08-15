"""
PHASE 4: AI Writing Assistant API Endpoints
"""
from flask import Blueprint, request, jsonify, session
from app.services.phase4_ai_writer import phase4_writer
import logging

logger = logging.getLogger(__name__)

phase4_bp = Blueprint('phase4_writer', __name__)

@phase4_bp.route('/api/phase4/writer/narrative', methods=['POST'])
def generate_narrative():
    """Generate grant narrative"""
    try:
        user_id = session.get('user_id', 1)
        data = request.json
        
        grant_id = data.get('grant_id')
        narrative_type = data.get('narrative_type', 'mission_alignment')
        
        if not grant_id:
            return jsonify({'success': False, 'error': 'Grant ID required'}), 400
        
        result = phase4_writer.generate_narrative(user_id, grant_id, narrative_type)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating narrative: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase4_bp.route('/api/phase4/writer/executive-summary', methods=['POST'])
def create_executive_summary():
    """Create executive summary"""
    try:
        user_id = session.get('user_id', 1)
        data = request.json
        
        grant_id = data.get('grant_id')
        max_words = data.get('max_words', 250)
        
        if not grant_id:
            return jsonify({'success': False, 'error': 'Grant ID required'}), 400
        
        result = phase4_writer.create_executive_summary(user_id, grant_id, max_words)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating executive summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase4_bp.route('/api/phase4/writer/impact', methods=['POST'])
def write_impact_statement():
    """Generate impact statement"""
    try:
        user_id = session.get('user_id', 1)
        data = request.json
        
        result = phase4_writer.write_impact_statement(user_id, data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error writing impact statement: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase4_bp.route('/api/phase4/writer/budget-narrative', methods=['POST'])
def generate_budget_narrative():
    """Generate budget narrative"""
    try:
        user_id = session.get('user_id', 1)
        budget_data = request.json
        
        result = phase4_writer.generate_budget_narrative(user_id, budget_data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating budget narrative: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase4_bp.route('/api/phase4/writer/optimize', methods=['POST'])
def optimize_content():
    """Optimize existing content"""
    try:
        data = request.json
        
        content = data.get('content')
        optimization_type = data.get('optimization_type', 'clarity')
        target = data.get('target')
        
        if not content:
            return jsonify({'success': False, 'error': 'Content required'}), 400
        
        result = phase4_writer.optimize_content(content, optimization_type, target)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error optimizing content: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase4_bp.route('/api/phase4/writer/templates', methods=['GET'])
def get_templates():
    """Get document templates"""
    try:
        template_type = request.args.get('type')
        result = phase4_writer.get_templates(template_type)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500