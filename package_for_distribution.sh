#!/bin/bash
#
# Package executable for distribution
# Creates a ZIP file with executable, README files, and instructions
#

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "═══════════════════════════════════════════════════"
echo " 📦 Packaging Dad Ware for Distribution"
echo "═══════════════════════════════════════════════════"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if executable exists
if [ ! -f "dist/askdad" ]; then
    echo -e "${RED}❌ Executable not found!${NC}"
    echo ""
    echo "Please build the executable first:"
    echo "  ./build_executable.sh"
    echo ""
    exit 1
fi

# Get the version and build the way the binary itself resolves them, so the
# ZIP filename always matches what the executable reports. There's no live
# .git directory inside the already-built binary to ask directly, so we
# re-derive the same build stamp from the current commit (build and package
# are run back-to-back against the same commit) and read it back through
# utils/version.py, exactly as build_executable.sh does.
STAMP_FILE="utils/_build_stamp.py"
cleanup_stamp() {
    rm -f "$STAMP_FILE"
}
trap cleanup_stamp EXIT

GIT_BUILD=""
if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null; then
    GIT_BUILD=$(git log -1 --date=format:%Y-%m-%d --format=%cd-%h 2>/dev/null || echo "")
    if [ -n "$GIT_BUILD" ] && [ -n "$(git status --porcelain 2>/dev/null)" ]; then
        GIT_BUILD="${GIT_BUILD}-dirty"
    fi
fi

if [ -n "$GIT_BUILD" ]; then
    echo "BUILD = \"$GIT_BUILD\"" > "$STAMP_FILE"
fi

# Prefer the repo's venv interpreter (the setup the docs assume) so the
# version/build stamped onto the package matches the one build_executable.sh
# baked into the binary, rather than coming from whatever python3 is on PATH.
PYTHON_CMD="python3"
if [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON_CMD="$SCRIPT_DIR/venv/bin/python"
fi

VERSION=$("$PYTHON_CMD" -c "from utils.version import VERSION; print(VERSION)" 2>/dev/null || echo "0.7")
BUILD=$("$PYTHON_CMD" -c "from utils.version import BUILD; print(BUILD)" 2>/dev/null || echo "unknown")

echo -e "${BLUE}Version:${NC} $VERSION"
echo -e "${BLUE}Build:${NC} $BUILD"
echo ""

# Create package directory
PACKAGE_DIR="package"
PACKAGE_NAME="askdad-${VERSION}-${BUILD}"

echo -e "${BLUE}Creating package directory...${NC}"
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# Copy executable
echo -e "${BLUE}Copying executable...${NC}"
cp dist/askdad "$PACKAGE_DIR/"

# Copy README files
echo -e "${BLUE}Copying README files...${NC}"
cp README.md "$PACKAGE_DIR/"
if [ -f "docs/USER-GUIDE.md" ]; then
    cp docs/USER-GUIDE.md "$PACKAGE_DIR/"
fi

# Generate HTML README
echo -e "${BLUE}Generating HTML README...${NC}"
if [ -f "scripts/generate_html_readme.py" ]; then
    "$PYTHON_CMD" scripts/generate_html_readme.py "$PACKAGE_DIR/README.html"
else
    echo -e "${YELLOW}⚠️  HTML README generator not found, skipping...${NC}"
fi

# Create ZIP file
echo -e "${BLUE}Creating ZIP file...${NC}"
cd "$PACKAGE_DIR"
zip -r "../${PACKAGE_NAME}.zip" . -x "*.DS_Store" "*.git*" > /dev/null
cd ..

# Get ZIP size
ZIP_SIZE=$(du -h "${PACKAGE_NAME}.zip" | cut -f1)

echo ""
echo "═══════════════════════════════════════════════════"
echo -e "${GREEN}✓ Package created successfully!${NC}"
echo "═══════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}Package:${NC} ${PACKAGE_NAME}.zip"
echo -e "${GREEN}Size:${NC} $ZIP_SIZE"
echo ""
echo "Package contents:"
echo "  - askdad (executable)"
if [ -f "$PACKAGE_DIR/README.html" ]; then
    echo "  - README.html (open in browser)"
fi
echo "  - README.md (markdown instructions)"
if [ -f "$PACKAGE_DIR/USER-GUIDE.md" ]; then
    echo "  - USER-GUIDE.md (user guide)"
fi
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Upload ${PACKAGE_NAME}.zip to Google Drive"
echo "  2. Share the link with users"
echo "  3. Users download, extract, and open README.html"
echo ""

