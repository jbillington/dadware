# Docker Container Intelligent Handling

**Date:** December 2025  
**Issue:** Docker containers showing huge sizes and taking too long to scan

---

## Problem

Docker containers are **sparse files** that report huge logical sizes (often 1TB+) but use little actual disk space. This caused:
1. **Incorrect sizes** - Containers showing as 1TB+ when they only use a few GB
2. **Slow scans** - Scanning inside Docker containers takes forever
3. **Confusing reports** - Developers seeing impossible storage amounts

---

## Solution: Intelligent Docker Detection

Instead of completely excluding Docker, we now:
1. **Detect Docker containers** - Identify Docker-related paths and files
2. **Use actual disk usage** - Show real space used, not logical size
3. **Skip deep scanning** - Don't scan inside Docker data directories (too slow)
4. **Mark in reports** - Indicate when something is a Docker container

---

## Implementation

### 1. Docker Detection Functions

**`is_docker_path(path)`** - Detects Docker-related paths:
- Common Docker paths: `/docker/`, `/.docker/`, `docker/containers`, etc.
- Docker disk images: `docker.qcow2`, `Docker.raw`
- Docker data directories

**`is_sparse_file(path)`** - Detects sparse files (virtual disk images):
- File extensions: `.qcow2`, `.vmdk`, `.vdi`, `.vhd`, `.vhdx`, `.raw`
- Size ratio check: If logical size >> actual disk usage (10x+), it's sparse

### 2. Size Calculation

**For Docker containers and sparse files:**
- Use `st_blocks * 512` (actual disk usage)
- Shows real space used, not logical size

**For regular files:**
- Use `os.path.getsize()` (logical size)
- Matches Finder's display

### 3. Exclusion Strategy

**Skip scanning inside Docker data directories:**
- `/containers/` - Too many files, too slow
- `/volumes/` - Too many files, too slow
- `/data/` - Too many files, too slow

**But allow Docker files themselves:**
- Docker disk images (`.qcow2`, `.raw`) are detected and shown
- Use actual disk usage for accurate sizes

---

## Benefits

### For Developers with Docker:
- ✅ Docker containers show **actual disk usage** (accurate)
- ✅ No more 1TB+ false reports
- ✅ Fast scans (skips slow Docker data directories)
- ✅ Docker containers are **marked** in reports

### For Regular Users:
- ✅ No impact (Docker is rare)
- ✅ Regular files still match Finder
- ✅ No performance penalty

---

## Example

### Before:
```
Docker.qcow2: 1.2 TB  (logical size - wrong!)
Scan time: 30+ minutes (scanning inside containers)
```

### After:
```
Docker.qcow2: 15.3 GB  (actual disk usage - correct!)
[🐳 Docker Container]
Scan time: < 1 minute (skips Docker data directories)
```

---

## Technical Details

### Detection Patterns

**Docker paths:**
- `/docker/`
- `/.docker/`
- `docker/containers`
- `docker/volumes`
- `docker/data`
- `com.docker.`
- `docker.qcow2`
- `Docker.raw`

**Sparse file detection:**
- File extension check (`.qcow2`, `.vmdk`, etc.)
- Size ratio check: `logical_size / actual_size > 10`

### Size Calculation Logic

```python
if is_docker_path(file_path) or is_sparse_file(file_path):
    # Use actual disk usage
    stat_info = os.stat(file_path)
    size = stat_info.st_blocks * 512
else:
    # Use logical size (matches Finder)
    size = os.path.getsize(file_path)
```

---

## Report Display

Docker containers are marked in scan results:
- Files: `is_docker: True` flag
- Folders: `is_docker: True` flag

**Future enhancement:** Could add visual indicator in HTML report (🐳 icon, note about actual vs logical size)

---

## Testing

### Test Cases:
1. **Docker container file** - Should show actual disk usage
2. **Docker data directory** - Should be skipped (too slow)
3. **Regular file** - Should show logical size (matches Finder)
4. **Sparse file** - Should show actual disk usage

### Expected Results:
- Docker containers: Accurate sizes (actual disk usage)
- Scan speed: Fast (skips Docker data directories)
- Regular files: Match Finder (logical size)

---

## Related Issues

- **Bug #5:** Docker Container Size Miscalculation (original issue)
- **Finder Size Match:** Regular files use logical size to match Finder
- **Performance:** Docker data directories excluded to prevent slow scans

---

## Notes

### Why Not Exclude Docker Completely?

The user wanted **intelligent handling**, not complete exclusion:
- Developers need to see Docker container sizes
- But they need **accurate** sizes (actual disk usage)
- And they need **fast** scans (skip data directories)

### Trade-offs:

- ✅ Accurate sizes for Docker containers
- ✅ Fast scans (skips slow directories)
- ✅ Regular files still match Finder
- ⚠️ Docker containers marked but not visually distinct in HTML (yet)

---

**Status:** ✅ Implemented  
**Files Modified:**
- `scanners/storage.py` - Added Docker detection, intelligent size calculation, exclusion of data directories

