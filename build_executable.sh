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

# Locate PyInstaller. Checked in order of how explicit the choice is:
# an activated environment or global install on PATH wins, then the repo's
# own venv/ (the setup docs/CLAUDE.md tell you to create, whose pyinstaller
# is NOT on PATH unless you activate it), then a global python3. Whichever
# interpreter wins is reused for the version probe below, so the build and
# the numbers stamped into it never come from two different Pythons.
PYINSTALLER_CMD=()
PYTHON_CMD="python3"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
if command -v pyinstaller &> /dev/null; then
    PYINSTALLER_CMD=(pyinstaller)
    if [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
        PYTHON_CMD="$VIRTUAL_ENV/bin/python"
    fi
elif [ -x "$VENV_PYTHON" ] && "$VENV_PYTHON" -m PyInstaller --version &> /dev/null; then
    PYINSTALLER_CMD=("$VENV_PYTHON" -m PyInstaller)
    PYTHON_CMD="$VENV_PYTHON"
elif python3 -m PyInstaller --version &> /dev/null; then
    PYINSTALLER_CMD=(python3 -m PyInstaller)
else
    echo -e "${RED}❌ PyInstaller not found!${NC}"
    echo ""
    echo "Install it into this project's venv (the setup the docs assume):"
    echo "  python3 -m venv venv && ./venv/bin/pip install -r requirements-dev.txt"
    echo ""
    echo "Or install it globally:"
    echo "  python3 -m pip install --user pyinstaller"
    echo ""
    exit 1
fi

# Bake in a build stamp before PyInstaller runs, since there's no .git
# directory inside a frozen app for utils/version.py to derive one from.
# Always clean up the stamp file afterwards - even on failure - so a stale
# stamp can never leak into a later `python askdad.py` run from source.
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
else
    echo -e "${YELLOW}⚠️  Could not determine build from git; PyInstaller build will fall back to the literal default.${NC}"
fi

# Ask Python for the values it will actually report, so what we print here
# matches what the built executable reports (same resolution logic either way).
VERSION=$("$PYTHON_CMD" -c "from utils.version import VERSION; print(VERSION)" 2>/dev/null || echo "0.7")
BUILD=$("$PYTHON_CMD" -c "from utils.version import BUILD; print(BUILD)" 2>/dev/null || echo "unknown")

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

"${PYINSTALLER_CMD[@]}" askdad.spec

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

# Check if executable was created
EXECUTABLE="dist/askdad"
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
echo "  1. Test it: ./dist/askdad cpu"
echo "  2. Copy it anywhere: cp dist/askdad ~/bin/"
echo "  3. Share it: No Python required for end users!"
echo ""
echo -e "${YELLOW}Note:${NC} First run may show a security warning."
echo "      Right-click → Open (first time only)"
echo ""

