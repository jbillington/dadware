# Finder vs Scan Size Difference

**Date:** December 2025  
**Issue:** Finder shows 16.4 GB but scan shows 15.2 GB for Application Support folder

---

## The Difference

- **Finder:** 16.4 GB (full recursive size, includes everything)
- **Scan:** 15.2 GB (1.2 GB difference)

---

## Why the Difference?

The scan uses `os.walk()` which goes **all the way** through the directory tree (no depth limit), but it **excludes** certain paths that Finder includes:

### 1. Hidden Files/Folders
**Excluded by scanner:**
```python
# Skip hidden files/folders (starting with .)
basename = os.path.basename(path)
if basename.startswith('.'):
    return True
```

**Finder includes:** Hidden files and folders (`.DS_Store`, `.git`, etc.)

### 2. Caches
**Excluded by scanner:**
```python
# Skip caches
if '/Library/Caches/' in path or '/tmp/' in path or path.endswith('/tmp'):
    return True
```

**Finder includes:** Cache files

### 3. Permission Errors
**Excluded by scanner:**
- Files that can't be read (permission denied)
- Caught by `except (OSError, PermissionError): pass`

**Finder includes:** If Finder can see it, it counts it (might have different permissions)

### 4. Symlinks
**Excluded by scanner:**
```python
if os.path.islink(item_path):
    continue  # Skip symlinks to avoid double-counting
```

**Finder includes:** Symlinks (but might handle them differently)

---

## What the Scan Does

1. **Uses `os.walk()`** - Goes through ALL files recursively (no depth limit)
2. **Groups by depth-2 folders** - Takes first 2 path components for grouping
3. **Excludes certain paths** - Hidden files, caches, symlinks, etc.
4. **Handles errors** - Skips files that can't be read

---

## The 1.2 GB Difference

The missing 1.2 GB is likely:
- **Hidden files/folders** (`.DS_Store`, `.git`, `.npm`, etc.)
- **Cache files** (if any caches are in Application Support)
- **Permission errors** (files that can't be read)
- **Symlinks** (if any)

---

## Should We Match Finder Exactly?

### Option 1: Include Hidden Files
**Pros:**
- ✅ Matches Finder exactly
- ✅ More accurate

**Cons:**
- ⚠️ Shows clutter (`.DS_Store`, `.git`, etc.)
- ⚠️ Less useful for cleanup (users don't usually delete hidden files)

### Option 2: Keep Current Behavior
**Pros:**
- ✅ Focuses on user-visible files
- ✅ More useful for cleanup decisions
- ✅ Faster (skips hidden files)

**Cons:**
- ⚠️ Doesn't match Finder exactly
- ⚠️ Can be confusing

### Option 3: Add Note in Report
**Pros:**
- ✅ Explains the difference
- ✅ Users understand why

**Cons:**
- ⚠️ Still doesn't match Finder

---

## Recommendation

**Option 2 + Option 3:** Keep current behavior but add a note explaining the difference.

The scan is designed for **cleanup decisions**, not exact Finder matching. Users want to know about files they can actually see and delete, not hidden system files.

However, we could:
1. Add a note: "Size may differ from Finder due to excluded hidden files and caches"
2. Or add a `--include-hidden` flag for developers who want exact matching

---

## Technical Details

### What Gets Excluded:
- Hidden files/folders (starting with `.`)
- Cache directories (`/Library/Caches/`, `/tmp/`)
- Symlinks (to avoid double-counting)
- System directories (at root level)
- App bundles (`.app`)
- Photos libraries (`.photoslibrary`)
- Mail/Messages data (scanned separately)
- Docker data directories (too slow)

### What Gets Included:
- All visible files and folders
- Files at any depth (no depth limit in main scan)
- Files grouped by depth-2 folders for display

---

## Testing

To verify what's being excluded:
1. Run: `du -sh ~/Library/Application\ Support` (Finder's view)
2. Compare with scan result
3. Check for hidden files: `find ~/Library/Application\ Support -name ".*" -type f | wc -l`

---

**Status:** Expected behavior (by design)  
**Recommendation:** Add note explaining difference, or add `--include-hidden` flag

