from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
from app import db
from app.models import CaseSupportDoc, GrantPitchDoc, ImpactReport
from app.services.ai_prompter import run_prompt
from app.services.ai_data_reader import build_data_pack

bp = Blueprint("writing", __name__)

def _json():
    data = request.get_json(silent=True)
    if not data:
        raise BadRequest("JSON body required")
    return data

@bp.post("/case-support")
def create_case_support():
    body = _json()
    org_id = int(body.get("orgId") or 1)
    tokens = {
        "org_name": body.get("orgName") or "Your Organization",
        "audience_type": body.get("audience") or "individual and foundation donors",
        "word_count_range": body.get("length") or "600-900"
    }
    data_pack = build_data_pack(org_id)
    result = run_prompt("case_support", tokens, data_pack)
    content = result["content"]
    needs = _extract_missing(content)
    doc = CaseSupportDoc(org_id=org_id, title=body.get("title") or "Case for Support", sections={"body": content}, needs_input=needs, sources={})
    db.session.add(doc); db.session.commit()
    return jsonify({"id": doc.id, "needsInput": needs, "content": content}), 200

@bp.post("/grant-pitch")
def create_grant_pitch():
    body = _json()
    org_id = int(body.get("orgId") or 1)
    tokens = {
        "org_name": body.get("orgName") or "Your Organization",
        "funder_name": body.get("funder") or "Target Funder",
        "alignment_points": body.get("alignment") or "youth, AI literacy, community impact",
        "per_section_word_limits": body.get("limits") or "120"
    }
    data_pack = build_data_pack(org_id)
    result = run_prompt("grant_pitch", tokens, data_pack)
    content = result["content"]
    needs = _extract_missing(content)
    doc = GrantPitchDoc(org_id=org_id, funder=tokens["funder_name"], sections={"body": content}, needs_input=needs, sources={})
    db.session.add(doc); db.session.commit()
    return jsonify({"id": doc.id, "needsInput": needs, "content": content}), 200

@bp.post("/impact-report")
def create_impact_report():
    body = _json()
    org_id = int(body.get("orgId") or 1)
    tokens = {
        "org_name": body.get("orgName") or "Your Organization",
        "template_sections": body.get("templateSections") or "Grant Summary; Objectives & Activities; Outputs; Outcomes; Financial Report; Challenges & Learnings; Next Steps",
        "start_date": body.get("startDate") or "2025-01-01",
        "end_date": body.get("endDate") or "2025-06-30"
    }
    data_pack = build_data_pack(org_id)
    result = run_prompt("impact_report", tokens, data_pack)
    content = result["content"]
    needs = _extract_missing(content)
    doc = ImpactReport(org_id=org_id, grant_id=body.get("grantId"), period_start=None, period_end=None, sections={"body": content}, needs_update=needs, sources={})
    db.session.add(doc); db.session.commit()
    return jsonify({"id": doc.id, "needsUpdate": needs, "content": content}), 200

def _extract_missing(text: str):
    # If the model followed our prompts, it lists "Missing Info" or "Needs Update" when data is absent.
    import re
    m = re.search(r"(?i)(Missing Info|Needs Update)\s*:\s*(.+)$", text, re.DOTALL)
    if not m:
        return []
    section = m.group(2).strip()
    items = [ln.strip("-• ").strip() for ln in section.splitlines() if ln.strip()]
    return items[:20]