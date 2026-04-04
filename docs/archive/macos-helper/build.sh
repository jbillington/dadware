#!/bin/bash
#
# Build script for PermissionHelper Swift helper
# This creates a Mac app bundle that can be used to check/request permissions
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_DIR="$SCRIPT_DIR/build"
APP_NAME="PermissionHelper"
APP_BUNDLE="$BUILD_DIR/$APP_NAME.app"
CONTENTS_DIR="$APP_BUNDLE/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

echo "Building PermissionHelper..."

# Clean build directory
rm -rf "$BUILD_DIR"
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Compile Swift code
swiftc -o "$MACOS_DIR/$APP_NAME" \
    "$SCRIPT_DIR/PermissionHelper.swift" \
    -framework Foundation \
    -framework AppKit

# Copy Info.plist
cp "$SCRIPT_DIR/Info.plist" "$CONTENTS_DIR/"

echo "✅ Build complete: $APP_BUNDLE"
echo ""
echo "To use this helper:"
echo "  1. The app bundle can be called from Python CLI if bundled together"
echo "  2. Or integrated into a full Mac app"
echo "  3. Or used standalone to check permissions"

