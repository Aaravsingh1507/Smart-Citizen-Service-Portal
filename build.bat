@echo off
echo Building Smart Citizen Service Portal...
cd /d "%~dp0"
if not exist dist mkdir dist
python -m pip show setuptools wheel 2>&1 | findstr "Name" >nul
if errorlevel 1 (
    pip install setuptools wheel
)
python setup.py sdist bdist_wheel 2>&1 || (
    echo Creating zip archive directly...
    powershell -Command "Compress-Archive -Path 'src','tests','docs','scripts','*.py','*.bat','*.txt','*.md','*.toml' -DestinationPath 'dist\Smart-Citizen-Service-Portal.zip' -Force"
)
echo Build complete. Check dist/ folder.
pause
