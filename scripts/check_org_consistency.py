#!/usr/bin/env python3
"""
Check and fix user-organization relationship consistency

Usage:
    python scripts/check_org_consistency.py          # Check only (dry run)
    python scripts/check_org_consistency.py --fix    # Auto-fix issues
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from app import db
from app.models import User, Organization
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """Create Flask app for script context"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    db.init_app(app)
    return app

def check_consistency():
    """Find and report organization relationship issues"""
    issues = []
    
    # Check 1: Organizations without user_id
    orphaned_orgs = Organization.query.filter_by(user_id=None).all()
    for org in orphaned_orgs:
        # Try to find user by org_id (convert to string for comparison)
        user = User.query.filter_by(org_id=str(org.id)).first()
        issues.append({
            'type': 'orphaned_org',
            'org_id': org.id,
            'org_name': org.name,
            'potential_user_id': user.id if user else None,
            'potential_user_email': user.email if user else None,
            'fix': f"UPDATE organizations SET user_id = {user.id} WHERE id = {org.id};" if user else "Manual review needed - no user found"
        })
    
    # Check 2: Users with org_id but org has no user_id
    users = User.query.filter(User.org_id.isnot(None)).all()
    for user in users:
        # Convert org_id to int if it's a string
        try:
            org_id = int(user.org_id) if user.org_id else None
        except (ValueError, TypeError):
            org_id = None
        
        if org_id:
            org = Organization.query.get(org_id)
            if org and org.user_id != user.id:
                issues.append({
                    'type': 'mismatched_link',
                    'user_id': user.id,
                    'user_email': user.email,
                    'org_id': org.id,
                    'org_name': org.name,
                    'org_user_id': org.user_id,
                    'fix': f"UPDATE organizations SET user_id = {user.id} WHERE id = {org.id};"
                })
    
    # Check 3: Organizations linked to wrong user
    orgs_with_user = Organization.query.filter(Organization.user_id.isnot(None)).all()
    for org in orgs_with_user:
        user = User.query.get(org.user_id)
        if not user:
            issues.append({
                'type': 'broken_user_link',
                'org_id': org.id,
                'org_name': org.name,
                'org_user_id': org.user_id,
                'fix': f"UPDATE organizations SET user_id = NULL WHERE id = {org.id}; -- User {org.user_id} not found"
            })
        elif user.org_id != str(org.id):  # Convert org.id to string for comparison
            issues.append({
                'type': 'broken_reverse_link',
                'org_id': org.id,
                'org_name': org.name,
                'org_user_id': org.user_id,
                'user_org_id': user.org_id,
                'fix': f"UPDATE users SET org_id = '{org.id}' WHERE id = {org.user_id};"
            })
    
    return issues

def auto_fix(dry_run=True):
    """Automatically fix fixable issues"""
    issues = check_consistency()
    fixed_count = 0
    
    for issue in issues:
        if issue['type'] in ['orphaned_org', 'mismatched_link'] and issue.get('potential_user_id'):
            org = Organization.query.get(issue['org_id'])
            user_id = issue.get('potential_user_id') or issue.get('user_id')
            
            if org and user_id:
                logger.info(f"Fixing: {issue['type']} - Org {org.id} -> User {user_id}")
                if not dry_run:
                    org.user_id = user_id
                    user = User.query.get(user_id)
                    if user:
                        user.org_id = str(org.id)  # Convert to string for user.org_id
                    fixed_count += 1
        
        elif issue['type'] == 'broken_reverse_link':
            user_id = issue.get('org_user_id')
            org_id = issue.get('org_id')
            user = User.query.get(user_id)
            
            if user and org_id:
                logger.info(f"Fixing: {issue['type']} - User {user_id} -> Org {org_id}")
                if not dry_run:
                    user.org_id = str(org_id)  # Convert to string for user.org_id
                    fixed_count += 1
    
    if not dry_run and fixed_count > 0:
        db.session.commit()
        logger.info(f"✅ Fixed {fixed_count} issues")
    elif dry_run and fixed_count > 0:
        logger.info(f"DRY RUN: Would fix {fixed_count} issues. Run with --fix to apply changes")
    
    return fixed_count

def main():
    """Main entry point"""
    app = create_app()
    
    with app.app_context():
        if '--fix' in sys.argv:
            logger.info("Running in FIX mode...")
            auto_fix(dry_run=False)
        else:
            logger.info("Running in CHECK mode (dry run)...")
            issues = check_consistency()
            
            if issues:
                print(f"\n⚠️  Found {len(issues)} consistency issues:\n")
                for i, issue in enumerate(issues, 1):
                    print(f"{i}. {issue['type'].upper().replace('_', ' ')}")
                    for key, value in issue.items():
                        if key != 'type':
                            print(f"   {key}: {value}")
                    print()
                
                print(f"\n💡 Run with --fix to automatically fix these issues")
            else:
                print("\n✅ No consistency issues found!")

if __name__ == '__main__':
    main()
