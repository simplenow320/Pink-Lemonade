from app import db
from app.models import Grant
from sqlalchemy import and_
from datetime import datetime
import logging
from app.services.mode import is_live
from app.services.grant_contact_extractor import get_contact_extractor

log = logging.getLogger(__name__)

def upsert_grant(record: dict, org_id: int | None = None) -> Grant | None:
    """
    record expects keys: title, funder, link, deadline (ISO), amount_min, amount_max, source_name, source_url
    Enhanced to extract contact information automatically
    """
    try:
        # Extract contact information from the grant data
        extractor = get_contact_extractor()
        contact_info = extractor.extract_from_grant(record)
        
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
            
            # Update contact info if better data is available
            if contact_info.get('contact_confidence') in ['medium', 'high']:
                if contact_info.get('contact_name') and not existing.contact_name:
                    existing.contact_name = contact_info['contact_name']
                if contact_info.get('contact_email') and not existing.contact_email:
                    existing.contact_email = contact_info['contact_email']
                if contact_info.get('contact_phone') and not existing.contact_phone:
                    existing.contact_phone = contact_info['contact_phone']
                if contact_info.get('contact_department') and not existing.contact_department:
                    existing.contact_department = contact_info['contact_department']
                if contact_info.get('organization_website') and not existing.organization_website:
                    existing.organization_website = contact_info['organization_website']
                if contact_info.get('application_url') and not existing.application_url:
                    existing.application_url = contact_info['application_url']
                if contact_info.get('alternate_contact'):
                    existing.alternate_contact = contact_info['alternate_contact']
                existing.contact_confidence = contact_info.get('contact_confidence', 'low')
                existing.contact_verified_date = contact_info.get('contact_verified_date')
            
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
            status="idea",
            # Add contact information fields
            contact_name=contact_info.get('contact_name'),
            contact_email=contact_info.get('contact_email'),
            contact_phone=contact_info.get('contact_phone'),
            contact_department=contact_info.get('contact_department'),
            organization_website=contact_info.get('organization_website'),
            application_url=contact_info.get('application_url'),
            alternate_contact=contact_info.get('alternate_contact'),
            contact_confidence=contact_info.get('contact_confidence', 'low'),
            contact_verified_date=contact_info.get('contact_verified_date')
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