@echo off
REM Build Windows executable using PyInstaller
pyinstaller --onefile -n smtp-burst smtpburst\__main__.py --distpath dist\windows
if %errorlevel% neq 0 exit /b %errorlevel%
