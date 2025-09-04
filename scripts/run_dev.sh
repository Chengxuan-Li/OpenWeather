#!/bin/bash

# Development script for OpenWeather
# This script sets up the development environment and runs the application

set -e

echo "🚀 Starting OpenWeather Development Server"

# Check if Python 3.11+ is available
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.11 or higher is required. Found: $python_version"
    echo "Please install Python 3.11+ and try again."
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -e .

# Create outputs directory if it doesn't exist
mkdir -p outputs

# Set environment variables
export DEBUG=true
export LOG_LEVEL=DEBUG
export HOST=0.0.0.0
export PORT=8080

echo "🌐 Starting development server..."
echo "📍 URL: http://localhost:8080"
echo "📚 API Docs: http://localhost:8080/docs"
echo "🔍 Health Check: http://localhost:8080/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the development server
uvicorn openweather.main:app --host 0.0.0.0 --port 8080 --reload
