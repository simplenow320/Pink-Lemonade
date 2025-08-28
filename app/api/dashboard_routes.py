"""
Smart Dashboard Routes - Profile-driven grant discovery
"""
from flask import Blueprint, render_template, jsonify, request, session, redirect
from app import db
from app.models import User, Organization, Grant, Analytics
from app.services.auth_manager import AuthManager
from app.services.grant_fetcher import GrantFetcher
from app.services.geoname_mapping import get_geoname_id
from app.services.ai_service import AIService
from datetime import datetime, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@AuthManager.require_auth
def index():
    """Main dashboard - different views for new vs returning users"""
    user = AuthManager.get_current_user()
    if not user:
        return redirect('/login')
    org = Organization.query.filter_by(user_id=user.id).first()
    
    # Check if new or returning user
    is_new_user = not org or org.profile_completeness < 80
    
    if is_new_user:
        # Guided discovery view for new users
        return render_template('dashboard/guided_discovery.html', user=user, org=org)
    else:
        # Power dashboard for returning users
        return render_template('dashboard/power_dashboard.html', user=user, org=org)

@dashboard_bp.route('/smart-discovery')
@AuthManager.require_auth
@AuthManager.require_onboarding
def smart_discovery():
    """Smart grant discovery based on profile"""
    user = AuthManager.get_current_user()
    if not user:
        return redirect('/login')
    org = Organization.query.filter_by(user_id=user.id).first()
    
    # Get personalized grants
    grants = get_profile_based_grants(org)
    
    return render_template('dashboard/smart_discovery.html', 
                         user=user, 
                         org=org, 
                         grants=grants)

@dashboard_bp.route('/api/profile-grants')
@AuthManager.require_auth
def get_profile_grants():
    """API endpoint for profile-based grant recommendations"""
    user = AuthManager.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    org = Organization.query.filter_by(user_id=user.id).first()
    
    if not org:
        return jsonify({'error': 'Organization profile not found'}), 404
    
    # Get grants based on profile
    grants = get_profile_based_grants(org, limit=25)
    
    # Calculate AI scores for top grants
    ai_service = AIService()
    for grant in grants[:10]:  # Score top 10 for performance
        try:
            # Use the match_grant method which exists on AIService
            score, explanation = ai_service.match_grant(org.to_dict(), grant)
            grant['ai_score'] = score
            grant['ai_score'] = score
        except:
            grant['ai_score'] = None
    
    return jsonify({
        'success': True,
        'grants': grants,
        'total': len(grants),
        'profile_used': {
            'focus_areas': org.focus_areas or [],
            'location': f"{org.city}, {org.state}",
            'budget': org.annual_budget,
            'keywords': org.keywords or []
        }
    })

@dashboard_bp.route('/api/refresh-matches')
@AuthManager.require_auth
def refresh_matches():
    """Refresh grant matches with latest data"""
    user = AuthManager.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    org = Organization.query.filter_by(user_id=user.id).first()
    
    if not org:
        return jsonify({'error': 'Complete your profile first'}), 400
    
    # Force refresh from APIs
    grants = get_profile_based_grants(org, force_refresh=True)
    
    return jsonify({
        'success': True,
        'message': f'Found {len(grants)} new matches!',
        'grants': grants[:10]  # Return top 10
    })

def get_profile_based_grants(org, limit=50, force_refresh=False):
    """Get grants matching organization profile using real APIs"""
    grants = []
    
    # Use GrantFetcher to get real grants from multiple sources
    fetcher = GrantFetcher()
    
    try:
        # Fetch grants from all sources (Federal Register, USAspending, Candid)
        fetch_result = fetcher.fetch_all_grants(limit=limit)
        
        # Also fetch Candid grants specifically for the org's state
        if org.state:
            candid_grants = fetcher.fetch_candid_grants(limit=20, state=org.state)
            
            # Format Candid grants for display
            for grant in candid_grants:
                grants.append({
                    'title': grant.get('title', 'Untitled Grant'),
                    'funder': grant.get('funder_name', 'Unknown Funder'),
                    'amount': format_amount(grant.get('amount')),
                    'deadline': grant.get('deadline', 'Rolling'),
                    'description': grant.get('description', ''),
                    'focus_areas': [grant.get('focus_area', 'General')],
                    'source': 'Candid',
                    'match_reason': f"Located in {org.state}"
                })
        
        # Add grants from other sources
        if fetch_result.get('success'):
            # The grants were already stored in DB by fetch_all_grants
            # We can query them from the database
            from app.models import Grant
            db_grants = Grant.query.order_by(Grant.created_at.desc()).limit(limit).all()
            
            for grant in db_grants:
                grants.append({
                    'title': grant.title,
                    'funder': grant.funder,
                    'amount': format_amount(grant.amount_min or grant.amount_max),
                    'deadline': grant.deadline.strftime('%Y-%m-%d') if grant.deadline else 'Rolling',
                    'description': grant.eligibility or '',
                    'focus_areas': [grant.geography or 'National'],
                    'source': grant.source_name or 'Federal',
                    'match_reason': 'Recently added grant opportunity'
                })
                
    except Exception as e:
        print(f"Grant fetch error: {e}")
    
    # Add some default high-quality grants if we don't have enough
    if len(grants) < 5:
        grants.extend(get_default_grants_for_type(org.type))
    
    return grants[:limit]

def get_min_grant_amount(budget):
    """Calculate minimum grant amount based on budget"""
    budget_map = {
        'under_50k': 1000,
        '50k_100k': 5000,
        '100k_250k': 10000,
        '250k_500k': 25000,
        '500k_1m': 50000,
        '1m_5m': 100000,
        'over_5m': 250000
    }
    return budget_map.get(budget, 5000)

def get_max_grant_amount(budget):
    """Calculate maximum grant amount based on budget"""
    budget_map = {
        'under_50k': 50000,
        '50k_100k': 100000,
        '100k_250k': 250000,
        '250k_500k': 500000,
        '500k_1m': 1000000,
        '1m_5m': 5000000,
        'over_5m': 10000000
    }
    return budget_map.get(budget, 100000)

def format_amount(amount):
    """Format grant amount for display"""
    if not amount:
        return "Amount Varies"
    if isinstance(amount, (int, float)):
        if amount >= 1000000:
            return f"${amount/1000000:.1f}M"
        elif amount >= 1000:
            return f"${amount/1000:.0f}K"
        else:
            return f"${amount:.0f}"
    return str(amount)

def get_default_grants_for_type(org_type):
    """Get default grants based on organization type"""
    defaults = {
        'faith_based': [
            {
                'title': 'Lilly Endowment Religion Grant',
                'funder': 'Lilly Endowment Inc.',
                'amount': '$25K - $100K',
                'deadline': 'Quarterly',
                'description': 'Supporting faith-based community programs',
                'focus_areas': ['Religion', 'Community'],
                'source': 'Foundation',
                'match_reason': 'Perfect for faith-based organizations'
            }
        ],
        'educational': [
            {
                'title': 'Gates Foundation Education Grant',
                'funder': 'Bill & Melinda Gates Foundation',
                'amount': '$50K - $500K',
                'deadline': 'Annual',
                'description': 'Advancing educational equity and opportunity',
                'focus_areas': ['Education', 'Youth'],
                'source': 'Foundation',
                'match_reason': 'Ideal for educational institutions'
            }
        ]
    }
    return defaults.get(org_type, [])