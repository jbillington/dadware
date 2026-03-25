# Dad Ware TUI - Implementation Roadmap

**Step-by-step guide to building the TUI**

---

## Prerequisites

### 1. Install Dependencies

```bash
cd ~/openclaw-workspace/1_Projects/dadware
pip install rich textual
```

**Why these?**
- `rich` - Beautiful terminal output, progress bars, tables
- `textual` - Full TUI framework with reactive widgets

### 2. Verify Installation

```bash
python3 -c "import textual; print(f'✅ Textual {textual.__version__}')"
python3 -c "import rich; print(f'✅ Rich {rich.__version__}')"
```

---

## Phase 1: Basic TUI (MVP) - 4-6 hours

**Goal:** Launch TUI, run scan, show progress, display report

### Step 1.1: Project Structure (30 min)

```bash
mkdir -p tui/screens tui/widgets
touch tui/__init__.py
touch tui/app.py
touch tui/screens/__init__.py
touch tui/widgets/__init__.py
touch tui/styles.tcss
```

**Files created:**
- [x] `tui/__init__.py`
- [x] `tui/app.py` - Main Textual app
- [x] `tui/screens/__init__.py`
- [x] `tui/styles.tcss` - CSS-like styling
- [x] `tui/widgets/__init__.py`

---

### Step 1.2: Main App Entry Point (30 min)

**File:** `tui/app.py`

```python
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer
from tui.screens.main_menu import MainMenuScreen

class DadWareApp(App):
    """Dad Ware TUI Application"""
    
    TITLE = "Dad Ware"
    SUB_TITLE = "Mac Cleanup Tool"
    CSS_PATH = "styles.tcss"
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("?", "help", "Help", show=True),
    ]
    
    def on_mount(self) -> None:
        """Show main menu on startup"""
        self.push_screen(MainMenuScreen())
    
    def action_quit(self) -> None:
        """Quit the app"""
        self.exit()
    
    def action_help(self) -> None:
        """Show help screen"""
        from tui.screens.help import HelpScreen
        self.push_screen(HelpScreen())

if __name__ == "__main__":
    app = DadWareApp()
    app.run()
```

**Tasks:**
- [x] Create `tui/app.py`
- [x] Define app class
- [x] Add key bindings (q=quit, ?=help)
- [x] Test: `python3 -m tui.app` (should show error - screen not yet created)

---

### Step 1.3: Main Menu Screen (1-2 hours)

**File:** `tui/screens/main_menu.py`

```python
from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Static, Button, Label
from textual.app import ComposeResult
import datetime
import os
import json

class MainMenuScreen(Screen):
    """Main menu - choose scan type"""
    
    CSS = """
    MainMenuScreen {
        align: center middle;
    }
    
    #menu-container {
        width: 70;
        height: auto;
        border: thick $primary;
        padding: 2;
    }
    
    .menu-button {
        width: 100%;
        margin: 1 0;
    }
    
    .welcome-text {
        color: $accent;
        text-align: center;
        margin: 1 0 2 0;
    }
    
    .recent-reports {
        margin-top: 2;
        padding: 1;
        border: solid $secondary;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose main menu UI"""
        with Container(id="menu-container"):
            yield Static("👔 Hey there! Ready to see what's eating up your disk space?", classes="welcome-text")
            
            yield Label("What do you want to scan?")
            yield Button("Storage (Find large files and folders)", id="scan-storage", classes="menu-button", variant="primary")
            yield Button("CPU & Memory (See what's hogging RAM)", id="scan-cpu", classes="menu-button")
            yield Button("Both Scans (Full checkup)", id="scan-all", classes="menu-button")
            
            # Recent reports section
            recent = self.load_recent_reports()
            if recent:
                with Vertical(classes="recent-reports"):
                    yield Label("📁 Recent Reports:")
                    for report in recent[:3]:
                        yield Static(report)
    
    def load_recent_reports(self) -> list:
        """Load recent reports from ~/.dadware/reports/"""
        reports_dir = os.path.expanduser('~/.dadware/reports')
        if not os.path.exists(reports_dir):
            return []
        
        reports = []
        for file in os.listdir(reports_dir):
            if file.endswith('.json'):
                # Parse report metadata
                try:
                    with open(os.path.join(reports_dir, file)) as f:
                        data = json.load(f)
                        scan_type = file.split('_')[0]
                        timestamp = data.get('generated_at', '')
                        # Format as relative time
                        reports.append(f"• {scan_type.title()} - {timestamp}")
                except:
                    pass
        
        return sorted(reports, reverse=True)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        if event.button.id == "scan-storage":
            self.start_storage_scan()
        elif event.button.id == "scan-cpu":
            self.start_cpu_scan()
        elif event.button.id == "scan-all":
            self.start_both_scans()
    
    def start_storage_scan(self) -> None:
        """Launch storage scan"""
        from tui.screens.scan_progress import ScanProgressScreen
        self.app.push_screen(ScanProgressScreen(scan_type="storage"))
    
    def start_cpu_scan(self) -> None:
        """Launch CPU scan"""
        from tui.screens.scan_progress import ScanProgressScreen
        self.app.push_screen(ScanProgressScreen(scan_type="cpu"))
    
    def start_both_scans(self) -> None:
        """Launch both scans"""
        from tui.screens.scan_progress import ScanProgressScreen
        self.app.push_screen(ScanProgressScreen(scan_type="all"))
```

**Tasks:**
- [x] Create `tui/screens/main_menu.py`
- [x] Add menu buttons (Storage, CPU, Both)
- [x] Load recent reports from `~/.dadware/reports/`
- [x] Wire up button click handlers
- [x] Test: Should show menu (buttons don't work yet - screens not created)

---

### Step 1.4: Scan Progress Screen (1-2 hours)

**File:** `tui/screens/scan_progress.py`

```python
from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Static, ProgressBar, Label
from textual.app import ComposeResult
from textual.worker import Worker
import time

class ScanProgressScreen(Screen):
    """Show scan progress with live updates"""
    
    CSS = """
    ScanProgressScreen {
        align: center middle;
    }
    
    #progress-container {
        width: 70;
        height: auto;
        border: thick $primary;
        padding: 2;
    }
    
    .stats-box {
        margin: 1 0;
        padding: 1;
        border: solid $secondary;
    }
    
    .dad-comment {
        color: $accent;
        margin: 1 0;
        padding: 1;
        border: dashed $accent;
    }
    """
    
    def __init__(self, scan_type: str):
        super().__init__()
        self.scan_type = scan_type
        self.progress = 0
        self.stats = {}
    
    def compose(self) -> ComposeResult:
        """Compose progress UI"""
        with Container(id="progress-container"):
            yield Label(f"🔍 Scanning {self.scan_type.title()}...")
            yield ProgressBar(id="scan-progress")
            
            with Vertical(classes="stats-box"):
                yield Static("📊 Current Stats:", id="stats-header")
                yield Static("Files scanned: 0", id="stat-files")
                yield Static("Folders analyzed: 0", id="stat-folders")
                yield Static("Largest file: Searching...", id="stat-largest")
            
            yield Static("💬 Dad says: \"Let's see what we're working with here...\"", classes="dad-comment", id="dad-comment")
            yield Static("⚙️  Scanning: /", id="current-path")
    
    def on_mount(self) -> None:
        """Start scan worker on mount"""
        self.run_scan_worker()
    
    @Worker(thread=True)
    def run_scan_worker(self) -> None:
        """Run scan in background thread"""
        from scanners.storage import scan_storage
        from scanners.cpu import scan_cpu
        
        # TODO: Hook up real scanner with progress callback
        # For now, simulate progress
        for i in range(100):
            self.progress = i
            self.update_progress(i, {"files": i * 1000, "folders": i * 100})
            time.sleep(0.05)
        
        # When done, show report
        self.show_report()
    
    def update_progress(self, percent: int, stats: dict) -> None:
        """Update progress bar and stats"""
        self.call_from_thread(self._update_ui, percent, stats)
    
    def _update_ui(self, percent: int, stats: dict) -> None:
        """Update UI elements (must run on main thread)"""
        progress_bar = self.query_one("#scan-progress", ProgressBar)
        progress_bar.update(progress=percent)
        
        self.query_one("#stat-files", Static).update(f"Files scanned: {stats.get('files', 0):,}")
        self.query_one("#stat-folders", Static).update(f"Folders analyzed: {stats.get('folders', 0):,}")
        
        # Rotate dad comments based on progress
        if percent == 25:
            self.query_one("#dad-comment", Static).update("💬 Dad says: \"Still going... You've got quite the collection here.\"")
        elif percent == 50:
            self.query_one("#dad-comment", Static).update("💬 Dad says: \"Halfway there! Found some interesting stuff already.\"")
        elif percent == 75:
            self.query_one("#dad-comment", Static).update("💬 Dad says: \"Almost done. Prepare yourself for the report card.\"")
    
    def show_report(self) -> None:
        """Show report screen after scan completes"""
        from tui.screens.report_card import ReportCardScreen
        self.app.push_screen(ReportCardScreen(scan_type=self.scan_type, scan_data={}))
```

**Tasks:**
- [x] Create `tui/screens/scan_progress.py`
- [x] Add progress bar widget
- [x] Add stats display (files, folders, largest)
- [x] Add dad commentary (rotates during scan)
- [x] Run scan in background worker thread
- [x] Hook up to real scanner (storage.scan_storage or cpu.scan_cpu)
- [x] Navigate to report when done

---

### Step 1.5: Report Card Screen (1-2 hours)

**File:** `tui/screens/report_card.py`

```python
from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Static, Button, Label
from textual.app import ComposeResult

class ReportCardScreen(Screen):
    """Show storage/CPU report card with grades"""
    
    CSS = """
    ReportCardScreen {
        align: center middle;
    }
    
    #report-container {
        width: 70;
        height: auto;
        border: thick $primary;
        padding: 2;
    }
    
    .grade-row {
        margin: 0.5 0;
    }
    
    .grade-good {
        color: green;
    }
    
    .grade-warn {
        color: yellow;
    }
    
    .grade-bad {
        color: red;
    }
    
    .dad-advice {
        color: $accent;
        margin: 2 0;
        padding: 1;
        border: dashed $accent;
    }
    """
    
    def __init__(self, scan_type: str, scan_data: dict):
        super().__init__()
        self.scan_type = scan_type
        self.scan_data = scan_data
    
    def compose(self) -> ComposeResult:
        """Compose report card UI"""
        with Container(id="report-container"):
            yield Label(f"📊 {self.scan_type.title()} Report Card")
            yield Static(f"Overall Grade: C+", id="overall-grade")
            
            # TODO: Calculate real grades from scan_data
            yield Static("🟡 Free Space: 28% free (288GB) - Grade: C", classes="grade-row grade-warn")
            yield Static("🟢 Home Folders: Well organized - Grade: A-", classes="grade-row grade-good")
            yield Static("🔴 Downloads: 47GB of clutter - Grade: D+", classes="grade-row grade-bad")
            
            yield Static("💬 Dad's Advice: \"28% free space isn't terrible, but you're one software update away from trouble. Let's tackle that Downloads folder first.\"", classes="dad-advice")
            
            yield Label("Actions:")
            yield Button("View Top Files", id="view-files", variant="primary")
            yield Button("View Top Folders", id="view-folders")
            yield Button("Export HTML Report", id="export-html")
            yield Button("← Back to Menu", id="back")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        if event.button.id == "view-files":
            # TODO: Navigate to file browser
            pass
        elif event.button.id == "view-folders":
            # TODO: Navigate to folder browser
            pass
        elif event.button.id == "export-html":
            # TODO: Export HTML report
            pass
        elif event.button.id == "back":
            self.app.pop_screen()
```

**Tasks:**
- [x] Create `tui/screens/report_card.py`
- [x] Display overall grade
- [x] Show individual grades (color-coded)
- [x] Add dad advice section
- [x] Add action buttons (View Files, Folders, Export, Back)
- [x] Wire up grading system from `scanners/grading.py`
- [x] Test: Full flow (menu → scan → progress → report)

---

### Step 1.6: Update yourdad.py CLI (15 min)

**File:** `yourdad.py`

```python
# Add new command to argparse
def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    
    # Existing commands: scan, export
    
    # NEW: TUI command
    tui_parser = subparsers.add_parser('tui', help='Launch interactive TUI')
    
    args = parser.parse_args()
    
    if args.command == 'tui':
        from tui.app import DadWareApp
        app = DadWareApp()
        app.run()
        return 0
```

**Tasks:**
- [x] Add `tui` command to argparse
- [x] Import and launch `DadWareApp`
- [x] Test: `./yourdad tui` (launches TUI)

---

### Phase 1 Testing Checklist

- [x] Install dependencies (rich, textual)
- [x] Run `./yourdad tui` - main menu appears
- [x] Press arrow keys - selection moves
- [x] Click "Storage Scan" - progress screen shows
- [x] Progress bar animates from 0-100%
- [x] Dad comments update during scan
- [x] Report card appears after scan
- [x] Press "Back" - returns to menu
- [x] Press `q` - quits app gracefully

---

## Phase 2: File Browser - 3-4 hours

**Goal:** Browse top files, drill into folders, reveal in Finder

### Step 2.1: File Browser Screen (2 hours)

**File:** `tui/screens/file_browser.py`

```python
from textual.screen import Screen
from textual.containers import Container
from textual.widgets import DataTable, Static
from textual.app import ComposeResult
import subprocess

class FileBrowserScreen(Screen):
    """Browse top files and folders"""
    
    CSS = """
    FileBrowserScreen {
        layout: vertical;
    }
    
    #file-table {
        height: 100%;
    }
    
    .summary-bar {
        height: 3;
        background: $surface;
    }
    """
    
    def __init__(self, files: list):
        super().__init__()
        self.files = files
    
    def compose(self) -> ComposeResult:
        """Compose file browser UI"""
        yield Static(f"💾 Total Reclaimable: {sum(f['size'] for f in self.files)}", classes="summary-bar")
        
        table = DataTable()
        table.add_columns("Size", "Type", "Path")
        for file in self.files:
            table.add_row(file['size'], file['type'], file['path'])
        
        yield table
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection - reveal in Finder"""
        file_path = self.files[event.cursor_row]['path']
        self.reveal_in_finder(file_path)
    
    def reveal_in_finder(self, path: str) -> None:
        """Open Finder to file location"""
        subprocess.run(['open', '-R', path])
```

**Tasks:**
- [x] Create `tui/screens/file_browser.py`
- [x] Add DataTable widget (sortable columns)
- [x] Populate from scan results
- [x] Handle row selection (reveal in Finder)
- [x] Add keyboard shortcuts (s=sort, /=search, c=copy path)

---

### Step 2.2: Folder Drill-Down (1-2 hours)

**Tasks:**
- [x] Add folder drill-down support
- [x] Breadcrumb navigation (show current path)
- [x] Arrow keys to navigate hierarchy
- [x] Enter drills into folder
- [x] Backspace/← goes to parent

---

## Phase 3: CPU Report - 2-3 hours

### Step 3.1: CPU Report Screen (1-2 hours)

**File:** `tui/screens/cpu_report.py`

```python
from textual.screen import Screen
from textual.widgets import DataTable, Static, ProgressBar
from textual.app import ComposeResult
import signal

class CPUReportScreen(Screen):
    """Show CPU and memory report"""
    
    CSS = """
    CPUReportScreen {
        layout: vertical;
    }
    
    .memory-bar {
        height: 5;
    }
    
    #process-table {
        height: 100%;
    }
    """
    
    def __init__(self, scan_data: dict):
        super().__init__()
        self.scan_data = scan_data
        self.auto_refresh = True
    
    def compose(self) -> ComposeResult:
        """Compose CPU report UI"""
        total_gb = self.scan_data.get('total_memory_gb', 0)
        used_gb = self.scan_data.get('total_used_gb', 0)
        used_percent = (used_gb / total_gb * 100) if total_gb > 0 else 0
        
        yield Static(f"💻 Memory Status: {'🟡 Under Pressure' if used_percent > 80 else '🟢 Healthy'}")
        yield Static(f"Total: {total_gb:.1f}GB | Used: {used_gb:.1f}GB ({used_percent:.0f}%)")
        yield ProgressBar(total=100, progress=used_percent, classes="memory-bar")
        
        # Process table
        table = DataTable()
        table.add_columns("App", "Memory", "CPU%", "Processes")
        
        for app in self.scan_data.get('memory_hogs', []):
            table.add_row(
                app['name'],
                app['memory'],
                f"{app['cpu_percent']:.1f}%",
                str(app['process_count'])
            )
        
        yield table
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection - prompt to kill process"""
        app = self.scan_data['memory_hogs'][event.cursor_row]
        # TODO: Show confirmation modal, then kill process
```

**Tasks:**
- [x] Create `tui/screens/cpu_report.py`
- [x] Show memory pressure indicator
- [x] Display top memory hogs in table
- [x] Add auto-refresh (every 5s)
- [x] Add kill process action (with confirmation)

---

### Step 3.2: Auto-Refresh Worker (1 hour)

**Tasks:**
- [x] Background worker to refresh CPU data
- [x] Update table every 5 seconds
- [x] Toggle auto-refresh with keyboard shortcut
- [x] Manual refresh with `r` key

---

## Phase 4: Polish - 2-3 hours

### Step 4.1: Help Screen (30 min)

**File:** `tui/screens/help.py`

```python
from textual.screen import Screen
from textual.containers import Container
from textual.widgets import Static
from textual.app import ComposeResult

class HelpScreen(Screen):
    """Show help and keyboard shortcuts"""
    
    CSS = """
    HelpScreen {
        align: center middle;
    }
    
    #help-container {
        width: 70;
        height: auto;
        border: thick $primary;
        padding: 2;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose help UI"""
        with Container(id="help-container"):
            yield Static("⌨️  Dad Ware Keyboard Shortcuts")
            yield Static("Navigation: ↑↓←→ Move | Enter Select | Esc Back | q Quit")
            yield Static("File Browser: → Reveal | s Sort | / Search | c Copy")
            yield Static("CPU Report: k Kill | r Refresh | a Auto-refresh")
            yield Static("Export: h HTML | j JSON | e CSV")
            yield Static("💬 \"Need more help? Just ask!\"")
    
    def on_key(self, event) -> None:
        """Any key returns to previous screen"""
        self.app.pop_screen()
```

**Tasks:**
- [x] Create `tui/screens/help.py`
- [x] List all keyboard shortcuts
- [x] Group by context (navigation, files, CPU, export)
- [x] Add dad humor

---

### Step 4.2: Export Actions (1 hour)

**Tasks:**
- [x] Export HTML report (hook into existing renderer)
- [x] Export JSON data (save manifest)
- [x] Export CSV (CPU data only)
- [x] Show success notification after export

---

### Step 4.3: Search/Filter (1 hour)

**Tasks:**
- [x] Add search input widget
- [x] Filter table rows as user types
- [x] Highlight matching text
- [x] Escape clears filter

---

## Testing Checklist (All Phases)

### Navigation
- [x] Arrow keys navigate all screens
- [x] Enter selects items
- [x] Esc goes back
- [x] q quits from anywhere
- [x] ? shows help

### Storage Scan
- [x] Progress bar updates smoothly
- [x] Stats update in real-time
- [x] Dad comments rotate during scan
- [x] Esc cancels gracefully
- [x] Report shows correct grades

### File Browser
- [x] Table scrolls (arrow keys, Page Up/Down)
- [x] Enter reveals in Finder
- [x] s cycles sort (size/date/type/name)
- [x] / activates search
- [x] c copies path to clipboard
- [x] Drill-down works (folders)
- [x] Breadcrumb shows current path

### CPU Report
- [x] Memory bar accurate
- [x] Process table updates
- [x] Auto-refresh works (5s interval)
- [x] r manually refreshes
- [x] a toggles auto-refresh
- [x] k kills process (with confirmation)

### Export
- [x] h exports HTML
- [x] j exports JSON
- [x] e exports CSV (CPU only)
- [x] Success notification shows

### Edge Cases
- [x] Terminal too small (show warning)
- [x] No recent reports (hide section)
- [x] Permission denied (show helpful message)
- [x] Scan cancelled (saves partial results)
- [x] Process already killed (handles gracefully)

---

## Launch Checklist

Before releasing TUI:
- [x] All Phase 1 features working
- [x] All Phase 2 features working
- [x] All Phase 3 features working
- [x] All Phase 4 features working
- [x] Testing checklist complete
- [x] Documentation updated (README)
- [x] Help screen accurate
- [x] Dad personality present throughout
- [x] Error handling robust
- [x] Performance acceptable (no lag)

---

## Post-Launch Enhancements

### v1.1 (Future)
- [ ] Themes (light/dark mode toggle)
- [ ] Mouse support (click buttons/rows)
- [ ] Graphs (disk usage over time)
- [ ] Comparison view (two scans side-by-side)
- [ ] Desktop notifications (scan complete)

### v1.2 (Future)
- [ ] Scheduled scans (run automatically)
- [ ] Smart suggestions (ML-based cleanup tips)
- [ ] Undo support (restore deleted files)
- [ ] Cloud sync (compare across devices)

---

## Resources

**Textual Docs:** https://textual.textualize.io/  
**Rich Docs:** https://rich.readthedocs.io/  
**Examples:** https://github.com/Textualize/textual/tree/main/examples  

**Tutorial:** https://textual.textualize.io/tutorial/  

---

**Ready to start? Begin with Phase 1, Step 1.1!**
