# Permission Handling and Distribution Strategy

## Current State
- Python CLI app that needs Full Disk Access for Photos/Messages/Mail
- No permission detection or user guidance
- Manual permission setup required

## Goal
- Phase 1: Improve CLI with permission detection and clear guidance
- Phase 2: Create Swift helper framework for future Mac app bundle
- Phase 3: Document distribution path (Homebrew → Mac App Bundle)

---

## Phase 1: CLI Permission Detection & Guidance

### 1.1 Add Permission Detection Module
**File:** `utils/permissions.py` (new file)

**Features:**
- `check_full_disk_access()` - Test if we can read protected directories
- `check_messages_access()` - Test Messages folder access
- `check_photos_access()` - Test Photos library access
- `check_mail_access()` - Test Mail folder access
- Returns structured results: `{'has_access': bool, 'missing_permissions': list}`

**Implementation:**
```python
def check_full_disk_access():
    """Check if Full Disk Access is granted by testing protected directories."""
    test_paths = [
        os.path.expanduser('~/Library/Messages'),
        os.path.expanduser('~/Library/Mail'),
        os.path.expanduser('~/Pictures/Photos Library.photoslibrary')
    ]
    # Try to list contents or check file access
    # Return which permissions are missing
```

### 1.2 Add Permission Check to Storage Scan
**File:** `yourdad.py`

**Changes:**
- Before scanning Mac libraries, check permissions
- If missing, show helpful error message with instructions
- Continue scan but mark libraries as "permission restricted"
- Add `--skip-protected` flag to skip protected directories entirely

### 1.3 Improve User Guidance
**File:** `renderers/html.py` and `renderers/terminal.py`

**Changes:**
- Show permission status in reports
- Display warning if libraries couldn't be scanned due to permissions
- Add link/instructions to grant permissions in HTML report
- Show "Permission required" indicator in grade breakdown

### 1.4 Create Permission Helper Script
**File:** `scripts/check_permissions.py` (new file)

**Purpose:**
- Standalone script users can run to check permission status
- Shows clear instructions if permissions are missing
- Can be run before main scan

---

## Phase 2: Swift Helper Framework (Future Mac App)

### 2.1 Create Swift Helper Project Structure
**Directory:** `macos-helper/` (new directory)

**Files:**
- `macos-helper/PermissionHelper.swift` - Core permission checking/requesting
- `macos-helper/Info.plist` - Required entitlements
- `macos-helper/build.sh` - Build script for helper app

**Purpose:**
- Mac app bundle can use this to trigger system permission dialogs
- CLI can optionally call this helper if bundled together
- Foundation for future full Mac app

**Key Features:**
```swift
class PermissionHelper {
    static func checkFullDiskAccess() -> Bool
    static func requestFullDiskAccess() -> Bool
    static func openSystemPreferences()
}
```

### 2.2 Integration Points
**File:** `utils/permissions.py`

**Changes:**
- Add function to detect if Swift helper is available
- Optionally call Swift helper if present
- Fall back to Python detection if helper not available

---

## Phase 3: Distribution Documentation

### 3.1 Homebrew Formula (Tech Users)
**File:** `Formula/yourdad.rb` (new file)

**Features:**
- Install Python CLI via Homebrew
- Include permission setup instructions in post-install message
- Simple distribution for technical users

### 3.2 Mac App Bundle Plan
**File:** `DISTRIBUTION.md` (new file)

**Document:**
- Current: Python CLI via Homebrew
- Future: Mac App Bundle with Swift helper
- Migration path and timeline
- How Mac app will handle permissions (system dialog)

### 3.3 Installer Script (Optional)
**File:** `scripts/install.sh` (new file)

**Features:**
- Check Python version
- Install dependencies (if any added)
- Guide user through permission setup
- Create symlink for `yourdad` command

---

## Implementation Priority

### Immediate (Phase 1)
1. Create `utils/permissions.py` with detection functions
2. Add permission check to storage scan
3. Show helpful error messages when permissions missing
4. Update HTML/terminal reports to show permission status

### Short-term (Phase 2)
5. Create Swift helper framework structure
6. Document how it will integrate with Mac app
7. Test permission detection accuracy

### Long-term (Phase 3)
8. Create Homebrew formula
9. Build Mac app bundle prototype
10. Full Mac app with permission dialogs

---

## Key Files to Create/Modify

**New Files:**
- `utils/permissions.py` - Permission detection
- `scripts/check_permissions.py` - Standalone permission checker
- `macos-helper/PermissionHelper.swift` - Swift helper (future)
- `Formula/yourdad.rb` - Homebrew formula
- `DISTRIBUTION.md` - Distribution strategy doc
- `scripts/install.sh` - Installer script

**Modified Files:**
- `yourdad.py` - Add permission check before Mac libraries scan
- `scanners/mac_libraries.py` - Better error handling for permissions
- `renderers/html.py` - Show permission status in report
- `renderers/terminal.py` - Show permission warnings

---

## User Experience Flow

### Current (No Permissions)
1. User runs scan
2. Libraries show 0 bytes
3. User confused

### Improved (Phase 1)
1. User runs scan
2. Permission check runs first
3. Clear message: "Full Disk Access required for Photos/Messages/Mail"
4. Instructions shown: "Go to System Settings → Privacy & Security → Full Disk Access"
5. Scan continues, but shows "Permission Restricted" for protected libraries
6. Report clearly indicates which data couldn't be scanned

### Future (Mac App)
1. User opens Mac app
2. App detects missing permissions
3. System permission dialog appears automatically
4. User grants permission
5. Full scan with all data

---

## Technical Notes

- macOS doesn't allow programmatic permission requests from CLI
- Mac app bundles CAN trigger system permission dialogs
- Swift helper will be optional - CLI works without it
- Permission detection uses file access tests (try to read protected directories)
- `du` command fallback already implemented for Photos library

---

## Distribution Strategy Summary

**Phase 1 (Now):** Python CLI with permission detection
- Homebrew formula for tech users
- Clear instructions for permission setup
- Graceful degradation when permissions missing

**Phase 2 (Future):** Mac App Bundle
- Swift helper for permission dialogs
- Native macOS experience
- Better UX for non-technical users
- Can still include CLI as part of bundle

**Migration Path:**
- Keep CLI working independently
- Mac app can wrap CLI or use same Python code
- Users can choose: CLI (Homebrew) or Mac app (App Store/Direct download)

