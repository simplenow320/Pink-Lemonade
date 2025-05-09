#!/bin/bash
# Development script for GrantFlow

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}      GrantFlow Dev Environment     ${NC}"
echo -e "${BLUE}====================================${NC}"

# Check if environment file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Environment file not found. Setting up...${NC}"
    python3 setup_env.py --non-interactive --force
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to set up environment. Exiting.${NC}"
        exit 1
    fi
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Verify database connection
if [ -n "$DATABASE_URL" ]; then
    if [[ "$DATABASE_URL" == postgresql://* ]]; then
        echo -e "${YELLOW}Verifying PostgreSQL connection...${NC}"
        if ! command -v psql &> /dev/null; then
            echo -e "${RED}PostgreSQL client not found.${NC}"
        else
            # Extract connection details from URL
            DB_USER=$(echo $DATABASE_URL | sed -n 's/^postgresql:\/\/\([^:]*\):.*/\1/p')
            DB_HOST=$(echo $DATABASE_URL | sed -n 's/^postgresql:\/\/[^:]*:[^@]*@\([^:]*\):.*/\1/p')
            DB_PORT=$(echo $DATABASE_URL | sed -n 's/^postgresql:\/\/[^:]*:[^@]*@[^:]*:\([0-9]*\)\/.*/\1/p')
            DB_NAME=$(echo $DATABASE_URL | sed -n 's/^postgresql:\/\/[^:]*:[^@]*@[^:]*:[0-9]*\/\([^?]*\).*/\1/p')
            
            echo -e "${GREEN}Database: $DB_NAME on $DB_HOST:$DB_PORT${NC}"
        fi
    elif [[ "$DATABASE_URL" == sqlite://* ]]; then
        echo -e "${GREEN}Using SQLite database${NC}"
    fi
else
    echo -e "${RED}DATABASE_URL not found in environment.${NC}"
fi

# Check OpenAI API key
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" == "your_openai_api_key_here" ]; then
    echo -e "${YELLOW}WARNING: OpenAI API key not set. AI features will not work.${NC}"
else
    echo -e "${GREEN}OpenAI API key found.${NC}"
fi

# Development options
echo -e "\n${BLUE}Development options:${NC}"
echo -e "1. Run backend only"
echo -e "2. Run frontend only"
echo -e "3. Run both backend and frontend"
echo -e "4. Clean project"
echo -e "5. Exit"

read -p "Select option (1-5): " option

case $option in
    1)
        echo -e "${GREEN}Starting backend server...${NC}"
        gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
        ;;
    2)
        echo -e "${GREEN}Starting frontend server...${NC}"
        cd client && npm install && npm start
        ;;
    3)
        echo -e "${GREEN}Starting backend and frontend servers...${NC}"
        ./run_services.sh
        ;;
    4)
        echo -e "${YELLOW}Cleaning project...${NC}"
        make clean
        echo -e "${GREEN}Cleaning complete.${NC}"
        ;;
    5)
        echo -e "${BLUE}Exiting.${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option. Exiting.${NC}"
        exit 1
        ;;
esac