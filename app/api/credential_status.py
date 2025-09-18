"""
Credential Status API
Provides endpoints for checking and managing API credentials
"""

import logging
from flask import Blueprint, jsonify, request
from app.services.credential_manager import get_credential_manager

logger = logging.getLogger(__name__)

credential_status_bp = Blueprint('credential_status', __name__)

@credential_status_bp.route('/api/credentials/status')
def get_credential_status():
    """Get comprehensive credential status report"""
    try:
        credential_manager = get_credential_manager()
        report = credential_manager.get_service_status_report()
        
        return jsonify({
            'status': 'success',
            'data': report
        })
        
    except Exception as e:
        logger.error(f"Error getting credential status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@credential_status_bp.route('/api/credentials/missing')
def get_missing_credentials():
    """Get list of missing credentials"""
    try:
        credential_manager = get_credential_manager()
        
        # Get priority filter from query params
        priority = request.args.get('priority')
        if priority == 'critical':
            missing = credential_manager.get_critical_missing_credentials()
        elif priority == 'high':
            missing = credential_manager.get_high_priority_missing_credentials()
        else:
            missing = credential_manager.get_missing_credentials()
        
        return jsonify({
            'status': 'success',
            'data': {
                'missing_credentials': missing,
                'count': len(missing)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting missing credentials: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@credential_status_bp.route('/api/credentials/validate/<credential_id>')
def validate_specific_credential(credential_id):
    """Validate a specific credential"""
    try:
        credential_manager = get_credential_manager()
        status, message = credential_manager.validate_credential(credential_id)
        
        return jsonify({
            'status': 'success',
            'data': {
                'credential_id': credential_id,
                'validation_status': status.value,
                'message': message,
                'has_value': bool(credential_manager.get_credential(credential_id))
            }
        })
        
    except Exception as e:
        logger.error(f"Error validating credential {credential_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@credential_status_bp.route('/api/credentials/services/enabled')
def get_enabled_services():
    """Get list of enabled services based on available credentials"""
    try:
        credential_manager = get_credential_manager()
        report = credential_manager.get_service_status_report()
        
        return jsonify({
            'status': 'success',
            'data': {
                'enabled_services': report['enabled_services'],
                'total_enabled': len(report['enabled_services']),
                'disabled_services': report['disabled_services'],
                'total_disabled': len(report['disabled_services'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting enabled services: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@credential_status_bp.route('/api/credentials/setup-guide')
def get_setup_guide():
    """Get credential setup guide with next steps"""
    try:
        credential_manager = get_credential_manager()
        
        # Get high priority missing credentials for setup guidance
        high_priority_missing = credential_manager.get_high_priority_missing_credentials()
        
        setup_steps = []
        for cred in high_priority_missing:
            step = {
                'credential_id': cred['credential_id'],
                'name': cred['name'],
                'service': cred['service_name'],
                'description': cred['description'],
                'env_var': cred['env_var'],
                'setup_url': cred['setup_url'],
                'priority': cred['priority'],
                'instructions': f"1. Visit {cred['setup_url'] or 'the service website'}\n2. Create an account or sign in\n3. Generate an API key\n4. Add it to Replit Secrets as {cred['env_var']}"
            }
            setup_steps.append(step)
        
        return jsonify({
            'status': 'success',
            'data': {
                'setup_steps': setup_steps,
                'total_steps': len(setup_steps),
                'next_actions': credential_manager._generate_next_steps(credential_manager.check_all_credentials())
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting setup guide: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500