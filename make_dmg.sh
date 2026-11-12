#!/bin/bash
#
# Put "Ask Dad.app" (see make_app.sh) in a drag-to-Applications DMG, sign the
# DMG, notarize it and staple the ticket. A bare Mach-O cannot be stapled, and
# on macOS 15 a loose binary dragged out of a DMG was refused; an app inside a
# stapled DMG is verified offline.
#
# Run AFTER ./build_executable.sh, ./sign_and_notarize.sh and ./make_app.sh. Uses the same
# environment variables as sign_and_notarize.sh (API key flavour only).
#
set -e
cd "$( dirname "${BASH_SOURCE[0]}" )"

for v in DADWARE_CODESIGN_IDENTITY APPLE_API_KEY_ID APPLE_API_ISSUER APPLE_API_KEY_PATH; do
    [ -n "${!v}" ] || { echo "❌ $v is not set (see sign_and_notarize.sh)" >&2; exit 1; }
done
[ -d "dist/Ask Dad.app" ] || { echo "❌ dist/Ask Dad.app not found - run ./make_app.sh" >&2; exit 1; }
command -v create-dmg >/dev/null || { echo "❌ create-dmg not found - brew install create-dmg" >&2; exit 1; }
BG=assets/askdad/dmg-background.tiff
VOLICON=assets/askdad/AskDad.icns
for f in "$BG" "$VOLICON"; do
    [ -f "$f" ] || { echo "❌ $f not found - run scripts/build_app_art.sh" >&2; exit 1; }
done
codesign --verify --deep --strict "dist/Ask Dad.app"
xcrun stapler validate "dist/Ask Dad.app"

VERSION=$(./dist/askdad --version | awk '{print $NF}' | sed 's/^v//')
DMG="dist/AskDad-${VERSION}.dmg"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

ditto "dist/Ask Dad.app" "$STAGE/Ask Dad.app"
# create-dmg lays out the window: the background with its arrow, icon size and
# positions, and the Applications shortcut (--app-drop-link). It drives a real
# Finder window through AppleScript, so run it from a logged-in desktop session,
# not over SSH; the first run may ask to let Terminal control Finder.
# Positions are icon centres in points and must match the arrow in
# assets/askdad/dmg-background.html. --window-size is the whole window frame,
# so the height is the 320-point background plus 28 for the title bar.
rm -f "$DMG"
create-dmg \
    --volname "Ask Dad ${VERSION}" \
    --volicon "$VOLICON" \
    --background "$BG" \
    --window-pos 200 120 \
    --window-size 600 348 \
    --icon-size 100 \
    --text-size 13 \
    --icon "Ask Dad.app" 150 165 \
    --hide-extension "Ask Dad.app" \
    --app-drop-link 450 165 \
    --hdiutil-quiet \
    "$DMG" "$STAGE"
codesign --force --timestamp --sign "$DADWARE_CODESIGN_IDENTITY" "$DMG"
codesign --verify --verbose=2 "$DMG"

xcrun notarytool submit "$DMG" --key "$APPLE_API_KEY_PATH" --key-id "$APPLE_API_KEY_ID" \
    --issuer "$APPLE_API_ISSUER" --wait | tee /tmp/dmg-notarize.$$ 
grep -q '^  status: Accepted' /tmp/dmg-notarize.$$ || { echo "❌ not accepted"; exit 1; }
rm -f /tmp/dmg-notarize.$$

xcrun stapler staple "$DMG"
xcrun stapler validate "$DMG"
echo "✓ $DMG is signed, notarized and stapled."
