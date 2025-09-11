"""
Mock Impact Reporting QR Code and Unique URL API
Two-sided impact reporting system without external QRCode dependency
"""

import io
import base64
import secrets
from flask import Blueprint, jsonify, request, url_for
from app.models import db
from app.models_extended import Survey, SurveyResponse
import logging

logger = logging.getLogger(__name__)

impact_qr_bp = Blueprint('impact_qr', __name__, url_prefix='/api/impact-qr')

def generate_mock_qr_code(data):
    """Generate a mock QR code (placeholder SVG)"""
    # Return a simple SVG placeholder for QR code
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
        <rect width="200" height="200" fill="white"/>
        <rect x="10" y="10" width="180" height="180" fill="none" stroke="black" stroke-width="2"/>
        <text x="100" y="100" text-anchor="middle" font-family="Arial" font-size="14">
            QR Code
        </text>
        <text x="100" y="120" text-anchor="middle" font-family="Arial" font-size="10">
            {data[:20]}...
        </text>
    </svg>
    """
    return base64.b64encode(svg.encode()).decode()

@impact_qr_bp.route('/create-survey', methods=['POST'])
def create_program_survey():
    """Create program-specific survey with mock QR codes and unique URLs"""
    try:
        data = request.get_json() or {}
        org_id = data.get('org_id')
        program_name = data.get('program_name')
        program_type = data.get('program_type', 'general')
        
        if not org_id or not program_name:
            return jsonify({
                'success': False,
                'error': 'org_id and program_name are required'
            }), 400
        
        # Generate unique survey token
        survey_token = secrets.token_urlsafe(16)
        
        # Create survey record
        survey = Survey()
        survey.org_id = org_id
        survey.title = f"{program_name} Impact Survey"
        survey.description = f"Help us measure the impact of our {program_name} program"
        survey.program_name = program_name
        survey.program_type = program_type
        survey.survey_token = survey_token
        survey.is_active = True
        
        # Default questions for program impact
        survey.questions_json = [
            {"type": "dropdown", "question": "Which program did you participate in?", 
             "options": [program_name, "Other"]},
            {"type": "rating", "question": "How would you rate your experience before the program?", 
             "scale": 5},
            {"type": "rating", "question": "How would you rate your situation after the program?", 
             "scale": 5},
            {"type": "text", "question": "Please share your story - how did this program impact you?"},
            {"type": "checkbox", "question": "What skills or knowledge did you gain?", 
             "options": ["Technical skills", "Life skills", "Career development", "Personal growth", "Other"]},
            {"type": "rating", "question": "How satisfied are you with the program?", "scale": 5}
        ]
        
        db.session.add(survey)
        db.session.commit()
        
        # Generate URLs
        base_url = request.host_url.rstrip('/')
        survey_url = f"{base_url}/impact/survey/{survey_token}"
        
        # Generate mock QR code
        qr_image = generate_mock_qr_code(survey_url)
        
        return jsonify({
            'success': True,
            'survey_id': survey.id,
            'survey_token': survey_token,
            'survey_url': survey_url,
            'qr_code': f"data:image/svg+xml;base64,{qr_image}",
            'qr_code_mock': True,
            'message': 'Survey created with mock QR code (install qrcode package for real QR codes)'
        })
        
    except Exception as e:
        logger.error(f"Error creating survey: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@impact_qr_bp.route('/surveys/<org_id>', methods=['GET'])
def get_organization_surveys(org_id):
    """Get all surveys for an organization"""
    try:
        surveys = Survey.query.filter_by(org_id=org_id).order_by(Survey.created_at.desc()).all()
        
        survey_list = []
        for survey in surveys:
            survey_data = {
                'id': survey.id,
                'title': survey.title,
                'program_name': survey.program_name,
                'token': survey.survey_token,
                'is_active': survey.is_active,
                'response_count': SurveyResponse.query.filter_by(survey_id=survey.id).count(),
                'created_at': survey.created_at.isoformat() if survey.created_at else None
            }
            survey_list.append(survey_data)
        
        return jsonify({
            'success': True,
            'surveys': survey_list
        })
        
    except Exception as e:
        logger.error(f"Error getting surveys: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@impact_qr_bp.route('/survey/<token>', methods=['GET'])
def get_survey_by_token(token):
    """Get survey details by token (for public access)"""
    try:
        survey = Survey.query.filter_by(survey_token=token, is_active=True).first()
        
        if not survey:
            return jsonify({
                'success': False,
                'error': 'Survey not found or inactive'
            }), 404
        
        return jsonify({
            'success': True,
            'survey': {
                'id': survey.id,
                'title': survey.title,
                'description': survey.description,
                'program_name': survey.program_name,
                'questions': survey.questions_json
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting survey: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@impact_qr_bp.route('/survey/<token>/submit', methods=['POST'])
def submit_survey_response(token):
    """Submit response to a survey (public endpoint)"""
    try:
        survey = Survey.query.filter_by(survey_token=token, is_active=True).first()
        
        if not survey:
            return jsonify({
                'success': False,
                'error': 'Survey not found or inactive'
            }), 404
        
        data = request.get_json() or {}
        responses = data.get('responses', {})
        respondent_info = data.get('respondent_info', {})
        
        # Create survey response
        response = SurveyResponse()
        response.survey_id = survey.id
        response.responses_json = responses
        response.respondent_name = respondent_info.get('name')
        response.respondent_email = respondent_info.get('email')
        response.respondent_phone = respondent_info.get('phone')
        
        # Extract impact story if present
        for key, value in responses.items():
            if 'story' in key.lower() or 'impact' in key.lower():
                response.impact_story = value
                break
        
        db.session.add(response)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Thank you for sharing your story!',
            'response_id': response.id
        })
        
    except Exception as e:
        logger.error(f"Error submitting response: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@impact_qr_bp.route('/survey/<survey_id>/responses', methods=['GET'])
def get_survey_responses(survey_id):
    """Get all responses for a survey"""
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({
                'success': False,
                'error': 'Survey not found'
            }), 404
        
        responses = SurveyResponse.query.filter_by(survey_id=survey_id).order_by(SurveyResponse.created_at.desc()).all()
        
        response_list = []
        for resp in responses:
            response_data = {
                'id': resp.id,
                'responses': resp.responses_json,
                'impact_story': resp.impact_story,
                'respondent_name': resp.respondent_name,
                'created_at': resp.created_at.isoformat() if resp.created_at else None
            }
            response_list.append(response_data)
        
        # Calculate analytics
        analytics = calculate_survey_analytics(responses)
        
        return jsonify({
            'success': True,
            'survey': {
                'title': survey.title,
                'program_name': survey.program_name
            },
            'responses': response_list,
            'analytics': analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting responses: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@impact_qr_bp.route('/generate-impact-report', methods=['POST'])
def generate_impact_report():
    """Generate AI-powered impact report from survey responses"""
    try:
        data = request.get_json() or {}
        survey_id = data.get('survey_id')
        org_id = data.get('org_id')
        
        if not survey_id or not org_id:
            return jsonify({
                'success': False,
                'error': 'survey_id and org_id are required'
            }), 400
        
        # Get survey and responses
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({
                'success': False,
                'error': 'Survey not found'
            }), 404
        
        responses = SurveyResponse.query.filter_by(survey_id=survey_id).all()
        
        if not responses:
            return jsonify({
                'success': False,
                'error': 'No responses found for this survey'
            }), 404
        
        # Collect impact stories
        impact_stories = []
        for resp in responses:
            if resp.impact_story:
                impact_stories.append({
                    'story': resp.impact_story,
                    'name': resp.respondent_name or 'Anonymous'
                })
        
        # Calculate metrics
        analytics = calculate_survey_analytics(responses)
        
        # Generate mock impact report
        report = {
            'title': f"{survey.program_name} Impact Report",
            'program': survey.program_name,
            'total_participants': len(responses),
            'satisfaction_rate': analytics.get('average_satisfaction', 0),
            'improvement_rate': analytics.get('improvement_rate', 0),
            'impact_stories': impact_stories[:5],  # Top 5 stories
            'key_outcomes': analytics.get('key_outcomes', []),
            'recommendations': [
                'Continue program with current structure',
                'Expand reach to more participants',
                'Consider additional support services'
            ]
        }
        
        return jsonify({
            'success': True,
            'report': report,
            'message': 'Impact report generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def calculate_survey_analytics(responses):
    """Calculate analytics from survey responses"""
    analytics = {
        'total_responses': len(responses),
        'average_satisfaction': 0,
        'improvement_rate': 0,
        'key_outcomes': [],
        'skills_gained': {}
    }
    
    if not responses:
        return analytics
    
    satisfaction_scores = []
    before_scores = []
    after_scores = []
    
    for resp in responses:
        if resp.responses_json:
            for key, value in resp.responses_json.items():
                if 'satisfaction' in key.lower() and isinstance(value, (int, float)):
                    satisfaction_scores.append(value)
                elif 'before' in key.lower() and isinstance(value, (int, float)):
                    before_scores.append(value)
                elif 'after' in key.lower() and isinstance(value, (int, float)):
                    after_scores.append(value)
    
    if satisfaction_scores:
        analytics['average_satisfaction'] = sum(satisfaction_scores) / len(satisfaction_scores)
    
    if before_scores and after_scores:
        avg_before = sum(before_scores) / len(before_scores)
        avg_after = sum(after_scores) / len(after_scores)
        analytics['improvement_rate'] = ((avg_after - avg_before) / avg_before) * 100 if avg_before > 0 else 0
    
    analytics['key_outcomes'] = [
        f"{analytics['total_responses']} participants reached",
        f"{analytics['average_satisfaction']:.1f}/5 average satisfaction",
        f"{analytics['improvement_rate']:.0f}% improvement reported"
    ]
    
    return analytics