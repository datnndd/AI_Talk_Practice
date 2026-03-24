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

# Optional: install local model dependencies
if [ "$1" == "--local" ]; then
    echo "📦 Installing local model dependencies..."
    pip install -r requirements-local.txt --quiet
fi

# Start server
echo ""
echo "🚀 Starting AI Talk Practice Backend..."
echo "   WebSocket: ws://localhost:8000/ws/conversation"
echo "   Health:    http://localhost:8000/"
echo "   Providers: http://localhost:8000/providers"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
