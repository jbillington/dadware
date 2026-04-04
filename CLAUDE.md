# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dad Ware is a personality-driven macOS cleanup tool that scans storage and memory, generates letter grades (A-F), and provides dad-style commentary with actionable cleanup advice. It is read-only by design (never deletes files) and uses only the Python standard library at runtime.

## Commands

```bash
# Run tests
./venv/bin/python -m pytest tests/ -v

# Run tests by marker
./venv/bin/python -m pytest -m "unit" -v
./venv/bin/python -m pytest -m "cli" -v

# Run the tool (dev mode auto-detected via .git directory)
python yourdad.py             # storage scan (default)
python yourdad.py cpu         # CPU/RAM scan
python yourdad.py all         # both scans

# Build standalone executable
./build_executable.sh          # outputs dist/yourdad

# Enable diagnostic subprocess logging
DIAGNOSTIC_LOGGING=1 python yourdad.py scan storage
```

## Architecture

The data flow is: **CLI → Scanners → Personality → Renderers → Save & Display**.

- **`yourdad.py`** — CLI entry point. Parses args, orchestrates scanning, triggers rendering, saves JSON manifests, opens HTML reports in browser.
- **`scanners/`** — Data collection modules. `storage.py` (file/folder sizes, volume info), `cpu.py` (RAM, memory pressure via `vm_stat`, processes), `mac_libraries.py` (Photos, Mail, Music, Messages, Time Machine libraries), `grading.py` (weighted composite letter grades with type-specific thresholds).
- **`renderers/`** — Output formatting. `terminal.py` (ANSI-colored terminal output), `html.py` (self-contained HTML reports with inline CSS/JS, sortable tables, expandable sections, Finder integration).
- **`personality/`** — `yourdad.py` analyzes scan data and generates contextual dad comments with status levels (ok/warn/critical).
- **`utils/`** — Shared utilities. `formatters.py` (size formatting, status emojis), `path_utils.py` (exclusion rules, Docker/sparse file detection, disk-accurate sizing), `permissions.py` (Full Disk Access detection), `system_info.py` (Mac model/OS/CPU detection), `volumes.py` (volume discovery and selection), `subprocess_utils.py` (diagnostic logging).

## Key Design Decisions

- **Zero external runtime dependencies** — everything uses Python stdlib. Dev dependencies are pytest only.
- **macOS-specific** — relies on `vm_stat`, `system_profiler`, `sysctl`, macOS permission model, and Apple library structures.
- **Dev vs production mode** — auto-detected via `.git` directory presence. Reports go to `test-reports/` (dev) or `~/.dadware/reports/` (prod). Override with `--test-reports`.
- **Graceful degradation** — works without Full Disk Access; skips protected directories and shows setup instructions instead of failing.
- **Disk-accurate sizing** — uses `st_blocks * 512` for Docker containers and sparse files (qcow2, vmdk, etc.) to report actual disk usage, not logical size.
- **Non-recursive allowlist scanning** for Mac libraries — prevents hangs on iCloud/CloudStorage paths. Paths like `Mobile Documents` and `CloudStorage` are explicitly skipped.
- **HTML reports are fully self-contained** — no external assets, can be shared as standalone files.

## Testing

Test markers defined in `pytest.ini`: `unit`, `integration`, `cli`, `slow`, `requires_permissions`. Current tests are CLI smoke tests (version, help, subcommand recognition). CI runs on macOS-latest with Python 3.9.
