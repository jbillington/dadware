# Release Notes - Dad Ware

## Version 0.1-poc

### Build 2025-11-28-009 (Current)
**Release Date:** November 28, 2025

#### Bug Fixes
- **Fixed Free Memory Calculation**: Corrected memory overview display showing 0.0 GB free when memory was actually available
  - Changed from using `vm_stat` free pages (incomplete) to calculating `Total RAM - Used RAM`
  - Now accurately displays free memory (e.g., 16.0 GB total - 9.5 GB used = 6.5 GB free)
  - Fixed in both HTML and terminal reports

---

### Build 2025-11-28-008
**Release Date:** November 28, 2025

#### Bug Fixes
- **Fixed Safari Font Rendering Issue**: Resolved Chinese/Kanji characters appearing in reports on Safari
  - Changed italic text fonts from system fonts (`-apple-system`) to explicit Helvetica/Arial
  - Fixed "Dad says" personality comments displaying incorrectly
  - Fixed "📁 in Downloads" file table text displaying incorrectly
  - Tested and verified on Safari 17.3.1
  - Maintains compatibility with Chrome and other browsers

#### Technical Details
- Updated `.personality p` CSS to use `'Helvetica Neue', Helvetica, Arial, sans-serif`
- Updated `.file-folder-name` CSS to use `'Helvetica Neue', Helvetica, Arial, sans-serif`
- Added font smoothing properties for better rendering

---

### Build 2025-11-28-007
**Release Date:** November 28, 2025

#### Enhancements
- **Enhanced Browser Tabs Memory Advice**: Added comprehensive tips about browser tab memory usage
  - New dedicated "Browser Tabs & Memory" section in CPU reports
  - Specific advice for Chrome and Safari memory management
  - Tips appear when browsers are using significant memory (>0.5GB)
  - Explains that each tab uses 100-300MB of memory
  - Provides actionable advice: bookmark instead of keeping tabs open, close unused tabs, etc.

#### Improvements
- More detailed tips throughout the report when browsers are detected
- Browser-specific advice based on memory usage and process count
- General tab management tips in multiple sections

---

### Build 2025-11-28-006
**Release Date:** November 28, 2025

#### Enhancements
- **Enhanced AI Prompt with Detailed Process Information**: Significantly expanded the AI consultation prompt
  - Added Process Statistics section (total processes, distribution, averages)
  - Increased from top 10 to top 30 memory hogs (grouped by app)
  - Added "Top Individual Processes by Memory" section (top 30 individual processes)
  - Increased from top 10 to top 15 CPU processes
  - Added complete detailed list of top 100 processes with full command lines
  - Provides AI with comprehensive context for better analysis and advice

#### Technical Details
- Enhanced `generate_cpu_prompt()` in `utils/llm_prompt.py`
- More process details for deeper AI analysis
- Better context for identifying memory pressure causes

---

### Build 2025-11-28-005
**Release Date:** November 28, 2025

#### Enhancements
- **Better Memory Analysis for Many Small Processes**: Improved detection and advice for "death by a thousand cuts" scenarios
  - Detects when many small processes (>400) are using significant total memory (>5GB)
  - Provides specific comment: "death by a thousand cuts"
  - Suggests restarting Mac as solution
  - Enhanced personality tips based on process metrics

#### Improvements
- Lowered memory hog threshold from 200MB to 50MB to catch more apps using memory
- Increased displayed memory hogs from 10 to 20 in HTML report
- Increased displayed memory hogs from 5 to 20 in terminal report
- Added process metrics calculation (total processes, processes over thresholds, average memory)

---

### Build 2025-11-28-004
**Release Date:** November 28, 2025

#### Enhancements
- **Improved CPU Report Helpfulness**: Enhanced CPU/RAM reports with more actionable information
  - Added Process Statistics section showing:
    - Total processes count
    - Processes over 100MB, 500MB, 1GB thresholds
    - Average memory per process
  - Added Memory Distribution bar chart (Small, Medium, Large processes)
  - Added "Top Individual Processes by Memory" section (top 30 processes)
  - Better advice for reducing memory usage
  - More apps shown in memory hogs list

#### Improvements
- Grouped `com.apple.webkit.webcontent` processes with Safari for accurate memory reporting
- Enhanced memory-related comments and tips
- More specific advice based on memory pressure and top memory hogs

---

### Build 2025-11-28-003
**Release Date:** November 28, 2025

#### Enhancements
- **Build Number Display**: Added build number to menu and scan start messages
  - Menu script displays version and build number
  - Scan start messages include build number for version verification
  - Helps verify correct version is installed

#### Bug Fixes
- **Fixed Home Folder Breakdown in Full Scan**: Ensured home folder color bar chart always appears
  - Always performs separate scan of home directory
  - Merges home folder results into main scan
  - Home folders always appear at top of report
  - Removed "Home directory only" option (kept volume selection for multi-volume systems)

---

### Build 2025-11-28-002
**Release Date:** November 28, 2025

#### Enhancements
- **Improved Progress Indicators**: Better feedback during long storage scans
  - Time-based heartbeat ensures progress updates every 5 seconds
  - More frequent updates when items are found (every 2 seconds)
  - Prevents progress counter from stalling on slower computers
  - Better user experience during long scans

#### Bug Fixes
- **Removed Storage Scan Timeout**: Scans now run to completion
  - Removed 60-second timeout that was stopping scans prematurely
  - Users can still manually cancel with Ctrl+C
  - Scans complete even with large file counts (1M+ files)

---

### Build 2025-11-28-001
**Release Date:** November 28, 2025

#### Enhancements
- **Renamed "Quick" Scan to "All"**: Updated command and menu
  - Changed `yourdad scan quick` to `yourdad scan all`
  - Menu option renamed to "Check Both"
  - Scans both storage and CPU, opens both reports
  - Updated help text throughout

#### New Features
- **Memory Export Functionality**: Export all memory processes to CSV
  - `yourdad scan cpu --export-memory filename.csv` - Export during scan
  - `yourdad export memory filename.json` - Export from existing JSON report
  - Includes all processes (not just top 10)
  - Includes system memory information

#### Improvements
- Updated help text to clearly explain export options
- Clarified that export is CPU/memory only (not storage)
- Better documentation in `-h` output

---

## Known Issues

### Bug #2: fork_exec() Argument Count Mismatch
**Status:** Open  
**Severity:** High  
**Description:** Error during "full scan" - `fork_exec() takes exactly 23 arguments (21 given)`  
**Workaround:** Run storage and CPU scans separately  
**See:** `BUG-LOG.md` and `BUG-FIX-PLAN.md`

### Bug #3: Performance Degradation with Large File Counts
**Status:** Open  
**Severity:** High  
**Description:** Scan becomes very slow after ~1M files (only finding ~100 files at a time)  
**Affected:** Systems with iCloud Drive containing many code repos or symlinks  
**Workaround:** Use `--skip-protected` or scan specific directories  
**See:** `BUG-LOG.md` and `BUG-FIX-PLAN.md`

---

## Installation

See `README.md` for installation instructions.

## Reporting Issues

Please report bugs and issues in the bug tracker or via the issues system.

---

**Last Updated:** November 28, 2025  
**Current Version:** 0.1-poc  
**Current Build:** 2025-11-28-009

