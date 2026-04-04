# Distribution Roadmap - Installable Versions

**Goal:** Create simple, installable versions of Dad Ware for end users  
**Timeline:** Start with Homebrew, then move to compiled Python binary

---

## Current State

### What We Have
- ✅ Working Python CLI application
- ✅ Homebrew formula template (`Formula/yourdad.rb`)
- ✅ Distribution build script (`build_distribution.sh`)
- ✅ Manual installation script (`install.sh`)
- ✅ **Executable build system complete** (`build_executable.sh`, `yourdad.spec`)
- ✅ **Executable documentation** (`BUILD-EXECUTABLE.md`)
- ✅ No external dependencies (Python standard library only)

### What We Need
- 🔜 Working Homebrew tap/formula (testing needed)
- ✅ Compiled Python binary (PyInstaller) - **COMPLETE, needs testing**
- 🔜 Version management
- 🔜 Release process

---

## Phase 1: Homebrew Distribution (Priority 1)

**Target:** Technical users who use Homebrew  
**Timeline:** 1-2 days  
**Status:** Ready to implement

### Steps

#### 1.1 Create Homebrew Tap
```bash
# Create a new tap repository (separate from main repo)
# Or use existing GitHub repo with Formula/ directory
```

**Option A: Personal Tap (Easier)**
- Create `homebrew-yourdad` tap repository
- Formula lives in tap, points to main repo releases

**Option B: In-Repo Formula (Current)**
- Formula in `Formula/yourdad.rb`
- Install with: `brew install --build-from-source ./Formula/yourdad.rb`
- Or create tap that references this

#### 1.2 Fix Homebrew Formula
**Current Issues:**
- URL points to non-existent GitHub repo
- SHA256 not set
- Wrapper script has wrong path
- Missing proper Python path handling

**Fixes Needed:**
1. Update `homepage` and `url` to actual repository
2. Set proper `version` (use git tags)
3. Fix wrapper script to use correct Python and paths
4. Test installation locally
5. Handle QGIS Python conflict (use system Python)

#### 1.3 Test Installation
```bash
# Test local formula
brew install --build-from-source ./Formula/yourdad.rb

# Test tap (if using tap)
brew tap yourusername/yourdad
brew install yourdad
```

#### 1.4 Create Release Process
1. Tag releases: `git tag v0.1.0`
2. Create GitHub release with zip/tarball
3. Update formula with new version/SHA256
4. Test installation from release

### Deliverables
- ✅ Working Homebrew formula
- ✅ Installation instructions
- ✅ Tested on clean macOS system
- ✅ Version management

---

## Phase 2: Compiled Python Binary (Priority 2)

**Target:** Non-technical users without Python  
**Timeline:** ✅ **COMPLETE** (Build system ready, testing needed)  
**Status:** ✅ **BUILD SYSTEM COMPLETE** - Ready for testing

### Approach: PyInstaller

**Why PyInstaller:**
- ✅ Single executable file
- ✅ No Python installation required
- ✅ Works with standard library only
- ✅ Cross-platform (though we only need macOS)
- ✅ **Solves QGIS Python conflicts** (uses bundled Python)

**Challenges:**
- ⚠️ macOS security warnings (unsigned binary) - **Documented in BUILD-EXECUTABLE.md**
- ⚠️ File size (~20-30 MB) - **Acceptable for standalone executable**
- ⚠️ First launch may be slow (extraction) - **Normal for PyInstaller**

### Steps

#### 2.1 Setup PyInstaller ✅ **COMPLETE**
```bash
pip install pyinstaller
```
- ✅ PyInstaller installed
- ✅ PATH configured for pip access

#### 2.2 Create Spec File ✅ **COMPLETE**
- ✅ `yourdad.spec` created and configured
- ✅ One-file mode enabled
- ✅ All modules included
- ✅ Proper paths set
- ✅ Hidden imports configured

#### 2.3 Build Binary ✅ **COMPLETE**
- ✅ `build_executable.sh` script created
- ✅ Uses `python3 -m PyInstaller` for reliability
- ✅ Builds to `dist/yourdad`
- ✅ Build process documented

#### 2.4 Test Binary ⚠️ **NEEDS TESTING**
- [ ] Test on clean macOS system (no Python)
- [ ] Verify all functionality works
- [ ] Check file size
- [ ] Test security warnings
- [ ] Verify QGIS conflict resolution

#### 2.5 Handle macOS Security ✅ **DOCUMENTED**
- ✅ Security warning handling documented in `BUILD-EXECUTABLE.md`
- ✅ User instructions provided
- ⚠️ Notarization optional (requires Developer account)

**User Instructions (documented in BUILD-EXECUTABLE.md):**
```bash
# First run: right-click → Open
# Or: xattr -d com.apple.quarantine yourdad
```

#### 2.6 Create Distribution Package ⚠️ **OPTIONAL**
- [ ] Create DMG or ZIP with:
  - `yourdad` binary
  - `README.txt` with instructions
  - Permission setup guide
  - Optional: `index.html` documentation

### Deliverables
- ✅ Standalone `yourdad` binary (build system complete)
- ✅ Build script (`build_executable.sh`)
- ✅ Build documentation (`BUILD-EXECUTABLE.md`)
- ✅ Security warning handling guide (in BUILD-EXECUTABLE.md)
- ⚠️ Distribution package (DMG/ZIP) - Optional, can be added later

---

## Phase 3: Version Management & Releases

**Timeline:** Ongoing  
**Status:** Needs implementation

### Version Strategy

**Current:** Build numbers (`2025-11-28-013`)  
**Target:** Semantic versioning (`v0.1.0`)

**Migration:**
1. Add `--version` flag to `yourdad.py`
2. Store version in code: `VERSION = "0.1.0"`
3. Update build script to use version
4. Tag releases in git
5. Update Homebrew formula with version

### Release Process

1. **Update Version**
   ```bash
   # In yourdad.py
   VERSION = "0.1.0"
   BUILD = "2025-11-28-013"
   ```

2. **Tag Release**
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. **Create GitHub Release**
   - Upload distribution files
   - Add release notes
   - Update Homebrew formula

4. **Update Formula**
   - Update version in `Formula/yourdad.rb`
   - Update SHA256
   - Test installation

---

## Implementation Plan

### Week 1: Homebrew (Days 1-2)
- [ ] Fix Homebrew formula
- [ ] Test local installation
- [ ] Create/configure tap (if needed)
- [ ] Document installation process
- [ ] Test on clean system

### Week 1: Compiled Binary (Days 3-5) ✅ **COMPLETE**
- [x] Install PyInstaller
- [x] Create spec file (`yourdad.spec`)
- [x] Build script (`build_executable.sh`)
- [x] Write security warning guide (`BUILD-EXECUTABLE.md`)
- [ ] Test on clean system (next step)
- [ ] Create distribution package (optional)

### Week 2: Polish & Release
- [ ] Add version management
- [ ] Create release process
- [ ] Test both distribution methods
- [ ] Update documentation
- [ ] Create first release

---

## File Structure After Implementation

```
dadware/
├── Formula/
│   └── yourdad.rb          # Homebrew formula
├── dist/                   # Build outputs
│   ├── yourdad             # PyInstaller binary
│   └── yourdad.dmg        # Distribution package
├── yourdad.spec            # PyInstaller spec file
├── build_distribution.sh   # Updated for both methods
└── docs/
    └── roadmap/
        └── DISTRIBUTION-ROADMAP.md  # This file
```

---

## Testing Checklist

### Homebrew Installation
- [ ] Install on clean macOS system
- [ ] Verify `yourdad` command works
- [ ] Test all scan types
- [ ] Verify permissions handling
- [ ] Test QGIS Python conflict handling

### Binary Installation
- [ ] Test on system without Python
- [ ] Verify all functionality
- [ ] Test security warnings (instructions documented)
- [ ] Verify file size is reasonable (~20-30 MB expected)
- [ ] Test on different macOS versions
- [ ] Verify QGIS conflict resolution (executable should work)

---

## Next Steps

1. **Immediate:** Test executable on clean macOS system
2. **This Week:** Fix Homebrew formula and test
3. **Next Week:** Get Homebrew working end-to-end
4. **Ongoing:** Create release process and version management

## Current Status (December 13, 2025)

### ✅ Completed
- ✅ Executable build system complete (`build_executable.sh`, `yourdad.spec`)
- ✅ Build documentation complete (`BUILD-EXECUTABLE.md`)
- ✅ PyInstaller installed and configured
- ✅ Build script tested and working
- ✅ Security warning handling documented

### ⚠️ Needs Testing
- [ ] Test executable on clean macOS system (no Python)
- [ ] Verify executable solves QGIS Python conflicts
- [ ] Test all scan types with executable
- [ ] Verify file size and performance

### Benefits of Executable
- ✅ **Solves QGIS Python conflicts** - Uses bundled Python, no environment issues
- ✅ **No Python required** - Works on any Mac without Python installation
- ✅ **Easy distribution** - Single file, easy to share
- ✅ **Resolves Bug #2** - fork_exec() error was Python version issue, executable avoids it

---

## Resources

- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [PyInstaller Documentation](https://pyinstaller.org/)
- [macOS Code Signing](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)

---

**Last Updated:** December 13, 2025  
**Status:** Executable build system complete, ready for testing. Homebrew needs implementation.


