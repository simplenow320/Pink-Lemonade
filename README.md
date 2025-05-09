# GrantFlow

A comprehensive grant management platform for nonprofits that dynamically scales grant discovery through intelligent web scraping and AI-powered technologies.

## Key Features

- Robust multi-source grant scraping engine
- Advanced AI-assisted grant matching and scoring
- Intelligent OpenAI-powered narrative generation
- Flexible nonprofit workflow optimization tools
- Scalable and adaptive grant source management

## DevOps Setup

### Environment Setup

To set up the environment:

1. Run the environment setup script:
   ```bash
   ./setup_env.py
   ```
   or
   ```bash
   make setup-env
   ```
   This will create a `.env` file from `.env.example` and prompt for required values.

2. The script validates inputs to ensure they meet requirements:
   - Database URL (must be valid SQLite or PostgreSQL URL)
   - Session Secret (must be secure and at least 16 characters)
   - OpenAI API Key (must follow OpenAI's key format)

### Running the Application

You can run both the backend and frontend concurrently:

```bash
./run_services.sh
```

This will:
1. Check if `.env` exists and create it if needed
2. Start the Flask backend on port 5000
3. Start the React frontend on port 3000 (if available)

### Available Make Commands

The project includes a Makefile with useful commands:

- `make setup` - Set up the development environment
- `make setup-env` - Set up environment variables only
- `make clean` - Clean up cached and temporary files
- `make run` - Run the application
- `make run-backend` - Run only the backend
- `make db-schema` - Initialize database schema
- `make help` - Show help message

## Development Guidelines

- Backend changes should be made in the Flask application (`app/` directory)
- Frontend changes should be made in the React application (`client/` directory)
- Environment variables are managed through `.env` (not committed to Git)
- Database schema changes should use appropriate migration tools

## Database Configuration

The application uses SQLAlchemy ORM with support for:

- SQLite (default for development)
- PostgreSQL (recommended for production)

The database connection string is configured through the `DATABASE_URL` environment variable.

## AI Integration

The application integrates with OpenAI for:

1. Grant matching against organization profiles
2. Narrative generation for grant applications
3. Information extraction from web content

An OpenAI API key must be set in the `.env` file to use these features.

## Deployment

The application is configured for deployment on Replit with:

- Gunicorn as the WSGI server
- PostgreSQL database support
- Autoscaling enabled

## License

[MIT License](LICENSE)