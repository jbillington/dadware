# Single Volume Auto-Select Fix

**Date:** December 2025  
**Issue:** Menu asks user to choose volume even when only one volume exists

---

## Problem

When running a storage scan, the program always prompts the user to select a volume, even when there's only one volume available. This creates unnecessary friction in the user experience.

**Before:**
```
Available volumes:
1) Macintosh HD (/) - 460.4 GB, 173.7 GB used (38%)

Note: Home directory will be scanned separately for detailed breakdown.
Pick one [1]: 
```

User has to press Enter even though there's only one option.

---

## Solution

Automatically select the volume when there's only one available. Only show the menu when multiple volumes exist.

**After:**
```
→ Using Macintosh HD (/) - 460.4 GB, 173.7 GB used (38%)
Note: Home directory will be scanned separately for detailed breakdown.

→ scanning volume: /
```

Scan starts immediately without prompting.

---

## Implementation

### Changes Made

**File:** `utils/volumes.py`

**Logic:**
1. Get list of volumes
2. If only one volume exists:
   - Automatically select it
   - Show brief confirmation message
   - Return the volume path immediately
3. If multiple volumes exist:
   - Show interactive menu as before
   - Prompt user to choose

### Code Changes

```python
# If only one volume, automatically select it
if len(volumes) == 1:
    selected_volume = volumes[0]
    info = selected_volume['info']
    print(f"\n→ Using {selected_volume['name']} ({selected_volume['path']}) - "
          f"{info['total_human']}, {info['used_human']} used ({info['used_percent']:.0f}%)")
    print("Note: Home directory will be scanned separately for detailed breakdown.\n")
    return selected_volume['path']
```

---

## Benefits

1. **Better UX** - No unnecessary prompts when only one option exists
2. **Faster workflow** - Scan starts immediately
3. **Still flexible** - Menu still appears when multiple volumes exist
4. **Clear feedback** - User still sees which volume is being used

---

## Testing

### Single Volume Scenario
- Run storage scan with only one volume mounted
- Should automatically select and start scan
- Should show brief confirmation message

### Multiple Volumes Scenario
- Mount additional external drive
- Run storage scan
- Should show menu with all volumes
- Should prompt for selection

### Edge Cases
- No volumes found - Should show error (unchanged)
- Invalid volume path provided - Should fall back to menu (unchanged)

---

## Related

This addresses the enhancement logged in `docs/roadmap/FEATURE-ENHANCEMENTS.md`:
- **Enhancement:** Single Volume Confirmation
- **Status:** ✅ Implemented

---

**Status:** ✅ Fixed  
**Files Modified:**
- `utils/volumes.py` - Added auto-select for single volume

