"""
AI-Powered Grant Matching API Endpoints
Using REACTO structure for all AI operations
"""

from flask import Blueprint, jsonify, request
from app.services.ai_grant_matcher import AIGrantMatcher
from app.models import Grant, Organization, db
import logging

logger = logging.getLogger(__name__)

ai_grants_bp = Blueprint('ai_grants', __name__)

@ai_grants_bp.route('/match/<int:org_id>', methods=['GET'])
def get_ai_matched_grants(org_id):
    """Get AI-matched grants for an organization using REACTO"""
    try:
        # Initialize AI matcher
        matcher = AIGrantMatcher()
        
        # Check if organization exists
        org = Organization.query.get(org_id)
        if not org:
            # Try the organizations table instead
            from sqlalchemy import text
            result = db.session.execute(
                text("SELECT * FROM organizations WHERE id = :org_id"),
                {'org_id': org_id}
            ).first()
            
            if not result:
                return jsonify({
                    'success': False,
                    'error': 'Organization not found'
                }), 404
            
            # Create org context from raw result
            org_context = {
                'name': result.name if hasattr(result, 'name') else 'Organization',
                'mission': result.mission if hasattr(result, 'mission') else '',
                'focus_areas': result.primary_focus_areas if hasattr(result, 'primary_focus_areas') else [],
                'geographic_focus': f"{result.primary_city if hasattr(result, 'primary_city') else ''}, {result.primary_state if hasattr(result, 'primary_state') else ''}",
                'annual_budget': result.annual_budget_range if hasattr(result, 'annual_budget_range') else 'Unknown'
            }
        else:
            org_context = org.to_ai_context()
        
        # Get all grants
        grants = Grant.query.limit(20).all()
        
        # Score each grant
        matched_grants = []
        for grant in grants:
            try:
                # Generate REACTO prompt and get match
                from app.services.reacto_prompts import ReactoPrompts
                prompts = ReactoPrompts()
                
                prompt = prompts.grant_matching_prompt(
                    org_context=org_context,
                    grant_data=grant.to_dict()
                )
                
                # Get AI response
                response = matcher.ai_service.generate_json_response(prompt)
                
                if response and 'match_score' in response:
                    grant_dict = grant.to_dict()
                    grant_dict.update({
                        'match_score': response['match_score'],
                        'match_percentage': response.get('match_percentage', response['match_score'] * 20),
                        'match_verdict': response.get('verdict', 'Not Evaluated'),
                        'match_reason': response.get('recommendation', ''),
                        'key_alignments': response.get('key_alignments', []),
                        'potential_challenges': response.get('potential_challenges', []),
                        'next_steps': response.get('next_steps', []),
                        'application_tips': response.get('application_tips', '')
                    })
                    matched_grants.append(grant_dict)
            except Exception as e:
                logger.error(f"Error matching grant {grant.id}: {str(e)}")
                # Add grant without score
                grant_dict = grant.to_dict()
                grant_dict['match_score'] = 0
                grant_dict['match_reason'] = 'Unable to score'
                matched_grants.append(grant_dict)
        
        # Sort by match score
        matched_grants.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'organization': org_context.get('name', 'Organization'),
            'total_grants': len(matched_grants),
            'matched_grants': matched_grants[:10]  # Top 10 matches
        })
        
    except Exception as e:
        logger.error(f"Error in AI grant matching: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_grants_bp.route('/analyze/<int:grant_id>/<int:org_id>', methods=['GET'])
def analyze_grant_fit(grant_id, org_id):
    """Get detailed AI analysis of grant-organization fit"""
    try:
        matcher = AIGrantMatcher()
        
        # Get grant and org
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'success': False, 'error': 'Grant not found'}), 404
        
        # Try to get organization
        org = Organization.query.get(org_id)
        if not org:
            # Create minimal context
            org_context = {
                'name': 'Organization',
                'mission': 'Not specified',
                'focus_areas': [],
                'geographic_focus': 'Not specified',
                'annual_budget': 'Unknown'
            }
        else:
            org_context = org.to_ai_context()
        
        # Generate detailed analysis
        from app.services.reacto_prompts import ReactoPrompts
        prompts = ReactoPrompts()
        
        # Get match analysis
        match_prompt = prompts.grant_matching_prompt(org_context, grant.to_dict())
        match_response = matcher.ai_service.generate_json_response(match_prompt)
        
        # Get intelligence analysis
        intelligence_prompt = prompts.grant_intelligence_prompt(
            f"{grant.title}\n{grant.eligibility or ''}\n{grant.source_url or ''}"
        )
        intelligence_response = matcher.ai_service.generate_json_response(intelligence_prompt)
        
        return jsonify({
            'success': True,
            'grant': grant.to_dict(),
            'organization': org_context.get('name'),
            'match_analysis': match_response or {},
            'intelligence': intelligence_response or {},
            'recommended_action': _determine_action(match_response.get('match_score', 0) if match_response else 0)
        })
        
    except Exception as e:
        logger.error(f"Error analyzing grant fit: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_grants_bp.route('/generate-narrative', methods=['POST'])
def generate_narrative():
    """Generate grant narrative section using REACTO"""
    try:
        data = request.json
        grant_id = data.get('grant_id')
        org_id = data.get('org_id')
        section = data.get('section', 'executive_summary')
        
        if not grant_id or not org_id:
            return jsonify({
                'success': False,
                'error': 'grant_id and org_id required'
            }), 400
        
        matcher = AIGrantMatcher()
        
        # Get grant
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'success': False, 'error': 'Grant not found'}), 404
        
        # Get organization context
        org = Organization.query.get(org_id)
        if not org:
            org_context = {
                'name': 'Organization',
                'mission': 'Not specified',
                'unique_capabilities': '',
                'unique_factors': {},
                'current_needs': 'General operating support'
            }
        else:
            org_context = org.to_ai_context()
        
        # Generate narrative
        from app.services.reacto_prompts import ReactoPrompts
        prompts = ReactoPrompts()
        
        prompt = prompts.narrative_generation_prompt(
            org_context=org_context,
            grant_data=grant.to_dict(),
            section=section
        )
        
        response = matcher.ai_service.generate_json_response(prompt)
        
        if response:
            return jsonify({
                'success': True,
                'section': section,
                'narrative': response.get('narrative_text', ''),
                'word_count': response.get('word_count', 0),
                'key_points': response.get('key_points_covered', []),
                'metrics': response.get('metrics_included', []),
                'suggestions': response.get('suggested_attachments', [])
            })
        
        return jsonify({
            'success': False,
            'error': 'Failed to generate narrative'
        }), 500
        
    except Exception as e:
        logger.error(f"Error generating narrative: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def _determine_action(score):
    """Determine recommended action based on match score"""
    if score >= 4:
        return "Apply Immediately - Excellent match"
    elif score == 3:
        return "Consider Applying - Good potential"
    elif score == 2:
        return "Review Carefully - Some alignment"
    else:
        return "Skip - Poor match"