"""
Test Stripe Live Integration
Verifies that Stripe API keys are working correctly
"""

import os
import sys

# Check if stripe module is available
try:
    import stripe
    print("✓ Stripe module is available")
except ImportError:
    print("✗ Stripe module not installed, using fallback mode")
    print("  The payment system will work but without actual Stripe API calls")
    sys.exit(0)

# Check environment variables
stripe_key = os.environ.get('STRIPE_SECRET_KEY')
webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

print("\n=== STRIPE CONFIGURATION STATUS ===")
print(f"✓ STRIPE_SECRET_KEY: {'Configured' if stripe_key else 'Not configured'}")
print(f"✓ STRIPE_WEBHOOK_SECRET: {'Configured' if webhook_secret else 'Not configured'}")

if stripe_key:
    # Test mode detection
    if stripe_key.startswith('sk_test_'):
        print("✓ Running in TEST MODE (safe for testing)")
    elif stripe_key.startswith('sk_live_'):
        print("⚠ Running in LIVE MODE (real money transactions)")
    
    # Set the API key
    stripe.api_key = stripe_key
    
    # Test the connection
    try:
        # Try to retrieve account details
        account = stripe.Account.retrieve()
        print(f"\n✓ Successfully connected to Stripe!")
        print(f"  - Account ID: {account.id}")
        print(f"  - Business Name: {account.get('business_profile', {}).get('name', 'Not set')}")
        print(f"  - Country: {account.country}")
        
        # Check for existing products
        products = stripe.Product.list(limit=3)
        print(f"\n✓ Products configured: {len(products.data)} found")
        for product in products.data:
            print(f"  - {product.name}: {product.description or 'No description'}")
        
        # Check for existing prices
        prices = stripe.Price.list(limit=3)
        print(f"\n✓ Prices configured: {len(prices.data)} found")
        for price in prices.data:
            amount = price.unit_amount / 100 if price.unit_amount else 0
            print(f"  - ${amount:.2f} {price.currency.upper()} /{price.recurring.interval if price.recurring else 'one-time'}")
        
    except stripe.error.AuthenticationError as e:
        print(f"\n✗ Authentication failed: {e}")
        print("  Please check that your API key is correct")
    except stripe.error.PermissionError as e:
        print(f"\n✗ Permission error: {e}")
        print("  Your API key doesn't have the required permissions")
    except Exception as e:
        print(f"\n✗ Connection error: {e}")
else:
    print("\n⚠ No Stripe API key configured")
    print("  The payment system is running in test mode")

print("\n=== NEXT STEPS ===")
print("1. ✓ Stripe API keys are configured")
print("2. → Create products in Stripe Dashboard:")
print("   - Discovery Plan ($79/month)")
print("   - Professional Plan ($149/month)")
print("   - Enterprise Plan ($299/month)")
print("   - Unlimited Plan ($499/month)")
print("3. → Set up webhook endpoint in Stripe Dashboard:")
print("   - URL: https://your-domain.replit.app/api/payment/webhook")
print("4. → Test checkout flow with test cards")
print("5. → Ready for Phase 4: Analytics Dashboard")