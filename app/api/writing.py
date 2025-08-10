from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
from app import db
from app.models import CaseSupportDoc, GrantPitchDoc, ImpactReport
import logging
import os

logger = logging.getLogger(__name__)

bp = Blueprint("writing", __name__)

@bp.route('/improve', methods=['POST'])
def improve_text():
    """Improve text using AI"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        improvement_type = data.get('improvement_type', 'professional')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Use OpenAI for text improvement
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Define improvement prompts
        prompts = {
            'professional': 'Make this text more professional and polished while keeping the original meaning:',
            'clarity': 'Improve the clarity and readability of this text:',
            'concise': 'Make this text more concise while preserving all key information:',
            'expand': 'Expand on this text with more detail and examples:',
            'persuasive': 'Make this text more persuasive and compelling:'
        }
        
        prompt = prompts.get(improvement_type, prompts['professional'])
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional writing assistant helping with grant applications."},
                {"role": "user", "content": f"{prompt}\n\n{text}"}
            ],
            max_tokens=1000
        )
        
        improved_text = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'improved_text': improved_text,
            'improvement_type': improvement_type
        })
        
    except Exception as e:
        logger.error(f"Error improving text: {e}")
        return jsonify({'error': str(e)}), 500

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