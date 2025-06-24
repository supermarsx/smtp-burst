#!/usr/bin/env bash
set -e

PLATFORM="$(uname | tr '[:upper:]' '[:lower:]')"

case "$PLATFORM" in
    linux*)
        OUTDIR="dist/linux"
        ;;
    darwin*)
        OUTDIR="dist/macos"
        ;;
    msys*|mingw*|cygwin*)
        OUTDIR="dist/windows"
        ;;
    *)
        echo "Unsupported platform: $PLATFORM"
        exit 1
        ;;
esac

pyinstaller --onefile -n smtp-burst smtpburst/__main__.py --distpath "$OUTDIR"
