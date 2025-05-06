from app import db
from sqlalchemy.dialects.sqlite import JSON

class Organization(db.Model):
    """Model for organization profile"""
    
    __tablename__ = 'organization'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    mission = db.Column(db.Text)
    website = db.Column(db.String(255))
    location = db.Column(JSON, default=dict)  # City, State, Zip
    founding_year = db.Column(db.Integer)
    team = db.Column(JSON, default=list)  # List of team members with their roles
    focus_areas = db.Column(JSON, default=list)  # List of focus areas
    keywords = db.Column(JSON, default=list)  # List of keywords for grant matching
    past_programs = db.Column(JSON, default=list)  # List of past programs with details
    financials = db.Column(JSON, default=dict)  # Financial information
    case_for_support = db.Column(db.Text)  # Rich text content for case for support
    
    def to_dict(self):
        """Convert organization to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'mission': self.mission,
            'website': self.website,
            'location': self.location,
            'founding_year': self.founding_year,
            'team': self.team,
            'focus_areas': self.focus_areas,
            'keywords': self.keywords,
            'past_programs': self.past_programs,
            'financials': self.financials,
            'case_for_support': self.case_for_support
        }
