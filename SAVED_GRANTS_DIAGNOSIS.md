# Saved Grants Functionality - Diagnosis Report

## Executive Summary
The Saved Grants feature has a **fully functional backend** but an **incomplete frontend implementation**. The API endpoints work correctly, but the UI elements are either not wired up or completely missing.

---

## Issue Breakdown

### ✅ What's Working (Backend)
The backend API is fully implemented and functional:

1. **API Endpoints** (in `app/api/grants.py`):
   - `POST /api/grants/<grant_id>/save` - Saves a grant for the current user
   - `GET /api/grants/saved` - Retrieves all saved grants for the current user
   - `DELETE /api/grants/<grant_id>/unsave` - Removes a grant from saved list

2. **Database Model** (in `app/models.py`):
   - `LovedGrant` model exists (line 579)
   - Proper relationships between User, Grant, and LovedGrant
   - Fields: user_id, grant_id, status, notes, loved_at, reminder_date, progress_percentage

3. **Multi-tenant Safety**:
   - All endpoints check for authenticated user
   - Queries are properly filtered by user_id
   - Duplicate prevention is in place

---

### ❌ What's NOT Working (Frontend)

#### 1. Save Grant Button - Not Wired Up
**Location**: `app/static/js/discovery.js` (lines 165-189)

**Problem**: The `saveGrant()` function exists but is not implemented:
```javascript
async function saveGrant(grantId) {
    // TODO: API call to save grant
    showError('Failed to save grant. Please try again.');
}
```

**Impact**: When users click "Save Grant" button, they just see an error message instead of the grant being saved.

---

#### 2. Saved Grants Page - Placeholder Only
**Location**: `app/templates/saved.html`

**Problem**: The page is just a placeholder:
```html
<h1>Saved</h1>
<section class="card">
  <h2>Coming soon</h2>
</section>
```

**Impact**: Users can navigate to `/saved` but see no saved grants, even if they have some.

---

#### 3. No Visual Indicators
**Problem**: There's no way to tell if a grant is already saved when browsing opportunities.

**Impact**: Users might try to save the same grant multiple times, creating poor UX.

---

## Recommended Fixes

### Fix 1: Implement the saveGrant() Function
**File**: `app/static/js/discovery.js`

Replace the stub function with:
```javascript
async function saveGrant(grantId) {
    try {
        const response = await fetch(`/api/grants/${grantId}/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showSuccess(`Grant saved! View it in <a href="/saved">Saved Grants</a>`);
            // Update button visual state
            const saveBtn = document.querySelector(`button[onclick*="${grantId}"]`);
            if (saveBtn) {
                saveBtn.innerHTML = '✓ Saved';
                saveBtn.disabled = true;
                saveBtn.classList.add('saved');
            }
        } else {
            showError(data.message || 'Failed to save grant');
        }
    } catch (error) {
        console.error('Save grant error:', error);
        showError('Failed to save grant. Please try again.');
    }
}
```

---

### Fix 2: Build the Saved Grants Page
**File**: `app/templates/saved.html`

Replace the placeholder with a full implementation:
```html
{% extends "base.html" %}
{% block title %}Saved Grants · Pink Lemonade{% endblock %}

{% block content %}
<div style="min-height:100vh;background:linear-gradient(135deg,#FAFAFA 0%,#F5F5F5 100%);padding:80px 20px 40px">
  <div style="max-width:1200px;margin:0 auto">
    
    <div style="text-align:center;margin-bottom:40px">
      <h1 style="font-size:2.5rem;font-weight:700;color:#2A2A2A;margin:0 0 12px 0">
        Saved Grants
      </h1>
      <p style="color:#6B6B6B;font-size:1.1rem;margin:0">
        Your bookmarked grant opportunities
      </p>
    </div>

    <div id="savedGrantsContainer">
      <div style="text-align:center;padding:40px">
        <div class="spinner"></div>
        <p>Loading saved grants...</p>
      </div>
    </div>

  </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', async () => {
    await loadSavedGrants();
});

async function loadSavedGrants() {
    const container = document.getElementById('savedGrantsContainer');
    
    try {
        const response = await fetch('/api/grants/saved');
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            container.innerHTML = `
                <div style="text-align:center;padding:40px">
                    <p style="color:#E63946;font-size:1.1rem">Failed to load saved grants</p>
                </div>
            `;
            return;
        }
        
        const grants = data.grants || [];
        
        if (grants.length === 0) {
            container.innerHTML = `
                <div style="text-align:center;padding:60px 20px">
                    <div style="font-size:3rem;margin-bottom:20px">📋</div>
                    <h3 style="color:#2A2A2A;margin:0 0 12px 0">No saved grants yet</h3>
                    <p style="color:#6B6B6B;margin:0 0 24px 0">
                        Browse <a href="/opportunities" style="color:#B8899A">opportunities</a> and save grants you're interested in
                    </p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:24px">
                ${grants.map(grant => createGrantCard(grant)).join('')}
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading saved grants:', error);
        container.innerHTML = `
            <div style="text-align:center;padding:40px">
                <p style="color:#E63946">Error loading saved grants</p>
            </div>
        `;
    }
}

function createGrantCard(grant) {
    const deadline = grant.deadline ? new Date(grant.deadline).toLocaleDateString() : 'No deadline';
    const amountRange = formatAmountRange(grant.amount_min, grant.amount_max);
    
    return `
        <div style="background:white;border-radius:16px;padding:24px;border:1px solid #F0F0F0;box-shadow:0 2px 12px rgba(0,0,0,0.06);position:relative">
            <button onclick="unsaveGrant(${grant.id})" 
                style="position:absolute;top:16px;right:16px;background:none;border:none;cursor:pointer;font-size:1.5rem;color:#E63946;padding:4px 8px"
                title="Remove from saved">
                ✕
            </button>
            
            <div style="margin-bottom:16px">
                <h3 style="font-size:1.2rem;font-weight:600;color:#2A2A2A;margin:0 0 8px 0;line-height:1.3;padding-right:40px">
                    ${grant.title}
                </h3>
                <p style="color:#B8899A;font-weight:500;margin:0;font-size:0.95rem">
                    ${grant.funder || 'Unknown Funder'}
                </p>
            </div>
            
            <div style="display:flex;gap:16px;margin-bottom:16px;flex-wrap:wrap">
                ${amountRange ? `
                <div style="display:flex;align-items:center;gap:6px;color:#6B6B6B;font-size:0.9rem">
                    <span>💰</span>
                    <span>${amountRange}</span>
                </div>
                ` : ''}
                
                <div style="display:flex;align-items:center;gap:6px;color:#6B6B6B;font-size:0.9rem">
                    <span>📅</span>
                    <span>${deadline}</span>
                </div>
            </div>
            
            ${grant.eligibility ? `
            <p style="color:#6B6B6B;font-size:0.9rem;line-height:1.5;margin:0 0 16px 0;
                display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden">
                ${grant.eligibility}
            </p>
            ` : ''}
            
            <div style="display:flex;gap:8px;margin-top:16px;padding-top:16px;border-top:1px solid #F0F0F0">
                <a href="/grant/${grant.id}" 
                    style="flex:1;text-align:center;padding:10px 20px;background:#B8899A;color:white;border-radius:8px;text-decoration:none;font-weight:500;font-size:0.9rem">
                    View Details
                </a>
            </div>
            
            <div style="margin-top:12px;font-size:0.8rem;color:#999">
                Saved on ${new Date(grant.saved_at).toLocaleDateString()}
            </div>
        </div>
    `;
}

function formatAmountRange(min, max) {
    if (!min && !max) return null;
    
    const formatter = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
    
    if (min && max && min !== max) {
        return `${formatter.format(min)} - ${formatter.format(max)}`;
    } else if (max) {
        return `Up to ${formatter.format(max)}`;
    } else if (min) {
        return `From ${formatter.format(min)}`;
    }
    return null;
}

async function unsaveGrant(grantId) {
    if (!confirm('Remove this grant from your saved list?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/grants/${grantId}/unsave`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            await loadSavedGrants();
        } else {
            alert('Failed to remove grant');
        }
    } catch (error) {
        console.error('Unsave error:', error);
        alert('Failed to remove grant');
    }
}
</script>
{% endblock %}
```

---

### Fix 3: Add Visual Indicators for Already-Saved Grants
Add a function to check saved status when loading grants and update button states accordingly.

---

## Testing Checklist

After implementing fixes, verify:

1. ✅ Click "Save Grant" button on Discovery page
2. ✅ See success message
3. ✅ Navigate to `/saved` page
4. ✅ See the saved grant displayed
5. ✅ Click the X button to unsave
6. ✅ Confirm grant is removed from the list
7. ✅ Try saving the same grant twice (should show "already saved")
8. ✅ Logout and login - saved grants should persist

---

## Summary

**Backend**: ✅ Fully functional  
**Frontend Discovery**: ⚠️ Button exists but not wired up  
**Frontend Saved Page**: ❌ Not implemented  
**Visual Indicators**: ❌ Not implemented  

**Estimated Fix Time**: 1-2 hours for a developer  
**Priority**: High - This is a core feature users expect to work
