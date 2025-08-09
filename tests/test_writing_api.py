import json, os, pytest
from app import create_app, db
from app.models import Org

@pytest.fixture
def app_ctx():
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY","sk-test")  # model will be mocked by OpenAI lib or fail gracefully
    os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    os.environ["SQLALCHEMY_TRACK_MODIFICATIONS"] = "false"
    app = create_app()
    with app.app_context():
        db.create_all()
        db.session.add(Org(name="Test Org")); db.session.commit()
        yield app
        db.session.remove(); db.drop_all()

def test_case_support_route(app_ctx, monkeypatch):
    # Monkeypatch run_prompt to avoid a real model call
    from app.api import writing as w
    monkeypatch.setattr(w, "run_prompt", lambda name, tokens, pack: {"content":"Executive Summary\\n...\\nSource Notes: org_profile", "model":"mock"})
    client = app_ctx.test_client()
    r = client.post("/api/writing/case-support", data=json.dumps({"orgId":1}), content_type="application/json")
    assert r.status_code == 200
    assert "content" in r.get_json()

def test_grant_pitch_route(app_ctx, monkeypatch):
    from app.api import writing as w
    monkeypatch.setattr(w, "run_prompt", lambda name, tokens, pack: {"content":"Personal Impact\\n...\\nSource Notes: fields", "model":"mock"})
    client = app_ctx.test_client()
    r = client.post("/api/writing/grant-pitch", data=json.dumps({"orgId":1}), content_type="application/json")
    assert r.status_code == 200

def test_impact_report_route(app_ctx, monkeypatch):
    from app.api import writing as w
    monkeypatch.setattr(w, "run_prompt", lambda name, tokens, pack: {"content":"Grant Summary\\n...\\nSource Notes: KPIs", "model":"mock"})
    client = app_ctx.test_client()
    r = client.post("/api/writing/impact-report", data=json.dumps({"orgId":1}), content_type="application/json")
    assert r.status_code == 200