#!/bin/bash
#
# Sign and notarize the Dad Ware executable (dist/askdad) for distribution
# outside the App Store. Run this AFTER ./build_executable.sh has produced
# dist/askdad.
#
# All configuration comes from environment variables - nothing here is
# hardcoded, and no secret should ever be committed to this repo.
#
# Required for signing:
#   DADWARE_CODESIGN_IDENTITY   "Developer ID Application: Name (TEAMID)"
#
# Required for notarization - EITHER (preferred, App Store Connect API key):
#   APPLE_API_KEY_ID             Key ID, e.g. "2X9R4HXF34"
#   APPLE_API_ISSUER             Issuer ID (UUID)
#   APPLE_API_KEY_PATH           Path to the downloaded AuthKey_<KEYID>.p8
# OR (Apple ID + app-specific password):
#   APPLE_ID                     Your Apple ID email
#   APPLE_TEAM_ID                Your 10-character Team ID
#   APPLE_APP_PASSWORD           An app-specific password (not your Apple ID password)
#
# See docs/BUILDING.md for how to obtain each of these.
#

set -e  # Exit on error

# Colors (matches build_executable.sh house style)
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

section() {
    echo ""
    echo "═══════════════════════════════════════════════════"
    echo " $1"
    echo "═══════════════════════════════════════════════════"
    echo ""
}

fail() {
    echo -e "${RED}❌ $1${NC}" >&2
    shift
    for line in "$@"; do
        echo -e "$line" >&2
    done
    exit 1
}

section "🔏 Signing & Notarizing Dad Ware"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

EXECUTABLE="dist/askdad"
ENTITLEMENTS="entitlements.plist"

# ── Preflight checks ─────────────────────────────────────────────────────

if [ ! -f "$EXECUTABLE" ]; then
    fail "Executable not found at $EXECUTABLE" \
        "Build it first with: ./build_executable.sh"
fi

if [ ! -f "$ENTITLEMENTS" ]; then
    fail "Entitlements file not found at $ENTITLEMENTS" \
        "This file should be checked into the repo root."
fi

if [ -z "$DADWARE_CODESIGN_IDENTITY" ]; then
    fail "DADWARE_CODESIGN_IDENTITY is not set." \
        "Set it to your Developer ID Application identity, e.g.:" \
        "  export DADWARE_CODESIGN_IDENTITY=\"Developer ID Application: Jane Dev (ABCDE12345)\"" \
        "List available identities with:" \
        "  security find-identity -v -p codesigning"
fi

# Determine notarization auth method: API key (preferred) or Apple ID.
NOTARY_AUTH_ARGS=()
if [ -n "$APPLE_API_KEY_ID" ] || [ -n "$APPLE_API_ISSUER" ] || [ -n "$APPLE_API_KEY_PATH" ]; then
    if [ -z "$APPLE_API_KEY_ID" ] || [ -z "$APPLE_API_ISSUER" ] || [ -z "$APPLE_API_KEY_PATH" ]; then
        fail "Incomplete App Store Connect API key configuration." \
            "All three of APPLE_API_KEY_ID, APPLE_API_ISSUER, and APPLE_API_KEY_PATH must be set together."
    fi
    if [ ! -f "$APPLE_API_KEY_PATH" ]; then
        fail "APPLE_API_KEY_PATH does not point to a file: $APPLE_API_KEY_PATH" \
            "Download the AuthKey_<KEYID>.p8 from App Store Connect and set APPLE_API_KEY_PATH to its location."
    fi
    NOTARY_AUTH_ARGS=(--key "$APPLE_API_KEY_PATH" --key-id "$APPLE_API_KEY_ID" --issuer "$APPLE_API_ISSUER")
    NOTARY_AUTH_DESC="App Store Connect API key ($APPLE_API_KEY_ID)"
elif [ -n "$APPLE_ID" ] || [ -n "$APPLE_TEAM_ID" ] || [ -n "$APPLE_APP_PASSWORD" ]; then
    if [ -z "$APPLE_ID" ] || [ -z "$APPLE_TEAM_ID" ] || [ -z "$APPLE_APP_PASSWORD" ]; then
        fail "Incomplete Apple ID notarization configuration." \
            "All three of APPLE_ID, APPLE_TEAM_ID, and APPLE_APP_PASSWORD must be set together."
    fi
    NOTARY_AUTH_ARGS=(--apple-id "$APPLE_ID" --team-id "$APPLE_TEAM_ID" --password "$APPLE_APP_PASSWORD")
    NOTARY_AUTH_DESC="Apple ID ($APPLE_ID)"
else
    fail "No notarization credentials found." \
        "Set EITHER:" \
        "  APPLE_API_KEY_ID, APPLE_API_ISSUER, APPLE_API_KEY_PATH   (preferred)" \
        "OR:" \
        "  APPLE_ID, APPLE_TEAM_ID, APPLE_APP_PASSWORD" \
        "See docs/BUILDING.md for details on obtaining these."
fi

echo -e "${BLUE}Executable:${NC}       $EXECUTABLE"
echo -e "${BLUE}Identity:${NC}         $DADWARE_CODESIGN_IDENTITY"
echo -e "${BLUE}Entitlements:${NC}     $ENTITLEMENTS"
echo -e "${BLUE}Notarization auth:${NC} $NOTARY_AUTH_DESC"

# ── Sign ──────────────────────────────────────────────────────────────────

section "Step 1/4: Code signing"

codesign --force \
    --options runtime \
    --timestamp \
    --entitlements "$ENTITLEMENTS" \
    --sign "$DADWARE_CODESIGN_IDENTITY" \
    "$EXECUTABLE"

echo -e "${GREEN}✓ Signed.${NC}"

section "Step 2/4: Verifying signature"

codesign --verify --verbose=2 "$EXECUTABLE"
echo ""
codesign -dv --entitlements - "$EXECUTABLE"

echo ""
echo -e "${GREEN}✓ Signature verified.${NC}"

# ── Notarize ─────────────────────────────────────────────────────────────

section "Step 3/4: Notarization"

echo "A bare Mach-O executable cannot be submitted to notarytool directly -"
echo "it must be zipped first. Zipping with 'ditto' (not 'zip') to preserve"
echo "the binary exactly as codesign saw it."
echo ""

NOTARIZE_ZIP="dist/askdad-notarize.zip"
rm -f "$NOTARIZE_ZIP"
ditto -c -k --keepParent "$EXECUTABLE" "$NOTARIZE_ZIP"

echo -e "${BLUE}Submitting to Apple notary service (this can take a few minutes)...${NC}"
echo ""

# Capture output so we can pull the submission ID out on failure.
SUBMIT_OUTPUT_FILE=$(mktemp)
set +e
xcrun notarytool submit "$NOTARIZE_ZIP" \
    "${NOTARY_AUTH_ARGS[@]}" \
    --wait \
    | tee "$SUBMIT_OUTPUT_FILE"
SUBMIT_STATUS=$?
set -e

SUBMISSION_ID=$(grep -m1 '^  id:' "$SUBMIT_OUTPUT_FILE" | awk '{print $2}')
FINAL_STATUS=$(grep -m1 '^  status:' "$SUBMIT_OUTPUT_FILE" | awk '{print $2}')
rm -f "$SUBMIT_OUTPUT_FILE"

if [ "$SUBMIT_STATUS" -ne 0 ] || [ "$FINAL_STATUS" != "Accepted" ]; then
    echo ""
    echo -e "${RED}❌ Notarization failed or was rejected (status: ${FINAL_STATUS:-unknown}).${NC}"
    if [ -n "$SUBMISSION_ID" ]; then
        echo ""
        echo "Fetch the detailed log with:"
        echo "  xcrun notarytool log $SUBMISSION_ID ${NOTARY_AUTH_ARGS[*]}"
    else
        echo "No submission ID was captured - re-run with --wait and inspect the output above,"
        echo "or list recent submissions with:"
        echo "  xcrun notarytool history ${NOTARY_AUTH_ARGS[*]}"
    fi
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Notarization accepted (submission $SUBMISSION_ID).${NC}"

rm -f "$NOTARIZE_ZIP"

# ── Stapling ─────────────────────────────────────────────────────────────

section "Step 4/4: Stapling"

echo -e "${YELLOW}Note:${NC} 'xcrun stapler staple' only works on .app bundles, .dmg, and"
echo ".pkg installers - it CANNOT staple a ticket onto a bare Mach-O executable."
echo "This is a hard limitation of the stapler tool, not something this script"
echo "can work around, so it is deliberately skipped here for a raw binary."
echo ""
echo "This is not a problem: the notarization ticket for $EXECUTABLE is now"
echo "held by Apple's servers. When a user runs the binary, Gatekeeper looks"
echo "it up online by its code signature and allows it, the same as a stapled"
echo "ticket would - it just requires network access on first launch instead"
echo "of working fully offline."
echo ""
echo "If fully offline verification is ever required, the binary would need"
echo "to be wrapped in a .dmg or .pkg, which could then be stapled with:"
echo "  xcrun stapler staple <file>.dmg"
echo "That is out of scope for this script - see docs/BUILDING.md if it"
echo "becomes necessary."

section "✓ Done"

echo -e "${GREEN}$EXECUTABLE is signed and notarized.${NC}"
echo ""
echo "Verify Gatekeeper acceptance with:"
echo "  spctl -a -vvv -t install $EXECUTABLE"
echo ""
echo -e "${YELLOW}Note:${NC} spctl's 'install' type check is aimed at installer packages"
echo "and app bundles. For a bare notarized CLI binary it may still print"
echo "something like 'rejected' or 'no usable signature' even though signing"
echo "and notarization above both succeeded - that is a known quirk of spctl"
echo "with loose executables, not proof the binary is invalid. The reliable"
echo "check for a raw binary is that codesign verification (step 2 above)"
echo "passed and notarization was Accepted (step 3 above). See docs/BUILDING.md."
