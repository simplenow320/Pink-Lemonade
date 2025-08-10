"""
Smart Reporting API Blueprint - Phase 2: AI Question Refinement & Survey Builder
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, date
import json

# Import Phase 2 models when ready
try:
    from app.models_extended import SurveyTemplate, QuestionRefinementLog, ResponseAnalytics, SurveySession
except ImportError:
    # Fallback for development
    SurveyTemplate = None
    QuestionRefinementLog = None
    ResponseAnalytics = None
    SurveySession = None

bp = Blueprint('smart_reporting_phase2', __name__, url_prefix='/api/smart-reporting/phase2')

@bp.route('/health', methods=['GET'])
def health_check():
    """Phase 2 health check"""
    return jsonify({
        "success": True,
        "phase": "Phase 2 - AI Question Refinement & Survey Builder",
        "status": "operational",
        "features": [
            "AI Question Refinement Engine",
            "Advanced Survey Builder", 
            "Response Analytics",
            "Survey Session Management"
        ],
        "timestamp": datetime.utcnow().isoformat()
    })

@bp.route('/ai/refine-questions', methods=['POST'])
def refine_questions():
    """Refine existing questions using AI feedback analysis"""
    try:
        data = request.get_json()
        questions = data.get('questions', [])
        feedback_data = data.get('feedback_data', {})
        
        # Simulate AI question refinement
        refined_questions = []
        for i, question in enumerate(questions):
            refined_questions.append({
                "original_id": question.get("id", f"q_{i}"),
                "original_text": question.get("question_text", ""),
                "refined_text": f"[REFINED] {question.get('question_text', '')} (Improved for clarity and engagement)",
                "improvements_made": ["clarity", "specificity", "engagement"],
                "expected_improvement": "25% increase in response quality",
                "ai_confidence": 0.85,
                "refinement_rationale": "Enhanced question structure to improve respondent understanding and engagement"
            })
        
        new_questions = [
            {
                "question_text": "What specific outcomes have you observed since participating in this program?",
                "question_type": "qualitative",
                "category": "outcomes",
                "rationale": "Captures specific, measurable changes that validate program effectiveness",
                "ai_confidence": 0.90
            },
            {
                "question_text": "On a scale of 1-10, how likely are you to recommend this program to others?",
                "question_type": "quantitative", 
                "category": "satisfaction",
                "rationale": "Net Promoter Score methodology for standardized satisfaction measurement",
                "ai_confidence": 0.92
            }
        ]
        
        return jsonify({
            "success": True,
            "refined_questions": refined_questions,
            "new_questions": new_questions,
            "optimization_recommendations": [
                "Balance quantitative and qualitative questions for comprehensive insights",
                "Include story-based questions to capture human impact narratives",
                "Add conditional logic to reduce survey fatigue"
            ],
            "ai_metadata": {
                "refinement_timestamp": datetime.utcnow().isoformat(),
                "model_version": "gpt-4o",
                "processing_time": "2.3 seconds"
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Question refinement error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/survey-builder/generate-template', methods=['POST'])
def generate_survey_template():
    """Generate comprehensive survey templates for different stakeholder groups"""
    try:
        data = request.get_json()
        project_context = data.get('project_context', {})
        stakeholder_types = data.get('stakeholder_types', ['beneficiaries'])
        
        # Generate stakeholder-specific survey templates
        survey_templates = {}
        
        for stakeholder_type in stakeholder_types:
            if stakeholder_type == "beneficiaries":
                survey_templates[stakeholder_type] = {
                    "title": "Program Impact Assessment - Your Experience",
                    "welcome_message": "Thank you for participating in our program. Your feedback helps us improve and demonstrate our impact to funders.",
                    "sections": [
                        {
                            "section_name": "Program Participation",
                            "questions": [
                                {
                                    "question_text": "How long have you been participating in this program?",
                                    "question_type": "multiple_choice",
                                    "required": True,
                                    "options": ["Less than 3 months", "3-6 months", "6-12 months", "More than 1 year"],
                                    "ai_rationale": "Establishes baseline for measuring program duration impact"
                                },
                                {
                                    "question_text": "What changes have you noticed in your life since joining the program?",
                                    "question_type": "text",
                                    "required": True,
                                    "ai_rationale": "Captures qualitative impact in participants' own words"
                                }
                            ]
                        },
                        {
                            "section_name": "Outcomes and Impact",
                            "questions": [
                                {
                                    "question_text": "Rate your overall satisfaction with the program (1-10)",
                                    "question_type": "scale",
                                    "required": True,
                                    "scale_min": 1,
                                    "scale_max": 10,
                                    "ai_rationale": "Quantifiable satisfaction metric for program evaluation"
                                },
                                {
                                    "question_text": "Tell us about a specific moment when the program made a difference for you",
                                    "question_type": "story",
                                    "required": False,
                                    "ai_rationale": "Narrative data provides compelling evidence for grant reports"
                                }
                            ]
                        }
                    ],
                    "thank_you_message": "Thank you for sharing your experience. Your feedback directly helps us secure continued funding for this program.",
                    "estimated_time": "5-7 minutes"
                }
            
            elif stakeholder_type == "staff":
                survey_templates[stakeholder_type] = {
                    "title": "Program Implementation Assessment - Staff Perspective",
                    "welcome_message": "Your insights into program delivery help us measure effectiveness and identify improvement opportunities.",
                    "sections": [
                        {
                            "section_name": "Program Delivery",
                            "questions": [
                                {
                                    "question_text": "What has been most effective about this program's approach?",
                                    "question_type": "text",
                                    "required": True,
                                    "ai_rationale": "Identifies successful strategies for replication and reporting"
                                },
                                {
                                    "question_text": "How would you rate participant engagement levels (1-10)?",
                                    "question_type": "scale",
                                    "required": True,
                                    "scale_min": 1,
                                    "scale_max": 10,
                                    "ai_rationale": "Quantifies engagement as a key success indicator"
                                }
                            ]
                        }
                    ],
                    "thank_you_message": "Your professional insights are invaluable for program improvement and grant reporting.",
                    "estimated_time": "8-10 minutes"
                }
        
        return jsonify({
            "success": True,
            "survey_templates": survey_templates,
            "cross_cutting_themes": [
                "Program satisfaction and engagement",
                "Specific outcomes and behavior changes", 
                "Story-based impact narratives",
                "Recommendations for improvement"
            ],
            "data_integration_notes": [
                "Combine quantitative metrics for statistical analysis",
                "Use qualitative responses to provide context for numbers",
                "Story responses become case studies for grant narratives"
            ],
            "ai_metadata": {
                "generation_timestamp": datetime.utcnow().isoformat(),
                "stakeholder_count": len(stakeholder_types),
                "template_version": "2.0",
                "ai_optimization": "Templates optimized for response quality and funder requirements"
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Survey template generation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/analytics/response-quality', methods=['GET'])
def get_response_analytics():
    """Get advanced analytics on survey response quality and insights"""
    try:
        project_id = request.args.get('project_id')
        
        # Simulate response analytics
        analytics = {
            "project_id": int(project_id) if project_id else 1,
            "overall_metrics": {
                "completion_rate": 78.5,
                "average_quality_score": 8.2,
                "insight_value_rating": 7.9,
                "engagement_score": 8.5
            },
            "question_performance": [
                {
                    "question_id": 1,
                    "question_text": "How satisfied are you with the program?",
                    "completion_rate": 95.2,
                    "quality_score": 8.8,
                    "insight_value": 8.1,
                    "improvement_suggestions": ["Add follow-up question about specific satisfaction factors"]
                },
                {
                    "question_id": 2,
                    "question_text": "What changes have you noticed?",
                    "completion_rate": 72.1,
                    "quality_score": 7.6,
                    "insight_value": 9.2,
                    "improvement_suggestions": ["Provide examples to guide responses", "Break into specific categories"]
                }
            ],
            "sentiment_analysis": {
                "positive": 68,
                "neutral": 22,
                "negative": 10
            },
            "key_themes": [
                "Increased confidence and self-esteem",
                "Improved job readiness and skills",
                "Stronger community connections",
                "Enhanced educational outcomes"
            ],
            "actionable_insights": [
                "Program most effective for participants engaged 6+ months",
                "Peer mentoring component drives highest satisfaction scores",
                "Educational outcomes strongest in math and technology skills"
            ],
            "ai_summary": "Overall positive impact with strong participant satisfaction. Key success factors include program duration and peer support elements. Recommendations for enhancement focus on structured skill development tracking."
        }
        
        return jsonify({
            "success": True,
            "analytics": analytics,
            "analysis_metadata": {
                "analysis_period": "2024-01-01 to 2024-08-10",
                "total_responses": 127,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Response analytics error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/survey-sessions', methods=['GET'])
def get_survey_sessions():
    """Get survey session tracking and user experience data"""
    try:
        project_id = request.args.get('project_id')
        
        # Simulate survey session data
        sessions = [
            {
                "id": 1,
                "session_token": "sess_abc123",
                "respondent_type": "beneficiary",
                "completion_percentage": 100.0,
                "status": "completed",
                "device_type": "mobile",
                "actual_time_spent": 6,
                "difficulty_rating": 2.0,
                "user_feedback": "Easy to complete on my phone"
            },
            {
                "id": 2, 
                "session_token": "sess_def456",
                "respondent_type": "staff",
                "completion_percentage": 75.0,
                "status": "in_progress",
                "device_type": "desktop",
                "actual_time_spent": 8,
                "difficulty_rating": 3.0,
                "user_feedback": None
            }
        ]
        
        return jsonify({
            "success": True,
            "sessions": sessions,
            "summary": {
                "total_sessions": len(sessions),
                "completed_sessions": 1,
                "average_completion_rate": 87.5,
                "average_difficulty_rating": 2.5,
                "mobile_vs_desktop": {"mobile": 50, "desktop": 50}
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Survey sessions error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500