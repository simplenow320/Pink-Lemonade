"""
Smart Templates Models for Phase 5
Handles template storage, versioning, and document generation
"""

from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class TemplateCategory(db.Model):
    """Categories for organizing templates"""
    __tablename__ = 'template_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    templates = db.relationship('SmartTemplate', back_populates='category', lazy='dynamic')

class SmartTemplate(db.Model):
    """Smart document templates with AI enhancement"""
    __tablename__ = 'smart_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('template_categories.id'))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    template_type = db.Column(db.String(50))  # 'grant_pitch', 'case_support', 'impact_report', 'thank_you', 'social_media', 'newsletter'
    
    # Template content and structure
    structure = db.Column(JSON)  # Sections, fields, requirements
    default_content = db.Column(JSON)  # Pre-filled content blocks
    ai_prompts = db.Column(JSON)  # AI generation prompts for each section
    
    # Smart Tools specific fields
    tool_type = db.Column(db.String(50))  # 'grant_pitch', 'case_support', 'impact_report', etc.
    input_parameters = db.Column(JSON)  # Parameters used to generate content
    tags = db.Column(JSON)  # Tags for categorization: ['education', 'foundation', 'community']
    focus_areas = db.Column(JSON)  # Focus areas: ['health', 'education', 'environment']
    funder_types = db.Column(JSON)  # Funder types: ['foundation', 'government', 'corporate']
    generated_content = db.Column(db.Text)  # The actual generated content
    
    # Organization access control
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_shared = db.Column(db.Boolean, default=False)  # Whether template can be shared across organizations
    
    # Metadata
    typical_length = db.Column(db.String(50))  # '2-3 pages', '500 words', etc.
    time_to_complete = db.Column(db.String(50))  # '30 minutes', '1 hour', etc.
    difficulty_level = db.Column(db.String(20))  # 'easy', 'moderate', 'advanced'
    
    # Usage tracking
    times_used = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    avg_rating = db.Column(db.Float, default=0.0)
    last_used_at = db.Column(db.DateTime, nullable=True)
    
    # System fields
    is_active = db.Column(db.Boolean, default=True)
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = db.relationship('TemplateCategory', back_populates='templates')
    documents = db.relationship('GeneratedDocument', back_populates='template', lazy='dynamic')

class GeneratedDocument(db.Model):
    """Documents generated from templates"""
    __tablename__ = 'generated_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('smart_templates.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    
    # Document content
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(JSON)  # Structured content with sections
    rendered_html = db.Column(db.Text)  # HTML version
    rendered_text = db.Column(db.Text)  # Plain text version
    
    # Version control
    version = db.Column(db.Integer, default=1)
    parent_document_id = db.Column(db.Integer, db.ForeignKey('generated_documents.id'), nullable=True)
    
    # Metadata
    word_count = db.Column(db.Integer)
    ai_enhanced = db.Column(db.Boolean, default=False)
    completion_percentage = db.Column(db.Float, default=0.0)
    
    # Collaboration
    is_shared = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(100), unique=True, nullable=True)
    last_edited_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Status
    status = db.Column(db.String(50), default='draft')  # draft, in_review, final, submitted
    submitted_at = db.Column(db.DateTime, nullable=True)
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    template = db.relationship('SmartTemplate', back_populates='documents')
    versions = db.relationship('GeneratedDocument', backref=db.backref('parent', remote_side=[id]))
    comments = db.relationship('DocumentComment', back_populates='document', lazy='dynamic')

class DocumentComment(db.Model):
    """Comments and feedback on generated documents"""
    __tablename__ = 'document_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('generated_documents.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Comment content
    section_id = db.Column(db.String(100), nullable=True)  # Specific section being commented on
    comment_text = db.Column(db.Text, nullable=False)
    suggestion = db.Column(db.Text, nullable=True)  # Suggested edit
    
    # Comment metadata
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    document = db.relationship('GeneratedDocument', back_populates='comments')

class ContentLibrary(db.Model):
    """Reusable content blocks for templates"""
    __tablename__ = 'content_library'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    
    # Content details
    title = db.Column(db.String(200), nullable=False)
    content_type = db.Column(db.String(50))  # 'mission', 'impact', 'methodology', 'budget_narrative', etc.
    content = db.Column(db.Text, nullable=False)
    
    # Usage tracking
    times_used = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime, nullable=True)
    success_rate = db.Column(db.Float, default=0.0)
    
    # Metadata
    tags = db.Column(JSON)
    is_favorite = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)