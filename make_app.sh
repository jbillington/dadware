#!/bin/bash
#
# Wrap the signed dist/askdad in "Ask Dad.app" so Gatekeeper judges an app
# (which can carry a stapled ticket and be verified offline) instead of a bare
# executable (which needs an online ticket lookup, and was refused on macOS 15).
#
# The app is a thin launcher: double-clicking it opens Terminal running the
# bundled scanner through a small .command script. Terminal remains the app that owns the
# permission prompts and Full Disk Access. A native, Terminal-free app is
# the later Swift work (docs/roadmap/PERMISSIONS-PLAN.md).
#
# Run after ./build_executable.sh and ./sign_and_notarize.sh. Uses the same
# environment variables as sign_and_notarize.sh (API key flavour only).
#
set -e
cd "$( dirname "${BASH_SOURCE[0]}" )"

for v in DADWARE_CODESIGN_IDENTITY APPLE_API_KEY_ID APPLE_API_ISSUER APPLE_API_KEY_PATH; do
    [ -n "${!v}" ] || { echo "❌ $v is not set (see sign_and_notarize.sh)" >&2; exit 1; }
done
[ -f dist/askdad ] || { echo "❌ dist/askdad not found" >&2; exit 1; }
[ -f assets/askdad/AskDad.icns ] || { echo "❌ assets/askdad/AskDad.icns not found - run scripts/build_app_art.sh" >&2; exit 1; }
codesign --verify --strict dist/askdad

VERSION=$(./dist/askdad --version | awk '{print $NF}' | sed 's/^v//')
APP="dist/Ask Dad.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp dist/askdad "$APP/Contents/Resources/askdad"
# The app icon (built from the logo SVG by scripts/build_app_art.sh). It goes in
# before codesign: changing the bundle after signing breaks the signature.
cp assets/askdad/AskDad.icns "$APP/Contents/Resources/AskDad.icns"

# Terminal run directly on a program has no shell behind it: when the scan
# ends the window just says "[Process completed]" with nothing to type at.
# The report's "Reveal in Finder" buttons copy an `open -R "<path>"` command
# for the reader to paste into Terminal, so the window has to stay usable.
# So Terminal opens a small .command script that runs the scanner and then
# hands the window over to a normal prompt.
cat > "$APP/Contents/Resources/AskDad.command" <<'CMD'
#!/bin/bash
clear
# Put the bundled scanner on this window's PATH, so `askdad cpu` (which the
# scan suggests at the end) works at the prompt this window is left with.
# ASKDAD_CHANNEL tells the scanner it was started here, so it says "in this
# Terminal window": a new window has no askdad command.
HERE="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HERE:$PATH"
export ASKDAD_CHANNEL=app
"$HERE/askdad"
echo
echo "────────────────────────────────────────"
echo " All done. Your report is open in your browser."
echo
echo " To open a folder from the report: click \"Reveal in Finder\" there,"
echo " paste here (Cmd+V) and press Return."
echo "────────────────────────────────────────"
echo
exec "${SHELL:-/bin/zsh}" -l
CMD
chmod +x "$APP/Contents/Resources/AskDad.command"

cat > "$APP/Contents/MacOS/AskDad" <<'LAUNCH'
#!/bin/bash
# Open Terminal running the scanner script that lives next to this launcher.
HERE="$(cd "$(dirname "$0")/../Resources" && pwd)"
exec open -a Terminal "$HERE/AskDad.command"
LAUNCH
chmod +x "$APP/Contents/MacOS/AskDad"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key><string>com.dadware.askdad</string>
    <key>CFBundleName</key><string>Ask Dad</string>
    <key>CFBundleDisplayName</key><string>Ask Dad for Mac</string>
    <key>CFBundleExecutable</key><string>AskDad</string>
    <key>CFBundleIconFile</key><string>AskDad</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleShortVersionString</key><string>${VERSION}</string>
    <key>CFBundleVersion</key><string>${VERSION}</string>
    <key>LSMinimumSystemVersion</key><string>11.0</string>
    <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST
plutil -lint "$APP/Contents/Info.plist"

# The inner scanner is already signed (hardened runtime, timestamp). Sign the
# bundle around it; no --deep, so the inner signature is left as it is.
codesign --force --options runtime --timestamp --sign "$DADWARE_CODESIGN_IDENTITY" "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"

ZIP="dist/AskDad-app-notarize.zip"
rm -f "$ZIP"
ditto -c -k --keepParent "$APP" "$ZIP"
OUT=$(mktemp)
xcrun notarytool submit "$ZIP" --key "$APPLE_API_KEY_PATH" --key-id "$APPLE_API_KEY_ID" \
    --issuer "$APPLE_API_ISSUER" --wait | tee "$OUT"
if ! grep -q '^  status: Accepted' "$OUT"; then
    ID=$(grep -m1 '^  id:' "$OUT" | awk '{print $2}')
    echo "❌ not accepted. Log: xcrun notarytool log $ID (add the same key options)"; rm -f "$OUT" "$ZIP"; exit 1
fi
rm -f "$OUT" "$ZIP"

xcrun stapler staple "$APP"
xcrun stapler validate "$APP"
spctl -a -t exec -vv "$APP"
echo "✓ $APP is signed, notarized and stapled."
