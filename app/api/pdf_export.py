"""
PDF Export API Endpoints
Professional PDF generation for all Smart Tools content
"""

from flask import Blueprint, jsonify, request, send_file
from app.services.pdf_service import get_pdf_service
from app.services.smart_tools import SmartToolsService
from app.models import Organization, Grant, db
import io
import logging

logger = logging.getLogger(__name__)

pdf_export_bp = Blueprint('pdf_export', __name__, url_prefix='/api/pdf')
pdf_service = get_pdf_service()
smart_tools = SmartToolsService()

@pdf_export_bp.route('/grant-pitch/<int:org_id>', methods=['POST'])
def export_grant_pitch_pdf(org_id):
    """Generate and download grant pitch as PDF"""
    try:
        data = request.get_json() or {}
        grant_id = data.get('grant_id')
        pitch_type = data.get('pitch_type', 'elevator')
        
        # Get organization
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 404
        
        # Generate pitch using Smart Tools
        pitch_result = smart_tools.generate_grant_pitch(org_id, grant_id, pitch_type)
        
        if not pitch_result['success']:
            return jsonify(pitch_result), 500
        
        # Create PDF content
        pdf_content = {
            'title': f"Grant Pitch - {pitch_type.title()}",
            'sections': {
                'Hook': pitch_result.get('hook', ''),
                'Problem Statement': pitch_result.get('problem_statement', ''),
                'Solution Overview': pitch_result.get('solution_overview', ''),
                'Impact Evidence': pitch_result.get('impact_evidence', ''),
                'Call to Action': pitch_result.get('call_to_action', ''),
                'Full Pitch': pitch_result.get('pitch_text', '')
            }
        }
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_narrative_pdf(pdf_content, org.name)
        
        # Return PDF file
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)
        
        filename = f"grant_pitch_{pitch_type}_{org_id}.pdf"
        
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting grant pitch PDF: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@pdf_export_bp.route('/case-support/<int:org_id>', methods=['POST'])
def export_case_support_pdf(org_id):
    """Generate and download case for support as PDF"""
    try:
        data = request.get_json() or {}
        campaign_details = {
            'goal': data.get('campaign_goal', 100000),
            'purpose': data.get('campaign_purpose', 'general support'),
            'timeline': data.get('timeline', '12 months'),
            'target_donors': data.get('target_donors', 'major donors')
        }
        
        # Get organization
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 404
        
        # Generate case for support
        case_result = smart_tools.generate_case_for_support(org_id, campaign_details)
        
        if not case_result['success']:
            return jsonify(case_result), 500
        
        # Create PDF content
        pdf_content = {
            'campaign_details': campaign_details,
            'need_statement': case_result.get('need_statement', ''),
            'solution': case_result.get('solution_overview', ''),
            'impact': case_result.get('impact_potential', ''),
            'call_to_action': case_result.get('call_to_action', ''),
            'donor_benefits': case_result.get('donor_benefits', ''),
            'stewardship_plan': case_result.get('stewardship_plan', '')
        }
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_case_support_pdf(pdf_content, org.name)
        
        # Return PDF file
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)
        
        filename = f"case_for_support_{org_id}.pdf"
        
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting case support PDF: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@pdf_export_bp.route('/impact-report/<int:org_id>', methods=['POST'])
def export_impact_report_pdf(org_id):
    """Generate and download impact report as PDF"""
    try:
        data = request.get_json() or {}
        report_period = {
            'start': data.get('period_start', '2024-01-01'),
            'end': data.get('period_end', '2024-12-31')
        }
        metrics_data = data.get('metrics', {
            'grants_submitted': 10,
            'grants_won': 3,
            'funding_secured': 250000,
            'beneficiaries_served': 500,
            'programs_delivered': 5
        })
        
        # Get organization
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 404
        
        # Generate impact report
        report_result = smart_tools.generate_impact_report(
            org_id, 
            report_period, 
            metrics_data
        )
        
        if not report_result['success']:
            return jsonify(report_result), 500
        
        # Create PDF content
        pdf_content = {
            'period': report_period,
            'executive_summary': report_result.get('executive_summary', ''),
            'metrics': metrics_data,
            'success_stories': report_result.get('success_stories', []),
            'challenges_overcome': report_result.get('challenges_overcome', []),
            'recommendations': report_result.get('recommendations', [])
        }
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_impact_report_pdf(pdf_content, org.name)
        
        # Return PDF file
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)
        
        filename = f"impact_report_{org_id}.pdf"
        
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting impact report PDF: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@pdf_export_bp.route('/grant-matches/<int:org_id>', methods=['GET'])
def export_grant_matches_pdf(org_id):
    """Export grant matches as PDF report"""
    try:
        # Get organization
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 404
        
        # Get grants for organization
        grants = Grant.query.filter_by(organization_id=org_id).order_by(Grant.match_score.desc()).limit(50).all()
        
        # Convert grants to dict format
        grants_data = []
        for grant in grants:
            grants_data.append({
                'title': grant.title,
                'funder': grant.funder,
                'amount': grant.amount,
                'deadline': grant.deadline.strftime('%Y-%m-%d') if grant.deadline else 'N/A',
                'match_score': grant.match_score
            })
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_grant_report_pdf(grants_data, org.name)
        
        # Return PDF file
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)
        
        filename = f"grant_matches_{org_id}.pdf"
        
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting grant matches PDF: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@pdf_export_bp.route('/thank-you/<int:org_id>', methods=['POST'])
def export_thank_you_pdf(org_id):
    """Generate and download thank you letter as PDF"""
    try:
        data = request.get_json() or {}
        donor_info = {
            'name': data.get('donor_name', 'Valued Supporter'),
            'amount': data.get('donation_amount', 0),
            'date': data.get('donation_date'),
            'campaign': data.get('campaign', 'general support')
        }
        
        # Get organization
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 404
        
        # Generate thank you letter
        thank_you_result = smart_tools.generate_thank_you_letter(org_id, donor_info)
        
        if not thank_you_result['success']:
            return jsonify(thank_you_result), 500
        
        # Create PDF content
        pdf_content = {
            'title': 'Thank You Letter',
            'sections': {
                'Letter': thank_you_result.get('letter_text', ''),
                'Impact Summary': thank_you_result.get('impact_summary', ''),
                'Next Steps': thank_you_result.get('next_steps', '')
            }
        }
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_narrative_pdf(pdf_content, org.name)
        
        # Return PDF file
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)
        
        filename = f"thank_you_letter_{org_id}.pdf"
        
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting thank you PDF: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@pdf_export_bp.route('/newsletter/<int:org_id>', methods=['POST'])
def export_newsletter_pdf(org_id):
    """Generate and download newsletter as PDF"""
    try:
        data = request.get_json() or {}
        newsletter_data = {
            'month': data.get('month', 'Current'),
            'highlights': data.get('highlights', []),
            'upcoming_events': data.get('upcoming_events', [])
        }
        
        # Get organization
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({'success': False, 'error': 'Organization not found'}), 404
        
        # Generate newsletter
        newsletter_result = smart_tools.generate_newsletter(org_id, newsletter_data)
        
        if not newsletter_result['success']:
            return jsonify(newsletter_result), 500
        
        # Create PDF content
        pdf_content = {
            'title': f"Newsletter - {newsletter_data['month']}",
            'sections': {
                'Introduction': newsletter_result.get('introduction', ''),
                'Highlights': newsletter_result.get('highlights_text', ''),
                'Upcoming Events': newsletter_result.get('events_text', ''),
                'Call to Action': newsletter_result.get('call_to_action', '')
            }
        }
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_narrative_pdf(pdf_content, org.name)
        
        # Return PDF file
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)
        
        filename = f"newsletter_{org_id}.pdf"
        
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting newsletter PDF: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500