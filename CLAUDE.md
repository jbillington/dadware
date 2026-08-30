# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dad Ware is a personality-driven macOS cleanup tool that scans storage and memory, generates letter grades (A-F), and provides dad-style commentary with actionable cleanup advice. It is read-only by design (never deletes files) and uses only the Python standard library at runtime.

## Commands

```bash
# Run tests
./venv/bin/python -m pytest tests/ -v   # create the venv first: python3 -m venv venv && ./venv/bin/pip install -r requirements-dev.txt

# Run tests by marker
./venv/bin/python -m pytest -m "unit" -v
./venv/bin/python -m pytest -m "cli" -v

# Run the tool (dev mode auto-detected via .git directory)
python askdad.py             # storage scan (default)
python askdad.py cpu         # CPU/RAM scan
python askdad.py all         # both scans

# Build standalone executable
./build_executable.sh          # outputs dist/askdad

# Package executable for distribution (zip with README/USER-GUIDE)
./package_for_distribution.sh  # outputs askdad-VERSION-BUILD.zip

# Export memory data from a saved CPU report to CSV
python askdad.py export memory test-reports/cpu_*.json

# Enable diagnostic subprocess logging
DIAGNOSTIC_LOGGING=1 python askdad.py
```

## Architecture

The data flow is: **CLI → Scanners → Personality → Renderers → Save & Display**.

- **`askdad.py`** — CLI entry point. Parses args and dispatches. The scan flows live in `run_storage_scan(args)` and `run_cpu_scan(args)`; `save_and_open_report()` handles rendering, the JSON manifest, and opening the browser. The `all` command is just both scans through those same helpers, so every flag applies uniformly.
- **`scanners/`** — Data collection modules. `storage.py` (file/folder sizes, volume info), `cpu.py` (RAM, memory pressure via `vm_stat`, processes), `mac_libraries.py` (Photos, Mail, Music, Messages, Time Machine libraries), `hidden_storage.py` (app caches under `~/Library/Caches` and `~/Library/Logs`, sized with `du -skx` and labeled with friendly app names), `grading.py` (weighted composite letter grades with type-specific thresholds), `models.py` (typed scan data model).
- **`renderers/`** — Output formatting. `terminal.py` (ANSI-colored terminal output), `html.py` (self-contained HTML reports with inline CSS/JS, sortable tables, expandable sections, Finder integration). `render_html()` is a thin assembler over per-section functions; CSS and JS live in the `REPORT_CSS`/`REPORT_JS` module constants.
- **`personality/`** — `dad.py` analyzes scan data and generates contextual dad comments with status levels (ok/warn/critical).
- **`utils/`** — Shared utilities. `formatters.py` (size formatting, status emojis), `path_utils.py` (exclusion rules, Docker/sparse file detection, disk-accurate sizing), `permissions.py` (Full Disk Access detection), `system_info.py` (Mac model/OS/CPU detection), `volumes.py` (volume discovery and selection), `subprocess_utils.py` (diagnostic logging), `llm_prompt.py` (generates LLM-ready prompts from scan data for AI consultation).

## Key Design Decisions

- **Zero external runtime dependencies** — everything uses Python stdlib. Dev dependencies are pytest only.
- **No AI calls at runtime** — the code was written with AI assistance, but the binary makes no network calls. `utils/llm_prompt.py` *generates* a prompt the user can paste into an LLM; it never calls one.
- **Read-only is a trust constraint, not a feature gap** — the tool never deletes and doesn't even recommend specific deletions; the user makes every cleanup decision.
- **macOS-specific** — relies on `vm_stat`, `system_profiler`, `sysctl`, macOS permission model, and Apple library structures.
- **Dev vs production mode** — auto-detected via `.git` directory presence. Reports go to `test-reports/` (dev) or `~/.dadware/reports/` (prod). Override with `--test-reports`.
- **Graceful degradation** — works without Full Disk Access; skips protected directories and shows setup instructions instead of failing.
- **Disk-accurate sizing** — uses `st_blocks * 512` for Docker containers and sparse files (qcow2, vmdk, etc.) to report actual disk usage, not logical size.
- **Single-pass scanning** — `scan_storage()` walks the tree once via `os.scandir`, reusing each `DirEntry`'s cached stat (one `stat()` per file) and accumulating per-folder file lists and subfolder sizes as it goes. Pass a `stat_result` into `get_file_size()`/`is_sparse_file()` rather than re-statting. Sorts break ties on path so reports are reproducible.
- **Typed scan data with a dict boundary** — scanners and grading pass `FolderInfo`/`FileInfo`/`VolumeInfo`/`StorageScan` objects; `scan_storage()` calls `to_dict()` on the way out so renderers and JSON manifests keep their existing shape. `is_docker`/`is_sparse` keys are emitted only when true, which the manifest format depends on.
- **Escape scan data in HTML** — file paths and process names come off disk and out of `ps`, so everything interpolated into a report goes through `html.escape()`; paths destined for `revealInFinder()` also go through `json.dumps()` for the JS-literal context.
- **Non-interactive by default outside a TTY** — `select_volume()` only prompts when stdin is a terminal, so scheduled runs work; `--volume PATH` is the explicit selector.
- **Only storage devices in the volume picker** — `classify_volume()` tags each mount as `system`/`disk`/`disk_image`/`network`/`read_only` using `hdiutil info -plist` (mounted .dmg installers), `mount` output (network filesystems), and `statvfs` `ST_RDONLY`. Non-scannable kinds are listed as "not shown" rather than dropped silently; `--all-volumes` restores them and an explicit `--volume PATH` always wins. Every detection degrades to "can't tell → still offer it" if the tool is missing, and `/` is exempt from the read-only rule because the macOS system volume is sealed read-only.
- **Non-recursive allowlist scanning** for Mac libraries — prevents hangs on iCloud/CloudStorage paths. Paths like `Mobile Documents` and `CloudStorage` are explicitly skipped.
- **HTML reports are fully self-contained** — no external assets, can be shared as standalone files.

## Product & Distribution

- **Audience:** built by a real Dad for kids and non-technical adults who want to understand *why* their Mac is slow or full; doubles as a learning tool for the Unix filesystem.
- **Beta MVP ships two packages from one codebase** (spec: `docs/roadmap/PERMISSIONS-PLAN.md`): a signed, notarized `.app` in a stapled drag-to-Applications DMG (primary — double-click runs the scan with progress in the browser, no Terminal), and the same scanner as a CLI via a Homebrew tap (technical users and the LLM-harness use case).
- **Later: a native Swift app** wrapping the Python scanner — distributed with Developer ID + notarization, **never** the Mac App Store: App Store sandboxing is incompatible with the Full Disk Access the scanner needs.
- **Landing page:** `site/index.html`, deployed via Vercel.
- **Build pipeline gotcha:** `build/`, `dist/`, and `package/` are gitignored and regenerated by the build scripts — never edit anything in `package/` (wiped on every build); the canonical README is at root.

## Testing

Test markers defined in `pytest.ini`: `unit`, `integration`, `cli`, `slow`, `requires_permissions`. The suite covers grading thresholds and composite scoring (`test_grading.py`), path exclusion and sparse-file detection (`test_path_utils.py`), formatters, storage and CPU scanners, personality output, and CLI smoke tests. CI runs on macOS-latest with Python 3.9.
