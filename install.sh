#!/bin/sh
#
# Ask Dad installer for the command-line tool.
#
#   curl -fsSL https://justaskdad.app/install.sh | sh
#
# Downloads the signed, notarized universal binary (Apple silicon and Intel)
# from the latest GitHub release, checks its SHA-256, and puts `askdad` in
# ~/.local/bin. Most people want the app instead: https://justaskdad.app
#
# Settings (environment variables):
#   ASKDAD_VERSION=v1.1         install this release tag, not the latest
#   ASKDAD_INSTALL_DIR=PATH     install here, not ~/.local/bin
#   ASKDAD_NO_MODIFY_PATH=1     do not add the install folder to ~/.zshrc
#   ASKDAD_DOWNLOAD_URL=URL     use this folder of release files (for testing)
#
# POSIX sh on purpose: `curl ... | sh` runs it with /bin/sh.

set -eu

REPO="jbillington/dadware"
ASSET="askdad-macos.tar.gz"

say() { printf '%s\n' "$*"; }
fail() { printf 'askdad install: %s\n' "$*" >&2; exit 1; }

[ "$(uname -s)" = "Darwin" ] || fail "Ask Dad runs on macOS only."

command -v curl >/dev/null 2>&1 || fail "curl is missing."
command -v tar >/dev/null 2>&1 || fail "tar is missing."
command -v shasum >/dev/null 2>&1 || fail "shasum is missing."

if [ -n "${ASKDAD_DOWNLOAD_URL:-}" ]; then
    BASE_URL="$ASKDAD_DOWNLOAD_URL"
elif [ -n "${ASKDAD_VERSION:-}" ]; then
    BASE_URL="https://github.com/$REPO/releases/download/$ASKDAD_VERSION"
else
    BASE_URL="https://github.com/$REPO/releases/latest/download"
fi

INSTALL_DIR="${ASKDAD_INSTALL_DIR:-$HOME/.local/bin}"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/askdad-install.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT INT TERM

say "Downloading Ask Dad..."
curl -fsSL "$BASE_URL/$ASSET" -o "$TMP_DIR/$ASSET" \
    || fail "could not download $BASE_URL/$ASSET"
curl -fsSL "$BASE_URL/$ASSET.sha256" -o "$TMP_DIR/$ASSET.sha256" \
    || fail "could not download the checksum file"

EXPECTED="$(awk '{print $1; exit}' "$TMP_DIR/$ASSET.sha256")"
ACTUAL="$(shasum -a 256 "$TMP_DIR/$ASSET" | awk '{print $1}')"
[ -n "$EXPECTED" ] && [ "$EXPECTED" = "$ACTUAL" ] \
    || fail "checksum does not match. The download is damaged; nothing was installed."

tar -xzf "$TMP_DIR/$ASSET" -C "$TMP_DIR"
[ -f "$TMP_DIR/askdad" ] || fail "the download does not contain askdad"

mkdir -p "$INSTALL_DIR"
# Move into place last, so a failed run never leaves half a binary behind.
chmod 755 "$TMP_DIR/askdad"
mv -f "$TMP_DIR/askdad" "$INSTALL_DIR/askdad"
say "Installed askdad to $INSTALL_DIR/askdad"

case ":$PATH:" in
    *":$INSTALL_DIR:"*)
        ON_PATH=1 ;;
    *)
        ON_PATH=0 ;;
esac

if [ "$ON_PATH" = 0 ]; then
    LINE="export PATH=\"$INSTALL_DIR:\$PATH\""
    RC="$HOME/.zshrc"
    if [ -n "${ASKDAD_NO_MODIFY_PATH:-}" ]; then
        say ""
        say "$INSTALL_DIR is not on your PATH. To add it, run:"
        say "  echo '$LINE' >> $RC"
    elif [ -f "$RC" ] && grep -qF "$LINE" "$RC"; then
        say "Open a new Terminal window to use askdad."
    else
        printf '\n# Added by the Ask Dad installer\n%s\n' "$LINE" >> "$RC"
        say "Added $INSTALL_DIR to your PATH in $RC."
        say "Open a new Terminal window to use askdad."
    fi
fi

say ""
say "Run it:"
say "  askdad          # storage check-up"
say "  askdad cpu      # memory and CPU check-up"
say ""
say "For the full report (Photos, Mail, Messages), give Terminal Full Disk Access:"
say "System Settings > Privacy & Security > Full Disk Access."
