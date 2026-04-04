#!/bin/bash
#
# Installation script for yourdad (Dad Ware)
# Checks Python version, installs dependencies, and sets up permissions
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "=========================================="
echo "  Dad Ware Installation"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    echo "   Please install Python 3.9 or later"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo "❌ Error: Python 3.9 or later required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"
echo ""

# Check for dependencies file
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "Installing Python dependencies..."
    python3 -m pip install --user -r "$PROJECT_DIR/requirements.txt" || {
        echo "⚠️  Warning: Some dependencies may have failed to install"
        echo "   The app may still work if using only standard library"
    }
    echo ""
fi

# Create symlink (optional)
read -p "Create symlink 'yourdad' in /usr/local/bin? (requires sudo) [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -w "/usr/local/bin" ] || sudo -n true 2>/dev/null; then
        if [ -w "/usr/local/bin" ]; then
            ln -sf "$PROJECT_DIR/yourdad.py" /usr/local/bin/yourdad
            chmod +x /usr/local/bin/yourdad
        else
            sudo ln -sf "$PROJECT_DIR/yourdad.py" /usr/local/bin/yourdad
            sudo chmod +x /usr/local/bin/yourdad
        fi
        echo "✅ Symlink created: /usr/local/bin/yourdad"
        echo ""
    else
        echo "⚠️  Could not create symlink (permission denied)"
        echo "   You can run the script directly: python3 $PROJECT_DIR/yourdad.py"
        echo ""
    fi
fi

# Check permissions
echo "=========================================="
echo "  Permission Setup"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: Full Disk Access Required"
echo ""
echo "To scan Photos, Messages, and Mail libraries, you need to grant"
echo "Full Disk Access to Terminal (or your IDE):"
echo ""
echo "  1. Open System Settings → Privacy & Security"
echo "  2. Scroll to 'Full Disk Access'"
echo "  3. Click the lock icon and enter your password"
echo "  4. Click '+' and add Terminal.app (or your IDE)"
echo "  5. Make sure the checkbox is checked ✅"
echo "  6. Restart Terminal/IDE"
echo ""
read -p "Would you like to check permissions now? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 "$PROJECT_DIR/scripts/check_permissions.py"
fi

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "Run scans with:"
if [ -f "/usr/local/bin/yourdad" ]; then
    echo "  yourdad scan storage"
else
    echo "  python3 $PROJECT_DIR/yourdad.py scan storage"
fi
echo ""
echo "Check permissions anytime with:"
echo "  python3 $PROJECT_DIR/scripts/check_permissions.py"
echo ""

