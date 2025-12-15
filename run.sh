#!/bin/bash
# Stock Screener - Auto Setup and Launch Script
# This script automatically sets up everything you need and runs the screener

set -e  # Exit on error

cd "$(dirname "$0")"

echo "=========================================="
echo "Stock Screener - Setup & Launch"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3 from https://www.python.org/"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo ""
echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "✓ Dependencies installed"

# Run the screener
echo ""
echo "=========================================="
echo "Launching Stock Screener..."
echo "=========================================="
echo ""

python screener.py "$@"

# Keep terminal open if double-clicked
if [ -z "$1" ]; then
    echo ""
    read -p "Press Enter to exit..."
fi
