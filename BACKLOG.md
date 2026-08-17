# Backlog & Roadmap

**Last Updated:** August 16, 2026

Milestones are in execution order — each one is shippable on its own. Detailed specs live in `docs/roadmap/`: `HIDDEN-STORAGE-PLAN.md` and `PERMISSIONS-PLAN.md` are the two active PRDs. Check the box when done.

---

## Milestone 1 — Hidden Storage, Phase 1

The scan learns to see what it currently can't: app caches, hidden folders, purgeable space, and snapshots — all folded into the existing storage report. Needs no new permissions, pure Python, ships value immediately. Spec: `docs/roadmap/HIDDEN-STORAGE-PLAN.md`.

- [ ] **App cache scanner (1a).** `~/Library/Caches` + `~/Library/Logs`, sized per-subfolder via `du -skx`, with bundle-ID → friendly app name mapping ("Spotify — 8.2 GB").
- [ ] **Developer cache bonus + hidden-folder sweep (1b).** Allowlist (Xcode, Docker/Colima/OrbStack, npm/Gradle/…) plus the generic `~/.*` sweep with a 1 GB reporting floor.
- [ ] **Validation spike: the purgeable-space data source.** Manual test on real hardware with visible purgeable space — find which CLI source (if any) diverges from `statvfs`. **Gates the next item.**
- [ ] **Purgeable + snapshot scanner (1c).** `tmutil listlocalsnapshots` / `diskutil apfs listSnapshots /System/Volumes/Data`, aggregate purgeable estimate, `com.apple.os.update-*` filtered.
- [ ] **Wiring.** New grade components, personality comments, report sections (in the existing single report), `llm_prompt.py` data.

## Milestone 2 — Identity & Permission UX Foundation

Everything that must be right *before* the first signed build, because macOS keys permission grants to bundle ID + signature — the app's identity has to be final first.

- [ ] **Rename `yourdad` → `askdad`.** Plan in `docs/roadmap/ASKDAD-RENAME-PLAN.md` (~1 hour). **Must land before signing** — it fixes the bundle ID (`com.dadware.askdad`) and executable name that permission grants will be keyed to forever.
- [ ] **Permission UX foundation.** Prompt choreography (all folder dialogs up front, with context), per-folder TCC denial detection in `utils/permissions.py`, honest-denial copy in both renderers, FDA deep link. Spec: `PERMISSIONS-PLAN.md` Phase 1.

## Milestone 3 — Signed Beta Packages

The MVP ships as two packages from one codebase: a double-clickable `.app` in a DMG (primary, for beta testers) and a CLI (Homebrew + website, for technical users and LLM-harness use). Spec: `PERMISSIONS-PLAN.md` Phase 2.

- [ ] **Apple Developer Program enrollment** ($99/yr) + Developer ID Application certificate.
- [ ] **`.app` bundle + app mode.** PyInstaller onedir `.app`, `Info.plist` usage strings, browser progress page via meta-refresh. (Non-interactive volume selection is already done — `select_volume()` auto-selects when there's no TTY as of the Aug 2026 refactor.)
- [ ] **Sign, notarize, package.** Tooling exists but has never run: `sign_and_notarize.sh` + `entitlements.plist` script the codesign/notarytool flow, CI has a tag-gated universal2 build, and `docs/BUILDING.md` lists the required secrets. Remaining: get the Developer ID cert, extend the script/`package_for_distribution.sh` to produce the stapled drag-to-Applications DMG and the Homebrew CLI package, then run it all for the first time.
- [ ] **Homebrew formula + tap.** `Formula/askdad.rb` currently has a placeholder URL and stale syntax; needs real release URL and a `homebrew-tap` repo.
- [ ] **Clean-machine test matrix.** Intel + Apple Silicon; Sonoma/Sequoia/Tahoe; verify no Gatekeeper warnings, prompts attribute to the app, and the Tahoe launch bug (below) is resolved.
- [ ] **GitHub Release + screenshots.** Tag the release, upload both packages, capture report-card/terminal/breakdown screenshots for the landing page and Reddit.

## Milestone 4 — Full-Report Experience

- [ ] **First-run onboarding.** HTML welcome page: read-only promise, what macOS will ask, with-vs-without-FDA comparison, guided FDA walkthrough. Spec: `PERMISSIONS-PLAN.md` Phase 3.
- [ ] **Trash scanner.** `~/.Trash` + `/Volumes/*/.Trashes` (FDA-gated, so it depends on the onboarding/FDA flow). Spec: `HIDDEN-STORAGE-PLAN.md` Phase 2.

## Milestone 5 — Beta Launch

Per `docs/TESTING-AND-LAUNCH.md`: family first, then friends on unseen Macs, then Reddit (r/macapps). Launch waits for Milestone 3 — the signed DMG removes the security-warning friction that plan was written around.

## Feature Pool (unscheduled, pull as capacity allows)

- [ ] **`--json` flag.** Scan results as JSON to stdout. Elevated in value by the CLI channel's LLM-harness positioning; also the prerequisite for the MCP server. Low effort.
- [ ] **`--prompt` flag.** Output the LLM-ready prompt (from `utils/llm_prompt.py`) to stdout for agents.
- [ ] **Redesign report card layout.** Component grades first, overall grade at the bottom, one-line explanation per component.
- [ ] **Expand personality comments.** More variety; the current set repeats quickly. New hidden-storage comments from Milestone 1 help.
- [ ] **Report history.** `askdad history` — list past reports with dates and grades.
- [ ] **Lightweight TUI.** Curses menu/progress/summary for the CLI channel. Deprioritized: the `.app` + browser-progress path now serves non-technical users, so this is a CLI-channel nicety. Plan: `docs/roadmap/LIGHTWEIGHT-TUI-PLAN.md`.

## Code Quality

- [x] **Reconcile the code-review refactor.** Resolved Aug 16, 2026 — the work *was* in an unpushed local checkout and is now on `main` (`db06f88`..`ecc32f4`, plus follow-ups). All of `docs/CODE-REVIEW.md` is implemented: `main()` de-duplicated, single-pass `os.scandir` scanner, `docker.raw`, terminal color globals, `format_size`. `docs/CODE-REVIEW.md` now carries an "implemented" status header.
- [x] **Add type hints.** Done — `scanners/models.py` adds `FileInfo`/`FolderInfo`/`VolumeInfo`/`StorageScan` dataclasses with `to_dict()`, plus type hints across the scanner signatures. Renderers and JSON manifests still receive dicts by design, so the report format is unchanged.
- [x] **Replace `os.listdir()` with `os.scandir()` in the storage scanner.** Done, and it was not minor: reusing each `DirEntry`'s cached stat and folding the second pass into the first took a 40,000-file scan from 3.60s to 1.09s (~8 filesystem syscalls per file down to ~1).
- [ ] **Standardize scanner return formats.** Partially done. Storage is modeled in `scanners/models.py`; the CPU scanner's process dicts were deliberately left unmodeled, since converting them reaches into the HTML renderer's process tables for little gain. Worth finishing if the CPU report grows.
- [ ] **Two grading decisions left open** (see `docs/GRADING.md`): the home-folder clutter grade can never return a C (`problem_count == 2` scores exactly 60, a D), and that grade is excluded from the composite, so an F there moves the top-line grade by zero. Both change grades users already see, so they need a product call rather than a code fix.

## Bugs

- [ ] **Launch fails on macOS Tahoe 26.4.1 / Apple Silicon** (Micah Evans, 2026-04-13). `RBSRequestErrorDomain Code=5`, quarantined-binary symptoms. Expected root cause: unsigned binary under Tahoe's tightened Gatekeeper. **Expected fix: Milestone 3 signing** — keep open until verified on a Tahoe machine. Details preserved in git history of this file.

## Future (post-beta)

- [ ] **Duplicate file detection.** By hash; the old v0.2 idea. 20-30 hours.
- [ ] **Native Swift app.** Real UI wrapping the Python scanner — the CleanMyMac competitor. Must keep the bundle ID from Milestone 2 so permission grants carry over. Permission implications already covered in `PERMISSIONS-PLAN.md` future-work.
- [ ] **MCP server.** Expose scans as MCP tools for AI agents. Depends on `--json`.

## Dropped / Superseded

- ~~**Test the security warning flow** (right-click → Open for unsigned builds)~~ — obsolete: the MVP ships signed and notarized, so there is no security warning to test. Replaced by the Milestone 3 clean-machine matrix.
- ~~**Sign and ship as `.app`** (single backlog line)~~ — expanded into `PERMISSIONS-PLAN.md` Phases 1-3 / Milestones 2-3.
- ~~**Test executable on clean Mac** (standalone item)~~ — folded into the Milestone 3 clean-machine matrix.

## Done

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
