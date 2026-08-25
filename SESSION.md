# Session

A running log of what was done, newest day first.

Unshipped work lives in `BACKLOG.md`. Shipped detail — the evidence and the reasoning behind each
decision — lives in `CHANGELOG.md`. This file is just the diary.

---

## August 24, 2026

The big one. Milestone 1 finished, merged, and then twice tested on real hardware.

**Shipped Milestone 1 (Hidden Storage).** `scan_developer_caches()` and `sweep_hidden_folders()` landed as
phase 1b — Xcode, container runtimes, package managers and ML model stores, plus a generic `~/.*` sweep at a
1 GB floor — sharing one deadline and one "already measured" set with 1a so overlaps like
`~/Library/Caches/Homebrew` and `~/.docker` count exactly once. Then `scanners/snapshots.py` as phase 1c:
APFS local snapshots via `tmutil`, with `diskutil apfs listSnapshots` for the per-snapshot `Purgeable` flag.
All three scanners wired into the HTML report, the terminal report and the LLM prompt. Merged as `489f2d4`.

**Ran the purgeable-space spike and got a clean negative.** `scripts/purgeable_spike.py` on a 2017 MBP
compared every candidate source against Finder: `statvfs`, `diskutil APFSContainerFree` and
`system_profiler free_space_in_bytes` all return the identical number, and Finder's differs by exactly its
own stated purgeable figure (57.77 − 50.98 = 6.79 GB, to the cent). The formula was right; the data source
does not exist outside PyObjC. So 1c reports snapshot count, age and the purgeable flag, and invents no
number.

**Switched every size to decimal units.** `format_size()` was doing 1024-based math and labelling it "GB",
so every figure read ~7% under Finder — the single most likely "this tool is broken" trigger. Now 1000-based,
with `parse_size()` moved in lockstep. RAM deliberately stays binary; grading thresholds deliberately stay
binary for now, documented in `docs/GRADING.md`.

**Two real-Mac runs, nine findings logged.** The report card gained a used/free headline and a hidden-cache
stat tile. Fixed the naming bug where `com.microsoft.VSCode.ShipIt`, `com.anthropic.claudefordesktop.ShipIt`
and `com.ujam.ujam.ShipIt` all rendered as "ShipIt" — Squirrel's updater, not an app. Measured 16.4 GB of
caches across 212 folders on the first run, 20.3 GB across 214 on the second, plus one 168-day-old snapshot.

**Fixed the volume picker** (PR #5, issue #3). `list_volumes()` offered anything under `/Volumes` that passed
`os.path.ismount()`, so a mounted `.dmg` installer sat in the menu beside the real drives. `classify_volume()`
now tags each mount via `hdiutil`/`mount`/`statvfs`; non-storage mounts are listed as "not shown" and
`--all-volumes` brings them back. Verified on hardware — a mounted ChatGPT installer was correctly hidden and
named from its backing `.dmg`.

**Discovered CI had never run a single test** (PR #6). The workflow's pip cache pointed at a
`requirements.txt` this project doesn't have, so every run since the workflow was added died during setup,
before pytest was ever invoked. Fixed; the suite now runs on the macOS runners at **355 passed, 1 skipped**.
Suite grew 227 → 355 over the day.

**Made the caches-are-information call.** Cache size will never be a grade component. A cache is an app doing
its job, it rebuilds itself, and grading someone down for it would be scolding them for something they can't
permanently fix. Report the total, explain it, stop there.

**Reorganized the project docs.** `BACKLOG.md` now holds only unshipped work; everything shipped moved to a
new `CHANGELOG.md` with its full text and evidence intact.

## August 22, 2026

**App cache scanner (phase 1a).** `scanners/hidden_storage.py` — `~/Library/Caches` and `~/Library/Logs`
sized per-subfolder with `du -skx`, with a Python-walk fallback when `du` is missing. Bundle IDs resolve to
friendly names against the apps actually installed on the Mac, then a mainstream lookup table, then a
reverse-DNS heuristic. Totals stay honest when the size floor trims the list, and both the per-folder and
whole-scan time budgets degrade to `partial` rather than failing outright.

## August 16, 2026

**Planning day.** Wrote two standalone PRDs — `HIDDEN-STORAGE-PLAN.md` and `PERMISSIONS-PLAN.md` — and
reframed phase 1 for a non-technical audience rather than for people who already know what a cache is.
Snapshot detection was promoted into phase 1 on prevalence research. Reworked the MVP shape into a
double-clickable `.app` in a DMG with a browser progress page. Restructured the backlog into sequenced
milestones, documented every CLI flag in README and USER-GUIDE, re-verified the askdad rename plan against
the codebase, and fixed the menu launcher's stale build and EOF crash. Stopped building the executable on
ordinary pushes.

## August 15, 2026

**The code-review refactor.** `main()` had three copies of the same program; they became one. The storage
scan was rewritten as a single `os.scandir` pass reusing each `DirEntry`'s cached stat — a 40,000-file scan
went from 3.60s to 1.09s, roughly 8 filesystem syscalls per file down to about 1. Added a typed data model
(`FileInfo`/`FolderInfo`/`VolumeInfo`/`StorageScan`) with a `to_dict()` boundary so renderers keep receiving
dicts. Split the HTML renderer into per-section functions and escaped all scan data on the way out. Pinned
report behavior with golden-output tests. Fixed home-folder matching to use basenames instead of loose
substrings, and made volume selection non-interactive outside a TTY. Modernized the PyInstaller build, added
signing tooling, derived the build number from git, and documented the grading rubric.

## May 3, 2026

**Repo hygiene.** Consolidated to a single root README under the "Ask Dad for Mac" name, deleted the stale
root `index.html` and an iCloud duplicate of the built binary, wiped transient `build/` and `package/` dirs,
archived `message-for-max.txt`, fixed the CI workflow's `scan cpu` → `cpu` invocation, and moved `BACKLOG.md`
to the root alongside new `CONTEXT.md` and `SESSION.md`.
