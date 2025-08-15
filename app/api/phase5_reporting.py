"""
Phase 5: Impact Reporting API endpoints
"""
from flask import Blueprint, request, jsonify, session
from app.services.phase5_impact_reporting import phase5_service
import logging

logger = logging.getLogger(__name__)

phase5_bp = Blueprint('phase5', __name__, url_prefix='/api/phase5')

@phase5_bp.route('/reports/create', methods=['POST'])
def create_report():
    """Create a new grant report"""
    try:
        data = request.json
        grant_id = data.get('grant_id')
        
        if not grant_id:
            return jsonify({'success': False, 'error': 'Grant ID required'}), 400
        
        result = phase5_service.create_grant_report(grant_id, data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase5_bp.route('/reports/list', methods=['GET'])
def list_reports():
    """List all grant reports"""
    try:
        # Mock data for demonstration
        reports = [
            {
                'id': 1,
                'grant_title': 'Federal Education Grant',
                'period': 'Q4 2024',
                'status': 'submitted',
                'submitted_date': '2024-12-31'
            },
            {
                'id': 2,
                'grant_title': 'Community Development Fund',
                'period': 'Q1 2025',
                'status': 'draft',
                'due_date': '2025-03-31'
            }
        ]
        
        return jsonify({
            'success': True,
            'reports': reports,
            'total': len(reports)
        })
        
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase5_bp.route('/qr/generate', methods=['POST'])
def generate_qr():
    """Generate QR code for participant survey"""
    try:
        data = request.json
        grant_id = data.get('grant_id', 1)
        program_name = data.get('program_name', 'Community Program')
        
        result = phase5_service.generate_qr_code(grant_id, program_name)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase5_bp.route('/survey/submit', methods=['POST'])
def submit_survey():
    """Submit participant survey response"""
    try:
        data = request.json
        result = phase5_service.submit_participant_survey(data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error submitting survey: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase5_bp.route('/survey/questions', methods=['GET'])
def get_survey_questions():
    """Get survey question structure"""
    try:
        result = phase5_service.get_survey_questions()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting questions: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase5_bp.route('/metrics/aggregate/<int:grant_id>', methods=['GET'])
def aggregate_metrics(grant_id):
    """Get aggregated impact metrics for a grant"""
    try:
        result = phase5_service.aggregate_impact_metrics(grant_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error aggregating metrics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase5_bp.route('/reports/export/<report_id>', methods=['GET'])
def export_report(report_id):
    """Export a grant report"""
    try:
        format = request.args.get('format', 'pdf')
        result = phase5_service.export_report(report_id, format)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error exporting report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase5_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    """Get reporting dashboard data"""
    try:
        result = phase5_service.get_reporting_dashboard()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@phase5_bp.route('/reports/submit/<report_id>', methods=['POST'])
def submit_report(report_id):
    """Submit a completed report"""
    try:
        data = request.json
        
        # Mock submission process
        result = {
            'success': True,
            'report_id': report_id,
            'status': 'submitted',
            'submitted_at': '2025-01-15T10:30:00',
            'confirmation_number': f'RPT-{report_id}-2025',
            'message': 'Report submitted successfully'
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error submitting report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500