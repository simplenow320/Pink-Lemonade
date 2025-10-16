"""
Enhanced Grant Matching API
Quality-focused endpoints that return only the best matches
"""
from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
import logging

from app.services.enhanced_ai_matcher import EnhancedAIGrantMatcher

logger = logging.getLogger(__name__)

enhanced_matching_bp = Blueprint('enhanced_matching', __name__)

@enhanced_matching_bp.route('/api/matching/excellence/<int:org_id>', methods=['GET'])
@cross_origin()
def get_excellent_matches(org_id: int):
    """
    Get only the highest quality grant matches
    Quality over quantity approach
    """
    try:
        # Get query parameters
        tier = request.args.get('tier', 'all')  # all, apply_now, explore
        limit = request.args.get('limit', 10, type=int)
        
        # Initialize enhanced matcher
        matcher = EnhancedAIGrantMatcher()
        
        # Get high-quality matches
        matches = matcher.match_grants_with_excellence(org_id, limit)
        
        # Filter by tier if requested
        if tier == 'apply_now':
            matches = [m for m in matches if m['composite_score'] >= 85]
        elif tier == 'explore':
            matches = [m for m in matches if 70 <= m['composite_score'] < 85]
        
        # Group matches by confidence level
        grouped = {
            'apply_now': [],      # Score >= 85
            'worth_exploring': [], # Score 70-84
            'review_carefully': [] # Score < 70 (if any passed threshold)
        }
        
        for match in matches:
            if match['composite_score'] >= 85:
                grouped['apply_now'].append(match)
            elif match['composite_score'] >= 70:
                grouped['worth_exploring'].append(match)
            else:
                grouped['review_carefully'].append(match)
        
        # Calculate statistics
        stats = {
            'total_evaluated': len(matches),
            'high_confidence': len(grouped['apply_now']),
            'medium_confidence': len(grouped['worth_exploring']),
            'average_score': round(sum(m['composite_score'] for m in matches) / len(matches), 1) if matches else 0,
            'best_match_score': max((m['composite_score'] for m in matches), default=0)
        }
        
        return jsonify({
            'success': True,
            'organization_id': org_id,
            'matches': grouped,
            'statistics': stats,
            'approach': 'quality_over_quantity',
            'message': f"Showing {len(matches)} high-quality matches"
        }), 200
        
    except Exception as e:
        logger.error(f"Enhanced matching error for org {org_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@enhanced_matching_bp.route('/api/matching/excellence/<int:org_id>/<int:grant_id>', methods=['GET'])
@cross_origin()
def get_detailed_match_analysis(org_id: int, grant_id: int):
    """
    Get detailed analysis for a specific grant match
    Shows all scoring dimensions and reasoning
    """
    try:
        from app.models import Organization, Grant
        
        org = Organization.query.get(org_id)
        grant = Grant.query.get(grant_id)
        
        if not org or not grant:
            return jsonify({
                'success': False,
                'error': 'Organization or grant not found'
            }), 404
        
        # Get detailed match analysis
        matcher = EnhancedAIGrantMatcher()
        analysis = matcher._calculate_enhanced_match(org, grant)
        
        # Add additional insights
        insights = {
            'quick_wins': [],
            'red_flags': [],
            'improvement_suggestions': []
        }
        
        # Analyze dimensions for insights
        for dim, score in analysis['dimensions'].items():
            if score >= 85:
                insights['quick_wins'].append(f"Strong {dim.replace('_', ' ')}: {score}%")
            elif score < 50:
                insights['red_flags'].append(f"Weak {dim.replace('_', ' ')}: {score}%")
            elif score < 70:
                insights['improvement_suggestions'].append(
                    f"Improve {dim.replace('_', ' ')} from {score}% to increase chances"
                )
        
        analysis['insights'] = insights
        
        return jsonify({
            'success': True,
            'analysis': analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Detailed analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@enhanced_matching_bp.route('/api/matching/feedback', methods=['POST'])
@cross_origin()
def submit_match_feedback():
    """
    Submit feedback on match quality for continuous improvement
    """
    try:
        data = request.json
        org_id = data.get('org_id')
        grant_id = data.get('grant_id')
        feedback_type = data.get('feedback_type')  # applied, won, lost, skipped
        feedback_reason = data.get('reason', '')
        
        # TODO: Store this feedback for ML model training
        # For now, just log it
        logger.info(f"Match feedback: Org {org_id}, Grant {grant_id}, Type: {feedback_type}, Reason: {feedback_reason}")
        
        return jsonify({
            'success': True,
            'message': 'Feedback recorded for improving match quality'
        }), 200
        
    except Exception as e:
        logger.error(f"Feedback submission error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500