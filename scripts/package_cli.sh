#!/bin/bash
#
# Package the signed CLI binary for the curl installer and the Homebrew tap.
#
# Run after ./build_executable.sh and ./sign_and_notarize.sh. Makes:
#   dist/askdad-macos.tar.gz          the binary, for install.sh and brew
#   dist/askdad-macos.tar.gz.sha256   its checksum, which install.sh checks
# and updates Formula/askdad.rb with this release's url, sha256 and version.
#
# Attach both dist files and install.sh to the GitHub release, then copy
# Formula/askdad.rb into the jbillington/homebrew-tap repo.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

BINARY="dist/askdad"
ASSET="askdad-macos.tar.gz"
FORMULA="Formula/askdad.rb"
REPO="jbillington/dadware"

[ -f "$BINARY" ] || { echo "❌ $BINARY not found. Run ./build_executable.sh first." >&2; exit 1; }

# Refuse an unsigned binary on a Mac: the whole point of this package is that
# it runs without a Gatekeeper warning. Skip with ALLOW_UNSIGNED=1 for a test.
if command -v codesign &> /dev/null && [ -z "${ALLOW_UNSIGNED:-}" ]; then
    if ! codesign --verify --strict "$BINARY" 2> /dev/null; then
        echo "❌ $BINARY is not signed. Run ./sign_and_notarize.sh first." >&2
        exit 1
    fi
fi

PYTHON="python3"
[ -x venv/bin/python ] && PYTHON="venv/bin/python"
VERSION="$("$PYTHON" -c 'from utils.version import VERSION; print(VERSION)')"
TAG="v$VERSION"

# Plain tar, binary at the archive root. COPYFILE_DISABLE keeps macOS from
# adding ._ AppleDouble files. The signature is inside the Mach-O, so tar
# keeps it.
COPYFILE_DISABLE=1 tar -czf "dist/$ASSET" -C dist askdad
SHA="$(shasum -a 256 "dist/$ASSET" | awk '{print $1}')"
echo "$SHA  $ASSET" > "dist/$ASSET.sha256"

URL="https://github.com/$REPO/releases/download/$TAG/$ASSET"
URL="$URL" SHA="$SHA" VERSION="$VERSION" perl -pi -e '
    s/^(\s*url\s+)".*"/$1"$ENV{URL}"/;
    s/^(\s*sha256\s+)".*"/$1"$ENV{SHA}"/;
    s/^(\s*version\s+)".*"/$1"$ENV{VERSION}"/;
' "$FORMULA"

echo "✅ dist/$ASSET"
echo "✅ dist/$ASSET.sha256  ($SHA)"
echo "✅ $FORMULA updated for $TAG"
echo ""
echo "Next:"
echo "  1. Attach to the $TAG release: dist/$ASSET, dist/$ASSET.sha256, install.sh"
echo "  2. Copy $FORMULA to the homebrew-tap repo's Formula/ folder and push"
echo "  3. Check: brew install jbillington/tap/askdad && askdad --version"
