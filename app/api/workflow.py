"""
Grant Management Workflow API
Handles grant application lifecycle and status transitions
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
from app import db
from app.models.grant import Grant
from app.models.organization import Organization
from app.services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('workflow', __name__, url_prefix='/api/workflow')

# Grant workflow states
WORKFLOW_STATES = {
    'draft': ['in_progress', 'abandoned'],
    'in_progress': ['submitted', 'draft', 'abandoned'],
    'submitted': ['under_review', 'withdrawn'],
    'under_review': ['awarded', 'declined', 'more_info_needed'],
    'more_info_needed': ['under_review', 'withdrawn'],
    'awarded': ['completed'],
    'declined': [],
    'withdrawn': [],
    'abandoned': [],
    'completed': []
}

@bp.route('/grants/<int:grant_id>/status', methods=['PUT'])
def update_grant_status(grant_id):
    """Update grant status with workflow validation"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        # Get the grant
        grant = Grant.query.get_or_404(grant_id)
        current_status = grant.status or 'draft'
        
        # Validate workflow transition
        if new_status not in WORKFLOW_STATES.get(current_status, []):
            return jsonify({
                'error': f'Invalid transition from {current_status} to {new_status}',
                'allowed_transitions': WORKFLOW_STATES.get(current_status, [])
            }), 400
        
        # Update grant status
        grant.status = new_status
        
        # Update relevant dates
        if new_status == 'submitted':
            grant.date_submitted = datetime.now().date()
        elif new_status in ['awarded', 'declined']:
            grant.date_decision = datetime.now().date()
        
        # Add notes if provided
        if notes:
            existing_notes = grant.notes or ''
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            grant.notes = f"{existing_notes}\n[{timestamp}] Status changed to {new_status}: {notes}"
        
        db.session.commit()
        
        # Send notification for important status changes
        if new_status in ['submitted', 'awarded', 'declined']:
            NotificationService.send_status_update(grant, new_status)
        
        return jsonify({
            'success': True,
            'grant_id': grant_id,
            'new_status': new_status,
            'previous_status': current_status
        })
        
    except Exception as e:
        logger.error(f"Error updating grant status: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/grants/<int:grant_id>/attachments', methods=['POST'])
def add_attachment(grant_id):
    """Add document attachment to grant application"""
    try:
        grant = Grant.query.get_or_404(grant_id)
        
        # Handle file upload
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save file (implement secure file storage)
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', 'grants', str(grant_id), filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        
        # Store attachment metadata
        attachment_data = {
            'filename': filename,
            'path': file_path,
            'uploaded_at': datetime.now().isoformat(),
            'size': os.path.getsize(file_path),
            'type': request.form.get('type', 'general')
        }
        
        # Update grant attachments (stored as JSON)
        attachments = grant.attachments or []
        attachments.append(attachment_data)
        grant.attachments = attachments
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'attachment': attachment_data
        })
        
    except Exception as e:
        logger.error(f"Error adding attachment: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/grants/deadlines', methods=['GET'])
def get_upcoming_deadlines():
    """Get grants with upcoming deadlines"""
    try:
        # Get deadline range
        days = int(request.args.get('days', 30))
        deadline_date = datetime.now() + timedelta(days=days)
        
        # Query grants with deadlines
        grants = Grant.query.filter(
            Grant.deadline != None,
            Grant.deadline <= deadline_date,
            Grant.deadline >= datetime.now(),
            Grant.status.in_(['draft', 'in_progress'])
        ).order_by(Grant.deadline).all()
        
        # Group by urgency
        urgent = []  # < 7 days
        soon = []    # 7-14 days
        upcoming = [] # 14-30 days
        
        for grant in grants:
            days_until = (grant.deadline - datetime.now()).days
            grant_data = grant.to_dict()
            grant_data['days_until_deadline'] = days_until
            
            if days_until < 7:
                urgent.append(grant_data)
            elif days_until < 14:
                soon.append(grant_data)
            else:
                upcoming.append(grant_data)
        
        return jsonify({
            'urgent': urgent,
            'soon': soon,
            'upcoming': upcoming,
            'total': len(grants)
        })
        
    except Exception as e:
        logger.error(f"Error fetching deadlines: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/grants/<int:grant_id>/reminders', methods=['POST'])
def set_reminder(grant_id):
    """Set deadline reminder for a grant"""
    try:
        data = request.get_json()
        grant = Grant.query.get_or_404(grant_id)
        
        reminder_date = datetime.fromisoformat(data.get('reminder_date'))
        reminder_type = data.get('type', 'deadline')
        
        # Store reminder (implement with notification service)
        reminder = {
            'grant_id': grant_id,
            'date': reminder_date,
            'type': reminder_type,
            'created_at': datetime.now()
        }
        
        # Add to reminders table or notification queue
        NotificationService.schedule_reminder(reminder)
        
        return jsonify({
            'success': True,
            'reminder': reminder
        })
        
    except Exception as e:
        logger.error(f"Error setting reminder: {e}")
        return jsonify({'error': str(e)}), 500

from werkzeug.utils import secure_filename
import os