#!/bin/bash
# Simple launcher for the stock screener
# Double-click this file (on Mac/Linux) or run ./screen.sh

cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3 from https://www.python.org/"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import yfinance" 2>/dev/null; then
    echo "Installing required packages..."
    pip install -r requirements.txt
    echo ""
fi

# Run the screener in interactive mode
python3 screener.py

# Keep window open on Windows
read -p "Press Enter to exit..."
