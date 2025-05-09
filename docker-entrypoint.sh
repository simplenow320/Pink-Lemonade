#!/bin/bash
set -e

# Wait for the database to be ready
if [ -n "$DATABASE_URL" ]; then
  echo "Waiting for PostgreSQL to be ready..."
  
  # Extract host and port from DATABASE_URL
  if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    
    # Wait for the database to become available
    until pg_isready -h "$DB_HOST" -p "$DB_PORT"; do
      echo "PostgreSQL is unavailable - sleeping"
      sleep 1
    done
    
    echo "PostgreSQL is up - continuing"
  else
    echo "WARNING: Couldn't parse DATABASE_URL for waiting script"
  fi
fi

# Run database migrations
echo "Running database migrations..."
python -c "from app import db; db.create_all()"

# Execute the command provided as arguments to this script
exec "$@"