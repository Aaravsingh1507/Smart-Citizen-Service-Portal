@echo off
echo Running Smart Citizen Service Portal Tests...
cd /d "%~dp0"
set PYTHONPATH=%CD%\src;%PYTHONPATH%
python -m pytest tests/ -v 2>&1
if errorlevel 1 (
    echo Tests failed. Trying with unittest...
    python -m unittest discover tests -v 2>&1
)
pause
