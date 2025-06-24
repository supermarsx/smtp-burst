@echo off
REM Run unit tests and collect coverage on Windows
pytest --cov
if %errorlevel% neq 0 exit /b %errorlevel%
