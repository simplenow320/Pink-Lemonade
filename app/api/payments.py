"""
Payment API Endpoints
Stripe integration for subscription management
"""

from flask import Blueprint, jsonify, request, redirect
from app.services.stripe_service import StripeService
import os
import logging

logger = logging.getLogger(__name__)

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')
stripe_service = StripeService()

@payments_bp.route('/plans', methods=['GET'])
def get_plans():
    """Get all available subscription plans"""
    try:
        plans = []
        for plan_key, plan_info in StripeService.PLANS.items():
            plans.append({
                'id': plan_key,
                'name': plan_info['name'],
                'price_monthly': plan_info['price_monthly'],
                'price_yearly': plan_info['price_yearly'],
                'features': plan_info['features'],
                'popular': plan_key == 'professional'  # Mark professional as popular
            })
        
        return jsonify({
            'success': True,
            'plans': plans,
            'comparison': stripe_service.get_pricing_comparison()
        })
        
    except Exception as e:
        logger.error(f"Error getting plans: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/checkout', methods=['POST'])
def create_checkout():
    """Create Stripe checkout session"""
    try:
        data = request.json
        plan = data.get('plan')
        billing_period = data.get('billing_period', 'monthly')
        customer_email = data.get('email')
        
        if not plan or not customer_email:
            return jsonify({
                'success': False,
                'error': 'Plan and email are required'
            }), 400
        
        # Generate URLs
        base_url = os.environ.get('REPLIT_DEV_DOMAIN', 'http://localhost:5000')
        if not base_url.startswith('http'):
            base_url = f'https://{base_url}'
        
        success_url = f"{base_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}/pricing"
        
        # Create checkout session
        result = stripe_service.create_checkout_session(
            plan=plan,
            billing_period=billing_period,
            customer_email=customer_email,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error creating checkout: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/portal', methods=['POST'])
def create_portal():
    """Create customer portal for subscription management"""
    try:
        data = request.json
        customer_id = data.get('customer_id')
        
        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'Customer ID required'
            }), 400
        
        # Generate return URL
        base_url = os.environ.get('REPLIT_DEV_DOMAIN', 'http://localhost:5000')
        if not base_url.startswith('http'):
            base_url = f'https://{base_url}'
        
        return_url = f"{base_url}/account"
        
        # Create portal session
        result = stripe_service.create_customer_portal(
            customer_id=customer_id,
            return_url=return_url
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error creating portal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/subscription/<subscription_id>', methods=['GET'])
def get_subscription(subscription_id):
    """Get subscription status"""
    try:
        result = stripe_service.get_subscription_status(subscription_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/subscription/<subscription_id>/cancel', methods=['POST'])
def cancel_subscription(subscription_id):
    """Cancel subscription"""
    try:
        data = request.json
        immediate = data.get('immediate', False)
        
        result = stripe_service.cancel_subscription(
            subscription_id=subscription_id,
            immediate=immediate
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error canceling subscription: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/subscription/<subscription_id>/update', methods=['POST'])
def update_subscription(subscription_id):
    """Update subscription plan"""
    try:
        data = request.json
        new_plan = data.get('plan')
        new_billing_period = data.get('billing_period', 'monthly')
        
        if not new_plan:
            return jsonify({
                'success': False,
                'error': 'New plan required'
            }), 400
        
        result = stripe_service.update_subscription(
            subscription_id=subscription_id,
            new_plan=new_plan,
            new_billing_period=new_billing_period
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating subscription: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    try:
        payload = request.get_data(as_text=True)
        signature = request.headers.get('Stripe-Signature')
        
        if not signature:
            return jsonify({'error': 'No signature'}), 400
        
        result = stripe_service.process_webhook(payload, signature)
        
        if result['success']:
            return jsonify({'received': True}), 200
        else:
            return jsonify({'error': result.get('error')}), 400
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/pricing-strategy', methods=['GET'])
def get_pricing_strategy():
    """Get competitive pricing strategy details"""
    try:
        strategy = {
            'positioning': 'Aggressive undercutting - 25-67% below competitors',
            'target_market': 'Small to medium nonprofits priced out by enterprise solutions',
            'value_proposition': 'Enterprise features at startup prices',
            'comparison': stripe_service.get_pricing_comparison(),
            'roi_message': 'Pay for itself with just one successful grant',
            'testimonial': 'Save $3,000+ per year compared to GrantStation',
            'guarantee': '30-day money back guarantee',
            'special_offers': [
                '2 months free with annual billing',
                'Nonprofit discount available',
                'Free migration from competitors'
            ]
        }
        
        return jsonify({
            'success': True,
            'strategy': strategy
        })
        
    except Exception as e:
        logger.error(f"Error getting pricing strategy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500