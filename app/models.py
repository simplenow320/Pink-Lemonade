from app import db
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

# User authentication models
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)  # Made nullable for auth flow
    password_hash = db.Column(db.String(256))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    org_name = db.Column(db.String(200))  # Added for organization name
    job_title = db.Column(db.String(100))  # User's role/title in the organization
    role = db.Column(db.String(20), default='member')  # admin, manager, member
    org_id = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    verification_token_expires = db.Column(db.DateTime)  # Added for token expiry
    reset_token = db.Column(db.String(100))
    reset_token_expires = db.Column(db.DateTime)  # Renamed from reset_token_expiry
    verified_at = db.Column(db.DateTime)  # Added for tracking verification time
    timezone = db.Column(db.String(50), default='UTC')
    notification_preferences = db.Column(db.JSON, default=dict)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Flask-Login properties
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self):
        self.verification_token = secrets.token_urlsafe(32)
        return self.verification_token
    
    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
        return self.reset_token
    
    def verify_reset_token(self, token):
        if not self.reset_token or self.reset_token != token:
            return False
        if self.reset_token_expiry and self.reset_token_expiry < datetime.utcnow():
            return False
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role,
            'org_id': self.org_id,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'timezone': self.timezone,
            'notification_preferences': self.notification_preferences or {},
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserProgress(db.Model):
    __tablename__ = "user_progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    total_xp = db.Column(db.Integer, default=0)
    current_level = db.Column(db.Integer, default=1)
    completed_steps = db.Column(db.Text)  # JSON array of completed step IDs
    achievements = db.Column(db.Text)  # JSON array of achievement IDs
    streak_days = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime)
    onboarding_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_xp': self.total_xp,
            'current_level': self.current_level,
            'completed_steps': self.completed_steps,
            'achievements': self.achievements,
            'streak_days': self.streak_days,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'onboarding_complete': self.onboarding_complete,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Achievement(db.Model):
    __tablename__ = "achievements"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    xp_reward = db.Column(db.Integer, default=0)
    icon = db.Column(db.String(10))
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'xp_reward': self.xp_reward,
            'icon': self.icon,
            'category': self.category
        }

class OnboardingStep(db.Model):
    __tablename__ = "onboarding_steps"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    xp_reward = db.Column(db.Integer, default=0)
    icon = db.Column(db.String(10))
    category = db.Column(db.String(50))
    tasks = db.Column(db.Text)  # JSON array of tasks
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'title': self.title,
            'description': self.description,
            'order': self.order,
            'xp_reward': self.xp_reward,
            'icon': self.icon,
            'category': self.category,
            'tasks': self.tasks
        }

class UserInvite(db.Model):
    __tablename__ = "user_invites"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    org_id = db.Column(db.String(50))
    role = db.Column(db.String(20), default='member')
    invite_token = db.Column(db.String(100), unique=True)
    invited_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    accepted = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def generate_token(self):
        self.invite_token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(days=7)
        return self.invite_token
    
    def is_valid(self):
        if self.accepted:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'org_id': self.org_id,
            'role': self.role,
            'invited_by': self.invited_by,
            'accepted': self.accepted,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Organization(db.Model):
    __tablename__ = "organizations"
    id = db.Column(db.Integer, primary_key=True)
    
    # Core Identity
    name = db.Column(db.String(255), nullable=False, unique=True)
    legal_name = db.Column(db.String(255))  # Legal registered name
    ein = db.Column(db.String(20))  # Tax ID / EIN
    org_type = db.Column(db.String(50))  # 501c3, faith-based, educational, etc.
    year_founded = db.Column(db.Integer)
    website = db.Column(db.String(255))
    social_media = db.Column(db.JSON)  # {twitter: '', facebook: '', etc.}
    
    # Mission & Vision
    mission = db.Column(db.Text)
    vision = db.Column(db.Text)
    values = db.Column(db.Text)  # Core values
    
    # Program Focus
    primary_focus_areas = db.Column(db.JSON)  # ['education', 'housing', 'healthcare']
    secondary_focus_areas = db.Column(db.JSON)  # Additional areas
    programs_services = db.Column(db.Text)  # Detailed program descriptions
    target_demographics = db.Column(db.JSON)  # ['youth', 'seniors', 'families']
    age_groups_served = db.Column(db.JSON)  # ['0-5', '6-12', '13-18', etc.]
    
    # Geographic Scope
    service_area_type = db.Column(db.String(50))  # local, regional, national, international
    primary_city = db.Column(db.String(100))
    primary_state = db.Column(db.String(50))
    primary_zip = db.Column(db.String(20))
    counties_served = db.Column(db.JSON)  # List of counties
    states_served = db.Column(db.JSON)  # List of states if multi-state
    
    # Organizational Capacity
    annual_budget_range = db.Column(db.String(50))  # <$100k, $100k-500k, etc.
    staff_size = db.Column(db.String(50))  # 1-5, 6-10, 11-25, etc.
    volunteer_count = db.Column(db.String(50))  # Range
    board_size = db.Column(db.Integer)
    
    # Impact Metrics
    people_served_annually = db.Column(db.String(50))  # Range or number
    key_achievements = db.Column(db.Text)  # Major accomplishments
    impact_metrics = db.Column(db.JSON)  # Measurable outcomes
    
    # Grant History & Preferences
    previous_funders = db.Column(db.JSON)  # List of past funders
    typical_grant_size = db.Column(db.String(50))  # Range
    grant_success_rate = db.Column(db.Float)  # Percentage
    preferred_grant_types = db.Column(db.JSON)  # ['operating', 'project', 'capacity']
    grant_writing_capacity = db.Column(db.String(50))  # internal, consultant, both
    
    # Special Characteristics
    faith_based = db.Column(db.Boolean, default=False)
    minority_led = db.Column(db.Boolean, default=False)
    woman_led = db.Column(db.Boolean, default=False)
    lgbtq_led = db.Column(db.Boolean, default=False)
    veteran_led = db.Column(db.Boolean, default=False)
    
    # AI Learning Fields
    keywords = db.Column(db.JSON)  # Important keywords for matching
    unique_capabilities = db.Column(db.Text)  # What makes org unique
    partnership_interests = db.Column(db.Text)  # Collaboration areas
    funding_priorities = db.Column(db.Text)  # Current funding needs
    exclusions = db.Column(db.JSON)  # Things they DON'T do/want
    
    # Profile Completion
    profile_completeness = db.Column(db.Integer, default=0)  # Percentage
    onboarding_completed_at = db.Column(db.DateTime)
    last_profile_update = db.Column(db.DateTime)
    
    # Admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    
    def calculate_completeness(self):
        """Calculate profile completion percentage"""
        required_fields = [
            'name', 'mission', 'org_type', 'primary_focus_areas', 
            'service_area_type', 'annual_budget_range', 'staff_size'
        ]
        optional_fields = [
            'legal_name', 'ein', 'year_founded', 'website', 'vision', 
            'programs_services', 'target_demographics', 'key_achievements',
            'previous_funders', 'unique_capabilities'
        ]
        
        completed = 0
        total = len(required_fields) + len(optional_fields)
        
        for field in required_fields:
            if getattr(self, field):
                completed += 2  # Required fields worth more
        
        for field in optional_fields:
            if getattr(self, field):
                completed += 1
                
        self.profile_completeness = min(100, int((completed / (len(required_fields) * 2 + len(optional_fields))) * 100))
        return self.profile_completeness
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'legal_name': self.legal_name,
            'ein': self.ein,
            'org_type': self.org_type,
            'year_founded': self.year_founded,
            'website': self.website,
            'social_media': self.social_media or {},
            'mission': self.mission,
            'vision': self.vision,
            'values': self.values,
            'primary_focus_areas': self.primary_focus_areas or [],
            'secondary_focus_areas': self.secondary_focus_areas or [],
            'programs_services': self.programs_services,
            'target_demographics': self.target_demographics or [],
            'age_groups_served': self.age_groups_served or [],
            'service_area_type': self.service_area_type,
            'primary_city': self.primary_city,
            'primary_state': self.primary_state,
            'counties_served': self.counties_served or [],
            'annual_budget_range': self.annual_budget_range,
            'staff_size': self.staff_size,
            'volunteer_count': self.volunteer_count,
            'board_size': self.board_size,
            'people_served_annually': self.people_served_annually,
            'key_achievements': self.key_achievements,
            'impact_metrics': self.impact_metrics or {},
            'previous_funders': self.previous_funders or [],
            'typical_grant_size': self.typical_grant_size,
            'grant_success_rate': self.grant_success_rate,
            'preferred_grant_types': self.preferred_grant_types or [],
            'faith_based': self.faith_based,
            'minority_led': self.minority_led,
            'woman_led': self.woman_led,
            'keywords': self.keywords or [],
            'unique_capabilities': self.unique_capabilities,
            'funding_priorities': self.funding_priorities,
            'profile_completeness': self.profile_completeness,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def to_ai_context(self):
        """Generate comprehensive context for AI matching"""
        return {
            'name': self.name,
            'mission': self.mission,
            'vision': self.vision,
            'focus_areas': (self.primary_focus_areas or []) + (self.secondary_focus_areas or []),
            'keywords': self.keywords or [],
            'geographic_focus': f"{self.service_area_type} - {self.primary_city}, {self.primary_state}",
            'target_population': ', '.join(self.target_demographics or []),
            'annual_budget': self.annual_budget_range,
            'staff_capacity': self.staff_size,
            'grant_experience': {
                'previous_funders': self.previous_funders or [],
                'typical_size': self.typical_grant_size,
                'success_rate': self.grant_success_rate
            },
            'unique_factors': {
                'faith_based': self.faith_based,
                'minority_led': self.minority_led,
                'woman_led': self.woman_led,
                'unique_capabilities': self.unique_capabilities
            },
            'current_needs': self.funding_priorities,
            'exclusions': self.exclusions or []
        }

class Module(db.Model):
    __tablename__ = "modules"
    key = db.Column(db.String(50), primary_key=True)  # e.g., 'case_support'
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    enabled_default = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'key': self.key,
            'name': self.name,
            'description': self.description,
            'enabled_default': self.enabled_default
        }

class OrgModule(db.Model):
    __tablename__ = "org_modules"
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id"), nullable=False)
    module_key = db.Column(db.String(50), db.ForeignKey("modules.key"), nullable=False)
    enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'module_key': self.module_key,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class OrgAsset(db.Model):
    __tablename__ = "org_assets"
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id"), nullable=False)
    type = db.Column(db.String(20))  # 'web'|'pdf'|'text'
    title = db.Column(db.String(255))
    url_or_path = db.Column(db.Text)
    approved = db.Column(db.Boolean, default=False)
    added_by = db.Column(db.String(120))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'type': self.type,
            'title': self.title,
            'url_or_path': self.url_or_path,
            'approved': self.approved,
            'added_by': self.added_by,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }

class OrgVoiceProfile(db.Model):
    __tablename__ = "org_voice_profiles"
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id"), primary_key=True)
    reading_level = db.Column(db.String(50))
    formality = db.Column(db.Integer)  # 1..5
    faith_language = db.Column(db.Boolean)
    sentence_length = db.Column(db.String(20))  # 'short'|'medium'|'long'
    cta_style = db.Column(db.String(255))
    common_phrases = db.Column(db.JSON, default=list)  # ["...","..."]
    preferred_proof_points = db.Column(db.JSON, default=list)  # ["...","..."]
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'org_id': self.org_id,
            'reading_level': self.reading_level,
            'formality': self.formality,
            'faith_language': self.faith_language,
            'sentence_length': self.sentence_length,
            'cta_style': self.cta_style,
            'common_phrases': self.common_phrases or [],
            'preferred_proof_points': self.preferred_proof_points or [],
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class GrantActivity(db.Model):
    __tablename__ = "grant_activities"
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey("grants.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(50))  # status_change, document_added, note_added, etc.
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'user_id': self.user_id,
            'action': self.action,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class GrantDocument(db.Model):
    __tablename__ = "grant_documents"
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey("grants.id"), nullable=False)
    filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    document_type = db.Column(db.String(50))  # proposal, budget, letter_of_support, etc.
    description = db.Column(db.Text)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'document_type': self.document_type,
            'description': self.description,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }

class Grant(db.Model):
    __tablename__ = "grants"
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id"))
    title = db.Column(db.String(500), nullable=False)
    funder = db.Column(db.String(255))
    link = db.Column(db.Text)
    amount_min = db.Column(db.Numeric(14,2))
    amount_max = db.Column(db.Numeric(14,2))
    deadline = db.Column(db.Date)
    geography = db.Column(db.String(255))
    eligibility = db.Column(db.Text)
    status = db.Column(db.String(30), default="idea")  # idea|researching|drafting|submitted|awarded|declined
    source_name = db.Column(db.String(255))
    source_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Legacy fields for backward compatibility
    match_score = db.Column(db.Integer)
    match_reason = db.Column(db.Text)
    
    # Intelligence fields
    contact_info = db.Column(db.JSON)
    requirements_summary = db.Column(db.Text)
    application_complexity = db.Column(db.Integer)
    ai_summary = db.Column(db.Text)
    last_intelligence_update = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'title': self.title,
            'funder': self.funder,
            'link': self.link,
            'amount_min': float(self.amount_min) if self.amount_min else None,
            'amount_max': float(self.amount_max) if self.amount_max else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'geography': self.geography,
            'eligibility': self.eligibility,
            'status': self.status,
            'source_name': self.source_name,
            'source_url': self.source_url,
            'match_score': self.match_score,
            'match_reason': self.match_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class GrantNote(db.Model):
    __tablename__ = "grant_notes"
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey("grants.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'body': self.body,
            'author': self.author,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class GrantContact(db.Model):
    __tablename__ = "grant_contacts"
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey("grants.id"), nullable=False)
    name = db.Column(db.String(120))
    role = db.Column(db.String(120))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'name': self.name,
            'role': self.role,
            'email': self.email,
            'phone': self.phone,
            'notes': self.notes
        }

class CaseSupportDoc(db.Model):
    __tablename__ = "case_support_docs"
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id"), nullable=False)
    title = db.Column(db.String(255))
    sections = db.Column(db.JSON, default=dict)  # { "Executive Summary": "...", ... }
    sources = db.Column(db.JSON, default=dict)   # source map
    needs_input = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'title': self.title,
            'sections': self.sections or {},
            'sources': self.sources or {},
            'needs_input': self.needs_input or [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class GrantPitchDoc(db.Model):
    __tablename__ = "grant_pitch_docs"
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id"), nullable=False)
    funder = db.Column(db.String(255))
    sections = db.Column(db.JSON, default=dict)
    sources = db.Column(db.JSON, default=dict)
    needs_input = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'funder': self.funder,
            'sections': self.sections or {},
            'sources': self.sources or {},
            'needs_input': self.needs_input or [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ImpactReport(db.Model):
    __tablename__ = "impact_reports"
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id"), nullable=False)
    grant_id = db.Column(db.Integer, db.ForeignKey("grants.id"))
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    sections = db.Column(db.JSON, default=dict)
    tables = db.Column(db.JSON, default=list)
    charts = db.Column(db.JSON, default=list)
    sources = db.Column(db.JSON, default=dict)
    needs_update = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'grant_id': self.grant_id,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'sections': self.sections or {},
            'tables': self.tables or [],
            'charts': self.charts or [],
            'sources': self.sources or {},
            'needs_update': self.needs_update or [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Contribution(db.Model):
    __tablename__ = "contributions"
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id"), nullable=False)
    raw = db.Column(db.Text)
    clean = db.Column(db.Text)
    facts = db.Column(db.JSON, default=list)     # [{"key":"", "value":"", "date":"", ...}]
    tags = db.Column(db.JSON, default=list)
    confidence = db.Column(db.String(10))        # high|med|low
    source = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'raw': self.raw,
            'clean': self.clean,
            'facts': self.facts or [],
            'tags': self.tags or [],
            'confidence': self.confidence,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class EditLearningEvent(db.Model):
    __tablename__ = "edit_learning_events"
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id"), nullable=False)
    draft_type = db.Column(db.String(40))  # case_support|pitch|report
    draft_id = db.Column(db.Integer)
    phrases_added = db.Column(db.JSON, default=list)
    proof_points_added = db.Column(db.JSON, default=list)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'draft_type': self.draft_type,
            'draft_id': self.draft_id,
            'phrases_added': self.phrases_added or [],
            'proof_points_added': self.proof_points_added or [],
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Watchlist(db.Model):
    __tablename__ = "watchlists"
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id"), nullable=False)
    city = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'city': self.city,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class WatchlistSource(db.Model):
    __tablename__ = "watchlist_sources"
    id = db.Column(db.Integer, primary_key=True)
    watchlist_id = db.Column(db.Integer, db.ForeignKey("watchlists.id"), nullable=False)
    name = db.Column(db.String(255))
    url = db.Column(db.Text)
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'watchlist_id': self.watchlist_id,
            'name': self.name,
            'url': self.url,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Organization class is now the primary organization model

# Legacy ScraperSource and ScraperHistory for backward compatibility with existing scraper code
class ScraperSource(db.Model):
    __tablename__ = "scraper_sources"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_scraped = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'is_active': self.is_active,
            'last_scraped': self.last_scraped.isoformat() if self.last_scraped else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ScraperHistory(db.Model):
    __tablename__ = "scraper_history"
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    sources_scraped = db.Column(db.Integer)
    grants_found = db.Column(db.Integer)
    grants_added = db.Column(db.Integer)
    status = db.Column(db.String(50))
    error_message = db.Column(db.Text)
    
    # Web search related fields
    sites_searched_estimate = db.Column(db.Integer)
    total_queries_attempted = db.Column(db.Integer)
    successful_queries = db.Column(db.Integer)
    search_keywords_used = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'sources_scraped': self.sources_scraped,
            'grants_found': self.grants_found,
            'grants_added': self.grants_added,
            'status': self.status,
            'error_message': self.error_message,
            'sites_searched_estimate': self.sites_searched_estimate,
            'total_queries_attempted': self.total_queries_attempted,
            'successful_queries': self.successful_queries,
            'search_keywords_used': self.search_keywords_used
        }

# Legacy analytics models for backward compatibility
class GrantAnalytics(db.Model):
    __tablename__ = "grant_analytics"
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey("grants.id"), nullable=False)
    views = db.Column(db.Integer, default=0)
    applications = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'views': self.views,
            'applications': self.applications,
            'success_rate': self.success_rate,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class GrantSuccessMetrics(db.Model):
    __tablename__ = "grant_success_metrics"
    id = db.Column(db.Integer, primary_key=True)
    period = db.Column(db.String(50))  # 'monthly', 'quarterly', 'yearly'
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    total_applications = db.Column(db.Integer, default=0)
    successful_applications = db.Column(db.Integer, default=0)
    total_amount_requested = db.Column(db.Float, default=0.0)
    total_amount_awarded = db.Column(db.Float, default=0.0)
    focus_areas = db.Column(db.JSON, default=list)
    
    def to_dict(self):
        return {
            'id': self.id,
            'period': self.period,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'total_applications': self.total_applications,
            'successful_applications': self.successful_applications,
            'total_amount_requested': self.total_amount_requested,
            'total_amount_awarded': self.total_amount_awarded,
            'focus_areas': self.focus_areas or []
        }

# Legacy narrative model for backward compatibility
class Narrative(db.Model):
    __tablename__ = "narratives"
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey("grants.id"), nullable=False)
    section = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    ai_generated = db.Column(db.Boolean, default=False)
    human_edited = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'section': self.section,
            'content': self.content,
            'ai_generated': self.ai_generated,
            'human_edited': self.human_edited,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
class Analytics(db.Model):
    __tablename__ = "analytics"
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)  # grant_decision, application_outcome, etc.
    event_data = db.Column(db.JSON)  # Flexible data storage for various event types
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"))
    grant_id = db.Column(db.Integer, db.ForeignKey("grants.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "user_id": self.user_id,
            "org_id": self.org_id,
            "grant_id": self.grant_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
