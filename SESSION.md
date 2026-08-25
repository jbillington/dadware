# Session

A full log of what was done, newest day first. Every completed item keeps its original
text, including the real-Mac evidence and the reasoning behind each decision - that
detail is the part that is expensive to rediscover.

`BACKLOG.md` holds only work that has not shipped yet.

---

## August 25, 2026

Versioned the project and finished Milestone 1's report-card work. Two real-Mac runs — one
without Full Disk Access, one with — turned up a grading bug that only affects users who have
not granted access, which is most of them. Suite 363 -> 382.

- **Version 0.7.** `VERSION` went from `"0.1-poc"` to `"0.7"`. The jump is deliberate and approximate: the tool went through roughly this many rounds of real iteration without anyone moving the number, and "0.1" had stopped describing it. Nothing was ever tagged or released under the old value, so no published version is being skipped. Build metadata already resolved itself from git and is unchanged.
- **Caches are information, not a grade (report card).** The cache total was a fourth tile in the report card's metric row, sitting beside graded numbers, which read as "here is a problem to act on". It is now a quiet one-line aside that still gives the total, still links to the section, and says outright that it is not counted in the grade. The section copy says what to do in four plain points: a cache is not the app and not your files; they fill back up, so clearing one is safe but temporary; mostly leave them alone; and the one time it stays cleared is when you are deleting the app, because macOS leaves the cache behind. The terminal report carries the short version.
- **Personality comments for caches and snapshots.** Neither touches `status` and neither produces a tip — a full cache is an app working, and calling it a warning would scold someone for something they cannot permanently fix. Found end-to-end while checking the output: a pre-existing `comments[:2]` cap meant the new notes were competing with real findings for those two slots and silently evicting them — with a cache note present, the snapshot note vanished entirely. Notes are now appended after the cap rather than inside it, so "where did my disk go" never costs you a real finding. No unit test would have caught this; each piece passed in isolation. There is a regression test now. Also aligned the personality thresholds with the clutter grade, which went decimal in the re-baseline — the comment and the letter were disagreeing at the margin.
- **Don't grade libraries that Full Disk Access blocked.** Done Aug 25, 2026. A library blocked by FDA does *not* report an error — it reports `status: complete` with **zero bytes**, because the scanner finds nothing at a path it cannot read. The measurement fix's "don't grade what you didn't measure" check looked at status alone and sailed straight past it. **Caught on a real Mac:** the report read "Mac App Libraries **A 100/100**" computed from Music alone at 3.66 GB, while Photos, Messages and Mail were all blocked and silent. Granting FDA and rescanning the same machine measured **36.1 GB across four libraries and graded them B 88/100** — because Messages is an **F at 29.9 GB**. That 29.9 GB was invisible, and the grade said A. The users this hits are the ones who have *not* granted access, which is the default state. Now a silently-empty library we know we lack permission for is treated as unmeasured: the component drops out of the composite and the row reads "needs Full Disk Access to measure". A library reporting its own `error` or `skipped` keeps that status — only the silent zero needed reinterpreting — and a genuinely empty library on a machine with full access (Creative Apps, 0 bytes) is still a true zero and does not block grading.
- **The grade breakdown documents itself.** Nothing in the report explained what any component measured, so "Home Folders Ratio: A" told a reader nothing — an A was meaningless and a D was unactionable. Each row now carries one line saying what it looks at and what share of the grade it carries, so the weights add up in the open rather than only in `docs/GRADING.md`.
- **The 60s library budget is verified on real hardware.** The open question from the measurement fix. With Full Disk Access granted and a 29.9 GB Messages store — the exact case that blew the old 10s budget — all five scanners complete with `scan_status: complete` and no truncation.

## August 24, 2026

The big one. Milestone 1 finished, merged, and twice tested on real hardware. Suite 227 -> 355.

**Summary.** All three hidden-storage scanners landed and merged as `489f2d4`: developer
caches and the generic `~/.*` sweep (1b), then APFS local snapshots (1c), on top of the app
cache scanner from Aug 22 (1a). All three are wired into the HTML report, the terminal report
and the LLM prompt - **display only**, so no letter grade moved. The purgeable-space spike
returned a clean negative, every size switched to decimal units to match Finder, and two real
Mac runs produced nine findings. Two bug fixes also landed, one of which revealed that CI had
never executed a single test.

Later the same day, the grading half followed in two sequential PRs: fix *what* is measured,
then fix *how* it is scored, kept apart so each grade movement is attributable.

**Decided:** caches are information, not a grade. Cache size will never be a grade component.
A cache is an app doing its job, it rebuilds itself, and grading someone down for it would be
scolding them for something they cannot permanently fix. Report the total, explain it, stop
there.

### Grading — measurement, then score

- **Stop grading Mac libraries the scan never measured (the measurement fix).** Done Aug 24, 2026 — branch `fix/mac-library-measurement`. The library scan ran against a 10s budget that could not finish six scanners on a real Mac; the Aug 24 run got through Photos, Music and Messages and skipped Mail, Time Machine and Creative Apps. Two things went wrong with that. The Partial Scan banner under-reported it, because `interrupted_scans` recorded only the scanner whose turn it was when the budget ran out — it named `mail` while three libraries were missing. And the grade was quietly computed from a third of the evidence: skipped libraries are *excluded* from the Mac App Libraries average rather than averaged in as zeros, so a truncated scan never drags the score down, it shrinks what the score is based on — and that subset then carried its full 0.2 of the composite as though all six libraries had been measured. On the test fixture the average was **98.7 from three of six libraries**, propping the composite up to 77; the honest number is 72. The partial measurement was *flattering*, which is the opposite of what the original finding predicted. Fixes: `interrupted_scans` now records every skipped library; the default budget goes to 60s with a `--library-timeout` flag; and if any library is missing the `mac_libraries` component is dropped from the composite entirely, with the remaining weights renormalized to 1.0 and the report card showing "not scored" instead of a letter that doesn't count. The renormalization also fixed a bug nobody was looking for: **`--no-mac-libraries` used to cost 20 points**, because the component kept its 0.2 weight at a score of 0 — a flag meaning "don't look here" was reading as "score zero here". **Not yet verified on real hardware:** the 60s budget was measured on a machine without Full Disk Access, where the protected libraries return instantly (0.4s total). The run that blew the 10s budget had FDA and a 29.9 GB Messages store.
- **Re-baseline the score (the scoring fix).** Done Aug 24, 2026 — branch `grading/score-rebaseline`, stacked on the measurement fix. Three grade changes that each move letters testers have already seen, landed in one commit so grades move once rather than three times. **(1) Decimal thresholds.** `format_size()` went 1000-based on Aug 24 but the grading thresholds stayed 1024-based, so every library was graded against a bucket about 7% larger than its label claimed — a 100 GB Photos library scored as though it were 93.1 GB, and a 10.5 GB Downloads folder did not trip the ">10 GB" rule because that threshold was really 10.74 GB. **(2) Retired the pre-APFS Time Machine check.** `scan_time_machine_backups()` looked only for `/Backups.backupdb`, so on any modern Mac it returned zero and contributed a permanent empty row — while still being a *graded* library, which gave something it could not see a say in the composite. `scanners/snapshots.py` supersedes it, and legacy backup volumes are external drives the volume scanner already covers. **(3) Home folders clutter now counts, at 0.2.** It was computed, displayed, and excluded, so a user could score an F on Downloads and Desktop and watch the top-line grade not move by a single point. It is also the only component measuring something a reader can act on in ten minutes. Free space gave up 0.1 and the library average 0.05 to make room. The clutter ladder was re-spaced 100/85/72/62/40 so C is reachable — it was 100/80/60/40/20, where `problem_count == 2` scored exactly 60 and mapped to D. Re-spacing alone was not enough: `problem_count` could only reach 3, because Downloads had two tiers and Desktop had one, so making C reachable just moved the hole to F. Desktop now uses the same two tiers, and a test pins every letter A–F as reachable. `docs/GRADING.md` updated throughout, including the worked examples. **Grade movement on the test fixture: 77 → 72 → 71.**

### Milestone 1 - Hidden Storage

- **Developer cache bonus + hidden-folder sweep (1b).** Done Aug 24, 2026 — `scan_developer_caches()` (Xcode, container runtimes, package managers, ML model stores) and `sweep_hidden_folders()` (generic `~/.*`, 1 GB floor), combined with 1a behind `scan_hidden_storage()`. Shared deadline and shared "already measured" set so overlaps (`~/Library/Caches/Homebrew`, `~/.docker`) are counted exactly once. `.Trash` is skipped and left to Phase 2. Also fixed the ShipIt/updater naming bug from the real-Mac run in the same pass.
- **Show used/free on the report card (1a-fix).** Done Aug 24, 2026 — the card now carries a headline line under the grade: "196.3 GB used of 250.7 GB — 51.0 GB free (22%)". Display-only; no grade change. Found on the first real-Mac run, Aug 24 2026. `render_report_card()` already computes `used_bytes`, `used_percent` and `free_percent` — it grades Free Space with them — but never prints them. The card says "Free Space: C" without ever telling the user how full the disk is, which is the one number a storage tool most owes them. Display-only, no grade change.
- **Surface hidden caches in the report-card summary (1a-fix).** Done Aug 24, 2026 — fourth stat tile showing the measured cache total, linking to `#hidden-caches` so the tile actually takes you to the section. Omitted entirely when a scan found no caches, so older reports are unchanged. The *grade component* remains deferred to the re-baseline. Same run: 16.4 GB of caches appeared nowhere in the top section, while the header advertised "Reclaimable 8.1%" computed from the top 25 files alone — a smaller and harder-to-act-on story than the caches sitting below it. Add a fourth stat tile now (display-only); the *grade component* stays deferred to the re-baseline below.
- **Fix framework-tail app names (1a-fix).** Done Aug 24, 2026 with 1b — updater frameworks are generic suffixes now, each strip re-checks the lookups (so `com.microsoft.VSCode.ShipIt` resolves to Visual Studio Code), hyphenated updater folders are tidied, and the reverse-DNS prefix is held aside so it can never become the name itself. Same run: `com.microsoft.VSCode.ShipIt`, `com.anthropic.claudefordesktop.ShipIt` and `com.ujam.ujam.ShipIt` all render as "ShipIt" — three unrelated apps, one indistinguishable label. ShipIt is Squirrel's auto-updater, not an app; the heuristic takes the last meaningful component and doesn't know that. Treat `ShipIt` and similar framework tails as generic suffixes so the real app name wins. Same root cause behind `evernote-client-updater` and friends. Worth doing before 1b, which pushes many more folders through the same naming path.
- **Decide decimal vs binary size units.** Decided and done Aug 24, 2026: **decimal**, matching Finder. Research (`docs/research/COMPETITOR-UX-RESEARCH.md`) was one-sided — decimal is the macOS platform convention since Snow Leopard, Apple's own `ByteCountFormatter` defaults to it, DaisyDisk and CleanMyMac both match Finder, and GrandPerspective's help documents our exact bug verbatim ("the size reported by GrandPerspective will be smaller"). `format_size()` and `parse_size()` are now 1000-based. **RAM deliberately stays binary** — Apple calls a 16 GiB module "16 GB" everywhere, so decimal RAM would disagree with Activity Monitor. **Grading thresholds deliberately stay binary** and are documented as such in `docs/GRADING.md`; converting them would move real grades, so it waits for the re-baseline. Original note:  Found by the purgeable spike, Aug 24 2026. `format_size()` is 1024-based but labels output "GB", so we print 47.5 GB where Finder prints 50.98 GB for the same bytes — macOS has been decimal since Snow Leopard. A user checking our report against Finder sees ~7% less and concludes the tool is broken. Three options: match Finder (decimal), keep binary, or keep binary with honest GiB labels. Changes every number in every report, so it needs a product call. Research prompt written: `docs/research/COMPETITOR-UX-RESEARCH-PROMPT.md`.
- **Validation spike: the purgeable-space data source.** Done Aug 24, 2026 via `scripts/purgeable_spike.py` on a 2017 MBP / macOS 13.7.8. **Result: no CLI source diverges from `statvfs`** — `diskutil APFSContainerFree` and `system_profiler free_space_in_bytes` both report exactly the `statvfs` number. The formula is confirmed (Finder 57.77 GB − statvfs 50.98 GB = 6.79 GB, matching Finder's own purgeable figure exactly), but Finder's side of it has no CLI equivalent. Per the plan's fallback, 1c ships snapshot count/age plus the per-snapshot `Purgeable` flag with honest copy, and invents no purgeable number. `tmutil` confirmed working without Full Disk Access. Full write-up in `docs/roadmap/HIDDEN-STORAGE-PLAN.md`. Previous text:  Manual test on real hardware with visible purgeable space — find which CLI source (if any) diverges from `statvfs`. **Gates the next item.** Ready to run: `python3 scripts/purgeable_spike.py` prints `statvfs`, every `diskutil info -plist` byte-count key, `system_profiler SPStorageDataType -json` and both snapshot listings side by side with deltas, then asks for the Finder comparison. Read-only. **Needs a human on a Mac — this is the one Milestone 1 item that cannot be done from a Linux sandbox.**
- **Purgeable + snapshot scanner (1c).** Done Aug 24, 2026 — `scanners/snapshots.py`. `tmutil listlocalsnapshots` (primary; no Full Disk Access needed) plus `diskutil apfs listSnapshots` against `/System/Volumes/Data` for the per-snapshot `Purgeable` flag, `-plist` first with a text-parsing fallback. Reports count, per-snapshot dates and ages, stale count (>2 days, since Time Machine's normal ~24h retention is the system *working*), and the purgeable flag. `com.apple.os.update-*` snapshots are counted but never listed. **No aggregate purgeable estimate and no per-snapshot sizes** — the spike proved the first is unavailable to any CLI, and the second has no single true value under copy-on-write. The report says so in plain language instead. Wired into the HTML report, terminal report and LLM prompt; no grade component (see Wiring). Tested against the verbatim output captured from the spike Mac.

### Fixes

- **Volume picker offered mounted `.dmg` installers** (Jeff, 2026-08-24) — fixed, PR [#5](https://github.com/jbillington/dadware/pull/5), merged to `main` as `84c8729`. `list_volumes()` offered anything under `/Volumes` that passed `os.path.ismount()`, so a mounted installer image sat in the menu next to the real drives — along with network shares and read-only mounts. `classify_volume()` now tags each mount via `hdiutil`/`mount`/`statvfs`, non-storage kinds are listed as "not shown" instead of offered, and `--all-volumes` restores them. **Verified on real hardware** Aug 24, 2026 — a mounted ChatGPT installer was correctly hidden and named from its backing `.dmg`, confirming the `hdiutil` plist parse. Findings and verification steps: `docs/bugs/VOLUME-PICKER-DISK-IMAGES.md`. Closed issue [#3](https://github.com/jbillington/dadware/issues/3).
- **CI had never run a test.** Fixed, PR [#6](https://github.com/jbillington/dadware/pull/6), merged as `5c03a77`. The workflow's pip cache pointed at a `requirements.txt` this project does not have, so every run since the workflow was added failed during setup — before a single test executed. The suite now runs on the macOS runners: **355 passed, 1 skipped**.

### Docs

- **Reorganized the project docs.** `BACKLOG.md` now holds only unshipped work. `SESSION.md`
  became this full day-by-day log. Recorded the caches-are-information decision and the
  deprioritization of snapshots, which together cut the score re-baseline from five grade
  changes to three. Added a backlog item to explore a scoring system built from errands a dad
  would recognize rather than ratios, since three of the four current components sit
  permanently at 100/100.

## August 22, 2026

- **App cache scanner (1a).** Done Aug 22, 2026 — `scanners/hidden_storage.py`. `~/Library/Caches` + `~/Library/Logs` sized per-subfolder via `du -skx` (Python-walk fallback when `du` is missing), bundle IDs resolved to friendly names against the apps installed on this Mac, then a mainstream table, then a reverse-DNS heuristic. Totals stay honest when the entry list is trimmed by the size floor; per-folder and whole-scan time budgets degrade to `partial` rather than failing. Wired for display Aug 24, 2026 (see the Wiring item below) and verified on real hardware: 16.4 GB across 212 folders on the test Mac.

## August 16, 2026

**Planning day.** Wrote two standalone PRDs - `HIDDEN-STORAGE-PLAN.md` and
`PERMISSIONS-PLAN.md` - and reframed phase 1 for a non-technical audience rather than for
people who already know what a cache is. Snapshot detection was promoted into phase 1 on
prevalence research. Reworked the MVP shape into a double-clickable `.app` in a DMG with a
browser progress page. Stopped building the executable on ordinary pushes, and fixed the menu
launcher's stale build and EOF crash.

- **Reconcile the code-review refactor.** Resolved Aug 16, 2026 — the work *was* in an unpushed local checkout and is now on `main` (`db06f88`..`ecc32f4`, plus follow-ups). All of `docs/CODE-REVIEW.md` is implemented: `main()` de-duplicated, single-pass `os.scandir` scanner, `docker.raw`, terminal color globals, `format_size`. `docs/CODE-REVIEW.md` now carries an "implemented" status header.

**Roadmap + docs pass**
- [x] Write Hidden Storage PRD and Permissions & Trust PRD (`docs/roadmap/`)
- [x] Restructure this backlog into sequenced milestones
- [x] Document all current CLI flags in README.md and USER-GUIDE.md (Options sections)
- [x] Re-verify ASKDAD-RENAME-PLAN.md against the current codebase (line refs confirmed; added install.sh stale-echo fix and signed-app coordination notes)

## August 15, 2026

**The code-review refactor.** `main()` had three copies of the same program; they became one.
Split the HTML renderer into per-section functions and escaped all scan data on the way out.
Pinned report behavior with golden-output tests. Fixed home-folder matching to use basenames
instead of loose substrings, and made volume selection non-interactive outside a TTY.
Modernized the PyInstaller build, added signing tooling, derived the build number from git,
and documented the grading rubric.

- **Add type hints.** Done — `scanners/models.py` adds `FileInfo`/`FolderInfo`/`VolumeInfo`/`StorageScan` dataclasses with `to_dict()`, plus type hints across the scanner signatures. Renderers and JSON manifests still receive dicts by design, so the report format is unchanged.
- **Replace `os.listdir()` with `os.scandir()` in the storage scanner.** Done, and it was not minor: reusing each `DirEntry`'s cached stat and folding the second pass into the first took a 40,000-file scan from 3.60s to 1.09s (~8 filesystem syscalls per file down to ~1).

## May 3, 2026

**Repo hygiene pass**
- [x] Delete stale root `index.html` (superseded by `site/index.html` Vercel landing page)
- [x] Delete `dist/yourdad 2` iCloud duplicate
- [x] Move `message-for-max.txt` to `docs/archive/`
- [x] Wipe transient `build/` and `package/` dirs (regenerated by build scripts)
- [x] Consolidate to single root `README.md` ("Ask Dad for Mac" branding)
- [x] Remove broken `[TECHNICAL.md]` link from root README
- [x] Remove stale TECHNICAL.md reference from `scripts/generate_html_readme.py`
- [x] Fix CI workflow `scan cpu` → `cpu` (two occurrences in `.github/workflows/test-and-build.yml`)
- [x] Fix CLAUDE.md stale `scan storage` example, refresh test section, add `llm_prompt.py` and `export memory` subcommand
- [x] Verify `package_for_distribution.sh` no longer references TECHNICAL.md (already fixed)
- [x] Move `BACKLOG.md` from `docs/` to root; add `CONTEXT.md` and `SESSION.md`

## Earlier

- [x] Simplify CLI: flatten `yourdad scan storage` to just `yourdad`
- [x] Move shared flags to top level (no more duplication across subparsers)
- [x] Refactor utils into dedicated modules (formatters, path_utils, subprocess_utils)
- [x] Fix `parse_size()` bug (unit matching checked 'B' before 'MB')
- [x] Fix diagnostic logging (was hardcoded on, now env var)
- [x] Write 101 unit tests
- [x] Update PyInstaller spec with new util modules
- [x] Update menu launcher for new CLI syntax
- [x] Simplify README (170 lines to 40)
- [x] Update all docs for new commands
- [x] Write user guide
- [x] Write competitive comparison doc
- [x] Write testing and launch plan
- [x] Write lightweight TUI plan
- [x] Clean up root directory, archive old files
- [x] Build new executable and ZIP
- [x] Add CLAUDE.md
