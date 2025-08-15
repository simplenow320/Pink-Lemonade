"""
Payment API endpoints - Phase 3
Handles Stripe checkout, billing portal, and payment management
"""

from flask import Blueprint, request, jsonify, session
from app.services.payment_service import PaymentService
from app import db
import logging
import os

# Simple auth check for now (can be replaced with proper auth later)
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in via session
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Mock current_user for now
class CurrentUser:
    @property
    def id(self):
        return session.get('user_id', 1)

current_user = CurrentUser()

logger = logging.getLogger(__name__)

payment_bp = Blueprint('payment', __name__)
payment_service = PaymentService()

@payment_bp.route('/checkout/session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for subscription upgrade"""
    try:
        data = request.json
        plan_tier = data.get('plan_tier')
        
        if not plan_tier:
            return jsonify({'error': 'Plan tier required'}), 400
        
        # Get return URLs
        base_url = request.host_url.rstrip('/')
        success_url = f"{base_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}/subscription/plans"
        
        # Create checkout session
        result = payment_service.create_checkout_session(
            user_id=current_user.id,
            plan_tier=plan_tier,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if result:
            return jsonify({
                'success': True,
                'checkout_url': result['url'],
                'session_id': result['id']
            })
        else:
            return jsonify({'error': 'Failed to create checkout session'}), 500
            
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/portal/session', methods=['POST'])
@login_required
def create_portal_session():
    """Create Stripe customer portal session for subscription management"""
    try:
        base_url = request.host_url.rstrip('/')
        return_url = f"{base_url}/subscription/manage"
        
        portal_url = payment_service.create_portal_session(
            user_id=current_user.id,
            return_url=return_url
        )
        
        if portal_url:
            return jsonify({
                'success': True,
                'portal_url': portal_url
            })
        else:
            return jsonify({'error': 'Failed to create portal session'}), 500
            
    except Exception as e:
        logger.error(f"Error creating portal session: {e}")
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel user's subscription"""
    try:
        data = request.json
        immediate = data.get('immediate', False)
        
        success = payment_service.cancel_subscription(
            user_id=current_user.id,
            immediate=immediate
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Subscription cancelled successfully'
            })
        else:
            return jsonify({'error': 'Failed to cancel subscription'}), 500
            
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/payment-method', methods=['POST'])
@login_required
def update_payment_method():
    """Update default payment method"""
    try:
        data = request.json
        payment_method_id = data.get('payment_method_id')
        
        if not payment_method_id:
            return jsonify({'error': 'Payment method ID required'}), 400
        
        success = payment_service.update_payment_method(
            user_id=current_user.id,
            payment_method_id=payment_method_id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Payment method updated'
            })
        else:
            return jsonify({'error': 'Failed to update payment method'}), 500
            
    except Exception as e:
        logger.error(f"Error updating payment method: {e}")
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/history', methods=['GET'])
@login_required
def get_payment_history():
    """Get user's payment history"""
    try:
        history = payment_service.get_payment_history(user_id=current_user.id)
        
        return jsonify({
            'success': True,
            'payments': history
        })
        
    except Exception as e:
        logger.error(f"Error getting payment history: {e}")
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle Stripe webhook events"""
    try:
        payload = request.data
        signature = request.headers.get('Stripe-Signature')
        
        if not signature:
            return jsonify({'error': 'No signature'}), 400
        
        result = payment_service.process_webhook(payload, signature)
        
        if result['success']:
            return jsonify({'received': True}), 200
        else:
            return jsonify({'error': result.get('error')}), 400
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/stripe-key', methods=['GET'])
@login_required
def get_stripe_public_key():
    """Get Stripe publishable key for frontend"""
    try:
        # Return public key for Stripe.js
        public_key = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
        
        if not public_key:
            # Test mode key
            public_key = 'pk_test_51234567890abcdefghijklmnop'
        
        return jsonify({
            'success': True,
            'publishable_key': public_key
        })
        
    except Exception as e:
        logger.error(f"Error getting Stripe key: {e}")
        return jsonify({'error': str(e)}), 500

# Phase 3 status endpoint
@payment_bp.route('/status', methods=['GET'])
def payment_status():
    """Check Phase 3 payment system status"""
    try:
        stripe_configured = bool(os.environ.get('STRIPE_SECRET_KEY'))
        
        return jsonify({
            'phase': 3,
            'name': 'Payment Processing',
            'status': 'active',
            'features': {
                'stripe_integration': stripe_configured,
                'checkout_sessions': True,
                'customer_portal': True,
                'webhooks': True,
                'payment_methods': True,
                'invoicing': True
            },
            'pricing': {
                'discovery': 79,
                'professional': 149,
                'enterprise': 299,
                'unlimited': 499
            },
            'message': 'Phase 3 Payment Processing ready. Configure STRIPE_SECRET_KEY to enable live payments.'
        })
        
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        return jsonify({'error': str(e)}), 500