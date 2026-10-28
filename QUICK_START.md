# Quick Start Guide

## Prerequisites
- Python 3.12+ installed and in PATH

## Running the Application

### Option 1: Using run.bat (Windows)
Double-click `run.bat` in the project folder.

### Option 2: Command Line
```cmd
cd Smart-Citizen-Service-Portal
set PYTHONPATH=src
python main.py
```

## First Use
1. Launch the application
2. Go to "Register Complaint" to submit a test complaint
3. View dashboard for real-time stats
4. Check "OS Control Center" to see integrated OS concepts
5. Export reports from "Reports & Export"

## Running Tests
```cmd
test.bat
```

## Features to Try
- Submit multiple complaints with different priorities
- Watch worker pool process them in "Dashboard" > Operations Panel
- View audit logs for all operations
- Export complaints to CSV
- Check resource availability

## Troubleshooting
- If Python not found: Install from https://www.python.org/
- If GUI doesn't appear: Ensure Tkinter is installed (included with standard Python)
- Database errors: Check app data folder permissions
