from datetime import date
from calendar import monthrange
from sqlalchemy import func
from app import db
from app.models import Grant

def month_bounds(dt: date):
    start = dt.replace(day=1)
    end = dt.replace(day=monthrange(dt.year, dt.month)[1])
    return start, end

def get_dashboard_stats(org_id: int):
    total = db.session.query(func.count(Grant.id)).filter(
        (Grant.org_id == org_id) | (Grant.org_id.is_(None))
    ).scalar() or 0
    today = date.today()
    start, end = month_bounds(today)
    due_this_month = db.session.query(func.count(Grant.id)).filter(
        ((Grant.org_id == org_id) | (Grant.org_id.is_(None))),
        Grant.deadline.isnot(None),
        Grant.deadline >= start,
        Grant.deadline <= end
    ).scalar() or 0
    avg_fit = None
    if hasattr(Grant, "match_score"):
        avg_fit = db.session.query(func.avg(Grant.match_score)).filter(
            (Grant.org_id == org_id) | (Grant.org_id.is_(None))
        ).scalar()
        if avg_fit is not None:
            avg_fit = round(float(avg_fit), 1)
    submitted = db.session.query(func.count(Grant.id)).filter(
        ((Grant.org_id == org_id) | (Grant.org_id.is_(None))),
        Grant.status == "submitted"
    ).scalar() or 0
    return {"total": int(total), "due_this_month": int(due_this_month), "avg_fit": avg_fit, "submitted": int(submitted)}

def get_top_matches(org_id: int, limit: int = 5):
    q = db.session.query(Grant).filter(
        (Grant.org_id == org_id) | (Grant.org_id.is_(None))
    )
    if hasattr(Grant, "match_score"):
        q = q.order_by(Grant.match_score.desc().nullslast())
    else:
        q = q.order_by(Grant.created_at.desc())
    return q.limit(limit).all()