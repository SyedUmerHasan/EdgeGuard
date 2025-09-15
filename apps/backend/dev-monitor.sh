#!/bin/bash
# Development script to run background monitoring service

cd "$(dirname "$0")"

if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root for packet capture"
    echo "Run: sudo -E ./dev-monitor.sh"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Run ./setup-dev.sh first"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

echo "Starting EdgeGuard monitoring service..."
echo "Note: Running with root privileges for packet capture"
echo ""

python3 service/monitor.py
