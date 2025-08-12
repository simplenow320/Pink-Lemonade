from flask import Blueprint, request, jsonify
from app import db
from app.models import Grant, Organization
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("grant_analysis", __name__)

@bp.route('/api/grants/<int:grant_id>/analyze', methods=['GET'])
def analyze_grant(grant_id):
    """
    Provide comprehensive AI analysis of a grant opportunity to help users
    make informed decisions about whether to apply.
    """
    try:
        # Get the grant
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Get the user's organization (use first org for now)
        org = Organization.query.first()
        
        # Prepare grant data
        grant_data = {
            'title': grant.title,
            'funder': grant.funder,
            'deadline': grant.deadline.isoformat() if grant.deadline else None,
            'amount_min': grant.amount_min,
            'amount_max': grant.amount_max,
            'description': grant.ai_summary or grant.eligibility or '',
            'link': grant.link,
            'source': grant.source_name
        }
        
        # Prepare org data
        org_data = {}
        if org:
            org_data = {
                'name': org.name,
                'mission': org.mission,
                'focus_areas': org.focus_areas,
                'programs': org.programs,
                'budget': org.budget,
                'ein': org.ein
            }
        
        # Generate comprehensive AI analysis
        analysis = generate_comprehensive_grant_analysis(grant_data, org_data)
        
        return jsonify({
            'success': True,
            'grant': grant_data,
            'organization': org_data,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error analyzing grant {grant_id}: {e}")
        return jsonify({'error': str(e)}), 500

def generate_comprehensive_grant_analysis(grant_data, org_data):
    """
    Generate comprehensive AI analysis including alignment, requirements,
    success factors, and actionable recommendations.
    """
    
    # The prompt we use for comprehensive grant analysis
    analysis_prompt = f"""
    Analyze this grant opportunity for the nonprofit organization and provide comprehensive guidance.
    
    GRANT OPPORTUNITY:
    Title: {grant_data.get('title', 'Unknown')}
    Funder: {grant_data.get('funder', 'Unknown')}
    Amount Range: ${grant_data.get('amount_min', 0):,} - ${grant_data.get('amount_max', 0):,}
    Deadline: {grant_data.get('deadline', 'Not specified')}
    Description: {grant_data.get('description', 'No description available')}
    Source: {grant_data.get('source', 'Unknown')}
    
    ORGANIZATION PROFILE:
    Name: {org_data.get('name', 'Organization not specified')}
    Mission: {org_data.get('mission', 'Not specified')}
    Focus Areas: {org_data.get('focus_areas', 'Not specified')}
    Programs: {org_data.get('programs', 'Not specified')}
    Budget: {org_data.get('budget', 'Not specified')}
    
    Provide a comprehensive analysis in JSON format with these sections:
    
    1. "alignment_score": A score from 1-10 rating how well this grant aligns with the organization
    2. "alignment_explanation": Detailed explanation of why this is or isn't a good fit
    3. "key_requirements": List of 3-5 key requirements that must be met to apply
    4. "success_factors": Top 3-5 factors that would make a successful application
    5. "potential_challenges": 2-3 challenges or concerns to be aware of
    6. "recommended_approach": Step-by-step approach for applying (3-5 steps)
    7. "time_estimate": Estimated hours needed to prepare a competitive application
    8. "decision_recommendation": Clear recommendation: "Highly Recommended", "Worth Considering", "Consider Carefully", or "Not Recommended"
    9. "decision_rationale": 2-3 sentence explanation of the recommendation
    10. "next_steps": Immediate next 3 actions if they decide to proceed
    11. "similar_opportunities": Suggestions for finding similar grants if this one isn't ideal
    12. "preparation_checklist": List of 5-7 documents/items to prepare before applying
    
    Be specific, practical, and actionable. Focus on helping them make an informed decision.
    """
    
    try:
        # Call the AI service
        result = ai_service._make_request(
            messages=[
                {"role": "system", "content": "You are an expert grant consultant with 20 years of experience helping nonprofits win grants. Provide practical, actionable advice."},
                {"role": "user", "content": analysis_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=2000
        )
        
        if result:
            return result
        else:
            # Fallback analysis if AI is not available
            return {
                "alignment_score": 5,
                "alignment_explanation": "Unable to perform AI analysis. Please review the grant details manually.",
                "key_requirements": ["Review grant guidelines", "Check eligibility criteria", "Verify deadline"],
                "success_factors": ["Strong mission alignment", "Clear project proposal", "Demonstrated impact"],
                "potential_challenges": ["Competition may be high", "Requirements need careful review"],
                "recommended_approach": ["Review guidelines", "Assess fit", "Prepare documents", "Submit early"],
                "time_estimate": "20-40 hours",
                "decision_recommendation": "Review Manually",
                "decision_rationale": "AI analysis unavailable. Manual review of grant guidelines recommended.",
                "next_steps": ["Download guidelines", "Review requirements", "Assess organizational fit"],
                "similar_opportunities": ["Check Federal Register for similar grants", "Search Grants.gov"],
                "preparation_checklist": ["501(c)(3) verification", "Financial statements", "Board list", "Project budget", "Impact metrics"]
            }
    except Exception as e:
        logger.error(f"Error generating AI analysis: {e}")
        return {
            "error": "Analysis temporarily unavailable",
            "message": "Please try again later or review grant details manually"
        }

@bp.route('/api/grants/<int:grant_id>', methods=['GET'])
def get_grant_detail(grant_id):
    """Get detailed information about a specific grant"""
    try:
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        return jsonify({
            'success': True,
            'grant': {
                'id': grant.id,
                'title': grant.title,
                'funder': grant.funder,
                'deadline': grant.deadline.isoformat() if grant.deadline else None,
                'amount_min': grant.amount_min,
                'amount_max': grant.amount_max,
                'description': grant.ai_summary or grant.eligibility or '',
                'link': grant.link,
                'source': grant.source_name,
                'status': grant.status,
                'geography': grant.geography,
                'created_at': grant.created_at.isoformat() if grant.created_at else None
            }
        })
    except Exception as e:
        logger.error(f"Error fetching grant {grant_id}: {e}")
        return jsonify({'error': str(e)}), 500