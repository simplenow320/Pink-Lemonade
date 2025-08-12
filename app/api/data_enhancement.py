from flask import Blueprint, request, jsonify
from app import db
from app.models import Grant, Organization
from app.services.enhanced_grant_fetcher import enhanced_grant_fetcher
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("data_enhancement", __name__)

@bp.route('/api/data/enhance-grants', methods=['POST'])
def enhance_grant_data():
    """
    Enhance existing grants with comprehensive details using the enhanced fetcher
    """
    try:
        data = request.get_json() or {}
        keyword = data.get('keyword', 'nonprofit')
        limit = data.get('limit', 10)
        
        # Fetch comprehensive grant data
        enhanced_grants = enhanced_grant_fetcher.fetch_comprehensive_grants(keyword, limit)
        
        # Save enhanced grants to database
        saved_count = 0
        for grant_data in enhanced_grants:
            try:
                # Check if grant already exists
                existing = Grant.query.filter_by(
                    title=grant_data['title'],
                    funder=grant_data['funder']
                ).first()
                
                if not existing:
                    grant = Grant(
                        title=grant_data['title'],
                        funder=grant_data['funder'],
                        link=grant_data.get('link', ''),
                        deadline=grant_data.get('deadline'),
                        amount_min=grant_data.get('amount_min'),
                        amount_max=grant_data.get('amount_max'),
                        org_id=1,  # Default org
                        source_name=grant_data.get('source', 'Enhanced Fetcher'),
                        source_url=grant_data.get('link', ''),
                        ai_summary=grant_data.get('description', ''),
                        status='idea',
                        # Enhanced fields stored in ai_summary for now
                        eligibility=grant_data.get('eligibility_criteria', ''),
                        geography=grant_data.get('geographic_scope', '')
                    )
                    db.session.add(grant)
                    db.session.commit()
                    saved_count += 1
                    
            except Exception as e:
                logger.error(f"Error saving enhanced grant: {e}")
                db.session.rollback()
                continue
        
        return jsonify({
            'success': True,
            'message': f'Enhanced and saved {saved_count} grants',
            'total_fetched': len(enhanced_grants),
            'saved_count': saved_count
        })
        
    except Exception as e:
        logger.error(f"Error enhancing grant data: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/data/organization-completeness', methods=['GET'])
def check_organization_completeness():
    """
    Check the completeness of organization data for better AI analysis
    """
    try:
        org = Organization.query.first()
        
        if not org:
            return jsonify({
                'success': False,
                'message': 'No organization found',
                'completeness': 0,
                'missing_fields': ['All organization data missing']
            })
        
        # Check completeness of key fields for AI analysis
        key_fields = {
            'mission': org.mission,
            'primary_focus_areas': org.primary_focus_areas,
            'programs_services': org.programs_services,
            'annual_budget_range': org.annual_budget_range,
            'staff_size': org.staff_size,
            'service_area_type': org.service_area_type,
            'target_demographics': org.target_demographics,
            'ein': org.ein,
            'org_type': org.org_type,
            'website': org.website,
            'primary_city': org.primary_city,
            'primary_state': org.primary_state
        }
        
        total_fields = len(key_fields)
        completed_fields = sum(1 for value in key_fields.values() if value)
        completeness = (completed_fields / total_fields) * 100
        
        missing_fields = [field for field, value in key_fields.items() if not value]
        
        return jsonify({
            'success': True,
            'organization_name': org.name,
            'completeness': round(completeness, 1),
            'completed_fields': completed_fields,
            'total_fields': total_fields,
            'missing_fields': missing_fields,
            'recommendations': get_data_recommendations(missing_fields)
        })
        
    except Exception as e:
        logger.error(f"Error checking organization completeness: {e}")
        return jsonify({'error': str(e)}), 500

def get_data_recommendations(missing_fields):
    """
    Provide specific recommendations for improving data quality
    """
    recommendations = []
    
    field_importance = {
        'mission': 'Critical - AI needs mission statement to assess grant alignment',
        'primary_focus_areas': 'Critical - Required for matching grant focus areas',
        'programs_services': 'High - Helps AI understand your work and capabilities',
        'annual_budget_range': 'High - Essential for grant amount matching',
        'target_demographics': 'High - Important for demographic-specific grants',
        'service_area_type': 'Medium - Helps with geographic grant matching',
        'staff_size': 'Medium - Indicates organizational capacity',
        'org_type': 'Medium - Important for eligibility requirements',
        'ein': 'Medium - Required for most federal grants',
        'website': 'Low - Provides additional context',
        'primary_city': 'Low - Helps with local grant opportunities',
        'primary_state': 'Low - Helps with state-specific grants'
    }
    
    for field in missing_fields:
        if field in field_importance:
            recommendations.append({
                'field': field,
                'importance': field_importance[field],
                'action': f'Complete {field.replace("_", " ")} in organization profile'
            })
    
    return recommendations

@bp.route('/api/data/grant-data-quality', methods=['GET'])
def assess_grant_data_quality():
    """
    Assess the quality and completeness of grant data for AI analysis
    """
    try:
        grants = Grant.query.all()
        
        if not grants:
            return jsonify({
                'success': False,
                'message': 'No grants found in database'
            })
        
        quality_metrics = {
            'total_grants': len(grants),
            'grants_with_descriptions': 0,
            'grants_with_deadlines': 0,
            'grants_with_amounts': 0,
            'grants_with_links': 0,
            'grants_with_eligibility': 0,
            'average_description_length': 0,
            'data_quality_score': 0
        }
        
        description_lengths = []
        
        for grant in grants:
            if grant.ai_summary:
                quality_metrics['grants_with_descriptions'] += 1
                description_lengths.append(len(grant.ai_summary))
            
            if grant.deadline:
                quality_metrics['grants_with_deadlines'] += 1
                
            if grant.amount_min or grant.amount_max:
                quality_metrics['grants_with_amounts'] += 1
                
            if grant.link:
                quality_metrics['grants_with_links'] += 1
                
            if grant.eligibility:
                quality_metrics['grants_with_eligibility'] += 1
        
        if description_lengths:
            quality_metrics['average_description_length'] = sum(description_lengths) / len(description_lengths)
        
        # Calculate overall data quality score
        total_possible = len(grants) * 5  # 5 key data points per grant
        total_present = (quality_metrics['grants_with_descriptions'] + 
                        quality_metrics['grants_with_deadlines'] + 
                        quality_metrics['grants_with_amounts'] + 
                        quality_metrics['grants_with_links'] + 
                        quality_metrics['grants_with_eligibility'])
        
        quality_metrics['data_quality_score'] = round((total_present / total_possible) * 100, 1)
        
        # Recommendations for improvement
        recommendations = []
        
        if quality_metrics['grants_with_descriptions'] < len(grants) * 0.8:
            recommendations.append('Enhance grant descriptions - many grants lack detailed information')
            
        if quality_metrics['grants_with_deadlines'] < len(grants) * 0.6:
            recommendations.append('Add deadline information - critical for application planning')
            
        if quality_metrics['grants_with_amounts'] < len(grants) * 0.5:
            recommendations.append('Include funding amounts - essential for budget planning')
            
        if quality_metrics['average_description_length'] < 200:
            recommendations.append('Expand grant descriptions - current descriptions are too brief for good AI analysis')
        
        return jsonify({
            'success': True,
            'quality_metrics': quality_metrics,
            'recommendations': recommendations,
            'next_steps': [
                'Use enhanced grant fetcher to collect more detailed data',
                'Regularly update grant information',
                'Focus on grants with complete eligibility criteria'
            ]
        })
        
    except Exception as e:
        logger.error(f"Error assessing grant data quality: {e}")
        return jsonify({'error': str(e)}), 500