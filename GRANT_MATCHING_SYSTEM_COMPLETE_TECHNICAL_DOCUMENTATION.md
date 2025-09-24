# 🎯 GrantFlow: Complete Technical Documentation & System Rebuild Guide

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Deep Dive](#architecture-deep-dive) 
3. [Database Schema](#database-schema)
4. [Authentication & User Management](#authentication--user-management)
5. [Grant Data Collection System](#grant-data-collection-system)
6. [AI Matching Engine](#ai-matching-engine)
7. [API Integration Framework](#api-integration-framework)
8. [Workflow Management](#workflow-management)
9. [Payment & Subscription System](#payment--subscription-system)
10. [Service Layer Architecture](#service-layer-architecture)
11. [Frontend Integration](#frontend-integration)
12. [Deployment & Infrastructure](#deployment--infrastructure)
13. [Troubleshooting Guide](#troubleshooting-guide)
14. [System Rebuild Instructions](#system-rebuild-instructions)

---

## 🏗️ System Overview

### Core Purpose
GrantFlow is an AI-powered grant management platform that:
- **Discovers** grants from 70+ sources automatically
- **Matches** opportunities using AI scoring (1-5 scale)
- **Manages** complete grant lifecycle (8-stage workflow)
- **Generates** AI-powered narratives and proposals
- **Tracks** analytics and success metrics
- **Collaborates** through team-based RBAC system

### Technology Stack
- **Backend**: Flask (Python 3.11) with SQLAlchemy ORM
- **Database**: PostgreSQL with 45+ tables
- **Frontend**: React 18 + Tailwind CSS
- **AI**: OpenAI GPT-4o/3.5-turbo with REACTO prompting
- **Payment**: Stripe integration
- **Deployment**: Gunicorn + Replit hosting
- **Caching**: Redis (with memory fallback)

---

## 🏛️ Architecture Deep Dive

### Application Factory Pattern
```python
# app/__init__.py
def create_app():
    app = Flask(__name__)
    
    # Core configurations
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.secret_key = os.environ.get("SESSION_SECRET")
    
    # Initialize extensions
    db.init_app(app)
    
    # Register all blueprints
    from app.api import auth, grants, ai_grants, workflow, analytics
    app.register_blueprint(auth.bp)
    app.register_blueprint(grants.bp)
    # ... 30+ API blueprints
    
    return app
```

### Main Entry Point Logic Flow
```python
# main.py
app = create_app()

# Health check for deployment monitoring
@app.route('/health')
def health():
    return {'status': 'healthy', 'message': 'Application is running'}

# React app serving with fallbacks
@app.route('/')
def serve_react_app():
    # Priority: build > public > templates
    try:
        return send_file('client/build/index.html')
    except:
        try:
            return send_file('client/public/index.html')  
        except:
            return send_file('templates/index.html')

# API route protection (don't serve React for /api/*)
@app.route('/<path:path>')
def catch_all(path):
    if path.startswith('api/'):
        abort(404)  # Let Flask blueprints handle API routes
    return serve_react_app()
```

### Service Layer Architecture
```
app/services/
├── Core Services
│   ├── apiManager.py          # Unified API integration manager
│   ├── ai_service.py          # OpenAI GPT integration
│   ├── auth_service.py        # Authentication logic
│   └── mode.py               # DEMO/LIVE mode detection
├── Data Collection
│   ├── candid_client.py       # Premium Candid APIs (News, Grants, Essentials)
│   ├── federal_register_client.py  # Government funding notices
│   ├── grants_gov_client.py   # Federal grant opportunities
│   ├── comprehensive_grant_scraper.py  # 70-foundation scraper
│   └── foundation_aggregator.py       # Foundation data aggregation
├── AI & Matching
│   ├── ai_grant_matcher.py    # Grant-to-organization matching
│   ├── ai_optimizer_service.py # Cost optimization (GPT-4o vs 3.5)
│   ├── reacto_prompt_service.py # REACTO prompt engineering
│   └── matching_service.py    # Core matching algorithms
├── Business Logic
│   ├── workflow_service.py    # 8-stage grant workflow
│   ├── analytics_service.py   # Success tracking & metrics
│   ├── payment_service.py     # Stripe integration
│   └── team_service.py       # Collaboration & RBAC
└── Infrastructure
    ├── cache_service.py       # Redis/memory caching
    ├── credential_manager.py  # API key management
    └── monitoring_service.py  # System health monitoring
```

---

## 🗄️ Database Schema

### Core Tables (45+ tables total)

#### User Management
```sql
-- Users table with authentication & profile data
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    username VARCHAR(80) UNIQUE,
    password_hash VARCHAR(256),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    org_name VARCHAR(200),
    job_title VARCHAR(100),
    role VARCHAR(20) DEFAULT 'member',  -- admin, manager, member
    org_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(100),
    verification_token_expires TIMESTAMP,
    reset_token VARCHAR(100),
    reset_token_expires TIMESTAMP,
    timezone VARCHAR(50) DEFAULT 'UTC',
    notification_preferences JSON,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Organization profiles with AI matching data
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    legal_name VARCHAR(500),
    dba_name VARCHAR(500),
    ein VARCHAR(20),
    mission_statement TEXT,
    website_url VARCHAR(500),
    phone VARCHAR(20),
    email VARCHAR(200),
    address_line1 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(100),
    organization_type VARCHAR(100),
    annual_budget DECIMAL(15,2),
    staff_size INTEGER,
    board_size INTEGER,
    founded_year INTEGER,
    focus_areas JSON,  -- AI matching keywords
    target_populations JSON,  -- Geographic & demographic targets
    program_keywords JSON,    -- Program-specific matching terms
    past_funders JSON,       -- Historical funder relationships
    grant_history_summary TEXT,
    capacity_assessment JSON,
    ai_profile_completeness DECIMAL(5,2),  -- 0-100% completeness score
    last_profile_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Grant Management System
```sql
-- Main grants table (current: 677 grants)
CREATE TABLE grants (
    id SERIAL PRIMARY KEY,
    org_id INTEGER,  -- Links to organization
    title TEXT NOT NULL,
    funder TEXT,
    link TEXT,
    amount_min DECIMAL(15,2),
    amount_max DECIMAL(15,2),
    deadline DATE,
    geography VARCHAR(200),
    eligibility TEXT,
    status VARCHAR(50) DEFAULT 'idea',  -- idea, researching, writing, submitted, etc.
    source_name VARCHAR(200),
    source_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- AI Enhancement Fields
    match_score DECIMAL(3,1),  -- 1.0-5.0 AI matching score
    match_reason TEXT,         -- AI explanation of match
    contact_info JSON,         -- Extracted contact information
    requirements_summary TEXT, -- AI-parsed requirements
    application_complexity VARCHAR(50), -- Simple, Moderate, Complex
    ai_summary TEXT,          -- AI-generated summary
    last_intelligence_update TIMESTAMP,
    
    -- Workflow Management
    application_stage VARCHAR(50) DEFAULT 'discovery', -- 8-stage workflow
    priority_level VARCHAR(20) DEFAULT 'medium',       -- high, medium, low
    checklist JSON,           -- Stage-specific tasks
    team_members JSON,        -- Assigned collaborators
    activity_log JSON,        -- Audit trail
    requirements JSON,        -- Detailed requirements data
    
    -- Extended Metadata (for complex grants)
    user_id INTEGER,
    grant_name TEXT,          -- Alternative title
    funding_organization TEXT, -- Alternative funder name
    grant_amount DECIMAL(15,2), -- Single amount field
    submission_deadline DATE,   -- Alternative deadline
    date_submitted DATE,
    date_decision DATE,
    search_query TEXT,         -- Discovery search terms
    discovery_method VARCHAR(100),
    contact_name VARCHAR(200),
    contact_email VARCHAR(200),
    contact_phone VARCHAR(50),
    submission_url TEXT,
    application_process TEXT,
    grant_cycle VARCHAR(100),
    discovered_at TIMESTAMP,
    tags JSON,
    contact_department VARCHAR(200),
    organization_website VARCHAR(500),
    application_url TEXT,
    alternate_contact VARCHAR(300),
    contact_verified_date DATE,
    contact_confidence VARCHAR(20)
);

-- Foundation grants from premium 70-source scraper
CREATE TABLE denominational_grants (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255),  -- Unique identifier for deduplication
    title VARCHAR(500),
    funder VARCHAR(300),
    source_name VARCHAR(200),
    source_url TEXT,
    link TEXT,
    amount_min DECIMAL(15,2),
    amount_max DECIMAL(15,2),
    deadline DATE,
    geography VARCHAR(200),
    eligibility TEXT,
    description TEXT,
    requirements TEXT,
    contact_info JSONB,        -- Structured contact data
    ai_enhanced_data JSONB,    -- AI analysis results
    scrape_metadata JSONB,     -- Scraping technical metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    scraped_at TIMESTAMP
);
```

#### AI & Analytics System
```sql
-- AI service usage tracking
CREATE TABLE ai_usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    model_used VARCHAR(50),    -- gpt-4o, gpt-3.5-turbo, etc.
    tokens_used INTEGER,
    cost_usd DECIMAL(10,4),
    operation_type VARCHAR(100), -- match, generate, analyze, etc.
    processing_time_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Analytics events for business intelligence  
CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100),   -- login, grant_view, match_run, etc.
    event_data JSON,          -- Structured event details
    user_id INTEGER,
    org_id INTEGER,
    grant_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Grant success tracking
CREATE TABLE grant_success_metrics (
    id SERIAL PRIMARY KEY,
    grant_id INTEGER REFERENCES grants(id),
    organization_id INTEGER,
    application_submitted_date DATE,
    decision_date DATE,
    award_amount DECIMAL(15,2),
    decision_outcome VARCHAR(50), -- awarded, declined, pending
    match_score_at_application DECIMAL(3,1), -- Match score when applied
    time_spent_hours DECIMAL(8,2),
    success_factors JSON,     -- Why it succeeded/failed
    lessons_learned TEXT,
    follow_up_opportunities JSON,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Workflow & Collaboration
```sql
-- 8-stage grant workflow tracking
CREATE TABLE workflow_stages (
    id SERIAL PRIMARY KEY,
    grant_id INTEGER REFERENCES grants(id),
    stage_name VARCHAR(50),    -- discovery, researching, writing, etc.
    status VARCHAR(20),        -- active, completed, skipped
    entered_at TIMESTAMP,
    completed_at TIMESTAMP,
    assigned_to INTEGER REFERENCES users(id),
    notes TEXT,
    checklist_items JSON,
    stage_data JSON,          -- Stage-specific data
    estimated_duration_hours INTEGER,
    actual_duration_hours INTEGER
);

-- Team collaboration system
CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER,
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(50),         -- admin, manager, writer, reviewer
    permissions JSON,         -- Granular permissions
    invitation_status VARCHAR(20), -- invited, accepted, declined
    invited_by INTEGER REFERENCES users(id),
    invited_at TIMESTAMP,
    joined_at TIMESTAMP,
    last_active TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

---

## 🔐 Authentication & User Management

### Authentication Flow Logic
```python
# app/services/auth_service.py
class AuthService:
    """Custom session-based authentication without flask-login dependency"""
    
    @staticmethod
    def register_user(email, password, **profile_data):
        """Complete user registration with profile creation"""
        # 1. Validate email uniqueness
        if User.query.filter_by(email=email).first():
            return {'error': 'Email already registered'}
        
        # 2. Create user with hashed password
        user = User(
            email=email,
            username=email.split('@')[0],  # Generate username from email
            **profile_data
        )
        user.set_password(password)  # Werkzeug password hashing
        
        # 3. Generate verification token
        user.verification_token = secrets.token_urlsafe(32)
        user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        
        # 4. Save to database
        db.session.add(user)
        db.session.commit()
        
        # 5. Create session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['org_name'] = user.org_name
        
        return {'success': True, 'user': user.to_dict()}
    
    @staticmethod
    def login_user(email, password):
        """Authenticate and create session"""
        # 1. Find user by email
        user = User.query.filter_by(email=email).first()
        
        # 2. Verify password
        if not user or not user.check_password(password):
            return {'error': 'Invalid email or password'}
        
        # 3. Check if account is active
        if not user.is_active:
            return {'error': 'Account is disabled'}
        
        # 4. Create session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['org_name'] = user.org_name
        
        # 5. Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return {'success': True, 'user': user.to_dict()}
    
    @staticmethod
    def require_login(f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return decorated_function
```

### 3-Step Smart Onboarding System
```python
# app/services/onboarding_service.py
class SmartOnboarding:
    """Progressive profile building with live grant previews"""
    
    STEPS = [
        {
            'id': 'basic_info',
            'title': 'Organization Basics',
            'duration_minutes': 2,
            'required_fields': ['org_name', 'mission_statement', 'city', 'state'],
            'ai_benefit': 'Geographic grant matching'
        },
        {
            'id': 'focus_areas',
            'title': 'Programs & Focus Areas', 
            'duration_minutes': 3,
            'required_fields': ['focus_areas', 'target_populations'],
            'ai_benefit': 'Program-specific grant matching'
        },
        {
            'id': 'capacity',
            'title': 'Grant History & Capacity',
            'duration_minutes': 2,
            'required_fields': ['annual_budget', 'past_funders', 'grant_experience'],
            'ai_benefit': 'Match complexity and funder relationships'
        }
    ]
    
    def get_live_preview_grants(self, partial_profile):
        """Show grant previews as user fills profile"""
        from app.services.ai_grant_matcher import AIGrantMatcher
        
        # Run AI matching with partial data
        matcher = AIGrantMatcher()
        preview_grants = matcher.find_matches(
            profile_data=partial_profile,
            limit=3,
            preview_mode=True
        )
        
        return [
            {
                'title': grant.title,
                'funder': grant.funder, 
                'match_score': grant.match_score,
                'why_matched': grant.match_reason[:100] + '...'
            }
            for grant in preview_grants
        ]
```

---

## 📊 Grant Data Collection System

### Multi-Source Data Architecture
```python
# app/services/apiManager.py
class APIManager:
    """Unified manager for all grant data sources"""
    
    def __init__(self):
        self.sources = {
            # Government Sources (No API keys required)
            'grants_gov': GrantsGovClient(),
            'federal_register': FederalRegisterClient(),
            'govinfo': GovInfoClient(),
            
            # Premium APIs (Require credentials)
            'candid_grants': CandidGrantsClient(),    # 29M historical grants
            'candid_news': CandidNewsClient(),        # Foundation news
            'candid_essentials': CandidEssentialsClient(), # Org profiles
            'sam_gov': SAMGovClient(),                # Federal contracts
            
            # RSS & Scraping Sources  
            'pnd_rss': PNDClient(),                   # Philanthropy News Digest
            'foundation_scraper': ComprehensiveGrantScraper(), # 70 foundations
            
            # Regional Sources
            'michigan_socrata': MichiganSocrataClient(),
            'georgia_portal': GeorgiaPortalClient()
        }
        
        self.circuit_breakers = {
            name: CircuitBreaker(name) for name in self.sources.keys()
        }
    
    def collect_all_grants(self, keywords=None, days_back=30):
        """Collect grants from all active sources"""
        all_grants = []
        
        for source_name, client in self.sources.items():
            if not self.circuit_breakers[source_name].can_execute():
                logger.warning(f"Circuit breaker OPEN for {source_name}")
                continue
                
            try:
                logger.info(f"Collecting from {source_name}")
                grants = client.get_grants(keywords=keywords, days_back=days_back)
                
                # Standardize grant format
                standardized = [
                    self.standardize_grant(grant, source_name) 
                    for grant in grants
                ]
                all_grants.extend(standardized)
                
                # Circuit breaker success
                self.circuit_breakers[source_name].record_success()
                
            except Exception as e:
                # Circuit breaker failure
                self.circuit_breakers[source_name].record_failure()
                logger.error(f"Failed to collect from {source_name}: {e}")
        
        return self.deduplicate_grants(all_grants)
```

### 70-Foundation Scraper System
```python  
# app/services/comprehensive_grant_scraper.py
class ComprehensiveGrantScraper:
    """Scrapes 70+ foundation websites for grant opportunities"""
    
    FOUNDATION_SOURCES = {
        # Tech/AI Philanthropy (20 sources)
        'patrick_mcgovern': {
            'name': 'Patrick J. McGovern Foundation',
            'url': 'https://www.mcgovern.org/grants',
            'focus': 'AI for social good, digital equity'
        },
        'schmidt_sciences': {
            'name': 'Schmidt Sciences AI2050',
            'url': 'https://www.schmidtsciences.org/ai2050',
            'focus': 'AI research and applications'
        },
        
        # Regional Foundation Networks
        'grand_rapids_community': {
            'name': 'Grand Rapids Community Foundation', 
            'url': 'https://www.grfoundation.org/grants',
            'region': 'Michigan'
        },
        'woodruff_foundation': {
            'name': 'Robert W. Woodruff Foundation',
            'url': 'https://woodruff.org/grants',
            'region': 'Georgia'
        },
        
        # Faith-based Foundations (25 sources)
        'lilly_endowment': {
            'name': 'Lilly Endowment, Inc.',
            'url': 'https://www.lillyendowment.org/grants',
            'focus': 'Religion, community development, education'
        }
        # ... 65 more sources
    }
    
    async def scrape_all_foundations(self):
        """Scrape all 70 foundation sources"""
        results = []
        
        # Use asyncio for parallel scraping
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
        
        async def scrape_source(source_id, config):
            async with semaphore:
                try:
                    grants = await self.scrape_foundation(source_id, config)
                    logger.info(f"{source_id}: Found {len(grants)} grants")
                    return grants
                except Exception as e:
                    logger.error(f"{source_id}: Scraping failed - {e}")
                    return []
        
        # Execute all scraping tasks
        tasks = [
            scrape_source(source_id, config) 
            for source_id, config in self.FOUNDATION_SOURCES.items()
        ]
        
        scrape_results = await asyncio.gather(*tasks)
        
        # Flatten and save results
        for grants in scrape_results:
            results.extend(grants)
        
        # Save to denominational_grants table
        self.save_to_database(results)
        
        return {
            'total_grants': len(results),
            'sources_processed': len(self.FOUNDATION_SOURCES),
            'success_rate': f"{sum(1 for r in scrape_results if r) / len(scrape_results) * 100:.1f}%"
        }
```

### Automated Collection Schedule
```python
# server/services/scheduledScraper.js
class ScheduledScraper {
    /**
     * 3-day automated collection schedule
     * Ensures fresh grant data without overwhelming sources
     */
    
    constructor() {
        this.schedule = {
            // Day 1: Government & RSS sources (fast, reliable)
            government_day: {
                frequency: 'daily',
                sources: ['grants_gov', 'federal_register', 'pnd_rss'],
                time: '06:00'  // 6 AM UTC
            },
            
            // Day 2: Premium APIs (rate-limited)  
            premium_day: {
                frequency: 'every_3_days', 
                sources: ['candid_grants', 'candid_news', 'candid_essentials'],
                time: '08:00'  // 8 AM UTC
            },
            
            // Day 3: Foundation scraping (intensive)
            scraping_day: {
                frequency: 'every_3_days',
                sources: ['foundation_scraper'],
                time: '10:00',  // 10 AM UTC
                max_duration_hours: 4
            }
        }
    }
    
    async runScheduledCollection() {
        const today = new Date().getDay(); // 0=Sunday, 1=Monday, etc.
        
        switch(today) {
            case 1:  // Monday - Government sources
                await this.collectGovernmentSources();
                break;
            case 3:  // Wednesday - Premium APIs  
                await this.collectPremiumAPIs();
                break;
            case 5:  // Friday - Foundation scraping
                await this.runFoundationScraping();
                break;
            default:
                console.log('No collection scheduled for today');
        }
    }
}
```

---

## 🤖 AI Matching Engine

### REACTO Prompt Engineering System
```python
# app/services/reacto_prompt_service.py
class ReactoPromptService:
    """Industry-leading 6-section prompt engineering for 3-5x better results"""
    
    def generate_grant_match_prompt(self, grant, organization):
        """Generate REACTO prompt for grant-organization matching"""
        
        return f"""
**R - ROLE**: You are a senior grant strategist with 15+ years experience matching nonprofits to foundation funding. You understand funder priorities, application requirements, and success factors that lead to awards.

**E - EXAMPLE**: Here's what an excellent match analysis looks like:

GRANT: $50K Community Health Initiative - Kresge Foundation
ORGANIZATION: Detroit Urban Health Center - Focus: community health, underserved populations
MATCH SCORE: 4.2/5.0

KEY ALIGNMENTS:
- Mission alignment: Organization's community health focus directly matches funder's health equity priorities
- Geographic fit: Detroit location aligns with Kresge's Midwest focus 
- Budget range: $50K request fits organization's $200K annual budget and past awards
- Program model: Community-based approach matches funder's grassroots investment strategy

CHALLENGES TO CONSIDER:
- Competition: Kresge receives 500+ health proposals annually
- Requirements: Requires detailed community impact metrics (organization should strengthen data collection)
- Timeline: 90-day application process requires dedicated staff time

STRATEGIC NEXT STEPS:
1. Review past Kresge awards to similar organizations (research competitive landscape)
2. Strengthen community partnership documentation 
3. Prepare detailed health outcome metrics for application

**A - APPLICATION**: Analyze the match between this grant and organization using these exact steps:

STEP 1: Mission Alignment Analysis
- Compare grant focus areas to organization's mission and programs
- Identify direct overlaps and potential gaps
- Rate mission alignment 1-5 (5 = perfect match)

STEP 2: Feasibility Assessment  
- Compare grant amount to organization budget and capacity
- Evaluate application complexity vs. organization experience
- Check geographic and eligibility requirements

STEP 3: Competitive Analysis
- Assess likelihood of success based on funder patterns
- Identify competitive advantages organization has
- Note potential weaknesses compared to typical winners

STEP 4: Strategic Recommendations
- List 3-5 specific actions to strengthen application
- Identify potential red flags or deal-breakers
- Suggest timeline and resource allocation

GUARDRAILS:
- Base analysis only on factual information provided
- Don't fabricate funder preferences or requirements
- Flag any missing information needed for complete analysis
- Provide specific, actionable recommendations

**C - CONTEXT**: 
GRANT DETAILS:
Title: {grant.title}
Funder: {grant.funder}
Amount Range: ${grant.amount_min:,} - ${grant.amount_max:,}
Deadline: {grant.deadline}
Focus Areas: {grant.description[:500]}
Requirements: {grant.eligibility}

ORGANIZATION PROFILE:
Name: {organization.legal_name}
Mission: {organization.mission_statement}
Annual Budget: ${organization.annual_budget:,}
Focus Areas: {organization.focus_areas}
Location: {organization.city}, {organization.state}
Past Funders: {organization.past_funders}
Grant Experience: {organization.grant_history_summary}

**T - TONE**: Professional yet accessible. Write as an expert advisor speaking to an experienced nonprofit leader. Use confident language for strong matches, cautious language for questionable fits. Include specific details and actionable insights rather than generic advice.

**O - OUTPUT**: Provide your analysis in exactly this format:

MATCH SCORE: [X.X/5.0]

KEY ALIGNMENTS:
- [Specific alignment point 1 with evidence]
- [Specific alignment point 2 with evidence]
- [Specific alignment point 3 with evidence]

CHALLENGES TO CONSIDER:
- [Challenge 1 with context]
- [Challenge 2 with context]
- [Challenge 3 with context]

STRATEGIC NEXT STEPS:
1. [Specific action with timeline]
2. [Specific action with timeline] 
3. [Specific action with timeline]

CONFIDENCE LEVEL: [High/Medium/Low] - [Brief explanation]

TESTING VALIDATION:
- Verify all claims are based on provided information
- Check that match score aligns with evidence presented
- Ensure recommendations are specific and actionable
- Confirm tone is professional yet accessible
"""

    def generate_narrative_prompt(self, grant, organization, section_type):
        """Generate REACTO prompt for grant narrative writing"""
        # Similar detailed REACTO structure for narrative generation
        # ... (detailed prompt structure)
```

### AI Cost Optimizer
```python
# app/services/ai_optimizer_service.py
class AIOptimizerService:
    """Intelligent model routing for 30-60% cost reduction"""
    
    MODEL_COSTS = {
        'gpt-4o': {'input': 0.01, 'output': 0.03},      # $0.01/1K input tokens
        'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002}  # $0.0015/1K input tokens
    }
    
    def select_optimal_model(self, task_type, complexity_indicators):
        """Choose best model based on task complexity and cost"""
        
        # Define complexity scoring
        complexity_score = self.calculate_complexity_score({
            'text_length': len(complexity_indicators.get('text', '')),
            'analysis_depth': complexity_indicators.get('analysis_depth', 'basic'),
            'creativity_required': complexity_indicators.get('creativity', False),
            'accuracy_critical': complexity_indicators.get('accuracy_critical', False),
            'context_length': complexity_indicators.get('context_length', 0)
        })
        
        # Model selection logic
        if complexity_score >= 7:
            # Complex tasks: Use GPT-4o
            return 'gpt-4o'
        elif complexity_score >= 4:
            # Medium complexity: Cost-benefit analysis
            estimated_4o_cost = self.estimate_cost('gpt-4o', complexity_indicators)
            estimated_35_cost = self.estimate_cost('gpt-3.5-turbo', complexity_indicators)
            
            if estimated_4o_cost < estimated_35_cost * 2:  # If 4o is <2x cost, use it
                return 'gpt-4o'
            else:
                return 'gpt-3.5-turbo'
        else:
            # Simple tasks: Always use 3.5-turbo
            return 'gpt-3.5-turbo'
    
    def calculate_complexity_score(self, indicators):
        """Score task complexity 1-10"""
        score = 0
        
        # Text length factor
        if indicators['text_length'] > 5000:
            score += 3
        elif indicators['text_length'] > 2000:
            score += 2
        elif indicators['text_length'] > 500:
            score += 1
        
        # Analysis depth factor
        depth_scores = {'basic': 0, 'standard': 2, 'detailed': 4, 'comprehensive': 6}
        score += depth_scores.get(indicators['analysis_depth'], 0)
        
        # Special requirements
        if indicators['creativity_required']:
            score += 2
        if indicators['accuracy_critical']:
            score += 2
        if indicators['context_length'] > 10000:
            score += 1
        
        return min(score, 10)  # Cap at 10
```

### Grant Matching Logic Flow
```python
# app/services/ai_grant_matcher.py  
class AIGrantMatcher:
    """Core AI matching engine"""
    
    def find_matches(self, organization_profile, limit=20):
        """Find and score grant matches for an organization"""
        
        # STEP 1: Pre-filtering (performance optimization)
        candidate_grants = self.pre_filter_grants(organization_profile)
        logger.info(f"Pre-filtered to {len(candidate_grants)} candidate grants")
        
        # STEP 2: AI matching with batch processing
        matched_grants = []
        
        # Process in batches to manage API costs
        for batch in self.batch_grants(candidate_grants, batch_size=10):
            batch_results = self.ai_match_batch(batch, organization_profile)
            matched_grants.extend(batch_results)
        
        # STEP 3: Sort by match score and return top results
        matched_grants.sort(key=lambda x: x.match_score, reverse=True)
        return matched_grants[:limit]
    
    def pre_filter_grants(self, profile):
        """Fast SQL-based filtering before expensive AI analysis"""
        filters = []
        
        # Geographic filtering
        if profile.get('state'):
            filters.append(
                Grant.geography.contains(profile['state']) |
                Grant.geography.contains('National') |
                Grant.geography.is_(None)
            )
        
        # Budget range filtering  
        if profile.get('annual_budget'):
            budget = profile['annual_budget']
            filters.append(
                (Grant.amount_min <= budget * 0.5) |  # Grant is reasonable size
                Grant.amount_min.is_(None)
            )
        
        # Focus area keyword filtering
        if profile.get('focus_areas'):
            focus_keywords = ' '.join(profile['focus_areas'])
            filters.append(
                Grant.title.ilike(f'%{focus_keywords}%') |
                Grant.description.ilike(f'%{focus_keywords}%')
            )
        
        # Apply filters
        query = Grant.query
        for filter_condition in filters:
            query = query.filter(filter_condition)
        
        return query.all()
    
    def ai_match_batch(self, grants, profile):
        """AI analysis for a batch of grants"""
        results = []
        
        for grant in grants:
            # Use AI Optimizer to select model
            complexity = self.assess_matching_complexity(grant, profile)
            model = self.ai_optimizer.select_optimal_model('matching', complexity)
            
            # Generate REACTO prompt
            prompt = self.reacto_service.generate_grant_match_prompt(grant, profile)
            
            # Get AI analysis
            response = self.ai_service.analyze_match(
                prompt=prompt,
                model=model,
                temperature=0.3  # Lower temperature for consistent scoring
            )
            
            # Parse AI response and update grant
            match_data = self.parse_ai_match_response(response)
            grant.match_score = match_data['score']
            grant.match_reason = match_data['reasoning']
            grant.ai_summary = match_data['summary']
            
            results.append(grant)
        
        return results
```

---

## 🔧 API Integration Framework

### Circuit Breaker Pattern Implementation
```python
# app/services/apiManager.py
class CircuitBreaker:
    """Prevents system crashes from API failures"""
    
    def __init__(self, source_name, failure_threshold=5, cooldown_minutes=15):
        self.source_name = source_name
        self.failure_threshold = failure_threshold
        self.cooldown_period = timedelta(minutes=cooldown_minutes)
        
        # State tracking
        self.state = CircuitBreakerState.CLOSED  # CLOSED = normal operation
        self.failure_count = 0
        self.last_failure_time = None
        
    def can_execute(self):
        """Check if API calls are allowed"""
        now = datetime.now()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True  # Normal operation
            
        elif self.state == CircuitBreakerState.OPEN:
            # Check if cooldown period has passed
            if self.last_failure_time and (now - self.last_failure_time) > self.cooldown_period:
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info(f"Circuit breaker for {self.source_name} moving to HALF_OPEN")
                return True
            return False  # Still cooling down
            
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True  # Testing if service recovered
    
    def record_success(self):
        """Record successful API call"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            # Service has recovered
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            logger.info(f"Circuit breaker for {self.source_name} CLOSED - service recovered")
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record failed API call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker for {self.source_name} OPENED after {self.failure_count} failures")
```

### Credential Management System
```python
# app/services/credential_manager.py
class CredentialManager:
    """Manages API keys with validation and fallback handling"""
    
    CREDENTIAL_CONFIGS = {
        # Premium APIs
        'candid_grants': {
            'primary_env': 'CANDID_GRANTS_KEY',
            'fallbacks': ['CANDID_GRANTS_KEYS', 'CANDID_API_KEY'],
            'validation_pattern': r'^[a-f0-9]{32}$',
            'priority': 'HIGH',
            'description': 'Candid Grants API for 29M grant database access'
        },
        'sam_gov': {
            'primary_env': 'SAM_GOV_API_KEY', 
            'fallbacks': ['SAM_API_KEY', 'SAMGOV_KEY'],
            'validation_pattern': r'^[A-Za-z0-9_-]{32,}$',
            'priority': 'HIGH',
            'description': 'SAM.gov API for federal opportunities'
        },
        'openai': {
            'primary_env': 'OPENAI_API_KEY',
            'fallbacks': ['OPENAI_KEY', 'AI_API_KEY'],
            'validation_pattern': r'^sk-[A-Za-z0-9]{48,}$',
            'priority': 'CRITICAL',
            'description': 'OpenAI GPT API for AI matching and writing'
        }
    }
    
    def get_credential(self, service_name):
        """Get validated credential with fallback support"""
        config = self.CREDENTIAL_CONFIGS.get(service_name)
        if not config:
            return None
        
        # Try primary environment variable
        credential = os.environ.get(config['primary_env'])
        
        # Try fallback environment variables
        if not credential:
            for fallback in config['fallbacks']:
                credential = os.environ.get(fallback)
                if credential:
                    logger.info(f"Using fallback credential for {service_name}: {fallback}")
                    break
        
        # Validate credential format
        if credential and config.get('validation_pattern'):
            if not re.match(config['validation_pattern'], credential):
                logger.error(f"Invalid credential format for {service_name}")
                return None
        
        return credential
    
    def get_credential_status_report(self):
        """Generate comprehensive credential status report"""
        report = {
            'critical_missing': [],
            'high_missing': [],
            'available': [],
            'invalid': []
        }
        
        for service, config in self.CREDENTIAL_CONFIGS.items():
            credential = self.get_credential(service)
            
            if not credential:
                if config['priority'] == 'CRITICAL':
                    report['critical_missing'].append({
                        'service': service,
                        'description': config['description'],
                        'setup_required': config['primary_env']
                    })
                elif config['priority'] == 'HIGH':
                    report['high_missing'].append({
                        'service': service,
                        'description': config['description'],
                        'setup_required': config['primary_env']
                    })
            else:
                # Test credential validity
                if self.test_credential(service, credential):
                    report['available'].append(service)
                else:
                    report['invalid'].append(service)
        
        return report
```

### Rate Limiting & Caching Strategy
```python
# app/services/cache_service.py
class IntelligentCacheService:
    """Smart caching with TTL based on data volatility"""
    
    CACHE_STRATEGIES = {
        # High-volatility data: Short TTL
        'grant_search': {'ttl': 300, 'strategy': 'LRU'},      # 5 minutes
        'ai_matching': {'ttl': 1800, 'strategy': 'LFU'},     # 30 minutes
        
        # Medium-volatility data: Medium TTL
        'grant_details': {'ttl': 3600, 'strategy': 'LRU'},   # 1 hour
        'organization_profile': {'ttl': 7200, 'strategy': 'LRU'}, # 2 hours
        
        # Low-volatility data: Long TTL
        'funder_profiles': {'ttl': 86400, 'strategy': 'LFU'}, # 24 hours
        'static_references': {'ttl': 604800, 'strategy': 'LFU'} # 1 week
    }
    
    def __init__(self):
        # Try Redis first, fallback to memory
        try:
            import redis
            self.redis_client = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
            self.redis_client.ping()  # Test connection
            self.backend = 'redis'
            logger.info("Cache service initialized with Redis backend")
        except:
            self.memory_cache = {}
            self.backend = 'memory'
            logger.warning("Cache service using memory fallback - Redis not available")
    
    def get_cached_result(self, cache_key, data_type='grant_search'):
        """Retrieve cached result with intelligent TTL"""
        try:
            if self.backend == 'redis':
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            else:
                # Memory cache with expiry
                if cache_key in self.memory_cache:
                    cached_item = self.memory_cache[cache_key]
                    if cached_item['expires_at'] > time.time():
                        return cached_item['data']
                    else:
                        del self.memory_cache[cache_key]
            
            return None
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
    
    def set_cached_result(self, cache_key, data, data_type='grant_search'):
        """Store result with appropriate TTL"""
        strategy = self.CACHE_STRATEGIES.get(data_type, self.CACHE_STRATEGIES['grant_search'])
        ttl = strategy['ttl']
        
        try:
            if self.backend == 'redis':
                self.redis_client.setex(
                    cache_key, 
                    ttl, 
                    json.dumps(data, default=str)  # Handle datetime serialization
                )
            else:
                # Memory cache with manual expiry
                self.memory_cache[cache_key] = {
                    'data': data,
                    'expires_at': time.time() + ttl
                }
                
                # Prevent memory cache from growing too large
                if len(self.memory_cache) > 1000:
                    self.evict_oldest_entries()
                    
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
```

---

## 🔄 Workflow Management

### 8-Stage Grant Workflow System
```python
# app/services/workflow_service.py
class WorkflowService:
    """Manages the complete 8-stage grant lifecycle"""
    
    WORKFLOW_STAGES = [
        {
            'id': 'discovery',
            'name': 'Discovery',
            'description': 'Finding and evaluating grant opportunities',
            'typical_duration_hours': 2,
            'required_actions': ['search_grants', 'review_matches', 'select_opportunities'],
            'auto_transitions': True,
            'color': '#3B82F6',  # Blue
            'icon': '🔍'
        },
        {
            'id': 'researching', 
            'name': 'Researching',
            'description': 'Deep dive into funder requirements and strategy',
            'typical_duration_hours': 8,
            'required_actions': ['analyze_requirements', 'research_funder', 'develop_strategy'],
            'auto_transitions': False,
            'color': '#8B5CF6',  # Purple  
            'icon': '📚'
        },
        {
            'id': 'writing',
            'name': 'Writing', 
            'description': 'Drafting proposal narratives and materials',
            'typical_duration_hours': 20,
            'required_actions': ['draft_narrative', 'gather_documents', 'review_draft'],
            'auto_transitions': False,
            'color': '#10B981',  # Green
            'icon': '✍️'
        },
        {
            'id': 'review',
            'name': 'Review',
            'description': 'Internal review and final preparation', 
            'typical_duration_hours': 4,
            'required_actions': ['internal_review', 'final_edits', 'prepare_submission'],
            'auto_transitions': False,
            'color': '#F59E0B',  # Orange
            'icon': '👥'
        },
        {
            'id': 'submitted',
            'name': 'Submitted',
            'description': 'Application submitted, awaiting response',
            'typical_duration_hours': 0,  # Passive waiting stage
            'required_actions': ['submit_application', 'send_confirmation', 'set_follow_up'],
            'auto_transitions': True,
            'color': '#6366F1',  # Indigo
            'icon': '📤'
        },
        {
            'id': 'pending',
            'name': 'Pending Decision',
            'description': 'Under funder review, may require follow-up',
            'typical_duration_hours': 0,
            'required_actions': ['track_status', 'respond_to_questions', 'maintain_contact'],
            'auto_transitions': False,
            'color': '#EF4444',  # Red
            'icon': '⏳'
        },
        {
            'id': 'awarded',
            'name': 'Awarded',
            'description': 'Grant awarded, moving to implementation',
            'typical_duration_hours': 2,
            'required_actions': ['celebrate_success', 'plan_implementation', 'setup_reporting'],
            'auto_transitions': False,
            'color': '#059669',  # Emerald
            'icon': '🎉'
        },
        {
            'id': 'declined',
            'name': 'Declined',
            'description': 'Application not successful, capture learnings',
            'typical_duration_hours': 1,
            'required_actions': ['request_feedback', 'document_lessons', 'plan_next_steps'],
            'auto_transitions': False,
            'color': '#DC2626',  # Red
            'icon': '📝'
        }
    ]
    
    def move_grant_to_stage(self, grant_id, new_stage_id, user_id, notes=None):
        """Move grant to new workflow stage"""
        
        # Validate stage transition
        current_stage = self.get_grant_current_stage(grant_id)
        if not self.is_valid_transition(current_stage, new_stage_id):
            return {'error': f'Invalid transition from {current_stage} to {new_stage_id}'}
        
        # Update grant record
        grant = Grant.query.get(grant_id)
        if not grant:
            return {'error': 'Grant not found'}
        
        # Create workflow stage record
        stage_record = WorkflowStage(
            grant_id=grant_id,
            stage_name=new_stage_id,
            status='active',
            entered_at=datetime.utcnow(),
            assigned_to=user_id,
            notes=notes
        )
        
        # Complete previous stage
        if current_stage:
            prev_stage = WorkflowStage.query.filter_by(
                grant_id=grant_id,
                stage_name=current_stage,
                status='active'
            ).first()
            if prev_stage:
                prev_stage.status = 'completed'
                prev_stage.completed_at = datetime.utcnow()
        
        # Update grant application_stage
        grant.application_stage = new_stage_id
        
        # Add to activity log
        self.add_activity_log(grant_id, f"Moved to {new_stage_id}", user_id, notes)
        
        # Generate stage-specific checklist
        checklist = self.generate_stage_checklist(new_stage_id, grant)
        stage_record.checklist_items = checklist
        
        # Save changes
        db.session.add(stage_record)
        db.session.commit()
        
        # Trigger stage-specific actions
        self.trigger_stage_actions(grant, new_stage_id)
        
        return {'success': True, 'new_stage': new_stage_id}
    
    def generate_stage_checklist(self, stage_id, grant):
        """Generate dynamic checklist based on stage and grant details"""
        stage_config = next(s for s in self.WORKFLOW_STAGES if s['id'] == stage_id)
        base_actions = stage_config['required_actions']
        
        # Customize checklist based on grant specifics
        checklist = []
        for action in base_actions:
            if action == 'analyze_requirements':
                checklist.append({
                    'id': 'requirements_analysis',
                    'title': f'Analyze {grant.funder} requirements',
                    'description': 'Review eligibility, budget, and application process',
                    'estimated_hours': 2,
                    'completed': False
                })
            elif action == 'research_funder':
                checklist.append({
                    'id': 'funder_research', 
                    'title': f'Research {grant.funder} giving patterns',
                    'description': 'Study past awards, funding priorities, and decision makers',
                    'estimated_hours': 3,
                    'completed': False
                })
            # ... more dynamic checklist generation
        
        return checklist
    
    def get_workflow_analytics(self, organization_id):
        """Get workflow performance analytics"""
        
        # Get all grants for organization
        grants = Grant.query.filter_by(org_id=organization_id).all()
        
        analytics = {
            'total_grants': len(grants),
            'stage_distribution': {},
            'average_stage_durations': {},
            'success_metrics': {
                'submitted_rate': 0,
                'award_rate': 0,
                'pipeline_value': 0
            }
        }
        
        # Calculate stage distribution
        for grant in grants:
            stage = grant.application_stage
            analytics['stage_distribution'][stage] = analytics['stage_distribution'].get(stage, 0) + 1
        
        # Calculate success rates
        submitted_count = len([g for g in grants if g.application_stage in ['submitted', 'pending', 'awarded', 'declined']])
        awarded_count = len([g for g in grants if g.application_stage == 'awarded'])
        
        if len(grants) > 0:
            analytics['success_metrics']['submitted_rate'] = (submitted_count / len(grants)) * 100
        if submitted_count > 0:
            analytics['success_metrics']['award_rate'] = (awarded_count / submitted_count) * 100
        
        # Calculate pipeline value
        pipeline_grants = [g for g in grants if g.application_stage in ['discovery', 'researching', 'writing', 'review']]
        analytics['success_metrics']['pipeline_value'] = sum(
            (g.amount_max or g.amount_min or 0) for g in pipeline_grants
        )
        
        return analytics
```

---

## 💳 Payment & Subscription System

### Stripe Integration Architecture
```python
# app/services/stripe_service.py
class StripeService:
    """Complete Stripe payment processing integration"""
    
    SUBSCRIPTION_PLANS = {
        'starter': {
            'price_id': 'price_starter_monthly',
            'amount': 7900,  # $79.00 in cents
            'currency': 'usd',
            'interval': 'month',
            'features': [
                'Up to 100 grant matches per month',
                'Basic AI writing assistance', 
                'Standard workflow management',
                'Email support'
            ]
        },
        'professional': {
            'price_id': 'price_professional_monthly',
            'amount': 19900,  # $199.00 in cents  
            'currency': 'usd',
            'interval': 'month',
            'features': [
                'Up to 500 grant matches per month',
                'Advanced AI writing & analysis',
                'Team collaboration (5 users)',
                'Analytics dashboard',
                'Priority support'
            ]
        },
        'enterprise': {
            'price_id': 'price_enterprise_monthly',
            'amount': 49900,  # $499.00 in cents
            'currency': 'usd', 
            'interval': 'month',
            'features': [
                'Unlimited grant matches',
                'Full AI suite with custom prompts',
                'Unlimited team members',
                'Advanced analytics & reporting',
                'Dedicated account manager',
                'Custom integrations'
            ]
        }
    }
    
    def __init__(self):
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        self.webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    def create_checkout_session(self, plan_id, user_id, success_url, cancel_url):
        """Create Stripe checkout session for subscription"""
        
        plan = self.SUBSCRIPTION_PLANS.get(plan_id)
        if not plan:
            raise ValueError(f'Invalid plan: {plan_id}')
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f'User not found: {user_id}')
        
        try:
            # Create or retrieve Stripe customer
            stripe_customer = self.get_or_create_stripe_customer(user)
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=stripe_customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan['price_id'],
                    'quantity': 1
                }],
                mode='subscription',
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                metadata={
                    'user_id': user_id,
                    'plan_id': plan_id,
                    'org_id': user.org_id
                },
                allow_promotion_codes=True,
                billing_address_collection='required',
                tax_id_collection={
                    'enabled': True
                }
            )
            
            return {
                'session_id': session.id,
                'checkout_url': session.url
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe checkout error: {e}")
            raise
    
    def handle_webhook(self, payload, signature):
        """Process Stripe webhook events"""
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
        except ValueError:
            raise ValueError('Invalid payload')
        except stripe.error.SignatureVerificationError:
            raise ValueError('Invalid signature')
        
        # Handle specific events
        if event['type'] == 'checkout.session.completed':
            self.handle_successful_payment(event['data']['object'])
            
        elif event['type'] == 'customer.subscription.created':
            self.handle_subscription_created(event['data']['object'])
            
        elif event['type'] == 'customer.subscription.updated':
            self.handle_subscription_updated(event['data']['object'])
            
        elif event['type'] == 'customer.subscription.deleted':
            self.handle_subscription_cancelled(event['data']['object'])
            
        elif event['type'] == 'invoice.payment_failed':
            self.handle_payment_failed(event['data']['object'])
            
        return {'status': 'success'}
    
    def handle_successful_payment(self, session):
        """Process successful subscription payment"""
        
        user_id = session['metadata']['user_id']
        plan_id = session['metadata']['plan_id']
        
        # Create subscription record
        subscription = Subscription(
            user_id=user_id,
            stripe_customer_id=session['customer'],
            stripe_subscription_id=session['subscription'],
            plan_id=plan_id,
            status='active',
            current_period_start=datetime.fromtimestamp(session.get('current_period_start', 0)),
            current_period_end=datetime.fromtimestamp(session.get('current_period_end', 0)),
            created_at=datetime.utcnow()
        )
        
        db.session.add(subscription)
        
        # Update user role
        user = User.query.get(user_id)
        user.subscription_status = 'active'
        user.subscription_plan = plan_id
        
        db.session.commit()
        
        # Send welcome email
        self.send_welcome_email(user, plan_id)
        
        # Log analytics event
        self.track_subscription_event('subscription_created', user_id, plan_id)
```

---

## 🖥️ Frontend Integration

### React Component Architecture
```javascript
// client/src/components/GrantMatcher.jsx
import React, { useState, useEffect } from 'react';
import { GrantCard } from './GrantCard';
import { MatchingFilters } from './MatchingFilters';
import { LoadingSpinner } from './ui/LoadingSpinner';

export const GrantMatcher = ({ organizationProfile }) => {
  const [grants, setGrants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    minScore: 3.0,
    amountRange: 'all',
    focusAreas: [],
    deadline: 'all'
  });

  const runMatching = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('/api/ai-grants/match', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          organization_profile: organizationProfile,
          filters: filters,
          limit: 20
        })
      });
      
      if (!response.ok) {
        throw new Error('Matching failed');
      }
      
      const data = await response.json();
      setGrants(data.matches);
      
      // Track analytics
      trackEvent('grant_matching_completed', {
        matches_found: data.matches.length,
        avg_score: data.average_score,
        filters_used: filters
      });
      
    } catch (error) {
      console.error('Grant matching error:', error);
      setError('Failed to find grant matches. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grant-matcher">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          AI Grant Matching
        </h2>
        <button
          onClick={runMatching}
          disabled={loading}
          className="bg-pink-600 hover:bg-pink-700 text-white px-6 py-2 rounded-lg disabled:opacity-50"
        >
          {loading ? 'Finding Matches...' : 'Run AI Matching'}
        </button>
      </div>
      
      <MatchingFilters 
        filters={filters}
        onFiltersChange={setFilters}
      />
      
      {loading && (
        <div className="text-center py-12">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-gray-600">
            Analyzing {grants.length}+ grant opportunities...
          </p>
        </div>
      )}
      
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {grants.map(grant => (
          <GrantCard 
            key={grant.id}
            grant={grant}
            onStageChange={handleStageChange}
            showMatchDetails={true}
          />
        ))}
      </div>
      
      {grants.length === 0 && !loading && (
        <div className="text-center py-12">
          <p className="text-gray-500">
            No grants found. Try adjusting your filters or running matching first.
          </p>
        </div>
      )}
    </div>
  );
};
```

### API Integration Pattern
```javascript
// client/src/services/api.js
class APIService {
  constructor() {
    this.baseURL = '/api';
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: this.defaultHeaders,
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Grant Management
  async getGrants(filters = {}) {
    return this.request('/grants', {
      method: 'GET',
      headers: {
        ...this.defaultHeaders,
        'X-Requested-With': 'XMLHttpRequest'
      }
    });
  }

  async runAIMatching(organizationProfile, options = {}) {
    return this.request('/ai-grants/match', {
      method: 'POST',
      body: JSON.stringify({
        organization_profile: organizationProfile,
        ...options
      })
    });
  }

  async moveGrantToStage(grantId, newStage, notes = '') {
    return this.request('/workflow/move-stage', {
      method: 'POST',
      body: JSON.stringify({
        grant_id: grantId,
        new_stage: newStage,
        notes
      })
    });
  }

  // Analytics
  async getAnalytics(dateRange = '30d') {
    return this.request(`/analytics?range=${dateRange}`);
  }
}

export const apiService = new APIService();
```

---

## ☁️ Deployment & Infrastructure

### Replit Configuration
```toml
# .replit
modules = ["python-3.11", "postgresql-16", "nodejs-20"]

[nix]
channel = "stable-24_05"
packages = [
    "freetype", "geckodriver", "glibcLocales", "imagemagick", "jq",
    "lcms2", "libimagequant", "libjpeg", "libtiff", "libwebp", 
    "libxcrypt", "openjpeg", "openssl", "poetry", "postgresql",
    "python311Packages.flask", "python311Packages.flask-cors",
    "python311Packages.flask-sqlalchemy", "python311Packages.pytest",
    "python311Packages.requests", "python311Packages.sendgrid",
    "tcl", "tk", "zlib"
]

[deployment]
deploymentTarget = "autoscale"
run = ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]

[[workflows.workflow]]
name = "Start application"
author = "agent"

[[workflows.workflow.tasks]]
task = "shell.exec"
args = "gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app"
waitForPort = 5000
```

### Environment Variables Setup
```bash
# Core Application
SESSION_SECRET=your-secure-session-secret
DATABASE_URL=postgresql://user:pass@host:port/dbname

# AI Services
OPENAI_API_KEY=sk-your-openai-key-here

# Premium Data Sources  
CANDID_GRANTS_KEY=your-candid-grants-api-key
CANDID_NEWS_KEY=your-candid-news-api-key
CANDID_ESSENTIALS_KEY=your-candid-essentials-api-key
SAM_GOV_API_KEY=your-sam-gov-api-key
FDO_API_KEY=your-foundation-directory-key

# Payment Processing
STRIPE_SECRET_KEY=sk_live_or_test_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_stripe_webhook_secret

# Optional Services
REDIS_URL=redis://localhost:6379
SENDGRID_API_KEY=SG.your-sendgrid-key
ZYTE_API_KEY=your-zyte-scraping-key
```

### Production Deployment Flow
```python
# scripts/deploy.py
class ProductionDeployer:
    """Handles production deployment with safety checks"""
    
    def deploy(self):
        """Execute safe production deployment"""
        
        # Step 1: Pre-deployment health checks
        self.run_health_checks()
        
        # Step 2: Database migrations
        self.run_database_migrations()
        
        # Step 3: Static asset compilation
        self.compile_frontend_assets()
        
        # Step 4: Environment validation
        self.validate_environment()
        
        # Step 5: Deploy with zero downtime
        self.zero_downtime_deploy()
        
        # Step 6: Post-deployment verification
        self.verify_deployment()
        
        # Step 7: Enable monitoring
        self.enable_monitoring()
    
    def run_health_checks(self):
        """Verify system health before deployment"""
        checks = [
            self.check_database_connection(),
            self.check_external_apis(),
            self.check_redis_connection(),
            self.check_stripe_connection(),
            self.validate_environment_variables()
        ]
        
        if not all(checks):
            raise Exception("Health checks failed - aborting deployment")
    
    def run_database_migrations(self):
        """Apply database schema changes safely"""
        from flask_migrate import upgrade
        
        # Create database backup
        self.create_database_backup()
        
        try:
            # Apply migrations
            upgrade()
            logger.info("Database migrations completed successfully")
        except Exception as e:
            # Rollback on failure
            self.rollback_database_backup()
            raise e
```

---

## 🚨 Troubleshooting Guide

### Common Issues & Solutions

#### 1. Grant Count Drop (677 → Lower Number)
**Symptoms:**
- Fewer grants showing in dashboard
- Missing foundation or government grants
- Empty search results

**Diagnosis Steps:**
```python
# Check grant count by source
SELECT source_name, COUNT(*) as count 
FROM grants 
GROUP BY source_name 
ORDER BY count DESC;

# Check if denominational grants are merged
SELECT COUNT(*) FROM denominational_grants;

# Check recent scraping runs
SELECT * FROM denominational_scrape_runs 
ORDER BY created_at DESC LIMIT 5;
```

**Solutions:**
1. **Merge Foundation Grants:**
   ```sql
   INSERT INTO grants (title, funder, link, amount_min, amount_max, deadline, geography, eligibility, status, source_name, source_url, created_at, updated_at, application_stage, priority_level)
   SELECT title, funder, link, amount_min, amount_max, deadline, geography, eligibility, 'idea', source_name, source_url, created_at, updated_at, 'discovery', 'medium'
   FROM denominational_grants
   WHERE title IS NOT NULL AND funder IS NOT NULL;
   ```

2. **Restart Data Collection:**
   ```python
   from app.services.comprehensive_grant_scraper import ComprehensiveGrantScraper
   scraper = ComprehensiveGrantScraper()
   results = scraper.run_complete_scrape()
   ```

#### 2. AI Matching Failures  
**Symptoms:**
- Match scores showing as null
- Error "OpenAI API key invalid"
- Slow or failed AI responses

**Diagnosis:**
```python
# Check AI usage logs
SELECT model_used, success, error_message, COUNT(*) 
FROM ai_usage_logs 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY model_used, success, error_message;

# Test OpenAI connection
from app.services.ai_service import AIService
ai = AIService()
ai.test_connection()
```

**Solutions:**
1. **Verify API Key:**
   ```python
   import os
   print(f"OpenAI Key Present: {bool(os.environ.get('OPENAI_API_KEY'))}")
   print(f"Key Format Valid: {os.environ.get('OPENAI_API_KEY', '').startswith('sk-')}")
   ```

2. **Reset AI Matching:**
   ```python
   # Clear failed AI results
   UPDATE grants SET match_score = NULL, match_reason = NULL 
   WHERE match_score IS NULL OR match_reason IS NULL;
   
   # Re-run matching
   from app.services.ai_grant_matcher import AIGrantMatcher
   matcher = AIGrantMatcher()
   matcher.rematch_all_grants()
   ```

#### 3. Authentication Issues
**Symptoms:**
- Unable to login
- Session expires immediately
- "Authentication required" errors

**Solutions:**
1. **Check Session Secret:**
   ```python
   # Verify SESSION_SECRET is set
   print(f"Session Secret Present: {bool(os.environ.get('SESSION_SECRET'))}")
   
   # If missing, generate new one:
   import secrets
   new_secret = secrets.token_urlsafe(32)
   # Add to environment variables
   ```

2. **Clear Corrupted Sessions:**
   ```python
   from flask import session
   session.clear()
   ```

#### 4. Database Connection Problems
**Symptoms:**
- "Database connection failed"
- Slow query performance
- Connection timeout errors

**Solutions:**
1. **Check Database Status:**
   ```sql
   SELECT COUNT(*) FROM pg_stat_activity 
   WHERE state = 'active';
   
   SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
   FROM pg_stat_user_tables 
   ORDER BY n_tup_ins DESC;
   ```

2. **Optimize Connection Pool:**
   ```python
   # app/config.py
   SQLALCHEMY_ENGINE_OPTIONS = {
       "pool_recycle": 300,
       "pool_pre_ping": True,
       "pool_size": 10,
       "max_overflow": 20
   }
   ```

#### 5. Stripe Payment Failures
**Symptoms:**
- Checkout sessions not creating
- Webhooks not processing
- Subscription status not updating

**Diagnosis:**
```python
# Check Stripe configuration
import stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
try:
    stripe.Account.retrieve()
    print("Stripe connection successful")
except Exception as e:
    print(f"Stripe error: {e}")
```

**Solutions:**
1. **Verify Webhook Endpoint:**
   ```python
   # Check webhook events
   events = stripe.Event.list(limit=10)
   for event in events:
       print(f"{event.type}: {event.created}")
   ```

2. **Sync Subscription Status:**
   ```python
   from app.services.stripe_service import StripeService
   stripe_service = StripeService()
   stripe_service.sync_all_subscriptions()
   ```

---

## 🔧 System Rebuild Instructions

### Complete System Rebuild from Scratch

#### Step 1: Environment Setup
```bash
# 1. Clone/Create repository structure
mkdir grantflow && cd grantflow

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 3. Install Python dependencies  
pip install flask sqlalchemy psycopg2-binary gunicorn
pip install openai requests beautifulsoup4 python-dateutil
pip install stripe sendgrid flask-cors werkzeug

# 4. Install Node.js dependencies (if using React frontend)
npm install react react-dom @heroicons/react tailwindcss
npm install axios chart.js react-chartjs-2 framer-motion

# 5. Setup PostgreSQL database
createdb grantflow_dev
psql grantflow_dev -c "CREATE EXTENSION IF NOT EXISTS 'uuid-ossp';"
```

#### Step 2: Database Schema Recreation
```python
# create_database.py
from app import create_app, db
from app.models import *  # Import all models

def create_database():
    app = create_app()
    
    with app.app_context():
        # Drop all tables (if rebuilding)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Insert default data
        create_default_data()
        
        print("Database created successfully!")

def create_default_data():
    """Insert required default data"""
    
    # Create workflow stages
    stages = [
        {'id': 'discovery', 'name': 'Discovery', 'color': '#3B82F6'},
        {'id': 'researching', 'name': 'Researching', 'color': '#8B5CF6'},
        {'id': 'writing', 'name': 'Writing', 'color': '#10B981'},
        {'id': 'review', 'name': 'Review', 'color': '#F59E0B'},
        {'id': 'submitted', 'name': 'Submitted', 'color': '#6366F1'},
        {'id': 'pending', 'name': 'Pending Decision', 'color': '#EF4444'},
        {'id': 'awarded', 'name': 'Awarded', 'color': '#059669'},
        {'id': 'declined', 'name': 'Declined', 'color': '#DC2626'}
    ]
    
    # Create achievements
    achievements = [
        {'code': 'first_match', 'name': 'First Match', 'xp_reward': 50},
        {'code': 'first_submission', 'name': 'First Submission', 'xp_reward': 100},
        {'code': 'first_award', 'name': 'First Award', 'xp_reward': 500}
    ]
    
    # Insert data
    for achievement_data in achievements:
        achievement = Achievement(**achievement_data)
        db.session.add(achievement)
    
    db.session.commit()

if __name__ == "__main__":
    create_database()
```

#### Step 3: Core Application Structure
```python
# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/grantflow_dev')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key')
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    from app.api import auth, grants, ai_grants, workflow, analytics
    app.register_blueprint(auth.bp)
    app.register_blueprint(grants.bp) 
    app.register_blueprint(ai_grants.bp)
    app.register_blueprint(workflow.bp)
    app.register_blueprint(analytics.bp)
    
    return app
```

#### Step 4: Essential Service Implementation
```python
# app/services/essential_services.py
"""Minimal essential services for system bootstrap"""

class BootstrapServices:
    """Essential services needed for basic system operation"""
    
    @staticmethod
    def create_test_user():
        """Create a test user for system verification"""
        from app.models import User, Organization
        
        user = User(
            email='test@grantflow.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            org_name='Test Organization'
        )
        user.set_password('testpass123')
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod  
    def import_sample_grants():
        """Import sample grants for testing"""
        from app.models import Grant
        
        sample_grants = [
            {
                'title': 'Community Health Initiative Grant',
                'funder': 'Sample Foundation',
                'amount_min': 25000,
                'amount_max': 50000,
                'source_name': 'Bootstrap Sample',
                'status': 'idea',
                'application_stage': 'discovery'
            },
            {
                'title': 'Education Technology Grant',
                'funder': 'Tech Foundation',
                'amount_min': 10000,
                'amount_max': 25000,
                'source_name': 'Bootstrap Sample',
                'status': 'idea', 
                'application_stage': 'discovery'
            }
        ]
        
        for grant_data in sample_grants:
            grant = Grant(**grant_data)
            db.session.add(grant)
        
        db.session.commit()
        print(f"Imported {len(sample_grants)} sample grants")
    
    @staticmethod
    def test_system_health():
        """Verify all essential systems are working"""
        tests = []
        
        # Test database connection
        try:
            db.session.execute('SELECT 1')
            tests.append(('Database', True, 'Connected'))
        except Exception as e:
            tests.append(('Database', False, str(e)))
        
        # Test OpenAI connection
        try:
            if os.environ.get('OPENAI_API_KEY'):
                from app.services.ai_service import AIService
                ai = AIService()
                ai.test_connection()
                tests.append(('OpenAI API', True, 'Connected'))
            else:
                tests.append(('OpenAI API', False, 'No API key'))
        except Exception as e:
            tests.append(('OpenAI API', False, str(e)))
        
        # Test data collection
        try:
            from app.services.grants_gov_client import GrantsGovClient
            client = GrantsGovClient()
            grants = client.get_recent_grants(limit=1)
            tests.append(('Data Collection', True, f'Retrieved {len(grants)} grants'))
        except Exception as e:
            tests.append(('Data Collection', False, str(e)))
        
        # Print results
        print("\n=== SYSTEM HEALTH CHECK ===")
        for service, status, message in tests:
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {service}: {message}")
        
        return all(test[1] for test in tests)
```

#### Step 5: Bootstrap Script
```python
# bootstrap.py
"""Complete system bootstrap script"""

import os
import sys
from app import create_app, db
from app.services.essential_services import BootstrapServices

def main():
    print("🚀 Starting GrantFlow System Bootstrap...")
    
    # Step 1: Create application
    app = create_app()
    
    with app.app_context():
        # Step 2: Create database
        print("📊 Creating database schema...")
        db.create_all()
        
        # Step 3: Create test user
        print("👤 Creating test user...")
        test_user = BootstrapServices.create_test_user()
        print(f"   Test user: {test_user.email} / testpass123")
        
        # Step 4: Import sample data
        print("📋 Importing sample grants...")
        BootstrapServices.import_sample_grants()
        
        # Step 5: Test system health
        print("🔍 Running system health check...")
        healthy = BootstrapServices.test_system_health()
        
        if healthy:
            print("\n🎉 BOOTSTRAP SUCCESSFUL!")
            print("   System is ready for use.")
            print("   Start with: python main.py")
        else:
            print("\n⚠️ BOOTSTRAP COMPLETED WITH WARNINGS")
            print("   Some services may not be fully functional.")
            print("   Check error messages above.")

if __name__ == "__main__":
    main()
```

#### Step 6: Configuration Checklist
```python
# config_checklist.py
"""Verify all required configurations are present"""

import os

REQUIRED_CONFIGS = {
    # Essential
    'DATABASE_URL': 'Database connection string',
    'SESSION_SECRET': 'Flask session secret key',
    
    # AI Services
    'OPENAI_API_KEY': 'OpenAI GPT API for AI features',
    
    # Optional but recommended
    'CANDID_GRANTS_KEY': 'Candid API for premium grant data',
    'STRIPE_SECRET_KEY': 'Stripe for payment processing',
    'SENDGRID_API_KEY': 'SendGrid for email notifications'
}

def check_configuration():
    print("🔧 CONFIGURATION CHECKLIST")
    print("=" * 50)
    
    missing_required = []
    missing_optional = []
    
    for config, description in REQUIRED_CONFIGS.items():
        value = os.environ.get(config)
        
        if config in ['DATABASE_URL', 'SESSION_SECRET', 'OPENAI_API_KEY']:
            # Required
            if value:
                print(f"✅ {config}: Configured")
            else:
                print(f"❌ {config}: MISSING (Required)")
                missing_required.append((config, description))
        else:
            # Optional
            if value:
                print(f"✅ {config}: Configured")
            else:
                print(f"⚠️ {config}: Not configured (Optional)")
                missing_optional.append((config, description))
    
    if missing_required:
        print(f"\n❌ MISSING REQUIRED CONFIGURATIONS ({len(missing_required)}):")
        for config, desc in missing_required:
            print(f"   {config}: {desc}")
        print("\n   System will not function properly without these!")
        return False
    
    if missing_optional:
        print(f"\n⚠️ MISSING OPTIONAL CONFIGURATIONS ({len(missing_optional)}):")
        for config, desc in missing_optional:
            print(f"   {config}: {desc}")
        print("\n   System will work but with limited functionality.")
    
    print("\n✅ CONFIGURATION CHECK PASSED")
    return True

if __name__ == "__main__":
    check_configuration()
```

---

## 📚 Final Notes & Best Practices

### System Architecture Principles
1. **Modular Design**: Each service is independent and replaceable
2. **Circuit Breaker Pattern**: Prevents cascading failures from API outages
3. **Intelligent Caching**: Reduces API costs and improves performance
4. **Progressive Enhancement**: System works with minimal features, scales with more APIs
5. **Cost Optimization**: AI model routing saves 30-60% on OpenAI costs

### Maintenance Procedures
1. **Daily**: Monitor API circuit breakers and error rates
2. **Weekly**: Review AI usage logs and cost optimization
3. **Monthly**: Analyze grant success rates and system performance
4. **Quarterly**: Update foundation sources and API configurations

### Performance Optimization
- **Database Indexing**: Critical indexes on `grants.match_score`, `grants.application_stage`, `users.org_id`
- **API Batching**: Process grant matching in batches of 10 for optimal cost/performance
- **Caching Strategy**: 5-minute cache for searches, 1-hour for grant details, 24-hour for funder profiles
- **Background Jobs**: Run foundation scraping and data collection asynchronously

### Security Considerations
- **API Key Rotation**: Implement quarterly rotation for all external API keys
- **Session Security**: Use secure session cookies with proper expiration
- **Input Validation**: Sanitize all user inputs, especially in AI prompts
- **Rate Limiting**: Implement per-user rate limits to prevent abuse

This documentation provides complete technical coverage of the GrantFlow system. Use it for troubleshooting, rebuilding, and maintaining the platform. Keep it updated as the system evolves.

---

**Document Version**: 1.0  
**Last Updated**: September 24, 2025  
**System Version**: Production-Ready v2.0  
**Grant Count**: 677 active opportunities