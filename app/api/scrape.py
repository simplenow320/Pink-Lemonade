# app/api/scrape.py
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
from app.services.scraper_service import run_now_for_org

bp = Blueprint("scrape", __name__)

@bp.post("/run-now")
def run_now():
    """
    Body:
      { "orgId": 1, "query": "youth" }  // query optional
    Returns:
      { "orgId": 1, "query": "youth", "upserted": 12, "mode": "LIVE" }
    """
    data = request.get_json(silent=True) or {}
    org_id = data.get("orgId")
    if not org_id:
        raise BadRequest("orgId is required")
    query = data.get("query")

    upserted = run_now_for_org(org_id=int(org_id), query=query)
    # Reflect current mode for front end badge or logs
    from app.services.mode import is_live
    mode = "LIVE" if is_live() else "DEMO"
    return jsonify({"orgId": org_id, "query": query, "upserted": upserted, "mode": mode}), 200