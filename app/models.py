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

class Org(db.Model):
    __tablename__ = "orgs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    mission = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mission': self.mission,
            'created_at': self.created_at.isoformat() if self.created_at else None
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

# Legacy Organization class for backward compatibility
Organization = Org

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