#!/bin/bash
# AI Talk Practice - Backend Server Startup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and set your API keys, then run this script again."
    exit 1
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet

# Run migrations
echo "🛠️  Checking and applying database migrations..."
alembic upgrade head

# Start server
echo ""
echo "🚀 Starting AI Talk Practice Backend..."
echo "   Host:      0.0.0.0"
echo "   Port:      8000"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
