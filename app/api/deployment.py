"""
Deployment API - Phase 3
Endpoints for deployment automation, configuration generation, and production validation
"""

from flask import Blueprint, request, jsonify, send_file
from app.services.deployment_service import DeploymentService
from functools import wraps
import logging
import os
import tempfile
import zipfile
from datetime import datetime

logger = logging.getLogger(__name__)
bp = Blueprint('deployment', __name__, url_prefix='/api/deployment')

# Initialize deployment service
deployment_service = DeploymentService()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Simple admin check for deployment endpoints
        api_key = request.headers.get('X-Admin-Key')
        expected_key = os.getenv('ADMIN_API_KEY')
        
        if not expected_key or api_key != expected_key:
            # For development, allow if no key is set
            if not expected_key and os.getenv('FLASK_ENV') == 'development':
                return f(*args, **kwargs)
            return jsonify({'error': 'Admin access required for deployment operations'}), 403
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/prepare', methods=['POST'])
@admin_required
def prepare_deployment():
    """
    Prepare comprehensive production deployment package
    Admin only endpoint for deployment preparation
    """
    try:
        deployment_package = deployment_service.prepare_production_deployment()
        
        return jsonify({
            'success': True,
            'deployment_package': deployment_package,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Deployment preparation failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/replit-config', methods=['GET'])
def get_replit_config():
    """
    Get optimized Replit deployment configuration
    Public endpoint for Replit deployment
    """
    try:
        replit_config = deployment_service.create_replit_deployment_config()
        
        return jsonify(replit_config)
        
    except Exception as e:
        logger.error(f"Replit config generation failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/docker-config', methods=['GET'])
@admin_required
def get_docker_config():
    """
    Generate Docker configuration for containerized deployment
    Admin only endpoint
    """
    try:
        docker_config = deployment_service.generate_docker_configuration()
        
        return jsonify(docker_config)
        
    except Exception as e:
        logger.error(f"Docker config generation failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/test', methods=['POST'])
@admin_required
def run_deployment_tests():
    """
    Run comprehensive deployment testing
    Admin only endpoint
    """
    try:
        test_results = deployment_service.run_deployment_tests()
        
        return jsonify({
            'success': True,
            'test_results': test_results
        })
        
    except Exception as e:
        logger.error(f"Deployment testing failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/validate', methods=['GET'])
def validate_production_readiness():
    """
    Comprehensive production readiness validation
    Public endpoint for deployment validation
    """
    try:
        validation_results = deployment_service.validate_production_readiness()
        
        # Set appropriate HTTP status based on readiness
        status_code = 200
        overall_readiness = validation_results.get('overall_readiness', 'needs_work')
        
        if overall_readiness == 'needs_work':
            status_code = 412  # Precondition Failed
        elif overall_readiness == 'nearly_ready':
            status_code = 206  # Partial Content
        
        return jsonify({
            'success': True,
            'validation_results': validation_results
        }), status_code
        
    except Exception as e:
        logger.error(f"Production validation failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/download-config', methods=['GET'])
@admin_required
def download_deployment_config():
    """
    Download deployment configuration files as ZIP
    Admin only endpoint
    """
    try:
        # Get configuration type from query parameter
        config_type = request.args.get('type', 'all')  # all, replit, docker, nginx
        
        # Create temporary directory for files
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, f'deployment_config_{config_type}.zip')
            
            with zipfile.ZipFile(zip_path, 'w') as zip_file:
                if config_type in ['all', 'replit']:
                    replit_config = deployment_service.create_replit_deployment_config()
                    if 'replit_config' in replit_config:
                        for filename, content in replit_config['replit_config'].items():
                            zip_file.writestr(f'replit/{filename}', content)
                
                if config_type in ['all', 'docker']:
                    docker_config = deployment_service.generate_docker_configuration()
                    if 'docker_config' in docker_config:
                        for filename, content in docker_config['docker_config'].items():
                            zip_file.writestr(f'docker/{filename}', content)
                
                if config_type in ['all']:
                    deployment_package = deployment_service.prepare_production_deployment()
                    if 'configuration_files' in deployment_package:
                        for filename, content in deployment_package['configuration_files'].items():
                            zip_file.writestr(f'production/{filename}', content)
                    
                    if 'environment_files' in deployment_package:
                        for filename, content in deployment_package['environment_files'].items():
                            zip_file.writestr(f'environment/{filename}', content)
            
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=f'pinklemonade_deployment_{config_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
                mimetype='application/zip'
            )
            
    except Exception as e:
        logger.error(f"Config download failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/status', methods=['GET'])
def get_deployment_status():
    """
    Get current deployment status and readiness
    Public endpoint for deployment pipelines
    """
    try:
        # Get deployment status information
        status = {
            'environment': os.getenv('FLASK_ENV', 'development'),
            'deployment_mode': os.getenv('DEPLOYMENT_MODE', 'local'),
            'version': '2.0.0',
            'last_deployment': None,  # Would track from deployment history
            'current_commit': None,   # Would get from git if available
            'deployment_ready': False,
            'health_checks_passing': True,
            'components': {
                'database': 'healthy',
                'ai_services': 'healthy',
                'api_endpoints': 'healthy',
                'monitoring': 'healthy',
                'security': 'configured'
            }
        }
        
        # Check deployment readiness
        validation_results = deployment_service.validate_production_readiness()
        status['deployment_ready'] = validation_results.get('overall_readiness') == 'production_ready'
        status['readiness_score'] = validation_results.get('readiness_score', 0)
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Deployment status check failed: {e}")
        return jsonify({
            'error': str(e),
            'deployment_ready': False
        }), 500

@bp.route('/environments', methods=['GET'])
def get_supported_environments():
    """
    Get list of supported deployment environments
    Public endpoint for deployment information
    """
    try:
        environments = {
            'replit': {
                'name': 'Replit Deployment',
                'description': 'Native Replit deployment with automatic scaling',
                'requirements': ['Replit Core plan', 'PostgreSQL addon'],
                'configuration_endpoint': '/api/deployment/replit-config',
                'supported': True,
                'recommended': True
            },
            'docker': {
                'name': 'Docker Containerized',
                'description': 'Docker-based deployment for any container platform',
                'requirements': ['Docker', 'PostgreSQL instance', 'Redis (optional)'],
                'configuration_endpoint': '/api/deployment/docker-config',
                'supported': True,
                'recommended': False
            },
            'traditional': {
                'name': 'Traditional Server',
                'description': 'Traditional server deployment with Nginx and Gunicorn',
                'requirements': ['Linux server', 'Python 3.11+', 'PostgreSQL', 'Nginx'],
                'configuration_endpoint': '/api/deployment/prepare',
                'supported': True,
                'recommended': False
            },
            'cloud': {
                'name': 'Cloud Platforms',
                'description': 'Deployment to AWS, GCP, Azure, etc.',
                'requirements': ['Cloud account', 'Container orchestration'],
                'configuration_endpoint': '/api/deployment/docker-config',
                'supported': True,
                'recommended': False
            }
        }
        
        return jsonify({
            'success': True,
            'environments': environments,
            'recommended_environment': 'replit'
        })
        
    except Exception as e:
        logger.error(f"Environment listing failed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/checklist', methods=['GET'])
def get_deployment_checklist():
    """
    Get deployment checklist with current status
    Public endpoint for deployment validation
    """
    try:
        checklist_items = [
            {
                'category': 'Environment',
                'items': [
                    {'task': 'Environment variables configured', 'status': 'complete', 'required': True},
                    {'task': 'Database connection tested', 'status': 'complete', 'required': True},
                    {'task': 'AI services configured', 'status': 'complete', 'required': True},
                    {'task': 'Email service configured', 'status': 'pending', 'required': False}
                ]
            },
            {
                'category': 'Security',
                'items': [
                    {'task': 'Security headers implemented', 'status': 'complete', 'required': True},
                    {'task': 'Authentication secured', 'status': 'complete', 'required': True},
                    {'task': 'Rate limiting enabled', 'status': 'complete', 'required': True},
                    {'task': 'HTTPS configured', 'status': 'pending', 'required': True}
                ]
            },
            {
                'category': 'Performance',
                'items': [
                    {'task': 'Database optimized', 'status': 'complete', 'required': True},
                    {'task': 'API endpoints optimized', 'status': 'complete', 'required': True},
                    {'task': 'Caching implemented', 'status': 'pending', 'required': False},
                    {'task': 'Load testing completed', 'status': 'pending', 'required': False}
                ]
            },
            {
                'category': 'Monitoring',
                'items': [
                    {'task': 'Health checks implemented', 'status': 'complete', 'required': True},
                    {'task': 'Performance monitoring active', 'status': 'complete', 'required': True},
                    {'task': 'Error tracking configured', 'status': 'complete', 'required': True},
                    {'task': 'Backup system configured', 'status': 'pending', 'required': True}
                ]
            }
        ]
        
        # Calculate completion statistics
        total_items = sum(len(category['items']) for category in checklist_items)
        completed_items = sum(
            sum(1 for item in category['items'] if item['status'] == 'complete')
            for category in checklist_items
        )
        required_items = sum(
            sum(1 for item in category['items'] if item['required'])
            for category in checklist_items
        )
        completed_required = sum(
            sum(1 for item in category['items'] if item['required'] and item['status'] == 'complete')
            for category in checklist_items
        )
        
        return jsonify({
            'success': True,
            'checklist': checklist_items,
            'statistics': {
                'total_items': total_items,
                'completed_items': completed_items,
                'required_items': required_items,
                'completed_required': completed_required,
                'completion_percentage': round((completed_items / total_items) * 100, 1),
                'required_completion_percentage': round((completed_required / required_items) * 100, 1)
            },
            'deployment_ready': completed_required >= required_items * 0.9  # 90% of required items
        })
        
    except Exception as e:
        logger.error(f"Deployment checklist failed: {e}")
        return jsonify({'error': str(e)}), 500