# GrantFlow Makefile for common operations
.PHONY: setup setup-env clean run-backend run-frontend run

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

# Run backend server
run-backend:
	@echo "Starting backend server..."
	@gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Run frontend (to be implemented for React frontend)
run-frontend:
	@echo "Starting frontend server... (not implemented yet)"
	@echo "For React development, you would typically run 'npm start' in client directory."

# Run both backend and frontend (for local development)
run: run-backend

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
	@echo "  make run         - Run the application (backend for now)"
	@echo "  make run-backend - Run only the backend"
	@echo "  make db-schema   - Initialize database schema"
	@echo "  make help        - Show this help message"