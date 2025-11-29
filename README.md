# Dad Ware / `yourdad`

A personality-driven Mac cleanup tool that makes system maintenance fun and approachable. Get a "report card" for your Mac with dad-style commentary and actionable advice.

**Version:** 0.1-poc (Build 2025-11-28-009)  
**Last Updated:** November 28, 2025

---

## What is Dad Ware?

Dad Ware scans your Mac's storage and memory, then gives you a report card with:
- 📊 **Letter grades** (A-F) for storage health
- 💬 **Dad-style commentary** ("memory's maxed out. that's why you're seeing warnings.")
- 💡 **Actionable tips** for freeing up space and reducing memory usage
- 📁 **Interactive HTML reports** with sortable tables and clickable file links
- 🔍 **Detailed analysis** of large files, folders, and memory usage

**Safety First:** This tool is **read-only** - it never deletes files. You control what gets deleted.

---

## Quick Start

### Installation

1. **Download or clone this repository**
2. **Ensure Python 3.9+ is installed** (check with `python3 --version`)
3. **No external dependencies** - uses only Python standard library

### Run Your First Scan

```bash
# Scan storage (find large files and folders)
python3 yourdad.py scan storage

# Scan CPU and RAM usage
python3 yourdad.py scan cpu

# Scan both (opens both reports)
python3 yourdad.py scan all
```

The HTML report will open automatically in your browser!

---

## Commands

### Storage Scan

Scan your Mac's storage to find large files and folders:

```bash
# Basic scan (prompts for volume selection)
python3 yourdad.py scan storage

# Scan specific volume
python3 yourdad.py scan storage --volume /Volumes/External

# Limit number of files shown
python3 yourdad.py scan storage --top 1000

# Set minimum file size (only show files larger than this)
python3 yourdad.py scan storage --min-size 500MB

# Skip protected directories (Photos, Messages, Mail)
python3 yourdad.py scan storage --skip-protected

# Skip Mac app libraries entirely (faster scan)
python3 yourdad.py scan storage --no-mac-libraries

# Terminal output only (skip HTML report)
python3 yourdad.py scan storage --terminal

# Disable ANSI colors in terminal
python3 yourdad.py scan storage --no-color

# Save to test-reports/ folder (for development)
python3 yourdad.py scan storage --test-reports
```

### CPU/RAM Scan

Monitor memory usage and identify memory hogs:

```bash
# Basic CPU/RAM scan
python3 yourdad.py scan cpu

# Export memory data to CSV during scan
python3 yourdad.py scan cpu --export-memory memory.csv

# Terminal output only
python3 yourdad.py scan cpu --terminal

# Disable colors
python3 yourdad.py scan cpu --no-color
```

### Combined Scan

Run both storage and CPU scans, opening both reports:

```bash
# Scan both storage and CPU
python3 yourdad.py scan all

# All storage scan options work here too
python3 yourdad.py scan all --volume /Volumes/External --skip-protected
```

### Export Data

Export memory/process data from existing reports:

```bash
# Export from existing JSON report
python3 yourdad.py export memory cpu_2025-11-26_16-54.json

# Export to specific file
python3 yourdad.py export memory cpu_2025-11-26_16-54.json memory_export.csv
```

**Note:** Memory export only works with CPU scan JSON files, not storage scans.

---

## Features

### Storage Analysis

- **Report Card System**: Get letter grades (A-F) for:
  - Free space percentage
  - Home folders organization
  - Downloads/Desktop clutter
  - Individual Mac app libraries (Photos, Music, Messages, Mail, etc.)
  - Overall composite grade

- **Two-Bar Visualization**: Separate bars for Home Folders vs Other Folders
- **Top Files & Folders**: Identifies largest files and folders with sizes
- **Mac App Libraries**: Scans Photos, Music, Messages, Mail, Time Machine, and creative app libraries
- **Expandable Details**: Click folder bars to see subfolders and top files
- **Reclaimable Space**: Shows how much space you could free by deleting top files

### CPU/RAM Analysis

- **Memory Overview**: Total RAM, used, free, and memory pressure
- **Process Statistics**: Total processes, processes over thresholds (100MB, 500MB, 1GB)
- **Memory Hogs**: Apps using the most memory (grouped by application)
- **Top Individual Processes**: Individual processes sorted by memory usage
- **Memory Distribution**: Visual breakdown of small/medium/large processes
- **Browser Tab Advice**: Tips for managing browser memory usage

### Dad Personality

- Witty, helpful comments based on scan results
- Actionable advice for cleanup
- Status indicators: 🟢 all good, 🟡 stable but cluttered, 🔴 needs attention
- Browser-specific tips (Chrome, Safari memory management)

### Reports

- **Terminal Output**: Color-coded, personality-driven terminal reports
- **HTML Reports**: Interactive reports with:
  - Report card with grades
  - Sortable file tables
  - Expandable folder details
  - Clickable file links (opens in Finder)
  - "Reveal in Finder" buttons (copies command to clipboard)
  - Permission warnings and setup instructions
  - AI consultation prompt (copy/paste for AI assistants)

---

## Report Locations

Reports are automatically saved to:

- **Production Mode**: `~/.dadware/reports/` (hidden folder in home directory)
- **Development Mode**: `test-reports/` (if in git repo or using `--test-reports` flag)

Each scan creates two files:
- **HTML Report**: `{scan_type}_{timestamp}.html` - Interactive visual report
- **JSON Manifest**: `{scan_type}_{timestamp}.json` - Raw scan data for programmatic access

---

## Permissions

To scan Photos, Messages, and Mail libraries, you need **Full Disk Access**:

1. Open **System Settings** → **Privacy & Security**
2. Scroll to **Full Disk Access**
3. Click the lock icon and enter your password
4. Click **+** and add **Terminal.app** (or your IDE like Cursor/VS Code)
5. Make sure the checkbox is checked ✅
6. Restart Terminal/IDE

**Check permissions:**
```bash
python3 scripts/check_permissions.py
```

The scan will work without permissions, but protected libraries will show 0 bytes.

See `GRANT-PERMISSIONS.md` for detailed instructions with screenshots.

---

## Installation Options

### Quick Install (Recommended)

Run the installation script:

```bash
./install.sh
```

This will:
- Check Python version
- Verify dependencies
- Guide you through permission setup

### Manual Install

1. Clone or download this repository
2. Ensure Python 3.9+ is installed
3. Make scripts executable: `chmod +x install.sh yourdad`
4. Run: `python3 yourdad.py scan storage`

### Homebrew (Future)

A Homebrew formula is available in `Formula/yourdad.rb` for future distribution.

---

## Project Structure

```
dadware/
├── yourdad.py              # Main CLI entry point
├── yourdad                 # Menu launcher script
├── personality/            # Personality engine (dad comments)
├── scanners/               # Scan modules
│   ├── storage.py         # Storage scanning
│   ├── cpu.py             # CPU/RAM scanning
│   ├── mac_libraries.py   # Mac app library scanning
│   └── grading.py         # Report card grading system
├── renderers/             # Report generators
│   ├── terminal.py        # Terminal output
│   └── html.py            # HTML reports
├── utils/                 # Utilities
│   ├── volumes.py         # Volume selection
│   ├── permissions.py     # Permission detection
│   ├── system_info.py     # System information
│   └── llm_prompt.py      # AI prompt generation
├── scripts/               # Helper scripts
│   ├── check_permissions.py  # Permission checker
│   └── install.sh         # Installation script
├── macos-helper/          # Swift helper (future Mac app)
└── Formula/               # Homebrew formula
```

---

## Development

### Test Reports

During development, reports are automatically saved to `test-reports/` folder when:
- Running in a git repository, OR
- Using the `--test-reports` flag

This makes it easy to iterate on UX without navigating to hidden folders.

### Generate Sample Report

Use existing JSON data to generate HTML reports for UX iteration:

```bash
python3 generate_sample_report.py
```

### Preview Reports

Open HTML reports in browser:

```bash
python3 preview_report.py
```

---

## Troubleshooting

### QGIS Python Conflict

If you have **QGIS** installed and see an error like:
```
AssertionError: SRE module mismatch
```

**Solution:** Use the menu script instead:
```bash
./yourdad
```

The menu script automatically detects and avoids QGIS's Python. Alternatively, use system Python directly:
```bash
/usr/bin/python3 yourdad.py scan all
```

### Other Common Issues

**"command not found: python3"**
→ Install Python from [python.org](https://www.python.org/downloads/)

**"No such file or directory"**
→ Make sure you're in the right folder: `cd ~/Downloads/dadware-max`

**Security warning about "unidentified developer"**
→ Right-click the file → Open (first time only)

---

## Documentation

### Current Documentation
- **`RELEASE-NOTES.md`** - Release notes and changelog
- **`GRANT-PERMISSIONS.md`** - Detailed permission setup guide

**Note:** Additional documentation (roadmaps, bug tracking, design docs) is stored in the `docs/` directory, which is excluded from the GitHub repository.

---

## Safety & Disclaimer

**Read-Only by Design**: This tool never deletes files. It only scans and reports. You control what gets deleted.

**Important**: This software provides reports and information about what is taking up space on your computer. It does NOT provide advice about what to delete or archive. **You must determine, at your own discretion, what files or folders to delete or archive from your computer.** The authors are not responsible for any data loss or consequences resulting from decisions you make based on information provided by this software.

---

## License

Copyright (c) 2025 John Billington

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

**Why MIT?** MIT is a permissive open-source license that allows:
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ✅ Patent use

The only requirement is to include the original copyright notice and license.

**Alternative:** If you prefer a copyleft license (requires derivative works to be open source), consider the **GNU General Public License (GPL) v3**.

**Disclaimer:** This software provides reports and information only. It does not provide advice about what to delete or archive. Users must determine, at their own discretion, what files or folders to delete or archive from their computers. See the [LICENSE](LICENSE) file for full disclaimer.

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## Changelog

See [`RELEASE-NOTES.md`](RELEASE-NOTES.md) for detailed release notes and changelog.

**Recent Updates:**
- ✅ Fixed Safari font rendering issue (Build 2025-11-28-008)
- ✅ Fixed free memory calculation bug (Build 2025-11-28-009)
- ✅ Enhanced browser tabs memory advice
- ✅ Improved CPU report with process statistics
- ✅ Added memory export functionality

---

**Made with ❤️ by a dad who's tired of explaining disk space**
