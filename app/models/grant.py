from app import db
from datetime import datetime

class Grant(db.Model):
    __tablename__ = 'grants'
    
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=True)
    title = db.Column(db.String(500), nullable=False)
    funder = db.Column(db.String(200))
    link = db.Column(db.String(500))
    amount_min = db.Column(db.Integer)
    amount_max = db.Column(db.Integer)
    deadline = db.Column(db.Date)
    geography = db.Column(db.String(200))
    eligibility = db.Column(db.Text)
    source_name = db.Column(db.String(100))
    source_url = db.Column(db.String(500))
    status = db.Column(db.String(50), default='idea')
    match_score = db.Column(db.Integer)
    match_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'title': self.title,
            'funder': self.funder,
            'link': self.link,
            'amount_min': self.amount_min,
            'amount_max': self.amount_max,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'geography': self.geography,
            'eligibility': self.eligibility,
            'source_name': self.source_name,
            'source_url': self.source_url,
            'status': self.status,
            'match_score': self.match_score,
            'match_reason': self.match_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }