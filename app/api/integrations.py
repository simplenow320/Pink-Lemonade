"""
Advanced Integration API Endpoints
Calendar, CRM, and Document Management
"""

from flask import Blueprint, jsonify, request, send_file
from app.services.integration_service import IntegrationService
import logging

logger = logging.getLogger(__name__)

integrations_bp = Blueprint('integrations', __name__, url_prefix='/api/integrations')
integration_service = IntegrationService()

@integrations_bp.route('/available', methods=['GET'])
def get_available_integrations():
    """Get list of available integrations"""
    try:
        result = integration_service.get_available_integrations()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting integrations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrations_bp.route('/calendar/sync', methods=['POST'])
def sync_calendar():
    """Sync grant deadlines with calendar"""
    try:
        data = request.json
        org_id = data.get('org_id', 1)
        calendar_service = data.get('service', 'google_calendar')
        
        result = integration_service.sync_calendar_events(org_id, calendar_service)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error syncing calendar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrations_bp.route('/crm/sync', methods=['POST'])
def sync_crm():
    """Sync contacts with CRM"""
    try:
        data = request.json
        org_id = data.get('org_id', 1)
        crm_service = data.get('service', 'salesforce')
        
        result = integration_service.sync_crm_contacts(org_id, crm_service)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error syncing CRM: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrations_bp.route('/documents', methods=['POST'])
def manage_documents():
    """Manage grant documents"""
    try:
        data = request.json
        org_id = data.get('org_id', 1)
        action = data.get('action', 'list')
        document_data = data.get('document_data', {})
        
        result = integration_service.manage_documents(org_id, action, document_data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error managing documents: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrations_bp.route('/email/templates', methods=['GET'])
def get_email_templates():
    """Get email templates"""
    try:
        org_id = request.args.get('org_id', 1, type=int)
        result = integration_service.setup_email_templates(org_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrations_bp.route('/status', methods=['GET'])
def get_integration_status():
    """Get status of all integrations"""
    try:
        org_id = request.args.get('org_id', 1, type=int)
        result = integration_service.get_integration_status(org_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrations_bp.route('/export', methods=['GET'])
def export_data():
    """Export grant data"""
    try:
        org_id = request.args.get('org_id', 1, type=int)
        format = request.args.get('format', 'csv')
        
        result = integration_service.export_data(org_id, format)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrations_bp.route('/connect/<service>', methods=['POST'])
def connect_service(service):
    """Connect to external service"""
    try:
        data = request.json
        org_id = data.get('org_id', 1)
        credentials = data.get('credentials', {})
        
        # Validate service
        valid_services = [
            'google_calendar', 'outlook_calendar', 'salesforce',
            'hubspot', 'pipedrive', 'google_drive', 'dropbox',
            'gmail', 'outlook'
        ]
        
        if service not in valid_services:
            return jsonify({
                'success': False,
                'error': 'Invalid service'
            }), 400
        
        # Store connection (would save to database)
        return jsonify({
            'success': True,
            'service': service,
            'connected': True,
            'message': f'Successfully connected to {service}'
        })
        
    except Exception as e:
        logger.error(f"Error connecting service: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integrations_bp.route('/disconnect/<service>', methods=['POST'])
def disconnect_service(service):
    """Disconnect from external service"""
    try:
        data = request.json
        org_id = data.get('org_id', 1)
        
        # Remove connection (would update database)
        return jsonify({
            'success': True,
            'service': service,
            'connected': False,
            'message': f'Disconnected from {service}'
        })
        
    except Exception as e:
        logger.error(f"Error disconnecting service: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500