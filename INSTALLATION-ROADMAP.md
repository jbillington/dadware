# Installation Roadmap - Simple Path Forward

**Goal:** Get Dad Ware installable via Homebrew, then create compiled Python binary  
**Status:** Ready to implement

---

## Current State ✅

- Working Python CLI application
- Homebrew formula exists (just fixed)
- Version management in code
- No external dependencies

## Target State 🎯

1. **Homebrew:** `brew install --build-from-source ./Formula/yourdad.rb` works
2. **Binary:** Standalone executable works without Python

---

## Quick Start Guide

### Step 1: Test Homebrew (Today)

```bash
# Test the formula
brew install --build-from-source ./Formula/yourdad.rb

# Verify it works
yourdad --version
yourdad scan cpu --terminal
```

**If it works:** ✅ Homebrew is ready!  
**If it fails:** Check error and fix (see action plan below)

### Step 2: Create Binary (This Week)

```bash
# Install PyInstaller
pip install pyinstaller

# Build binary (we'll create the spec file)
pyinstaller --onefile --name yourdad yourdad.py

# Test it
./dist/yourdad --version
```

---

## Detailed Plans

### 📋 Full Roadmap
See: `docs/roadmap/DISTRIBUTION-ROADMAP.md`
- Complete distribution strategy
- Phase-by-phase implementation
- Testing checklist

### 🎯 Action Plan
See: `docs/roadmap/INSTALLATION-ACTION-PLAN.md`
- Step-by-step instructions
- Immediate next steps
- Testing procedures

---

## What's Been Done

### ✅ Fixed Homebrew Formula
- Uses system Python (`/usr/bin/python3`) to avoid QGIS conflicts
- Proper PYTHONPATH setup
- Correct file paths
- Ready for local testing

### ✅ Version Management
- Version in code: `VERSION = "0.1-poc"`
- `--version` flag works
- Build numbers tracked

---

## What's Next

### Immediate (Today)
1. **Test Homebrew formula**
   ```bash
   brew install --build-from-source ./Formula/yourdad.rb
   ```

2. **Fix any issues** found during testing

### This Week
1. **Get Homebrew working** end-to-end
2. **Set up PyInstaller** for binary builds
3. **Test both methods** on clean systems

### Next Week
1. **Create release process**
2. **Build first distribution packages**
3. **Document installation methods**

---

## Files to Know

### Core Files
- `Formula/yourdad.rb` - Homebrew formula (just fixed)
- `yourdad.py` - Main application
- `build_distribution.sh` - Distribution builder

### Documentation
- `docs/roadmap/DISTRIBUTION-ROADMAP.md` - Complete strategy
- `docs/roadmap/INSTALLATION-ACTION-PLAN.md` - Step-by-step plan
- `README.md` - User documentation

---

## Testing

### Homebrew Test
```bash
# Install
brew install --build-from-source ./Formula/yourdad.rb

# Test commands
yourdad --version
yourdad scan cpu --terminal
yourdad scan storage --terminal
```

### Binary Test (after building)
```bash
# Test on system without Python
./dist/yourdad --version
./dist/yourdad scan cpu --terminal
```

---

## Common Issues

### Homebrew
- **"No such file"**: Make sure you're in the project root
- **Python not found**: Formula uses `/usr/bin/python3` (system Python)
- **QGIS conflict**: Formula explicitly uses system Python to avoid this

### Binary
- **Security warning**: First run requires right-click → Open
- **"Command not found"**: Make sure binary is executable: `chmod +x yourdad`

---

## Next Action

**Right now:** Test the Homebrew formula:
```bash
brew install --build-from-source ./Formula/yourdad.rb
```

If it works, you're ready to move to binary builds!  
If it fails, check the error and see `docs/roadmap/INSTALLATION-ACTION-PLAN.md` for fixes.

---

**Last Updated:** December 2025  
**Status:** Ready to test


