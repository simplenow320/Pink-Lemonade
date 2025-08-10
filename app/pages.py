from flask import Blueprint, render_template
from app.services.stats_service import get_dashboard_stats, get_top_matches
from app.models import Grant

pages = Blueprint("pages", __name__)

@pages.get("/")
def home():
    return render_template("index.html", active="home")

@pages.get("/dashboard")
def dashboard():
    org_id = 1
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
def opportunities():
    # Use the new opportunities template with full filtering
    return render_template("opportunities_new.html", active="opportunities")

@pages.get("/saved")
def saved():
    return render_template("saved.html", active="saved")

@pages.get("/applications")
def applications():
    return render_template("applications.html", active="apps")

@pages.get("/settings")
def settings():
    return render_template("settings.html", active="settings")

@pages.get("/writing")
def writing():
    return render_template("writing.html", active="writing")



@pages.get("/live-data")
def live_data():
    """Live Data Integration Page"""
    return render_template("live_data.html", active="live")

@pages.get("/journey")
def journey():
    """Interactive Onboarding Journey Page"""
    return render_template("onboarding.html", active="journey")

@pages.get("/profile")
def profile():
    """Organization Profile Management Page"""
    return render_template("profile.html", active="profile")

@pages.get("/case-support")
def case_support():
    """Case for Support Generator Form"""
    return render_template("case_support_form.html", active="writing")

@pages.get("/grant-pitch")
def grant_pitch():
    """Grant Pitch Generator Form"""
    return render_template("grant_pitch_form.html", active="writing")

@pages.get("/admin")
def admin_dashboard():
    """Admin Dashboard Page"""
    return render_template("admin_dashboard.html", active="admin")

@pages.get("/grant/<int:grant_id>")
def grant_detail(grant_id):
    """Grant Detail Page"""
    grant = Grant.query.get_or_404(grant_id)
    return render_template("grant_detail.html", grant=grant, active="opportunities")