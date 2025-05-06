from app import db
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime

class ScraperSource(db.Model):
    """Model for scraper sources"""
    
    __tablename__ = 'scraper_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    selector_config = db.Column(JSON, default=dict)  # Configuration for CSS selectors or XPath
    is_active = db.Column(db.Boolean, default=True)
    last_scraped = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    grants = db.relationship('Grant', backref='source')
    
    def to_dict(self):
        """Convert scraper source to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'selector_config': self.selector_config,
            'is_active': self.is_active,
            'last_scraped': self.last_scraped.isoformat() if self.last_scraped else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ScraperHistory(db.Model):
    """Model for scraper run history"""
    
    __tablename__ = 'scraper_history'
    
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    sources_scraped = db.Column(db.Integer, default=0)
    grants_found = db.Column(db.Integer, default=0)
    grants_added = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="pending")  # pending, completed, failed
    error_message = db.Column(db.Text)
    
    def to_dict(self):
        """Convert scraper history to dictionary"""
        return {
            'id': self.id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': str((self.end_time - self.start_time)) if self.end_time and self.start_time else None,
            'sources_scraped': self.sources_scraped,
            'grants_found': self.grants_found,
            'grants_added': self.grants_added,
            'status': self.status,
            'error_message': self.error_message
        }
