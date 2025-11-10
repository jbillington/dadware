# Dad Ware / `yourdad` — Product Requirements Document

**Version:** 0.1
**Owner:** John Billington
**Date:** November 2025
**Status:** Pre-development

---

## 1) Vision

A **personality-driven Mac cleanup tool** that makes system maintenance fun and approachable for non-technical users (teens, young adults, women, anyone intimidated by terminal tools).

**Why it exists:**
- Existing tools are expensive, scammy, or boring
- Terminal apps are cool again
- People need help but don't want to learn technical jargon
- No one wants software making destructive decisions for them

**Core principle:** *Read-only scanning + personality-driven guidance + user control = safe, fun cleanup.*

---

## 2) Target Users

| Persona | Need | Pain Point |
|---------|------|------------|
| **College student** | "My Mac says I'm out of space" | Doesn't know where to start, scared to delete wrong thing |
| **Creative professional** | "My computer is slow and cluttered" | Too busy to dig through folders manually |
| **Non-technical family member** | "I keep getting storage warnings" | Existing tools are confusing or cost $40 |
| **Power user** | "I want a quick audit" | Tired of manually running `du` and `top` |

---

## 3) Core Outcomes

| User Problem | Dad Ware Solution |
|--------------|-------------------|
| "Where did my storage go?" | Clear breakdown of largest folders/files with sizes |
| "What's slowing my computer?" | CPU/RAM snapshot showing resource hogs |
| "I'm scared to delete the wrong thing" | Read-only tool, user reviews before deleting anything |
| "Terminal tools are intimidating" | Friendly dad personality makes it approachable |
| "Reports are boring" | Dad's Report Card - witty, data-aware commentary |

---

## 4) Features (v0.1)

### 4.1 Storage Analysis
- **Scan volumes** - List all mounted drives, let user pick (default: home directory)
- **Large files detection** - Find top 500 largest files by default
- **Folder size analysis** - Show which folders consume most space (depth=2 default)
- **Smart exclusions** - Skip system folders (`/System`, `/Library`), app bundles, iCloud placeholders, caches
- **Safe scanning** - Handle permission errors gracefully, never require sudo

### 4.2 Performance Analysis
- **CPU snapshot** - Top 5 processes by CPU usage
- **RAM snapshot** - Memory pressure and top consumers
- **Process insights** - Dad comments on common culprits (Chrome, photoanalysisd, etc.)

### 4.3 Reporting (Dual Format)
- **HTML report (default)** - Beautiful, sortable tables with file:// links to originals
- **Terminal report** - "Dad's Report Card" with ANSI colors and dad personality
- **Export options** - Save reports with timestamp for tracking over time

### 4.4 Personality Engine
- **Data-aware comments** - Dad voice responds to actual findings (e.g., "Downloads folder looks like a garage shelf")
- **Helpful tips** - Actionable next steps, never condescending
- **Short & dry** - Max 2 lines per section, no word bloat

### 4.5 User Actions
- **Reveal in Finder** - HTML report includes clickable file:// links
- **Terminal commands** - Copy-paste `open -R` commands to reveal files
- **Manual deletion** - User controls what gets deleted (send to Trash themselves)
- **Review workflow** - Reports clearly highlight candidates, user decides

---

## 5) Command Structure

```bash
# Main command
$ yourdad

# Volume selection & storage scan
$ yourdad scan storage           # prompts for volume, scans with defaults
$ yourdad scan storage --volume /Volumes/External
$ yourdad scan storage --top 1000 --min-size 500MB
$ yourdad scan storage --terminal  # terminal report only (no HTML)

# Performance scan
$ yourdad scan cpu               # CPU + RAM snapshot

# Quick troubleshoot (runs storage + cpu)
$ yourdad scan quick             # fast storage scan + cpu

# Utility commands
$ yourdad --version
$ yourdad --help
```

**Default behavior:** HTML report generated and opened in browser automatically. Add `--terminal` to suppress HTML.

---

## 6) User Flows

### 6.1 First Run

1. User runs `yourdad scan storage`
2. Tool detects macOS version, checks permissions
3. Lists available volumes:
   ```
   ────────────────────────────────
    Dad Ware  |  yourdad v0.1
   ────────────────────────────────

   Available volumes:
   1) Macintosh HD (/) - 500 GB, 387 GB used
   2) External Backup (/Volumes/Backup) - 2 TB, 1.1 TB used
   3) Home directory only (~/) - quickest

   Pick one (3 is fastest):
   ```
4. User selects option (default = 3)
5. Scanning progress with dad comments:
   ```
   Scanning storage...
   → digging through the attic (home folder)
   → found 3,214 items so far
   → Downloads folder... yep, it's a mess
   ```
6. Generates reports:
   - Opens HTML in browser automatically
   - Displays terminal summary with personality
7. Returns to prompt

### 6.2 Storage Scan Output (Terminal)

```
────────────────────────────────────────
 DAD'S REPORT CARD — Dad Ware v0.1
 MacBook-Pro  |  User: John
 Date: November 9, 2025
────────────────────────────────────────

📦 STORAGE SCAN — /Users/john

Top Folders (depth 2):
  Movies/                    47.2 GB
  Library/Application Support 23.8 GB
  Downloads/                 18.5 GB
  Documents/                  7.1 GB
  Desktop/                    4.3 GB

Top 10 Largest Files:
  Final_Cut_Project.zip       8.4 GB
  2022_backup.dmg             5.1 GB
  OldWorkVideos.mov           3.2 GB
  ...

Total: 500 GB  |  Used: 387 GB (77%)  |  Free: 113 GB

💬 Dad says: "downloads looks like a garage shelf.
   time to label a box."

Status: 🟡 stable but cluttered

────────────────────────────────────────
💡 Quick Wins:
  • Start with ~/Downloads (18.5 GB)
  • Review old backups (2022_backup.dmg)
  • Check ~/Movies for archived projects

📊 Full report: file:///Users/john/.dadware/reports/storage_2025-11-09_14-23.html
   (opened in browser)
────────────────────────────────────────
```

### 6.3 HTML Report Structure

**Layout:**
- Header: "Dad's Report Card" with Dad Ware branding + scan metadata
- Dad's commentary section at top
- Sortable table with columns:
  - Path (clickable file:// link)
  - Size (human readable, sortable)
  - Modified date
  - Actions (Reveal in Finder button)
- Summary footer with total reclaimable space
- Clear instructions: "Delete files manually from Finder. Trash = safe undo."

**Features:**
- Client-side sorting (no server required)
- Filter by size threshold
- Copy "Reveal in Finder" command
- Works offline (embedded CSS, zero dependencies)

---

## 7) Architecture (Extensible for New Scans)

```
┌──────────────────────────────┐
│ CLI Entry Point              │  → argparse, subcommands
│  yourdad.py                  │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ Orchestrator                 │  → routes commands, collects results
│  • handles volume selection  │
│  • runs appropriate scanner  │
│  • passes to report gen      │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ Scanners (modular)           │  → each scan = separate module
│  scanners/                   │
│    storage.py                │  → large files, folder sizes
│    cpu.py                    │  → process monitoring
│    duplicates.py             │  → (future) hash-based dupes
│    battery.py                │  → (future) battery health
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ Analysis Engine              │  → interpret scan results
│  • applies thresholds        │
│  • tags ok/warn/critical     │
│  • generates insights        │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ Personality Engine           │  → dad voice layer
│  personality/                │
│    yourdad.py                │  → data-aware comment rules
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ Report Generators            │  → output formatting
│  renderers/                  │
│    terminal.py               │  → ANSI colored terminal
│    html.py                   │  → HTML with embedded CSS
└──────────────────────────────┘
```

**Key Design Principle:**
Adding a new scan type (e.g., `network.py`, `duplicates.py`) should NOT require touching the orchestrator or report generators. Each scanner returns standard format:

```python
{
  "scan_type": "storage",
  "status": "warn",  # ok | warn | critical
  "data": {...},     # scan-specific results
  "metadata": {
    "scanned_at": "2025-11-09T14:23:00Z",
    "volume": "/Users/john",
    "duration_seconds": 18.3
  }
}
```

---

## 8) Data Models

### 8.1 Scan Result (Standard Format)

```json
{
  "scan_type": "storage",
  "status": "warn",
  "data": {
    "top_folders": [
      {"path": "~/Movies", "size_bytes": 50653265920, "size_human": "47.2 GB"}
    ],
    "top_files": [
      {"path": "~/Movies/big.mov", "size_bytes": 9021562880, "mtime": "2025-08-02T16:10:03Z"}
    ],
    "volume_info": {
      "total_bytes": 536870912000,
      "used_bytes": 415560596480,
      "free_bytes": 121310315520,
      "used_percent": 77
    }
  },
  "tips": [
    "Start with ~/Downloads (18.5 GB)",
    "Review old backups"
  ],
  "metadata": {
    "scanned_at": "2025-11-09T14:23:00Z",
    "volume": "/Users/john",
    "duration_seconds": 18.3
  }
}
```

### 8.2 Report Manifest

```json
{
  "report_id": "storage_2025-11-09_14-23",
  "generated_at": "2025-11-09T14:23:42Z",
  "scan_results": {
    "storage": { /* full scan result */ },
    "cpu": { /* if included */ }
  },
  "personality_comments": [
    {"section": "storage", "comment": "downloads looks like a garage shelf..."}
  ],
  "report_files": {
    "html": "/Users/john/.dadware/reports/storage_2025-11-09_14-23.html",
    "terminal": "/Users/john/.dadware/reports/storage_2025-11-09_14-23.txt"
  }
}
```

---

## 9) Personality Rules (Dad Voice)

### 9.1 Tone Guidelines
- **Dry and witty**, never try-hard
- **Helpful, not condescending** - assumes user is capable
- **Data-aware** - comments react to actual findings
- **Short** - max 2 sentences per section
- **Relatable** - uses metaphors (garage, attic, junk drawer)

### 9.2 Example Rules

```python
# Downloads folder
if downloads_size > 10_GB:
    "downloads looks like a garage shelf. time to label a box."
elif downloads_size > 5_GB:
    "downloads is getting crowded. regular cleanup day?"

# CPU usage
if chrome_cpu > 50:
    "lots of tabs. lots of fans. cause ↔ effect."
if photoanalysisd_running:
    "photoanalysisd is doing its thing. mac's version of 'I'm organizing.'"

# Low storage
if free_space_percent < 10:
    "living on the edge. let's back away from the cliff."

# Desktop clutter
if desktop_size > 5_GB:
    "desktop isn't meant to be storage. it's a desk, not a storage unit."

# Good state
if status == "ok":
    "looks fine. don't mess with success."
```

---

## 10) Smart Exclusions (Safety First)

### 10.1 Always Skip (Never Scan)
- `/System` - macOS system files
- `/Library` - system libraries
- `/Applications` - app bundles
- `/usr`, `/bin`, `/sbin` - Unix directories
- `*.app/` - application packages
- `*.photoslibrary/` - Photos libraries
- `~/Library/Mail/` - Mail data
- `*/Library/Caches/*` - cache directories
- `*/tmp/*` - temporary files
- Hidden files starting with `.` (unless `--show-hidden`)

### 10.2 iCloud Handling
- **Detect cloud-only files** - skip placeholders that aren't downloaded
- **Show in report** - mark with cloud icon so user knows
- **Don't trigger downloads** - prevents surprise bandwidth usage

### 10.3 Permission Handling
- **Never require sudo** - scan only what user can access
- **Gracefully skip restricted** - note in report if areas were inaccessible
- **Suggest Full Disk Access** - if many areas blocked, provide instructions

---

## 11) Functional Requirements

| ID | Feature | Details |
|----|---------|---------|
| F-1 | Volume selection | List mounted volumes, let user pick or default to home |
| F-2 | Large files scan | Top N files (default 500), configurable min size |
| F-3 | Folder size analysis | Recursive depth (default 2), show top folders |
| F-4 | CPU snapshot | Top 5 processes by CPU%, memory usage |
| F-5 | Smart exclusions | Skip system folders, app bundles, iCloud placeholders |
| F-6 | Terminal report | Dad's Report Card with ANSI colors, dad personality |
| F-7 | HTML report | Sortable table, file:// links, Reveal in Finder buttons |
| F-8 | Report storage | Save to `~/.dadware/reports/` with timestamp |
| F-9 | Personality engine | Data-aware dad comments, max 2 lines per section |
| F-10 | Safety | Read-only, no destructive actions, manual user deletion |

---

## 12) Non-Functional Requirements

- **Performance:** Storage scan ≤ 30 seconds for typical 200GB home directory
- **Compatibility:** macOS 12+ (Monterey or later)
- **Dependencies:** Python 3.9+ stdlib, optional: `colorama`, `humanize`
- **Privacy:** No network access, no telemetry, all data stays local
- **Accessibility:** Support `--no-color` for terminal, works with screen readers
- **Error handling:** Never crash on permission denied, always return partial results

---

## 13) MVP Definition (What Ships First)

**Minimum Viable Product** - The absolute minimum to validate the concept:

**Must Have (MVP):**
- ✅ `yourdad scan storage` - volume selection + storage scan
- ✅ Terminal report with dad personality
- ✅ HTML report with sortable tables
- ✅ Large files detection (top 500)
- ✅ Folder size analysis (depth 2)
- ✅ Smart exclusions (system folders, app bundles)
- ✅ File:// links in HTML report
- ✅ Basic dad comments (5-10 rules)

**Should Have (v0.1):**
- ✅ `yourdad scan cpu` - CPU/RAM snapshot
- ✅ `yourdad scan quick` - storage + cpu combined
- ✅ Progress feedback during scan
- ✅ Error handling (permissions, timeouts)
- ✅ Report history (`~/.dadware/reports/`)

**Could Have (v0.2+):**
- 🔜 Review workspace (symlink staging for easy deletion)
- 🔜 Duplicate file detection
- 🔜 Bulk move/trash script generation
- 🔜 More dad comments (data-aware, contextual)
- 🔜 Filter options (min size, date ranges)

---

## 14) Out of Scope (Deferred to Later Versions)

**Not in v0.1:**
- ❌ Menu interface (just subcommands for now)
- ❌ Config file / settings (hardcoded defaults)
- ❌ Multiple personalities (just "dad" voice)
- ❌ Duplicate file detection (v0.2)
- ❌ Review workspace / symlink staging (v0.2)
- ❌ Bulk delete operations (v0.2)
- ❌ Auto-cleanup agents / scheduled scans
- ❌ Plugin system (architecture is extensible, but no external plugins)
- ❌ Network diagnostics (v0.5)
- ❌ Battery health analysis (v0.5)
- ❌ Login items management (v0.5)

---

## 14) Success Metrics

**For v0.1 (qualitative):**
- ✅ Non-technical users can run it without help
- ✅ Dad personality makes people smile (test with 5+ people)
- ✅ Users find and delete at least 5GB after first scan
- ✅ Zero reports of accidental deletions (read-only safety works)
- ✅ HTML report is clear and actionable

**For later versions:**
- Track: weekly active users (if distributed)
- Track: average storage freed per scan
- Track: feature requests (what scans do people want?)

---

## 15) Roadmap (Post-v0.1)

See `/roadmap` folder for detailed specs. High-level plan:

| Version | Key Features | Estimated Effort |
|---------|--------------|------------------|
| **v0.1** | Storage + CPU scans, dual reports, dad personality | 4-6 weeks |
| **v0.2** | Duplicate file detection, symlink review workspace | 2-3 weeks |
| **v0.3** | Full-screen TUI (menu, keyboard navigation) | 3-4 weeks |
| **v0.4** | Animations, progress feedback, status messages | 1-2 weeks |
| **v0.5** | Battery health, network diagnostics, login items | 2-3 weeks |
| **v1.0** | Multiple personalities, themes, polish | 2-3 weeks |

---

## 16) Why This Design?

### Why personality-driven?
- Makes terminal tools approachable for non-technical users
- Differentiates from boring system utilities
- Creates emotional connection (people remember "the dad app")

### Why read-only?
- Safety first - users must consciously decide to delete
- Builds trust - tool won't mess up your system
- Legal/liability - we guide, user acts

### Why HTML + Terminal?
- HTML is shareable, sortable, clickable (better UX)
- Terminal is fast for power users, enables scripting
- Both audiences served

### Why extensible architecture?
- Easy to add new scans (battery, network, etc.)
- Each scanner is isolated - test independently
- Future-proof for community contributions

### Why subcommands vs menu?
- More scriptable / automation-friendly
- Easier to build incrementally
- Can add TUI menu layer later without changing core

---

## 17) Development Phases (High-Level)

**Phase 1: Foundation** (2 weeks)
- CLI skeleton with subcommands
- Volume selection logic
- Basic storage scanner (no personality)

**Phase 2: Core Scanners** (1 week)
- Large files detection
- Folder size analysis
- CPU/RAM snapshot

**Phase 3: Reports** (1 week)
- Terminal report with ANSI colors
- HTML report with sortable tables
- Dad personality engine

**Phase 4: Polish** (1 week)
- Error handling
- Smart exclusions
- Progress feedback
- Testing with real users

---

## 18) Open Questions

- [ ] Distribution: Python package (pip), standalone binary, or both?
- [ ] Auto-update mechanism?
- [ ] Should HTML report auto-refresh if re-run?
- [ ] Voice/sound effects for future versions?
- [ ] Windows/Linux ports, or Mac-only forever?

---

**End of PRD**
**Next step:** Create POC plan (simplified version to validate concept)
