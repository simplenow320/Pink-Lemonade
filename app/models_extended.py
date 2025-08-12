"""
Extended organization model to support profile features while maintaining compatibility
Smart Reporting models for Phase 1 implementation
"""

from app import db
from datetime import datetime, date, timedelta
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Index
import json
import secrets


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



# =============================================================================
# Smart Reporting Phase 3 Models - Data Collection & Validation Automation
# =============================================================================

class DataCollectionWorkflow(db.Model):
    """Automated data collection workflow management"""
    __tablename__ = "data_collection_workflows"
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    workflow_type = db.Column(db.String(100), nullable=False)
    trigger_conditions = db.Column(db.Text)
    stakeholder_targets = db.Column(db.Text)
    distribution_channels = db.Column(db.Text)
    collection_window_days = db.Column(db.Integer, default=14)
    mobile_optimized = db.Column(db.Boolean, default=True)
    offline_capable = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(50), default="draft")
    automation_enabled = db.Column(db.Boolean, default=False)
    target_response_rate = db.Column(db.Float)
    actual_response_rate = db.Column(db.Float)
    quality_threshold = db.Column(db.Float, default=7.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    activated_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "automation_enabled": self.automation_enabled,
            "mobile_optimized": self.mobile_optimized,
            "offline_capable": self.offline_capable,
            "target_response_rate": self.target_response_rate,
            "actual_response_rate": self.actual_response_rate
        }


class ValidationRule(db.Model):
    """Configurable validation criteria and business rules"""
    __tablename__ = "validation_rules"
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    question_id = db.Column(db.Integer, db.ForeignKey("impact_questions.id"))
    rule_name = db.Column(db.String(200), nullable=False)
    rule_type = db.Column(db.String(50), nullable=False)
    validation_criteria = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(50), default="error")
    auto_fix_enabled = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text)
    help_text = db.Column(db.Text)
    rule_enabled = db.Column(db.Boolean, default=True)
    times_triggered = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "rule_type": self.rule_type,
            "severity": self.severity,
            "rule_enabled": self.rule_enabled,
            "success_rate": self.success_rate
        }


class ResponseValidation(db.Model):
    """Real-time validation results and quality metrics"""
    __tablename__ = "response_validations"
    
    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer, db.ForeignKey("survey_responses.id"), nullable=False)
    validation_rule_id = db.Column(db.Integer, db.ForeignKey("validation_rules.id"))
    validation_status = db.Column(db.String(50), nullable=False)
    quality_score = db.Column(db.Float)
    completeness_score = db.Column(db.Float)
    issues_found = db.Column(db.Text)
    auto_corrections = db.Column(db.Text)
    manual_review_required = db.Column(db.Boolean, default=False)
    response_time_seconds = db.Column(db.Float)
    device_type = db.Column(db.String(50))
    connection_quality = db.Column(db.String(50))
    authenticity_score = db.Column(db.Float)
    validated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "response_id": self.response_id,
            "validation_status": self.validation_status,
            "quality_score": self.quality_score,
            "completeness_score": self.completeness_score,
            "manual_review_required": self.manual_review_required,
            "authenticity_score": self.authenticity_score
        }


class DataCleansingLog(db.Model):
    """Audit trail of automated data corrections"""
    __tablename__ = "data_cleansing_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer, db.ForeignKey("survey_responses.id"), nullable=False)
    operation_type = db.Column(db.String(100), nullable=False)
    field_name = db.Column(db.String(200))
    original_value = db.Column(db.Text)
    corrected_value = db.Column(db.Text)
    correction_method = db.Column(db.String(100))
    confidence_score = db.Column(db.Float)
    correction_reasoning = db.Column(db.Text)
    auto_applied = db.Column(db.Boolean, default=False)
    requires_review = db.Column(db.Boolean, default=False)
    review_status = db.Column(db.String(50))
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "response_id": self.response_id,
            "operation_type": self.operation_type,
            "correction_method": self.correction_method,
            "confidence_score": self.confidence_score,
            "auto_applied": self.auto_applied,
            "review_status": self.review_status
        }


# =============================================================================
# Smart Reporting Phase 4 Models - Dashboard & Analytics Integration
# =============================================================================

class DashboardConfig(db.Model):
    """User-customizable dashboard configurations"""
    __tablename__ = "dashboard_configs"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50))
    dashboard_name = db.Column(db.String(200), nullable=False)
    dashboard_type = db.Column(db.String(50), default="executive")
    layout_config = db.Column(db.Text)
    active_widgets = db.Column(db.Text)
    refresh_interval = db.Column(db.Integer, default=300)
    data_range_days = db.Column(db.Integer, default=30)
    is_default = db.Column(db.Boolean, default=False)
    is_shared = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "dashboard_name": self.dashboard_name,
            "dashboard_type": self.dashboard_type,
            "refresh_interval": self.refresh_interval,
            "data_range_days": self.data_range_days,
            "is_default": self.is_default
        }


class AnalyticsSnapshot(db.Model):
    """Point-in-time analytics data storage"""
    __tablename__ = "analytics_snapshots"
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    snapshot_type = db.Column(db.String(50), nullable=False)
    snapshot_date = db.Column(db.DateTime, nullable=False)
    response_rate = db.Column(db.Float)
    completion_rate = db.Column(db.Float)
    quality_score = db.Column(db.Float)
    engagement_score = db.Column(db.Float)
    participants_reached = db.Column(db.Integer)
    satisfaction_rating = db.Column(db.Float)
    impact_score = db.Column(db.Float)
    surveys_distributed = db.Column(db.Integer, default=0)
    surveys_completed = db.Column(db.Integer, default=0)
    validation_pass_rate = db.Column(db.Float)
    data_quality_score = db.Column(db.Float)
    detailed_metrics = db.Column(db.Text)
    trend_indicators = db.Column(db.Text)
    predictive_insights = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "snapshot_type": self.snapshot_type,
            "response_rate": self.response_rate,
            "completion_rate": self.completion_rate,
            "quality_score": self.quality_score,
            "satisfaction_rating": self.satisfaction_rating,
            "impact_score": self.impact_score
        }


class PredictiveModel(db.Model):
    """AI model configurations and performance tracking"""
    __tablename__ = "predictive_models"
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(200), nullable=False)
    model_type = db.Column(db.String(100), nullable=False)
    target_variable = db.Column(db.String(100))
    algorithm_type = db.Column(db.String(100))
    accuracy_score = db.Column(db.Float)
    model_status = db.Column(db.String(50), default="training")
    prediction_count = db.Column(db.Integer, default=0)
    average_confidence = db.Column(db.Float)
    model_version = db.Column(db.String(50))
    last_training_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "model_name": self.model_name,
            "model_type": self.model_type,
            "accuracy_score": self.accuracy_score,
            "model_status": self.model_status,
            "prediction_count": self.prediction_count,
            "average_confidence": self.average_confidence
        }


class DataVisualization(db.Model):
    """Chart and visualization definitions"""
    __tablename__ = "data_visualizations"
    
    id = db.Column(db.Integer, primary_key=True)
    dashboard_config_id = db.Column(db.Integer, db.ForeignKey("dashboard_configs.id"))
    viz_name = db.Column(db.String(200), nullable=False)
    viz_type = db.Column(db.String(50), nullable=False)
    data_source = db.Column(db.String(100))
    chart_config = db.Column(db.Text, nullable=False)
    position_x = db.Column(db.Integer, default=0)
    position_y = db.Column(db.Integer, default=0)
    width = db.Column(db.Integer, default=6)
    height = db.Column(db.Integer, default=4)
    auto_refresh = db.Column(db.Boolean, default=True)
    refresh_interval_seconds = db.Column(db.Integer, default=300)
    is_interactive = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "viz_name": self.viz_name,
            "viz_type": self.viz_type,
            "data_source": self.data_source,
            "width": self.width,
            "height": self.height,
            "auto_refresh": self.auto_refresh,
            "is_interactive": self.is_interactive
        }


# =============================================================================
# Smart Reporting Phase 5 Models - Automated Report Generation
# =============================================================================

class ReportTemplate(db.Model):
    """Professional report layouts and section definitions"""
    __tablename__ = "report_templates"
    
    id = db.Column(db.Integer, primary_key=True)
    template_name = db.Column(db.String(200), nullable=False)
    template_type = db.Column(db.String(100), nullable=False)  # executive, funder, board, program, beneficiary
    stakeholder_audience = db.Column(db.String(100))  # primary target audience
    
    # Template structure
    template_sections = db.Column(db.Text)  # JSON: ordered list of report sections
    layout_config = db.Column(db.Text)  # JSON: visual layout and styling
    content_rules = db.Column(db.Text)  # JSON: AI content generation rules
    
    # Branding and styling
    brand_theme = db.Column(db.String(50), default="pink_lemonade")
    header_config = db.Column(db.Text)  # JSON: header layout and logos
    footer_config = db.Column(db.Text)  # JSON: footer content and styling
    
    # Output formats
    supported_formats = db.Column(db.Text)  # JSON: list of export formats (pdf, docx, html)
    default_format = db.Column(db.String(20), default="pdf")
    
    # Usage and performance
    usage_count = db.Column(db.Integer, default=0)
    average_generation_time = db.Column(db.Float)  # seconds
    user_satisfaction_score = db.Column(db.Float)
    
    # Template status
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    version = db.Column(db.String(20), default="1.0")
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "template_name": self.template_name,
            "template_type": self.template_type,
            "stakeholder_audience": self.stakeholder_audience,
            "supported_formats": json.loads(self.supported_formats) if self.supported_formats else [],
            "default_format": self.default_format,
            "usage_count": self.usage_count,
            "user_satisfaction_score": self.user_satisfaction_score,
            "is_active": self.is_active,
            "version": self.version,
            "created_at": self.created_at.isoformat()
        }


class ReportGeneration(db.Model):
    """Generated report tracking and metadata"""
    __tablename__ = "report_generations"
    
    id = db.Column(db.Integer, primary_key=True)
    report_template_id = db.Column(db.Integer, db.ForeignKey("report_templates.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    
    # Report metadata
    report_title = db.Column(db.String(300), nullable=False)
    report_type = db.Column(db.String(100))  # executive_summary, quarterly_report, impact_report
    stakeholder_audience = db.Column(db.String(100))
    reporting_period_start = db.Column(db.DateTime)
    reporting_period_end = db.Column(db.DateTime)
    
    # Generation details
    generation_status = db.Column(db.String(50), default="pending")  # pending, generating, completed, failed
    generation_progress = db.Column(db.Integer, default=0)  # 0-100
    generation_time_seconds = db.Column(db.Float)
    ai_confidence_score = db.Column(db.Float)
    
    # Content summary
    total_sections = db.Column(db.Integer)
    total_pages = db.Column(db.Integer)
    word_count = db.Column(db.Integer)
    chart_count = db.Column(db.Integer)
    data_points_included = db.Column(db.Integer)
    
    # Output information
    output_format = db.Column(db.String(20))
    file_size_mb = db.Column(db.Float)
    file_path = db.Column(db.String(500))
    download_url = db.Column(db.String(500))
    
    # Quality metrics
    content_quality_score = db.Column(db.Float)  # AI-assessed content quality
    visual_appeal_score = db.Column(db.Float)  # Layout and design quality
    stakeholder_relevance_score = db.Column(db.Float)  # Audience appropriateness
    
    # Usage and feedback
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    stakeholder_feedback_score = db.Column(db.Float)
    
    # Timestamps
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)  # File cleanup date
    
    def to_dict(self):
        return {
            "id": self.id,
            "report_title": self.report_title,
            "report_type": self.report_type,
            "stakeholder_audience": self.stakeholder_audience,
            "generation_status": self.generation_status,
            "generation_progress": self.generation_progress,
            "output_format": self.output_format,
            "total_pages": self.total_pages,
            "word_count": self.word_count,
            "ai_confidence_score": self.ai_confidence_score,
            "download_url": self.download_url,
            "requested_at": self.requested_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class ReportSchedule(db.Model):
    """Automated report generation and distribution schedules"""
    __tablename__ = "report_schedules"
    
    id = db.Column(db.Integer, primary_key=True)
    report_template_id = db.Column(db.Integer, db.ForeignKey("report_templates.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    
    # Schedule configuration
    schedule_name = db.Column(db.String(200), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)  # monthly, quarterly, annually, custom
    custom_schedule = db.Column(db.String(100))  # Cron expression for custom schedules
    
    # Timing settings
    generation_day = db.Column(db.Integer)  # Day of month/quarter for generation
    generation_hour = db.Column(db.Integer, default=9)  # Hour of day (24-hour format)
    timezone = db.Column(db.String(50), default="UTC")
    
    # Content configuration
    auto_data_refresh = db.Column(db.Boolean, default=True)
    include_trends = db.Column(db.Boolean, default=True)
    include_comparisons = db.Column(db.Boolean, default=True)
    include_recommendations = db.Column(db.Boolean, default=True)
    
    # Distribution settings
    auto_distribute = db.Column(db.Boolean, default=False)
    distribution_list = db.Column(db.Text)  # JSON: list of email recipients
    distribution_message = db.Column(db.Text)  # Custom message for distribution
    
    # Schedule status
    is_active = db.Column(db.Boolean, default=True)
    last_generated = db.Column(db.DateTime)
    next_generation = db.Column(db.DateTime)
    generation_count = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float)  # Success rate of automated generations
    
    # Error handling
    max_retries = db.Column(db.Integer, default=3)
    current_retries = db.Column(db.Integer, default=0)
    last_error_message = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "schedule_name": self.schedule_name,
            "frequency": self.frequency,
            "generation_day": self.generation_day,
            "generation_hour": self.generation_hour,
            "is_active": self.is_active,
            "auto_distribute": self.auto_distribute,
            "last_generated": self.last_generated.isoformat() if self.last_generated else None,
            "next_generation": self.next_generation.isoformat() if self.next_generation else None,
            "generation_count": self.generation_count,
            "success_rate": self.success_rate
        }


class ReportDistribution(db.Model):
    """Stakeholder-specific distribution tracking and analytics"""
    __tablename__ = "report_distributions"
    
    id = db.Column(db.Integer, primary_key=True)
    report_generation_id = db.Column(db.Integer, db.ForeignKey("report_generations.id"))
    
    # Recipient information
    recipient_name = db.Column(db.String(200))
    recipient_email = db.Column(db.String(200))
    recipient_type = db.Column(db.String(100))  # executive, board_member, funder, staff, partner
    recipient_organization = db.Column(db.String(200))
    
    # Distribution details
    distribution_method = db.Column(db.String(50), default="email")  # email, download, api
    distribution_status = db.Column(db.String(50), default="pending")  # pending, sent, delivered, failed
    custom_message = db.Column(db.Text)
    
    # Engagement tracking
    delivery_timestamp = db.Column(db.DateTime)
    first_viewed = db.Column(db.DateTime)
    last_viewed = db.Column(db.DateTime)
    view_count = db.Column(db.Integer, default=0)
    time_spent_viewing = db.Column(db.Integer)  # seconds
    
    # Download tracking
    download_count = db.Column(db.Integer, default=0)
    first_download = db.Column(db.DateTime)
    last_download = db.Column(db.DateTime)
    
    # Feedback and interaction
    feedback_rating = db.Column(db.Integer)  # 1-5 rating
    feedback_comments = db.Column(db.Text)
    feedback_submitted = db.Column(db.DateTime)
    
    # Follow-up actions
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_notes = db.Column(db.Text)
    follow_up_completed = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "recipient_name": self.recipient_name,
            "recipient_email": self.recipient_email,
            "recipient_type": self.recipient_type,
            "distribution_status": self.distribution_status,
            "view_count": self.view_count,
            "download_count": self.download_count,
            "feedback_rating": self.feedback_rating,
            "delivery_timestamp": self.delivery_timestamp.isoformat() if self.delivery_timestamp else None,
            "first_viewed": self.first_viewed.isoformat() if self.first_viewed else None,
            "last_viewed": self.last_viewed.isoformat() if self.last_viewed else None
        }


# =============================================================================
# Smart Reporting Phase 6 Models - Governance & Compliance Framework
# =============================================================================

class AuditLog(db.Model):
    """Comprehensive activity and change tracking"""
    __tablename__ = "audit_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Activity identification
    activity_type = db.Column(db.String(100), nullable=False)  # login, report_generation, template_edit, etc.
    entity_type = db.Column(db.String(100))  # report, template, user, system
    entity_id = db.Column(db.String(100))  # ID of affected entity
    action = db.Column(db.String(50), nullable=False)  # create, read, update, delete, execute
    
    # User and session information
    user_id = db.Column(db.String(100))
    user_role = db.Column(db.String(50))
    session_id = db.Column(db.String(100))
    ip_address = db.Column(db.String(45))  # IPv6 support
    user_agent = db.Column(db.Text)
    
    # Activity details
    activity_description = db.Column(db.Text, nullable=False)
    before_state = db.Column(db.Text)  # JSON: state before change
    after_state = db.Column(db.Text)  # JSON: state after change
    change_summary = db.Column(db.Text)  # Human-readable change description
    
    # Context and metadata
    request_method = db.Column(db.String(10))  # GET, POST, PUT, DELETE
    endpoint = db.Column(db.String(200))  # API endpoint accessed
    request_data = db.Column(db.Text)  # JSON: sanitized request data
    response_status = db.Column(db.Integer)  # HTTP response code
    
    # Compliance and security
    compliance_relevant = db.Column(db.Boolean, default=False)
    security_relevant = db.Column(db.Boolean, default=False)
    privacy_relevant = db.Column(db.Boolean, default=False)
    retention_period_days = db.Column(db.Integer, default=2555)  # 7 years default
    
    # Performance metrics
    processing_time_ms = db.Column(db.Float)
    memory_usage_mb = db.Column(db.Float)
    database_queries = db.Column(db.Integer)
    
    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "activity_type": self.activity_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "user_id": self.user_id,
            "activity_description": self.activity_description,
            "compliance_relevant": self.compliance_relevant,
            "security_relevant": self.security_relevant,
            "privacy_relevant": self.privacy_relevant,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms
        }


class ComplianceRule(db.Model):
    """Regulatory requirements and monitoring configuration"""
    __tablename__ = "compliance_rules"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Rule identification
    rule_name = db.Column(db.String(200), nullable=False)
    rule_category = db.Column(db.String(100), nullable=False)  # financial, reporting, privacy, security
    regulation_source = db.Column(db.String(100))  # GAAP, FASB, IRS, funder_specific, internal
    funder_id = db.Column(db.Integer)  # FK to specific funder if applicable
    
    # Rule definition
    rule_description = db.Column(db.Text, nullable=False)
    compliance_criteria = db.Column(db.Text, nullable=False)  # JSON: specific requirements
    validation_logic = db.Column(db.Text)  # JSON: automated validation rules
    severity_level = db.Column(db.String(20), default="medium")  # low, medium, high, critical
    
    # Monitoring configuration
    monitoring_frequency = db.Column(db.String(50), default="daily")  # continuous, hourly, daily, weekly
    automated_check = db.Column(db.Boolean, default=True)
    alert_threshold = db.Column(db.Float)  # Threshold for compliance violations
    notification_recipients = db.Column(db.Text)  # JSON: list of notification recipients
    
    # Deadlines and timing
    compliance_deadline_type = db.Column(db.String(50))  # fixed_date, periodic, event_triggered
    deadline_schedule = db.Column(db.String(100))  # Cron expression or specific dates
    advance_warning_days = db.Column(db.Integer, default=30)
    
    # Documentation and references
    legal_reference = db.Column(db.Text)
    documentation_url = db.Column(db.String(500))
    internal_policy_reference = db.Column(db.String(200))
    
    # Status and performance
    is_active = db.Column(db.Boolean, default=True)
    last_check = db.Column(db.DateTime)
    last_compliance_status = db.Column(db.String(20))  # compliant, non_compliant, warning, unknown
    violation_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    effective_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiration_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "rule_category": self.rule_category,
            "regulation_source": self.regulation_source,
            "rule_description": self.rule_description,
            "severity_level": self.severity_level,
            "monitoring_frequency": self.monitoring_frequency,
            "automated_check": self.automated_check,
            "is_active": self.is_active,
            "last_compliance_status": self.last_compliance_status,
            "violation_count": self.violation_count,
            "effective_date": self.effective_date.isoformat(),
            "last_check": self.last_check.isoformat() if self.last_check else None
        }


class DataGovernancePolicy(db.Model):
    """Privacy, security, and retention policy definitions"""
    __tablename__ = "data_governance_policies"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Policy identification
    policy_name = db.Column(db.String(200), nullable=False)
    policy_type = db.Column(db.String(50), nullable=False)  # privacy, security, retention, access
    data_category = db.Column(db.String(100))  # pii, financial, program_data, metadata
    jurisdiction = db.Column(db.String(50))  # US, EU, CA, etc.
    
    # Policy definition
    policy_description = db.Column(db.Text, nullable=False)
    policy_rules = db.Column(db.Text, nullable=False)  # JSON: specific policy rules
    enforcement_level = db.Column(db.String(20), default="strict")  # advisory, standard, strict
    
    # Privacy settings
    consent_required = db.Column(db.Boolean, default=False)
    opt_out_allowed = db.Column(db.Boolean, default=True)
    data_minimization = db.Column(db.Boolean, default=True)
    purpose_limitation = db.Column(db.Boolean, default=True)
    
    # Security controls
    encryption_required = db.Column(db.Boolean, default=True)
    access_controls = db.Column(db.Text)  # JSON: role-based access rules
    audit_logging = db.Column(db.Boolean, default=True)
    anonymization_rules = db.Column(db.Text)  # JSON: data anonymization requirements
    
    # Retention and lifecycle
    retention_period_days = db.Column(db.Integer)
    auto_deletion = db.Column(db.Boolean, default=False)
    archive_before_deletion = db.Column(db.Boolean, default=True)
    deletion_method = db.Column(db.String(50), default="secure_wipe")  # soft_delete, secure_wipe, cryptographic
    
    # Compliance and legal
    regulatory_basis = db.Column(db.Text)  # Legal basis for policy (GDPR Article, etc.)
    breach_notification_required = db.Column(db.Boolean, default=True)
    breach_notification_timeframe = db.Column(db.Integer, default=72)  # hours
    
    # Monitoring and enforcement
    automated_enforcement = db.Column(db.Boolean, default=True)
    violation_tracking = db.Column(db.Boolean, default=True)
    exception_process = db.Column(db.Text)  # Process for handling exceptions
    
    # Status and versioning
    is_active = db.Column(db.Boolean, default=True)
    version = db.Column(db.String(20), default="1.0")
    approval_status = db.Column(db.String(20), default="draft")  # draft, approved, deprecated
    approved_by = db.Column(db.String(200))
    approved_date = db.Column(db.DateTime)
    
    # Timestamps
    effective_date = db.Column(db.DateTime, default=datetime.utcnow)
    review_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "policy_name": self.policy_name,
            "policy_type": self.policy_type,
            "data_category": self.data_category,
            "jurisdiction": self.jurisdiction,
            "policy_description": self.policy_description,
            "enforcement_level": self.enforcement_level,
            "consent_required": self.consent_required,
            "encryption_required": self.encryption_required,
            "retention_period_days": self.retention_period_days,
            "automated_enforcement": self.automated_enforcement,
            "is_active": self.is_active,
            "version": self.version,
            "approval_status": self.approval_status,
            "effective_date": self.effective_date.isoformat()
        }


class QualityAssessment(db.Model):
    """Report and data quality evaluation records"""
    __tablename__ = "quality_assessments"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Assessment target
    assessment_type = db.Column(db.String(50), nullable=False)  # report, data, system, process
    target_entity_type = db.Column(db.String(50))  # report_generation, template, data_collection
    target_entity_id = db.Column(db.String(100))
    
    # Assessment execution
    assessment_method = db.Column(db.String(50), default="automated")  # automated, manual, hybrid
    assessor_id = db.Column(db.String(100))  # User ID or system identifier
    assessment_criteria = db.Column(db.Text)  # JSON: quality criteria used
    
    # Quality scores
    overall_quality_score = db.Column(db.Float, nullable=False)  # 0-10 scale
    accuracy_score = db.Column(db.Float)
    completeness_score = db.Column(db.Float)
    consistency_score = db.Column(db.Float)
    timeliness_score = db.Column(db.Float)
    relevance_score = db.Column(db.Float)
    
    # Detailed findings
    quality_issues = db.Column(db.Text)  # JSON: list of identified issues
    recommendations = db.Column(db.Text)  # JSON: improvement recommendations
    corrective_actions = db.Column(db.Text)  # JSON: required/suggested actions
    
    # Assessment context
    assessment_scope = db.Column(db.Text)  # What was assessed
    baseline_comparison = db.Column(db.Float)  # Comparison to baseline/previous assessment
    trend_analysis = db.Column(db.Text)  # JSON: quality trend information
    
    # Validation and approval
    validation_status = db.Column(db.String(20), default="pending")  # pending, validated, rejected
    validated_by = db.Column(db.String(100))
    validation_notes = db.Column(db.Text)
    
    # Follow-up tracking
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_due_date = db.Column(db.DateTime)
    follow_up_completed = db.Column(db.Boolean, default=False)
    follow_up_notes = db.Column(db.Text)
    
    # Performance metrics
    assessment_duration_seconds = db.Column(db.Float)
    automated_checks_performed = db.Column(db.Integer)
    manual_validations_performed = db.Column(db.Integer)
    
    # Timestamps
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "assessment_type": self.assessment_type,
            "target_entity_type": self.target_entity_type,
            "target_entity_id": self.target_entity_id,
            "assessment_method": self.assessment_method,
            "overall_quality_score": self.overall_quality_score,
            "accuracy_score": self.accuracy_score,
            "completeness_score": self.completeness_score,
            "consistency_score": self.consistency_score,
            "timeliness_score": self.timeliness_score,
            "relevance_score": self.relevance_score,
            "validation_status": self.validation_status,
            "follow_up_required": self.follow_up_required,
            "assessment_date": self.assessment_date.isoformat(),
            "assessment_duration_seconds": self.assessment_duration_seconds
        }
