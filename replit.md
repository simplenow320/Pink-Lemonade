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

### Job Scheduling & Integration
- **Automated Discovery**: Scheduled scraping jobs using Python's schedule library.
- **Background Processing**: Threaded execution for non-blocking operations.
- **Progress Tracking**: Real-time status updates.
- **Integration Service**: Central orchestration service for all system components with real-time data synchronization.
- **Automated Monitoring**: Proactive system health checks, performance analytics, and intelligent alerting.
- **Notification Enhancement**: Advanced notification system with grant match alerts, watchlist notifications, and personalized communications.

### Error Handling
- **API Layer**: Comprehensive error logging and response formatting.
- **Frontend**: React ErrorBoundary components.
- **Database**: Transaction management with rollback capabilities.

### UI/UX Decisions
- **Branding**: Strict Pink Lemonade branding (pink, white, black, grey only) with single logo placement.
- **Design**: Mobile-first responsive design.
- **Enhanced Features**: Animated progress indicators, personalized dashboard welcome, contextual help tooltips, gamified profile completion rewards, and interactive error message visualizations.

### Feature Specifications
- **Unified Discovery Page**: Search, filters (city, focus area, deadline, source), and actions (Save, Add to Applications).
- **User Profile Space**: Complete profile management with document upload capabilities for enhanced AI matching.
- **Authentication System**: Full registration/login system with session management, password hashing, and role-based access.
- **Automated Workflow**: 8-stage pipeline (Discovery→Awarded), smart deadline tracking, intelligent reminders, and team collaboration features.
- **Smart Reporting System**: Foundation models & AI integration, AI question refinement & survey builder, data collection & validation automation, dashboard & analytics integration, automated report generation, and governance & compliance framework.

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