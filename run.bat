@echo off
echo Starting Smart Citizen Service Portal...
python -c "import sys; print(sys.version)" 2>&1 | findstr "Python 3" >nul
if errorlevel 1 (
    echo ERROR: Python 3.12+ not found. Please install Python from python.org
    pause
    exit /b 1
)
cd /d "%~dp0"
set PYTHONPATH=%CD%\src;%PYTHONPATH%
python main.py
if errorlevel 1 (
    echo.
    echo Application exited with errors.
    pause
)
