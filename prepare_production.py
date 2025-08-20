#!/usr/bin/env python
"""Prepare platform for production - remove all test data"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Organization, Grant

def clean_database():
    """Remove all test data for production"""
    app = create_app()
    
    with app.app_context():
        print("🧹 Cleaning database for production...")
        
        # Remove all test data
        Grant.query.delete()
        User.query.delete()
        Organization.query.delete()
        db.session.commit()
        
        print("✅ Database cleaned - ready for production")
        
        # Verify empty state
        org_count = Organization.query.count()
        user_count = User.query.count()
        grant_count = Grant.query.count()
        
        print(f"\n📊 Production Database Status:")
        print(f"  Organizations: {org_count}")
        print(f"  Users: {user_count}")
        print(f"  Grants: {grant_count}")
        
        return org_count == 0 and user_count == 0 and grant_count == 0

if __name__ == "__main__":
    if clean_database():
        print("\n🚀 PLATFORM READY FOR PRODUCTION")
        print("Real organizations can now sign up and use the platform")
    else:
        print("\n❌ Error: Database not properly cleaned")