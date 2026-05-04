#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! xcode-select -p >/dev/null 2>&1; then
    echo "Error: Xcode command line tools not found. Run: xcode-select --install" >&2
    exit 1
fi

APP_NAME="KaraokeProcessGUI"
APP_BUNDLE="${APP_NAME}.app"
BIN_PATH=".build/release/${APP_NAME}"

echo "Building ${APP_NAME} (release)..."
swift build -c release

echo "Assembling ${APP_BUNDLE}..."
rm -rf "${APP_BUNDLE}"
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
mkdir -p "${APP_BUNDLE}/Contents/Resources"

cp "${BIN_PATH}" "${APP_BUNDLE}/Contents/MacOS/${APP_NAME}"
cp Info.plist   "${APP_BUNDLE}/Contents/Info.plist"

echo "Codesigning (ad-hoc)..."
codesign --force --deep --sign - "${APP_BUNDLE}"

echo
echo "Built: $(pwd)/${APP_BUNDLE}"
echo
echo "Install:  mv \"${APP_BUNDLE}\" /Applications/"
echo "Launch:   open -a /Applications/${APP_BUNDLE} <video.mp4>"
