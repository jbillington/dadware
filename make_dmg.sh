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
codesign --verify --deep --strict "dist/Ask Dad.app"
xcrun stapler validate "dist/Ask Dad.app"

VERSION=$(./dist/askdad --version | awk '{print $NF}' | sed 's/^v//')
DMG="dist/AskDad-${VERSION}.dmg"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

ditto "dist/Ask Dad.app" "$STAGE/Ask Dad.app"
ln -s /Applications "$STAGE/Applications"
cat > "$STAGE/READ ME FIRST.txt" <<TXT
Ask Dad for Mac ${VERSION}  -  a free, read-only Mac storage check-up.

1. Drag "Ask Dad" onto the Applications folder.
2. Open it from Applications (double-click). A Terminal window opens and the
   scan runs; your report opens in your browser when it finishes.

For the full report, turn on Full Disk Access for Terminal:
System Settings > Privacy & Security > Full Disk Access.

It never deletes anything. Nothing leaves your Mac.
TXT

rm -f "$DMG"
hdiutil create -quiet -volname "Ask Dad ${VERSION}" -srcfolder "$STAGE" -format UDZO -fs HFS+ "$DMG"
codesign --force --timestamp --sign "$DADWARE_CODESIGN_IDENTITY" "$DMG"
codesign --verify --verbose=2 "$DMG"

xcrun notarytool submit "$DMG" --key "$APPLE_API_KEY_PATH" --key-id "$APPLE_API_KEY_ID" \
    --issuer "$APPLE_API_ISSUER" --wait | tee /tmp/dmg-notarize.$$ 
grep -q '^  status: Accepted' /tmp/dmg-notarize.$$ || { echo "❌ not accepted"; exit 1; }
rm -f /tmp/dmg-notarize.$$

xcrun stapler staple "$DMG"
xcrun stapler validate "$DMG"
echo "✓ $DMG is signed, notarized and stapled."
