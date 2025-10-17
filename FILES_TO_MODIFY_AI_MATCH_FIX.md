# Files to Modify: AI Smart Match Fix

This document lists **ALL files** that need modifications to fix the AI Smart Match issue and prevent future occurrences.

---

## 📁 IMMEDIATE DATABASE FIX (No Code Changes)

**Run this SQL first:**
```sql
UPDATE organizations SET user_id = 36 WHERE id = 45;
```

After this, AI Smart Match will work immediately since the profile is 100% complete.

---

## 📁 FILE 1: `app/api/ai_grants.py`

### Issue
Lines 109-114: Uses single-field lookup that fails if `user_id` is missing.

### Current Code (Lines 109-114)
```python
org = Organization.query.filter_by(user_id=user_id).first()
if not org:
    return jsonify({
        'success': False,
        'error': 'Organization profile not found. Please complete your profile.'
    }), 404
```

### Recommended Fix
```python
# Try primary lookup by user_id
org = Organization.query.filter_by(user_id=user_id).first()

# Fallback: Look up by user.org_id and auto-repair
if not org:
    user = User.query.get(user_id)
    if user and user.org_id:
        org = Organization.query.get(user.org_id)
        if org:
            # Auto-repair missing user_id
            org.user_id = user_id
            db.session.commit()
            logger.warning(f"Auto-repaired org_id {org.id} with user_id {user_id}")

if not org:
    return jsonify({
        'success': False,
        'error': 'Organization profile not found',
        'message': 'Please complete your organization profile to use AI matching',
        'action': 'redirect',
        'url': '/profile'
    }), 404

# Validate required fields for AI matching
required_fields = {
    'mission': org.mission,
    'focus_areas': org.get_focus_areas() if hasattr(org, 'get_focus_areas') else [],
    'location': f"{org.primary_city}, {org.primary_state}",
    'budget': org.annual_budget_range
}

missing_fields = [field for field, value in required_fields.items() 
                  if not value or value == ', ' or value == 'N/A, N/A']

if missing_fields:
    return jsonify({
        'success': False,
        'error': 'Incomplete organization profile',
        'message': f'Please add the following to your profile: {", ".join(missing_fields)}',
        'missing_fields': missing_fields,
        'profile_completeness': org.profile_completeness or 0,
        'action': 'redirect',
        'url': '/profile'
    }), 400
```

### Additional Import Needed
Add at top of file (around line 11):
```python
from app.models import Grant, Organization, User, db
```

---

## 📁 FILE 2: `app/api/auth.py`

### Issue
Lines 106-116: Creates organization without updating `user.org_id` - creates one-way link only.

### Current Code (Lines 106-116)
```python
# Create minimal Organization for the new user
# Low completeness ensures they go through onboarding
from app.models import Organization
org = Organization()
org.name = org_name
org.legal_name = org_name
org.user_id = result['user']['id']
org.created_by_user_id = result['user']['id']
org.profile_completeness = 10  # Needs onboarding
db.session.add(org)
db.session.commit()
```

### Recommended Fix
```python
# Create minimal Organization for the new user
# Low completeness ensures they go through onboarding
from app.models import Organization
org = Organization()
org.name = org_name
org.legal_name = org_name
org.user_id = result['user']['id']
org.created_by_user_id = result['user']['id']
org.profile_completeness = 10  # Needs onboarding
db.session.add(org)
db.session.flush()  # Get org.id before commit

# ✅ FIX: Create bi-directional link
user = User.query.get(result['user']['id'])
if user:
    user.org_id = org.id
    
db.session.commit()

# Verify relationship
if org.user_id != user.id or user.org_id != org.id:
    db.session.rollback()
    logger.error(f"Failed to link user {user.id} with org {org.id}")
    return jsonify({'error': 'Registration failed - organization setup error'}), 500

logger.info(f"Created org {org.id} for user {user.id} with bi-directional link")
```

---

## 📁 FILE 3: `app/api/onboarding_flow.py`

### Issue
Lines 84-90: Creates organization without updating `user.org_id` - same issue as auth.py.

### Current Code (Lines 84-90)
```python
if not org:
    org = Organization()
    org.user_id = user.id
    org.created_by_user_id = user.id
    db.session.add(org)
```

### Recommended Fix
```python
if not org:
    org = Organization()
    org.user_id = user.id
    org.created_by_user_id = user.id
    db.session.add(org)
    db.session.flush()  # Get org.id before proceeding
    
    # ✅ FIX: Create bi-directional link
    user.org_id = org.id
    db.session.commit()
    
    # Verify relationship
    if org.user_id != user.id or user.org_id != org.id:
        db.session.rollback()
        logger.error(f"Failed to link user {user.id} with org {org.id}")
        flash('There was an error setting up your organization. Please try again.', 'error')
        return redirect(url_for('onboarding.step1'))
    
    logger.info(f"Created org {org.id} for user {user.id} during onboarding")
```

### Additional Import Needed
Add at top if not present:
```python
import logging
logger = logging.getLogger(__name__)
```

---

## 📁 FILE 4: `app/templates/opportunities.html`

### Issue
Generic error handling doesn't help users understand what's wrong.

### Location
Find the AI Smart Match button click handler (search for "ai-match" or similar).

### Current Code (Approximate)
```javascript
async function loadAIRecommendations() {
    try {
        const response = await fetch('/api/ai-grants/match', {method: 'POST'});
        const data = await response.json();
        
        if (!response.ok) {
            alert('Error: ' + data.error);
            return;
        }
        
        displayResults(data.matched_grants);
    } catch (error) {
        alert('Error loading AI matches');
    }
}
```

### Recommended Fix
```javascript
async function loadAIRecommendations() {
    const button = document.querySelector('[data-action="ai-match"]');
    const resultsDiv = document.getElementById('aiResults');
    
    // Show loading state
    button.disabled = true;
    button.innerHTML = '<span class="spinner"></span> Analyzing your profile...';
    
    try {
        const response = await fetch('/api/ai-grants/match', {method: 'POST'});
        const data = await response.json();
        
        if (!response.ok) {
            // Handle specific error cases
            if (response.status === 404) {
                showProfilePrompt(data.message || 'Please complete your organization profile', data.url || '/profile');
                return;
            } else if (response.status === 400 && data.missing_fields) {
                showProfileCompletion(data.missing_fields, data.profile_completeness || 0, data.url || '/profile');
                return;
            }
            throw new Error(data.error || 'AI matching failed');
        }
        
        // Display results
        displayAIMatches(data.matched_grants);
        
    } catch (error) {
        console.error('AI Match Error:', error);
        showErrorMessage('Unable to generate AI matches. Please try again later.');
    } finally {
        button.disabled = false;
        button.innerHTML = '✨ AI Smart Match';
    }
}

function showProfilePrompt(message, redirectUrl) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md mx-4">
            <h3 class="text-xl font-bold mb-3">Complete Your Organization Profile</h3>
            <p class="text-gray-600 mb-4">${message}</p>
            <p class="text-sm text-gray-500 mb-6">AI matching requires information about your organization to find the best grants for you.</p>
            <div class="flex gap-3">
                <a href="${redirectUrl}" class="flex-1 bg-pink-500 hover:bg-pink-600 text-white px-4 py-2 rounded text-center">
                    Complete Profile
                </a>
                <button onclick="this.closest('.fixed').remove()" class="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded">
                    Maybe Later
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function showProfileCompletion(missingFields, completeness, redirectUrl) {
    const fieldsList = missingFields.map(f => `<li class="text-gray-600">• ${f}</li>`).join('');
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md mx-4">
            <h3 class="text-xl font-bold mb-2">Profile ${completeness}% Complete</h3>
            <p class="text-gray-600 mb-3">Add these fields to enable AI matching:</p>
            <ul class="mb-6">${fieldsList}</ul>
            <div class="flex gap-3">
                <a href="${redirectUrl}" class="flex-1 bg-pink-500 hover:bg-pink-600 text-white px-4 py-2 rounded text-center">
                    Add Missing Info
                </a>
                <button onclick="this.closest('.fixed').remove()" class="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded">
                    Cancel
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function showErrorMessage(message) {
    const alert = document.createElement('div');
    alert.className = 'fixed top-4 right-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded z-50';
    alert.innerHTML = `
        <div class="flex items-center gap-2">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-red-500 hover:text-red-700">&times;</button>
        </div>
    `;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
}
```

---

## 📁 FILE 5: `app/utils/error_responses.py` (NEW FILE)

### Purpose
Centralized error response formatting for consistent user feedback.

### Create New File
```python
"""
Consistent error response utilities for organization profile issues
"""

def org_profile_error(message, missing_fields=None, profile_completeness=0, redirect_url='/profile'):
    """Return helpful error response for organization profile issues
    
    Args:
        message: Main error message
        missing_fields: List of missing field names
        profile_completeness: Percentage (0-100)
        redirect_url: Where to send user to fix the issue
    
    Returns:
        dict: Formatted error response
    """
    response = {
        'error': 'Organization Profile Required',
        'message': message,
        'profile_completeness': profile_completeness,
        'action': 'redirect',
        'url': redirect_url
    }
    
    if missing_fields:
        response['missing_fields'] = missing_fields
        response['help_text'] = f"Add these fields to enable AI matching: {', '.join(missing_fields)}"
    
    return response


def ai_match_prerequisites():
    """Return list of prerequisites for AI matching
    
    Returns:
        dict: Prerequisites information
    """
    return {
        'required_fields': ['mission', 'focus_areas', 'location', 'budget'],
        'minimum_completeness': 50,
        'help_url': '/help/ai-matching',
        'description': 'AI matching requires basic organization information to find relevant grants'
    }


def organization_not_found_error(user_id):
    """Return error for missing organization
    
    Args:
        user_id: The user ID that has no organization
    
    Returns:
        dict: Error response
    """
    return {
        'error': 'Organization Not Found',
        'message': 'No organization profile found. Please complete your profile to use AI matching.',
        'action': 'redirect',
        'url': '/profile',
        'user_id': user_id
    }


def incomplete_profile_error(missing_fields, completeness=0):
    """Return error for incomplete profile
    
    Args:
        missing_fields: List of missing field names
        completeness: Profile completion percentage
    
    Returns:
        dict: Error response
    """
    return org_profile_error(
        message=f"Your organization profile is {completeness}% complete.",
        missing_fields=missing_fields,
        profile_completeness=completeness
    )
```

---

## 📁 FILE 6: `scripts/check_org_consistency.py` (NEW FILE)

### Purpose
Database consistency checker to find and fix orphaned organizations.

### Create New File
```python
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

from app import create_app, db
from app.models import User, Organization
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create Flask app for script context"""
    from flask import Flask
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
        # Try to find user by org_id
        user = User.query.filter_by(org_id=org.id).first()
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
        org = Organization.query.get(user.org_id)
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
        elif user.org_id != org.id:
            issues.append({
                'type': 'broken_reverse_link',
                'org_id': org.id,
                'org_name': org.name,
                'org_user_id': org.user_id,
                'user_org_id': user.org_id,
                'fix': f"UPDATE users SET org_id = {org.id} WHERE id = {org.user_id};"
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
                        user.org_id = org.id
                    fixed_count += 1
        
        elif issue['type'] == 'broken_reverse_link':
            user_id = issue.get('org_user_id')
            org_id = issue.get('org_id')
            user = User.query.get(user_id)
            
            if user and org_id:
                logger.info(f"Fixing: {issue['type']} - User {user_id} -> Org {org_id}")
                if not dry_run:
                    user.org_id = org_id
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
                    print(f"   {issue}")
                    print(f"   FIX: {issue['fix']}\n")
                
                print(f"\n💡 Run with --fix to automatically fix these issues")
            else:
                print("\n✅ No consistency issues found!")

if __name__ == '__main__':
    main()
```

---

## 📊 IMPLEMENTATION SUMMARY

### Priority 1: Immediate Fix (2 minutes)
✅ **Run SQL:**
```sql
UPDATE organizations SET user_id = 36 WHERE id = 45;
```

### Priority 2: Prevent Future Issues (30-45 minutes)
1. ✅ **app/api/auth.py** - Fix registration flow (bi-directional linking)
2. ✅ **app/api/onboarding_flow.py** - Fix onboarding flow (bi-directional linking)
3. ✅ **app/api/ai_grants.py** - Robust lookup + auto-repair + validation

### Priority 3: Better UX (30 minutes)
1. ✅ **app/templates/opportunities.html** - Enhanced error handling
2. ✅ **app/utils/error_responses.py** - Create new utility file

### Priority 4: Monitoring (30 minutes)
1. ✅ **scripts/check_org_consistency.py** - Create consistency checker
2. ✅ Run script to find other issues
3. ✅ Schedule weekly audit

---

## 🧪 TESTING CHECKLIST

### Test 1: Database Fix
```bash
# Run SQL
psql $DATABASE_URL -c "UPDATE organizations SET user_id = 36 WHERE id = 45;"

# Verify
psql $DATABASE_URL -c "SELECT user_id FROM organizations WHERE id = 45;"
# Expected: 36
```

### Test 2: AI Smart Match
1. Login as user (username: admin)
2. Go to Opportunities page
3. Click "AI Smart Match" button
4. Expected: See 10-20 grants with scores and explanations

### Test 3: Error Scenarios
```python
# Test incomplete profile
UPDATE organizations SET mission = NULL WHERE id = 45;
# Click AI Match → Should show modal with missing fields

# Restore
UPDATE organizations SET mission = 'To empower...' WHERE id = 45;
```

### Test 4: New Registration
1. Register new user
2. Check database: Both `org.user_id` and `user.org_id` should be set
3. Verify bi-directional link

### Test 5: Consistency Check
```bash
# Run check
python scripts/check_org_consistency.py

# If issues found, fix them
python scripts/check_org_consistency.py --fix
```

---

## 📈 EXPECTED OUTCOMES

### After Database Fix (Immediate)
- ✅ AI Smart Match works for user ID 36
- ✅ 10-20 grants displayed with AI scores
- ✅ Detailed explanations for each match
- ✅ High-quality results (profile is 100% complete)

### After Code Improvements
- ✅ New users get proper bi-directional links
- ✅ Auto-repair if user_id is missing
- ✅ Helpful error messages guide users
- ✅ Profile validation prevents wasted API calls
- ✅ Consistency checker finds and fixes issues

### Long-term Benefits
- ✅ No more orphaned organizations
- ✅ Better user experience with actionable errors
- ✅ Reduced support tickets
- ✅ Automated monitoring and repair

---

## 📋 FILES SUMMARY

**Files to Modify (3):**
1. `app/api/ai_grants.py` - Lines 109-114 (robust lookup + validation)
2. `app/api/auth.py` - Lines 106-116 (bi-directional linking)
3. `app/api/onboarding_flow.py` - Lines 84-90 (bi-directional linking)
4. `app/templates/opportunities.html` - AI Match button handler (better UX)

**New Files to Create (2):**
1. `app/utils/error_responses.py` - Error response utilities
2. `scripts/check_org_consistency.py` - Database consistency checker

**Total Work:** ~2 hours for all improvements
**Immediate Fix:** 2 minutes (SQL only)

---

**Generated:** October 17, 2025  
**Purpose:** Implementation guide for AI Smart Match fix  
**Status:** Ready for implementation
