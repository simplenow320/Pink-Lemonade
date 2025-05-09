# GrantFlow Deployment Guide

This document provides instructions for deploying the GrantFlow application using Docker and explains the CI/CD pipeline setup with GitHub Actions.

## Local Development with Docker

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Setup and Deployment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/grantflow.git
   cd grantflow
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.docker.example .env
   ```

   Edit the `.env` file to set your environment variables:
   - Set a strong `SESSION_SECRET`
   - Add your `OPENAI_API_KEY`
   - Modify database credentials if needed

3. **Build and start the containers**:
   ```bash
   docker-compose up -d
   ```

   This command builds and starts three containers:
   - PostgreSQL database
   - Flask backend
   - React/Nginx frontend

4. **Access the application**:
   - Frontend: http://localhost (or the port specified in your .env file)
   - Backend API: http://localhost:5000/api (or the port specified in your .env file)

5. **View logs**:
   ```bash
   # View logs from all containers
   docker-compose logs -f

   # View logs from a specific container
   docker-compose logs -f backend
   docker-compose logs -f frontend
   docker-compose logs -f postgres
   ```

6. **Stop the application**:
   ```bash
   docker-compose down
   ```

   To remove volumes (database data) as well:
   ```bash
   docker-compose down -v
   ```

## Container Architecture

The application is divided into three main containers:

### 1. PostgreSQL Database (`postgres`)
- Stores all application data
- Persists data in a Docker volume
- Configured with health checks

### 2. Flask Backend (`backend`)
- Built from `python:3.11-slim`
- Runs the Flask application with Gunicorn
- Connects to PostgreSQL database
- Exposes API endpoints

### 3. React Frontend (`frontend`)
- Uses multi-stage build process
  - Stage 1: Builds React application
  - Stage 2: Serves via Nginx
- Configured for optimal performance
- Proxies API requests to backend

## CI/CD Pipeline with GitHub Actions

The repository includes a GitHub Actions workflow for continuous integration and deployment.

### Workflow File

The workflow configuration is located in `.github/workflows/ci.yml` and runs on each push to the `main` branch.

### CI Pipeline Stages

The workflow consists of three main jobs:

#### 1. Backend Tests
- Sets up PostgreSQL service
- Runs Python linting with flake8
- Executes pytest with code coverage
- Uploads coverage reports to Codecov

#### 2. Frontend Build
- Sets up Node.js environment
- Installs dependencies
- Runs ESLint
- Executes Jest tests
- Builds the React application
- Uploads build artifacts

#### 3. Docker Build
- Depends on the success of backend tests and frontend build
- Downloads frontend build artifacts
- Builds Docker images for:
  - Backend (using Dockerfile.backend)
  - Frontend (using Dockerfile.frontend)
- Pushes images to GitHub Container Registry (ghcr.io)
- Tags images with latest and commit SHA

## Production Deployment

For production deployment:

1. **Configure environment variables**:
   - Set environment variables in your production environment
   - Ensure all sensitive information is securely stored

2. **Pull and run Docker images**:
   ```bash
   # Pull images from GitHub Container Registry
   docker pull ghcr.io/your-org/grantflow/backend:latest
   docker pull ghcr.io/your-org/grantflow/frontend:latest

   # Create an external network
   docker network create grantflow-network

   # Run Docker Compose in production
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

## Security Considerations

- The Docker Compose setup includes security best practices:
  - No root access in containers
  - Environment variables for credentials
  - Network isolation through Docker networks
  - Health checks for service dependencies

- For production:
  - Consider using Docker Swarm or Kubernetes for orchestration
  - Set up proper monitoring and logging (Prometheus/Grafana)
  - Implement a reverse proxy (like Traefik or Nginx) with HTTPS
  - Use secrets management for sensitive data

## Troubleshooting

### Common Issues

1. **Database connection issues**:
   ```bash
   docker-compose logs backend
   ```
   Check if the backend can connect to PostgreSQL.

2. **Frontend not connecting to API**:
   Verify Nginx configuration in the frontend container:
   ```bash
   docker exec -it grantflow-frontend cat /etc/nginx/conf.d/default.conf
   ```

3. **Container not starting**:
   Check if there are port conflicts or missing environment variables:
   ```bash
   docker-compose logs
   ```

## Directory Structure

```
.
├── .github/workflows    # GitHub Actions workflows
│   └── ci.yml           # CI/CD configuration
├── app/                 # Backend Flask application
├── client/              # Frontend React application
├── nginx/               # Nginx configuration
│   └── default.conf     # Default Nginx server config
├── .env.docker.example  # Example environment variables
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile.backend   # Docker config for backend
├── Dockerfile.frontend  # Docker config for frontend
└── docker-entrypoint.sh # Script for backend container startup
```