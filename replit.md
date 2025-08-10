# GrantFlow

## Overview
Pink Lemonade is an AI-powered grant management platform for nonprofits. It streamlines the entire grant lifecycle from discovery to submission by leveraging intelligent web scraping, AI-powered matching, and automated narrative generation. The platform helps nonprofits discover, evaluate, track, and apply for grants, with a focus on urban ministries and faith-based organizations. Key capabilities include automated grant discovery, real-time analytics, and a comprehensive grant management dashboard.

## User Preferences
Preferred communication style: Simple, everyday language.

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

### AI Integration
- **Service Layer**: Centralized AI service using OpenAI GPT-4o
- **Grant Matching**: Intelligent 1-5 scoring system with detailed explanations
- **Content Generation**: Automated narrative writing and proposal assistance
- **Web Scraping**: AI-powered grant extraction from URLs and text content
- **Grant Intelligence System**: Comprehensive AI-powered analysis and data extraction for grant opportunities, including contact intelligence, requirements analysis, strategic decision-making recommendations, and mission alignment.
- **Executive Prompt System**: Production-ready prompt templates with global guardrails for data integrity.
- **AI Prompter Service**: Handles token filling, validation, and OpenAI API integration.

### Job Scheduling
- **Automated Discovery**: Scheduled scraping jobs using Python's schedule library.
- **Background Processing**: Threaded execution for non-blocking operations.
- **Progress Tracking**: Real-time status updates.

### Error Handling
- **API Layer**: Comprehensive error logging and response formatting.
- **Frontend**: React ErrorBoundary components.
- **Database**: Transaction management with rollback capabilities.

### UI/UX Decisions
- **Branding**: Strict Pink Lemonade branding (pink, white, black, grey only) with single logo placement.
- **Design**: Mobile-first responsive design.
- **Enhanced Features**: All 5 UI/UX enhancements implemented:
  1. Animated Progress Indicators for User Onboarding - Complete ✓
  2. Personalized Dashboard Welcome Animation - Complete ✓
  3. Contextual Help Tooltips with Playful Microinteractions - Complete ✓
  4. Gamified Profile Completion Rewards - Complete ✓
  5. Interactive Error Message Visualizations - Complete ✓

### Feature Specifications
- **Unified Discovery Page**: Search, filters (city, focus area, deadline, source), and actions (Save, Add to Applications).
- **User Profile Space**: Complete profile management with document upload capabilities for enhanced AI matching.
- **Authentication System**: Full registration/login system with session management, password hashing, and role-based access.

## External Dependencies

### Core Services
- **OpenAI API**: GPT-4o integration.
- **PostgreSQL**: Primary database.
- **SQLite**: Development and testing database.

### Live Data Sources
- **Grants.gov REST API**: Federal grant opportunities.
- **Federal Register API**: Government NOFOs and funding notices.
- **GovInfo API**: Federal document search.
- **Philanthropy News Digest**: RSS-based foundation opportunities.

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