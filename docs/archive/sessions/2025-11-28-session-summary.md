# Session Summary - November 28, 2025

## Overview
This session focused on bug fixes, documentation organization, and preparing distribution packages for external testing (Max, Graham, Livvy, Rosemary).

---

## Major Accomplishments

### 1. Bug Fixes (3 bugs fixed)

#### Bug #1: Safari Font Rendering Issue ✅ FIXED (Build 2025-11-28-008)
- **Problem:** HTML reports displayed Chinese/Kanji characters in Safari (but worked in Chrome)
- **Root Cause:** Safari fails to render italic text with system fonts (`-apple-system`)
- **Fix:** Changed font-family to explicit `'Helvetica Neue', Helvetica, Arial, sans-serif` and removed `font-style: italic`
- **Files:** `renderers/html.py`

#### Bug #4: Memory Pressure Calculation Mismatch ✅ FIXED (Build 2025-11-28-012)
- **Problem:** Memory pressure showed "high" when only 53% RAM used (7.5 GB free)
- **Root Cause:** Pressure calculation used only `vm_stat` "Pages free" (~0.1 GB) instead of available memory (free + inactive = ~7.5 GB)
- **Fix:** Changed to use available memory (free + inactive) for pressure calculation
- **Files:** `scanners/cpu.py` - `get_memory_pressure()`

#### Bug #5: Docker Container Size Miscalculation ✅ FIXED (Build 2025-11-28-013)
- **Problem:** Docker containers reported as 1TB+ on 500GB drives (total storage shown as 1.5TB)
- **Root Cause:** Sparse files (Docker containers, virtual disks) report huge logical sizes but use little actual disk space. Scanner used `os.path.getsize()` which returns logical size.
- **Fix:** 
  - Changed all file size calculations to use `os.stat().st_blocks * 512` for actual disk usage
  - Added Docker path and virtual disk format exclusions (.qcow2, .vmdk, .vdi, etc.)
- **Files:** `scanners/storage.py` - all file size calculations

### 2. Bug #2: fork_exec() Error - IN PROGRESS
- **Status:** Diagnostic logging added (Build 2025-11-28-011), but bug still occurs on Max's machine
- **Error:** `fork_exec() takes exactly 23 arguments (21 given)` during "all" scan
- **Action Taken:** 
  - Added comprehensive diagnostic logging to all `subprocess.run()` calls
  - Added defensive checks for None/invalid parameters
  - Waiting for Max to run diagnostic version and provide output
- **Files Modified:** `scanners/cpu.py`, `utils/permissions.py`, `utils/system_info.py`, `scanners/mac_libraries.py`, `yourdad.py`

### 3. QGIS Python Conflict - RESOLVED
- **Problem:** Max's machine has QGIS installed, which bundles its own Python. When running `python3`, it used QGIS Python causing "SRE module mismatch" error
- **Fix:** 
  - Updated `yourdad.py` shebang from `#!/usr/bin/env python3` to `#!/usr/bin/python3`
  - Updated menu script to detect and avoid QGIS Python
  - Added troubleshooting documentation
- **Files:** `yourdad.py`, `yourdad` (menu script), `README.md`, `index.html`

### 4. Documentation Organization
- **Created:** `docs/` directory structure
  - `docs/roadmap/` - Future features and planning (excluded from git)
  - `docs/archive/` - Historical/completed planning docs
  - `docs/UX-HISTORY.md` - Combined UX planning history
  - `docs/REPORT-LOCATION.md` - Combined report location docs
- **Moved to roadmap:**
  - `ROADMAP.md`, `yourdad-prd.md`, `design.md`, `REFACTOR-PLAN.md`
  - `BUG-LOG.md`, `BUG-FIX-PLAN.md`, `DISTRIBUTION.md`
  - All feature PRDs (text-ui, animations, review-workspace, space-wasters)
- **Root directory cleanup:** Only 6 .md files remain (README, RELEASE-NOTES, GRANT-PERMISSIONS, LICENSE, plus 2 in docs/)

### 5. Feature Enhancement Logged
- **Enhancement:** Single Volume Confirmation
- **Status:** Planned (not implemented yet)
- **Description:** When only 1 volume available, show confirmation prompt instead of selection menu
- **File:** `docs/roadmap/FEATURE-ENHANCEMENTS.md`

---

## Current Build Status

**Current Build:** `2025-11-28-013`
- Bug #4: Memory pressure calculation fix
- Bug #5: Docker container size fix
- Diagnostic logging enabled for subprocess calls
- QGIS Python conflict handling

**Previous Builds:**
- `2025-11-28-012`: Memory pressure calculation fix
- `2025-11-28-011`: Diagnostic logging for subprocess calls
- `2025-11-28-010`: Defensive checks for subprocess calls
- `2025-11-28-009`: Fixed free memory calculation

---

## Distribution Packages Created

1. **dadware-max.zip** (Build 2025-11-28-013)
   - Includes all bug fixes
   - Diagnostic logging enabled
   - QGIS Python conflict handling
   - Ready for Max to test

---

## Open Issues

### Bug #2: fork_exec() Error
- **Status:** Waiting for diagnostic output from Max
- **Next Steps:** 
  - Max needs to run: `python3 yourdad.py scan all 2>&1 | tee scan-output.txt`
  - Review diagnostic output to identify exact failing subprocess call
  - Fix the root cause once identified

### Bug #3: Performance Degradation
- **Status:** Open (not addressed yet)
- **Issue:** Scan becomes very slow after ~1M files
- **Affected:** Systems with iCloud Drive containing many code repos
- **Planned Fixes:** Use `os.scandir()`, better symlink handling, directory-level timeouts

---

## Key Files Modified This Session

### Core Functionality
- `scanners/cpu.py` - Memory pressure calculation, diagnostic logging
- `scanners/storage.py` - Docker/sparse file handling, actual disk usage
- `scanners/mac_libraries.py` - Defensive checks
- `utils/permissions.py` - Defensive checks, diagnostic logging
- `utils/system_info.py` - Defensive checks, diagnostic logging
- `yourdad.py` - Error handling, diagnostic logging, QGIS fix
- `yourdad` (menu script) - QGIS detection, build number display

### Documentation
- `README.md` - Updated with troubleshooting, accurate commands
- `LICENSE` - Added MIT license with disclaimer
- `RELEASE-NOTES.md` - Comprehensive release notes
- `docs/roadmap/BUG-LOG.md` - All bugs documented
- `docs/roadmap/FEATURE-ENHANCEMENTS.md` - New feature log

### Rendering
- `renderers/html.py` - Font fixes, memory display improvements
- `renderers/terminal.py` - Memory display consistency

---

## Important Context for Next Session

### Testing Status
- **Max:** Testing Build 2025-11-28-013
  - QGIS conflict resolved ✅
  - Waiting for diagnostic output on fork_exec() error
  - Docker size bug should be fixed
- **Graham:** Reported Docker container size issue (same as Max)
- **Livvy:** Previously tested, no current issues
- **Rosemary:** Previously tested Safari font fix ✅

### Diagnostic Logging
- **Enabled by default:** `DIAGNOSTIC_LOGGING = True` in `yourdad.py`
- **Output:** All diagnostic messages go to stderr
- **To capture:** `python3 yourdad.py scan all 2>&1 | tee scan-output.txt`
- **What it logs:**
  - Which subprocess call is about to execute
  - Command and arguments being passed
  - Type and value of each argument
  - Full traceback on errors

### Code Quality
- All subprocess calls now have defensive checks
- Error handling improved throughout
- Build numbers tracked in code and menu

### Documentation Structure
```
dadware/
├── README.md (main docs)
├── RELEASE-NOTES.md
├── GRANT-PERMISSIONS.md
├── LICENSE
├── docs/
│   ├── roadmap/ (excluded from git)
│   │   ├── BUG-LOG.md
│   │   ├── BUG-FIX-PLAN.md
│   │   ├── FEATURE-ENHANCEMENTS.md
│   │   └── [other planning docs]
│   ├── archive/ (historical docs)
│   ├── UX-HISTORY.md
│   └── REPORT-LOCATION.md
└── [code files]
```

---

## Next Steps / TODO

### Immediate
1. **Wait for Max's diagnostic output** - Need to identify exact failing subprocess call
2. **Fix Bug #2** - Once diagnostic output received
3. **Test Docker fix** - Verify with Max/Graham that sizes are now correct
4. **Test memory pressure fix** - Verify pressure matches displayed free memory

### Planned Features
1. **Single Volume Confirmation** - When only 1 volume, show confirmation instead of menu
2. **Performance optimization** (Bug #3) - Address slow scans with 1M+ files

### Known Issues
- Bug #2: fork_exec() error (waiting for diagnostic data)
- Bug #3: Performance degradation (not yet addressed)

---

## Technical Notes

### Memory Pressure Calculation
- **Old:** Used only `vm_stat` "Pages free" (~0.1 GB)
- **New:** Uses available memory = free + inactive pages (~7.5 GB)
- **Thresholds:**
  - High: available < 1 GB OR swapouts > 1000
  - Medium: available < 2 GB OR swapouts > 100
  - Low: otherwise

### File Size Calculation
- **Old:** `os.path.getsize()` - returns logical size (wrong for sparse files)
- **New:** `os.stat().st_blocks * 512` - returns actual disk usage
- **Applied to:** All file size calculations in `scanners/storage.py`

### Subprocess Error Handling
- All `subprocess.run()` calls now have:
  - Defensive parameter validation
  - Diagnostic logging (when enabled)
  - Proper exception handling
  - Type checking before calls

---

## Git Status

**Last Commit:** `2984874` - "Fix memory pressure calculation and Docker container size bugs"
- All code changes committed
- Documentation organized
- `docs/` directory excluded from git (as configured)

---

## Quick Reference

**Current Build:** `2025-11-28-013`
**Main Entry Point:** `yourdad.py`
**Menu Script:** `./yourdad`
**Distribution Script:** `./build_distribution.sh`
**Bug Log:** `docs/roadmap/BUG-LOG.md`
**Feature Log:** `docs/roadmap/FEATURE-ENHANCEMENTS.md`

---

**Session Date:** November 28, 2025
**Status:** All changes committed, ready for next session

