"""
Mobile Optimization API Endpoints
Responsive design and mobile features
"""

from flask import Blueprint, jsonify, request
from app.services.mobile_service import MobileService
import logging

logger = logging.getLogger(__name__)

mobile_bp = Blueprint('mobile', __name__, url_prefix='/api/mobile')
mobile_service = MobileService()

@mobile_bp.route('/config', methods=['GET'])
def get_mobile_config():
    """Get mobile-specific configuration"""
    try:
        device_type = request.args.get('device', 'mobile')
        result = mobile_service.get_mobile_config(device_type)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting mobile config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/dashboard', methods=['GET'])
def get_responsive_dashboard():
    """Get mobile-optimized dashboard"""
    try:
        device_type = request.args.get('device', 'mobile')
        user_id = request.args.get('user_id', 1, type=int)
        
        result = mobile_service.get_responsive_dashboard(device_type, user_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/navigation', methods=['GET'])
def get_mobile_navigation():
    """Get mobile navigation menu"""
    try:
        device_type = request.args.get('device', 'mobile')
        result = mobile_service.get_mobile_navigation(device_type)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting navigation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/images/optimize', methods=['GET'])
def optimize_images():
    """Get optimized image settings"""
    try:
        device_type = request.args.get('device', 'mobile')
        network_speed = request.args.get('network', 'auto')
        
        result = mobile_service.optimize_images(device_type, network_speed)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error optimizing images: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/offline', methods=['GET'])
def get_offline_config():
    """Get offline capabilities configuration"""
    try:
        result = mobile_service.get_offline_capabilities()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting offline config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/gestures', methods=['GET'])
def get_touch_gestures():
    """Get touch gesture configuration"""
    try:
        result = mobile_service.get_touch_gestures()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting gestures: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/performance', methods=['GET'])
def get_performance_metrics():
    """Get mobile performance metrics"""
    try:
        result = mobile_service.get_performance_metrics()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_bp.route('/features', methods=['GET'])
def get_mobile_features():
    """Get list of mobile features"""
    try:
        features = {
            'responsive_design': {
                'enabled': True,
                'breakpoints': MobileService.BREAKPOINTS,
                'fluid_typography': True,
                'flexible_images': True
            },
            'touch_optimization': {
                'enabled': True,
                'minimum_target_size': '44px',
                'gesture_support': True,
                'haptic_feedback': True
            },
            'performance': {
                'lazy_loading': True,
                'code_splitting': True,
                'service_worker': True,
                'offline_mode': True
            },
            'progressive_web_app': {
                'enabled': True,
                'installable': True,
                'push_notifications': True,
                'background_sync': True
            },
            'accessibility': {
                'wcag_compliant': True,
                'screen_reader_support': True,
                'keyboard_navigation': True,
                'high_contrast_mode': True
            }
        }
        
        return jsonify({
            'success': True,
            'features': features
        })
        
    except Exception as e:
        logger.error(f"Error getting features: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500