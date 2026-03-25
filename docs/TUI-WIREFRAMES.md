# Dad Ware TUI - ASCII Wireframes

**Visual mockups of the TUI screens**

---

## Screen Flow Diagram

```
                    ┌─────────────┐
                    │ Launch      │
                    │ Screen      │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │Storage  │  │  CPU    │  │  Both   │
        │ Scan    │  │  Scan   │  │  Scans  │
        └────┬────┘  └────┬────┘  └────┬────┘
             │            │            │
             ▼            ▼            │
        ┌─────────┐  ┌─────────┐     │
        │Storage  │  │  CPU    │     │
        │Progress │  │Progress │     │
        └────┬────┘  └────┬────┘     │
             │            │            │
             ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │Storage  │  │  CPU    │  │ Both    │
        │ Report  │  │ Report  │  │ Reports │
        └────┬────┘  └────┬────┘  └────┬────┘
             │            │            │
     ┌───────┼────────────┼────────────┼───────┐
     │       │            │            │       │
     ▼       ▼            ▼            ▼       ▼
  ┌──────┐┌──────┐    ┌──────┐    ┌──────┐┌──────┐
  │ Files││Folder│    │Memory│    │Export││ Help │
  │ Table││ Tree │    │ Hogs │    │      ││      │
  └──────┘└──────┘    └──────┘    └──────┘└──────┘
```

---

## 1. Main Menu (Launch Screen)

```
╔═══════════════════════════════════════════════════════════════════════╗
║                         Dad Ware v0.1-poc                             ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  👔 Hey there! Ready to see what's eating up your disk space?        ║
║                                                                       ║
║  ┌─────────────────────────────────────────────────────────────────┐ ║
║  │ ▶ Storage Scan                                                  │ ║
║  │   Find large files and folders hogging your disk                │ ║
║  ├─────────────────────────────────────────────────────────────────┤ ║
║  │   CPU & Memory Scan                                             │ ║
║  │   See what's hogging your RAM right now                         │ ║
║  ├─────────────────────────────────────────────────────────────────┤ ║
║  │   Both Scans                                                    │ ║
║  │   The full checkup (recommended)                                │ ║
║  └─────────────────────────────────────────────────────────────────┘ ║
║                                                                       ║
║  📁 Recent Reports:                                                   ║
║  ┌─────────────────────────────────────────────────────────────────┐ ║
║  │ • Storage - 2 hours ago               Grade: C+ (28% free)      │ ║
║  │ • CPU/RAM - Yesterday                 Chrome: 8.2GB (12 tabs)   │ ║
║  │ • Storage - 3 days ago                Grade: D+ (18% free)      │ ║
║  └─────────────────────────────────────────────────────────────────┘ ║
║                                                                       ║
║  💡 Tip: Press h for help, q to quit                                 ║
╚═══════════════════════════════════════════════════════════════════════╝
  ↑↓ Navigate   Enter Select   ? Help   q Quit
```

**Key Features:**
- Selected item highlighted (▶ indicator)
- Recent reports clickable (shows cached results)
- Dad welcome message at top
- Status bar at bottom

---

## 2. Storage Scan Progress

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    Scanning Storage - Macintosh HD                    ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  🔍 Analyzing files and folders...                                    ║
║                                                                       ║
║  ┌─ Progress ────────────────────────────────────────────────────────┤
║  │ ███████████████████████████████░░░░░░░░░░░░░░░░░░░░░░  62%       │
║  └────────────────────────────────────────────────────────────────────┤
║                                                                       ║
║  📊 Current Stats:                                                    ║
║  ┌────────────────────────────────────────────────────────────────┐  ║
║  │ Files scanned:        1,247,832                                │  ║
║  │ Folders analyzed:     87,423                                   │  ║
║  │ Large folders (>1GB): 523                                      │  ║
║  │ Largest file found:   45.2GB (some_old_video.mov)             │  ║
║  │ Time elapsed:         2m 14s                                   │  ║
║  └────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
║  💬 Dad says:                                                         ║
║  ┌────────────────────────────────────────────────────────────────┐  ║
║  │ "This is taking longer than expected... You got some hoarder   │  ║
║  │  tendencies going on here? Don't worry, we'll sort it out."    │  ║
║  └────────────────────────────────────────────────────────────────┘  ║
║                                                                       ║
║  ⚙️  Scanning: /Users/dad/Library/Application Support/...            ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
  Esc Cancel scan   (Will save partial results)
```

**Key Features:**
- Animated progress bar (fills left to right)
- Live stats update every 0.5s
- Current path being scanned
- Dad commentary rotates during scan
- Esc gracefully cancels

---

## 3. Storage Report Card

```
╔═══════════════════════════════════════════════════════════════════════╗
║                         Storage Report Card                           ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  📊 Overall Grade: C+                                                 ║
║  ═══════════════════════════════════════════════════════════════════  ║
║                                                                       ║
║  Volume: Macintosh HD  │  1TB total  │  712GB used (71%)            ║
║                                                                       ║
║  ┌─ Grades ──────────────────────────────────────────────────────────┤
║  │                                                                   │
║  │  🟡 Free Space               28% free (288GB)         Grade: C   │
║  │     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░            │
║  │                                                                   │
║  │  🟢 Home Folders             124GB / well organized   Grade: A-  │
║  │     ▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░            │
║  │                                                                   │
║  │  🔴 Downloads Folder         47GB / needs cleanup     Grade: D+  │
║  │     ▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░            │
║  │                                                                   │
║  │  🟡 Desktop                  12GB / cluttered         Grade: C   │
║  │     ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░            │
║  │                                                                   │
║  │  🟢 Photos Library           156GB / reasonable       Grade: B+  │
║  │     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░            │
║  │                                                                   │
║  │  🔴 Messages                 23GB / time to clean!    Grade: D   │
║  │     ▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░            │
║  │                                                                   │
║  └───────────────────────────────────────────────────────────────────┤
║                                                                       ║
║  💬 Dad's Advice:                                                     ║
║  ┌───────────────────────────────────────────────────────────────┐   ║
║  │ "Listen, 28% free space isn't terrible, but you're one       │   ║
║  │  software update away from trouble. Let's tackle that         │   ║
║  │  Downloads folder first—47GB of digital packrat syndrome."    │   ║
║  └───────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
║  ┌─ Actions ─────────────────────────────────────────────────────────┤
║  │ → View Top Files                                                 │
║  │   View Top Folders                                               │
║  │   View Mac App Libraries                                         │
║  │   Export HTML Report                                             │
║  │   ← Back to Main Menu                                            │
║  └──────────────────────────────────────────────────────────────────┤
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
  ↑↓ Navigate   Enter Select   h Export HTML   r Refresh   Esc Back
```

**Key Features:**
- Color-coded grades (🟢 A-B, 🟡 C, 🔴 D-F)
- Horizontal bars show size relative to total
- Dad advice tailored to worst grades
- Action menu at bottom

---

## 4. Top Files Browser

```
╔═══════════════════════════════════════════════════════════════════════╗
║                  Top Files (sorted by size)                           ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  💾 Total Reclaimable Space: 247GB (if you delete all these)         ║
║                                                                       ║
║  ┌─────────────────────────────────────────────────────────────────┐ ║
║  │ Size    Type      Path                                     [Act] │ ║
║  │ ─────────────────────────────────────────────────────────────── │ ║
║  │ 45.2GB  Video     /Users/dad/Movies/old_project.mov         [→] │ ║ ← Selected
║  │ 32.1GB  Archive   /Users/dad/Downloads/backup_2019.zip      [ ] │ ║
║  │ 18.5GB  App       /Applications/OldApp.app                   [ ] │ ║
║  │ 12.3GB  Video     /Users/dad/Desktop/screencast.mov          [ ] │ ║
║  │ 9.8GB   Database  /Users/dad/Library/Caches/huge.db          [ ] │ ║
║  │ 8.2GB   Video     /Users/dad/Movies/vacation_2018.mov        [ ] │ ║
║  │ 7.1GB   Archive   /Users/dad/Downloads/installer.dmg         [ ] │ ║
║  │ 5.4GB   Video     /Users/dad/Desktop/meeting_recording.mov   [ ] │ ║
║  │ 4.9GB   Database  /Users/dad/Library/Mail/V10/MailData/...   [ ] │ ║
║  │ 3.2GB   Video     /Users/dad/Movies/tutorial.mp4             [ ] │ ║
║  │                                                                   │ ║
║  │ ... 1,247,832 more files (showing top 100)                       │ ║
║  └─────────────────────────────────────────────────────────────────┘ ║
║                                                                       ║
║  💬 Dad says:                                                         ║
║  ┌───────────────────────────────────────────────────────────────┐   ║
║  │ "That 45GB video from 2019? When's the last time you opened   │   ║
║  │  it? Be honest. Either move it to external storage or let go."│   ║
║  └───────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
║  🔍 Filter: _____________ (press / to search)                         ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
  ↑↓ Navigate   Enter/→ Reveal in Finder   s Sort   / Search   c Copy path   Esc Back
```

**Key Features:**
- Scrollable table (Page Up/Down supported)
- Selected row highlighted (inverted colors)
- Enter/→ opens Finder to file location
- Press `/` activates search filter
- Press `s` cycles sort: size→date→type→name
- Press `c` copies full path to clipboard

---

## 5. Folder Drill-Down

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    Folder: Downloads (47.2GB)                         ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  📂 /Users/dad/Downloads                                              ║
║  🔗 Parent: /Users/dad (124GB total)                                  ║
║                                                                       ║
║  ┌─────────────────────────────────────────────────────────────────┐ ║
║  │ Size    Modified      Name                                  [Act]│ ║
║  │ ─────────────────────────────────────────────────────────────── │ ║
║  │ 15.2GB  2 years ago   old-backups/                            [→]│ ║ ← Selected
║  │  8.3GB  6 months ago  project-archives/                       [ ]│ ║
║  │  3.1GB  1 month ago   installers/                             [ ]│ ║
║  │  2.5GB  3 weeks ago   screenshots/                            [ ]│ ║
║  │  1.8GB  Yesterday     downloads_tmp/                          [ ]│ ║
║  │  892MB  2 days ago    pdfs/                                   [ ]│ ║
║  │  654MB  Last week     random_files/                           [ ]│ ║
║  │  234MB  Yesterday     work_stuff/                             [ ]│ ║
║  │  128MB  Today         quick_downloads/                        [ ]│ ║
║  │   89MB  3 hours ago   temp/                                   [ ]│ ║
║  │                                                                   │ ║
║  │ ... 453 more items in this folder                                │ ║
║  └─────────────────────────────────────────────────────────────────┘ ║
║                                                                       ║
║  💬 Dad says:                                                         ║
║  ┌───────────────────────────────────────────────────────────────┐   ║
║  │ "Old backups from 2 years ago? Either archive them properly   │   ║
║  │  to external storage or admit they're not that important."     │   ║
║  └───────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
  ↑↓ Navigate   Enter/→ Drill into folder   ← Parent folder   Esc Back to report
```

**Key Features:**
- Breadcrumb path at top
- Folders have trailing `/`
- Enter drills into selected folder
- `←` or Backspace goes up one level
- Shows last modified date
- Dad comments specific to folder contents

---

## 6. CPU & Memory Report

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    CPU & Memory Report                                ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  💻 Memory Status: 🟡 Under Pressure                                  ║
║  ════════════════════════════════════════════════════════════════     ║
║                                                                       ║
║  Total RAM:    32.0GB                                                ║
║  Used:         28.4GB  (89%)  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░ ║
║  Free:          3.6GB  (11%)  ░                                      ║
║  Cached:        8.2GB  (26%)                                         ║
║                                                                       ║
║  📊 Process Overview:                                                 ║
║  • Total processes:        387                                       ║
║  • Over 100MB:            48 processes                               ║
║  • Over 500MB:            12 processes                               ║
║  • Over 1GB:               5 processes                               ║
║                                                                       ║
║  ┌─ Top Memory Hogs ─────────────────────────────────────────────────┤
║  │ App           Memory   CPU%  Processes  Windows/Tabs         [Act]│ ║
║  │ ───────────────────────────────────────────────────────────────  │ ║
║  │ Chrome        8.2GB    12%   23         [23 tabs, 6 extensions] [k]│ ║ ← Selected
║  │ Docker        4.1GB     3%    5         [5 containers running] [ ]│ ║
║  │ Xcode         2.8GB     8%    1         [1 project open]       [ ]│ ║
║  │ Slack         1.2GB     2%    1         [4 workspaces]         [ ]│ ║
║  │ Spotify       892MB     1%    1         [Playing music]        [ ]│ ║
║  │ Firefox       654MB     4%    8         [12 tabs]              [ ]│ ║
║  │ iTerm2        543MB     1%    3         [4 terminals]          [ ]│ ║
║  │ Mail          412MB     0%    1         [Syncing]              [ ]│ ║
║  │ Messages      287MB     0%    1         [Background]           [ ]│ ║
║  │ Finder        189MB     0%    1         [6 windows]            [ ]│ ║
║  │                                                                   │ ║
║  │ ... 377 more processes (showing top 10)                          │ ║
║  └───────────────────────────────────────────────────────────────────┤
║                                                                       ║
║  💬 Dad says:                                                         ║
║  ┌───────────────────────────────────────────────────────────────┐   ║
║  │ "Chrome with 23 tabs? Classic. Close the ones you opened      │   ║
║  │  'just in case' three weeks ago. They're not coming back."     │   ║
║  └───────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
║  🔄 Auto-refresh: ON (every 5s)  │  Last updated: 2 seconds ago      ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
  ↑↓ Navigate   k Kill process   r Refresh now   a Toggle auto-refresh   Esc Back
```

**Key Features:**
- Live memory pressure indicator
- Memory bar visualization
- Process counts by size threshold
- Grouped by application (not individual processes)
- Shows browser tab counts
- Auto-refresh every 5s (toggle with `a`)
- Kill process with confirmation (press `k`)

---

## 7. Help Screen

```
╔═══════════════════════════════════════════════════════════════════════╗
║                              Dad Ware Help                            ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  ⌨️  Navigation:                                                       ║
║  ┌───────────────────────────────────────────────────────────────┐   ║
║  │  ↑↓←→        Move selection / Navigate                        │   ║
║  │  Enter       Select option / Drill down                        │   ║
║  │  Esc         Go back / Cancel                                  │   ║
║  │  q           Quit application                                  │   ║
║  │  h or ?      Show this help screen                             │   ║
║  └───────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
║  📊 File Browser Actions:                                             ║
║  ┌───────────────────────────────────────────────────────────────┐   ║
║  │  Enter / →   Reveal in Finder / Drill into folder             │   ║
║  │  ←           Go to parent folder                               │   ║
║  │  s           Cycle sort (size→date→type→name)                  │   ║
║  │  /           Activate search/filter                            │   ║
║  │  c           Copy path to clipboard                            │   ║
║  └───────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
║  💻 CPU Report Actions:                                               ║
║  ┌───────────────────────────────────────────────────────────────┐   ║
║  │  k           Kill selected process (with confirmation)         │   ║
║  │  r           Refresh now (manual refresh)                      │   ║
║  │  a           Toggle auto-refresh on/off                        │   ║
║  └───────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
║  📄 Export Options:                                                   ║
║  ┌───────────────────────────────────────────────────────────────┐   ║
║  │  h           Export current view as HTML                       │   ║
║  │  j           Export raw data as JSON                           │   ║
║  │  e           Export CPU data as CSV (CPU view only)            │   ║
║  └───────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
║  💬 Dad says:                                                         ║
║  ┌───────────────────────────────────────────────────────────────┐   ║
║  │ "Need more help? Just ask. That's what I'm here for.          │   ║
║  │  Now go clean up that Downloads folder."                       │   ║
║  └───────────────────────────────────────────────────────────────┘   ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
  Press any key to return
```

**Key Features:**
- Comprehensive keyboard shortcuts
- Grouped by context (navigation, files, CPU, export)
- Dad humor even in help screen
- Any key returns to previous screen

---

## Component Interaction Examples

### Example 1: Drill-Down Flow

```
Report Card
    │
    └→ View Top Folders
        │
        └→ Select "Downloads (47GB)"
            │
            └→ Drill into folder
                │
                ├→ Select "old-backups/ (15GB)"
                │   │
                │   └→ Press → to reveal in Finder
                │       │
                │       └→ Finder opens to /Users/dad/Downloads/old-backups/
                │
                └→ Press Esc to go back to Downloads
                    │
                    └→ Press Esc again to return to Report Card
```

### Example 2: Kill Process Flow

```
CPU Report
    │
    └→ Select "Chrome (8.2GB)"
        │
        └→ Press 'k' to kill
            │
            └→ Confirmation modal:
                ┌────────────────────────────────────────────┐
                │  ⚠️  Kill Chrome?                          │
                │                                            │
                │  This will close all 23 tabs.              │
                │  Make sure you've saved your work!         │
                │                                            │
                │  [Yes, kill it]  [Cancel]                  │
                └────────────────────────────────────────────┘
                    │
                    ├→ Yes → Chrome killed → Table updates
                    │
                    └→ Cancel → Return to CPU Report
```

---

## Color Scheme

### Light Mode (Default)
- Background: White (#FFFFFF)
- Text: Dark Gray (#2C2C2C)
- Selected: Blue highlight (#0066CC)
- Grades: 🟢 Green (#10B981), 🟡 Yellow (#F59E0B), 🔴 Red (#EF4444)
- Progress bars: Blue gradient (#0066CC → #00AAFF)

### Dark Mode (Optional)
- Background: Dark Gray (#1E1E1E)
- Text: Light Gray (#E0E0E0)
- Selected: Blue highlight (#0088FF)
- Grades: 🟢 Green (#34D399), 🟡 Yellow (#FBBF24), 🔴 Red (#F87171)
- Progress bars: Blue gradient (#0088FF → #00CCFF)

---

## Responsive Design Notes

### Minimum Terminal Size
- **Width:** 80 columns
- **Height:** 24 rows

If terminal is smaller:
```
╔═══════════════════════════════════════════╗
║  ⚠️  Terminal Too Small                  ║
╠═══════════════════════════════════════════╣
║                                           ║
║  Please resize your terminal to at       ║
║  least 80x24 to use Dad Ware TUI.        ║
║                                           ║
║  Current size: 72x20                     ║
║  Required:     80x24                     ║
║                                           ║
║  💬 "Come on, give me some elbow room!"  ║
║                                           ║
╚═══════════════════════════════════════════╝
```

### Large Terminal Optimization
- Tables expand to fill width
- More rows shown in file lists
- Dad comments can be multi-line

---

**Made with ❤️ by a dad who draws boxes in text files**
