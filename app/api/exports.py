from flask import Blueprint, request, abort
from app.models import CaseSupportDoc, GrantPitchDoc, ImpactReport
from app.services.export_service import export_content

bp = Blueprint("exports", __name__)

def _fmt():
    return request.args.get("format","docx").lower()

@bp.get("/case-support/<int:doc_id>")
def export_case(doc_id: int):
    doc = CaseSupportDoc.query.get_or_404(doc_id)
    md = (doc.sections or {}).get("body") or ""
    return export_content(md, _fmt(), doc.title or "Case_for_Support")

@bp.get("/grant-pitch/<int:doc_id>")
def export_pitch(doc_id: int):
    doc = GrantPitchDoc.query.get_or_404(doc_id)
    md = (doc.sections or {}).get("body") or ""
    base = f"Grant_Pitch_{doc.funder or 'Funder'}"
    return export_content(md, _fmt(), base)

@bp.get("/impact-report/<int:doc_id>")
def export_report(doc_id: int):
    doc = ImpactReport.query.get_or_404(doc_id)
    md = (doc.sections or {}).get("body") or ""
    base = "Impact_Report"
    return export_content(md, _fmt(), base)