"""
Stripe Payment Service
Handles subscription management and payment processing
"""

import os
import stripe
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

class StripeService:
    """
    Manages Stripe payments and subscriptions for Pink Lemonade
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
    
    def create_checkout_session(self, plan: str, billing_period: str, 
                              customer_email: str, success_url: str, 
                              cancel_url: str) -> Dict:
        """Create Stripe checkout session for subscription"""
        try:
            if plan not in self.PLANS:
                return {'success': False, 'error': 'Invalid plan'}
            
            if billing_period not in ['monthly', 'yearly']:
                return {'success': False, 'error': 'Invalid billing period'}
            
            plan_info = self.PLANS[plan]
            price_id = plan_info[f'stripe_price_id_{billing_period}']
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                metadata={
                    'plan': plan,
                    'billing_period': billing_period
                },
                allow_promotion_codes=True,
                billing_address_collection='required'
            )
            
            return {
                'success': True,
                'checkout_url': session.url,
                'session_id': session.id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_customer_portal(self, customer_id: str, return_url: str) -> Dict:
        """Create customer portal session for subscription management"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            
            return {
                'success': True,
                'portal_url': session.url
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error creating portal session: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_subscription_status(self, subscription_id: str) -> Dict:
        """Get current subscription status"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                'success': True,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'plan': self._get_plan_from_price(subscription.items.data[0].price.id)
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting subscription: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error getting subscription: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_subscription(self, subscription_id: str, immediate: bool = False) -> Dict:
        """Cancel subscription (immediately or at period end)"""
        try:
            if immediate:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            
            return {
                'success': True,
                'status': subscription.status,
                'canceled': True,
                'cancel_at': subscription.current_period_end if not immediate else datetime.utcnow().timestamp()
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error canceling subscription: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_subscription(self, subscription_id: str, new_plan: str, 
                          new_billing_period: str) -> Dict:
        """Update subscription to new plan"""
        try:
            if new_plan not in self.PLANS:
                return {'success': False, 'error': 'Invalid plan'}
            
            plan_info = self.PLANS[new_plan]
            price_id = plan_info[f'stripe_price_id_{new_billing_period}']
            
            # Get current subscription
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Update subscription
            updated = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': price_id,
                }],
                proration_behavior='create_prorations'
            )
            
            return {
                'success': True,
                'subscription_id': updated.id,
                'new_plan': new_plan,
                'status': updated.status
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_webhook(self, payload: str, signature: str) -> Dict:
        """Process Stripe webhook events"""
        try:
            webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
            
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                return self._handle_checkout_completed(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.updated':
                return self._handle_subscription_updated(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(event['data']['object'])
            
            elif event['type'] == 'invoice.payment_failed':
                return self._handle_payment_failed(event['data']['object'])
            
            else:
                logger.info(f"Unhandled webhook event type: {event['type']}")
                return {'success': True, 'message': 'Event received'}
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return {'success': False, 'error': 'Invalid signature'}
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_pricing_comparison(self) -> Dict:
        """Get pricing comparison with competitors"""
        return {
            'pink_lemonade': {
                'starter': 79,
                'professional': 199,
                'enterprise': 499
            },
            'competitors': {
                'grantstation': {
                    'basic': 199,
                    'professional': 299,
                    'premium': 699
                },
                'foundation_directory': {
                    'essential': 199,
                    'professional': 599,
                    'enterprise': 1499
                },
                'instrumentl': {
                    'basic': 182,
                    'professional': 379,
                    'enterprise': 'Custom'
                }
            },
            'savings': {
                'starter': '60% less than competitors',
                'professional': '47% less than competitors',
                'enterprise': '67% less than competitors'
            }
        }
    
    # Helper methods
    
    def _get_plan_from_price(self, price_id: str) -> Optional[str]:
        """Get plan name from Stripe price ID"""
        for plan_key, plan_info in self.PLANS.items():
            if price_id in [plan_info['stripe_price_id_monthly'], 
                          plan_info['stripe_price_id_yearly']]:
                return plan_key
        return None
    
    def _handle_checkout_completed(self, session: Dict) -> Dict:
        """Handle successful checkout"""
        try:
            customer_email = session.get('customer_email')
            subscription_id = session.get('subscription')
            plan = session.get('metadata', {}).get('plan')
            
            # Update user record with subscription
            from app.models import User, db
            user = User.query.filter_by(email=customer_email).first()
            if user:
                user.stripe_customer_id = session.get('customer')
                user.stripe_subscription_id = subscription_id
                user.subscription_plan = plan
                user.subscription_status = 'active'
                db.session.commit()
            
            logger.info(f"Checkout completed for {customer_email}, plan: {plan}")
            return {'success': True, 'subscription_id': subscription_id}
            
        except Exception as e:
            logger.error(f"Error handling checkout completion: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_subscription_updated(self, subscription: Dict) -> Dict:
        """Handle subscription update"""
        try:
            subscription_id = subscription.get('id')
            status = subscription.get('status')
            
            # Update user record
            from app.models import User, db
            user = User.query.filter_by(stripe_subscription_id=subscription_id).first()
            if user:
                user.subscription_status = status
                db.session.commit()
            
            logger.info(f"Subscription {subscription_id} updated to status: {status}")
            return {'success': True, 'status': status}
            
        except Exception as e:
            logger.error(f"Error handling subscription update: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_subscription_deleted(self, subscription: Dict) -> Dict:
        """Handle subscription cancellation"""
        try:
            subscription_id = subscription.get('id')
            
            # Update user record
            from app.models import User, db
            user = User.query.filter_by(stripe_subscription_id=subscription_id).first()
            if user:
                user.subscription_status = 'canceled'
                user.subscription_plan = None
                db.session.commit()
            
            logger.info(f"Subscription {subscription_id} canceled")
            return {'success': True, 'canceled': True}
            
        except Exception as e:
            logger.error(f"Error handling subscription deletion: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_payment_failed(self, invoice: Dict) -> Dict:
        """Handle failed payment"""
        try:
            customer_id = invoice.get('customer')
            
            # Update user record
            from app.models import User, db
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if user:
                user.subscription_status = 'past_due'
                db.session.commit()
                
                # TODO: Send email notification
            
            logger.warning(f"Payment failed for customer {customer_id}")
            return {'success': True, 'payment_failed': True}
            
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
            return {'success': False, 'error': str(e)}