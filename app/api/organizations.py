"""Organizations API endpoints for profile retrieval"""
from flask import Blueprint, jsonify
from app.models import Organization
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('organizations', __name__, url_prefix='/api/organizations')

@bp.route('/profile', methods=['GET'])
def get_organization_profile():
    """Get the organization profile for the current user"""
    try:
        # For now, get the first organization (in production, this would be user-specific)
        org = Organization.query.first()
        
        if not org:
            return jsonify({
                'error': 'No organization profile found',
                'message': 'Please complete your organization profile first'
            }), 404
        
        # Return comprehensive organization data
        org_data = {
            'id': org.id,
            'name': org.name,
            'legal_name': org.legal_name,
            'ein': org.ein,
            'org_type': org.org_type,
            'year_founded': org.year_founded,
            'website': org.website,
            'mission': org.mission,
            'vision': org.vision,
            'values': org.values,
            'primary_focus_areas': org.primary_focus_areas or [],
            'secondary_focus_areas': org.secondary_focus_areas or [],
            'programs_services': org.programs_services,
            'target_demographics': org.target_demographics or [],
            'age_groups_served': org.age_groups_served or [],
            'service_area_type': org.service_area_type,
            'primary_city': org.primary_city,
            'primary_state': org.primary_state,
            'primary_zip': org.primary_zip,
            'counties_served': org.counties_served or [],
            'states_served': org.states_served or [],
            'annual_budget_range': org.annual_budget_range,
            'staff_size': org.staff_size,
            'volunteer_count': org.volunteer_count,
            'board_size': org.board_size,
            'people_served_annually': org.people_served_annually,
            'key_achievements': org.key_achievements,
            'impact_metrics': org.impact_metrics or {},
            'previous_funders': org.previous_funders or [],
            'typical_grant_size': org.typical_grant_size,
            'grant_success_rate': org.grant_success_rate,
            'preferred_grant_types': org.preferred_grant_types or [],
            'grant_writing_capacity': org.grant_writing_capacity,
            'keywords': org.keywords or [],
            'unique_capabilities': org.unique_capabilities,
            'partnership_interests': org.partnership_interests,
            'funding_priorities': org.funding_priorities,
            'exclusions': org.exclusions or [],
            'faith_based': org.faith_based,
            'minority_led': org.minority_led,
            'woman_led': org.woman_led,
            'lgbtq_led': org.lgbtq_led,
            'veteran_led': org.veteran_led,
            'profile_completeness': getattr(org, 'profile_completeness', 0)
        }
        
        return jsonify(org_data)
        
    except Exception as e:
        logger.error(f"Error fetching organization profile: {e}")
        return jsonify({'error': str(e)}), 500