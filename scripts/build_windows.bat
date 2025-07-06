@echo off
REM Build Windows binary with PyInstaller
pushd %~dp0\..
where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Please install it first.
    popd
    exit /b 1
)
if not exist dist\windows mkdir dist\windows
pyinstaller --clean --onefile -n smtp-burst smtpburst\__main__.py --distpath dist\windows
popd
