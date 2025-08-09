# GrantFlow

## Overview

GrantFlow is a comprehensive AI-powered grant management platform designed specifically for nonprofit organizations. The system helps nonprofits discover, evaluate, track, and apply for grants through intelligent web scraping, AI-powered matching, and automated narrative generation. Built with a focus on urban ministries and faith-based organizations, GrantFlow streamlines the entire grant lifecycle from discovery to application submission.

The platform leverages OpenAI's GPT-4o for intelligent grant analysis, match scoring, and proposal writing assistance. It features automated grant discovery through web scraping, real-time analytics, and a complete grant management dashboard with status tracking from initial discovery through final decision.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with Drizzle ORM (SQLite as fallback)
- **API Design**: RESTful API with blueprint-based organization
- **Authentication**: JWT-based session management
- **Migration System**: Custom database migration runner for schema evolution

### Frontend Architecture
- **Framework**: React 18 with functional components and hooks
- **Styling**: Tailwind CSS with custom design system
- **State Management**: React hooks for local state, API calls for data persistence
- **Routing**: React Router for single-page application navigation
- **Charts**: Chart.js with react-chartjs-2 for analytics visualization

### Data Models
- **Grant**: Core entity tracking grant opportunities with enhanced contact details and submission tracking
- **Organization**: Profile management with mission, focus areas, and keywords
- **ScraperSource**: Manages grant sources and funder contact information
- **Narrative**: AI-generated grant proposal content
- **Analytics**: Success metrics and historical performance tracking

### AI Integration
- **Service Layer**: Centralized AI service using OpenAI GPT-4o
- **Grant Matching**: Intelligent 1-5 scoring system with detailed explanations
- **Content Generation**: Automated narrative writing and proposal assistance
- **Web Scraping**: AI-powered grant extraction from URLs and text content

### Job Scheduling
- **Automated Discovery**: Scheduled scraping jobs using Python's schedule library
- **Background Processing**: Threaded execution for non-blocking operations
- **Progress Tracking**: Real-time status updates and metrics collection

### Error Handling
- **API Layer**: Comprehensive error logging and response formatting
- **Frontend**: React ErrorBoundary components with graceful fallbacks
- **Database**: Transaction management with rollback capabilities
- **Migration Safety**: Column existence checks before schema changes

## External Dependencies

### Core Services
- **OpenAI API**: GPT-4o integration for AI-powered analysis and content generation
- **PostgreSQL**: Primary database for production deployments
- **SQLite**: Development and testing database

### Live Data Sources (Integrated August 2025)
- **Grants.gov REST API**: Live federal grant opportunities with 100 calls/hour limit
- **Federal Register API**: Government NOFOs and funding notices with 1000 calls/hour limit
- **GovInfo API**: Federal document search with 1000 calls/hour limit
- **Philanthropy News Digest**: RSS-based foundation opportunities (custom XML parser)

### Frontend Libraries
- **React Ecosystem**: React 18, React Router, React Scripts
- **UI Components**: Chart.js, Framer Motion for animations
- **Development Tools**: ESLint, Prettier, Tailwind CSS, Testing Library

### Backend Libraries
- **Flask Ecosystem**: Flask-SQLAlchemy, Flask-CORS
- **AI/ML**: OpenAI Python SDK
- **Data Processing**: Beautiful Soup for web scraping, Requests for HTTP operations
- **Utilities**: python-dateutil, schedule for job automation

### Development Infrastructure
- **Testing**: Jest for frontend, Pytest for backend
- **Code Quality**: ESLint, Prettier for consistent formatting
- **Build Tools**: React Scripts for frontend bundling
- **Deployment**: Docker containerization with multi-stage builds

### Grant Discovery Sources
- **Government**: Grants.gov for federal opportunities
- **Private Foundations**: Lilly Endowment, Maclellan Foundation, Mustard Seed Foundation
- **Grant Databases**: GrantWatch, Foundation Directory Online, GrantStation
- **Faith-Based**: National Christian Foundation, various denominational sources
- **Local Sources**: City and state-specific funding organizations