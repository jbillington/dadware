# TUI Architecture - Integration with Core CLI

**Goal:** Add TUI support without modifying `yourdad.py` core CLI code.

---

## Current Architecture

### Current Structure
```
yourdad.py          # Core CLI (argparse-based)
yourdad             # Menu script (calls yourdad.py via subprocess)
scanners/           # Scan functions (storage, cpu, mac_libraries)
renderers/          # Output renderers (terminal, html)
utils/              # Utilities (volumes, permissions, etc.)
personality/        # Personality/commentary
```

### How It Works Now
- `yourdad` menu script → calls `yourdad.py scan <type>` via subprocess
- `yourdad.py` → imports scanners, runs scans, renders output
- Scanners are pure functions that return data
- Renderers take data and output (terminal/HTML)

---

## TUI Architecture (No Core Changes Needed)

### New Structure
```
yourdad.py          # Core CLI (UNCHANGED)
yourdad             # Menu script (REMOVE THIS)
yourdad-tui         # New TUI entry point (NEW FILE)
tui/                # TUI code (NEW DIRECTORY)
  ├── app.py
  ├── screens/
  └── widgets/
scanners/           # Scan functions (UNCHANGED - TUI imports these)
renderers/          # Output renderers (UNCHANGED)
utils/              # Utilities (UNCHANGED - TUI imports these)
personality/        # Personality (UNCHANGED - TUI imports this)
```

---

## How TUI Integrates (No Core Changes)

### TUI Calls Scanners Directly (Non-Blocking)

**Instead of subprocess (like menu script):**
```python
# OLD: Menu script approach
subprocess.run(['python3', 'yourdad.py', 'scan', 'storage'])
```

**TUI imports and calls directly using worker threads:**
```python
# NEW: TUI approach with worker threads
from textual.worker import Worker, get_current_worker
from scanners.storage import scan_storage
from scanners.cpu import scan_cpu
from utils.volumes import select_volume

# In TUI screen:
async def run_storage_scan(self):
    volume = select_volume()  # Use same utility
    
    # Run scanner in worker thread (non-blocking)
    scan_data = await self.run_worker(
        self._scan_storage,
        volume_path=volume
    )
    # Display in TUI
```

### Key Points

1. **No changes to `yourdad.py`** - TUI doesn't use it
2. **No changes to scanners** - TUI imports and calls them
3. **No changes to utils** - TUI imports and uses them
4. **TUI is separate** - New files, new entry point
5. **Non-blocking** - Scanners run in worker threads to keep UI responsive
6. **Real-time progress** - Use existing `progress_callback` parameter

---

## File Structure

### New Files (TUI Only)

```
yourdad-tui          # New entry point script
tui/
├── __init__.py
├── app.py           # Main Textual app
├── screens/
│   ├── __init__.py
│   ├── menu_screen.py
│   ├── scan_screen.py
│   └── report_screen.py
└── widgets/
    ├── __init__.py
    └── progress_widget.py
```

### Entry Point: `yourdad-tui`

```python
#!/usr/bin/env python3
"""
Dad Ware TUI Entry Point
Launches the Textual TUI interface
"""

from tui.app import DadWareApp

if __name__ == '__main__':
    app = DadWareApp()
    app.run()
```

**Usage:**
```bash
python3 yourdad-tui        # Launch TUI
yourdad.py scan storage    # CLI still works unchanged
```

---

## How TUI Uses Existing Code

### Example: Storage Scan Screen (With Progress)

```python
# tui/screens/scan_screen.py
from textual.screen import Screen
from textual.worker import Worker, get_current_worker
from textual.widgets import ProgressBar, Static
from scanners.storage import scan_storage
from utils.volumes import select_volume
from personality.yourdad import add_personality

class StorageScanScreen(Screen):
    def compose(self):
        yield Static("Scanning...", id="status")
        yield ProgressBar(id="progress")
        yield Static("", id="details")
    
    async def on_mount(self):
        volume = select_volume()
        await self.run_scan(volume)
    
    async def run_scan(self, volume_path):
        # Run scanner in worker thread (non-blocking)
        scan_data = await self.run_worker(
            self._scan_storage,
            volume_path
        )
        
        # Add personality (use existing function)
        scan_data = add_personality(scan_data, 'storage')
        
        # Display in TUI
        self.app.push_screen(ReportScreen(scan_data))
    
    def _scan_storage(self, volume_path):
        """Run in worker thread - can block safely"""
        def progress_callback(items, elapsed):
            # Update UI from worker thread
            worker = get_current_worker()
            if worker:
                worker.call_from_thread(
                    self._update_progress,
                    items, elapsed
                )
        
        return scan_storage(
            volume_path=volume_path,
            top_files=500,
            min_size_bytes=0,
            progress_callback=progress_callback
        )
    
    def _update_progress(self, items, elapsed):
        """Called on UI thread - safe to update widgets"""
        self.query_one("#status").update(f"Found {items:,} items...")
        self.query_one("#details").update(f"Time: {elapsed:.0f}s")
        # Update progress bar if needed
```

### Example: CPU Scan Screen

```python
# tui/screens/scan_screen.py
from textual.screen import Screen
from textual.worker import Worker
from scanners.cpu import scan_cpu
from personality.yourdad import add_personality

class CPUScanScreen(Screen):
    async def on_mount(self):
        await self.run_scan()
    
    async def run_scan(self):
        # Run scanner in worker thread (non-blocking)
        scan_data = await self.run_worker(scan_cpu)
        
        # Add personality
        scan_data = add_personality(scan_data, 'cpu')
        
        # Display in TUI
        self.app.push_screen(ReportScreen(scan_data))
```

### Why Worker Threads?

**Problem:** Scanners are synchronous and can take time (especially storage scans)
- If called directly, they block the UI thread
- UI becomes unresponsive during scans
- Can't show real-time progress updates

**Solution:** Use Textual's worker system
- Run scanners in background worker thread
- UI thread stays responsive
- Can update progress in real-time via callbacks
- Better user experience

---

## Benefits of This Architecture

### 1. Complete Separation
- TUI code is isolated in `tui/` directory
- Core CLI (`yourdad.py`) remains untouched
- No risk of breaking CLI functionality

### 2. Direct Function Calls
- TUI calls scanner functions directly (no subprocess overhead)
- Can get real-time progress callbacks
- Better error handling
- Faster execution

### 3. Shared Utilities
- TUI uses same volume selection (`utils.volumes`)
- TUI uses same permission checks (`utils.permissions`)
- TUI uses same personality system (`personality.yourdad`)
- No code duplication

### 4. Easy Maintenance
- Scanner changes automatically work in both CLI and TUI
- Utility changes benefit both interfaces
- Clear separation of concerns

---

## Migration Path

### Phase 1: Add TUI (No Changes to Core)
1. Create `tui/` directory
2. Create `yourdad-tui` entry point
3. Build TUI screens that import scanners
4. Test TUI alongside CLI

### Phase 2: Remove Menu Script
1. Delete `yourdad` menu script
2. Update documentation
3. Users can use `yourdad-tui` or `yourdad.py` directly

### Phase 3: Optional - Make TUI Default
1. Rename `yourdad-tui` → `yourdad` (if desired)
2. Keep `yourdad.py` as `yourdad-cli` (if desired)
3. Or keep both as-is

---

## Code Example: Complete TUI Integration

### TUI App Structure

```python
# tui/app.py
from textual.app import App
from tui.screens.menu_screen import MenuScreen

class DadWareApp(App):
    def on_mount(self):
        self.push_screen(MenuScreen())
```

### Menu Screen

```python
# tui/screens/menu_screen.py
from textual.screen import Screen
from textual.widgets import Button
from tui.screens.scan_screen import StorageScanScreen

class MenuScreen(Screen):
    def compose(self):
        yield Button("Scan Storage", id="storage")
        yield Button("Scan CPU", id="cpu")
    
    def on_button_pressed(self, event):
        if event.button.id == "storage":
            self.app.push_screen(StorageScanScreen())
```

### Scan Screen (Uses Existing Scanners with Worker Threads)

```python
# tui/screens/scan_screen.py
from textual.screen import Screen
from textual.worker import Worker, get_current_worker
from scanners.storage import scan_storage
from utils.volumes import select_volume

class StorageScanScreen(Screen):
    async def on_mount(self):
        volume = select_volume()
        
        # Run in worker thread (non-blocking)
        scan_data = await self.run_worker(
            scan_storage,
            volume_path=volume,
            progress_callback=self.update_progress
        )
        
        # Display in TUI
        self.display_results(scan_data)
    
    def update_progress(self, items, elapsed):
        # Update progress bar/widgets
        pass
```

---

## What Gets Imported (No Changes Needed)

### From Existing Code
```python
# Scanners (unchanged)
from scanners.storage import scan_storage
from scanners.cpu import scan_cpu
from scanners.mac_libraries import scan_all_mac_libraries

# Utilities (unchanged)
from utils.volumes import select_volume, format_size
from utils.permissions import check_full_disk_access

# Personality (unchanged)
from personality.yourdad import add_personality

# Constants (unchanged)
from yourdad import VERSION, BUILD, get_reports_dir
```

**Note:** You might want to move `VERSION` and `BUILD` to a shared constants file, but it's not required - TUI can import from `yourdad.py` without executing the CLI code.

---

## Summary

### ✅ What You Can Do
- **Add TUI as new files** - `tui/` directory, `yourdad-tui` entry point
- **Import existing scanners** - Direct function calls, no subprocess
- **Use existing utilities** - Volume selection, permissions, etc.
- **Remove menu script** - `yourdad` can be deleted
- **Keep CLI unchanged** - `yourdad.py` stays exactly as-is

### ❌ What You Don't Need
- **No changes to `yourdad.py`** - TUI doesn't use it
- **No changes to scanners** - TUI imports them directly
- **No changes to renderers** - TUI has its own display
- **No subprocess calls** - Direct function imports

### 🎯 Result
- **Clean separation** - TUI and CLI are independent
- **Shared code** - Scanners and utilities used by both
- **Easy maintenance** - Changes to scanners benefit both
- **No risk** - CLI remains untouched and functional

---

---

## Supporting All Design Document Features

### Required Features (From Design Document)

#### 1. State Machine Support
All states from design document are supported:
- **MENU** → `MenuScreen`
- **SCAN_CPU/STORAGE/ALL** → `ScanScreen` (with type parameter)
- **SCAN_PROGRESS** → Progress display in `ScanScreen`
- **REPORT_VIEW** → `ReportScreen`
- **VIEW_REPORTS** → `ReportsListScreen` → `ReportScreen`
- **SETTINGS** → `SettingsScreen`
- **HELP_MODAL** → `HelpScreen` (modal overlay)

#### 2. Real-Time Progress
- Use `progress_callback` parameter in `scan_storage()`
- Update UI widgets from worker thread via `worker.call_from_thread()`
- Display progress bar, item count, elapsed time

#### 3. Report Viewing
- Load JSON reports from `~/.dadware/reports/` (using `get_reports_dir()`)
- Parse JSON data (same format as CLI generates)
- Display in TUI with navigation
- Option to open in browser (using `webbrowser` module)

#### 4. Settings/Configuration
- Create `SettingsScreen` for configuration
- Store settings in `~/.dadware/config.json` (new file)
- Settings: default scan options, report location, etc.

#### 5. Help Modal
- Create `HelpScreen` as modal overlay
- Show keybindings reference
- Accessible via `?` keybinding

#### 6. Recent Activity Tracking
- Store recent scans in `~/.dadware/activity.json` (new file)
- Display in menu screen
- Track: scan type, timestamp, report path

#### 7. Export Functionality
- Use existing export functions from `yourdad.py`
- Add export option in report view
- Export to CSV (memory) or other formats

### Additional Screens Needed

```
tui/
├── screens/
│   ├── menu_screen.py          # Main menu
│   ├── scan_screen.py          # Scan progress (handles CPU/Storage/All)
│   ├── report_screen.py        # View single report
│   ├── reports_list_screen.py  # List of previous reports
│   ├── settings_screen.py      # Settings/configuration
│   └── help_screen.py          # Help modal
```

### Integration with Existing Code

#### Report Loading
```python
# tui/screens/reports_list_screen.py
from yourdad import get_reports_dir
import json
import os
from pathlib import Path

class ReportsListScreen(Screen):
    def load_reports(self):
        reports_dir = get_reports_dir()
        reports = []
        for file in Path(reports_dir).glob("*.json"):
            with open(file) as f:
                data = json.load(f)
                reports.append({
                    'path': str(file),
                    'type': data.get('scan_type'),
                    'timestamp': file.stem
                })
        return reports
```

#### Export Functionality
```python
# tui/screens/report_screen.py
from yourdad import export_memory_to_csv
import webbrowser
from pathlib import Path

class ReportScreen(Screen):
    def export_report(self):
        if self.scan_data['scan_type'] == 'cpu':
            export_memory_to_csv(
                self.scan_data,
                f"memory_export_{timestamp}.csv"
            )
    
    def open_in_browser(self):
        # Find HTML report
        reports_dir = get_reports_dir()
        html_file = Path(reports_dir) / f"{self.report_id}.html"
        if html_file.exists():
            webbrowser.open(f"file://{html_file}")
```

#### Recent Activity
```python
# tui/utils/activity.py
import json
from pathlib import Path
from datetime import datetime

ACTIVITY_FILE = Path.home() / ".dadware" / "activity.json"

def save_activity(scan_type, report_path):
    """Save scan to activity log"""
    activities = load_activities()
    activities.append({
        'type': scan_type,
        'path': report_path,
        'timestamp': datetime.now().isoformat()
    })
    # Keep last 10
    activities = activities[-10:]
    
    ACTIVITY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ACTIVITY_FILE, 'w') as f:
        json.dump(activities, f)

def load_activities():
    """Load recent activity"""
    if ACTIVITY_FILE.exists():
        with open(ACTIVITY_FILE) as f:
            return json.load(f)
    return []
```

### Complete Feature Support Matrix

| Feature | Design Doc | Architecture Support | Implementation |
|---------|------------|---------------------|----------------|
| Keyboard navigation | ✅ | ✅ | Textual keybindings |
| Real-time progress | ✅ | ✅ | Worker threads + progress_callback |
| Report viewing | ✅ | ✅ | Load JSON, display in TUI |
| Settings | ✅ | ✅ | SettingsScreen + config file |
| Help modal | ✅ | ✅ | HelpScreen as modal |
| Recent activity | ✅ | ✅ | Activity tracking file |
| Export | ✅ | ✅ | Use existing export functions |
| Open in browser | ✅ | ✅ | webbrowser module |
| Scan cancellation | ✅ | ✅ | Worker cancellation |
| Multiple scan types | ✅ | ✅ | ScanScreen with type param |

---

**This architecture supports all features from the design document without touching your core CLI code!**

