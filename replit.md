# GrantFlow

## Overview
Pink Lemonade is an AI-powered grant management platform for nonprofits. It streamlines the entire grant lifecycle from discovery to submission by leveraging intelligent web scraping, AI-powered matching, and automated narrative generation. The platform helps nonprofits discover, evaluate, track, and apply for grants, with a focus on urban ministries and faith-based organizations. Its business vision is to provide enterprise AI features at startup pricing, aggressively undercutting competitors by 25-67%. The project aims for 100% completion with AI optimization, competitive pricing, a robust authentication system, Stripe payment processing, and production deployment, targeting 60% AI cost reduction while maintaining quality.

## User Preferences
Preferred communication style: Simple, everyday language.

### Prompt Generation Structure (REACTO)
When generating prompts for AI-driven tasks, use the REACTO framework:
- **R - Role**: Define the exact role with clear scope and responsibilities
- **E - Example**: Provide a vivid model of successful results
- **A - Application**: Step-by-step instructions with guardrails
- **C - Context**: Background, constraints, branding, and goals
- **T - Tone**: Style, personality, and feel of output
- **O - Output**: Exact deliverables with structure, formatting, and testing steps

Each section must be detailed (multiple sentences), include guardrails to prevent scope creep, and testing/debugging steps for technical outputs. Avoid placeholder text and keep language non-technical unless requested.

## System Architecture

### Backend Architecture
- **Framework**: Flask with factory pattern and SQLAlchemy ORM
- **Database**: PostgreSQL (SQLite as fallback)
- **API Design**: RESTful API with modular blueprint organization
- **Configuration**: Environment-based settings
- **Model Structure**: Organized models in separate files
- **Service Layer**: Mode detection and database operations

### Frontend Architecture
- **Framework**: React 18 with functional components and hooks
- **Styling**: Tailwind CSS with custom design system
- **State Management**: React hooks for local state, API calls for data persistence
- **Routing**: React Router for single-page application navigation
- **Charts**: Chart.js with react-chartjs-2 for analytics visualization

### Data Models
- **Grant**: Tracks grant opportunities with contact details and submission tracking
- **Organization**: Manages profiles with mission, focus areas, and keywords
- **ScraperSource**: Manages grant sources and funder contact information
- **Narrative**: Stores AI-generated grant proposal content
- **Analytics**: Stores success metrics and historical performance

### AI Integration (Phase 2 Complete ✅)
- **REACTO Prompt System**: Industry-leading prompt engineering with Role, Example, Application, Context, Tone, Output structure
- **Grant Matching Engine**: Live AI scoring (1-5) with detailed explanations, key alignments, challenges, and next steps
- **Narrative Generator**: Automated proposal writing for 8+ sections (executive summary, statement of need, etc.)
- **Grant Intelligence**: Comprehensive analysis extracting requirements, evaluation criteria, competitive insights
- **Working Endpoints**: `/api/ai-grants/match`, `/api/ai-grants/analyze`, `/api/ai-grants/generate-narrative`
- **OpenAI GPT-4o**: Latest model integration with JSON response formatting
- **Performance**: <2 seconds per grant match with error handling and fallbacks

### Workflow Automation (Phase 3 Complete ✅)
- **8-Stage Pipeline**: Discovery → Researching → Writing → Review → Submitted → Pending → Awarded/Declined → Reporting
- **Stage Management**: Automated transitions, validation, and progress tracking
- **Working Endpoints**: `/api/workflow/pipeline`, `/api/workflow/move-stage`, `/api/workflow/checklist`
- **Stage Features**: Color coding, icons, auto-actions, required fields, typical durations
- **Batch Operations**: Move multiple grants simultaneously for efficiency
- **Activity Logging**: Complete audit trail for every grant transition
- **Pipeline Analytics**: Real-time metrics, success rates, stage distribution

### Error Handling
- **API Layer**: Comprehensive error logging and response formatting.
- **Frontend**: React ErrorBoundary components.
- **Database**: Transaction management with rollback capabilities.

### UI/UX Decisions
- **Branding**: Strict Pink Lemonade branding (pink, white, black, grey only) with single logo placement.
- **Design**: Mobile-first responsive design.
- **Enhanced Features**: Animated progress indicators, personalized dashboard welcome, contextual help tooltips, gamified profile completion rewards, and interactive error message visualizations.

### Feature Specifications (Phases 1-5 Complete ✅)
- **Real Grant Discovery** (Phase 1): Federal Register API integration, live grant data
- **AI Matching with REACTO** (Phase 2): 1-5 scoring, detailed analysis, narrative generation
- **8-Stage Workflow Pipeline** (Phase 3): Discovery→Researching→Writing→Review→Submitted→Pending→Awarded/Declined→Reporting
- **Smart Tools Suite** (Phase 4): Grant Pitch, Case for Support, Impact Reports, Thank You Letters, Social Media
- **Analytics Dashboard** (Phase 5): Success rates, ROI tracking, funding forecasts, performance benchmarks
- **Payment Processing** (Phase 6 - Next): Stripe integration for subscriptions
- **Team Collaboration** (Phase 7): Multi-user support, role management
- **Mobile Optimization** (Phase 8): Responsive design improvements
- **Advanced Integrations** (Phase 9): Calendar, CRM, document management
- **Production Deployment** (Phase 10): Final optimization and launch

## External Dependencies

### Core Services
- **OpenAI API**: GPT-4o integration.
- **PostgreSQL**: Primary database.
- **SQLite**: Development and testing database.
- **Stripe**: Payment processing for checkout sessions, customer portal, webhooks, and invoicing.
- **SendGrid**: Email invitation system for surveys and stakeholder communications.

### Live Data Sources
- **Federal Register API**: Government NOFOs and funding notices.
- **USAspending.gov API**: Historical federal grant awards and spending data.
- **Candid Grants API**: Grant and foundation data.
- **Candid News API**: Articles about grants and foundations.
- **Grants.gov REST API**: Federal grant opportunities.
- **Major Foundations Directory**: Direct access to top 8 foundations.

### Frontend Libraries
- **React Ecosystem**: React 18, React Router, React Scripts.
- **UI Components**: Chart.js, Framer Motion.
- **Development Tools**: ESLint, Prettier, Tailwind CSS, Testing Library.

### Backend Libraries
- **Flask Ecosystem**: Flask-SQLAlchemy, Flask-CORS.
- **AI/ML**: OpenAI Python SDK.
- **Data Processing**: Beautiful Soup, Requests.
- **Utilities**: python-dateutil, schedule.

### Development Infrastructure
- **Testing**: Jest (frontend), Pytest (backend).
- **Code Quality**: ESLint, Prettier.
- **Build Tools**: React Scripts.
- **Deployment**: Docker containerization.