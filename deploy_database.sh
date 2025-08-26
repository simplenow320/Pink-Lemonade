#!/bin/bash
# Production Database Deployment Script
# Run this during deployment to ensure database is properly initialized

set -e  # Exit on any error

echo "🚀 Starting database deployment..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

echo "✅ DATABASE_URL is configured"

# Run database initialization
echo "📊 Initializing database..."
python init_database.py

if [ $? -eq 0 ]; then
    echo "✅ Database deployment completed successfully!"
else
    echo "❌ Database deployment failed!"
    exit 1
fi