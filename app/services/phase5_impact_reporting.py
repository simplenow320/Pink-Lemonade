"""
Phase 5: Impact Reporting & Data Collection Service
Handles grant reporting and participant impact surveys
"""
import os
import json
import base64
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import func, and_, or_, desc
from app.models import Grant, Organization
from app import db
import logging

# Try to import qrcode, fallback if not available
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

logger = logging.getLogger(__name__)

class Phase5ImpactReporting:
    """Service for grant reporting and impact data collection"""
    
    def __init__(self):
        self.base_url = os.environ.get('REPLIT_DEV_DOMAIN', 'http://localhost:5000')
        if self.base_url and not self.base_url.startswith('http'):
            self.base_url = f"https://{self.base_url}"
    
    def create_grant_report(self, grant_id: int, report_data: Dict) -> Dict:
        """Create a new grant report"""
        try:
            # Get grant details
            grant = Grant.query.get(grant_id)
            if not grant:
                return {'success': False, 'error': 'Grant not found'}
            
            # Create report record
            report = {
                'grant_id': grant_id,
                'grant_title': grant.title or grant.grant_name,
                'reporting_period': report_data.get('period', 'Q1 2025'),
                'status': 'draft',
                'created_at': datetime.now().isoformat(),
                'metrics': report_data.get('metrics', {}),
                'narrative': report_data.get('narrative', ''),
                'evidence_files': report_data.get('evidence_files', [])
            }
            
            # Store in session for demo (would use database in production)
            session_key = f"report_{grant_id}_{datetime.now().timestamp()}"
            
            return {
                'success': True,
                'report': report,
                'report_id': session_key,
                'message': 'Grant report created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating grant report: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_qr_code(self, grant_id: int, program_name: str) -> Dict:
        """Generate QR code for participant data collection"""
        try:
            # Create unique survey URL
            survey_id = f"{grant_id}_{datetime.now().timestamp()}"
            survey_url = f"{self.base_url}/survey/{survey_id}"
            
            if QRCODE_AVAILABLE:
                # Generate actual QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(survey_url)
                qr.make(fit=True)
                
                # Create QR code image
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convert to base64 for frontend display
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                qr_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                qr_code_data = f"data:image/png;base64,{qr_base64}"
            else:
                # Fallback: Create a placeholder QR code using SVG
                svg_qr = f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
                    <rect width="200" height="200" fill="white"/>
                    <rect x="10" y="10" width="180" height="180" fill="none" stroke="black" stroke-width="2"/>
                    <text x="100" y="90" text-anchor="middle" font-family="monospace" font-size="12">QR Code</text>
                    <text x="100" y="110" text-anchor="middle" font-family="monospace" font-size="10">Survey Link</text>
                    <rect x="20" y="20" width="20" height="20" fill="black"/>
                    <rect x="160" y="20" width="20" height="20" fill="black"/>
                    <rect x="20" y="160" width="20" height="20" fill="black"/>
                    <rect x="90" y="90" width="20" height="20" fill="black"/>
                </svg>'''
                svg_base64 = base64.b64encode(svg_qr.encode('utf-8')).decode('utf-8')
                qr_code_data = f"data:image/svg+xml;base64,{svg_base64}"
            
            return {
                'success': True,
                'qr_code': qr_code_data,
                'survey_url': survey_url,
                'survey_id': survey_id,
                'program_name': program_name,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating QR code: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def submit_participant_survey(self, survey_data: Dict) -> Dict:
        """Process participant survey submission and save to impact_intake table"""
        try:
            from app.models import ImpactIntake, db
            from app.utils.impact_intake_validator import validate_and_merge_intake_payload
            
            # Get grant_id (default to first available if not provided)
            grant_id = survey_data.get('grant_id')
            if not grant_id:
                from app.models import Grant
                first_grant = Grant.query.first()
                if first_grant:
                    grant_id = first_grant.id
                else:
                    return {'success': False, 'error': 'No grants available for submission'}
            
            # Build payload with new fields
            intake_payload = {
                # New demographic fields
                'age': survey_data.get('age'),
                'zip': survey_data.get('zip', ''),
                'ethnicity': survey_data.get('ethnicity', ''),
                
                # Stories array (up to 4 text answers)
                'stories': [],
                
                # Existing participant info
                'name': survey_data.get('name', ''),
                'location': survey_data.get('location', ''),
                'program': survey_data.get('program', ''),
                
                # Impact responses
                'impact_responses': {
                    'helped': survey_data.get('impact_q1', ''),
                    'changes': survey_data.get('impact_q2', ''),
                    'rating': survey_data.get('impact_q3', 0),
                    'recommend': survey_data.get('impact_q4', ''),
                    'valuable': survey_data.get('impact_q5', '')
                },
                
                # Improvement responses
                'improvement_responses': {
                    'better_serve': survey_data.get('improve_q1', ''),
                    'reach_others': survey_data.get('improve_q2', '')
                }
            }
            
            # Collect stories from story_1 through story_4
            for i in range(1, 5):
                story_key = f'story_{i}'
                if story_key in survey_data and survey_data[story_key]:
                    intake_payload['stories'].append(survey_data[story_key])
            
            # Validate and merge payload
            validated_payload = validate_and_merge_intake_payload(intake_payload, {})
            
            # Create impact intake record
            intake = ImpactIntake()
            intake.grant_id = grant_id
            intake.submitted_by = survey_data.get('name', 'Anonymous')
            intake.role = survey_data.get('role', 'participant')
            intake.payload = validated_payload
            intake.created_at = datetime.now()
            
            db.session.add(intake)
            db.session.commit()
            
            return {
                'success': True,
                'intake_id': intake.id,
                'message': 'Thank you for your feedback!',
                'confirmation_code': f"IMPACT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            
        except Exception as e:
            logger.error(f"Error submitting survey: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def aggregate_impact_metrics(self, grant_id: int) -> Dict:
        """Aggregate impact data from participant surveys"""
        try:
            # Mock aggregated data (would query database in production)
            metrics = {
                'total_participants': 127,
                'average_rating': 8.7,
                'demographics': {
                    'age_groups': {
                        '18-25': 35,
                        '26-35': 42,
                        '36-45': 28,
                        '46+': 22
                    },
                    'locations': {
                        'Urban': 78,
                        'Suburban': 32,
                        'Rural': 17
                    }
                },
                'impact_summary': {
                    'lives_improved': 115,
                    'would_recommend': 108,
                    'program_completion': 92
                },
                'key_themes': [
                    'Increased access to resources',
                    'Improved skills and knowledge',
                    'Better community connections',
                    'Enhanced quality of life'
                ],
                'improvement_suggestions': [
                    'Expand program hours',
                    'Offer transportation assistance',
                    'Add online components',
                    'Increase outreach efforts'
                ],
                'calculated_at': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'metrics': metrics,
                'grant_id': grant_id
            }
            
        except Exception as e:
            logger.error(f"Error aggregating metrics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def export_report(self, report_id: str, format: str = 'pdf') -> Dict:
        """Export grant report in specified format"""
        try:
            # Generate report content
            report_content = {
                'title': 'Grant Impact Report',
                'period': 'Q1 2025',
                'organization': 'Sample Organization',
                'grant': 'Community Development Grant',
                'executive_summary': 'This quarter demonstrated significant progress...',
                'metrics': {
                    'participants_served': 127,
                    'goals_achieved': 8,
                    'budget_utilized': 75
                },
                'participant_feedback': 'Overwhelmingly positive with 87% satisfaction',
                'next_steps': 'Continue program expansion and refinement',
                'generated_at': datetime.now().isoformat()
            }
            
            # For demo, return structured data (would generate actual PDF in production)
            return {
                'success': True,
                'format': format,
                'content': report_content,
                'download_url': f"/api/phase5/reports/download/{report_id}",
                'filename': f"grant_report_{datetime.now().strftime('%Y%m%d')}.{format}"
            }
            
        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_reporting_dashboard(self, org_id: Optional[int] = None) -> Dict:
        """Get reporting dashboard data"""
        try:
            dashboard = {
                'active_reports': 3,
                'pending_submissions': 2,
                'total_participants': 342,
                'average_impact_score': 8.5,
                'upcoming_deadlines': [
                    {
                        'grant': 'Federal Education Grant',
                        'deadline': (datetime.now() + timedelta(days=15)).isoformat(),
                        'status': 'in_progress'
                    },
                    {
                        'grant': 'State Health Initiative',
                        'deadline': (datetime.now() + timedelta(days=30)).isoformat(),
                        'status': 'not_started'
                    }
                ],
                'recent_surveys': 28,
                'completion_rate': 92,
                'data_quality_score': 94
            }
            
            return {
                'success': True,
                'dashboard': dashboard
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_survey_questions(self) -> Dict:
        """Get structured survey questions"""
        return {
            'success': True,
            'questions': {
                'participant_info': [
                    {'field': 'name', 'label': 'Your Name', 'type': 'text', 'required': True},
                    {'field': 'age', 'label': 'Your Age', 'type': 'number', 'required': True},
                    {'field': 'location', 'label': 'Your Location', 'type': 'text', 'required': True},
                    {'field': 'program', 'label': 'Program Enrolled', 'type': 'text', 'required': True}
                ],
                'impact_questions': [
                    {'field': 'impact_q1', 'label': 'How has this program helped you?', 'type': 'textarea'},
                    {'field': 'impact_q2', 'label': 'What specific changes have you experienced?', 'type': 'textarea'},
                    {'field': 'impact_q3', 'label': 'Rate the program\'s impact on your life (1-10)', 'type': 'rating', 'max': 10},
                    {'field': 'impact_q4', 'label': 'Would you recommend this program to others?', 'type': 'select', 'options': ['Yes', 'No', 'Maybe']},
                    {'field': 'impact_q5', 'label': 'What was the most valuable part of the program?', 'type': 'textarea'}
                ],
                'improvement_questions': [
                    {'field': 'improve_q1', 'label': 'How could this program better serve your needs?', 'type': 'textarea'},
                    {'field': 'improve_q2', 'label': 'Who else in your community could benefit from this program?', 'type': 'textarea'}
                ]
            }
        }

# Initialize service
phase5_service = Phase5ImpactReporting()