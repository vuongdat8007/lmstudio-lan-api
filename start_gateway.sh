#!/bin/bash

# Start llama-server LAN Gateway
# Usage: ./start_gateway.sh

set -e

echo "🚀 Starting llama-server LAN Gateway..."
echo "========================================"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -q -r requirements.txt
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   Please run: cp .env.example .env"
    exit 1
fi

# Set PYTHONPATH
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

echo ""
echo "✅ Configuration:"
echo "   API Key: change-me-please"
echo "   Gateway: 10.0.0.181:8001"
echo "   llama-server: 10.0.0.181:8080"
echo ""
echo "📚 API Documentation:"
echo "   http://10.0.0.181:8001/docs"
echo ""
echo "🔑 Example API call:"
echo '   curl -H "X-API-Key: change-me-please" http://10.0.0.181:8001/admin/models'
echo ""
echo "========================================"
echo ""

# Start the server
uvicorn llama_gateway.main:app \
    --host 10.0.0.181 \
    --port 8002 \
    --log-level info
