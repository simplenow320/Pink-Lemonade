"""
Initialize Phase 2 Subscription Plans in Database
Creates all subscription plans with competitive pricing
"""

import os
import sys
sys.path.append('.')

from app import create_app, db
from app.models import SubscriptionPlan, PlanTier
from app.services.subscription_service import SubscriptionService

def init_subscription_plans():
    """Initialize subscription plans in database"""
    app = create_app()
    
    with app.app_context():
        print("🚀 Initializing Phase 2 Subscription Plans...")
        
        # Initialize subscription service
        service = SubscriptionService()
        
        # Ensure plans exist in database
        service.ensure_plans_exist()
        
        # Verify plans were created
        plans = SubscriptionPlan.query.all()
        
        if plans:
            print(f"✅ Successfully created {len(plans)} subscription plans:")
            for plan in plans:
                print(f"   • {plan.name}: ${plan.price_monthly}/month")
        else:
            print("⚠️  No plans created. They may already exist.")
        
        # Check existing plans
        existing_plans = SubscriptionPlan.query.all()
        if existing_plans:
            print(f"\n📊 Current plans in database:")
            for plan in existing_plans:
                print(f"   • {plan.name} ({plan.tier}): ${plan.price_monthly}/month")
                print(f"     - Max users: {plan.max_users}")
                print(f"     - Max grants: {plan.max_grants_tracked}")
                print(f"     - AI requests/month: {plan.max_ai_requests_monthly}")
        
        print("\n✅ Phase 2 data initialization complete!")

if __name__ == "__main__":
    init_subscription_plans()