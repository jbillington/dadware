# Home Folders Display Fix

**Date:** December 2025  
**Issues Fixed:**
1. Home folders showing too many folders (should only show top 10)
2. Library/Messages showing incorrect size and appearing in home folders

---

## Problem 1: Too Many Home Folders Displayed

### Issue
- Home folders bar was showing ALL home folders, not just top 10
- Made it impossible to read folder names
- Non-home folders correctly limited to top 10, but home folders weren't

### Fix
- Limited home folders to top 10 (same as non-home folders)
- Sort home folders by size before limiting
- Added note if more than 10 home folders exist: "Only top 10 home folders displayed"

### Changes Made
**File:** `renderers/html.py`
- Sort home_folder_segments by size before limiting
- Create `top_10_home` list (limited to 10)
- Use `top_10_home` instead of `home_folder_segments` for display
- Update expanded details to only show top 10
- Add note if more than 10 exist

---

## Problem 2: Library/Messages Size and Display

### Issue
- Library/Messages showing 26.1 GB in home folders
- User reports only seeing a few files that don't add up to that size
- Library/Messages should be scanned separately as a Mac library, not as a home folder

### Root Causes
1. **Library/Messages was being scanned by storage scanner** - Should be excluded (scanned separately)
2. **Library/Messages was appearing as a home folder** - Because it contains "Library" in the path
3. **Size calculation using logical size** - Should use actual disk usage (st_blocks)

### Fixes Applied

#### 1. Exclude Library/Messages from Storage Scanner
**File:** `scanners/storage.py`
- Added exclusion for `/Library/Messages/` paths
- Prevents it from being scanned during main storage scan
- Already excluded Library/Mail, now also excludes Messages

#### 2. Exclude from Home Folders Display
**File:** `renderers/html.py`
- Skip Library/Messages and Library/Mail when categorizing folders
- These are scanned separately as Mac libraries
- Should not appear in home folders section

#### 3. Use Actual Disk Usage for Messages Scanner
**File:** `scanners/mac_libraries.py`
- Changed from `os.path.getsize()` to `os.stat().st_blocks * 512`
- Matches the storage scanner's method
- Handles sparse files correctly
- Shows actual disk usage, not logical file size

---

## Technical Details

### Size Calculation Change
**Before:**
```python
size = os.path.getsize(file_path)  # Logical file size
```

**After:**
```python
stat_info = os.stat(file_path)
size = stat_info.st_blocks * 512  # Actual disk usage
```

### Why This Matters
- **Logical size:** Maximum size a file can be (for sparse files, this can be huge)
- **Actual disk usage:** Real space used on disk (what we want to show)
- **Messages attachments:** May be stored as sparse files or have complex structures
- **Hidden files:** Messages uses many hidden files that user might not see

---

## Testing

### Expected Results
1. **Home Folders:** Should show only top 10 folders
2. **Library/Messages:** Should NOT appear in home folders
3. **Messages Size:** Should show actual disk usage (may still be large if there are many attachments/hidden files)
4. **Note:** If more than 10 home folders exist, should show note

### Verification
- Run storage scan
- Check HTML report
- Verify home folders bar shows max 10 folders
- Verify Library/Messages not in home folders
- Check Messages size in Mac Libraries section (should be accurate)

---

## Notes

### Messages Folder Size
Even with the fix, Messages folder might still show a large size if:
- There are many message attachments (photos, videos, files)
- Database files are large
- Hidden files in subdirectories
- Actual disk usage is legitimately large

The fix ensures we're showing **actual disk usage**, not logical file size, which is more accurate.

### Home Folders Limit
- Top 10 is a reasonable limit for readability
- Users can still see all folders in the detailed view (when clicking on a folder)
- Note indicates if more folders exist

---

**Status:** ✅ Fixed  
**Files Modified:**
- `renderers/html.py` - Limited home folders to top 10, excluded Messages/Mail
- `scanners/storage.py` - Excluded Library/Messages from scanning
- `scanners/mac_libraries.py` - Use actual disk usage for size calculation

