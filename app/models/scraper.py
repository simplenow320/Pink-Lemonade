from app import db
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime

class ScraperSource(db.Model):
    """Model for scraper sources"""
    
    __tablename__ = 'scraper_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    contact_email = db.Column(db.String(100))
    contact_name = db.Column(db.String(100))
    match_score = db.Column(db.Integer, default=0)  # 1-5 score indicating match quality
    best_fit_initiatives = db.Column(JSON, default=list)  # List of initiative names
    grant_programs = db.Column(JSON, default=list)  # List of grant program names
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
            'location': self.location,
            'phone': self.phone,
            'contact_email': self.contact_email,
            'contact_name': self.contact_name,
            'match_score': self.match_score,
            'best_fit_initiatives': self.best_fit_initiatives,
            'grant_programs': self.grant_programs,
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
    status = db.Column(db.String(50), default="pending")  # pending, in_progress, completed, completed_with_errors, failed
    error_message = db.Column(db.Text)
    
    # Search reporting columns
    sites_searched_estimate = db.Column(db.Integer, default=0)
    total_queries_attempted = db.Column(db.Integer, default=0)
    successful_queries = db.Column(db.Integer, default=0)
    search_keywords_used = db.Column(JSON, default=list)
    
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
            'error_message': self.error_message,
            # Add direct properties for dashboard compatibility
            'sites_searched': self.sites_searched_estimate,
            'queries_attempted': self.total_queries_attempted,
            'successful_queries': self.successful_queries,
            'search_report': {
                'sites_searched': self.sites_searched_estimate,
                'queries_attempted': self.total_queries_attempted,
                'successful_queries': self.successful_queries,
                'search_keywords_used': self.search_keywords_used,
                'success_rate': f"{(self.successful_queries / self.total_queries_attempted * 100):.1f}%" if self.total_queries_attempted > 0 else "0%"
            }
        }
