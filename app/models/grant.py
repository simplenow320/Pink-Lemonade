from app import db
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime
import logging

# Set up logger
logger = logging.getLogger(__name__)

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
    date_submitted = db.Column(db.Date)  # When the grant was submitted
    date_decision = db.Column(db.Date)  # When a decision was received
    search_query = db.Column(db.String(255))  # The search query that found this grant
    discovery_method = db.Column(db.String(50))  # web-search, focused-search, manual
    
    # Relationships
    narrative = db.relationship('Narrative', back_populates='grant', uselist=False, cascade="all, delete-orphan")
    # Analytics relationship defined in analytics.py to avoid circular imports
    
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
            'has_narrative': self.narrative is not None,
            'date_submitted': self.date_submitted.isoformat() if self.date_submitted else None,
            'date_decision': self.date_decision.isoformat() if self.date_decision else None
        }
    
    def update_status(self, new_status, metadata=None):
        """
        Update grant status and record the change for analytics
        
        Args:
            new_status (str): New status value
            metadata (dict, optional): Additional metadata
            
        Returns:
            bool: Success of the operation
        """
        try:
            # Import here to avoid circular imports
            from app.services.analytics_service import record_status_change
            
            # Store the previous status
            previous_status = self.status
            
            # Update the status
            self.status = new_status
            
            # Update submission and decision dates if applicable
            if new_status == "Submitted" and not self.date_submitted:
                self.date_submitted = datetime.now().date()
            
            if new_status in ["Won", "Declined"] and not self.date_decision:
                self.date_decision = datetime.now().date()
            
            # Record status change for analytics
            result = record_status_change(
                self.id, 
                new_status, 
                previous_status,
                metadata
            )
            
            return result["success"]
            
        except Exception as e:
            logger.error(f"Error updating grant status: {str(e)}")
            return False
