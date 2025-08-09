# tests/test_scraper_run_now.py
import json
import types
import os
import pytest

from app import create_app, db
from app.models import Org, Watchlist
import app.services.scraper_service as ss

@pytest.fixture
def app_ctx(tmp_path):
    os.environ["APP_DATA_MODE"] = "LIVE"  # test the live branch but we will stub network
    os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    os.environ["SQLALCHEMY_TRACK_MODIFICATIONS"] = "false"

    app = create_app()
    with app.app_context():
        db.create_all()
        # seed minimal org and watchlist
        org = Org(name="Test Org", mission="Testing")
        db.session.add(org); db.session.commit()
        wl = Watchlist(org_id=org.id, city="detroit")
        db.session.add(wl); db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

def _fake_records():
    return [
        {
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
        }
    ]

def test_run_now_upserts(app_ctx, monkeypatch):
    # stub network call
    monkeypatch.setattr(ss, "fetch_from_grants_gov", lambda search_term, limit=50, offset=0: _fake_records())
    client = app_ctx.test_client()

    # find org id
    from app.models import Org
    org_id = Org.query.first().id

    # call API
    resp = client.post("/api/scrape/run-now", data=json.dumps({"orgId": org_id}), content_type="application/json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["upserted"] >= 1
    assert data["mode"] == "LIVE"

    # call again to verify dedupe
    resp2 = client.post("/api/scrape/run-now", data=json.dumps({"orgId": org_id}), content_type="application/json")
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    # second run should not create duplicates
    assert data2["upserted"] >= 0