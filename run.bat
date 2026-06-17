@echo off
rem DigiNotes Launch Script for Windows

echo === DigiNotes: CS50 Capstone Launcher ===

cd /d "%~dp0"

rem Check if virtual environment exists
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment. Make sure Python is installed and added to PATH.
        pause
        exit /b 1
    )
)

rem Activate virtual environment
call .venv\Scripts\activate.bat

rem Check if PySide6 is installed
python -c "import PySide6" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install requirements.
        pause
        exit /b 1
    )
)

echo Launching DigiNotes...
python src\main.py %*

echo === DigiNotes closed ===
