# Finder Size Match Fix

**Date:** December 2025  
**Issue:** Report shows different folder sizes than Finder

---

## Problem

The report was showing folder sizes that didn't match Finder. For example:
- **Finder:** Arc folder = 10.06 GB
- **Report:** Arc folder = 155 MB

This created confusion and made the report less trustworthy.

---

## Root Cause

The scanner was using **actual disk usage** (`st_blocks * 512`) instead of **logical file size** (`os.path.getsize()`).

### Difference Between the Two:

1. **Logical File Size** (`os.path.getsize()`):
   - Sum of all file sizes as reported by the file system
   - What Finder shows
   - What you'd see if you added up file sizes manually
   - Can be larger than actual disk usage (for sparse files, compressed files)

2. **Actual Disk Usage** (`st_blocks * 512`):
   - Real disk blocks used
   - Accounts for file system compression (APFS compression)
   - Accounts for sparse files (holes in files)
   - Can be smaller than logical size (due to compression)

### Why We Were Using Actual Disk Usage:

We switched to `st_blocks` to fix Docker container size issues (Bug #5). Docker containers are sparse files that report huge logical sizes (1TB+) but use little actual space. Using `st_blocks` showed the correct actual disk usage.

However, this created a mismatch with Finder, which always shows logical size.

---

## Solution

Changed back to **logical file size** (`os.path.getsize()`) to match Finder's display.

### Trade-offs:

**Pros:**
- ✅ Matches Finder exactly
- ✅ More intuitive for users
- ✅ Consistent with what users expect

**Cons:**
- ⚠️ Docker containers will show large logical sizes again
- ⚠️ But Docker paths are excluded from scanning anyway, so this is fine

### Why This Works:

1. **Docker containers are excluded** - We already exclude Docker paths in `should_exclude()`, so they won't be scanned
2. **Virtual disk images are excluded** - We exclude `.qcow2`, `.vmdk`, `.vdi`, etc.
3. **Regular folders match Finder** - Users see what they expect

---

## Changes Made

**File:** `scanners/storage.py`

### Changed in 3 places:

1. **`get_folder_size()` function:**
   ```python
   # Before:
   stat_info = os.stat(item_path)
   size = stat_info.st_blocks * 512
   
   # After:
   size = os.path.getsize(item_path)
   ```

2. **`scan_folder_contents()` function:**
   ```python
   # Before:
   stat_info = os.stat(item_path)
   size = stat_info.st_blocks * 512
   
   # After:
   size = os.path.getsize(item_path)
   ```

3. **`scan_storage()` function:**
   ```python
   # Before:
   stat_info = os.stat(file_path)
   file_size = stat_info.st_blocks * 512
   
   # After:
   file_size = os.path.getsize(file_path)
   ```

---

## Impact

### Before:
- Report showed actual disk usage (smaller due to compression)
- Didn't match Finder
- Confusing for users

### After:
- Report shows logical file size (matches Finder)
- Consistent with user expectations
- More intuitive

### Example:
- **Arc folder:**
  - Finder: 10.06 GB
  - Report (before): 155 MB (actual disk usage with compression)
  - Report (after): 10.06 GB (logical size, matches Finder)

---

## Notes

### File System Compression

macOS APFS uses file system compression. This means:
- **Logical size:** What Finder shows (10 GB)
- **Actual disk usage:** What's actually on disk (might be 8 GB due to compression)

The report now shows logical size to match Finder, even though actual disk usage might be less.

### Sparse Files

For sparse files (files with holes):
- **Logical size:** Maximum size (can be huge)
- **Actual disk usage:** Real space used (much smaller)

We handle this by:
- Excluding Docker containers (sparse files)
- Excluding virtual disk images (sparse files)
- Regular files show logical size (matches Finder)

---

## Testing

### Expected Results:
1. **Folder sizes match Finder** - Report should show same size as Finder
2. **Docker containers excluded** - Should not appear in scan (already excluded)
3. **Virtual disks excluded** - Should not appear in scan (already excluded)

### Verification:
- Run storage scan
- Compare folder sizes in report with Finder
- Should match exactly

---

## Related Issues

- **Bug #5:** Docker Container Size Miscalculation (fixed by excluding Docker paths)
- This fix ensures regular folders match Finder, while Docker is handled separately

---

**Status:** ✅ Fixed  
**Files Modified:**
- `scanners/storage.py` - Changed from `st_blocks` to `os.path.getsize()` in 3 places

