"""
Production Grants API
Serves real grant data with filtering and matching
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import text
from app import db
from app.models import Grant, Organization, LovedGrant
from app.services.grant_fetcher import GrantFetcher
from app.services.ai_service import AIService
from app.services.cache_service import CacheService
from app.services.auth_manager import AuthManager
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('grants', __name__)
grant_fetcher = GrantFetcher()
ai_service = AIService()
cache_service = CacheService()

# Insert after line 22:
@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))

        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503
        
@bp.route('/', methods=['GET'])
def get_grants():
    """Get all active grants with optional filtering"""
    try:
        # Check cache first
        cache_key = f"grants_{request.query_string.decode()}"
        cached_data = cache_service.get(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # Get filter parameters
        focus_area = request.args.get('focus_area')
        min_amount = request.args.get('min_amount', type=float)
        max_amount = request.args.get('max_amount', type=float)
        deadline_days = request.args.get('deadline_days', type=int)
        search = request.args.get('search')
        org_id = request.args.get('org_id', type=int)
        
        # Build query - show all grants if no specific status filter
        query = db.session.query(Grant)
        
        # Optional status filter
        status_filter = request.args.get('status')
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # Apply filters
        if focus_area:
            query = query.filter(Grant.geography.contains(focus_area))
        
        if min_amount:
            query = query.filter(Grant.amount_min >= min_amount)
        
        if max_amount:
            query = query.filter(Grant.amount_max <= max_amount)
        
        if deadline_days:
            deadline_date = datetime.now() + timedelta(days=deadline_days)
            query = query.filter(Grant.deadline <= deadline_date)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Grant.title.ilike(search_term),
                    Grant.eligibility.ilike(search_term),
                    Grant.funder.ilike(search_term)
                )
            )
        
        # Sort by match score if org_id provided, otherwise by deadline
        if org_id:
            query = query.order_by(Grant.match_score.desc())
        else:
            query = query.order_by(Grant.deadline.asc())
        
        # Execute query
        grants = query.limit(100).all()
        
        # Also get denominational grants from direct SQL query
        denominational_grants = []
        try:
            from sqlalchemy import text
            # Build denominational grants query
            denom_sql = "SELECT * FROM denominational_grants WHERE 1=1"
            params = {}
            
            if search:
                denom_sql += " AND (title ILIKE :search OR funder ILIKE :search OR eligibility ILIKE :search)"
                params['search'] = f"%{search}%"
            
            if min_amount:
                denom_sql += " AND amount_min >= :min_amount"
                params['min_amount'] = min_amount
            
            if max_amount:
                denom_sql += " AND amount_max <= :max_amount"
                params['max_amount'] = max_amount
                
            if deadline_days:
                denom_sql += " AND deadline <= :deadline"
                params['deadline'] = datetime.now() + timedelta(days=deadline_days)
                
            denom_sql += " ORDER BY deadline ASC NULLS LAST LIMIT 100"
            
            result = db.session.execute(text(denom_sql), params)
            for row in result:
                denom_grant = {
                    'id': f"denom_{row.id}",
                    'title': row.title,
                    'funder': row.funder,
                    'amount_min': float(row.amount_min) if row.amount_min else None,
                    'amount_max': float(row.amount_max) if row.amount_max else None,
                    'deadline': row.deadline.isoformat() if row.deadline else None,
                    'geography': row.geography,
                    'eligibility': row.eligibility,
                    'description': row.description,
                    'requirements': row.requirements,
                    'link': row.link,
                    'source_name': row.source_name,
                    'source_url': row.source_url,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                    'is_denominational': True
                }
                denominational_grants.append(denom_grant)
        except Exception as e:
            logger.warning(f"Could not fetch denominational grants: {e}")
        
        # Combine both grant lists
        all_grants = [grant.to_dict() for grant in grants] + denominational_grants
        
        # Format response
        response = {
            'success': True,
            'grants': all_grants,
            'count': len(all_grants),
            'regular_grants_count': len(grants),
            'denominational_grants_count': len(denominational_grants),
            'filters_applied': {
                'focus_area': focus_area,
                'min_amount': min_amount,
                'max_amount': max_amount,
                'deadline_days': deadline_days,
                'search': search
            }
        }
        
        # Cache the response
        cache_service.set(cache_key, response, ttl_seconds=300)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error fetching grants: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'grants': []
        }), 500

@bp.route('/<int:grant_id>', methods=['GET'])
def get_grant_detail(grant_id):
    """Get detailed information about a specific grant"""
    try:
        grant = db.session.query(Grant).get(grant_id)

        if not grant:
            return jsonify({
                'success': False,
                'error': 'Grant not found',
                'message': f'Grant with ID {grant_id} does not exist or has been removed.',
                'grant_id': grant_id,
                'suggestion': 'Browse available grants',
                'action': {
                    'type': 'redirect',
                    'url': '/grants',
                    'label': 'View All Grants'
                }
            }), 404

        # Get organization if user is logged in
        org_id = request.args.get('org_id', type=int)

        grant_dict = grant.to_dict()

        # Calculate match score if organization provided
        if org_id and ai_service.is_enabled():
            org = db.session.query(Organization).get(org_id)
            if org:
                score, explanation = ai_service.match_grant(
                    org.to_dict(),
                    grant_dict
                )
                grant_dict['match_score'] = score
                grant_dict['match_explanation'] = explanation

        return jsonify({
            'success': True,
            'grant': grant_dict
        })

    except Exception as e:
        logger.error(f"Error fetching grant detail: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500
        
        # Get organization if user is logged in
        org_id = request.args.get('org_id', type=int)
        
        grant_dict = grant.to_dict()
        
        # Calculate match score if organization provided
        if org_id and ai_service.is_enabled():
            org = db.session.query(Organization).get(org_id)
            if org:
                score, explanation = ai_service.match_grant(
                    org.to_dict(),
                    grant_dict
                )
                grant_dict['match_score'] = score
                grant_dict['match_explanation'] = explanation
        
        # Check if already applied
        if org_id:
            # TODO: Implement application tracking
            grant_dict['application_status'] = None
        
        return jsonify({
            'success': True,
            'grant': grant_dict
        })
        
    except Exception as e:
        logger.error(f"Error fetching grant detail: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/<int:grant_id>/save', methods=['POST'])
def save_grant(grant_id):
    """Save/bookmark a grant to user's dashboard using LovedGrant join table"""
    try:
        user = AuthManager.get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get the grant
        grant = db.session.query(Grant).get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Check if already saved by this user (duplicate prevention)
        existing_save = db.session.query(LovedGrant).filter_by(
            user_id=user.id,
            grant_id=grant_id
        ).first()
        
        if existing_save:
            return jsonify({
                'success': True,
                'message': 'Grant already saved',
                'grant': {
                    'id': grant.id,
                    'title': grant.title,
                    'funder': grant.funder,
                    'saved_at': existing_save.loved_at.isoformat() if existing_save.loved_at else None
                }
            }), 200
        
        # Create new LovedGrant entry (multi-tenant safe)
        loved_grant = LovedGrant()
        loved_grant.user_id = user.id
        loved_grant.grant_id = grant_id
        loved_grant.status = 'interested'
        loved_grant.loved_at = datetime.utcnow()
        
        db.session.add(loved_grant)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Grant saved successfully',
            'grant': {
                'id': grant.id,
                'title': grant.title,
                'funder': grant.funder,
                'saved_at': loved_grant.loved_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error saving grant: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to save grant'}), 500

@bp.route('/<int:grant_id>/unsave', methods=['DELETE', 'POST'])
def unsave_grant(grant_id):
    """Remove grant from user's saved list using LovedGrant join table"""
    try:
        user = AuthManager.get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Find the LovedGrant entry for this user and grant
        loved_grant = db.session.query(LovedGrant).filter_by(
            user_id=user.id,
            grant_id=grant_id
        ).first()
        
        if not loved_grant:
            return jsonify({'error': 'Saved grant not found'}), 404
        
        # Delete the LovedGrant entry (multi-tenant safe)
        db.session.delete(loved_grant)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Grant removed from saved list'
        })
        
    except Exception as e:
        logger.error(f"Error unsaving grant: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to unsave grant'}), 500

@bp.route('/saved', methods=['GET'])
def get_saved_grants():
    """Get all grants saved by current user using LovedGrant join table"""
    try:
        user = AuthManager.get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Query LovedGrant entries for this user, join with Grant table
        saved_entries = db.session.query(LovedGrant, Grant).join(
            Grant, LovedGrant.grant_id == Grant.id
        ).filter(
            LovedGrant.user_id == user.id
        ).order_by(LovedGrant.loved_at.desc()).all()
        
        grants_list = [{
            'id': grant.id,
            'title': grant.title,
            'funder': grant.funder,
            'deadline': grant.deadline.isoformat() if grant.deadline else None,
            'amount_min': float(grant.amount_min) if grant.amount_min else None,
            'amount_max': float(grant.amount_max) if grant.amount_max else None,
            'eligibility': grant.eligibility,
            'source_name': grant.source_name,
            'saved_at': loved.loved_at.isoformat() if loved.loved_at else None,
            'saved_status': loved.status,
            'notes': loved.notes,
            'progress_percentage': loved.progress_percentage
        } for loved, grant in saved_entries]
        
        return jsonify({
            'success': True,
            'count': len(grants_list),
            'grants': grants_list
        })
        
    except Exception as e:
        logger.error(f"Error fetching saved grants: {e}")
        return jsonify({'error': 'Failed to fetch saved grants'}), 500

@bp.route('/fetch', methods=['POST'])
def fetch_new_grants():
    """Fetch new grants from external sources"""
    try:
        # Limit to admin users in production
        # For now, allow all for testing
        
        limit = (request.json or {}).get('limit', 30)
        
        # Fetch grants from all sources
        result = grant_fetcher.fetch_all_grants(limit=limit)
        
        # Calculate match scores for default organization
        org_id = (request.json or {}).get('org_id')
        if org_id:
            grant_fetcher.calculate_match_scores(org_id)
        
        return jsonify({
            'success': True,
            'message': f"Fetched {result['fetched']} grants, stored {result['stored']} new grants",
            'stats': result['stats']
        })
        
    except Exception as e:
        logger.error(f"Error fetching new grants: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/<int:grant_id>/apply', methods=['POST'])
def apply_to_grant(grant_id):
    """Create or update application for a grant"""
    try:
        data = request.json or {}
        org_id = data.get('organization_id')
        
        if not org_id:
            return jsonify({
                'success': False,
                'error': 'Organization ID required'
            }), 400
        
        # Check if grant exists
        grant = db.session.query(Grant).get(grant_id)
        if not grant:
            return jsonify({
                'success': False,
                'error': 'Grant not found'
            }), 404
        
        # TODO: Implement application tracking when Application model is created
        
        return jsonify({
            'success': True,
            'message': 'Application feature coming soon'
        })
        
    except Exception as e:
        logger.error(f"Error applying to grant: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/<int:grant_id>/contact', methods=['PUT'])
def update_grant_contact(grant_id):
    """Update contact information for a specific grant"""
    try:
        grant = db.session.query(Grant).get(grant_id)
        
        if not grant:
            return jsonify({
                'success': False,
                'error': 'Grant not found'
            }), 404
        
        data = request.json or {}
        
        # Update contact fields
        if 'contact_name' in data:
            grant.contact_name = data['contact_name'] or None
        if 'contact_email' in data:
            grant.contact_email = data['contact_email'] or None
        if 'contact_phone' in data:
            grant.contact_phone = data['contact_phone'] or None
        if 'contact_department' in data:
            grant.contact_department = data['contact_department'] or None
        if 'organization_website' in data:
            grant.organization_website = data['organization_website'] or None
        if 'application_url' in data:
            grant.application_url = data['application_url'] or None
        
        # Set confidence based on how much data we have
        contact_fields = [
            grant.contact_name,
            grant.contact_email,
            grant.contact_phone,
            grant.contact_department,
            grant.organization_website,
            grant.application_url
        ]
        filled_fields = sum(1 for field in contact_fields if field)
        
        if filled_fields >= 5:
            grant.contact_confidence = 'high'
        elif filled_fields >= 3:
            grant.contact_confidence = 'medium'
        else:
            grant.contact_confidence = 'low'
        
        # Set verified date when contact info is updated
        if filled_fields > 0:
            grant.contact_verified_date = datetime.utcnow()
        
        # Update the updated_at timestamp
        grant.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact information updated successfully',
            'grant': grant.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating grant contact: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/stats', methods=['GET'])
def get_grant_stats():
    """Get statistics about grants in the system"""
    try:
        total_grants = db.session.query(Grant).count()
        active_grants = db.session.query(Grant).filter_by(status='active').count()
        
        # Get grants by source (filter out None values)
        sources = db.session.query(
            Grant.source_name,
            db.func.count(Grant.id)
        ).filter(Grant.source_name.isnot(None)).group_by(Grant.source_name).all()
        
        # Get grants by geography since focus_area doesn't exist in model (filter out None values)
        geographies = db.session.query(
            Grant.geography,
            db.func.count(Grant.id)
        ).filter(Grant.geography.isnot(None)).group_by(Grant.geography).all()
        
        # Calculate average amount using amount_max field
        avg_amount = db.session.query(db.func.avg(Grant.amount_max)).scalar() or 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_grants': total_grants,
                'active_grants': active_grants,
                'average_amount': float(avg_amount),
                'by_source': dict(sources),
                'by_geography': dict(geographies),
                'last_updated': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting grant stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/recommended/<int:org_id>', methods=['GET'])
def get_recommended_grants(org_id):
    """Get AI-recommended grants for an organization"""
    try:
        if not ai_service.is_enabled():
            return jsonify({
                'success': False,
                'error': 'AI service not available'
            }), 503
        
        # Get organization
        org = db.session.query(Organization).get(org_id)
        if not org:
            return jsonify({
                'success': False,
                'error': 'Organization not found'
            }), 404
        
        # Get active grants
        grants = db.session.query(Grant).filter_by(status='active').limit(50).all()
        
        # Calculate match scores
        recommendations = []
        for grant in grants:
            score, explanation = ai_service.match_grant(
                org.to_dict(),
                grant.to_dict()
            )
            
            if score is not None and score >= 3:  # Only recommend good matches
                grant_dict = grant.to_dict()
                grant_dict['match_score'] = score
                grant_dict['match_explanation'] = explanation
                recommendations.append(grant_dict)
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations[:20],  # Top 20 matches
            'organization': org.name
        })
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500