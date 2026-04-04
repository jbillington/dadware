# Installation Action Plan - Simple Path to Installable Versions

**Goal:** Get Dad Ware installable via Homebrew, then create compiled Python binary  
**Timeline:** Week 1 (Homebrew), Week 2 (Binary)

---

## Quick Status

### Current State
- ✅ Working Python CLI
- ✅ Homebrew formula exists (needs fixes)
- ✅ Version management in code (`VERSION = "0.1-poc"`)
- ✅ `--version` flag implemented
- ⚠️ Formula needs fixes for proper installation

### Target State
- ✅ `brew install yourdad` works
- ✅ Standalone binary works without Python
- ✅ Simple release process

---

## Phase 1: Fix Homebrew (Days 1-2)

### Step 1: Test Current Formula
```bash
cd /path/to/dadware
brew install --build-from-source ./Formula/yourdad.rb
```

**Expected Issues:**
- URL points to non-existent repo (will fail for remote install)
- Wrapper script paths may be wrong
- Need to test on clean system

### Step 2: Fix Formula Issues

**Fixed in formula:**
- ✅ Use system Python (`/usr/bin/python3`) to avoid QGIS conflicts
- ✅ Proper PYTHONPATH setup
- ✅ Correct file paths
- ✅ Local file:// URL for development

**Still needed:**
- [ ] Test installation locally
- [ ] Create GitHub release process
- [ ] Update formula for remote installation (when ready)

### Step 3: Test Installation
```bash
# Install
brew install --build-from-source ./Formula/yourdad.rb

# Test
yourdad --version
yourdad scan cpu
yourdad scan storage --terminal
```

### Step 4: Create Tap (Optional)
If you want `brew install yourdad` without `--build-from-source`:

1. Create `homebrew-yourdad` repository
2. Move formula there
3. Users install with: `brew tap yourusername/yourdad && brew install yourdad`

**OR** keep it simple and use local formula for now.

---

## Phase 2: Compiled Python Binary (Days 3-5)

### Step 1: Install PyInstaller
```bash
pip install pyinstaller
```

### Step 2: Create Spec File
Create `yourdad.spec`:
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['yourdad.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='yourdad',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

### Step 3: Build Binary
```bash
pyinstaller yourdad.spec
```

**Output:** `dist/yourdad` (executable)

### Step 4: Test Binary
```bash
# Test on system without Python (or different Python)
./dist/yourdad --version
./dist/yourdad scan cpu
```

### Step 5: Handle macOS Security
**Option A: Provide Instructions**
Create `INSTALL-BINARY.md` with:
- Right-click → Open (first time)
- Or: `xattr -d com.apple.quarantine yourdad`

**Option B: Code Sign (Future)**
- Requires Apple Developer account ($99/year)
- Sign with: `codesign --sign "Developer ID" yourdad`
- Notarize with Apple

### Step 6: Create Distribution Package
Update `build_distribution.sh` to:
1. Build PyInstaller binary
2. Create ZIP/DMG with:
   - `yourdad` binary
   - `README.txt`
   - `GRANT-PERMISSIONS.md`
   - `index.html` (optional)

---

## Phase 3: Version Management (Ongoing)

### Current
- Version in code: `VERSION = "0.1-poc"`
- Build number: `BUILD = "2025-11-28-013"`
- `--version` flag works

### Needed
1. **Semantic Versioning**
   - Move to `v0.1.0`, `v0.2.0`, etc.
   - Keep BUILD for internal tracking

2. **Git Tags**
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. **Release Process**
   - Tag release
   - Create GitHub release
   - Update Homebrew formula (if using tap)
   - Build and upload binary

---

## Immediate Next Steps (Today)

### Priority 1: Test Homebrew Formula
```bash
# 1. Test local installation
brew install --build-from-source ./Formula/yourdad.rb

# 2. Verify it works
yourdad --version
yourdad scan cpu --terminal

# 3. Fix any issues found
```

### Priority 2: Create PyInstaller Setup
```bash
# 1. Install PyInstaller
pip install pyinstaller

# 2. Create spec file (use template above)

# 3. Test build
pyinstaller yourdad.spec

# 4. Test binary
./dist/yourdad --version
```

### Priority 3: Update Build Script
- Add PyInstaller build option
- Create distribution packages for both methods

---

## Testing Checklist

### Homebrew
- [ ] Install on clean macOS
- [ ] `yourdad --version` works
- [ ] `yourdad scan cpu` works
- [ ] `yourdad scan storage` works
- [ ] QGIS Python conflict handled
- [ ] Permissions guidance shown

### Binary
- [ ] Builds successfully
- [ ] Works on system without Python
- [ ] All scan types work
- [ ] File size reasonable (~20-30 MB)
- [ ] Security warnings documented
- [ ] Test on different macOS versions

---

## File Changes Needed

### Already Done
- ✅ Formula updated with system Python
- ✅ Version management in code
- ✅ `--version` flag implemented

### To Do
- [ ] Create `yourdad.spec` for PyInstaller
- [ ] Update `build_distribution.sh` for binary builds
- [ ] Create `INSTALL-BINARY.md` with security instructions
- [ ] Test both installation methods
- [ ] Document release process

---

## Success Criteria

### Homebrew
- ✅ `brew install --build-from-source ./Formula/yourdad.rb` works
- ✅ `yourdad` command available after install
- ✅ All functionality works
- ✅ Clear permission instructions

### Binary
- ✅ Single executable file
- ✅ Works without Python installed
- ✅ All functionality works
- ✅ Security warnings handled

---

## Resources

- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/usage.html)
- [macOS Code Signing](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)

---

**Next Action:** Test Homebrew formula installation locally


