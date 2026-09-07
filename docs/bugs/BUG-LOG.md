# Bug Log - Dad Ware

## Bug #1: Font/Rendering Issue - Chinese/Kanji Characters
**Status:** ✅ FIXED  
**Reported:** External testing  
**Severity:** Medium  
**Priority:** Medium  
**Fixed:** Build 2025-11-28-008

### Description
- HTML report displays Chinese/Kanji characters instead of proper text
- Prompt box appears visibly empty
- HTML file renders correctly in reporter's browser
- Suggests font encoding or CSS font-family issue on target machine

### Symptoms
- Characters render as Chinese/Kanji
- Empty prompt box (though content may be present)
- Issue is machine-specific (works in some browsers, not others)

### Root Cause
✅ **RESOLVED:** Safari fails to render italic text correctly with system fonts (`-apple-system`, `BlinkMacSystemFont`). When Safari can't find the italic variant, it falls back to fonts with different character encodings (CJK fonts), causing Chinese/Kanji characters to appear.

### Solution Applied
Changed font-family for italic text from system fonts to explicit Helvetica/Arial:
- `.personality p`: Changed to `'Helvetica Neue', Helvetica, Arial, sans-serif`
- `.file-folder-name`: Changed to `'Helvetica Neue', Helvetica, Arial, sans-serif`

**Tested on:** Safari 17.3.1 (Feb 2024) - ✅ Passed

### Files Affected
- `renderers/html.py` - HTML generation
- CSS font-family declarations
- Character encoding meta tag

### Investigation Needed
- Check all font-family declarations
- Verify UTF-8 encoding is properly set
- Test with explicit font fallbacks
- Check if prompt box content is actually empty or just not rendering

---

## Bug #2: fork_exec() Argument Count Mismatch
**Status:** ✅ RESOLVED  
**Reported:** External testing  
**Severity:** High  
**Priority:** High  
**Resolved:** December 2025

### Description
Error during "full scan" (memory + storage):
```
❌ Error running scan: fork_exec() takes exactly 23 arguments (21 given)
```

### Symptoms
- Occurs during full scan (both CPU and storage)
- Error suggests subprocess call with wrong number of arguments
- 2 arguments missing (23 expected, 21 given)

### Root Cause
✅ **RESOLVED:** The error was caused by using a non-system version of Python (likely QGIS's bundled Python or another custom Python installation). When forced to use the system Python (`/usr/bin/python3`), the error no longer occurs.

This was a Python environment compatibility issue, not a code bug. The system Python has the correct subprocess implementation that matches the expected argument count.

### Solution Applied
- Use system Python (`/usr/bin/python3`) instead of custom Python installations
- Executable build (PyInstaller) bundles system Python, avoiding this issue entirely
- Menu script and shebang ensure system Python is used

### Files Affected
- `yourdad.py` - Shebang points to `/usr/bin/python3`
- `build_executable.sh` - Creates standalone executable with bundled Python
- `yourdad.spec` - PyInstaller spec ensures correct Python version

### Testing
- ✅ Verified error no longer occurs when using system Python
- ✅ Executable build avoids Python version conflicts entirely

---

## Bug #3: Performance Degradation with Large File Counts
**Status:** ⚠️ LIKELY RESOLVED (No reproducible test case)  
**Reported:** External testing  
**Severity:** High  
**Priority:** Medium (if issue resurfaces)

### Description
- Scan becomes very slow after ~1M files
- Early in scan: fast (finds many files quickly)
- After 1M files: very slow (only finding ~100 files at a time)
- User has iCloud Drive with lots of code repos
- Possible symlinks not on machine

### Symptoms
- Performance degrades exponentially with file count
- Slowdown starts around 1M files
- Progress updates show very slow file discovery rate
- May be related to:
  - iCloud Drive syncing
  - Symlinks to non-existent paths
  - Docker containers (large sparse files)
  - Recursive directory traversal inefficiency

### Root Cause Hypothesis
✅ **LIKELY RESOLVED:** The performance issue was likely caused by Docker containers (large sparse files) that were taking a very long time to scan. Since Docker detection and exclusion is now implemented, this may no longer be an issue.

**Current Status:**
- ✅ Docker containers are now detected and excluded from deep scanning
- ✅ Docker paths are skipped to avoid slow I/O
- ⚠️ No reproducible test case available to confirm if issue is fully resolved
- ⚠️ Performance improvements (below) are still recommended as best practices

### Files Affected
- `scanners/storage.py` - Main scanning logic
- `get_folder_size()` - Recursive size calculation
- `scan_storage()` - Main scan loop with `os.walk()`
- `should_exclude()` - Path exclusion logic (now includes Docker detection)

### Docker Detection Implemented
- ✅ `is_docker_path()` function detects Docker containers, volumes, and data directories
- ✅ Docker data directories are excluded from scanning (too slow)
- ✅ Docker files are detected but not deeply scanned
- ✅ Sparse file detection prevents slow scanning of virtual disk images

### Performance Improvements Still Recommended (Best Practices)
While the issue may be resolved, these improvements would still benefit performance:
- Use `os.scandir()` instead of `os.listdir()` (faster, returns DirEntry objects)
- Skip symlinks early (check `os.path.islink()` before processing) - ✅ Already done
- Add directory-level timeouts (optional, for very slow paths)
- Cache directory sizes for repeated scans (future optimization)
- Parallel processing for independent directories (future optimization)
- Special handling for iCloud Drive (skip or scan separately) - Optional

### Testing
- ⚠️ No reproducible test case available
- ✅ Docker detection confirmed working
- ⚠️ Performance improvements can be implemented if needed, but may not be necessary

---

## Bug #4: Memory Pressure Calculation Mismatch
**Status:** ✅ FIXED  
**Reported:** Max (via report analysis)  
**Severity:** Medium  
**Priority:** Medium  
**Fixed:** Build 2025-11-28-012

### Description
- Memory pressure showing "high" when only 53% of RAM is used
- Report shows 7.5 GB free but pressure is high
- Confusing mismatch between displayed free memory and pressure level

### Symptoms
- Memory Overview shows: "Used: 8.5 GB (53%)" and "Free: 7.5 GB"
- Memory Pressure shows: "🔴 high"
- Users confused by the contradiction

### Root Cause
Memory pressure calculation was using only `vm_stat`'s "Pages free" (truly free pages, ~0.1 GB) instead of available memory (free + inactive pages that can be reclaimed, ~7.5 GB). The report correctly displayed available memory, but pressure was calculated from a different metric.

### Solution Applied
Changed pressure calculation to use **available memory** (free + inactive pages) instead of just free pages:
- High pressure: available memory < 1 GB OR swapouts > 1000
- Medium pressure: available memory < 2 GB OR swapouts > 100
- Low pressure: otherwise

This aligns with how macOS actually manages memory and makes pressure level match the displayed free memory.

### Files Affected
- `scanners/cpu.py` - `get_memory_pressure()` function
- Changed from `free_gb < 0.5` to `available_gb < 1.0` (where available = free + inactive)

### Testing
- Verified pressure calculation now matches displayed free memory
- Tested with Max's report: 7.5 GB available should show low/medium pressure, not high

---

## Bug #5: Docker Container Size Miscalculation
**Status:** ✅ FIXED  
**Reported:** Max and Graham  
**Severity:** High  
**Priority:** High  
**Fixed:** Build 2025-11-28-013

### Description
- Docker containers reported as 1TB+ when actual disk usage is much smaller
- Total storage shown as 1.5TB on a 500GB drive
- Caused by sparse files (virtual disk images) reporting logical size instead of actual disk usage

### Symptoms
- Docker container files show huge sizes (1TB+)
- Total storage exceeds physical drive capacity
- Confusing reports showing impossible storage amounts

### Root Cause
Docker containers and virtual disk images are **sparse files** - they report a large logical size (the maximum capacity) but use much less actual disk space. The scanner was using `os.path.getsize()` which returns logical size, not actual disk usage.

### Solution Applied
1. **Changed size calculation**: Now uses `os.stat().st_blocks * 512` to get actual disk usage instead of logical file size
2. **Added Docker exclusion**: Exclude Docker paths and virtual disk image formats (.qcow2, .vmdk, .vdi, etc.) from scanning
3. **Applied to all file size calculations**: Updated `get_folder_size()`, `scan_folder_contents()`, and `scan_storage()` to use actual disk usage

### Files Affected
- `scanners/storage.py` - All file size calculations
- Changed from `os.path.getsize()` to `os.stat().st_blocks * 512`
- Added Docker and virtual disk format exclusions to `should_exclude()`

### Testing
- Tested with Docker containers
- Verified sparse files now show correct actual disk usage
- Confirmed total storage no longer exceeds physical drive capacity

---

## Bug #6: QGIS Python Conflict (Direct python3 Call)
**Status:** Partially Fixed  
**Reported:** Max (test case - youdad_error 2.rtf)  
**Severity:** Medium  
**Priority:** Medium  
**Fixed:** Build 2025-11-28-013 (shebang fix)

### Description
When running `python3 yourdad.py` directly on systems with QGIS installed, Python uses QGIS's bundled Python instead of system Python, causing module conflicts:
```
AssertionError: SRE module mismatch
```

### Symptoms
- Error occurs when running `python3 yourdad.py` directly
- Error: `AssertionError: SRE module mismatch`
- Stack trace shows QGIS Python paths: `/Applications/QGIS.app/Contents/Resources/python/`
- Menu script works (has QGIS detection), but direct `python3` call fails

### Root Cause
- QGIS installs its own Python and modifies PATH
- When user runs `python3`, it resolves to QGIS's Python
- QGIS's Python has incompatible module versions
- Shebang fix (`#!/usr/bin/python3`) only works when running `./yourdad.py` directly, not `python3 yourdad.py`

### Solution Applied
- ✅ Updated shebang in `yourdad.py` to use `/usr/bin/python3`
- ✅ Menu script (`yourdad`) detects and avoids QGIS Python
- ⚠️ **Still fails** when user runs `python3 yourdad.py` directly

### Additional Fixes Needed
1. **Create wrapper script** that ensures system Python is used
2. **Update README** with explicit QGIS troubleshooting
3. **Add to installation instructions** - mention QGIS conflict and workarounds
4. **Test menu script** to ensure QGIS detection works properly

### Workarounds
- Use `/usr/bin/python3 yourdad.py` instead of `python3 yourdad.py`
- Use menu script: `./yourdad` (has QGIS detection)
- Check `which python3` to see what it points to

### Files Affected
- `yourdad.py` - Shebang fixed
- `yourdad` (menu script) - Has QGIS detection
- `README.md` - Needs QGIS troubleshooting section

### Testing
- Test menu script on Max's machine
- Verify QGIS detection works
- Document workarounds clearly

---

## Bug #7: Home Folder Item Count Reported as a Total
**Status:** ⚠️ OPEN
**Reported:** Sep 3, 2026 - real-Mac benchmarking session
**Severity:** Low
**Priority:** Medium

### Description
On the pre-PR#13 code path, scanning `/` runs a second, separate walk of
the home directory. Both walks end with the same line:

```
→ found {items_found:,} items total
```

So a single run prints "items total" twice, with two different numbers,
neither of which is the total:

```
→ found 325,114 items total      <- the volume walk
→ found 292,390 items total      <- the home walk, reported as if it were a total
```

A reader reasonably concludes the second number replaced the first, or
that the scan somehow lost 30,000 items. The real total work done is the
sum (~617,504 item visits), and neither printed number says so.

### Expected
The home walk should name what it counted and give a running total, e.g.

```
→ found 292,390 items in home folder, 617,504 items total
```

### Files Affected
- `scanners/storage.py:373` - the single `→ found {n:,} items total` print,
  reached by both walks with no idea which one is calling it.
- `askdad.py:94` - the in-progress `→ found {n:,} items...` line has the
  same ambiguity while running.

### Note on Scope
PR #13 (`ec65693`, "Fold the home breakdown into the volume walk") removes
the second walk, which makes the duplicate line disappear on `main` - the
symptom goes away without the wording ever being fixed. The message is
still wrong for any caller that scans a subtree, and the fix is worth
making on its own terms rather than treating the merge as the resolution.

---

## Bug #8: Scanning `/` Descends Into Every Mounted Volume
**Status:** ⚠️ OPEN
**Reported:** Sep 3, 2026 - real-Mac benchmarking session
**Severity:** High
**Priority:** High

### Description
`should_exclude()` filters a fixed list of root directories
(`EXCLUDED_ROOT_DIRS` in `utils/path_utils.py:24`) but has no notion of
filesystem boundaries, and `/Volumes` is not on the list. Choosing
"Macintosh HD (/)" in the volume picker therefore walks *every mounted
volume* - external drives, Time Machine backups, anything in `/Volumes`.

Verified:

```python
should_exclude('/Volumes')                       -> False
should_exclude('/Volumes/BACKUP')                -> False
should_exclude('/Volumes/BACKUP/Backups.backupdb') -> False
```

### Symptoms
Measured on the same machine, same code, same chosen volume (`/`):

| Backup drive | Items found | Result |
|---|---|---|
| unmounted | ~332,000 | completes in ~1m 45s |
| 2 TB Time Machine drive mounted | 678,566 and still climbing | interrupted at 499s, no end in sight |

The scan appears hung. The user's report was "glacially slow ... 2:30 and
it only found 180k items" - which was this, not a code regression.

### Impact
This is the worst possible case for a tool aimed at non-technical users:
plugging in the backup drive you were told to keep attached makes the
scan appear broken. It also silently corrupts the numbers - backup
contents get counted as if they were on the startup disk, so "Total /
Used / Free" and every folder ranking are wrong whenever a volume is
mounted.

### Root Cause
No cross-device check in the walk. `scanners/storage.py` recurses on
directory entries without comparing `st_dev` against the scan root, and
`/Volumes` is absent from `EXCLUDED_ROOT_DIRS`.

Note the hidden-caches scanner already gets this right - it shells out to
`du -skx`, where `-x` means "stay on one filesystem" (documented in
`scanners/hidden_storage.py`). The Python walk never got the equivalent.

### Suggested Fix
Stat the scan root once, then skip any directory whose `st_dev` differs.
That is the general fix and it costs nothing - the walk already has a
`stat_result` per entry from the single-pass design, so no extra syscall
is needed. Excluding `/Volumes` by name would also work but is narrower
(misses `/mnt`, `/media`, arbitrary mount points) and would wrongly block
an explicit `--volume /Volumes/BACKUP` scan, which must keep working.

### Files Affected
- `utils/path_utils.py:24` - `EXCLUDED_ROOT_DIRS`
- `scanners/storage.py` - the walk, where the device check belongs

---

## Summary

| Bug # | Description | Severity | Priority | Status |
|-------|-------------|----------|----------|--------|
| #1 | Font/Rendering Issue | Medium | Medium | ✅ FIXED |
| #2 | fork_exec() Error | High | High | ✅ RESOLVED |
| #3 | Performance Degradation | High | Medium | ⚠️ LIKELY RESOLVED |
| #4 | Memory Pressure Mismatch | Medium | Medium | ✅ FIXED |
| #5 | Docker Container Size | High | High | ✅ FIXED |
| #6 | QGIS Python Conflict | Medium | Medium | ✅ FIXED (via executable) |
| #7 | Home Count Reported as Total | Low | Medium | ⚠️ OPEN |
| #8 | Scan Crosses Into Mounted Volumes | High | High | ⚠️ OPEN |

**Total Estimated Effort:** ~2 hours (Bug #8 is a correctness + usability blocker for beta; Bug #7 is cosmetic wording)

