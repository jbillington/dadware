# Dad Ware TUI Design

**Interactive Terminal UI for yourdad**

---

## Overview

Transform Dad Ware from a CLI tool into an interactive TUI (Terminal User Interface) that maintains the dad personality while adding real-time navigation, progress, and drill-down capabilities.

**Key Goal:** Make disk cleanup feel less like work and more like getting advice from a helpful (slightly snarky) dad.

---

## Technology Stack

### Recommended: `rich` + `textual`

**Why:**
- ✅ **Rich**: Beautiful terminal output, progress bars, tables, colors
- ✅ **Textual**: Full reactive TUI framework (widgets, events, layouts)
- ✅ **Pure Python**: No external binaries, works everywhere
- ✅ **Active development**: Modern, well-maintained
- ✅ **Great docs**: Easy to learn

**Install:**
```bash
pip install rich textual
```

**Alternatives considered:**
- `urwid` - older, less modern styling
- `prompt_toolkit` - more low-level, steeper learning curve
- `blessed` - minimal, would require more custom work

---

## TUI Flow

### 1. Launch Screen

```
┌─ Dad Ware v0.1 ────────────────────────────────────────────┐
│                                                             │
│   👔 Hey there! Ready to clean up this mess?               │
│                                                             │
│   What do you want to scan?                                │
│                                                             │
│   → Storage (Find large files and folders)                 │
│     CPU/RAM (See what's hogging memory)                    │
│     Both (The full checkup)                                │
│                                                             │
│   Recent Reports:                                          │
│   • Storage scan - 2 hours ago (Grade: C+)                 │
│   • CPU scan - Yesterday (12 memory hogs found)            │
│                                                             │
│   Press ? for help  |  Press q to quit                     │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Arrow keys to navigate options
- Enter to select
- Shows recent scans with quick access
- Dad personality in welcome message

---

### 2. Storage Scan Progress

```
┌─ Scanning Storage... ────────────────────────────────────────┐
│                                                               │
│   Volume: Macintosh HD (1TB total, 712GB used)               │
│                                                               │
│   🔍 Finding files and folders...                            │
│   ████████████████░░░░░░░░░░░░ 62%                          │
│                                                               │
│   📊 Found so far:                                           │
│   • 1,247,832 files scanned                                  │
│   • 523 folders over 1GB                                     │
│   • Largest file: 45GB (some_video.mov)                      │
│                                                               │
│   💬 "This is taking longer than expected...                 │
│       You got some hoarder tendencies going on here?"        │
│                                                               │
│   Press Esc to cancel                                        │
└───────────────────────────────────────────────────────────────┘
```

**Features:**
- Real-time progress bar
- Live stats update
- Dad commentary changes based on findings
- Cancel with Esc (graceful shutdown)

---

### 3. Storage Report Card

```
┌─ Storage Report Card ────────────────────────────────────────┐
│                                                               │
│   📊 Overall Grade: C+                                        │
│                                                               │
│   🟡 Free Space: 28% free (288GB / 1TB)         Grade: C     │
│   🟢 Home Folders: Well organized                Grade: A-    │
│   🔴 Downloads: 47GB of old files                Grade: D+    │
│   🟡 Desktop: 12GB of clutter                    Grade: C     │
│   🟢 Photos Library: 156GB (reasonable)          Grade: B+    │
│   🔴 Messages: 23GB (time to clean up!)          Grade: D     │
│                                                               │
│   💬 "Listen, 28% free space isn't terrible, but           │
│       you're one software update away from trouble.        │
│       Let's tackle that Downloads folder first."           │
│                                                               │
│   Navigation:                                                 │
│   → View Top Files (↓)                                        │
│     View Top Folders (→)                                      │
│     View Mac Libraries (→)                                    │
│     Back to Menu (Esc)                                        │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Features:**
- Color-coded grades (🟢🟡🔴)
- Overall grade with breakdown
- Dad commentary tailored to results
- Arrow key navigation to drill-down views

---

### 4. Top Files View

```
┌─ Top Files (by size) ─────────────────────────────────────────┐
│                                                                │
│   Total Reclaimable: 247GB (if you delete all these)          │
│                                                                │
│   Size    Type      Path                              Actions │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│   45.2GB  Video     /Users/dad/Movies/old_project.mov    [→]  │
│   32.1GB  Archive   /Users/dad/Downloads/backup.zip      [→]  │
│   18.5GB  App       /Applications/OldApp.app             [→]  │
│   12.3GB  Video     /Users/dad/Desktop/screencast.mov    [→]  │
│   9.8GB   Database  /Users/dad/Library/Cache/huge.db     [→]  │
│   ...                                                          │
│                                                                │
│   💬 "That 45GB video file? When's the last time you       │
│       opened it? 2019? Come on."                           │
│                                                                │
│   Press [→] to reveal in Finder  |  [s] to sort  |  [Esc] Back│
└────────────────────────────────────────────────────────────────┘
```

**Features:**
- Scrollable table (arrow keys)
- Press Enter/→ to open in Finder
- Sort by size/date/type (press `s` to cycle)
- Real-time filtering (press `/` to search)
- Copy path to clipboard (press `c`)
- Dad commentary updates based on file types

---

### 5. Folder Drill-Down

```
┌─ Downloads Folder Breakdown ──────────────────────────────────┐
│                                                                │
│   📁 /Users/dad/Downloads (47.2GB total)                       │
│                                                                │
│   Size    Last Modified  Name                          [Action]│
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│   15.2GB  2 years ago    old-backups/                   [→]   │
│   8.3GB   6 months ago   project-archives/              [→]   │
│   3.1GB   1 month ago    installers/                    [→]   │
│   2.5GB   3 weeks ago    screenshots/                   [→]   │
│   1.8GB   Yesterday      downloads.tmp                  [→]   │
│   ...                                                          │
│                                                                │
│   💬 "Old backups from 2 years ago? Either archive them    │
│       properly or let them go. This isn't a time capsule." │
│                                                                │
│   [→] View contents  |  [↑] Parent folder  |  [Esc] Back      │
└────────────────────────────────────────────────────────────────┘
```

**Features:**
- Hierarchical navigation (arrow keys)
- Press Enter to drill into folders
- Backspace/← to go up a level
- Shows last modified dates
- Dad commentary specific to folder type

---

### 6. CPU/RAM Report

```
┌─ CPU & Memory Report ─────────────────────────────────────────┐
│                                                                │
│   💻 Memory Status: 🟡 Under Pressure                         │
│                                                                │
│   Total RAM: 32GB                                             │
│   Used: 28.4GB (89%)                                          │
│   Free: 3.6GB (11%)                                           │
│                                                                │
│   📊 Memory Hogs:                                             │
│   App               Memory    CPU %   Windows                 │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│   Chrome            8.2GB     12%     [23 tabs]              │
│   Docker            4.1GB     3%      [5 containers]         │
│   Xcode             2.8GB     8%      [1 window]             │
│   Slack             1.2GB     2%      [4 workspaces]         │
│   Spotify           892MB     1%      [Playing]              │
│                                                                │
│   💬 "Chrome with 23 tabs? Classic. Close the ones you     │
│       opened 'just in case' three weeks ago."              │
│                                                                │
│   [k] Kill process  |  [r] Refresh  |  [Esc] Back            │
└────────────────────────────────────────────────────────────────┘
```

**Features:**
- Live refresh (auto-updates every 5s, or press `r`)
- Highlight processes over thresholds (500MB, 1GB)
- Press `k` to kill process (with confirmation)
- Shows browser tab counts
- Dad advice specific to app types

---

### 7. Help Screen

```
┌─ Dad Ware Help ───────────────────────────────────────────────┐
│                                                                │
│   Navigation:                                                  │
│   ↑↓←→   Move selection                                       │
│   Enter  Select / Drill down                                  │
│   Esc    Go back / Cancel                                     │
│   q      Quit                                                 │
│                                                                │
│   Actions:                                                     │
│   r      Refresh current view                                 │
│   s      Sort table                                           │
│   /      Search/filter                                        │
│   c      Copy path to clipboard                               │
│   k      Kill process (CPU view)                              │
│                                                                │
│   Reports:                                                     │
│   h      Export HTML report                                   │
│   j      Export JSON data                                     │
│   e      Export CSV (CPU data)                                │
│                                                                │
│   💬 "Need help? Just ask. That's what I'm here for."        │
│                                                                │
│   Press any key to return                                     │
└────────────────────────────────────────────────────────────────┘
```

---

## Dad Personality Integration

### Dynamic Commentary

Dad commentary should:
- **Change based on findings** (good grades = praise, bad grades = gentle roasting)
- **Be contextual** (different jokes for Downloads vs Desktop)
- **Rotate randomly** (multiple comments per scenario to avoid repetition)
- **Show during scans** (keep user entertained during long scans)

### Examples by Scenario

**Good grades:**
> "Look at you! Your home folders are actually organized. Did I teach you that?"

**Bad grades:**
> "47GB in Downloads? What are you running, a digital landfill?"

**During scan:**
> "Still scanning... You really do have a lot of stuff. No judgment. Well, maybe a little."

**Large file found:**
> "Found a 45GB video file from 2019. Either archive it or admit you're never watching it again."

**Chrome with many tabs:**
> "23 Chrome tabs? Let me guess—you're 'researching' something you'll forget about tomorrow."

**Low disk space:**
> "28% free space. You're living dangerously. One macOS update and you're toast."

---

## Technical Implementation

### Project Structure

```
dadware/
├── yourdad.py           # CLI entry point (existing)
├── tui/                 # NEW: TUI components
│   ├── __init__.py
│   ├── app.py          # Main Textual app
│   ├── screens/        # Screen components
│   │   ├── main_menu.py
│   │   ├── scan_progress.py
│   │   ├── report_card.py
│   │   ├── file_browser.py
│   │   ├── cpu_report.py
│   │   └── help.py
│   ├── widgets/        # Reusable widgets
│   │   ├── dad_comment.py
│   │   ├── grade_card.py
│   │   ├── file_table.py
│   │   └── progress_bar.py
│   └── styles.tcss     # Textual CSS styling
├── scanners/           # Existing scan logic
├── personality/        # Existing dad comments
└── renderers/          # Existing HTML/terminal renderers
```

### Core App Structure

```python
# tui/app.py
from textual.app import App
from tui.screens.main_menu import MainMenuScreen

class DadWareApp(App):
    """Dad Ware TUI Application"""
    
    CSS_PATH = "styles.tcss"
    
    def on_mount(self):
        """Show main menu on startup"""
        self.push_screen(MainMenuScreen())
    
    def action_quit(self):
        """Quit the app"""
        self.exit()
```

### Launch Command

```python
# yourdad.py - add new command
def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    
    # Existing: scan, export
    # NEW:
    tui_parser = subparsers.add_parser('tui', help='Launch interactive TUI')
    
    args = parser.parse_args()
    
    if args.command == 'tui':
        from tui.app import DadWareApp
        app = DadWareApp()
        app.run()
```

**Usage:**
```bash
./yourdad tui
```

---

## Development Phases

### Phase 1: Basic TUI (MVP) - 4-6 hours

**Goals:**
- Main menu screen
- Launch storage scan
- Show scan progress
- Display basic report card
- Navigate back to menu

**Deliverables:**
- `tui/app.py` - Main app
- `tui/screens/main_menu.py` - Main menu
- `tui/screens/scan_progress.py` - Progress screen
- `tui/screens/report_card.py` - Report card view

### Phase 2: File Browser - 3-4 hours

**Goals:**
- Top files table (scrollable)
- Top folders table
- Drill-down into folders
- Open in Finder action

**Deliverables:**
- `tui/screens/file_browser.py`
- `tui/widgets/file_table.py`

### Phase 3: CPU Report - 2-3 hours

**Goals:**
- Memory hogs table
- Auto-refresh
- Kill process action

**Deliverables:**
- `tui/screens/cpu_report.py`
- Real-time refresh logic

### Phase 4: Polish - 2-3 hours

**Goals:**
- Help screen
- Export actions (HTML/JSON/CSV)
- Search/filter functionality
- Keyboard shortcuts overlay
- Error handling

**Deliverables:**
- `tui/screens/help.py`
- Export integration
- Search widget

---

## User Stories

**1. Dad needs to free up space quickly**
- Launches TUI
- Runs storage scan
- Sees Downloads has 47GB
- Drills into Downloads folder
- Opens old-backups/ in Finder
- Deletes manually
- Re-runs scan to see new grade

**2. Dad's Mac is slow**
- Launches TUI
- Runs CPU scan
- Sees Chrome using 8GB with 23 tabs
- Closes Chrome tabs manually
- Presses 'r' to refresh
- Sees memory drop to 4GB

**3. Dad wants to show results to family**
- Runs storage scan in TUI
- Presses 'h' to export HTML report
- HTML report opens in browser
- Shares link with family

---

## Testing Plan

### Manual Testing

**Main Menu:**
- [ ] Arrow keys navigate options
- [ ] Enter selects option
- [ ] Recent reports show correctly
- [ ] 'q' quits gracefully

**Storage Scan:**
- [ ] Progress bar updates in real-time
- [ ] Stats update as scan progresses
- [ ] Dad comments appear
- [ ] Esc cancels scan
- [ ] Report card shows after completion

**File Browser:**
- [ ] Table scrolls with arrow keys
- [ ] Enter/→ opens in Finder
- [ ] Sorting works (by size/date/type)
- [ ] Search filters results
- [ ] Copy path works

**CPU Report:**
- [ ] Auto-refresh updates every 5s
- [ ] Manual refresh (r) works
- [ ] Kill process works with confirmation
- [ ] Memory pressure indicator correct

### Edge Cases

- [ ] No recent reports (first run)
- [ ] Scan cancelled mid-way
- [ ] Permission denied for protected folders
- [ ] Very large directories (1M+ files)
- [ ] Terminal resize during scan
- [ ] Kill app during scan (graceful shutdown)

---

## Design Decisions

### Why Textual over alternatives?

**Pros:**
- Modern, reactive framework (like React for terminals)
- Built-in widgets (tables, progress bars, inputs)
- CSS-like styling
- Excellent docs and examples
- Active development (backed by Will McGugan, creator of Rich)

**Cons:**
- Slightly heavier dependency
- Newer (less battle-tested than urwid)

**Verdict:** Textual's modern design and built-in widgets will save development time and result in a more polished UI.

### Why TUI instead of GUI?

**Reasons:**
1. **Stays in terminal** - Aligns with power user audience
2. **Lightweight** - No Electron/WebView overhead
3. **SSH-friendly** - Can run remotely
4. **Fast** - No browser rendering lag
5. **Dad Ware brand** - Terminal tools feel "dad-like"

---

## Open Questions

1. **Should we keep CLI commands?**
   - **Yes** - TUI is additive, not replacement
   - CLI useful for scripting and automation

2. **Auto-launch TUI by default?**
   - **No** - Keep CLI as default for backward compatibility
   - Add `--tui` flag: `./yourdad scan storage --tui`

3. **Persist TUI state between runs?**
   - **Yes** - Save last scan results
   - Load immediately on launch for instant feedback

4. **Allow in-TUI deletions?**
   - **No** - Stay read-only
   - Open in Finder for user to decide

---

## Future Enhancements

### Phase 5+ (Post-MVP)

- **Themes** - Light/dark mode, color customization
- **Graphs** - Visual charts for disk usage over time
- **Notifications** - Desktop notifications when scan completes
- **Scheduled scans** - Run scans automatically, view in TUI
- **Comparison view** - Compare two scans side-by-side
- **Dad voice** - Text-to-speech for dad comments (easter egg?)

---

## Conclusion

A TUI transforms Dad Ware from a one-shot CLI tool into an interactive experience. Users can explore their disk usage like browsing files, with dad humor keeping it light.

**Key Benefits:**
- ✅ Faster workflow (no re-running scans)
- ✅ More discoverable (easier to explore results)
- ✅ More engaging (dad personality shines)
- ✅ More polished (modern terminal UI)

**Next Steps:**
1. Install dependencies: `pip install rich textual`
2. Build Phase 1 MVP (main menu + scan progress)
3. Test with real users
4. Iterate based on feedback

---

**Made with ❤️ by a dad who's tired of staring at HTML reports**
