from app import db
from app.models import Grant
from sqlalchemy import and_
from datetime import datetime
import logging
from app.services.mode import is_live

log = logging.getLogger(__name__)

def upsert_grant(record: dict, org_id: int | None = None) -> Grant | None:
    """
    record expects keys: title, funder, link, deadline (ISO), amount_min, amount_max, source_name, source_url
    """
    try:
        # normalize deadline
        deadline = None
        if record.get("deadline"):
            deadline = datetime.fromisoformat(record["deadline"]).date()

        # dedupe: title + funder + deadline
        existing = Grant.query.filter(
            and_(Grant.title == record["title"],
                 Grant.funder == record.get("funder"),
                 Grant.deadline == deadline)
        ).first()

        if existing:
            # update minimal fields
            existing.amount_min = record.get("amount_min")
            existing.amount_max = record.get("amount_max")
            existing.source_name = record.get("source_name")
            existing.source_url = record.get("source_url")
            existing.link = record.get("link")
            db.session.commit()
            return existing

        g = Grant(
            org_id=org_id,
            title=record["title"],
            funder=record.get("funder"),
            link=record.get("link"),
            amount_min=record.get("amount_min"),
            amount_max=record.get("amount_max"),
            deadline=deadline,
            geography=record.get("geography"),
            eligibility=record.get("eligibility"),
            source_name=record.get("source_name"),
            source_url=record.get("source_url"),
            status="idea"
        )
        db.session.add(g)
        db.session.commit()
        return g
    except Exception as e:
        db.session.rollback()
        log.exception("Grant save failed", extra={"record": record})
        return None

def scheduled_scraping_job():
    if not is_live():
        log.info("Skipping scheduled scraping in DEMO mode.")
        return
    # call your live connectors here, do not generate random data in LIVE