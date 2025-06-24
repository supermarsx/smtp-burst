@echo off
REM Build Windows binary with PyInstaller
pushd %~dp0\..
pyinstaller --onefile -n smtp-burst smtpburst\__main__.py --distpath dist\windows
popd
