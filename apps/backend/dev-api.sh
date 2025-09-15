#!/bin/bash
# Development script to run FastAPI server

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Run ./setup-dev.sh first"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

echo "Starting EdgeGuard API server..."
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""

python3 api/main.py
