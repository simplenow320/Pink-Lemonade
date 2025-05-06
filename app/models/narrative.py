from app import db
from datetime import datetime

class Narrative(db.Model):
    """Model for grant narratives"""
    
    __tablename__ = 'narratives'
    
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_updated = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    grant = db.relationship('Grant', back_populates='narrative')
    
    def to_dict(self):
        """Convert narrative to dictionary"""
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
