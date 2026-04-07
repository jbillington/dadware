# Error Reports Analysis - Test Cases

**Date:** December 2025  
**Source:** Test cases from Max  
**Files:** `youdad_error.rtf`, `youdad_error 2.rtf`

---

## Error Report #1: fork_exec() Error

**File:** `youdad_error.rtf`  
**Error:** `fork_exec() takes exactly 23 arguments (21 given)`

### Details
- **Command:** Running full scan (memory + storage)
- **Error Message:** `Error running scan: fork_exec() takes exactly 23 arguments (21 given)`
- **Additional Note:** "Make sure yourdad.py is in the same directory as this script."

### Analysis
This is **Bug #2** that we've been tracking. The error occurs during the "all" scan type (both CPU and storage).

**Key Observations:**
- Error happens during scan execution (not at startup)
- Specifically mentions "full scan (memory + storage)"
- The "23 arguments (21 given)" suggests a subprocess call is missing 2 arguments
- Could be:
  - Missing environment variables
  - Missing None checks causing arguments to be omitted
  - Incorrect argument unpacking

**Status:** 
- Diagnostic logging has been added
- Defensive checks have been added
- **Still waiting for diagnostic output** from Max to identify exact failing call

**Next Steps:**
1. Need Max to run the diagnostic version and capture output
2. Or proactively fix the most likely culprits (see Bug #2 investigation plan)

---

## Error Report #2: QGIS Python Conflict

**File:** `youdad_error 2.rtf`  
**Error:** `AssertionError: SRE module mismatch`

### Details
- **User:** maxsheldon@Maxs-Mac-mini
- **Command:** `python3 yourdad.py scan all 2>&1 | tee scan-output.txt`
- **Error:** 
  ```
  File "/Applications/QGIS.app/Contents/Resources/python/argparse.py", line 89, in <module>
    import re as _re
  File "/Applications/QGIS.app/Contents/Resources/python/re.py", line 125, in <module>
    import sre_compile
  File "/Applications/QGIS.app/Contents/Resources/python/sre_compile.py", line 17, in <module>
    assert _sre.MAGIC == MAGIC, "SRE module mismatch"
  AssertionError: SRE module mismatch
  ```

### Analysis
**This is a QGIS Python conflict issue** - Max's system has QGIS installed, which bundles its own Python. When running `python3`, it's using QGIS's Python instead of the system Python, causing module conflicts.

**What Was Supposedly Fixed:**
According to `SESSION-SUMMARY.md` (Build 2025-11-28-013):
- Updated `yourdad.py` shebang from `#!/usr/bin/env python3` to `#!/usr/bin/python3`
- Updated menu script to detect and avoid QGIS Python
- Added troubleshooting documentation

**However:**
- Max is still running `python3 yourdad.py` directly (not using the menu script)
- The shebang fix only helps when running `./yourdad.py` directly
- When running `python3 yourdad.py`, it still uses whatever `python3` points to (QGIS's Python)

### Solutions

**Option 1: Use System Python Directly**
```bash
/usr/bin/python3 yourdad.py scan all 2>&1 | tee scan-output.txt
```

**Option 2: Use the Menu Script**
```bash
./yourdad
```
The menu script should detect and avoid QGIS Python.

**Option 3: Fix PATH**
Check what `python3` points to:
```bash
which python3
```

If it points to QGIS, either:
- Use `/usr/bin/python3` directly
- Or modify PATH to prioritize system Python

**Option 4: Create a Wrapper Script**
Create a `run_yourdad.sh` script that ensures system Python is used:
```bash
#!/bin/bash
/usr/bin/python3 "$(dirname "$0")/yourdad.py" "$@"
```

### Recommended Fix
1. **Update README.md** with explicit QGIS troubleshooting
2. **Create a wrapper script** `run_yourdad.sh` that uses system Python
3. **Update installation instructions** to mention QGIS conflict
4. **Test the menu script** to ensure it properly detects and avoids QGIS Python

---

## Summary

### Bug #2: fork_exec() Error
- **Status:** Still occurring
- **Action:** Need diagnostic output OR proactively fix likely culprits
- **Priority:** 🔴 CRITICAL

### QGIS Python Conflict
- **Status:** Partially fixed (shebang), but direct `python3` call still fails
- **Action:** Need better documentation and/or wrapper script
- **Priority:** 🟡 MEDIUM (workaround exists)

---

## Recommendations

1. **Immediate:**
   - Add QGIS troubleshooting to README
   - Create wrapper script for system Python
   - Test menu script on Max's machine

2. **Short Term:**
   - Get diagnostic output for Bug #2 (or fix proactively)
   - Update installation instructions

3. **Documentation:**
   - Add QGIS section to troubleshooting
   - Document all workarounds clearly

---

**Next Action:** 
1. Create wrapper script for QGIS conflict
2. Update README with QGIS troubleshooting
3. Proactively fix Bug #2 likely culprits OR wait for diagnostic output

