# Dad Ware / `yourdad`

A personality-driven Mac cleanup tool that makes system maintenance fun and approachable.

## Current Status

**Version:** 0.1-poc (Proof of Concept)

**Latest Features:**
- ✅ Storage scanning with report card grading system
- ✅ Mac app library scanning (Photos, Music, Messages, Mail, Time Machine, Creative apps)
- ✅ Permission detection and user guidance
- ✅ Enhanced HTML reports with two-bar folder visualization
- ✅ Terminal and HTML reports with dad personality
- ✅ CPU/RAM snapshot scanning

## Installation

### Quick Start

1. Clone or download this repository
2. Ensure Python 3.9+ is installed
3. No external dependencies required (uses only Python stdlib)

### Optional: Install Script

Run the installation script for guided setup:

```bash
./scripts/install.sh
```

This will:
- Check Python version
- Install dependencies (if any)
- Create symlink for `yourdad` command (optional)
- Guide you through permission setup

### Homebrew (Future)

A Homebrew formula is available in `Formula/yourdad.rb` for future distribution.

## Usage

### Basic Commands

```bash
# Scan storage (large files and folders)
python3 yourdad.py scan storage

# Scan CPU and RAM usage
python3 yourdad.py scan cpu

# Quick scan (storage + CPU)
python3 yourdad.py scan quick
```

### Options

```bash
# Specify volume to scan
python3 yourdad.py scan storage --volume /Volumes/External

# Limit number of files shown
python3 yourdad.py scan storage --top 1000

# Set minimum file size
python3 yourdad.py scan storage --min-size 500MB

# Terminal report only (skip HTML)
python3 yourdad.py scan storage --terminal

# Disable ANSI colors
python3 yourdad.py scan storage --no-color

# Save reports to test-reports/ folder (for development)
python3 yourdad.py scan storage --test-reports

# Skip protected directories (Photos, Messages, Mail)
python3 yourdad.py scan storage --skip-protected
```

## Features

### Storage Analysis
- **Report Card System**: Grades your storage health with letter grades (A-F)
  - Free space grade
  - Home folders ratio grade
  - Home folders clutter grade (Downloads, Desktop)
  - Individual Mac app library grades (Photos, Music, Messages, Mail, etc.)
  - Composite overall grade
- **Two-Bar Visualization**: Separate bars for Home Folders and Other Folders
- **Top Files & Folders**: Identifies largest files and folders
- **Mac App Libraries**: Scans Photos, Music, Messages, Mail, Time Machine, and creative app libraries
- **Metrics**: Sum of top 10 folders, sum of top 25 files, reclaimable percentage

### CPU/RAM Snapshot
- Shows top processes by CPU and memory usage
- Real-time resource monitoring

### Dad Personality
- Witty, helpful comments based on scan results
- Actionable advice for cleanup
- Status indicators (all good, stable but cluttered, needs attention)

### Reports
- **Terminal Output**: Color-coded, personality-driven terminal reports
- **HTML Reports**: Interactive reports with:
  - Report card with grades
  - Sortable tables
  - Expandable folder details
  - File links (click to open in Finder)
  - Permission warnings and instructions

### Permission Management
- Automatic permission detection before scanning
- Clear warnings and setup instructions
- Graceful degradation when permissions missing
- Standalone permission checker: `python3 scripts/check_permissions.py`

## Reports Location

Reports are saved to:
- **Production**: `~/.dadware/reports/` (hidden folder in home directory)
- **Development**: `test-reports/` (if in git repo or using `--test-reports` flag)

Reports include:
- HTML file (interactive report)
- JSON manifest (scan data for programmatic access)

## Permissions

To scan Photos, Messages, and Mail libraries, you need **Full Disk Access**:

1. Open **System Settings** → **Privacy & Security**
2. Scroll to **Full Disk Access**
3. Click the lock icon and enter your password
4. Click **+** and add **Terminal.app** (or your IDE)
5. Make sure the checkbox is checked ✅
6. Restart Terminal/IDE

**Check permissions:**
```bash
python3 scripts/check_permissions.py
```

The scan will work without permissions, but protected libraries will show 0 bytes.

## Project Structure

```
dadware/
├── yourdad.py              # Main CLI entry point
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
│   └── permissions.py     # Permission detection
├── scripts/               # Helper scripts
│   ├── check_permissions.py  # Permission checker
│   └── install.sh        # Installation script
├── macos-helper/          # Swift helper (future Mac app)
└── Formula/               # Homebrew formula
```

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

Or manually open: `file:///path/to/report.html`

## Distribution

See `DISTRIBUTION.md` for distribution strategy:
- **Phase 1 (Current)**: Python CLI via Homebrew or direct installation
- **Phase 2 (Future)**: Mac App Bundle with Swift helper for permission dialogs

## Documentation

- `ROADMAP.md` - Product roadmap and version plans
- `DISTRIBUTION.md` - Distribution strategy
- `GRANT-PERMISSIONS.md` - Permission setup guide
- `SCAN-RESULTS-LOCATION.md` - Report file locations
- `PERMISSION-DISTRIBUTION-PLAN.md` - Permission handling implementation plan

## Safety

**Read-Only by Design**: This tool never deletes files. It only scans and reports. You control what gets deleted.

## License

[To be determined]

## Contributing

[To be added]

---

**Version:** 0.1-poc  
**Last Updated:** November 2025
