# Backlog & Roadmap

**Last Updated:** August 24, 2026

Milestones are in execution order — each one is shippable on its own. Detailed specs live in `docs/roadmap/`: `HIDDEN-STORAGE-PLAN.md` and `PERMISSIONS-PLAN.md` are the two active PRDs.

**This file holds only unshipped work.** When something ships it moves to `CHANGELOG.md` with its full text and evidence intact — so the backlog stays a to-do list rather than a history.

---

## Milestone 1 — Hidden Storage, Phase 1

The scan learns to see what it currently can't: app caches, hidden folders, purgeable space, and snapshots — all folded into the existing storage report. Needs no new permissions, pure Python, ships value immediately. Spec: `docs/roadmap/HIDDEN-STORAGE-PLAN.md`.

**All three scanners (1a, 1b, 1c) have shipped** and are verified on real hardware, and the grading work that had been deferred behind them shipped Aug 24, 2026 — see `CHANGELOG.md`. What is left of this milestone is copy and presentation.

**Caches are information, not a grade.** Decided Aug 24, 2026: cache size will never be a grade component and stays low-key on the report card. A cache is not mess — it is an app doing its job, and it comes back on its own. Grading someone down for it would be telling them off for something that isn't their fault and that they can't permanently fix. We report the total, we explain what it is, and we stop there. This removes the single biggest reason the grade re-baseline was ever a large piece of work.

**This milestone is done.** The scanners, the grading work and the report-card copy all
shipped Aug 24-25, 2026 — see *How it shipped* below and `CHANGELOG.md` for what moved and
why. The deferred items below were never blocking and remain open.

### Milestone 1 is closed

Everything in this milestone has shipped — the three scanners, the grading work, and the
report-card copy. See `CHANGELOG.md`. What is left below is deferred work that was
explicitly not blocking, plus the `Feature Pool` item on rethinking the metrics entirely.

### How it shipped

Four changes, in this order, on stacked branches — each kept separate so that when a letter
moved you could tell which change moved it:

1. **Measurement fix** — changed *what* is measured.
2. **Score re-baseline** — changed *how* it is scored.
3. **Version 0.7 + report-card copy** — no grade impact.
4. **Full Disk Access fix + per-metric documentation** — found by testing the real report.

Composite on the test fixture moved **77 → 72 → 71**. On a real Mac with Full Disk Access
granted the report reads **83/100**. **Cut one release, not four** — testers should be told
once that a letter may have moved for a disk that has not changed.

### Deferred — worth doing, not blocking Milestone 1

- [ ] **Snapshot size: check what `diskutil apfs listSnapshots -plist` actually returns.** Low priority — snapshots are the least important part of the milestone and the report is already honest about what it can't measure. Raised by the user on the Aug 24 test run — "I only have 1 local snapshot, I'd expect it to tell me size." Fair challenge. The copy-on-write objection is about attributing shared blocks *between* snapshots; with exactly one, "what would I get back by deleting it" is a well-formed question and the blanket no-sizes rule is weaker than stated. Two follow-ups, in order:
  1. **Cheap check first:** `scanners/snapshots.py::_parse_diskutil_plist()` only reads `SnapshotName` and `Purgeable`. Nobody has looked at the rest of the plist. Run `diskutil apfs listSnapshots -plist /System/Volumes/Data` on a Mac and dump every key. If a size key exists, the rule was over-broad and single-snapshot sizing should ship.
  2. **If it doesn't:** the size genuinely needs elevated access (DaisyDisk, the only tool that shows it, asks for admin and still labels its figures "for reference only"). Fall back to pointing the user at Finder → Get Info, which shows a purgeable total — and with one snapshot, say that most of it is probably this one. That is honest and still answers the question.
- [ ] **No next step for a bad library grade.** Messages graded **F at 29.9 GB** with nothing telling the user what to do about it — and a further 8.2 GB sits in its cache. A letter grade without an action is just a scolding. Needs per-library advice (Messages: attachment management and "Keep Messages" retention in Settings; Photos: iCloud optimization; Mail: rebuild/attachment cleanup), in the same read-only advisory framing as the snapshot section. Note this is about *graded* libraries, which caches are not.
- [ ] **Orphaned caches: cross-reference cache folders against installed apps.** `build_app_name_index()` already knows what is installed, so flagging "caches belonging to apps you no longer have" is nearly free — and it is the one cache category that is genuinely worth clearing for good, which makes it the natural follow-on to the guidance copy above.
- [ ] **Optimize the LLM prompt for the storage scan.** `utils/llm_prompt.py::generate_storage_prompt()` has grown organically — it now carries volume info, folders, files, libraries, hidden caches and snapshots, with a fixed six-question tail written before most of that data existed. Worth a pass for what an LLM can actually act on: the questions should reflect the new sections, and the prompt should state what the scan could *not* see (protected folders, purgeable space, skipped libraries) so the model does not reason from a total it assumes is complete.
- [ ] **Research how CleanMyMac / DaisyDisk / Sweep handle units, purgeable and cache-safety copy.** Prompt ready at `docs/research/COMPETITOR-UX-RESEARCH-PROMPT.md`. **Much narrower than when it was written:** units are decided (decimal), purgeable was settled by the spike, and the cache-safety message is now decided too. Nothing live depends on it. Would still extend `docs/COMPETITIVE-COMPARISON.md`, which currently covers only ncdu and htop.

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
- [ ] **No Intel runner exists in CI any more — the universal2 build cannot be verified automatically.** Found Aug 26, 2026 while fixing the Python 3.9 leg. GitHub has retired the `macos-13` image; `actions/runner-images` now lists only `macos-14`, `macos-15` and `macos-26`, all Apple Silicon. The test matrix was fine to move (both legs run on `macos-15`, and `setup-python` publishes darwin-arm64 builds of 3.9), because the runtime code is stdlib and subprocess calls with no architecture coupling. **The tag-gated universal2 PyInstaller build is the part that genuinely cannot be checked this way** — a cross-compiled `x86_64` slice that no CI runner can execute. Options: verify the Intel slice by hand on a real Intel Mac as part of the clean-machine matrix above (cheapest, and that matrix already calls for one), run a self-hosted Intel runner, or drop the Intel slice and ship Apple Silicon only. **Do not ship a signed universal2 binary whose Intel half has never been run.**
- [ ] **GitHub Release + screenshots.** Tag the release, upload both packages, capture report-card/terminal/breakdown screenshots for the landing page and Reddit.
- [ ] **Nothing has ever been tagged — `v0.7` exists only as a constant.** `VERSION` moved from `0.1-poc` to `0.7` on Aug 24, 2026, and `docs/TESTING-AND-LAUNCH.md` carries the `git tag -a v0.7` command ready to run, but no tag exists in the repo and no release has been cut. Worth knowing *why it has not been done yet*: tagging triggers the universal2 build job, which is the one thing CI can no longer verify (above), and the askdad rename must land before the first signed build because macOS keys permission grants to bundle ID. So the honest sequence is rename → Developer ID → Intel verification → tag, not tag-now.

## Milestone 4 — Full-Report Experience

- [ ] **First-run onboarding.** HTML welcome page: read-only promise, what macOS will ask, with-vs-without-FDA comparison, guided FDA walkthrough. Spec: `PERMISSIONS-PLAN.md` Phase 3.
- [ ] **Trash scanner.** `~/.Trash` + `/Volumes/*/.Trashes` (FDA-gated, so it depends on the onboarding/FDA flow). Spec: `HIDDEN-STORAGE-PLAN.md` Phase 2.

## Milestone 5 — Beta Launch

Per `docs/TESTING-AND-LAUNCH.md`: family first, then friends on unseen Macs, then Reddit (r/macapps). Launch waits for Milestone 3 — the signed DMG removes the security-warning friction that plan was written around.

## Feature Pool (unscheduled, pull as capacity allows)

- [ ] **`--json` flag.** Scan results as JSON to stdout. Elevated in value by the CLI channel's LLM-harness positioning; also the prerequisite for the MCP server. Low effort.
- [ ] **`--prompt` flag.** Output the LLM-ready prompt (from `utils/llm_prompt.py`) to stdout for agents.
- [ ] **Redesign report card layout.** Component grades first, overall grade at the bottom, one-line explanation per component.
- [ ] **Explore a scoring system a normal person can read (and want to beat).** Exploratory — find the metrics first, spec later. The current Grade Breakdown isn't intuitive. A real run shows **Free Space D (69/100)** sitting next to **Home Folders Ratio A (100/100)**, **Home Folders Clutter A (100/100)** and **Mac App Libraries A (100/100)**: the top-line grade is effectively just the free-space number, and the other three are decoration. Three things are wrong with it:
  - **The names are internal jargon.** "Home Folders Ratio" and "Home Folders Clutter" mean nothing to a non-technical reader, and nothing distinguishes them from each other. They describe how we compute, not what the user has.
  - **Three of four components are pinned at 100/100**, so they carry no information. A breakdown where nothing ever moves reads as a scoreboard nobody is playing.
  - **A component can score A on almost no evidence.** On that run "Mac App Libraries A" was computed from Music alone (3.7 GB) because the rest were skipped — see the time-budget item in Milestone 1.

  Explore metrics built from things a dad would actually check when fixing someone's computer, and that pay off in ten minutes: **Downloads folder**, **Trash**, **Desktop clutter**, **screenshots**, **big apps never opened**, **duplicate files**, **stale installers**. The current components are ratios; these are errands — each one is a concrete chore with a visible before-and-after, which is what makes it gameable. Points for clearing Downloads, a streak for keeping the Desktop clean, a "you got 12 GB back" number afterwards. Ratios can't be gamified; errands can.

  Pairs with the report-card layout redesign above. Worth exploring **before** the Milestone 1 score re-baseline hardens the current components any further.
- [ ] **Expand personality comments.** More variety; the current set repeats quickly. New hidden-storage comments from Milestone 1 help.
- [ ] **Report history.** `askdad history` — list past reports with dates and grades.
- [ ] **Lightweight TUI.** Curses menu/progress/summary for the CLI channel. Deprioritized: the `.app` + browser-progress path now serves non-technical users, so this is a CLI-channel nicety. Plan: `docs/roadmap/LIGHTWEIGHT-TUI-PLAN.md`.

## Code Quality

- [ ] **Move the analysis out of `personality/` into `scanners/grading.py`; personas become pure voice.** Decided Aug 28, 2026 alongside the rename-plan scope revision. `personality/dad.py` (post-rename; today `personality/yourdad.py`) fuses two jobs in one function: *analysis* (Downloads over 10 GB, free space under 10%, which folders to check) and *voice* (the dad one-liners). The analysis half duplicates what grading already does — both modules apply their own thresholds to the same Downloads/Desktop folders, and the numbers can drift apart silently. Target shape: `scanners/grading.py` is the single place that inspects scan data and emits neutral findings (e.g. `downloads_large` with size and path); a persona module maps each finding to a line in its own voice and never touches thresholds. That makes a second persona (`personality/mom.py`) a table of strings rather than a fork of the logic, and it means tuning a threshold changes the grade and the commentary together. Sequence after the askdad rename lands — the rename's `git mv` to `dad.py` sets up the persona naming this builds on.
- [ ] **Standardize scanner return formats.** Partially done. Storage is modeled in `scanners/models.py`; the CPU scanner's process dicts were deliberately left unmodeled, since converting them reaches into the HTML renderer's process tables for little gain. Worth finishing if the CPU report grows.

## Bugs

- [ ] **The CPU report tells the user to run a command that does not work.** Found Aug 26, 2026. `renderers/html.py` ends the CPU report with "Re-run `python3 yourdad.py scan cpu` anytime" — but `scan` was removed when the CLI was flattened, so that command exits with a usage error. The correct form is `python3 yourdad.py cpu`. One string, but it is the only instruction the report gives a reader, and it fails for everyone who follows it. Note the fix breaks `test_normalized_snapshot_matches` until `tests/fixtures/cpu_scan.snapshot.html` is regenerated — the snapshot carries the stale text. Surfaced by the askdad rename plan, which lists this line as a rename target; it is a live bug independent of the rename and does not need to wait for it.

- [ ] **Launch fails on macOS Tahoe 26.4.1 / Apple Silicon** (Micah Evans, 2026-04-13). `RBSRequestErrorDomain Code=5`, quarantined-binary symptoms. Expected root cause: unsigned binary under Tahoe's tightened Gatekeeper. **Expected fix: Milestone 3 signing** — keep open until verified on a Tahoe machine. Details preserved in git history of this file.

## Future (post-beta)

- [ ] **Duplicate file detection.** By hash; the old v0.2 idea. 20-30 hours.
- [ ] **Native Swift app.** Real UI wrapping the Python scanner — the CleanMyMac competitor. Must keep the bundle ID from Milestone 2 so permission grants carry over. Permission implications already covered in `PERMISSIONS-PLAN.md` future-work.
- [ ] **MCP server.** Expose scans as MCP tools for AI agents. Depends on `--json`.

## Dropped / Superseded

- ~~**Test the security warning flow** (right-click → Open for unsigned builds)~~ — obsolete: the MVP ships signed and notarized, so there is no security warning to test. Replaced by the Milestone 3 clean-machine matrix.
- ~~**Sign and ship as `.app`** (single backlog line)~~ — expanded into `PERMISSIONS-PLAN.md` Phases 1-3 / Milestones 2-3.
- ~~**Test executable on clean Mac** (standalone item)~~ — folded into the Milestone 3 clean-machine matrix.
