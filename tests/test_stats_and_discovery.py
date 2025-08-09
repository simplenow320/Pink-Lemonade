import json, os
from datetime import date, timedelta
import pytest
from app import create_app, db
from app.models import Org, Grant
import app.services.scraper_service as ss

@pytest.fixture
def app_ctx(tmp_path):
    os.environ["APP_DATA_MODE"] = "LIVE"
    os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    os.environ["SQLALCHEMY_TRACK_MODIFICATIONS"] = "false"
    app = create_app()
    with app.app_context():
        db.create_all()
        org = Org(name="Test Org"); db.session.add(org); db.session.commit()
        g1 = Grant(org_id=org.id, title="A", funder="X", deadline=date.today()+timedelta(days=5))
        g2 = Grant(org_id=org.id, title="B", funder="Y", status="submitted")
        g3 = Grant(org_id=org.id, title="C", funder="Z")
        db.session.add_all([g1,g2,g3]); db.session.commit()
        yield app
        db.session.remove(); db.drop_all()

def test_dashboard_stats(app_ctx):
    from app.services.stats_service import get_dashboard_stats
    with app_ctx.app_context():
        stats = get_dashboard_stats(1)
        assert stats["total"] == 3
        assert stats["submitted"] == 1
        assert isinstance(stats["due_this_month"], int)

def test_discover_endpoint_runs(app_ctx, monkeypatch):
    monkeypatch.setattr(ss, "fetch_from_grants_gov", lambda search_term, limit=50, offset=0: [{
        "title": "Community Tech Access",
        "funder": "US Dept of Education",
        "link": "https://example.org/opportunity/1",
        "amount_min": 50000,
        "amount_max": 150000,
        "deadline": "2025-12-31",
        "geography": "US",
        "eligibility": "Nonprofits",
        "source_name": "Grants.gov",
        "source_url": "https://www.grants.gov"
    }])
    client = app_ctx.test_client()
    r = client.post("/api/scrape/run-now", data=json.dumps({"orgId":1}), content_type="application/json")
    assert r.status_code == 200
    data = r.get_json()
    assert "upserted" in data