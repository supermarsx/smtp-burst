#!/usr/bin/env bash
# Build Linux binary with PyInstaller
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
pyinstaller --onefile -n smtp-burst smtpburst/__main__.py --distpath dist/linux
