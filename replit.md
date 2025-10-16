# GrantFlow

## Overview
GrantFlow is an AI-powered grant management platform for nonprofits, streamlining the entire grant lifecycle from discovery to submission. It leverages intelligent web scraping, AI-powered matching, and automated narrative generation to help organizations find, evaluate, track, and apply for grants. The platform focuses on urban ministries and faith-based organizations, aiming to provide enterprise-level AI features at competitive startup pricing. It supports comprehensive grant discovery from numerous sources, AI-driven proposal generation, and a full 8-stage workflow pipeline for grant management.

## User Preferences
Preferred communication style: Simple, everyday language.

### Documentation Requirements
- Complete Platform Documentation: User requires comprehensive explanations of all AI system components and flows
- Developer & Fundraiser Context: Documentation must be accessible to both technical implementers and non-technical fundraising professionals
- Plain Language Focus: Complex technical concepts explained in everyday terms with practical examples
- Complete Feature Coverage: All platform capabilities documented with use cases and business value

### Prompt Generation Structure (REACTO)
When generating prompts for AI-driven tasks, use the REACTO framework:
- R - Role: Define the exact role with clear scope and responsibilities
- E - Example: Provide a vivid model of successful results
- A - Application: Step-by-step instructions with guardrails
- C - Context: Background, constraints, branding, and goals
- T - Tone: Style, personality, and feel of output
- O - Output: Exact deliverables with structure, formatting, and testing steps

Each section must be detailed (multiple sentences), include guardrails to prevent scope creep, and testing/debugging steps for technical outputs. Avoid placeholder text and keep language non-technical unless requested.

## System Architecture

### Backend Architecture
- **Framework**: Flask with factory pattern and SQLAlchemy ORM.
- **Database**: PostgreSQL (SQLite as fallback).
- **API Design**: RESTful API with modular blueprint organization.
- **Service Layer**: Handles mode detection and database operations.

### Frontend Architecture
- **Framework**: React 18 with functional components and hooks.
- **Styling**: Tailwind CSS with a custom design system.
- **State Management**: React hooks for local state, API calls for data persistence.
- **Routing**: React Router for single-page application navigation.
- **Charts**: Chart.js with react-chartjs-2 for analytics visualization.

### AI Integration
- **REACTO Prompt System**: 6-section prompt engineering for improved AI outputs.
- **AI Cost Optimizer**: Intelligent model routing (GPT-3.5-turbo for simple, GPT-4o for complex) to reduce API costs by 30-60%.
- **Hybrid Smart Tools**: Template-based architecture (80% templates + 20% AI) achieving 95% cost reduction while maintaining consultant-quality personalization.
- **Adaptive Discovery**: Dynamic questioning that adapts based on user responses, saving 40-60% time.
- **Grant Matching Engine**: Live AI scoring (1-5) with explanations, alignments, and next steps.
- **Narrative Generator**: Automated proposal writing for various sections (e.g., executive summary, statement of need).
- **Grant Intelligence**: Extracts requirements, evaluation criteria, and competitive insights.

### Consultant-Quality Smart Tools
- **Case for Support Hybrid**: Uses all 60+ organization profile fields for deep personalization. Template structure + real org data + minimal AI polish. Quality levels: Template ($0.01), Consultant ($0.05), Premium ($0.50). McKinsey/Bridgespan-level output at startup prices.
- **Impact Reporting Hybrid**: Dual-facing system integrating real beneficiary survey data. Collects authentic stories via QR codes, generates consultant-quality funder reports. Template + real participant data + minimal AI. KPMG/Deloitte-level reports at $0.05 vs $1.20 traditional.
- **Deep Personalization Engine**: Never generic - uses YOUR 60+ field org profile including 9 consultant-quality fields (competitive_advantage, growth_plans, community_needs, market_gap, collaboration_approach, awards_recognition, media_coverage, partnerships, strategic_priorities) and REAL beneficiary survey responses to create authentic, data-driven documents.
- **Organization as "The Brain"**: The Organization profile with 60+ fields serves as the central intelligence for all platform features - from grant matching to Smart Tools generation - ensuring every output is deeply personalized and never generic.

### Workflow Automation
- **8-Stage Pipeline**: Manages grants through Discovery, Researching, Writing, Review, Submitted, Pending, Awarded/Declined, and Reporting stages.
- **Stage Management**: Automated transitions, validation, and progress tracking with color coding, icons, and auto-actions.
- **Pipeline Analytics**: Provides real-time metrics, success rates, and stage distribution.

### UI/UX Decisions
- **Branding**: Strict Pink Lemonade branding (pink, white, black, grey) with single logo placement.
- **Design**: Mobile-first responsive design.
- **Enhanced Features**: Animated progress indicators, personalized dashboards, contextual help, gamified profile completion, and interactive error messages.

## External Dependencies

### Core Services
- **OpenAI API**: For AI model integration (GPT-4o and GPT-3.5-turbo).
- **PostgreSQL**: Primary database.
- **Stripe**: Payment processing for subscriptions.
- **SendGrid**: Email automation.

### Live Data Sources
- **SAM.gov API**: Federal contract opportunities.
- **Socrata SODA API**: State/local grants from NY State and San Francisco portals.
- **Candid API Suite**: Premium database for grants, news, and foundation analytics.
- **Federal Register API**: Early grant notices and NOFOs.
- **Federal Agency APIs**: HHS, Education, NSF via GSA Search.
- **USAspending.gov API**: Historical federal spending data.
- **Custom Foundation Scraper**: Integrates 70 sources, including major foundations, tech/AI funders, and regional foundations.

### Frontend Libraries
- **React Ecosystem**: React 18, React Router.
- **UI Components**: Chart.js, Framer Motion.
- **Development Tools**: ESLint, Prettier, Tailwind CSS, Testing Library.

### Backend Libraries
- **Flask Ecosystem**: Flask-SQLAlchemy, Flask-CORS.
- **AI/ML**: OpenAI Python SDK.
- **Data Processing**: Beautiful Soup, Requests.
- **Utilities**: python-dateutil, schedule.