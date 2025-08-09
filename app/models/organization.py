from app import db
from datetime import datetime

class Organization(db.Model):
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    mission = db.Column(db.Text)
    focus_areas = db.Column(db.Text)
    keywords = db.Column(db.Text)
    location = db.Column(db.String(200))
    annual_budget = db.Column(db.Integer)
    ein = db.Column(db.String(20))
    documents = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mission': self.mission,
            'focus_areas': self.focus_areas,
            'keywords': self.keywords,
            'location': self.location,
            'annual_budget': self.annual_budget,
            'ein': self.ein,
            'documents': self.documents,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }