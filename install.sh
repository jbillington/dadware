#!/bin/bash
#
# Dad Ware One-Command Installer
# Usage: bash install.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "═══════════════════════════════════════════════════"
echo " 📋 DAD WARE INSTALLER"
echo "═══════════════════════════════════════════════════"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ Error: This tool only works on macOS${NC}"
    exit 1
fi

# Check Python 3 installation
echo -e "${BLUE}Checking for Python 3...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
    else
        echo -e "${YELLOW}⚠ Python $PYTHON_VERSION found, but 3.9+ is recommended${NC}"
        echo -e "${YELLOW}  Tool may still work, but consider upgrading${NC}"
    fi
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    echo ""
    echo "Please install Python 3.9 or higher:"
    echo "  1. Visit: https://www.python.org/downloads/"
    echo "  2. Download the macOS installer (~50 MB)"
    echo "  3. Run the installer"
    echo "  4. Run this script again"
    echo ""
    exit 1
fi

# Determine installation directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="$HOME/.dadware"
BIN_DIR="$HOME/.local/bin"

echo ""
echo -e "${BLUE}Installation settings:${NC}"
echo "  • Tool location: $INSTALL_DIR"
echo "  • Command location: $BIN_DIR"
echo ""

# Ask for confirmation
read -p "Continue with installation? [Y/n] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
    echo "Installation cancelled."
    exit 0
fi

# Create directories
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$INSTALL_DIR/reports"

# Copy files
echo -e "${BLUE}Copying files...${NC}"
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"

# Make executable
chmod +x "$INSTALL_DIR/askdad"

# Create symlink in bin directory
echo -e "${BLUE}Creating command shortcut...${NC}"
ln -sf "$INSTALL_DIR/askdad" "$BIN_DIR/askdad"

# Check if bin directory is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo -e "${YELLOW}⚠ $BIN_DIR is not in your PATH${NC}"
    echo ""
    echo "To use the 'askdad' command from anywhere, add this line to your shell config:"
    echo ""

    if [ -f "$HOME/.zshrc" ]; then
        echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
        echo "  source ~/.zshrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bash_profile"
        echo "  source ~/.bash_profile"
    else
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
    echo ""
fi

# Success message
echo ""
echo "═══════════════════════════════════════════════════"
echo -e "${GREEN}✓ Installation complete!${NC}"
echo "═══════════════════════════════════════════════════"
echo ""
echo "QUICK START:"
echo ""
echo "  Option 1: Run the menu (recommended)"
if [[ ":$PATH:" == *":$BIN_DIR:"* ]]; then
    echo "    $ askdad"
else
    echo "    $ ~/.local/bin/askdad"
fi
echo ""
echo "  Option 2: Run commands directly"
echo "    $ cd ~/.dadware"
echo "    $ python3 askdad.py cpu"
echo ""
echo "DOCUMENTATION:"
echo "  • Reports saved to: ~/.dadware/reports/"
echo ""
echo "NEED HELP?"
if [[ ":$PATH:" == *":$BIN_DIR:"* ]]; then
    echo "  $ askdad"
else
    echo "  $ ~/.local/bin/askdad"
fi
echo "  Then choose option 4 for help"
echo ""
echo "═══════════════════════════════════════════════════"
