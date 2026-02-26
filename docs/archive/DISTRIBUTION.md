# Distribution Strategy for Dad Ware

## Current State: Python CLI

The application is currently distributed as a Python CLI tool that can be:
- Run directly from source (development)
- Installed via Homebrew (technical users)
- Packaged as a standalone binary (future)

## Distribution Phases

### Phase 1: CLI Distribution (Current)

**Target Users:** Technical users, developers, early adopters

**Methods:**
1. **Homebrew Formula** (`Formula/yourdad.rb`)
   - Install via: `brew install --build-from-source ./Formula/yourdad.rb`
   - Or add to a Homebrew tap for easier installation
   - Includes post-install instructions for permissions

2. **Direct Installation Script** (`scripts/install.sh`)
   - Checks Python version
   - Installs dependencies
   - Creates symlink for `yourdad` command
   - Guides user through permission setup

3. **Manual Installation**
   - Clone repository
   - Run from source
   - Use `scripts/check_permissions.py` to verify setup

**Permission Handling:**
- Manual setup required (user must grant Full Disk Access)
- Clear instructions provided during installation
- Permission checker script available
- Graceful degradation when permissions missing

### Phase 2: Mac App Bundle (Future)

**Target Users:** Non-technical users, general Mac users

**Architecture:**
- **Swift Helper** (`macos-helper/PermissionHelper.swift`)
  - Handles permission detection and requests
  - Can trigger system permission dialogs
  - Foundation for full Mac app

- **Python Backend**
  - Core scanning logic remains in Python
  - Mac app can call Python scripts via subprocess
  - Or Python code can be embedded in app bundle

- **Mac App Bundle Structure:**
  ```
  DadWare.app/
  ├── Contents/
  │   ├── MacOS/
  │   │   └── DadWare (Swift app)
  │   ├── Resources/
  │   │   ├── yourdad.py
  │   │   ├── personality/
  │   │   ├── renderers/
  │   │   ├── scanners/
  │   │   ├── utils/
  │   │   └── PermissionHelper.app
  │   └── Info.plist
  ```

**Permission Handling:**
- System permission dialogs appear automatically
- No manual setup required
- Better UX for non-technical users

**Distribution Options:**
1. **Direct Download** (DMG or ZIP)
   - Host on website
   - Users download and drag to Applications
   - May require Gatekeeper approval

2. **Mac App Store**
   - Sandboxed environment (may limit functionality)
   - Requires Apple Developer account
   - Automatic updates
   - User trust

3. **Notarized Distribution**
   - Direct download with Apple notarization
   - No App Store restrictions
   - Still requires Gatekeeper approval

### Phase 3: Hybrid Approach

**Best of Both Worlds:**
- CLI remains available for technical users
- Mac app provides better UX for non-technical users
- Both can coexist and share core Python code
- Mac app can optionally include CLI in bundle

## Migration Path

### Current → Phase 1 (CLI Distribution)
- ✅ Homebrew formula created
- ✅ Installer script created
- ✅ Permission checker script created
- ⏳ Test with technical users
- ⏳ Gather feedback

### Phase 1 → Phase 2 (Mac App)
- ⏳ Build Swift helper framework
- ⏳ Create Mac app bundle structure
- ⏳ Integrate Python backend
- ⏳ Test permission dialogs
- ⏳ Package for distribution

## Technical Considerations

### Permission Requirements

**Full Disk Access** is required for:
- Photos Library scanning
- Messages scanning
- Mail scanning

**Why:**
- macOS protects these directories for privacy
- Only apps with Full Disk Access can read them
- CLI apps cannot trigger permission dialogs automatically
- Mac app bundles CAN trigger permission dialogs

### Distribution Challenges

1. **Permission Setup (CLI)**
   - Users must manually grant permissions
   - Instructions must be clear and easy to follow
   - Permission checker helps verify setup

2. **Code Signing (Mac App)**
   - Required for distribution
   - Apple Developer account needed
   - Notarization required for Gatekeeper

3. **Python Dependencies**
   - Currently uses standard library only
   - If dependencies added, need to bundle or use system Python
   - PyInstaller or similar for standalone binary

## Recommendations

### For Technical Users (Now)
- Use Homebrew formula or direct installation
- Clear permission setup instructions
- Permission checker script for troubleshooting

### For Non-Technical Users (Future)
- Build Mac app bundle with Swift helper
- Automatic permission dialogs
- Native macOS experience
- Consider App Store for distribution

### Timeline
- **Phase 1 (CLI):** Ready for testing
- **Phase 2 (Mac App):** Framework in place, needs implementation
- **Phase 3 (Hybrid):** Long-term goal

## Files

- `Formula/yourdad.rb` - Homebrew formula
- `scripts/install.sh` - Installation script
- `scripts/check_permissions.py` - Permission checker
- `macos-helper/` - Swift helper framework (future Mac app)
- `DISTRIBUTION.md` - This file

