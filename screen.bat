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

REM Virtual environment directory
set VENV_DIR=venv

REM Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Error: Failed to create virtual environment.
        echo Please ensure Python was installed with pip and venv support.
        pause
        exit /b 1
    )
    echo.
)

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"

REM Check if dependencies are installed in venv
python -c "import yfinance" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages in virtual environment...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Error: Failed to install dependencies.
        pause
        exit /b 1
    )
    echo.
)

REM Run the screener in interactive mode
python screener.py

REM Deactivate virtual environment
call "%VENV_DIR%\Scripts\deactivate.bat"

pause
