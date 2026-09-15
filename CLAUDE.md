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

# Show per-phase timings (also on with DIAGNOSTIC_LOGGING=1)
python askdad.py --timings
```

## Architecture

The data flow is: **CLI → Scanners → Personality → Renderers → Save & Display**.

- **`askdad.py`** — CLI entry point. Parses args and dispatches. The scan flows live in `run_storage_scan(args)` and `run_cpu_scan(args)`; `save_and_open_report()` handles rendering, the JSON manifest, and opening the browser. The `all` command is just both scans through those same helpers, so every flag applies uniformly.
- **`scanners/`** — Data collection modules. `storage.py` (file/folder sizes, volume info), `cpu.py` (RAM, memory pressure via `vm_stat`, processes), `mac_libraries.py` (Photos, Mail, Music, Messages, Time Machine libraries), `hidden_storage.py` (app caches under `~/Library/Caches` and `~/Library/Logs`, sized with `du -skx` and labeled with friendly app names), `trash.py` (`~/.Trash` plus each volume's `.Trashes/<uid>`, with item counts, ages, and a first-class "blocked by macOS" answer), `grading.py` (weighted composite letter grades with type-specific thresholds), `models.py` (typed scan data model).
- **`renderers/`** — Output formatting. `terminal.py` (ANSI-colored terminal output), `html.py` (self-contained HTML reports with inline CSS/JS, sortable tables, expandable sections, Finder integration). `render_html()` is a thin assembler over per-section functions; CSS and JS live in the `REPORT_CSS`/`REPORT_JS` module constants.
- **`personality/`** — `dad.py` analyzes scan data and generates contextual dad comments with status levels (ok/warn/critical).
- **`utils/`** — Shared utilities. `timing.py` (run wall clock and per-phase timers), `formatters.py` (size formatting, status emojis), `path_utils.py` (exclusion rules, Docker/sparse file detection, disk-accurate sizing), `permissions.py` (Full Disk Access detection), `system_info.py` (Mac model/OS/CPU detection), `volumes.py` (volume discovery and selection), `subprocess_utils.py` (diagnostic logging), `llm_prompt.py` (generates LLM-ready prompts from scan data for AI consultation).

## Key Design Decisions

- **Zero external runtime dependencies** — everything uses Python stdlib. Dev dependencies are pytest only.
- **No AI calls at runtime** — the code was written with AI assistance, but the binary makes no network calls. `utils/llm_prompt.py` *generates* a prompt the user can paste into an LLM; it never calls one.
- **Read-only is a trust constraint, not a feature gap** — the tool never deletes and doesn't even recommend specific deletions; the user makes every cleanup decision.
- **macOS-specific** — relies on `vm_stat`, `system_profiler`, `sysctl`, macOS permission model, and Apple library structures.
- **Dev vs production mode** — auto-detected via `.git` directory presence. Reports go to `test-reports/` (dev) or `~/.dadware/reports/` (prod). Override with `--test-reports`.
- **Graceful degradation** — works without Full Disk Access; skips protected directories and shows setup instructions instead of failing.
- **Disk-accurate sizing** — uses `st_blocks * 512` for Docker containers and sparse files (qcow2, vmdk, img, etc.) to report actual disk usage, not logical size. `.img` was missing from `VIRTUAL_DISK_EXTENSIONS` until Sep 2026, so a VM disk fell through to the ratio heuristic (sparse only when logical > 10x actual) and reported its provisioned size: on a real Mac, Claude Desktop's `rootfs.img` showed 10 GB while occupying 8.5 GB, as the report's largest single item.
- **Single-pass scanning** — `scan_storage()` walks the tree once via `os.scandir`, reusing each `DirEntry`'s cached stat (one `stat()` per file) and accumulating per-folder file lists and subfolder sizes as it goes. Pass a `stat_result` into `get_file_size()`/`is_sparse_file()` rather than re-statting. Sorts break ties on path so reports are reproducible.
- **The walk stays on one filesystem** — `scan_storage()` takes the scan root's device set from `get_scan_device_ids()` and skips any directory entry on another device, so scanning `/` no longer descends into mounted external and Time Machine drives. Not a name check on `/Volumes`: that misses other mount points and would break an explicit `--volume /Volumes/BACKUP`, which stays supported because the set is derived from the chosen root. **The set is not a single device**, because the macOS startup disk is two — a sealed system volume at `/` and a writable data volume at `/System/Volumes/Data`, joined by firmlinks, so `/Users` has a different `st_dev` from `/`; picking either half allows both, or a scan of `/` would skip the entire home directory. Directories are the only place a mount point appears, so the check costs one stat per directory and none per file. A directory whose device can't be read is still scanned. `scanners/hidden_storage.py` gets the same guarantee free from `du -skx`.
- **A volume that isn't home's gets its own report** — `run_storage_scan()` asks `is_on_scan_volume()` whether the chosen volume is the one the home folder lives on, and records the answer as `scan_data['scan_scope']` (`'home_volume'` / `'other_volume'`). On another volume the scan stops after the walk: no home breakdown, no permission choreography or Full Disk Access, no Mac libraries, hidden caches or snapshots, and none of those keys in `scan_data`. `render_html()` then assembles a **different report** — `render_volume_summary()` (free space, folder and file totals, no grade at all), the folder chart with `split_home=False`, the files table, next steps and the AI prompt. Not the full report with sections switched off: three of the four graded components measure the home folder and Apple's libraries, which are not on that drive, and a grade built from what is left answers a question the user didn't ask. Both reports call the same section functions, so neither is a pile of conditionals about the other. The rule is by *disk*, not by path, so `--volume ~/Downloads` still gets the whole report.
- **One row per folder, ranked on size — no allowlist** — the folder chart is the report's answer to "what is big?", so what appears in it is decided by size and by where the folder lives, nothing else. Two rules make that true. **Roll-up:** the walk's buckets are keyed at depth ≤ 2 and do *not* nest, so `Downloads` held only its loose files while `Downloads/archive` was a separate row; `_FolderBuckets.top_folders(rollup=True)` folds depth-2 buckets into the top-level folder they sit in, so a row is a whole folder. The volume walk keeps its raw depth-2 rows — `opt/homebrew` already absorbs everything below it, and rolling up would coarsen it to `opt`. **No allowlist:** `merge_home_folders()` used to keep seven folder names and discard the rest of home, so a 40 GB `~/Projects` never reached the report at all; every folder is kept now, and `render_folder_chart()` takes the top 10 per bar. Which bar is a path question — under `scan_data['home_path']` or not — not a name question, and the home recorded is *the home that was walked*, so a saved manifest opened on another Mac still files its rows correctly. `is_under()` does the prefix test, because `startswith` says `/Users/dad2` is inside `/Users/dad`.
- **The home breakdown rides along with the volume walk** — scanning `/` at depth 2 buckets everything under `/Users/<user>` into one row, which used to be fixed by walking `~` a second time (on a real Mac, 244,324 of 276,353 items read twice). `scan_storage(..., home_path=~)` now fills a second set of `_FolderBuckets` rooted at home during the same walk and returns them as `result['home_breakdown']`, which `run_storage_scan()` merges and drops. A home directory the walk never reached (another volume, a denied parent) omits the key, and the separate walk still runs as the fallback.
- **Typed scan data with a dict boundary** — scanners and grading pass `FolderInfo`/`FileInfo`/`VolumeInfo`/`StorageScan` objects; `scan_storage()` calls `to_dict()` on the way out so renderers and JSON manifests keep their existing shape. `is_docker`/`is_sparse` keys are emitted only when true, which the manifest format depends on.
- **Escape scan data in HTML** — file paths and process names come off disk and out of `ps`, so everything interpolated into a report goes through `html.escape()`; paths destined for `revealInFinder()` also go through `json.dumps()` for the JS-literal context.
- **Non-interactive by default outside a TTY** — `select_volume()` only prompts when stdin is a terminal, so scheduled runs work; `--volume PATH` is the explicit selector.
- **Only storage devices in the volume picker** — `classify_volume()` tags each mount as `system`/`disk`/`disk_image`/`network`/`read_only` using `hdiutil info -plist` (mounted .dmg installers), `mount` output (network filesystems), and `statvfs` `ST_RDONLY`. Non-scannable kinds are listed as "not shown" rather than dropped silently; `--all-volumes` restores them and an explicit `--volume PATH` always wins. Every detection degrades to "can't tell → still offer it" if the tool is missing, and `/` is exempt from the read-only rule because the macOS system volume is sealed read-only.
- **A blocked measurement is reported, never a zero** — `~/.Trash` is TCC-protected, and `du` prints a cheerful `0` for a folder it cannot read. `scanners/trash.py` runs the `utils/permissions.py` access probe *first* and lets its answer stand: a blocked location gets `status: 'no_permission'` and stays out of the totals rather than adding a zero to them. It also adds no folder row — a bar cannot draw "unknown", and a 0 B row reads as an empty Trash — so `render_permission_warning()` states the gap in words instead. `item_count` and `oldest_age_days` are `None`, not `0`, for the same reason.
- **The Trash is a folder, so it goes in the folder chart** — it is not a section, an aside or an explainer. `merge_trash_folders()` puts each measured location into `top_folders` as an ordinary row that sorts on size with everything else, and `'Trash'` is in `render_folder_chart()`'s `home_folder_names` so the home one lands in the Home Folders bar. On a real Mac it was 14.3 GB, larger than Downloads and larger than anything else in the report, and it appeared in no folder list at all because `should_exclude()` drops every dotfile before the walk sees it. Its bytes join `home_folders_total_bytes` too, or the chart's segments would not add up to the total beside them. Nothing is double-counted: the walk never reached these paths.
- **The Trash is not graded** — the plan proposed a letter-grade ding over 5 GB. Those bytes already sit inside the Free Space grade, which carries half the composite, so a Trash component would count the same gigabytes twice, and any new component re-baselines every existing tester's grade.
- **Apps are one item, and `/Applications` is scanned** — `EXCLUDED_ROOT_DIRS` now holds only the sealed OS (`System`, `usr`, `bin`, `sbin`, `private`, `var`): `/System` is read-only even to root, and a report that invites cleaning the others breaks Macs. `/Applications` and `/Library` were on that list and are not any more — they are the two biggest things at the top of the disk a person can act on, and excluding them left "Other Folders" with `/opt/homebrew` and little else. Un-excluding `/Applications` alone would have reported ~0, because `should_exclude()` also dropped every `.app`; the walk now calls `is_app_bundle()` and measures the bundle whole via `app_bundle_size()` instead of descending into it, then hands it to the same accounting a file gets (`_record_item()`), so an app ranks against files and "a 6 GB app you never open" can appear at all. **Sizing them is one `du -skx` per folder of apps, not per app:** `app_bundle_sizes()` passes every bundle in a directory as arguments to a single `du`, which is C-speed and replaces a few hundred thousand `stat()` calls — the first Python-walk version cost 20s of a 53s scan on an M4. `app_bundle_size()` (scandir, one `stat()` per file, blocks straight off the stat) is the per-path fallback when `du` is missing or silent about a path. Both report disk blocks, so the two paths agree. The scan prints `→ sized N apps in X.Xs` so the cost stays visible. `FileInfo.is_bundle` marks them; Docker and sparse flags are not set on a bundle, since both describe how a *file* was sized.
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
