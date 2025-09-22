"""Organizations API endpoints for profile retrieval and management"""
from flask import Blueprint, jsonify, request, session
from app.models import Organization, User
from app import db
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('organizations', __name__, url_prefix='/api/organizations')

@bp.route('/', methods=['GET'])
def list_organizations():
    """List all organizations (public endpoint for discovery)"""
    try:
        # Get all organizations
        orgs = Organization.query.limit(100).all()
        
        organizations = []
        for org in orgs:
            organizations.append({
                'id': org.id,
                'name': org.name,
                'mission': org.mission,
                'focus_areas': org.primary_focus_areas or [],
                'location': f"{org.primary_city}, {org.primary_state}" if org.primary_city else org.primary_state,
                'website': org.website
            })
        
        return jsonify({
            'success': True,
            'organizations': organizations,
            'count': len(organizations)
        })
        
    except Exception as e:
        logger.error(f"Error listing organizations: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'organizations': []
        }), 500

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

@bp.route('/profile', methods=['POST'])
def create_or_update_organization_profile():
    """Create or update organization profile"""
    try:
        # Get the current user (you might want to implement proper auth checking)
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Check if organization already exists for this user
        org = Organization.query.filter_by(created_by_user_id=user_id).first()
        
        if not org:
            # Create new organization
            org = Organization()
            org.created_by_user_id = user_id
        
        # Update organization fields
        org.name = data.get('name', org.name)
        org.legal_name = data.get('legal_name', org.legal_name)
        org.ein = data.get('ein', org.ein)
        org.org_type = data.get('org_type', org.org_type)
        org.year_founded = data.get('year_founded', org.year_founded)
        org.website = data.get('website', org.website)
        org.mission = data.get('mission', org.mission)
        org.vision = data.get('vision', org.vision)
        org.values = data.get('values', org.values)
        org.primary_focus_areas = data.get('primary_focus_areas', org.primary_focus_areas)
        org.secondary_focus_areas = data.get('secondary_focus_areas', org.secondary_focus_areas)
        org.programs_services = data.get('programs_services', org.programs_services)
        org.target_demographics = data.get('target_demographics', org.target_demographics)
        org.age_groups_served = data.get('age_groups_served', org.age_groups_served)
        org.service_area_type = data.get('service_area_type', org.service_area_type)
        org.primary_city = data.get('primary_city', org.primary_city)
        org.primary_state = data.get('primary_state', org.primary_state)
        org.primary_zip = data.get('primary_zip', org.primary_zip)
        org.counties_served = data.get('counties_served', org.counties_served)
        org.states_served = data.get('states_served', org.states_served)
        org.annual_budget_range = data.get('annual_budget_range', org.annual_budget_range)
        org.staff_size = data.get('staff_size', org.staff_size)
        org.volunteer_count = data.get('volunteer_count', org.volunteer_count)
        org.board_size = data.get('board_size', org.board_size)
        org.people_served_annually = data.get('people_served_annually', org.people_served_annually)
        org.key_achievements = data.get('key_achievements', org.key_achievements)
        org.impact_metrics = data.get('impact_metrics', org.impact_metrics)
        org.previous_funders = data.get('previous_funders', org.previous_funders)
        org.typical_grant_size = data.get('typical_grant_size', org.typical_grant_size)
        org.grant_success_rate = data.get('grant_success_rate', org.grant_success_rate)
        org.preferred_grant_types = data.get('preferred_grant_types', org.preferred_grant_types)
        org.grant_writing_capacity = data.get('grant_writing_capacity', org.grant_writing_capacity)
        org.faith_based = data.get('faith_based', org.faith_based)
        org.minority_led = data.get('minority_led', org.minority_led)
        org.woman_led = data.get('woman_led', org.woman_led)
        org.lgbtq_led = data.get('lgbtq_led', org.lgbtq_led)
        org.veteran_led = data.get('veteran_led', org.veteran_led)
        org.keywords = data.get('keywords', org.keywords)
        org.unique_capabilities = data.get('unique_capabilities', org.unique_capabilities)
        org.partnership_interests = data.get('partnership_interests', org.partnership_interests)
        org.funding_priorities = data.get('funding_priorities', org.funding_priorities)
        org.exclusions = data.get('exclusions', org.exclusions)

        # Calculate profile completeness
        org.calculate_completeness()
        org.last_profile_update = db.func.now()

        # If this is a new organization, add to session
        if org.id is None:
            db.session.add(org)

        db.session.commit()

        logger.info(f"Organization profile {'created' if org.id else 'updated'} for user {user_id}: {org.name}")

        # Return the updated organization data
        return jsonify(org.to_dict()), 201 if org.id else 200
        
    except Exception as e:
        logger.error(f"Error creating/updating organization profile: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:org_id>', methods=['GET'])
def get_organization_by_id(org_id):
    """Get organization profile by ID"""
    try:
        org = Organization.query.get(org_id)
        
        if not org:
            return jsonify({
                'error': 'Organization not found',
                'message': f'No organization found with ID {org_id}'
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
        logger.error(f"Error fetching organization {org_id}: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/me', methods=['GET'])
def get_my_organization():
    """Get organization profile for the current logged-in user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'error': 'Not authenticated',
                'message': 'Please log in to view your organization'
            }), 401
        
        # Get user's organization
        org = Organization.query.filter_by(user_id=user_id).first()
        
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
        logger.error(f"Error fetching user organization: {e}")
        return jsonify({'error': str(e)}), 500