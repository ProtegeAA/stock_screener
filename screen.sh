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

# Virtual environment directory
VENV_DIR="venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        echo "Please ensure python3-venv is installed:"
        echo "  Ubuntu/Debian: sudo apt install python3-venv"
        echo "  Fedora/RHEL: sudo dnf install python3-virtualenv"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo ""
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check if dependencies are installed in venv
if ! python -c "import yfinance" 2>/dev/null; then
    echo "Installing required packages in virtual environment..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo ""
        echo "Error: Failed to install dependencies."
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo ""
fi

# Run the screener in interactive mode
python screener.py

# Deactivate virtual environment
deactivate

# Keep window open
read -p "Press Enter to exit..."
