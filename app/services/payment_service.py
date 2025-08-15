"""
Payment Service - Phase 3
Handles Stripe integration for subscription billing and payment processing
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None

from app.models import User, SubscriptionPlan, UserSubscription
try:
    from app.models_payment import PaymentMethod, PaymentHistory, Invoice
except ImportError:
    # Fallback if payment models aren't imported yet
    PaymentMethod = None
    PaymentHistory = None
    Invoice = None
from app import db

logger = logging.getLogger(__name__)

class PaymentService:
    """
    Comprehensive payment processing service with Stripe integration
    Handles subscriptions, billing, invoices, and payment methods
    """
    
    def __init__(self):
        """Initialize Stripe with API key"""
        self.stripe_key = os.environ.get('STRIPE_SECRET_KEY')
        self.webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        if STRIPE_AVAILABLE and self.stripe_key:
            stripe.api_key = self.stripe_key
            self.stripe_enabled = True
            logger.info("Payment Service initialized with Stripe")
        else:
            self.stripe_enabled = False
            logger.warning("Payment Service initialized without Stripe (test mode)")
        
        # Price IDs for each plan (would be configured in Stripe Dashboard)
        self.stripe_price_ids = {
            'discovery': os.environ.get('STRIPE_PRICE_DISCOVERY', 'price_discovery'),
            'professional': os.environ.get('STRIPE_PRICE_PROFESSIONAL', 'price_professional'),
            'enterprise': os.environ.get('STRIPE_PRICE_ENTERPRISE', 'price_enterprise'),
            'unlimited': os.environ.get('STRIPE_PRICE_UNLIMITED', 'price_unlimited')
        }
    
    def create_customer(self, user: User) -> Optional[str]:
        """Create Stripe customer for user"""
        if not self.stripe_enabled:
            return f"cus_test_{user.id}"
        
        try:
            if not STRIPE_AVAILABLE:
                raise Exception("Stripe not available")
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}" if user.first_name else user.username,
                metadata={
                    'user_id': str(user.id),
                    'organization': user.organization.name if hasattr(user, 'organization') else ''
                }
            )
            
            # Store customer ID
            user.stripe_customer_id = customer.id
            db.session.commit()
            
            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer.id
            
        except Exception as e:
            logger.error(f"Error creating Stripe customer: {e}")
            return None
    
    def create_checkout_session(self, user_id: int, plan_tier: str, 
                              success_url: str, cancel_url: str) -> Optional[Dict]:
        """Create Stripe checkout session for subscription"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None
            
            # Ensure customer exists
            if not user.stripe_customer_id:
                customer_id = self.create_customer(user)
                if not customer_id:
                    return None
            else:
                customer_id = user.stripe_customer_id
            
            # Get plan details
            plan = SubscriptionPlan.query.filter_by(tier=plan_tier).first()
            if not plan:
                logger.error(f"Plan {plan_tier} not found")
                return None
            
            if not self.stripe_enabled:
                # Test mode - return mock session
                return {
                    'id': f'cs_test_{user_id}_{plan_tier}',
                    'url': success_url,
                    'success': True
                }
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': self.stripe_price_ids.get(plan_tier),
                    'quantity': 1
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user_id),
                    'plan_tier': plan_tier
                },
                subscription_data={
                    'trial_period_days': 14 if plan_tier == 'discovery' else 0,
                    'metadata': {
                        'user_id': str(user_id),
                        'plan_tier': plan_tier
                    }
                },
                allow_promotion_codes=True
            )
            
            logger.info(f"Created checkout session {session.id} for user {user_id}")
            
            return {
                'id': session.id,
                'url': session.url,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            return None
    
    def create_portal_session(self, user_id: int, return_url: str) -> Optional[str]:
        """Create Stripe customer portal session for managing subscription"""
        try:
            user = User.query.get(user_id)
            if not user or not user.stripe_customer_id:
                return None
            
            if not self.stripe_enabled:
                return return_url  # Test mode
            
            session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=return_url
            )
            
            return session.url
            
        except Exception as e:
            logger.error(f"Error creating portal session: {e}")
            return None
    
    def cancel_subscription(self, user_id: int, immediate: bool = False) -> bool:
        """Cancel user's subscription"""
        try:
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            if not subscription or not subscription.stripe_subscription_id:
                return False
            
            if not self.stripe_enabled:
                # Test mode - just update database
                subscription.status = 'cancelled'
                subscription.cancelled_at = datetime.utcnow()
                db.session.commit()
                return True
            
            # Cancel in Stripe
            stripe_sub = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=not immediate
            )
            
            if immediate:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = 'cancelled'
                subscription.cancelled_at = datetime.utcnow()
            else:
                subscription.status = 'cancelling'
                subscription.cancel_at_period_end = True
            
            db.session.commit()
            logger.info(f"Cancelled subscription for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return False
    
    def update_payment_method(self, user_id: int, payment_method_id: str) -> bool:
        """Update default payment method"""
        try:
            user = User.query.get(user_id)
            if not user or not user.stripe_customer_id:
                return False
            
            if not self.stripe_enabled:
                return True  # Test mode
            
            # Attach payment method to customer
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=user.stripe_customer_id
            )
            
            # Set as default
            stripe.Customer.modify(
                user.stripe_customer_id,
                invoice_settings={'default_payment_method': payment_method_id}
            )
            
            # Store in database
            payment_method = PaymentMethod.query.filter_by(
                user_id=user_id,
                is_default=True
            ).first()
            
            if payment_method:
                payment_method.is_default = False
            
            new_method = PaymentMethod(
                user_id=user_id,
                stripe_payment_method_id=payment_method_id,
                is_default=True
            )
            
            db.session.add(new_method)
            db.session.commit()
            
            logger.info(f"Updated payment method for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating payment method: {e}")
            return False
    
    def process_webhook(self, payload: bytes, signature: str) -> Dict:
        """Process Stripe webhook events"""
        if not self.stripe_enabled:
            return {'success': True, 'message': 'Test mode'}
        
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            # Handle different event types
            if event.type == 'checkout.session.completed':
                self._handle_checkout_completed(event.data.object)
            
            elif event.type == 'invoice.payment_succeeded':
                self._handle_payment_succeeded(event.data.object)
            
            elif event.type == 'invoice.payment_failed':
                self._handle_payment_failed(event.data.object)
            
            elif event.type == 'customer.subscription.updated':
                self._handle_subscription_updated(event.data.object)
            
            elif event.type == 'customer.subscription.deleted':
                self._handle_subscription_deleted(event.data.object)
            
            return {'success': True, 'event': event.type}
            
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return {'success': False, 'error': 'Invalid payload'}
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return {'success': False, 'error': 'Invalid signature'}
    
    def _handle_checkout_completed(self, session):
        """Handle successful checkout"""
        try:
            user_id = int(session.metadata.user_id)
            plan_tier = session.metadata.plan_tier
            
            # Get subscription details
            stripe_sub = stripe.Subscription.retrieve(session.subscription)
            
            # Create or update subscription
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            plan = SubscriptionPlan.query.filter_by(tier=plan_tier).first()
            
            if not subscription:
                subscription = UserSubscription(user_id=user_id)
            
            subscription.plan_id = plan.id
            subscription.stripe_subscription_id = stripe_sub.id
            subscription.stripe_customer_id = session.customer
            subscription.status = 'active'
            subscription.current_period_start = datetime.fromtimestamp(stripe_sub.current_period_start)
            subscription.current_period_end = datetime.fromtimestamp(stripe_sub.current_period_end)
            
            db.session.add(subscription)
            db.session.commit()
            
            logger.info(f"Activated subscription for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling checkout completion: {e}")
    
    def _handle_payment_succeeded(self, invoice):
        """Handle successful payment"""
        try:
            # Record payment
            payment = PaymentHistory(
                user_id=int(invoice.metadata.get('user_id', 0)),
                stripe_invoice_id=invoice.id,
                amount=invoice.amount_paid / 100,  # Convert from cents
                currency=invoice.currency.upper(),
                status='succeeded',
                description=f"Subscription payment for {invoice.period_start} to {invoice.period_end}"
            )
            
            db.session.add(payment)
            db.session.commit()
            
            logger.info(f"Recorded successful payment {invoice.id}")
            
        except Exception as e:
            logger.error(f"Error handling payment success: {e}")
    
    def _handle_payment_failed(self, invoice):
        """Handle failed payment"""
        try:
            user_id = int(invoice.metadata.get('user_id', 0))
            
            # Record failed payment
            payment = PaymentHistory(
                user_id=user_id,
                stripe_invoice_id=invoice.id,
                amount=invoice.amount_due / 100,
                currency=invoice.currency.upper(),
                status='failed',
                description="Payment failed"
            )
            
            db.session.add(payment)
            
            # Update subscription status
            subscription = UserSubscription.query.filter_by(
                stripe_customer_id=invoice.customer
            ).first()
            
            if subscription:
                subscription.status = 'past_due'
            
            db.session.commit()
            
            logger.warning(f"Payment failed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
    
    def _handle_subscription_updated(self, subscription):
        """Handle subscription update"""
        try:
            user_sub = UserSubscription.query.filter_by(
                stripe_subscription_id=subscription.id
            ).first()
            
            if user_sub:
                user_sub.status = subscription.status
                user_sub.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
                db.session.commit()
                
                logger.info(f"Updated subscription {subscription.id}")
                
        except Exception as e:
            logger.error(f"Error handling subscription update: {e}")
    
    def _handle_subscription_deleted(self, subscription):
        """Handle subscription cancellation"""
        try:
            user_sub = UserSubscription.query.filter_by(
                stripe_subscription_id=subscription.id
            ).first()
            
            if user_sub:
                user_sub.status = 'cancelled'
                user_sub.cancelled_at = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"Cancelled subscription {subscription.id}")
                
        except Exception as e:
            logger.error(f"Error handling subscription deletion: {e}")
    
    def get_payment_history(self, user_id: int) -> List[Dict]:
        """Get user's payment history"""
        payments = PaymentHistory.query.filter_by(user_id=user_id).order_by(
            PaymentHistory.created_at.desc()
        ).limit(20).all()
        
        return [payment.to_dict() for payment in payments]
    
    def generate_invoice(self, user_id: int, subscription_id: int) -> Optional[Dict]:
        """Generate invoice for subscription"""
        try:
            subscription = UserSubscription.query.get(subscription_id)
            if not subscription or subscription.user_id != user_id:
                return None
            
            invoice = Invoice(
                user_id=user_id,
                subscription_id=subscription_id,
                amount=subscription.plan.price_monthly,
                status='pending',
                due_date=subscription.current_period_end
            )
            
            db.session.add(invoice)
            db.session.commit()
            
            return invoice.to_dict()
            
        except Exception as e:
            logger.error(f"Error generating invoice: {e}")
            return None