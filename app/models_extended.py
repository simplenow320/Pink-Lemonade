"""
Extended organization model to support profile features while maintaining compatibility
Smart Reporting models for Phase 1 implementation
"""

from app import db
from datetime import datetime, date
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Index
import json


class OrgProfile(db.Model):
    """Extended organization profile with all fields needed for AI matching"""
    __tablename__ = "org_profiles"
    
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False, unique=True)
    
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


# =============================================================================
# Smart Reporting System Models - Phase 1 Foundation
# =============================================================================

class Project(db.Model):
    """Project model for grant-linked impact measurement"""
    __tablename__ = "projects"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Grant relationships - using existing table names
    grant_id = db.Column(db.Integer, db.ForeignKey("grants.id"), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    
    # Project timeline
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Project management
    project_owner = db.Column(db.String(100))
    status = db.Column(db.String(50), default="active")
    
    # Impact metrics
    target_participants = db.Column(db.Integer)
    target_outcome = db.Column(db.Text)
    budget_allocated = db.Column(db.Numeric(12, 2))
    
    # AI integration metadata
    ai_analysis_version = db.Column(db.String(50), default="1.0")
    impact_framework_generated = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "grant_id": self.grant_id,
            "organization_id": self.organization_id,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "project_owner": self.project_owner,
            "status": self.status,
            "target_participants": self.target_participants,
            "target_outcome": self.target_outcome,
            "budget_allocated": float(self.budget_allocated) if self.budget_allocated else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ReportingSchedule(db.Model):
    """Reporting schedule and deadline management"""
    __tablename__ = "reporting_schedules"
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    
    # Schedule details
    report_type = db.Column(db.String(100), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    submission_date = db.Column(db.Date)
    
    # Requirements
    deliverable_type = db.Column(db.String(100))
    funder_requirements = db.Column(db.Text)
    
    # Status tracking
    status = db.Column(db.String(50), default="pending")
    completion_percentage = db.Column(db.Integer, default=0)
    
    # AI assistance
    ai_suggestions_generated = db.Column(db.Boolean, default=False)
    auto_report_available = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "report_type": self.report_type,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "submission_date": self.submission_date.isoformat() if self.submission_date else None,
            "deliverable_type": self.deliverable_type,
            "funder_requirements": self.funder_requirements,
            "status": self.status,
            "completion_percentage": self.completion_percentage,
            "ai_suggestions_generated": self.ai_suggestions_generated,
            "auto_report_available": self.auto_report_available
        }


class ImpactQuestion(db.Model):
    """AI-generated and customized impact measurement questions"""
    __tablename__ = "impact_questions"
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    
    # Question details
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(100))
    
    # AI generation metadata
    ai_generated = db.Column(db.Boolean, default=True)
    ai_confidence_score = db.Column(db.Float)
    ai_reasoning = db.Column(db.Text)
    
    # Question configuration
    required = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=1)
    response_format = db.Column(db.String(50))
    options = db.Column(db.Text)  # JSON string for compatibility
    
    # Status
    approved = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    
    # Cross-tool learning integration
    learning_tags = db.Column(db.Text)  # JSON string for compatibility
    success_metrics = db.Column(db.Text)  # JSON string for compatibility
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "question_text": self.question_text,
            "question_type": self.question_type,
            "category": self.category,
            "ai_generated": self.ai_generated,
            "ai_confidence_score": self.ai_confidence_score,
            "ai_reasoning": self.ai_reasoning,
            "required": self.required,
            "display_order": self.display_order,
            "response_format": self.response_format,
            "options": json.loads(self.options) if self.options else None,
            "approved": self.approved,
            "active": self.active,
            "learning_tags": json.loads(self.learning_tags) if self.learning_tags else None,
            "success_metrics": json.loads(self.success_metrics) if self.success_metrics else None
        }


class SurveyResponse(db.Model):
    """Survey responses for impact measurement"""
    __tablename__ = "survey_responses"
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("impact_questions.id"), nullable=False)
    
    # Response data
    response_text = db.Column(db.Text)
    response_number = db.Column(db.Float)
    response_json = db.Column(db.Text)  # JSON string for compatibility
    
    # Respondent information
    respondent_type = db.Column(db.String(50))
    respondent_id = db.Column(db.String(100))
    respondent_metadata = db.Column(db.Text)  # JSON string for compatibility
    
    # Collection metadata
    collection_method = db.Column(db.String(50), default="web_survey")
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # Data quality
    validated = db.Column(db.Boolean, default=False)
    validation_notes = db.Column(db.Text)
    flagged_for_review = db.Column(db.Boolean, default=False)
    
    # AI analysis
    ai_sentiment_score = db.Column(db.Float)
    ai_insights = db.Column(db.Text)  # JSON string for compatibility
    ai_categorization = db.Column(db.Text)  # JSON string for compatibility
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "question_id": self.question_id,
            "response_text": self.response_text,
            "response_number": self.response_number,
            "response_json": json.loads(self.response_json) if self.response_json else None,
            "respondent_type": self.respondent_type,
            "respondent_id": self.respondent_id,
            "respondent_metadata": json.loads(self.respondent_metadata) if self.respondent_metadata else None,
            "collection_method": self.collection_method,
            "validated": self.validated,
            "validation_notes": self.validation_notes,
            "ai_sentiment_score": self.ai_sentiment_score,
            "ai_insights": json.loads(self.ai_insights) if self.ai_insights else None,
            "ai_categorization": json.loads(self.ai_categorization) if self.ai_categorization else None,
            "submitted_at": self.submitted_at.isoformat(),
            "validated_at": self.validated_at.isoformat() if self.validated_at else None
        }


class ImpactReport(db.Model):
    """Generated impact reports and documents"""
    __tablename__ = "smart_impact_reports"
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    reporting_schedule_id = db.Column(db.Integer, db.ForeignKey("reporting_schedules.id"))
    
    # Report details
    report_type = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    
    # Generation metadata
    ai_generated = db.Column(db.Boolean, default=True)
    generation_version = db.Column(db.String(50), default="1.0")
    data_sources = db.Column(db.Text)  # JSON string for compatibility
    
    # File management
    file_path = db.Column(db.String(500))
    file_format = db.Column(db.String(20))
    file_size = db.Column(db.Integer)
    
    # Status and approval
    status = db.Column(db.String(50), default="draft")
    approved_by = db.Column(db.String(100))
    approval_date = db.Column(db.DateTime)
    
    # Cross-tool learning
    report_effectiveness = db.Column(db.Float)
    funder_feedback = db.Column(db.Text)
    learning_insights = db.Column(db.Text)  # JSON string for compatibility
    
    # Timestamps
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "reporting_schedule_id": self.reporting_schedule_id,
            "report_type": self.report_type,
            "title": self.title,
            "content": self.content,
            "ai_generated": self.ai_generated,
            "generation_version": self.generation_version,
            "data_sources": json.loads(self.data_sources) if self.data_sources else None,
            "file_path": self.file_path,
            "file_format": self.file_format,
            "file_size": self.file_size,
            "status": self.status,
            "approved_by": self.approved_by,
            "approval_date": self.approval_date.isoformat() if self.approval_date else None,
            "report_effectiveness": self.report_effectiveness,
            "funder_feedback": self.funder_feedback,
            "learning_insights": json.loads(self.learning_insights) if self.learning_insights else None,
            "generated_at": self.generated_at.isoformat(),
            "last_modified": self.last_modified.isoformat()
        }

