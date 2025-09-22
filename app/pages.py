from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps
from app.services.stats_service import get_dashboard_stats, get_top_matches
from app.models import Grant

# Simple login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('pages.login'))
        return f(*args, **kwargs)
    return decorated_function

pages = Blueprint("pages", __name__)

@pages.get("/")
def home():
    return render_template("index.html", active="home")

@pages.get("/register")
def register():
    return render_template("auth/register.html")

@pages.get("/login")
def login():
    return render_template("auth/login.html")

@pages.get("/forgot-password")
def forgot_password():
    return render_template("auth/forgot_password.html")

@pages.get("/reset-password")
def reset_password():
    return render_template("auth/reset_password.html")

@pages.get("/verify-email")
def verify_email():
    from flask import request, redirect, url_for, flash
    from app.services.auth_service import AuthService
    
    auth_service = AuthService()
    token = request.args.get('token')
    
    if not token:
        return redirect(url_for('pages.login'))
    
    result = auth_service.verify_email(token)
    
    if result['success']:
        return redirect(url_for('pages.login') + '?verified=true')
    else:
        return redirect(url_for('pages.login'))

@pages.get("/dashboard")
@login_required
def dashboard():
    # Get the actual user's organization
    from app.models import Organization
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('pages.login'))
    
    # Find user's organization
    org = Organization.query.filter(
        (Organization.user_id == user_id) | 
        (Organization.created_by_user_id == user_id)
    ).first()
    
    if not org:
        # No org yet, redirect to onboarding
        return redirect('/onboarding/welcome')
    
    org_id = org.id
    
    # If organization profile is incomplete, suggest completing it
    if org.profile_completeness < 80:
        # Trigger grant fetching for initial matches
        from app.services.grant_fetcher import GrantFetcher
        fetcher = GrantFetcher()
        try:
            fetcher.fetch_all_grants(limit=10)
        except:
            pass  # Continue even if fetching fails
    
    stats = get_dashboard_stats(org_id)
    top_matches = [{
        "title": g.title,
        "funder": g.funder,
        "link": g.link,
        "fit": getattr(g, "match_score", None),
        "deadline": g.deadline.isoformat() if g.deadline else None
    } for g in get_top_matches(org_id)]
    return render_template("dashboard.html", active="dashboard", stats=stats, top_matches=top_matches, org_id=org_id)

@pages.get("/opportunities")
@login_required
def opportunities():
    # Get user's organization and trigger grant discovery
    from app.models import Organization, Grant
    user_id = session.get('user_id')
    
    org = Organization.query.filter(
        (Organization.user_id == user_id) | 
        (Organization.created_by_user_id == user_id)
    ).first()
    
    if org:
        # Trigger grant discovery to find real opportunities
        from app.services.grant_fetcher import GrantFetcher
        fetcher = GrantFetcher()
        try:
            # Fetch grants from real APIs (Federal Register, USAspending, Candid)
            fetcher.fetch_all_grants(limit=30)
        except Exception as e:
            print(f"Grant fetching error: {e}")
        
        # Get discovered grants from database
        grants = Grant.query.filter_by(org_id=org.id).order_by(Grant.match_score.desc()).limit(50).all()
    else:
        grants = []
    
    # Use the comprehensive opportunities template with all 50 states and Candid access
    return render_template("opportunities.html", active="opportunities", grants=grants, org=org)

@pages.get("/saved")
@login_required
def saved():
    return render_template("saved.html", active="saved")



@pages.get("/settings")
@login_required
def settings():
    return render_template("settings.html", active="settings")

@pages.get("/smart-tools")
@login_required
def smart_tools():
    return render_template("smart_tools.html", active="smart-tools")

# Onboarding routes
@pages.get("/onboarding/step1")
@login_required
def onboarding_step1():
    return render_template("onboarding/step1_basics.html")

@pages.get("/onboarding/step2")
@login_required  
def onboarding_step2():
    return render_template("onboarding/step2_programs.html")

@pages.get("/onboarding/step3")
@login_required
def onboarding_step3():
    return render_template("onboarding/step3_capacity.html")

@pages.get("/onboarding/step4")
@login_required
def onboarding_step4():
    return render_template("onboarding/step4_grant_history.html")

@pages.get("/onboarding/step5")
@login_required
def onboarding_step5():
    return render_template("onboarding/step5_ai_learning.html")

@pages.get("/profile")
@login_required
def profile():
    return render_template("profile.html", active="profile")

@pages.get("/writing")
@login_required
def writing():
    return render_template("writing.html", active="writing")



@pages.get("/r/<token>")
def public_intake(token):
    """Public intake form with token access"""
    return render_template("public_intake.html", token=token, active=None)

@pages.get("/live-data")
def live_data():
    """Live Data Integration Page"""
    return render_template("live_data.html", active="live")

@pages.get("/journey")
def journey():
    """Interactive Onboarding Journey Page"""
    return render_template("onboarding.html", active="journey")

@pages.get("/profile-legacy")
def profile_legacy():
    """Legacy Organization Profile Page"""
    return render_template("profile.html", active="profile")

@pages.get("/case-support")
def case_support():
    """Case for Support Generator Form"""
    return render_template("case_support_form.html", active="writing")

@pages.get("/grant-pitch")
def grant_pitch():
    """Grant Pitch Generator Form"""
    return render_template("grant_pitch_form.html", active="writing")

@pages.get("/impact-report")
def impact_report():
    """Impact Report Generator Form"""
    return render_template("impact_report_form.html", active="writing")

@pages.get("/grant-tracker")
def grant_tracker():
    """Grant Tracker Dashboard"""
    return render_template("grant_tracker.html", active="writing")

@pages.get("/settings-guided")
def settings_guided():
    """Guided Organization Setup Form"""
    return render_template("settings_guided.html", active="profile")

@pages.get("/grant-intelligence")
def grant_intelligence():
    """Grant Intelligence Dashboard"""
    return render_template("grant_intelligence.html", active="writing")

@pages.get("/admin")
def admin_dashboard():
    """Admin Dashboard Page"""
    return render_template("admin_dashboard.html", active="admin")

@pages.get("/grant/<int:grant_id>")
def grant_detail(grant_id):
    """Grant Detail Page"""
    grant = Grant.query.get_or_404(grant_id)
    return render_template("grant_detail.html", grant=grant, active="opportunities")