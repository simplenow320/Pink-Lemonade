"""
Subscription Management Service
Handles plan management, usage tracking, and billing preparation
Phase 2: Authentication & User Management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from app import db
from app.models import (
    SubscriptionPlan, UserSubscription, TeamMember, UsageLog, PlanTier
)
from app.models import User

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Service for managing subscriptions and usage"""
    
    # Competitive pricing structure (25-67% below competitors)
    PLAN_CONFIGS = {
        PlanTier.DISCOVERY.value: {
            'name': 'Discovery',
            'price_monthly': 79,
            'price_yearly': 790,  # ~$66/month
            'max_users': 1,
            'max_grants_tracked': 25,
            'max_applications_monthly': 10,
            'max_ai_requests_monthly': 500,
            'max_reports_monthly': 20,
            'features': {
                'ai_matching': True,
                'ai_writing': False,
                'analytics': True,
                'smart_tools': False,
                'team_collaboration': False,
                'api_access': False,
                'priority_support': False
            },
            'description': 'Perfect for small nonprofits just starting their grant journey',
            'features_list': [
                'AI-powered grant matching',
                'Track up to 25 grants',
                '10 applications per month',
                'Basic analytics dashboard',
                'Email support'
            ]
        },
        PlanTier.PROFESSIONAL.value: {
            'name': 'Professional',
            'price_monthly': 149,
            'price_yearly': 1490,  # ~$124/month
            'max_users': 5,
            'max_grants_tracked': 100,
            'max_applications_monthly': 50,
            'max_ai_requests_monthly': 2000,
            'max_reports_monthly': 100,
            'features': {
                'ai_matching': True,
                'ai_writing': True,
                'analytics': True,
                'smart_tools': True,
                'team_collaboration': True,
                'api_access': False,
                'priority_support': True
            },
            'description': 'Ideal for growing nonprofits with active grant programs',
            'features_list': [
                'Everything in Discovery, plus:',
                'AI writing assistant',
                'Smart Tools suite',
                'Team collaboration (5 users)',
                'Track up to 100 grants',
                '50 applications per month',
                'Advanced analytics',
                'Priority email support'
            ]
        },
        PlanTier.ENTERPRISE.value: {
            'name': 'Enterprise',
            'price_monthly': 299,
            'price_yearly': 2990,  # ~$249/month
            'max_users': 20,
            'max_grants_tracked': 500,
            'max_applications_monthly': 200,
            'max_ai_requests_monthly': 10000,
            'max_reports_monthly': 500,
            'features': {
                'ai_matching': True,
                'ai_writing': True,
                'analytics': True,
                'smart_tools': True,
                'team_collaboration': True,
                'api_access': True,
                'priority_support': True,
                'white_label': True
            },
            'description': 'Comprehensive solution for large nonprofits and foundations',
            'features_list': [
                'Everything in Professional, plus:',
                'API access',
                'White-label options',
                '20 team members',
                'Track up to 500 grants',
                '200 applications per month',
                'Custom integrations',
                'Phone & priority support',
                'Dedicated success manager'
            ]
        },
        PlanTier.UNLIMITED.value: {
            'name': 'Unlimited',
            'price_monthly': 499,
            'price_yearly': 4990,  # ~$416/month
            'max_users': 999,
            'max_grants_tracked': 99999,
            'max_applications_monthly': 99999,
            'max_ai_requests_monthly': 99999,
            'max_reports_monthly': 99999,
            'features': {
                'ai_matching': True,
                'ai_writing': True,
                'analytics': True,
                'smart_tools': True,
                'team_collaboration': True,
                'api_access': True,
                'priority_support': True,
                'white_label': True,
                'custom_integrations': True
            },
            'description': 'No limits for enterprise organizations and grant consultants',
            'features_list': [
                'Everything, unlimited:',
                'Unlimited users',
                'Unlimited grants',
                'Unlimited applications',
                'Unlimited AI usage',
                'Custom AI training',
                'Enterprise SSO',
                'Custom SLA',
                'Dedicated infrastructure'
            ]
        }
    }
    
    def __init__(self):
        """Initialize subscription service"""
        self.logger = logging.getLogger(__name__)
        self._plans_initialized = False
    
    def ensure_plans_exist(self):
        """Create default subscription plans if they don't exist"""
        if self._plans_initialized:
            return
        
        try:
            for tier_value, config in self.PLAN_CONFIGS.items():
                existing = SubscriptionPlan.query.filter_by(tier=tier_value).first()
                if not existing:
                    plan = SubscriptionPlan(
                        name=config['name'],
                        tier=tier_value,
                        price_monthly=config['price_monthly'],
                        price_yearly=config['price_yearly'],
                        max_users=config['max_users'],
                        max_grants_tracked=config['max_grants_tracked'],
                        max_applications_monthly=config['max_applications_monthly'],
                        max_ai_requests_monthly=config['max_ai_requests_monthly'],
                        max_reports_monthly=config['max_reports_monthly'],
                        has_ai_matching=config['features']['ai_matching'],
                        has_ai_writing=config['features']['ai_writing'],
                        has_analytics=config['features']['analytics'],
                        has_smart_tools=config['features']['smart_tools'],
                        has_team_collaboration=config['features']['team_collaboration'],
                        has_api_access=config['features'].get('api_access', False),
                        has_priority_support=config['features'].get('priority_support', False),
                        has_white_label=config['features'].get('white_label', False),
                        has_custom_integrations=config['features'].get('custom_integrations', False),
                        description=config['description'],
                        features_list=config['features_list']
                    )
                    db.session.add(plan)
            db.session.commit()
            logger.info("Subscription plans initialized")
        except Exception as e:
            logger.error(f"Error initializing plans: {e}")
            db.session.rollback()
    
    def create_trial_subscription(self, user_id: int, plan_tier: str = 'discovery') -> Optional[UserSubscription]:
        """Create a trial subscription for new user"""
        try:
            plan = SubscriptionPlan.query.filter_by(tier=plan_tier).first()
            if not plan:
                logger.error(f"Plan {plan_tier} not found")
                return None
            
            # Check if user already has subscription
            existing = UserSubscription.query.filter_by(user_id=user_id).first()
            if existing:
                return existing
            
            # Create 14-day trial
            subscription = UserSubscription(
                user_id=user_id,
                plan_id=plan.id,
                status='trial',
                trial_ends_at=datetime.utcnow() + timedelta(days=14),
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=14),
                usage_reset_date=datetime.utcnow()
            )
            
            db.session.add(subscription)
            db.session.commit()
            
            logger.info(f"Created trial subscription for user {user_id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Error creating trial subscription: {e}")
            db.session.rollback()
            return None
    
    def upgrade_subscription(self, user_id: int, new_plan_tier: str) -> Dict[str, Any]:
        """Upgrade user's subscription plan"""
        try:
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            if not subscription:
                return {'success': False, 'error': 'No subscription found'}
            
            new_plan = SubscriptionPlan.query.filter_by(tier=new_plan_tier).first()
            if not new_plan:
                return {'success': False, 'error': 'Invalid plan tier'}
            
            # Check if downgrade
            old_plan = subscription.plan
            is_downgrade = new_plan.price_monthly < old_plan.price_monthly
            
            # Update subscription
            subscription.plan_id = new_plan.id
            
            # If upgrading from trial, set as active
            if subscription.status == 'trial':
                subscription.status = 'active'
                subscription.trial_ends_at = None
                subscription.current_period_start = datetime.utcnow()
                subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
            
            db.session.commit()
            
            return {
                'success': True,
                'subscription': subscription.to_dict(),
                'is_downgrade': is_downgrade,
                'message': f"Successfully {'downgraded' if is_downgrade else 'upgraded'} to {new_plan.name} plan"
            }
            
        except Exception as e:
            logger.error(f"Error upgrading subscription: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def check_feature_access(self, user_id: int, feature: str) -> bool:
        """Check if user has access to a specific feature"""
        try:
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            if not subscription or not subscription.is_active():
                return False
            
            plan = subscription.plan
            if not plan:
                return False
            
            # Check feature availability
            feature_map = {
                'ai_matching': plan.has_ai_matching,
                'ai_writing': plan.has_ai_writing,
                'analytics': plan.has_analytics,
                'smart_tools': plan.has_smart_tools,
                'team': plan.has_team_collaboration,
                'api': plan.has_api_access,
                'white_label': plan.has_white_label
            }
            
            return feature_map.get(feature, False)
            
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return False
    
    def track_usage(self, user_id: int, feature_type: str, **kwargs) -> bool:
        """Track feature usage for billing and limits"""
        try:
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            if not subscription:
                return False
            
            # Check if monthly reset needed
            if subscription.usage_reset_date:
                if (datetime.utcnow() - subscription.usage_reset_date).days >= 30:
                    subscription.reset_monthly_usage()
            
            # Increment usage counters
            if feature_type == 'grant':
                subscription.grants_tracked_count += 1
            elif feature_type == 'application':
                subscription.applications_count_monthly += 1
            elif feature_type == 'ai_request':
                subscription.ai_requests_count_monthly += 1
            elif feature_type == 'report':
                subscription.reports_count_monthly += 1
            
            # Log usage
            usage_log = UsageLog(
                user_id=user_id,
                subscription_id=subscription.id,
                feature_type=feature_type,
                feature_name=kwargs.get('feature_name'),
                ai_model_used=kwargs.get('ai_model_used'),
                ai_tokens_used=kwargs.get('ai_tokens_used'),
                ai_cost_estimate=kwargs.get('ai_cost_estimate'),
                metadata=kwargs.get('metadata')
            )
            
            db.session.add(usage_log)
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking usage: {e}")
            db.session.rollback()
            return False
    
    def get_usage_summary(self, user_id: int) -> Dict[str, Any]:
        """Get usage summary for user"""
        try:
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            if not subscription:
                return {'error': 'No subscription found'}
            
            # Calculate usage percentages
            plan = subscription.plan
            usage_data = {
                'plan_name': plan.name if plan else 'Unknown',
                'status': subscription.status,
                'trial_ends': subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
                'usage': {
                    'grants': {
                        'used': subscription.grants_tracked_count,
                        'limit': plan.max_grants_tracked if plan else 0,
                        'percentage': (subscription.grants_tracked_count / max(plan.max_grants_tracked, 1) * 100) if plan else 0
                    },
                    'applications': {
                        'used': subscription.applications_count_monthly,
                        'limit': plan.max_applications_monthly if plan else 0,
                        'percentage': (subscription.applications_count_monthly / max(plan.max_applications_monthly, 1) * 100) if plan else 0
                    },
                    'ai_requests': {
                        'used': subscription.ai_requests_count_monthly,
                        'limit': plan.max_ai_requests_monthly if plan else 0,
                        'percentage': (subscription.ai_requests_count_monthly / max(plan.max_ai_requests_monthly, 1) * 100) if plan else 0
                    },
                    'reports': {
                        'used': subscription.reports_count_monthly,
                        'limit': plan.max_reports_monthly if plan else 0,
                        'percentage': (subscription.reports_count_monthly / max(plan.max_reports_monthly, 1) * 100) if plan else 0
                    }
                },
                'next_reset': (subscription.usage_reset_date + timedelta(days=30)).isoformat() if subscription.usage_reset_date else None
            }
            
            return usage_data
            
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return {'error': str(e)}
    
    def get_available_plans(self) -> List[Dict[str, Any]]:
        """Get all available subscription plans"""
        try:
            plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price_monthly).all()
            return [plan.to_dict() for plan in plans]
        except Exception as e:
            logger.error(f"Error getting plans: {e}")
            return []