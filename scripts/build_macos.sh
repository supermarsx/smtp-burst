#!/usr/bin/env bash
# Build macOS binary with PyInstaller
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "pyinstaller not found. Please install it first." >&2
    exit 1
fi

mkdir -p dist/macos
pyinstaller --clean --onefile -n smtp-burst smtpburst/__main__.py --distpath dist/macos
