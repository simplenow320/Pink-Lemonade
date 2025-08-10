from flask import Blueprint, request, jsonify
from app import db
from app.models import Grant
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("grants", __name__)

@bp.route('/tracker', methods=['GET'])
def get_grants_for_tracker():
    """Get all grants from database for the grant tracker"""
    try:
        # Fetch all grants from database
        grants = Grant.query.all()
        
        grants_data = []
        for grant in grants:
            grants_data.append({
                'id': grant.id,
                'title': grant.title or 'Untitled Grant',
                'funder': grant.funder or 'Unknown Funder',
                'deadline': grant.deadline.isoformat() if grant.deadline else None,
                'amount_min': grant.amount_min,
                'amount_max': grant.amount_max,
                'status': grant.status or 'available',
                'focus_area': grant.focus_area,
                'description': grant.description,
                'url': grant.url
            })
        
        # Sort by deadline (earliest first, nulls last)
        grants_data.sort(key=lambda x: (x['deadline'] is None, x['deadline'] or '9999-12-31'))
        
        return jsonify({
            'success': True,
            'grants': grants_data,
            'total_count': len(grants_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching grants for tracker: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/update-status', methods=['POST'])
def update_grant_status():
    """Update the status of a specific grant"""
    try:
        data = request.get_json()
        grant_id = data.get('grant_id')
        new_status = data.get('status')
        
        if not grant_id or not new_status:
            return jsonify({'error': 'Grant ID and status are required'}), 400
        
        valid_statuses = ['available', 'drafting', 'submitted', 'won', 'lost']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
        
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        grant.status = new_status
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Grant status updated to {new_status}',
            'grant_id': grant_id,
            'status': new_status
        })
        
    except Exception as e:
        logger.error(f"Error updating grant status: {e}")
        return jsonify({'error': str(e)}), 500