@echo off
REM Simple launcher for the stock screener on Windows
REM Double-click this file to run

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed.
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import yfinance" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    echo.
)

REM Run the screener in interactive mode
python screener.py

pause
