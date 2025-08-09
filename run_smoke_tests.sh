#!/bin/bash
# Smoke Test Runner for Pink Lemonade Grant Platform

echo "🚀 Starting Pink Lemonade Smoke Tests..."
echo "========================================"

# Set test environment
export APP_DATA_MODE=DEMO

# Check if server is running
echo "📡 Checking if server is running on port 5000..."
if ! curl -s http://localhost:5000/ > /dev/null 2>&1; then
    echo "❌ Server not running on localhost:5000"
    echo "💡 Please start the server first:"
    echo "   python main.py"
    echo "   OR"
    echo "   gunicorn --bind 0.0.0.0:5000 main:app"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Run smoke tests
echo "🧪 Running smoke tests..."
python tests/smoke_test.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All smoke tests passed!"
    echo "📋 Check TEST_REPORT.md for detailed results"
else
    echo ""
    echo "❌ Some smoke tests failed"
    echo "📋 Check TEST_REPORT.md for detailed results"
    exit 1
fi