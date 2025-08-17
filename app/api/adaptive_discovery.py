"""
Adaptive Discovery API - Dynamic grant discovery questions
Adapts questioning based on user answers for efficient profiling
"""
from flask import Blueprint, jsonify, request, session
from app.services.adaptive_discovery_service import adaptive_discovery
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('adaptive_discovery', __name__, url_prefix='/api/adaptive-discovery')

@bp.route('/start', methods=['POST'])
def start_discovery():
    """
    Start a new adaptive discovery session
    Returns the first high-priority question
    """
    try:
        data = request.get_json() or {}
        initial_data = data.get('initial_data', {})
        
        # Start discovery session
        result = adaptive_discovery.start_discovery(initial_data)
        
        # Store session ID
        session['discovery_session_id'] = result['session_id']
        
        return jsonify({
            'success': True,
            'session_id': result['session_id'],
            'question': result['question'],
            'progress': result['progress'],
            'estimated_remaining': result['estimated_questions_remaining']
        })
        
    except Exception as e:
        logger.error(f"Error starting discovery: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/answer', methods=['POST'])
def process_answer():
    """
    Process user's answer and get next question
    Adapts based on the answer provided
    """
    try:
        data = request.get_json()
        question_key = data.get('question_key')
        answer = data.get('answer')
        
        if not question_key or answer is None:
            return jsonify({'error': 'Missing question_key or answer'}), 400
        
        # Process answer and get next question
        result = adaptive_discovery.process_answer(question_key, answer)
        
        return jsonify({
            'success': True,
            'next_question': result['next_question'],
            'progress': result['progress'],
            'can_start_matching': result['can_start_matching'],
            'estimated_remaining': result['estimated_questions_remaining']
        })
        
    except Exception as e:
        logger.error(f"Error processing answer: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/skip', methods=['POST'])
def skip_question():
    """
    Skip current question and get next one
    Only skips non-required questions
    """
    try:
        data = request.get_json()
        question_key = data.get('question_key')
        
        # Check if question is required
        question = adaptive_discovery.questions.get(question_key, {})
        if question.get('required', False):
            return jsonify({
                'error': 'Cannot skip required question',
                'required': True
            }), 400
        
        # Get next question without storing answer
        next_question = adaptive_discovery.get_next_question()
        progress = adaptive_discovery.calculate_progress()
        
        return jsonify({
            'success': True,
            'next_question': next_question,
            'progress': progress,
            'skipped': question_key
        })
        
    except Exception as e:
        logger.error(f"Error skipping question: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/summary', methods=['GET'])
def get_summary():
    """
    Get discovery summary with AI-generated grant strategy
    Uses optimizer to route to appropriate model
    """
    try:
        summary = adaptive_discovery.get_discovery_summary()
        
        return jsonify({
            'success': summary.get('success', False),
            'profile': summary.get('profile'),
            'analysis': summary.get('analysis'),
            'model_info': {
                'model_used': summary.get('model_used'),
                'cost': summary.get('cost_info')
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/demo', methods=['GET'])
def demo_adaptive_flow():
    """
    Demo endpoint showing adaptive questioning in action
    Shows how questions change based on answers
    """
    try:
        # Scenario 1: Faith-based organization
        faith_demo = adaptive_discovery.start_discovery()
        faith_q1 = faith_demo['question']
        
        # Answer as faith-based
        adaptive_discovery.process_answer('org_name', 'Grace Community Church')
        adaptive_discovery.process_answer('mission', 'Serving inner-city youth through mentorship and education')
        faith_result = adaptive_discovery.process_answer('org_type', 'Faith-based')
        
        # Scenario 2: Small nonprofit
        adaptive_discovery.session_data = {}  # Reset
        small_demo = adaptive_discovery.start_discovery()
        adaptive_discovery.process_answer('org_name', 'Local Food Bank')
        adaptive_discovery.process_answer('mission', 'Fighting hunger in our community')
        adaptive_discovery.process_answer('org_type', '501(c)(3) Nonprofit')
        small_result = adaptive_discovery.process_answer('annual_budget', 'Under $100K')
        
        # Scenario 3: Urgent need
        adaptive_discovery.session_data = {}  # Reset
        urgent_demo = adaptive_discovery.start_discovery()
        adaptive_discovery.process_answer('org_name', 'Youth Crisis Center')
        adaptive_discovery.process_answer('mission', 'Emergency shelter and support for at-risk youth')
        adaptive_discovery.process_answer('org_type', 'Social Services')
        urgent_result = adaptive_discovery.process_answer('urgency', 'Immediately (1-3 months)')
        
        return jsonify({
            'success': True,
            'demonstration': {
                'scenario_1_faith_based': {
                    'description': 'Faith-based org gets denomination question',
                    'first_question': faith_q1,
                    'triggered_question': faith_result.get('next_question', {}).get('question'),
                    'adaptation': 'System asks about denomination after identifying faith-based'
                },
                'scenario_2_small_org': {
                    'description': 'Small org gets appropriate grant size question',
                    'budget': 'Under $100K',
                    'triggered_question': small_result.get('next_question', {}).get('question'),
                    'adaptation': 'System adjusts grant size options for small budget'
                },
                'scenario_3_urgent': {
                    'description': 'Urgent need skips low-priority questions',
                    'urgency': 'Immediately',
                    'questions_remaining': urgent_result.get('estimated_questions_remaining'),
                    'adaptation': 'System fast-tracks to essential questions only'
                }
            },
            'benefits': [
                'Saves 40-60% of time vs static forms',
                'Asks only relevant questions',
                'Adapts to organization type',
                'Prioritizes by importance',
                'Provides personalized strategy'
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in demo: {str(e)}")
        return jsonify({'error': str(e)}), 500