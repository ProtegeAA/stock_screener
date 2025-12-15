@echo off
REM Stock Screener - Auto Setup and Launch Script
REM This script automatically sets up everything you need and runs the screener

cd /d "%~dp0"

echo ==========================================
echo Stock Screener - Setup ^& Launch
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed.
    echo Please install Python from https://www.python.org/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYVERSION=%%i
echo [OK] Python found: %PYVERSION%

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo.
echo Installing dependencies...
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo [OK] Dependencies installed

REM Run the screener
echo.
echo ==========================================
echo Launching Stock Screener...
echo ==========================================
echo.

python screener.py %*

REM Keep window open
if "%~1"=="" (
    echo.
    pause
)
