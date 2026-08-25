# Changelog

Shipped work, newest first. `BACKLOG.md` carries only what has *not* shipped — if it is done, it moves here.

Entries keep their full original text, including the real-Mac evidence and the reasoning behind each
decision. That detail is deliberately preserved rather than summarized: several of these record *why*
something was done a particular way, or deliberately not done, which is the part that is expensive to
rediscover. `git log` has the commit-level record; this file has the reasons.

## Unreleased

`VERSION` is still `0.1-poc` — nothing here has been tagged or released yet.

### Milestone 1 — Hidden Storage, Phase 1 (August 2026)

The scan learned to see app caches, hidden folders and APFS local snapshots. All three scanners are wired
into the HTML report, the terminal report and the LLM prompt **for display only** — no grade component and
no personality comments, so no letter grade has moved. Suite 227 → 355.

- **App cache scanner (1a).** Done Aug 22, 2026 — `scanners/hidden_storage.py`. `~/Library/Caches` + `~/Library/Logs` sized per-subfolder via `du -skx` (Python-walk fallback when `du` is missing), bundle IDs resolved to friendly names against the apps installed on this Mac, then a mainstream table, then a reverse-DNS heuristic. Totals stay honest when the entry list is trimmed by the size floor; per-folder and whole-scan time budgets degrade to `partial` rather than failing. Wired for display Aug 24, 2026 (see the Wiring item below) and verified on real hardware: 16.4 GB across 212 folders on the test Mac.
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

### Code quality

- **Reconcile the code-review refactor.** Resolved Aug 16, 2026 — the work *was* in an unpushed local checkout and is now on `main` (`db06f88`..`ecc32f4`, plus follow-ups). All of `docs/CODE-REVIEW.md` is implemented: `main()` de-duplicated, single-pass `os.scandir` scanner, `docker.raw`, terminal color globals, `format_size`. `docs/CODE-REVIEW.md` now carries an "implemented" status header.
- **Add type hints.** Done — `scanners/models.py` adds `FileInfo`/`FolderInfo`/`VolumeInfo`/`StorageScan` dataclasses with `to_dict()`, plus type hints across the scanner signatures. Renderers and JSON manifests still receive dicts by design, so the report format is unchanged.
- **Replace `os.listdir()` with `os.scandir()` in the storage scanner.** Done, and it was not minor: reusing each `DirEntry`'s cached stat and folding the second pass into the first took a 40,000-file scan from 3.60s to 1.09s (~8 filesystem syscalls per file down to ~1).

## Earlier

**August 16, 2026 — roadmap + docs pass**
- [x] Write Hidden Storage PRD and Permissions & Trust PRD (`docs/roadmap/`)
- [x] Restructure this backlog into sequenced milestones
- [x] Document all current CLI flags in README.md and USER-GUIDE.md (Options sections)
- [x] Re-verify ASKDAD-RENAME-PLAN.md against the current codebase (line refs confirmed; added install.sh stale-echo fix and signed-app coordination notes)

**May 3, 2026 — repo hygiene pass**
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

**Earlier**
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
