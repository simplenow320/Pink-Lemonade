# AI Smart Match Feature - Diagnostic Report

## Executive Summary
The AI Smart Match feature is failing with a **405 Method Not Allowed** error. The root cause is a **URL routing mismatch** between the frontend request and backend endpoint definition. The frontend is calling `/api/ai-grants/match` while the backend expects `/api/ai-grants/match/<org_id>`.

---

## 1. Error Analysis

### Error Message
```
Error getting AI recommendations. Please try again.
```

### Root Cause (From Server Logs)
```
[2025-10-17 13:11:51,140] ERROR in app: Exception on /api/ai-grants/match [POST]
werkzeug.exceptions.MethodNotAllowed: 405 Method Not Allowed: The method is not allowed for the requested URL.
```

**Diagnosis:** The frontend is making a POST request to `/api/ai-grants/match`, but no route exists at this exact URL. The backend route requires an organization ID parameter in the URL path.

---

## 2. API Connectivity Analysis

### Frontend Request (opportunities.html, Line 397-406)
```javascript
function performAIMatch() {
    showLoading();
    
    fetch('/api/ai-grants/match', {  // ❌ Missing org_id in URL
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            use_profile: true,
            include_explanations: true
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        displayAIResults(data.matches || []);
    })
    .catch(error => {
        hideLoading();
        showError('Error getting AI recommendations. Please try again.');
    });
}
```

### Backend Route Definition (ai_grants.py, Line 94)
```python
@ai_grants_bp.route('/match/<int:org_id>', methods=['GET', 'POST'])
@request_timeout_protection(max_seconds=6)
def get_ai_matched_grants(org_id):
    """Get AI-matched grants for an organization"""
    # ... implementation
```

### Blueprint Registration (app/__init__.py, Line 304)
```python
flask_app.register_blueprint(ai_grants_bp, url_prefix='/api/ai-grants')
```

### URL Resolution
- **Frontend calls:** `/api/ai-grants/match`
- **Backend expects:** `/api/ai-grants/match/<int:org_id>` (e.g., `/api/ai-grants/match/1`)
- **Result:** 405 Method Not Allowed because the URL pattern doesn't match

---

## 3. Environment Variables Check

### OpenAI API Key
✅ **Status:** EXISTS
- The OPENAI_API_KEY is properly configured
- AI service can initialize successfully
- Not a contributing factor to this error

### Session Management
✅ **Status:** FUNCTIONAL
- Application uses Flask sessions to store user_id and org_id
- Session data is available: `session['user_id']` and `session['org_id']`
- Other endpoints successfully retrieve org_id from session

---

## 4. Backend Endpoint Response Analysis

### Current Endpoint Behavior
The endpoint `/api/ai-grants/match/<int:org_id>` expects:
1. **URL Parameter:** `org_id` as an integer in the path
2. **Request Method:** GET or POST
3. **Session Data:** User must be authenticated (user_id in session)
4. **Response:** JSON with matched grants and AI explanations

### What Happens When Called Incorrectly
1. Flask router cannot match `/api/ai-grants/match` to any route
2. No route accepts POST at this exact URL (missing org_id)
3. Flask raises MethodNotAllowed exception
4. Error propagates to frontend as generic error
5. User sees: "Error getting AI recommendations. Please try again."

---

## 5. Frontend Integration Logic Analysis

### Session Data Availability
The application stores organization ID in the session:
```python
# From auth.py login flow
session['user_id'] = user.id
session['org_id'] = user.org_id
```

### Pattern Used in Other Endpoints
Other API endpoints successfully retrieve org_id from session:
```python
# From dashboard_routes.py
user_id = session.get('user_id')
org = Organization.query.filter_by(user_id=user_id).first()
```

### Frontend Issue
The `performAIMatch()` function:
1. ❌ Does NOT retrieve org_id from session/user context
2. ❌ Does NOT include org_id in the URL
3. ❌ Sends POST to incomplete URL path
4. ✅ Correctly sends JSON body with preferences

---

## 6. Code Recommendations (DO NOT IMPLEMENT - ANALYSIS ONLY)

### Option 1: Frontend Fix (Recommended - Simpler)
**Modify:** `app/templates/opportunities.html` (Line 394-416)

**Change the fetch URL to include org_id from user session:**

```javascript
function performAIMatch() {
    showLoading();
    
    // Get org_id from user session (passed via template or API)
    const orgId = {{ session.get('org_id', 'null') }}; // Or from user context
    
    if (!orgId) {
        showError('Organization profile not found. Please complete your profile first.');
        hideLoading();
        return;
    }
    
    fetch(`/api/ai-grants/match/${orgId}`, {  // ✅ Include org_id in URL
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            use_profile: true,
            include_explanations: true
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        displayAIResults(data.matches || []);
    })
    .catch(error => {
        hideLoading();
        showError('Error getting AI recommendations. Please try again.');
    });
}
```

**Pros:**
- Minimal code change (1 line)
- Follows existing API pattern
- No backend changes needed
- Works with existing authentication flow

**Cons:**
- Requires org_id to be available in frontend context

---

### Option 2: Backend Fix (Alternative - More Complex)
**Add new route:** `app/api/ai_grants.py`

**Create a session-aware endpoint that doesn't require org_id in URL:**

```python
@ai_grants_bp.route('/match', methods=['POST'])  # No org_id parameter
@request_timeout_protection(max_seconds=6)
def get_ai_matched_grants_from_session():
    """Get AI-matched grants using org_id from session"""
    from flask import session
    
    # Get org_id from session
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Authentication required'
        }), 401
    
    # Get organization for this user
    org = Organization.query.filter_by(user_id=user_id).first()
    if not org:
        return jsonify({
            'success': False,
            'error': 'Organization profile not found'
        }), 404
    
    # Delegate to existing function
    return get_ai_matched_grants(org.id)
```

**Pros:**
- No frontend changes needed
- Automatically handles org_id from session
- More RESTful (data from session, not URL)

**Cons:**
- Requires backend code changes
- Adds another route to maintain
- Duplicates some logic

---

### Option 3: Hybrid Approach (Most Robust)
**Modify backend to accept BOTH patterns:**

```python
# Keep existing route
@ai_grants_bp.route('/match/<int:org_id>', methods=['GET', 'POST'])
@request_timeout_protection(max_seconds=6)
def get_ai_matched_grants(org_id):
    # ... existing implementation

# Add new session-aware route
@ai_grants_bp.route('/match', methods=['POST'])
@request_timeout_protection(max_seconds=6)
def get_ai_matched_grants_auto():
    """Auto-detect org_id from session"""
    from flask import session
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    org = Organization.query.filter_by(user_id=user_id).first()
    if not org:
        return jsonify({'success': False, 'error': 'No organization'}), 404
    
    return get_ai_matched_grants(org.id)
```

**Pros:**
- Works immediately without frontend changes
- Maintains backward compatibility
- Supports both URL and session-based org_id

**Cons:**
- Two routes doing similar things
- More code to maintain

---

## 7. Testing Recommendations

### Before Fix
**Test the current error:**
```bash
# Should return 405 error
curl -X POST http://localhost:5000/api/ai-grants/match \
  -H "Content-Type: application/json" \
  -d '{"use_profile": true}'
```

### After Fix (Option 1 - Frontend)
**Test with org_id in URL:**
```bash
# Should return matched grants
curl -X POST http://localhost:5000/api/ai-grants/match/1 \
  -H "Content-Type: application/json" \
  -H "Cookie: session=<session_cookie>" \
  -d '{"use_profile": true, "include_explanations": true}'
```

### After Fix (Option 2/3 - Backend)
**Test session-aware route:**
```bash
# Should auto-detect org_id from session
curl -X POST http://localhost:5000/api/ai-grants/match \
  -H "Content-Type: application/json" \
  -H "Cookie: session=<session_cookie>" \
  -d '{"use_profile": true, "include_explanations": true}'
```

---

## 8. Additional Findings

### OpenAI Integration
✅ **Status:** Working
- AI service initializes successfully
- API key is valid and configured
- Timeout protection is properly implemented (6 seconds max)

### Session Management
✅ **Status:** Working
- Flask sessions are functional
- User authentication works
- org_id is stored in session during login

### Database Connectivity
✅ **Status:** Working
- PostgreSQL connection is active
- Grant and Organization models are accessible
- No database-related errors in logs

### External API Status
⚠️ **Note:** Some external grant sources have issues (not related to AI Match):
- Candid API: 401 Unauthorized (trial expired)
- SAM.gov: 429 Too Many Requests (rate limited)
- These don't affect the AI matching functionality

---

## 9. Recommended Implementation Steps

### Immediate Fix (Choose One)

**🎯 RECOMMENDED: Option 1 (Frontend Fix)**
1. Update `app/templates/opportunities.html`
2. Change fetch URL from `/api/ai-grants/match` to `/api/ai-grants/match/${orgId}`
3. Ensure org_id is available in template context (via session or user object)
4. Test with authenticated user
5. Verify AI recommendations display correctly

**Alternative: Option 3 (Backend Fix)**
1. Add new route `@ai_grants_bp.route('/match', methods=['POST'])`
2. Extract org_id from session
3. Query Organization table for user's org
4. Call existing `get_ai_matched_grants(org_id)` function
5. Test without changing frontend

### Validation Steps
1. ✅ Authenticate as a user with an organization
2. ✅ Click "🤖 AI Smart Match" button
3. ✅ Verify loading state appears
4. ✅ Confirm no 405 error in browser console
5. ✅ Check matched grants display with AI scores
6. ✅ Verify explanations and match percentages show correctly

---

## 10. Summary

### Problem
Frontend calls `/api/ai-grants/match` but backend expects `/api/ai-grants/match/<org_id>`.

### Root Cause
URL routing mismatch - missing organization ID parameter.

### Impact
AI Smart Match feature completely non-functional, showing generic error.

### Solution
Add org_id to frontend URL OR create session-aware backend route.

### Dependencies
- ✅ OpenAI API key configured
- ✅ Database connected
- ✅ Session management working
- ✅ Organization data available

### Complexity
**Low** - Simple routing fix, no architectural changes needed.

---

## Appendix: Related Code Files

### Files to Modify (Option 1)
- `app/templates/opportunities.html` (Line 397)

### Files to Modify (Option 2/3)
- `app/api/ai_grants.py` (Add new route)

### Files Referenced
- `app/__init__.py` (Blueprint registration)
- `app/api/auth.py` (Session management)
- `app/models.py` (Organization model)
- `app/services/ai_grant_matcher.py` (AI matching service)

---

**Report Generated:** October 17, 2025  
**System Status:** Application running, AI services operational  
**Issue Severity:** High (Feature completely broken)  
**Fix Complexity:** Low (1-10 lines of code)
