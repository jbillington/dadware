#!/bin/bash
#
# Build executable binary for Dad Ware using PyInstaller
# This creates a standalone executable that bundles Python and all dependencies
# No Python installation required for end users!
#

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "═══════════════════════════════════════════════════"
echo " 🔨 Building Dad Ware Executable"
echo "═══════════════════════════════════════════════════"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if PyInstaller is installed (try both methods)
PYINSTALLER_CMD=""
if command -v pyinstaller &> /dev/null; then
    PYINSTALLER_CMD="pyinstaller"
elif python3 -m PyInstaller --version &> /dev/null; then
    PYINSTALLER_CMD="python3 -m PyInstaller"
else
    echo -e "${RED}❌ PyInstaller not found!${NC}"
    echo ""
    echo "Install it with:"
    echo "  python3 -m pip install --user pyinstaller"
    echo ""
    echo "Or if using a virtual environment:"
    echo "  source venv/bin/activate"
    echo "  pip install pyinstaller"
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

# Clean up old builds
echo -e "${BLUE}Cleaning up old builds...${NC}"
rm -rf build/ dist/ __pycache__/
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Build executable
echo -e "${BLUE}Building executable with PyInstaller...${NC}"
echo ""

$PYINSTALLER_CMD yourdad.spec

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

# Check if executable was created
EXECUTABLE="dist/yourdad"
if [ ! -f "$EXECUTABLE" ]; then
    echo -e "${RED}❌ Executable not found at $EXECUTABLE${NC}"
    exit 1
fi

# Get executable size
EXEC_SIZE=$(du -h "$EXECUTABLE" | cut -f1)

echo ""
echo "═══════════════════════════════════════════════════"
echo -e "${GREEN}✓ Executable built successfully!${NC}"
echo "═══════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}Executable:${NC} $EXECUTABLE"
echo -e "${GREEN}Size:${NC} $EXEC_SIZE"
echo ""
echo "You can now:"
echo "  1. Test it: ./dist/yourdad cpu"
echo "  2. Copy it anywhere: cp dist/yourdad ~/bin/"
echo "  3. Share it: No Python required for end users!"
echo ""
echo -e "${YELLOW}Note:${NC} First run may show a security warning."
echo "      Right-click → Open (first time only)"
echo ""

