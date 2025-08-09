import os, pytest
from app import create_app, db
from app.models import Org, CaseSupportDoc, GrantPitchDoc, ImpactReport

@pytest.fixture
def app_ctx():
    os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    os.environ["SQLALCHEMY_TRACK_MODIFICATIONS"] = "false"
    app = create_app()
    with app.app_context():
        db.create_all()
        db.session.add(Org(name="Test Org")); db.session.commit()
        yield app
        db.session.remove(); db.drop_all()

def test_case_export(app_ctx):
    with app_ctx.app_context():
        d = CaseSupportDoc(org_id=1, title="Case", sections={"body":"# Executive Summary\nHello\n\nSource Notes: org_profile"})
        db.session.add(d); db.session.commit()
        client = app_ctx.test_client()
        res = client.get(f"/api/exports/case-support/{d.id}?format=pdf")
        assert res.status_code == 200

def test_pitch_export(app_ctx):
    with app_ctx.app_context():
        d = GrantPitchDoc(org_id=1, funder="Acme", sections={"body":"# Pitch\nHello\n\nSource Notes: fields"})
        db.session.add(d); db.session.commit()
        client = app_ctx.test_client()
        res = client.get(f"/api/exports/grant-pitch/{d.id}?format=docx")
        assert res.status_code == 200

def test_report_export(app_ctx):
    with app_ctx.app_context():
        d = ImpactReport(org_id=1, sections={"body":"# Report\nHello\n\nSource Notes: KPIs"})
        db.session.add(d); db.session.commit()
        client = app_ctx.test_client()
        res = client.get(f"/api/exports/impact-report/{d.id}?format=pdf")
        assert res.status_code == 200