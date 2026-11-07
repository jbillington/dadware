#!/bin/bash
#
# Wrap the signed dist/askdad in a DMG, sign the DMG, notarize it and staple
# the ticket. A bare Mach-O cannot be stapled, so Gatekeeper has to look its
# ticket up online; a stapled DMG carries the ticket with it and works offline.
#
# Run AFTER ./build_executable.sh and ./sign_and_notarize.sh. Uses the same
# environment variables as sign_and_notarize.sh (API key flavour only).
#
set -e
cd "$( dirname "${BASH_SOURCE[0]}" )"

for v in DADWARE_CODESIGN_IDENTITY APPLE_API_KEY_ID APPLE_API_ISSUER APPLE_API_KEY_PATH; do
    [ -n "${!v}" ] || { echo "❌ $v is not set (see sign_and_notarize.sh)" >&2; exit 1; }
done
[ -f dist/askdad ] || { echo "❌ dist/askdad not found" >&2; exit 1; }
codesign --verify --strict dist/askdad

VERSION=$(./dist/askdad --version | awk '{print $NF}' | sed 's/^v//')
DMG="dist/AskDad-${VERSION}.dmg"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

cp dist/askdad "$STAGE/askdad"
cat > "$STAGE/READ ME FIRST.txt" <<TXT
Ask Dad for Mac ${VERSION}  -  a free, read-only Mac storage check-up.

1. Drag "askdad" to your Desktop (or anywhere you like).
2. Open Terminal, type:  cd ~/Desktop  and press Return.
3. Type:  ./askdad  and press Return.

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
