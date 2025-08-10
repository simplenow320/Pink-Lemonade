"""
Extended organization model to support profile features while maintaining compatibility
"""

from app import db
from datetime import datetime
import json


class OrgProfile(db.Model):
    """Extended organization profile with all fields needed for AI matching"""
    __tablename__ = "org_profiles"
    
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id"), nullable=False, unique=True)
    
    # Basic info (mirrors Org table)
    name = db.Column(db.String(255))
    mission = db.Column(db.Text)
    
    # Extended profile fields for AI matching
    focus_areas_json = db.Column(db.Text)  # JSON string of list
    keywords_json = db.Column(db.Text)     # JSON string of list
    location = db.Column(db.String(255))
    website = db.Column(db.String(255))
    annual_budget = db.Column(db.String(100))
    ein = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    
    # AI context fields
    program_description = db.Column(db.Text)
    target_population = db.Column(db.Text)
    geographic_scope = db.Column(db.String(255))
    
    # Metadata
    profile_complete = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def focus_areas(self):
        """Get focus areas as list"""
        if self.focus_areas_json:
            try:
                return json.loads(self.focus_areas_json)
            except:
                return []
        return []
    
    @focus_areas.setter
    def focus_areas(self, value):
        """Set focus areas from list"""
        if isinstance(value, list):
            self.focus_areas_json = json.dumps(value)
        else:
            self.focus_areas_json = json.dumps([])
    
    @property
    def keywords(self):
        """Get keywords as list"""
        if self.keywords_json:
            try:
                return json.loads(self.keywords_json)
            except:
                return []
        return []
    
    @keywords.setter
    def keywords(self, value):
        """Set keywords from list"""
        if isinstance(value, list):
            self.keywords_json = json.dumps(value)
        else:
            self.keywords_json = json.dumps([])
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'org_id': self.org_id,
            'name': self.name,
            'mission': self.mission,
            'focus_areas': self.focus_areas,
            'keywords': self.keywords,
            'location': self.location,
            'website': self.website,
            'annual_budget': self.annual_budget,
            'ein': self.ein,
            'phone': self.phone,
            'program_description': self.program_description,
            'target_population': self.target_population,
            'geographic_scope': self.geographic_scope,
            'profile_complete': self.profile_complete,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def calculate_completeness(self):
        """Calculate profile completeness percentage"""
        fields = [
            self.name,
            self.mission,
            self.focus_areas,
            self.keywords,
            self.location
        ]
        completed = sum(1 for field in fields if field)
        return int((completed / len(fields)) * 100)
    
    def get_ai_context_string(self):
        """Generate AI context string for grant matching"""
        parts = []
        
        if self.name:
            parts.append(f"Organization: {self.name}")
        
        if self.mission:
            parts.append(f"Mission: {self.mission}")
        
        if self.focus_areas:
            parts.append(f"Focus Areas: {', '.join(self.focus_areas)}")
        
        if self.keywords:
            parts.append(f"Keywords: {', '.join(self.keywords)}")
        
        if self.location:
            parts.append(f"Location: {self.location}")
        
        if self.target_population:
            parts.append(f"Target Population: {self.target_population}")
        
        if self.program_description:
            parts.append(f"Programs: {self.program_description}")
        
        return '\n'.join(parts)