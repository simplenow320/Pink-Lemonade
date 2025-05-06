# Architecture Overview

## 1. Overview

GrantFlow is a grant management application designed for nonprofit organizations. It helps users discover, evaluate, track, and apply for grants that align with their mission. The application leverages AI to match grants with organization profiles and generate grant narratives.

The system follows a client-server architecture with a React frontend and a Flask backend. It uses a SQLAlchemy ORM with SQLite as the default database (configurable to use other databases like PostgreSQL).

## 2. System Architecture

### 2.1 High-Level Architecture

The application follows a modern web application architecture with these key components:

- **Frontend**: React-based single-page application (SPA)
- **Backend**: Flask RESTful API
- **Database**: SQLAlchemy ORM with SQLite/PostgreSQL
- **AI Integration**: OpenAI API for grant analysis and narrative generation
- **Job Scheduling**: Background job system for automated grant scraping

```
┌──────────────┐       ┌───────────────┐       ┌───────────────┐
│              │       │               │       │               │
│  React SPA   │◄─────►│  Flask API    │◄─────►│   Database    │
│              │       │               │       │               │
└──────────────┘       └───────┬───────┘       └───────────────┘
                               │
                               │
                       ┌───────▼───────┐       ┌───────────────┐
                       │               │       │               │
                       │  AI Service   │◄─────►│   OpenAI API  │
                       │               │       │               │
                       └───────────────┘       └───────────────┘
```

### 2.2 Backend Architecture

The Flask backend follows a modular structure with blueprints for API routes, models for database entities, and services for business logic:

```
app/
├── __init__.py        # Application factory
├── config.py          # Configuration settings
├── routes.py          # Main routes
├── api/               # API endpoints
├── models/            # Database models
├── services/          # Business logic
├── utils/             # Helper functions
├── templates/         # Server-side templates
└── static/            # Static assets
```

### 2.3 Frontend Architecture

The React frontend is organized into a component-based architecture:

```
client/
├── public/            # Static files
├── src/
    ├── components/    # Reusable UI components
    ├── pages/         # Page-level components
    ├── hooks/         # Custom React hooks
    ├── utils/         # Helper utilities
    ├── App.js         # Main application component
    └── index.js       # Entry point
```

## 3. Key Components

### 3.1 Database Models

The application uses SQLAlchemy ORM with the following key models:

- **Grant**: Stores grant opportunities with details like title, funder, amount, due date
- **Organization**: Stores organization profile information
- **Narrative**: Stores AI-generated grant narratives
- **ScraperSource**: Stores configuration for grant scraping sources
- **ScraperHistory**: Tracks history of scraping jobs

### 3.2 API Structure

The API follows a RESTful design with these main endpoints:

- `/api/grants`: CRUD operations for grants
- `/api/organization`: Get and update organization profile
- `/api/scraper`: Manage scraper sources and trigger scraping jobs
- `/api/ai`: AI-powered operations like grant matching and narrative generation

### 3.3 Frontend Components

Key frontend components include:

- **Dashboard**: Overview of grant opportunities and stats
- **GrantList**: List of grants with filtering and sorting
- **GrantDetail**: Detailed view of a grant opportunity
- **Sidebar**: Navigation component
- **Organization Profile**: View and edit organization details

### 3.4 AI Integration

The application integrates with OpenAI API for:

1. **Grant Matching**: Analyzing how well a grant fits an organization's profile
2. **Narrative Generation**: Automatically generating grant application narratives
3. **Information Extraction**: Extracting structured grant information from web content

## 4. Data Flow

### 4.1 Grant Management Flow

1. Users can manually add grants or use the automated scraper
2. The AI service analyzes grants for match score with the organization profile
3. Users can track grant status through the application lifecycle
4. AI generates customized grant narratives based on organization profile

### 4.2 Scraper Flow

1. The scheduler triggers scraping jobs on a regular schedule
2. The scraper service extracts grant information from configured sources
3. The AI service processes and structures the extracted information
4. New grants are added to the database with match scores

### 4.3 Narrative Generation Flow

1. User requests a narrative for a specific grant
2. System retrieves grant details and organization profile
3. AI service generates a customized narrative
4. The narrative is stored in the database and presented to the user

## 5. External Dependencies

### 5.1 Core Dependencies

- **Flask**: Web framework for the backend
- **SQLAlchemy**: ORM for database operations
- **React**: Frontend library
- **Tailwind CSS**: Utility-first CSS framework

### 5.2 External Services

- **OpenAI API**: Used for AI-powered features
- **Grant websites**: External sources for grant scraping

## 6. Deployment Strategy

The application is configured to be deployed in multiple environments:

- **Development**: Local development with Flask's built-in server
- **Production**: Production deployment using Gunicorn WSGI server

The repository includes configuration for deployment on Replit with:
- Gunicorn as the WSGI server
- Autoscaling enabled
- Support for PostgreSQL database

## 7. Security Considerations

- Environment variables for sensitive information (API keys, database credentials)
- Session secrets for Flask session management
- Production configuration with secure cookie settings

## 8. Future Considerations

Potential areas for architectural expansion:

- User authentication and role-based access control
- Integration with email notification systems
- Document storage and management for grant applications
- Enhanced reporting and analytics capabilities