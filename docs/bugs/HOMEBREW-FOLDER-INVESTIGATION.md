# Homebrew Folder Investigation

**Date:** December 2025  
**Issue:** `/opt/homebrew` shows 1.3 GB but subfolders don't add up

---

## Location of `/opt/homebrew`

**`/opt/homebrew`** is the Homebrew installation directory on **Apple Silicon Macs** (M1, M2, M3, etc.).

- **Intel Macs:** Homebrew installs to `/usr/local`
- **Apple Silicon Macs:** Homebrew installs to `/opt/homebrew`

This is the standard location for Homebrew on ARM-based Macs.

---

## Actual Folder Contents

**Total size:** 1.5 GB (Finder) / 1.3 GB (scan - excludes hidden files)

**Largest subfolders (from `du`):**
- `Cellar`: 859 MB (largest - contains installed packages)
- `lib`: 428 MB (libraries)
- `.git`: 119 MB (hidden - excluded from scan)
- `Library`: 93 MB
- `var`: 8 MB
- `docs`: 1.4 MB
- `etc`: 504 KB
- `completions`: 396 KB
- `manpages`: 136 KB

---

## The Problem

**Report shows:**
- Library: 1.3 MB (should be 72.4 MB)
- docs: 684 KB (should be 1.2 MB)
- etc: 300 KB (should be 407 KB)
- completions: 383 KB ✅ (correct)
- manpages: 130 KB ✅ (correct)
- **Missing:** Cellar (788 MB) and lib (396 MB) - the two largest folders!

**Total shown:** ~2 MB (way off from 1.3 GB)

---

## Root Cause

The report was generated with the **old code** (before the depth fix). The `scan_folder_contents()` function was using `max_depth=1`, which meant:

1. **Subfolders only showed immediate children** - not full recursive size
2. **Large nested folders were undercounted** - Library showed 1.3 MB instead of 72.4 MB
3. **Some folders might have been missed** - if they had complex nested structures

### Why Cellar and lib are Missing

This is the most puzzling part. The function should find them. Possible reasons:

1. **Old scan data** - Report was generated before fix
2. **Sorting issue** - They're there but not displayed (unlikely, they're the largest)
3. **Exclusion bug** - They were incorrectly excluded (but our test shows they're not excluded)

---

## Verification

**After the fix, the function correctly returns:**
```
Cellar: 788.2 MB ✅
lib: 396.6 MB ✅
Library: 72.4 MB ✅
var: 6.2 MB ✅
docs: 1.2 MB ✅
etc: 407 KB ✅
completions: 383.6 KB ✅
manpages: 130.6 KB ✅
package: 76.3 KB ✅
bin: 9.4 KB ✅

Total: 1.2 GB (matches scan total, excluding hidden files)
```

---

## Solution

**The fix is already in place!** The issue is that the report was generated with old code.

**Action needed:**
1. Run a **new scan** to regenerate the report
2. The new report will show:
   - Cellar: 788 MB ✅
   - lib: 396 MB ✅
   - Library: 72 MB ✅
   - All subfolders with correct sizes ✅
   - Subfolders will add up to ~1.2 GB (excluding hidden files) ✅

---

## Why the Difference from Finder?

**Finder:** 1.5 GB (includes hidden files like `.git` at 119 MB)  
**Scan:** 1.3 GB (excludes hidden files)

**Difference:** ~200 MB (mostly `.git` folder and other hidden files)

This is expected - the scan excludes hidden files by design.

---

## Summary

- ✅ **Location:** `/opt/homebrew` is correct (Homebrew on Apple Silicon)
- ✅ **Total size:** 1.3 GB is correct (excludes hidden files)
- ✅ **Fix applied:** Subfolder depth issue fixed
- ⚠️ **Action needed:** Run new scan to see corrected subfolders
- ✅ **After new scan:** Will show Cellar, lib, and all subfolders with correct sizes

---

**Status:** ✅ Fixed (need to regenerate report)  
**Files Modified:**
- `scanners/storage.py` - Fixed `max_depth=1` → `max_depth=10` in `scan_folder_contents()`

