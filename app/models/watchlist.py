"""
Watchlist model for monitoring grant sources by city
"""

from datetime import datetime
from app import db


class Watchlist(db.Model):
    """Watchlist model for monitoring grant sources"""
    __tablename__ = 'watchlists'
    
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    sources = db.Column(db.JSON, default=list)  # List of connector IDs
    enabled = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert watchlist to dictionary"""
        return {
            'id': self.id,
            'orgId': self.org_id,
            'city': self.city,
            'sources': self.sources or [],
            'enabled': self.enabled,
            'lastRun': self.last_run.isoformat() if self.last_run else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_default_watchlists(cls, org_id: str):
        """Create default watchlists for major cities"""
        cities_and_sources = {
            'Grand Rapids': [
                'gr_foundation_1',
                'gr_foundation_2',
                'gr_foundation_3',
                'gr_foundation_4',
                'gr_foundation_5'
            ],
            'Charlotte': [
                'grants_gov',
                'federal_register'
            ],
            'Atlanta': [
                'grants_gov',
                'federal_register'
            ],
            'Detroit': [
                'grants_gov',
                'federal_register'
            ],
            'Indiana': [
                'grants_gov',
                'federal_register',
                'philanthropy_news'
            ]
        }
        
        watchlists = []
        for city, sources in cities_and_sources.items():
            watchlist = cls(
                org_id=org_id,
                city=city,
                sources=sources,
                enabled=True
            )
            watchlists.append(watchlist)
        
        return watchlists