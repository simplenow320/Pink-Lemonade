from flask import Blueprint, request, jsonify
from app import db
from app.models import Grant, Organization
from app.services.comprehensive_grant_scraper import comprehensive_scraper
from app.services.funder_intelligence import funder_intelligence
from app.services.enhanced_grant_fetcher import enhanced_grant_fetcher
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("enhanced_grant_data", __name__)

@bp.route('/api/grants/enhance/<int:grant_id>', methods=['POST'])
def enhance_single_grant(grant_id):
    """
    Enhance a single grant with comprehensive data scraping
    """
    try:
        grant = Grant.query.get_or_404(grant_id)
        
        if not grant.link:
            return jsonify({
                'success': False,
                'error': 'Grant has no source URL to enhance from'
            }), 400
        
        # Scrape comprehensive details from the grant URL
        enhanced_data = comprehensive_scraper.extract_full_grant_details(grant.link)
        
        if enhanced_data:
            # Update grant with enhanced information
            if enhanced_data.get('program_description'):
                grant.ai_summary = enhanced_data['program_description']
            
            if enhanced_data.get('individual_award_range'):
                # Parse award range if available
                try:
                    range_text = enhanced_data['individual_award_range']
                    amounts = [float(x.replace('$', '').replace(',', '')) for x in range_text.split('-')]
                    if len(amounts) >= 2:
                        grant.amount_min = amounts[0]
                        grant.amount_max = amounts[1]
                except:
                    pass
            
            if enhanced_data.get('deadline'):
                grant.deadline = enhanced_data['deadline']
            
            # Store additional details in JSON fields (if available)
            grant.eligibility = str(enhanced_data.get('eligibility_details', {}))
            grant.geography = enhanced_data.get('geographic_restrictions', '')
            
            db.session.commit()
            
            # Get funder intelligence
            funder_profile = funder_intelligence.get_funder_profile(
                grant.funder, 
                grant.link
            )
            
            return jsonify({
                'success': True,
                'message': 'Grant enhanced successfully',
                'enhanced_data': {
                    'grant_details': enhanced_data,
                    'funder_profile': funder_profile,
                    'contact_strategy': funder_intelligence.get_funder_contact_strategy(grant.funder)
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Unable to extract additional information from grant source'
            }), 400
            
    except Exception as e:
        logger.error(f"Error enhancing grant {grant_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/grants/discover-enhanced', methods=['POST'])
def discover_enhanced_grants():
    """
    Discover grants using the enhanced fetcher with comprehensive data
    """
    try:
        data = request.get_json() or {}
        keyword = data.get('keyword', 'nonprofit')
        limit = data.get('limit', 10)
        
        # Use enhanced grant fetcher
        comprehensive_grants = enhanced_grant_fetcher.fetch_comprehensive_grants(keyword, limit)
        
        saved_grants = []
        for grant_data in comprehensive_grants:
            try:
                # Check if grant already exists
                existing = Grant.query.filter_by(
                    title=grant_data['title'],
                    funder=grant_data['funder']
                ).first()
                
                if not existing:
                    # Create new grant with enhanced data
                    grant = Grant(
                        title=grant_data['title'],
                        funder=grant_data['funder'],
                        link=grant_data.get('link', ''),
                        deadline=grant_data.get('deadline'),
                        amount_min=grant_data.get('amount_min'),
                        amount_max=grant_data.get('amount_max'),
                        org_id=None,  # No org requirement
                        source_name=grant_data.get('source', 'Enhanced Discovery'),
                        source_url=grant_data.get('link', ''),
                        ai_summary=grant_data.get('program_description', grant_data.get('description', '')),
                        status='idea',
                        eligibility=grant_data.get('eligibility_criteria', ''),
                        geography=grant_data.get('geographic_scope', '')
                    )
                    
                    db.session.add(grant)
                    db.session.commit()
                    
                    # Get funder intelligence for each grant
                    funder_profile = funder_intelligence.get_funder_profile(grant.funder, grant.link)
                    
                    saved_grants.append({
                        'grant': {
                            'id': grant.id,
                            'title': grant.title,
                            'funder': grant.funder,
                            'amount_range': f"${grant.amount_min or 0:,} - ${grant.amount_max or 0:,}",
                            'deadline': grant.deadline,
                            'source': grant.source_name
                        },
                        'enhanced_data': grant_data,
                        'funder_intelligence': funder_profile
                    })
                    
            except Exception as e:
                logger.error(f"Error saving enhanced grant: {e}")
                db.session.rollback()
                continue
        
        return jsonify({
            'success': True,
            'message': f'Discovered and saved {len(saved_grants)} enhanced grants',
            'grants': saved_grants,
            'total_discovered': len(comprehensive_grants)
        })
        
    except Exception as e:
        logger.error(f"Error in enhanced grant discovery: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/funder/<int:grant_id>/intelligence', methods=['GET'])
def get_funder_intelligence(grant_id):
    """
    Get comprehensive funder intelligence for a specific grant
    """
    try:
        grant = Grant.query.get_or_404(grant_id)
        
        # Get comprehensive funder profile
        funder_profile = funder_intelligence.get_funder_profile(grant.funder, grant.link)
        
        # Get contact strategy
        contact_strategy = funder_intelligence.get_funder_contact_strategy(grant.funder)
        
        return jsonify({
            'success': True,
            'grant': {
                'id': grant.id,
                'title': grant.title,
                'funder': grant.funder
            },
            'funder_profile': funder_profile,
            'contact_strategy': contact_strategy,
            'recommendations': {
                'approach': f"This is a {funder_profile['type']} funder. {contact_strategy['recommended_approach']}",
                'timeline': contact_strategy['timing_recommendations'],
                'key_points': contact_strategy['key_talking_points'],
                'next_steps': [
                    f"Contact via {contact_strategy['best_contact_method']}",
                    "Prepare materials based on funder preferences",
                    "Follow up according to timeline recommendations"
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting funder intelligence for grant {grant_id}: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/data/quality-report', methods=['GET'])
def get_data_quality_report():
    """
    Generate comprehensive data quality report
    """
    try:
        # Grant data analysis
        grants = Grant.query.all()
        total_grants = len(grants)
        
        # Analyze data completeness
        grants_with_descriptions = sum(1 for g in grants if g.ai_summary and len(g.ai_summary) > 100)
        grants_with_amounts = sum(1 for g in grants if g.amount_min or g.amount_max)
        grants_with_deadlines = sum(1 for g in grants if g.deadline)
        grants_with_links = sum(1 for g in grants if g.link)
        grants_with_eligibility = sum(1 for g in grants if g.eligibility)
        
        # Organization data analysis
        org = Organization.query.first()
        org_completeness = 0
        org_missing_fields = []
        
        if org:
            key_fields = ['mission', 'primary_focus_areas', 'programs_services', 'annual_budget_range', 'staff_size']
            completed_fields = sum(1 for field in key_fields if getattr(org, field, None))
            org_completeness = (completed_fields / len(key_fields)) * 100
            org_missing_fields = [field for field in key_fields if not getattr(org, field, None)]
        
        # Data quality score
        if total_grants > 0:
            grant_quality_score = (
                (grants_with_descriptions / total_grants * 25) +
                (grants_with_amounts / total_grants * 25) +
                (grants_with_deadlines / total_grants * 25) +
                (grants_with_eligibility / total_grants * 25)
            )
        else:
            grant_quality_score = 0
        
        overall_score = (grant_quality_score * 0.7) + (org_completeness * 0.3)
        
        # Recommendations
        recommendations = []
        
        if grant_quality_score < 60:
            recommendations.append({
                'priority': 'High',
                'area': 'Grant Data Quality',
                'action': 'Use enhanced grant discovery to collect more detailed grant information',
                'impact': 'Better AI analysis and matching'
            })
        
        if org_completeness < 70:
            recommendations.append({
                'priority': 'High',
                'area': 'Organization Profile',
                'action': 'Complete missing organization profile fields',
                'impact': 'Improved grant matching accuracy'
            })
        
        if grants_with_eligibility < total_grants * 0.5:
            recommendations.append({
                'priority': 'Medium',
                'area': 'Eligibility Information',
                'action': 'Enhance grants with detailed eligibility criteria',
                'impact': 'Better application decision-making'
            })
        
        return jsonify({
            'success': True,
            'overall_score': round(overall_score, 1),
            'grant_data': {
                'total_grants': total_grants,
                'quality_score': round(grant_quality_score, 1),
                'completeness': {
                    'descriptions': f"{grants_with_descriptions}/{total_grants}",
                    'amounts': f"{grants_with_amounts}/{total_grants}",
                    'deadlines': f"{grants_with_deadlines}/{total_grants}",
                    'eligibility': f"{grants_with_eligibility}/{total_grants}"
                }
            },
            'organization_data': {
                'completeness_score': round(org_completeness, 1),
                'missing_fields': org_missing_fields
            },
            'recommendations': recommendations,
            'enhancement_options': [
                {
                    'method': 'Enhanced Grant Discovery',
                    'description': 'Use AI-powered scraping to collect comprehensive grant details',
                    'endpoint': '/api/grants/discover-enhanced'
                },
                {
                    'method': 'Individual Grant Enhancement',
                    'description': 'Enhance specific grants with detailed information',
                    'endpoint': '/api/grants/enhance/{grant_id}'
                },
                {
                    'method': 'Funder Intelligence',
                    'description': 'Get comprehensive funder profiles and contact strategies',
                    'endpoint': '/api/funder/{grant_id}/intelligence'
                }
            ]
        })
        
    except Exception as e:
        logger.error(f"Error generating data quality report: {e}")
        return jsonify({'error': str(e)}), 500