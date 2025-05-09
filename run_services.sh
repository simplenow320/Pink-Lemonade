#!/bin/bash
# Script to run the backend and frontend services concurrently

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}   GrantFlow Services Launcher      ${NC}"
echo -e "${BLUE}====================================${NC}"

# Function to check if environment variables are set
check_env() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}No .env file found. Setting up environment...${NC}"
        python3 setup_env.py
    else
        echo -e "${GREEN}Environment file found.${NC}"
    fi
}

# Get ports from environment or use defaults
BACKEND_PORT=${BACKEND_PORT:-5000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}

# Run backend in background
run_backend() {
    echo -e "${GREEN}Starting backend server on port ${BACKEND_PORT}...${NC}"
    # Export environment variables from .env file
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    gunicorn --bind 0.0.0.0:${BACKEND_PORT} --reuse-port --reload main:app &
    BACKEND_PID=$!
    echo -e "${GREEN}Backend server started with PID: ${BACKEND_PID}${NC}"
}

# Run frontend in background
run_frontend() {
    echo -e "${GREEN}Starting frontend server on port ${FRONTEND_PORT}...${NC}"
    
    # Check if package.json exists in client directory
    if [ -f "client/package.json" ]; then
        # Check if node_modules exists
        if [ ! -d "client/node_modules" ]; then
            echo -e "${YELLOW}Installing frontend dependencies...${NC}"
            (cd client && npm install)
        fi
        (cd client && npm start) &
        FRONTEND_PID=$!
        echo -e "${GREEN}Frontend server started with PID: ${FRONTEND_PID}${NC}"
    else
        echo -e "${RED}Error: Frontend package.json not found in client directory${NC}"
        echo -e "${YELLOW}Starting only the backend server...${NC}"
    fi
}

# Handle process termination
handle_shutdown() {
    echo -e "${YELLOW}Shutting down services...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo -e "${GREEN}Backend server stopped.${NC}"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}Frontend server stopped.${NC}"
    fi
    exit 0
}

# Set up signal handlers
trap handle_shutdown SIGINT SIGTERM

# Main execution
check_env
run_backend
run_frontend

echo -e "${GREEN}Services are running. Press Ctrl+C to shut down.${NC}"
echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}Backend URL: http://localhost:${BACKEND_PORT}${NC}"
echo -e "${BLUE}Frontend URL: http://localhost:${FRONTEND_PORT}${NC}"
echo -e "${BLUE}====================================${NC}"

# Wait for processes to complete
wait