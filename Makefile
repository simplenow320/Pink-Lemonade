# GrantFlow Makefile for common operations
.PHONY: setup setup-env clean test run-backend run-frontend run check-db dev-mode install-frontend-deps

# Setup the development environment
setup: setup-env
        @echo "Setup complete."

# Setup environment variables
setup-env:
        @echo "Setting up environment variables..."
        @python3 setup_env.py

# Clean up cached files and temporary files
clean:
        @echo "Cleaning up cached files..."
        @find . -name "__pycache__" -type d -exec rm -rf {} +
        @find . -name "*.pyc" -delete
        @find . -name "*.pyo" -delete
        @find . -name "*.pyd" -delete
        @find . -name ".pytest_cache" -type d -exec rm -rf {} +
        @find . -name ".coverage" -delete
        @find . -name "htmlcov" -type d -exec rm -rf {} +
        @find . -name ".tox" -type d -exec rm -rf {} +
        @echo "Clean complete."

# Run tests
test:
        @pytest -q

# Run backend server
run-backend:
        @echo "Starting backend server..."
        @gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Install frontend dependencies
install-frontend-deps:
        @echo "Installing frontend dependencies..."
        @cd client && npm install

# Run frontend
run-frontend: install-frontend-deps
        @echo "Starting frontend server..."
        @cd client && npm start

# Run both backend and frontend (for local development)
run:
        @echo "Starting both backend and frontend..."
        @./run_services.sh

# Interactive development mode
dev-mode:
        @echo "Starting development mode..."
        @./dev.sh

# Check database connection and setup
check-db:
        @echo "Checking database connection..."
        @./check_db.py

# Verify environment setup
verify-env:
        @echo "Verifying environment setup..."
        @python3 setup_env.py --non-interactive
        @./check_db.py

# Database helper commands
db-schema:
        @echo "Database schema information:"
        @python -c "from app import db; from app.models import grant, organization, narrative, scraper; print('Database schema initialized.')"

# Help command to display available targets
help:
        @echo "GrantFlow Makefile commands:"
        @echo "  make setup       - Setup development environment"
        @echo "  make setup-env   - Setup environment variables only"
        @echo "  make clean       - Clean up cached and temporary files"
        @echo "  make test        - Run tests with pytest"
        @echo "  make run         - Run the application (both backend and frontend)"
        @echo "  make run-backend - Run only the backend"
        @echo "  make run-frontend - Run only the frontend"
        @echo "  make dev-mode    - Interactive development mode"
        @echo "  make check-db    - Check database connection and setup"
        @echo "  make verify-env  - Verify environment setup"
        @echo "  make db-schema   - Initialize database schema"
        @echo "  make help        - Show this help message"