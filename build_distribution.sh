#!/bin/bash
#
# Build distribution zip file for Livvy
# Creates yourdad-for-livvy.zip with all necessary files
#

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "═══════════════════════════════════════════════════"
echo " 📦 Building Dad Ware Distribution Package"
echo "═══════════════════════════════════════════════════"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Distribution name
DIST_NAME="yourdad-for-livvy"
ZIP_FILE="${DIST_NAME}.zip"
TEMP_DIR="${DIST_NAME}"

# Clean up any existing build
echo -e "${BLUE}Cleaning up old build...${NC}"
rm -rf "$TEMP_DIR" "$ZIP_FILE"

# Create distribution directory
echo -e "${BLUE}Creating distribution directory...${NC}"
mkdir -p "$TEMP_DIR"

# Copy Python source files
echo -e "${BLUE}Copying Python modules...${NC}"
cp yourdad.py "$TEMP_DIR/"
cp yourdad "$TEMP_DIR/"  # Menu launcher
chmod +x "$TEMP_DIR/yourdad"

# Copy package directories
cp -r personality "$TEMP_DIR/"
cp -r scanners "$TEMP_DIR/"
cp -r renderers "$TEMP_DIR/"
cp -r utils "$TEMP_DIR/"

# Copy documentation
echo -e "${BLUE}Copying documentation...${NC}"
cp index.html "$TEMP_DIR/"

# Create a simple README for Livvy
cat > "$TEMP_DIR/README.txt" << 'EOF'
📋 DAD WARE - Your Mac's Report Card
═══════════════════════════════════════

QUICK START:
1. Double-click "index.html" to read the full instructions
2. Open Terminal (Cmd+Space → type "Terminal")
3. Navigate here: cd ~/Downloads/yourdad-for-livvy
4. Run: python3 yourdad.py scan cpu
   OR: ./yourdad (for menu)

WHAT IT DOES:
• Checks memory/CPU usage
• Finds large files taking up space
• Shows Mac app library sizes (Photos, Music, etc.)
• Opens beautiful HTML reports in your browser

NEED HELP?
• Open index.html in your browser for full docs
• All reports saved to: ~/.dadware/reports/

═══════════════════════════════════════
Made with ❤️ for Livvy
EOF

# Remove unnecessary files from copied directories
echo -e "${BLUE}Cleaning up unnecessary files...${NC}"

# Remove __pycache__ directories
find "$TEMP_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true

# Remove any .pyc files
find "$TEMP_DIR" -name "*.pyc" -delete 2>/dev/null || true

# Remove test/development files from scanners
rm -f "$TEMP_DIR/scanners/report-card-ideas.md" 2>/dev/null || true

# Create zip file
echo -e "${BLUE}Creating zip file...${NC}"
zip -r "$ZIP_FILE" "$TEMP_DIR" -q

# Clean up temp directory
rm -rf "$TEMP_DIR"

# Get file size
ZIP_SIZE=$(du -h "$ZIP_FILE" | cut -f1)

echo ""
echo "═══════════════════════════════════════════════════"
echo -e "${GREEN}✓ Distribution package created!${NC}"
echo "═══════════════════════════════════════════════════"
echo ""
echo "File: $ZIP_FILE"
echo "Size: $ZIP_SIZE"
echo ""
echo "Location: $SCRIPT_DIR/$ZIP_FILE"
echo ""
echo "Ready to transfer to Livvy's machine! 🚀"
echo ""

