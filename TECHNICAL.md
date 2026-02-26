# Dad Ware - Technical Documentation

**For Developers and Advanced Users**

This document contains technical details, development information, and advanced usage that was removed from the user-friendly README.

---

## Table of Contents

- [Installation Options](#installation-options)
- [Advanced Commands](#advanced-commands)
- [Project Structure](#project-structure)
- [Development](#development)
- [Building from Source](#building-from-source)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
- [Contributing](#contributing)

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

### Executable Binary (Recommended - Solves Python Conflicts)

**No Python required!** Build a standalone executable that solves Python environment issues:

```bash
# Install PyInstaller first (if not already installed)
pip install pyinstaller

# Build the executable
./build_executable.sh

# The executable will be at: dist/yourdad
# Just copy it anywhere and run it!
./dist/yourdad scan cpu
```

**Benefits:**
- ✅ **No Python installation needed** - Works on any Mac
- ✅ **Solves QGIS conflicts** - Uses bundled Python, avoids environment issues
- ✅ **Solves fork_exec() errors** - No Python version compatibility issues
- ✅ **Single file** - Easy to share and distribute
- ✅ **No dependencies** - Works on any Mac without setup

**Why use the executable?**
If you're experiencing Python-related errors (like `fork_exec()` or QGIS conflicts), the executable is the recommended solution. It bundles its own Python interpreter, avoiding all environment conflicts.

See `BUILD-EXECUTABLE.md` for detailed instructions and troubleshooting.

### Homebrew (Future)

A Homebrew formula is available in `Formula/yourdad.rb` for future distribution.

---

## Advanced Commands

### Storage Scan Options

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

### CPU/RAM Scan Options

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
│   ├── install.sh         # Installation script
│   └── generate_html_readme.py  # HTML README generator
├── macos-helper/          # Swift helper (future Mac app)
├── Formula/               # Homebrew formula
├── build_executable.sh    # Build executable script
├── package_for_distribution.sh  # Package for distribution
└── docs/                  # Documentation (excluded from GitHub)
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

### Building from Source

1. Clone the repository
2. Ensure Python 3.9+ is installed
3. No external dependencies (uses only Python standard library)
4. Run from source: `python3 yourdad.py scan storage`

### Building Executable

See `BUILD-EXECUTABLE.md` for detailed instructions on building the standalone executable.

---

## Troubleshooting

### QGIS Python Conflict

If you have **QGIS** installed and see an error like:
```
AssertionError: SRE module mismatch
```
or
```
fork_exec() takes exactly 23 arguments (21 given)
```

**These errors are caused by Python environment conflicts.** QGIS installs its own Python, and when you run `python3`, it may use QGIS's Python instead of the system Python.

**Solutions (choose one):**

1. **Use the executable** (✅ **RECOMMENDED** - solves all Python conflicts):
   ```bash
   ./dist/yourdad scan all
   ```
   The executable bundles its own Python, avoiding all environment issues.

2. **Build your own executable** (see `BUILD-EXECUTABLE.md`):
   ```bash
   ./build_executable.sh
   ```

3. **Use system Python directly**:
   ```bash
   /usr/bin/python3 yourdad.py scan all
   ```

4. **Use the menu script**:
   ```bash
   ./yourdad
   ```
   The menu script automatically detects and avoids QGIS's Python.

**Note:** The executable is the best solution as it completely avoids Python environment issues and works on any Mac without Python installed.

### Other Common Issues

**"command not found: python3"**
→ Install Python from [python.org](https://www.python.org/downloads/)

**"No such file or directory"**
→ Make sure you're in the right folder: `cd ~/Downloads/dadware-max`

**Security warning about "unidentified developer"**
→ Right-click the file → Open (first time only)

---

## Architecture

### Core Components

- **`yourdad.py`**: Main CLI entry point, orchestrates scans, report generation, and file I/O
- **`scanners/`**: Core scanning logic for storage, CPU, and Mac app libraries
- **`renderers/`**: Report generation (HTML and terminal output)
- **`personality/`**: Dad-style commentary engine
- **`utils/`**: Utility functions for volumes, permissions, system info

### Data Flow

1. User runs command → `yourdad.py` parses arguments
2. `yourdad.py` calls appropriate scanner (storage, cpu, etc.)
3. Scanner returns scan data
4. Personality engine adds commentary
5. Renderer generates HTML/terminal report
6. Report saved and opened in browser

### Key Design Decisions

- **Read-only by design**: Never deletes files, only reports
- **No external dependencies**: Uses only Python standard library
- **Graceful degradation**: Works without permissions (shows 0 bytes for protected files)
- **Personality-driven**: Makes technical information approachable

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Clone the repository
2. Ensure Python 3.9+ is installed
3. No virtual environment needed (no external dependencies)
4. Run tests: `pytest` (when tests are implemented)

### Code Style

- Follow PEP 8 Python style guide
- Use descriptive variable names
- Add docstrings to functions
- Keep functions focused and small

---

## Documentation

### Current Documentation
- **`RELEASE-NOTES.md`** - Release notes and changelog
- **`GRANT-PERMISSIONS.md`** - Detailed permission setup guide
- **`BUILD-EXECUTABLE.md`** - Executable build instructions
- **`TECHNICAL.md`** - This file (technical documentation)

**Note:** Additional documentation (roadmaps, bug tracking, design docs) is stored in the `docs/` directory, which is excluded from the GitHub repository.

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

---

## Changelog

See [`RELEASE-NOTES.md`](RELEASE-NOTES.md) for detailed release notes and changelog.

**Recent Updates:**
- ✅ Fixed Safari font rendering issue (Build 2025-11-28-008)
- ✅ Fixed free memory calculation bug (Build 2025-11-28-009)
- ✅ Enhanced browser tabs memory advice
- ✅ Improved CPU report with process statistics
- ✅ Added memory export functionality
- ✅ Executable build system complete (solves QGIS/Python conflicts)
- ✅ Docker container detection and exclusion (improves performance)
- ✅ Fixed reporting bugs (Messages folder, home folders, "View all" link)

---

**Made with ❤️ by a dad who's tired of explaining disk space**

