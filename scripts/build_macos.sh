#!/usr/bin/env bash
set -e
pyinstaller --onefile -n smtp-burst smtpburst/__main__.py --distpath dist/macos
