#!/bin/bash
# Setup development environment

cd "$(dirname "$0")"

echo "Setting up EdgeGuard backend environment..."
echo ""

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3"
    exit 1
fi

# Install system dependencies
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-venv

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "Virtual environment created at: .venv/"
echo ""
echo "To run the API server:"
echo "  ./dev-api.sh"
echo ""
echo "To run the monitoring service:"
echo "  sudo -E ./dev-monitor.sh"
