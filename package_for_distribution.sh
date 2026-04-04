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
if [ ! -f "dist/yourdad" ]; then
    echo -e "${RED}❌ Executable not found!${NC}"
    echo ""
    echo "Please build the executable first:"
    echo "  ./build_executable.sh"
    echo ""
    exit 1
fi

# Get version and build from yourdad.py
VERSION="0.1-poc"
BUILD="unknown"
if [ -f "yourdad.py" ]; then
    VERSION=$(grep '^VERSION =' yourdad.py | sed 's/.*"\(.*\)".*/\1/' || echo "0.1-poc")
    BUILD=$(grep '^BUILD =' yourdad.py | sed 's/.*"\(.*\)".*/\1/' | sed 's/ .*//' || echo "unknown")
fi

echo -e "${BLUE}Version:${NC} $VERSION"
echo -e "${BLUE}Build:${NC} $BUILD"
echo ""

# Create package directory
PACKAGE_DIR="package"
PACKAGE_NAME="yourdad-${VERSION}-${BUILD}"

echo -e "${BLUE}Creating package directory...${NC}"
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# Copy executable
echo -e "${BLUE}Copying executable...${NC}"
cp dist/yourdad "$PACKAGE_DIR/"

# Copy README files
echo -e "${BLUE}Copying README files...${NC}"
cp README.md "$PACKAGE_DIR/"
if [ -f "docs/USER-GUIDE.md" ]; then
    cp docs/USER-GUIDE.md "$PACKAGE_DIR/"
fi

# Generate HTML README
echo -e "${BLUE}Generating HTML README...${NC}"
if [ -f "scripts/generate_html_readme.py" ]; then
    python3 scripts/generate_html_readme.py "$PACKAGE_DIR/README.html"
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
echo "  - yourdad (executable)"
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

