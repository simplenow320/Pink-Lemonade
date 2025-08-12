"""
Automated Grant Matching Score System
Calculates match scores between organizations and grants using AI
"""
from flask import Blueprint, jsonify, request
from app import db
from app.models import Grant, Organization
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('grant_matching', __name__)

@bp.route('/api/grant-matching/calculate', methods=['POST'])
def calculate_match_scores():
    """
    Calculate AI-powered matching scores for grants
    """
    try:
        data = request.get_json() or {}
        org_id = data.get('org_id', 1)
        
        # Get organization profile
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Get all grants that need scoring
        grants = Grant.query.filter(
            (Grant.match_score == None) | (Grant.match_score == 0)
        ).limit(10).all()
        
        updated_count = 0
        results = []
        
        for grant in grants:
            # Calculate match score using AI
            score_data = calculate_single_match(org, grant)
            
            # Update grant with score
            grant.match_score = score_data['score']
            grant.match_reason = score_data['reason']
            
            results.append({
                'grant_id': grant.id,
                'title': grant.title,
                'score': score_data['score'],
                'reason': score_data['reason']
            })
            updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'matches': results
        })
        
    except Exception as e:
        logger.error(f"Error calculating match scores: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/grant-matching/score/<int:grant_id>', methods=['GET'])
def get_grant_match_score(grant_id):
    """
    Get or calculate match score for a specific grant
    """
    try:
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        org = Organization.query.get(grant.org_id or 1)
        
        # Return existing score or calculate new one
        if grant.match_score:
            return jsonify({
                'grant_id': grant.id,
                'score': grant.match_score,
                'reason': grant.match_reason
            })
        
        # Calculate new score
        score_data = calculate_single_match(org, grant)
        
        # Save to database
        grant.match_score = score_data['score']
        grant.match_reason = score_data['reason']
        db.session.commit()
        
        return jsonify({
            'grant_id': grant.id,
            'score': score_data['score'],
            'reason': score_data['reason']
        })
        
    except Exception as e:
        logger.error(f"Error getting match score: {e}")
        return jsonify({'error': str(e)}), 500

def calculate_single_match(org, grant):
    """
    Calculate match score between an organization and a grant
    """
    try:
        # Build organization context
        org_context = f"""
        Organization: {org.name}
        Mission: {org.mission or 'Not specified'}
        Focus Areas: {', '.join(org.primary_focus_areas or [])}
        Location: {org.primary_city}, {org.primary_state}
        Budget: {org.annual_budget_range}
        """
        
        # Build grant context
        grant_context = f"""
        Grant: {grant.title}
        Funder: {grant.funder}
        Description: {grant.ai_summary or 'Not specified'}
        Geography: {grant.geography or 'Not specified'}
        """
        
        # Use AI to calculate match
        prompt = f"""
        Calculate a match score (1-5) between this organization and grant.
        Consider mission alignment, geographic fit, capacity match, and eligibility.
        
        {org_context}
        
        {grant_context}
        
        Return a JSON object with:
        - score: integer 1-5 (5 being perfect match)
        - reason: brief explanation of the score
        """
        
        # Use AI service to generate response
        response = ai_service.generate_with_structure(prompt, {"properties": {"score": {"type": "integer"}, "reason": {"type": "string"}}})
        
        # Parse response
        if response and isinstance(response, dict):
            score = response.get('score', 3)
            reason = response.get('reason', 'Match score calculated based on profile alignment')
        elif response:
            # Fallback parsing if not dict
            import json
            try:
                result = json.loads(response) if isinstance(response, str) else {}
                score = result.get('score', 3)
                reason = result.get('reason', 'Match score calculated based on profile alignment')
            except:
                score = 3
                reason = 'Match score calculated based on profile alignment'
        else:
            score = 3
            reason = 'Match score calculated based on profile alignment'
        
        return {
            'score': min(5, max(1, score)),
            'reason': reason
        }
        
    except Exception as e:
        logger.error(f"Error in AI matching: {e}")
        # Fallback scoring based on basic criteria
        score = 3  # Default middle score
        reason = "Standard match based on general criteria"
        
        # Simple keyword matching
        if org.primary_focus_areas and grant.title:
            grant_lower = grant.title.lower()
            for area in org.primary_focus_areas:
                if area.lower() in grant_lower:
                    score = 4
                    reason = f"Good match based on {area} focus area"
                    break
        
        return {'score': score, 'reason': reason}

@bp.route('/api/grant-matching/batch', methods=['POST'])
def batch_calculate_scores():
    """
    Calculate scores for all grants in the system
    """
    try:
        # Get all grants
        grants = Grant.query.all()
        org = Organization.query.first()
        
        if not org:
            return jsonify({'error': 'No organization found'}), 404
        
        updated = 0
        for grant in grants:
            if not grant.match_score:
                score_data = calculate_single_match(org, grant)
                grant.match_score = score_data['score']
                grant.match_reason = score_data['reason']
                updated += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'total_grants': len(grants),
            'updated': updated
        })
        
    except Exception as e:
        logger.error(f"Error in batch scoring: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500