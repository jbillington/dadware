# Pre-Test Review: yourdad.py

**Date:** November 9, 2025  
**Status:** Ready for basic testing, but needs error handling improvements

---

## Critical Issues (Fix Before Testing)

### 1. **Missing Error Handling for File Operations**
- **Lines 197-198, 249-250, 357-358**: JSON file writes have no try/except
- **Line 184**: HTML render has no error handling
- **Risk**: Crashes if disk full or permission denied

### 2. **Browser Opening Failure**
- **Lines 202, 254, 362**: `webbrowser.open()` can fail silently
- **Risk**: User won't know if browser didn't open

### 3. **Input Validation Missing**
- **Line 91**: `--top` can be negative or zero (no validation)
- **Line 92**: `--min-size` parsing errors not caught
- **Risk**: Invalid input causes confusing errors

---

## Important Issues (Fix Soon)

### 4. **Storage Overview Missing in CLI**
- **Lines 127-129**: Volume selected but no storage info shown before scan
- **UX Review**: Identified as missing feature
- **Impact**: User doesn't see storage status until after scan

### 5. **Quick Scan Only Shows Storage**
- **Line 338**: Comment says "For now, just render storage"
- **Issue**: Quick scan should show combined storage + CPU report
- **Impact**: Feature incomplete

### 6. **Generic Error Messages**
- **Line 141**: Just returns 1, no error message
- **Line 211**: Generic "Could not scan CPU/RAM"
- **Impact**: Hard to debug issues

### 7. **No Progress Feedback During Scans**
- **Lines 133-138**: Long storage scans have no progress updates
- **Impact**: User doesn't know if scan is working or frozen

---

## Nice to Have (Can Test Without)

### 8. **Exception Handling for Critical Operations**
- Missing try/except around:
  - Volume selection (line 127)
  - Permission checks (line 144)
  - Mac library scanning (line 156)
  - Personality generation (line 163)

### 9. **Better Volume Validation**
- `select_volume()` may return invalid path
- Should validate path exists and is readable

### 10. **Report Directory Creation Errors**
- **Line 175**: `os.makedirs()` may fail (permissions, disk full)
- Should catch and report error

---

## Quick Fixes Needed

### Priority 1 (Before Testing)
```python
# Add input validation
if args.top <= 0:
    print("Error: --top must be positive")
    return 1

# Add error handling for file writes
try:
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
except (IOError, OSError) as e:
    print(f"Error: Could not save report: {e}")
    return 1

# Add error handling for HTML render
try:
    render_html(scan_data, personality_data, report_path)
except Exception as e:
    print(f"Error: Could not generate HTML report: {e}")
    return 1
```

### Priority 2 (Soon)
```python
# Add storage overview before scan
volume_info = get_volume_info(volume_path)
if volume_info:
    print(f"\nStorage Overview:")
    print(f"  Total: {volume_info['total_human']}")
    print(f"  Used: {volume_info['used_human']} ({volume_info['used_percent']:.0f}%)")
    print(f"  Free: {volume_info['free_human']} ({volume_info['free_percent']:.0f}%)\n")
```

---

## Testing Readiness

**Can Test Now:**
- ✅ Basic functionality works
- ✅ Happy path is complete
- ✅ Core features implemented

**Should Fix First:**
- ⚠️ File I/O error handling (critical)
- ⚠️ Input validation (important)
- ⚠️ Better error messages (important)

**Can Test Without:**
- 🔜 Storage overview in CLI
- 🔜 Quick scan combined report
- 🔜 Progress feedback
- 🔜 Enhanced exception handling

---

## Recommended Action Plan

1. **Add error handling** (30 min)
   - Wrap file operations in try/except
   - Add input validation
   - Improve error messages

2. **Add storage overview** (15 min)
   - Show volume info before scan starts
   - Use existing `get_volume_info()` function

3. **Test basic functionality** (1 hour)
   - Test all scan types
   - Test with/without permissions
   - Test error cases

4. **Fix quick scan** (30 min)
   - Create combined HTML report
   - Or document as known limitation

---

**Estimated Time to Test-Ready:** 1-2 hours



