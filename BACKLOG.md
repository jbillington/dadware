# Backlog & Roadmap

**Last Updated:** August 24, 2026

Milestones are in execution order — each one is shippable on its own. Detailed specs live in `docs/roadmap/`: `HIDDEN-STORAGE-PLAN.md` and `PERMISSIONS-PLAN.md` are the two active PRDs.

**This file holds only unshipped work.** When something ships it moves to `CHANGELOG.md` with its full text and evidence intact — so the backlog stays a to-do list rather than a history.

---

## Milestone 1 — Hidden Storage, Phase 1

The scan learns to see what it currently can't: app caches, hidden folders, purgeable space, and snapshots — all folded into the existing storage report. Needs no new permissions, pure Python, ships value immediately. Spec: `docs/roadmap/HIDDEN-STORAGE-PLAN.md`.

**All three scanners (1a, 1b, 1c) have shipped** and are verified on real hardware — see `CHANGELOG.md`. They are wired for **display only**. The milestone closes when the data reaches the score.

**Caches are information, not a grade.** Decided Aug 24, 2026: cache size will never be a grade component and stays low-key on the report card. A cache is not mess — it is an app doing its job, and it comes back on its own. Grading someone down for it would be telling them off for something that isn't their fault and that they can't permanently fix. We report the total, we explain what it is, and we stop there. This removes the single biggest reason the grade re-baseline was ever a large piece of work.

**Recommended order — three PRs, one release.** See *How to sequence this* below.

1. **Fix what's measured** — the Mac library scan currently grades on partial data.
2. **Re-baseline the score** — the remaining grade changes, in one commit.
3. **Cache education copy** — no grade impact, ships independently, can go any time.

### Essential to close Milestone 1

- [ ] **Wire the scan data into the grade and the personality (the other half of Wiring).** The scanners attach `scan_data['hidden_caches']` and `scan_data['snapshots']`, and both render in the HTML report, the terminal report and `llm_prompt.py`. Neither reaches `scanners/grading.py` or `personality/yourdad.py` — both files reference the two keys exactly **zero** times. The original deferral said this waits "until 1b and 1c are in and the composite can be re-baselined once"; **that gate cleared Aug 24, 2026** when 1c shipped.

  What this now means, given the caches-are-information call above:
  - **No cache grade component.** Dropped by decision, not deferred. The cache total is reported and explained; it never moves a letter.
  - **No snapshot grade component either** — snapshots are low-priority and the report already says honestly what it can't measure. Revisit only if the plist check below turns up a real size.
  - **Personality comments are unblocked right now.** A dad comment about caches or snapshots moves no grade, so it needs no re-baseline and can ship whenever. This is the cheapest user-visible win left in the milestone.
  - **What's actually left for the score** is the re-baseline item below — which is now three small grade changes, not five.
- [ ] **Re-baseline the score.** Three changes, all of which move grades that testers have already seen, so they land in **one commit** with release notes that say a grade may move and why:
  1. **Convert grading thresholds from binary to decimal.** `format_size()` and `parse_size()` are 1000-based as of Aug 24, 2026; the thresholds in `scanners/grading.py` are still 1024-based and documented that way in `docs/GRADING.md`. Until they agree, the numbers a user reads and the numbers we grade against are on different scales.
  2. **Retire the pre-APFS Time Machine check in `scan_time_machine_backups()`.** `scanners/mac_libraries.py` only looks for `/Backups.backupdb`, the pre-APFS backup format, and 1c now supersedes it for local snapshots (`HIDDEN-STORAGE-PLAN.md` calls for this). `time_machine` is a *graded* library, so changing what it measures moves real grades — which is why it waited.
  3. **Settle the two open grading decisions** (`docs/GRADING.md`): the home-folder clutter grade can never return a C (`problem_count == 2` scores exactly 60, a D), and that grade is excluded from the composite, so an F there moves the top-line grade by zero. Both need a product call rather than a code fix.
- [ ] **Cache guidance: plain-language education, not a chore list.** No grade attached, no urgency, no red. The message, in the user's own words, is four things:
  1. **These apps are building caches, and here's how much.** A total and a list. That's the whole headline.
  2. **A cache is not the app and not your data.** Clearing Spotify's cache keeps your playlists; clearing Arc's keeps your tabs and logins.
  3. **Caches rebuild themselves.** Delete one to free space now and the app quietly rebuilds it next time you use it. That makes clearing a cache low-risk — and usually temporary, which is the honest part most tools leave out.
  4. **The one time it's worth clearing for good is when you're deleting the app.** Dragging an app to the Trash leaves `~/Library/Caches/<bundle-id>`, Application Support and preferences behind. Uninstalling is not a cleanup path on its own.

  Keep the copy short and un-alarming. The current section explains what caches are but stops before saying what to do; the fix is guidance, not a to-do list. Presenting every row as an equal action item turns the section into pointless chores, which is a trust problem for a tool whose pitch is straight talk.
- [ ] **Make the cache total less prominent on the report card.** The Aug 24 stat tile put the cache figure in the top summary next to graded components, which reads as "this is a problem you should act on" — the opposite of the call above. Keep the number and the jump link to `#hidden-caches`, drop the visual weight so it sits as information rather than as a fourth grade.

### How to sequence this

Three PRs, landing in this order, and **cut no release between the first two** so testers' grades move exactly once:

1. **Measurement fix** (optional but recommended first — see the deferred library item below). Changes *what* is measured, not how it is scored.
2. **Score re-baseline.** Changes *how* it is scored. Kept separate so that when a grade moves you can tell which of the two caused it — landing them together makes every movement unattributable.
3. **Cache copy + report-card de-emphasis.** Zero grade impact, so it is independent of the other two and can ship first, last, or in parallel.

The reason for separate PRs is attribution, not caution: both 1 and 2 move letters, and if they arrive in one diff there is no way to tell a real change from a scan artifact. The reason for one release is the tester experience — two releases means explaining two grade movements for a disk that hasn't changed.

### Deferred — worth doing, not blocking Milestone 1

- [ ] **Mac library scan hits its time budget and truncates.** Deferred Aug 24, 2026 — the workaround is cheap enough that this doesn't need to be a project. On the Aug 24 run, Mail, Time Machine and Creative Apps all came back "(skipped: time-limited)" against `scan_all_mac_libraries(timeout_seconds=10)`. **`timeout_seconds` is a plain default parameter that `yourdad.py` never overrides**, so raising the budget, or exposing it as a flag, is close to a one-line fix — no second-pass architecture required.

  Two known defects, for whoever picks it up:
  - The Partial Scan banner named only `mail` while three libraries were skipped. `interrupted_scans` records the scanner that *tripped* the budget, not everything that got skipped. Confirmed in `test-reports/storage_2026-08-24_08-19.json`: `interrupted_scans` is `['mail']` while `mail`, `time_machine` and `creative` all carry `status: skipped`.
  - **It affects the grade, and this is the part worth knowing before the re-baseline.** Skipped libraries render as `-`/0 but are *excluded* from the Mac App Libraries average — `renderers/html.py` only appends to `library_scores` under `if lib_size > 0` — so they do not drag it down. Instead the average was computed from Photos, Music and Messages alone (three of six) and carried its full 0.2 composite weight as though all six had been measured. Nothing in the grade says it is based on half the evidence. Worth landing before the re-baseline for that reason; not worth blocking the milestone on.
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

- [ ] **Standardize scanner return formats.** Partially done. Storage is modeled in `scanners/models.py`; the CPU scanner's process dicts were deliberately left unmodeled, since converting them reaches into the HTML renderer's process tables for little gain. Worth finishing if the CPU report grows.
- [ ] **Two grading decisions left open** (see `docs/GRADING.md`): the home-folder clutter grade can never return a C (`problem_count == 2` scores exactly 60, a D), and that grade is excluded from the composite, so an F there moves the top-line grade by zero. Both change grades users already see, so they need a product call rather than a code fix. **Part of the Milestone 1 score re-baseline** — they land with the other two grade changes in one commit, not on their own.

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
