# Dad Ware / `yourdad` — Proof of Concept Plan

**Goal:** Validate core concept in 12-16 hours of focused coding
**Owner:** John Billington
**Date:** November 2025
**Strategy:** Build incrementally, test personality early, create savepoints

---

## 1) Purpose

Build a **minimal but complete** version of yourdad that proves:

1. **Architecture works** - scanners → analysis → personality → reports pipeline
2. **Personality lands** - dad voice is funny and helpful, not annoying
3. **HTML reports are useful** - better UX than terminal alone
4. **Performance is acceptable** - scans complete in <30 seconds

**What's NOT in POC:**
- ❌ Duplicate detection (v0.2)
- ❌ Review workspace / symlink staging (v0.2)
- ❌ Menu interface (v0.3)
- ❌ Config files (v0.1+)
- ❌ Multiple personalities (v1.0)

---

## 2) Success Criteria

**POC is successful if:**
- ✅ You can run `yourdad scan storage` and get an HTML report in <30s
- ✅ The dad comments make you smile (not cringe)
- ✅ HTML report is actually useful for finding large files
- ✅ 3+ non-technical people "get it" without explanation
- ✅ Architecture is clean enough to add CPU scanner easily

**POC fails if:**
- ❌ Personality feels forced or annoying
- ❌ HTML report is confusing or ugly
- ❌ Scan takes >60s on typical home directory
- ❌ Code is too tangled to extend

---

## 3) Phased Build Plan

### 🎯 Phase 0: Hello World CLI (30 min)

**Goal:** Prove basic Python CLI works

**Deliverable:**
```bash
$ python3 yourdad.py --version
Dad Ware v0.1-poc

$ python3 yourdad.py --help
usage: yourdad.py [-h] [--version] {scan} ...

Dad Ware - Your friendly Mac cleanup tool
```

**What to build:**
- Single file: `yourdad.py`
- Use `argparse` for CLI structure
- Define subcommands: `scan storage`, `scan cpu`, `scan quick`
- Print branded header
- Exit cleanly

**Test:** Run all commands, verify help text, no errors

**✅ SAVEPOINT 0**

---

### 🎯 Phase 1: Volume Selection (1 hr)

**Goal:** Let user pick a volume or default to home

**Deliverable:**
```bash
$ python3 yourdad.py scan storage

────────────────────────────────
 Dad Ware  |  yourdad v0.1
────────────────────────────────

Available volumes:
1) Macintosh HD (/) - 500 GB, 387 GB used (77%)
2) External Backup (/Volumes/Backup) - 2 TB, 1.1 TB used (55%)
3) Home directory only (~/) - quickest

Pick one [3]:
```

**What to build:**
- `list_volumes()` function using `os.statvfs()` and `/Volumes`
- Detect mounted volumes, get size info
- Default to option 3 (home directory)
- Store selected path for scanning

**Test:** Verify all mounted volumes appear, default works

**✅ SAVEPOINT 1**

---

### 🎯 Phase 2: Storage Scanner (Core) (3 hrs)

**Goal:** Scan directory and collect largest files + folders

**Deliverable:**
```bash
$ python3 yourdad.py scan storage
Scanning /Users/john...
→ found 3,214 items
→ calculating sizes...

Top 10 Folders:
  Movies/                    47.2 GB
  Library/Application Support 23.8 GB
  Downloads/                 18.5 GB
  ...

Top 10 Largest Files:
  Final_Cut_Project.zip       8.4 GB
  2022_backup.dmg             5.1 GB
  ...
```

**What to build:**
- `scanners/storage.py` module
- `scan_storage(path, depth=2)` function
- Use `os.walk()` to traverse directories
- Calculate folder sizes (sum of all files inside)
- Track top N largest files (heap or sorted list)
- **Smart exclusions:**
  - Skip: `/System`, `/Library`, `/Applications`, `/usr`, `/bin`, `/sbin`
  - Skip: `*.app/`, `*.photoslibrary/`, caches, temp
  - Skip: hidden files starting with `.`
- Handle permission errors gracefully (skip + count)
- Return structured data:
  ```python
  {
    "scan_type": "storage",
    "volume": "/Users/john",
    "top_folders": [...],
    "top_files": [...],
    "volume_info": {"total": ..., "used": ..., "free": ...},
    "skipped_count": 42,
    "duration_seconds": 18.3
  }
  ```

**Technical decisions:**
- Skip symlinks (avoid double-counting)
- Hard limit: depth 2, timeout 60s
- Use `os.path.getsize()` for files, sum for folders
- Store sizes in bytes, format later

**Test:** Scan your real home directory, verify results match Finder

**✅ SAVEPOINT 2**

---

### 🎯 Phase 3: Terminal Report Formatter (2 hrs)

**Goal:** Make output look like "Dad's Report Card"

**Deliverable:**
```bash
────────────────────────────────────────
 DAD'S REPORT CARD — Dad Ware v0.1
 MacBook-Pro  |  User: John
 Date: November 9, 2025 14:23
────────────────────────────────────────

📦 STORAGE SCAN — /Users/john

Top Folders (depth 2):
  Movies/                    47.2 GB
  Library/Application Support 23.8 GB
  Downloads/                 18.5 GB

Top 10 Largest Files:
  Final_Cut_Project.zip       8.4 GB
  2022_backup.dmg             5.1 GB

Total: 500 GB  |  Used: 387 GB (77%)  |  Free: 113 GB

(42 items skipped due to permissions)

────────────────────────────────────────
Scan completed in 18.3 seconds
────────────────────────────────────────
```

**What to build:**
- `renderers/terminal.py` module
- `render_terminal(scan_data)` function
- Formatted header with date/hostname/user
- Table formatting with aligned columns
- Human-readable sizes (GB, MB)
- Basic ANSI colors (optional, support `--no-color`)
- Footer with stats

**Libraries:** `colorama` (optional), or raw ANSI codes

**Test:** Output looks clean in Terminal.app and iTerm2

**✅ SAVEPOINT 3**

---

### 🎯 Phase 4: Personality Engine (2 hrs) ⚠️ CRITICAL

**Goal:** Add dad voice comments based on scan results

**Deliverable:**
```bash
📦 STORAGE SCAN — /Users/john

[... data ...]

💬 Dad says: "downloads looks like a garage shelf.
   time to label a box."

Status: 🟡 stable but cluttered
```

**What to build:**
- `personality/yourdad.py` module
- `add_personality(scan_data)` function
- Hardcoded rules (5-10 to start):
  ```python
  if downloads_size > 10_GB:
      return "downloads looks like a garage shelf. time to label a box."
  elif downloads_size > 5_GB:
      return "downloads is getting crowded. regular cleanup day?"

  if free_space_percent < 10:
      return "living on the edge. let's back away from the cliff."

  if desktop_size > 5_GB:
      return "desktop isn't meant to be storage. it's a desk, not a storage unit."

  # ... etc
  ```
- Pick 1-2 comments based on scan results
- Keep it SHORT (≤2 lines)
- Return status: `ok` | `warn` | `critical`

**Test:** Run on your Mac, verify comments are:
- ✅ Funny/charming
- ✅ Helpful/actionable
- ✅ Not annoying or condescending

**⚠️ CRITICAL CHECKPOINT:**
If the personality doesn't land here, pause and iterate on the comments before continuing. Show to 2-3 people for feedback.

**✅ SAVEPOINT 4**

---

### 🎯 Phase 5: HTML Report Generator (3 hrs)

**Goal:** Create beautiful, interactive HTML report

**Deliverable:**
- Generates `~/.dadware/reports/storage_2025-11-09_14-23.html`
- Opens automatically in default browser
- Sortable table, file:// links work

**HTML Structure:**
```html
<!DOCTYPE html>
<html>
<head>
  <title>Dad's Report Card - Nov 9, 2025</title>
  <style>
    /* Embedded CSS - clean, minimal design */
  </style>
</head>
<body>
  <header>
    <h1>DAD'S REPORT CARD</h1>
    <p>Dad Ware v0.1  |  MacBook-Pro  |  Nov 9, 2025 14:23</p>
  </header>

  <section class="personality">
    <h2>💬 Dad says:</h2>
    <p>"downloads looks like a garage shelf. time to label a box."</p>
  </section>

  <section class="summary">
    <h2>📦 Storage Scan - /Users/john</h2>
    <p>Total: 500 GB  |  Used: 387 GB (77%)  |  Free: 113 GB</p>
    <p class="status warn">🟡 stable but cluttered</p>
  </section>

  <section class="top-folders">
    <h3>Top Folders</h3>
    <table id="foldersTable">
      <thead>
        <tr>
          <th onclick="sortTable('foldersTable', 0)">Path</th>
          <th onclick="sortTable('foldersTable', 1)">Size</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>~/Movies</td>
          <td data-size="50653265920">47.2 GB</td>
          <td><button onclick="revealInFinder('~/Movies')">Reveal in Finder</button></td>
        </tr>
        <!-- ... -->
      </tbody>
    </table>
  </section>

  <section class="top-files">
    <h3>Top 10 Largest Files</h3>
    <table id="filesTable">
      <!-- similar structure -->
    </table>
  </section>

  <footer>
    <h3>💡 What to do next:</h3>
    <ul>
      <li>Click "Reveal in Finder" to see files in Finder</li>
      <li>Delete files manually (send to Trash)</li>
      <li>Start with ~/Downloads - easiest wins</li>
    </ul>
  </footer>

  <script>
    // Client-side sorting
    function sortTable(tableId, colIndex) { /* ... */ }

    // Copy reveal command
    function revealInFinder(path) {
      const cmd = `open -R "${path}"`;
      navigator.clipboard.writeText(cmd);
      alert(`Copied to clipboard:\n${cmd}\n\nPaste in Terminal to reveal file.`);
    }
  </script>
</body>
</html>
```

**What to build:**
- `renderers/html.py` module
- `render_html(scan_data, personality_data)` function
- Generate complete HTML file with embedded CSS/JS
- Client-side table sorting (no dependencies)
- Copy-to-clipboard for reveal commands
- Clean, minimal design (no Bootstrap, no external deps)
- Use `file://` URLs for clickable paths

**Test:**
- Open in Safari, Chrome, Firefox
- Verify sorting works
- Click file:// links, verify Finder opens
- Test "Reveal in Finder" buttons

**✅ SAVEPOINT 5**

---

### 🎯 Phase 6: CPU Scanner (2 hrs)

**Goal:** Add CPU/RAM snapshot

**Deliverable:**
```bash
$ python3 yourdad.py scan cpu

🔥 CPU & RAM SNAPSHOT

Top Processes:
  chrome helper          42.3% CPU    1.2 GB RAM
  photoanalysisd         31.1% CPU    800 MB RAM
  slack                  18.0% CPU    650 MB RAM
  ...

💬 Dad says: "lots of tabs. lots of fans. cause ↔ effect."

Status: 🟡 warm
```

**What to build:**
- `scanners/cpu.py` module
- `scan_cpu()` function
- Run `ps aux` and parse output
- Get top 5 processes by CPU%
- Get memory usage per process
- Return structured data (same format as storage scan)
- Add personality comments for CPU:
  ```python
  if chrome_cpu > 50:
      return "lots of tabs. lots of fans. cause ↔ effect."
  if photoanalysisd_running:
      return "photoanalysisd is doing its thing. mac's version of 'I'm organizing.'"
  ```

**Test:** Verify process list is accurate, compare with Activity Monitor

**✅ SAVEPOINT 6**

---

### 🎯 Phase 7: Integration & Polish (2 hrs)

**Goal:** Wire everything together, add final touches

**Deliverable:**
```bash
$ python3 yourdad.py scan quick
# Runs storage + cpu, generates combined report

$ python3 yourdad.py scan storage --terminal
# Skip HTML, terminal only

$ python3 yourdad.py scan storage --top 1000 --min-size 500MB
# Configurable options
```

**What to build:**
- `yourdad scan quick` command (runs both scanners)
- Combined HTML report (storage + cpu sections)
- `--terminal` flag to skip HTML generation
- `--top N` and `--min-size` flags for storage scan
- Report manifest saved to `~/.dadware/reports/manifest.json`
- Add tips section to reports:
  ```python
  tips = [
    "Start with ~/Downloads - easiest wins",
    "Review old backups (2022_backup.dmg)",
    "Check ~/Movies for archived projects"
  ]
  ```
- Error handling polish:
  - Timeout for long scans
  - Graceful handling of unreadable files
  - Clear error messages
- Summary line with emoji status (🟢 ok, 🟡 warn, 🔴 critical)

**Test:** Full end-to-end on real system, try all commands

**✅ SAVEPOINT 7 — POC COMPLETE**

---

## 4) Timeline & Effort

| Phase | Task | Hours | Cumulative |
|-------|------|-------|------------|
| 0 | Hello World CLI | 0.5 | 0.5 |
| 1 | Volume Selection | 1 | 1.5 |
| 2 | Storage Scanner | 3 | 4.5 |
| 3 | Terminal Report | 2 | 6.5 |
| 4 | Personality Engine | 2 | 8.5 |
| 5 | HTML Report | 3 | 11.5 |
| 6 | CPU Scanner | 2 | 13.5 |
| 7 | Integration & Polish | 2 | 15.5 |
| **TOTAL** | | **15.5 hrs** | |

**Realistic:** 4-5 coding sessions @ 3-4 hours each

---

## 5) Project Structure

```
dadware/
├── yourdad.py                 # CLI entry point, argparse
├── scanners/
│   ├── __init__.py
│   ├── storage.py             # Storage scan logic
│   └── cpu.py                 # CPU/RAM snapshot
├── personality/
│   ├── __init__.py
│   └── yourdad.py             # Dad voice comment rules
├── renderers/
│   ├── __init__.py
│   ├── terminal.py            # Terminal formatter
│   └── html.py                # HTML report generator
├── utils/
│   ├── __init__.py
│   └── volumes.py             # Volume detection
├── templates/
│   └── report_template.html   # HTML template (if separated)
└── tests/
    └── test_storage.py        # Basic tests
```

---

## 6) Architecture Validation

The POC must prove this pipeline works:

```
User Command
    ↓
CLI Parser (yourdad.py)
    ↓
Orchestrator
    ↓
Scanner (storage.py / cpu.py)
    ↓ returns structured data
Analysis Engine (thresholds, status tagging)
    ↓
Personality Engine (yourdad.py)
    ↓ adds comments
Report Generators (terminal.py + html.py)
    ↓
Output (terminal + HTML file)
```

**Key validation points:**
- ✅ Scanners return standard format (easy to add new ones)
- ✅ Personality is separate layer (easy to swap/extend)
- ✅ Renderers are independent (easy to add JSON, CSV, etc.)

---

## 7) Test Plan

### Manual Testing (POC)

**Test 1: Fresh system**
- Run on a clean Mac with default folders
- Verify volumes list correctly
- Check scan completes in <30s
- Verify HTML opens automatically

**Test 2: Large home directory**
- Run on system with 200+ GB home
- Verify doesn't timeout
- Check exclusions work (no system files)
- Verify large files are found correctly

**Test 3: Permission errors**
- Run without Full Disk Access
- Verify graceful handling of restricted folders
- Check skipped count is accurate

**Test 4: Personality validation**
- Run on systems with different patterns:
  - Large Downloads folder
  - Low free space
  - Heavy CPU usage
- Show to 3+ non-technical users
- Get feedback: funny? helpful? annoying?

**Test 5: HTML report usability**
- Open in different browsers
- Test sorting functionality
- Click file:// links
- Test "Reveal in Finder" buttons
- Try on different screen sizes

---

## 8) Success Checklist

Before calling POC complete, verify:

- [ ] `yourdad scan storage` works end-to-end
- [ ] Volume selection shows all mounted drives
- [ ] Scan completes in <30s for typical home directory
- [ ] Terminal report is readable and formatted
- [ ] HTML report opens automatically in browser
- [ ] HTML table sorting works
- [ ] File:// links open in Finder
- [ ] Dad comments make you smile (not cringe)
- [ ] 3+ people understand it without explanation
- [ ] Permission errors handled gracefully
- [ ] CPU scanner works independently
- [ ] `yourdad scan quick` combines both scans
- [ ] `--terminal` flag skips HTML generation
- [ ] Reports saved to `~/.dadware/reports/`

---

## 9) Known Limitations (POC)

**Acceptable for POC:**
- Hardcoded thresholds (no config file)
- Only "dad" personality (no alternatives)
- No duplicate detection
- No review workspace / symlink staging
- Basic personality rules (5-10 comments)
- Limited error recovery
- No progress bar (just status messages)
- No tests (manual testing only)

**Must fix for v0.1:**
- Add progress feedback
- More personality rules
- Better error messages
- Basic test coverage

---

## 10) After POC: Decision Points

**If personality works:**
→ Proceed to v0.1 (add polish, more comments, better UX)

**If personality doesn't land:**
→ Pause, iterate on comments, get more feedback
→ Consider different tone/style
→ Test with target users (teens, non-tech folks)

**If performance is slow:**
→ Profile and optimize scanner
→ Consider async/parallel file walking
→ Add configurable depth limits

**If HTML report isn't useful:**
→ Investigate why (design? functionality?)
→ Add missing features (filters, search)
→ Consider different format

---

## 11) Risks (Specific to POC)

| Risk | Mitigation |
|------|------------|
| Personality doesn't land | Test early (Phase 4), get feedback before continuing |
| Scan too slow | Set timeout, test on large directories early |
| HTML report ugly | Use simple, clean design; test on multiple browsers |
| Permission errors break scan | Handle gracefully from Phase 2 onward |
| Scope creep | Stick to 7 phases, resist adding features |

---

## 12) Deliverables

**At end of POC, you should have:**

1. ✅ Working CLI: `yourdad scan storage`, `yourdad scan cpu`, `yourdad scan quick`
2. ✅ Terminal report with dad personality ("Dad's Report Card")
3. ✅ HTML report with sortable tables
4. ✅ Reports saved to `~/.dadware/reports/`
5. ✅ Clean codebase ready to extend
6. ✅ Validated concept with real users

**Not required for POC:**
- ❌ Duplicate detection
- ❌ Review workspace
- ❌ Config file
- ❌ Automated tests
- ❌ Distribution package
- ❌ Documentation

---

**Ready to start?**

Begin with Phase 0: Create `yourdad.py` and print "Hello World"
