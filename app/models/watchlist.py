"""
Watchlist model for saved searches and alerts
"""

from app import db
from datetime import datetime

class Watchlist(db.Model):
    """Model for saved searches and alert preferences"""
    
    __tablename__ = 'watchlist'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'search' or 'alert'
    criteria = db.Column(db.JSON, nullable=True)  # Search criteria or alert conditions
    notify_email = db.Column(db.Boolean, default=True)
    notify_app = db.Column(db.Boolean, default=True)
    frequency = db.Column(db.String(50), default='daily')  # daily, weekly, immediate
    is_active = db.Column(db.Boolean, default=True)
    last_checked = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'type': self.type,
            'criteria': self.criteria,
            'notify_email': self.notify_email,
            'notify_app': self.notify_app,
            'frequency': self.frequency,
            'is_active': self.is_active,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }