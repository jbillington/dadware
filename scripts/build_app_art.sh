#!/bin/bash
#
# Rebuild the app icon and the DMG background from their sources:
#   assets/dadware/logo/askdad-icon-concept-bubble.svg -> assets/askdad/AskDad.icns
#   assets/askdad/dmg-background.html                   -> assets/askdad/dmg-background.tiff
#
# The outputs are committed, so a release build does not need this script; run it
# only after changing a source. Needs Google Chrome (headless, for rendering) and
# sips, iconutil and tiffutil, which ship with macOS.
#
set -e
cd "$( dirname "${BASH_SOURCE[0]}" )/.."

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[ -x "$CHROME" ] || { echo "❌ Google Chrome not found at $CHROME" >&2; exit 1; }

ICON_SVG="$PWD/assets/dadware/logo/askdad-icon-concept-bubble.svg"
BG_HTML="$PWD/assets/askdad/dmg-background.html"
OUT="$PWD/assets/askdad"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# render URL WIDTH HEIGHT SCALE OUTPUT.png  (transparent where the page is)
render() {
    "$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-first-run \
        --user-data-dir="$WORK/chrome" --default-background-color=00000000 \
        --force-device-scale-factor="$4" --window-size="$2,$3" \
        --virtual-time-budget=2000 --screenshot="$5" "$1" >/dev/null 2>&1
    [ -s "$5" ] || { echo "❌ Chrome did not render $1" >&2; exit 1; }
}

# --- App icon: one 1024 master, scaled down for each slot of the iconset ---
cat > "$WORK/icon.html" <<HTML
<html><body style="margin:0;background:transparent">
<img src="file://$ICON_SVG" width="1024" height="1024" style="display:block"></body></html>
HTML
render "file://$WORK/icon.html" 1024 1024 1 "$WORK/icon-1024.png"
SET="$WORK/AskDad.iconset"
mkdir "$SET"
for s in 16 32 128 256 512; do
    sips -z $s $s "$WORK/icon-1024.png" --out "$SET/icon_${s}x${s}.png" >/dev/null
    d=$((s * 2))
    sips -z $d $d "$WORK/icon-1024.png" --out "$SET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$SET" -o "$OUT/AskDad.icns"
echo "✓ $OUT/AskDad.icns"

# --- DMG background: 1x and 2x in one TIFF, so Retina screens get the sharp one ---
render "file://$BG_HTML" 600 320 1 "$WORK/bg.png"
render "file://$BG_HTML" 600 320 2 "$WORK/bg@2x.png"
tiffutil -cathidpicheck "$WORK/bg.png" "$WORK/bg@2x.png" -out "$OUT/dmg-background.tiff" 2>/dev/null
echo "✓ $OUT/dmg-background.tiff"
