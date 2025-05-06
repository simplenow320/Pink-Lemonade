from app import db
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime

class Grant(db.Model):
    """Model for grant opportunities"""
    
    __tablename__ = 'grants'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    funder = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float)
    due_date = db.Column(db.Date)
    eligibility = db.Column(db.Text)
    website = db.Column(db.String(255))
    status = db.Column(db.String(50), default="Not Started")  # Not Started, In Progress, Submitted, Won, Declined
    match_score = db.Column(db.Float, default=0)  # 0-100 matching score
    match_explanation = db.Column(db.Text)
    notes = db.Column(db.Text)
    focus_areas = db.Column(JSON, default=list)
    contact_info = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_scraped = db.Column(db.Boolean, default=False)
    source_id = db.Column(db.Integer, db.ForeignKey('scraper_sources.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    narrative = db.relationship('Narrative', back_populates='grant', uselist=False, cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert grant to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'funder': self.funder,
            'description': self.description,
            'amount': self.amount,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'eligibility': self.eligibility,
            'website': self.website,
            'status': self.status,
            'match_score': self.match_score,
            'match_explanation': self.match_explanation,
            'notes': self.notes,
            'focus_areas': self.focus_areas,
            'contact_info': self.contact_info,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_scraped': self.is_scraped,
            'source_id': self.source_id,
            'has_narrative': self.narrative is not None
        }
