"""
Mock Stripe Payment Service
Provides payment functionality without external dependencies
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

class StripeService:
    """
    Mock Stripe payments and subscriptions for Pink Lemonade
    Works without actual Stripe dependency
    """
    
    # Pricing Plans (Aggressive competitive pricing)
    PLANS = {
        'starter': {
            'name': 'Starter',
            'price_monthly': 79,
            'price_yearly': 790,  # 2 months free
            'features': [
                'Up to 5 grants per month',
                'AI matching & scoring',
                'Basic analytics',
                'Email support'
            ],
            'stripe_price_id_monthly': 'price_starter_monthly',
            'stripe_price_id_yearly': 'price_starter_yearly'
        },
        'professional': {
            'name': 'Professional',
            'price_monthly': 199,
            'price_yearly': 1990,  # 2 months free
            'features': [
                'Unlimited grants',
                'Advanced AI tools',
                'Full analytics suite',
                'Priority support',
                'Team collaboration (3 users)'
            ],
            'stripe_price_id_monthly': 'price_professional_monthly',
            'stripe_price_id_yearly': 'price_professional_yearly'
        },
        'enterprise': {
            'name': 'Enterprise',
            'price_monthly': 499,
            'price_yearly': 4990,  # 2 months free
            'features': [
                'Everything in Professional',
                'Unlimited team members',
                'Custom integrations',
                'Dedicated account manager',
                'SLA guarantee',
                'White-label options'
            ],
            'stripe_price_id_monthly': 'price_enterprise_monthly',
            'stripe_price_id_yearly': 'price_enterprise_yearly'
        }
    }
    
    def __init__(self):
        """Initialize mock Stripe service"""
        logger.warning("Payment Service initialized without Stripe (test mode)")
    
    def create_checkout_session(self, plan: str, billing_period: str, 
                              customer_email: str, success_url: str, 
                              cancel_url: str) -> Dict:
        """Create mock checkout session for subscription"""
        try:
            if plan not in self.PLANS:
                return {'success': False, 'error': 'Invalid plan'}
            
            if billing_period not in ['monthly', 'yearly']:
                return {'success': False, 'error': 'Invalid billing period'}
            
            plan_info = self.PLANS[plan]
            session_id = f"cs_test_{uuid.uuid4().hex[:24]}"
            
            # Mock checkout URL
            checkout_url = f"/payment/mock-checkout?session={session_id}&plan={plan}&period={billing_period}"
            
            logger.info(f"Mock checkout session created: {session_id}")
            
            return {
                'success': True,
                'checkout_url': checkout_url,
                'session_id': session_id,
                'mock': True,
                'message': 'This is a test checkout - no payment will be processed'
            }
            
        except Exception as e:
            logger.error(f"Error creating mock checkout session: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_customer_portal(self, customer_id: str, return_url: str) -> Dict:
        """Create mock customer portal session"""
        try:
            portal_url = f"/payment/mock-portal?customer={customer_id}"
            
            return {
                'success': True,
                'portal_url': portal_url,
                'mock': True,
                'message': 'This is a test portal - no actual subscription management'
            }
            
        except Exception as e:
            logger.error(f"Error creating mock portal: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_subscription_status(self, subscription_id: str) -> Dict:
        """Get mock subscription status"""
        try:
            # Return mock active subscription
            return {
                'success': True,
                'subscription': {
                    'id': subscription_id,
                    'status': 'active',
                    'plan': 'professional',
                    'billing_period': 'monthly',
                    'current_period_end': datetime.now().isoformat(),
                    'cancel_at_period_end': False
                },
                'mock': True
            }
            
        except Exception as e:
            logger.error(f"Error getting mock subscription: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_subscription(self, subscription_id: str, immediate: bool = False) -> Dict:
        """Cancel mock subscription"""
        try:
            return {
                'success': True,
                'message': 'Mock subscription cancelled',
                'subscription_id': subscription_id,
                'cancelled_at': datetime.now().isoformat(),
                'immediate': immediate,
                'mock': True
            }
            
        except Exception as e:
            logger.error(f"Error cancelling mock subscription: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_payment_intent(self, amount: int, currency: str = 'usd',
                            customer_email: str = None) -> Dict:
        """Create mock payment intent"""
        try:
            intent_id = f"pi_test_{uuid.uuid4().hex[:24]}"
            
            return {
                'success': True,
                'payment_intent': {
                    'id': intent_id,
                    'amount': amount,
                    'currency': currency,
                    'status': 'requires_payment_method',
                    'client_secret': f"pi_test_{uuid.uuid4().hex}_secret"
                },
                'mock': True
            }
            
        except Exception as e:
            logger.error(f"Error creating mock payment intent: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_customer(self, email: str, name: str = None, 
                       metadata: Dict = None) -> Dict:
        """Create mock customer"""
        try:
            customer_id = f"cus_test_{uuid.uuid4().hex[:14]}"
            
            return {
                'success': True,
                'customer': {
                    'id': customer_id,
                    'email': email,
                    'name': name,
                    'metadata': metadata or {},
                    'created': datetime.now().isoformat()
                },
                'mock': True
            }
            
        except Exception as e:
            logger.error(f"Error creating mock customer: {e}")
            return {'success': False, 'error': str(e)}
    
    def attach_payment_method(self, customer_id: str, payment_method_id: str) -> Dict:
        """Attach mock payment method to customer"""
        try:
            return {
                'success': True,
                'message': 'Mock payment method attached',
                'customer_id': customer_id,
                'payment_method_id': payment_method_id,
                'mock': True
            }
            
        except Exception as e:
            logger.error(f"Error attaching mock payment method: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_pricing_comparison(self) -> Dict:
        """Get pricing comparison data"""
        return {
            'pink_lemonade': {
                'starter': 79,
                'professional': 199,
                'enterprise': 499
            },
            'competitors': {
                'GrantStation': {
                    'basic': 95,
                    'professional': 299,
                    'enterprise': 'Custom'
                },
                'Foundation Directory': {
                    'essential': 99,
                    'professional': 349,
                    'enterprise': 1499
                },
                'GrantWatch': {
                    'basic': 89,
                    'plus': 199,
                    'premium': 399
                },
                'Instrumentl': {
                    'basic': 179,
                    'professional': 379,
                    'enterprise': 'Custom'
                },
                'Fluxx': {
                    'basic': 'Custom',
                    'professional': 'Custom',
                    'enterprise': 'Custom (typically $2000+)'
                }
            },
            'value_props': {
                'starter': 'Best value for small nonprofits',
                'professional': '60% cheaper than competitors',
                'enterprise': '75% less than traditional solutions'
            }
        }
    
    def handle_webhook(self, payload: Dict, sig_header: str) -> Dict:
        """Handle mock webhook events"""
        try:
            event_type = payload.get('type', 'unknown')
            
            logger.info(f"Mock webhook received: {event_type}")
            
            # Handle different event types
            if event_type == 'checkout.session.completed':
                return self._handle_checkout_completed(payload)
            elif event_type == 'customer.subscription.updated':
                return self._handle_subscription_updated(payload)
            elif event_type == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(payload)
            else:
                return {'success': True, 'message': f'Mock event {event_type} received'}
                
        except Exception as e:
            logger.error(f"Error handling mock webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_checkout_completed(self, payload: Dict) -> Dict:
        """Handle mock checkout completion"""
        return {
            'success': True,
            'message': 'Mock checkout completed',
            'mock': True
        }
    
    def _handle_subscription_updated(self, payload: Dict) -> Dict:
        """Handle mock subscription update"""
        return {
            'success': True,
            'message': 'Mock subscription updated',
            'mock': True
        }
    
    def _handle_subscription_deleted(self, payload: Dict) -> Dict:
        """Handle mock subscription deletion"""
        return {
            'success': True,
            'message': 'Mock subscription deleted',
            'mock': True
        }