"""
AI Matching API endpoints with advanced reasoning
"""

from flask import Blueprint, request, jsonify
from app.api.auth import login_required, get_current_user
from app.services.ai_reasoning_engine import AIReasoningEngine
from app.services.ai_learning_system import AILearningSystem
from app.models import Organization, Grant
from app import db
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('ai_matching', __name__, url_prefix='/api/ai-matching')

# Initialize AI services
reasoning_engine = AIReasoningEngine()
learning_system = AILearningSystem()

@bp.route('/analyze-grant', methods=['POST'])
@login_required
def analyze_grant():
    """
    Perform deep AI analysis of grant match with reasoning chain
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.json
        grant_id = data.get('grant_id')
        grant_data = data.get('grant_data')
        
        # Get user's organization
        org = Organization.query.filter_by(created_by_user_id=user.id).first()
        if not org:
            return jsonify({'error': 'Organization profile not found'}), 404
        
        # Get grant if ID provided
        if grant_id:
            grant = Grant.query.get(grant_id)
            if grant:
                grant_data = grant.to_dict()
        
        if not grant_data:
            return jsonify({'error': 'Grant data required'}), 400
        
        # Perform advanced reasoning analysis
        analysis = reasoning_engine.analyze_grant_match(org, grant_data)
        
        # Record the analysis for learning
        if grant_id:
            learning_system.record_user_decision(
                user_id=user.id,
                grant_id=grant_id,
                decision='analyzed',
                reasoning={'initial_score': analysis['match_score']}
            )
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'org_name': org.name
        }), 200
        
    except Exception as e:
        logger.error(f"Error in grant analysis: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/record-decision', methods=['POST'])
@login_required
def record_decision():
    """
    Record user decision on a grant for learning
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.json
        grant_id = data.get('grant_id')
        decision = data.get('decision')  # 'applied', 'saved', 'rejected', 'ignored'
        reasoning = data.get('reasoning')
        
        if not grant_id or not decision:
            return jsonify({'error': 'Grant ID and decision required'}), 400
        
        # Record decision for learning
        success = learning_system.record_user_decision(
            user_id=user.id,
            grant_id=grant_id,
            decision=decision,
            reasoning=reasoning
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Decision recorded: {decision}'
            }), 200
        else:
            return jsonify({'error': 'Failed to record decision'}), 500
            
    except Exception as e:
        logger.error(f"Error recording decision: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/record-outcome', methods=['POST'])
@login_required
def record_outcome():
    """
    Record grant application outcome for learning
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's organization
        org = Organization.query.filter_by(created_by_user_id=user.id).first()
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        data = request.json
        grant_id = data.get('grant_id')
        outcome = data.get('outcome')  # 'awarded', 'rejected', 'pending', 'withdrawn'
        details = data.get('details')
        
        if not grant_id or not outcome:
            return jsonify({'error': 'Grant ID and outcome required'}), 400
        
        # Record outcome for learning
        success = learning_system.record_application_outcome(
            org_id=org.id,
            grant_id=grant_id,
            outcome=outcome,
            details=details
        )
        
        if success:
            # Improve matching based on outcome
            improved_weights = learning_system.improve_matching_algorithm(org.id)
            
            return jsonify({
                'success': True,
                'message': f'Outcome recorded: {outcome}',
                'improved_weights': improved_weights
            }), 200
        else:
            return jsonify({'error': 'Failed to record outcome'}), 500
            
    except Exception as e:
        logger.error(f"Error recording outcome: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/insights', methods=['GET'])
@login_required
def get_insights():
    """
    Get personalized AI insights for the organization
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's organization
        org = Organization.query.filter_by(created_by_user_id=user.id).first()
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Generate personalized insights
        insights = learning_system.get_personalized_insights(org.id)
        
        return jsonify({
            'success': True,
            'insights': insights,
            'org_name': org.name
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/improve-matching', methods=['POST'])
@login_required
def improve_matching():
    """
    Trigger matching algorithm improvement based on learning
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's organization
        org = Organization.query.filter_by(created_by_user_id=user.id).first()
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Improve matching algorithm
        improved = learning_system.improve_matching_algorithm(org.id)
        
        return jsonify({
            'success': True,
            'message': 'Matching algorithm improved based on your history',
            'improvements': improved
        }), 200
        
    except Exception as e:
        logger.error(f"Error improving matching: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/batch-analyze', methods=['POST'])
@login_required
def batch_analyze():
    """
    Analyze multiple grants at once with reasoning
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's organization
        org = Organization.query.filter_by(created_by_user_id=user.id).first()
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        data = request.json
        grant_ids = data.get('grant_ids', [])
        
        if not grant_ids:
            return jsonify({'error': 'Grant IDs required'}), 400
        
        results = []
        for grant_id in grant_ids[:10]:  # Limit to 10 for performance
            grant = Grant.query.get(grant_id)
            if grant:
                analysis = reasoning_engine.analyze_grant_match(org, grant.to_dict())
                results.append({
                    'grant_id': grant_id,
                    'grant_title': grant.title,
                    'match_score': analysis['match_score'],
                    'confidence': analysis['confidence'],
                    'recommendation': analysis['recommendation']
                })
        
        # Sort by match score
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'analyses': results,
            'total_analyzed': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        return jsonify({'error': str(e)}), 500