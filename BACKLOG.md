# Backlog & Roadmap

**Last Updated:** August 30, 2026

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
- [ ] **Nothing measures the big third-party stores — Steam, Xcode, iOS Simulator runtimes.** Raised Aug 28, 2026. The Mac App Libraries grade covers Apple's five (Photos, Music, Messages, Mail, Creative Apps) and nothing else, so on a developer's or gamer's Mac the single largest pile on the disk can be absent from the graded section entirely. Candidates worth their own treatment: **Steam** (`~/Library/Application Support/Steam/steamapps`, routinely 100 GB+), **Xcode** (`~/Library/Developer/Xcode/DerivedData`, `~/Library/Developer/Xcode/iOS DeviceSupport`, archives), **iOS Simulator runtimes** (`~/Library/Developer/CoreSimulator/Devices` — gigabytes per unused runtime and a classic forgotten pile), and possibly Adobe/Creative Cloud caches. Two open questions before building anything: whether these belong in the *graded* Mac App Libraries average (they are not Apple libraries, and a big Steam folder is not "clutter" if the games are played) or as an ungraded reported section like hidden caches; and how much `scanners/hidden_storage.py::scan_developer_caches()` already picks up incidentally, since it covers Xcode and package-manager caches for the *cache* section.

  **Do not disturb the Docker handling while doing this.** `utils/path_utils.py` already special-cases Docker deliberately and correctly: `is_docker_path()` plus the disk-accurate `st_blocks * 512` sizing for `docker.raw` and other sparse images, so a 60 GB sparse file that occupies 5 GB reports 5 GB. That behaviour is tested and was hard-won — a new store scanner should sit alongside it, not rewrite it.
- [ ] **Orphaned caches: cross-reference cache folders against installed apps.** `build_app_name_index()` already knows what is installed, so flagging "caches belonging to apps you no longer have" is nearly free — and it is the one cache category that is genuinely worth clearing for good, which makes it the natural follow-on to the guidance copy above.
- [ ] **Optimize the LLM prompt for the storage scan.** `utils/llm_prompt.py::generate_storage_prompt()` has grown organically — it now carries volume info, folders, files, libraries, hidden caches and snapshots, with a fixed six-question tail written before most of that data existed. Worth a pass for what an LLM can actually act on: the questions should reflect the new sections, and the prompt should state what the scan could *not* see (protected folders, purgeable space, skipped libraries) so the model does not reason from a total it assumes is complete.
- [ ] **Research how CleanMyMac / DaisyDisk / Sweep handle units, purgeable and cache-safety copy.** Prompt ready at `docs/research/COMPETITOR-UX-RESEARCH-PROMPT.md`. **Much narrower than when it was written:** units are decided (decimal), purgeable was settled by the spike, and the cache-safety message is now decided too. Nothing live depends on it. Would still extend `docs/COMPETITIVE-COMPARISON.md`, which currently covers only ncdu and htop.

## Milestone 2 — Identity & Permission UX Foundation

Everything that must be right *before* the first signed build, because macOS keys permission grants to bundle ID + signature — the app's identity has to be final first.

**This milestone is done** (Aug 28, 2026): the askdad rename and the Phase 1 permission UX both shipped — see `CHANGELOG.md`. One deferred item:

- [ ] **Keep the permission *state* in `~/.dadware/.permissions-introduced`, not just a flag.** Raised Aug 30, 2026; deferred deliberately. The marker is currently a bare boolean — the file exists, so the explainer never runs again, forever. That is wrong in both directions. If someone runs `tccutil reset`, migrates to a new Mac, or has grants revoked, the dialogs come back and the marker says "already introduced", so they arrive unexplained — exactly the situation the explainer exists for. And when someone takes the end-of-run advice and switches Full Disk Access on, nothing acknowledges it: we open a loop ("run the scan once more, the blanks fill in") and never close it. Store the last-known state instead — `{introduced, fda, folders: {Desktop: granted, ...}, last_run}` — since every one of those values is already computed on each run, so it is a write rather than new work. Then the rules become transitions: explain when there is no record **or** when a folder went from granted back to denied/unknown; say one line when FDA flipped off→on; stay silent when nothing changed. **Two constraints or it becomes noise:** only ever speak on a transition, never on steady state, and only when the change is good news or actionable — do not announce "you turned FDA off", since the report already shows the blanks and the end-of-run block already explains the fix. Migration is trivial: the existing plain-text file means "introduced, state unknown", so the first run after upgrading records state and says nothing.
- [ ] **Verify the permission UX on real hardware.** The Phase 1 work (choreography, per-folder TCC detection, honest-denial copy, FDA deep link) is fully unit-tested with mocked errno, but TCC itself only exists on macOS. Run `PERMISSIONS-PLAN.md`'s testing matrix — `tccutil reset All`, then the all-denied, partially-granted, and FDA-revoked-after-grant states — and confirm the dialogs fire up front, denied folders come out labeled rather than zeroed, and the deep link lands on the Full Disk Access pane. Fits naturally into the next real-Mac test run.

## Milestone 3 — Signed Beta Packages

The MVP ships as two packages from one codebase: a double-clickable `.app` in a DMG (primary, for beta testers) and a CLI (Homebrew + website, for technical users and LLM-harness use). Spec: `PERMISSIONS-PLAN.md` Phase 2.

- [ ] **Apple Developer Program enrollment** ($99/yr) + Developer ID Application certificate.
- [ ] **`.app` bundle + app mode.** PyInstaller onedir `.app`, `Info.plist` usage strings, browser progress page via meta-refresh. (Non-interactive volume selection is already done — `select_volume()` auto-selects when there's no TTY as of the Aug 2026 refactor.)
- [ ] **Sign, notarize, package.** Tooling exists but has never run: `sign_and_notarize.sh` + `entitlements.plist` script the codesign/notarytool flow, CI has a tag-gated universal2 build, and `docs/BUILDING.md` lists the required secrets. Remaining: get the Developer ID cert, extend the script/`package_for_distribution.sh` to produce the stapled drag-to-Applications DMG and the Homebrew CLI package, then run it all for the first time.
- [ ] **Homebrew formula + tap.** `Formula/askdad.rb` currently has a placeholder URL and stale syntax; needs real release URL and a `homebrew-tap` repo.
- [ ] **Clean-machine test matrix.** Intel + Apple Silicon; Sonoma/Sequoia/Tahoe; verify no Gatekeeper warnings, prompts attribute to the app, and the Tahoe launch bug (below) is resolved.
- [ ] **The universal2 build has an untested half — and it is the Apple Silicon one.** Updated Aug 26, 2026 (folded from PR #10). GitHub retired the `macos-13` image, so `actions/runner-images` now lists only `macos-14`, `macos-15` and `macos-26`, all Apple Silicon. Moving the *test* matrix to `macos-15` was safe: the runtime code is stdlib and subprocess calls with no architecture coupling, and the suite passes on both arm64 (CI) and x86_64 (the dev Mac).

  **The x86_64 slice is covered.** Development happens on a MacBookPro14,2 (Intel Core i7-7567U, Ventura), so an Intel binary can be built and run natively at any time.

  **The arm64 slice is not.** No Apple Silicon hardware is in the loop — CI exercises the Python on arm64, but nobody runs the *packaged* app there, which is where Gatekeeper, notarization stapling and the launch path actually get tested. The Tahoe launch bug (below) was reported on Apple Silicon and has never been reproducible locally for exactly this reason.

  **Also worth knowing: universal2 cannot currently be built at all.** `askdad.spec` documents why — PyInstaller cannot cross-compile, so a universal2 output needs the *building* Python to itself be universal2. The project venv is `x86_64` only, and while `/usr/bin/python3` is universal it is `x86_64 + arm64e`, not the `arm64` PyInstaller wants. Producing a universal2 build means installing a python.org universal2 Python first.

  So the remaining question is not "find an Intel Mac" — it is whether to build universal2 on a universal2 Python and get the arm64 half onto real hardware for the Milestone 3 clean-machine matrix, or ship Intel-only and add arm64 later. **Do not ship a signed universal2 binary whose arm64 half has never been run.**
- [ ] **GitHub Release + screenshots.** Tag the release, upload both packages, capture report-card/terminal/breakdown screenshots for the landing page and Reddit.
- [ ] **Nothing has been tagged at the current version — `v0.7` exists only as a constant.** Updated Aug 28, 2026: a `v0.1-poc` tag now marks the original April POC commit (`bf2af14`) for history, but `VERSION` reads 0.7, no `v0.7` tag exists, and no release has been cut. Worth knowing *why not yet*: tagging triggers the universal2 build job, which is the one thing CI can no longer verify (above). The askdad rename (the other prerequisite — macOS keys permission grants to bundle ID) landed Aug 28, 2026, so the remaining sequence is Developer ID → arm64 verification → tag, not tag-now.

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
- [ ] **CPU/RAM grading thresholds have never gotten the scrutiny storage got.** Carried from CONTEXT.md's open questions when that file was folded away (Aug 28, 2026). Storage grades were tightened and re-baselined in Aug 2026; memory grading kept its original thresholds throughout.
- [ ] **Expand personality comments.** More variety; the current set repeats quickly. New hidden-storage comments from Milestone 1 help.
- [ ] **Report history.** `askdad history` — list past reports with dates and grades.
- [ ] **Lightweight TUI.** Curses menu/progress/summary for the CLI channel. Deprioritized: the `.app` + browser-progress path now serves non-technical users, so this is a CLI-channel nicety. Plan: `docs/roadmap/LIGHTWEIGHT-TUI-PLAN.md`.

## Code Quality

- [ ] **Move the analysis out of `personality/` into `scanners/grading.py`; personas become pure voice.** Decided Aug 28, 2026 alongside the rename-plan scope revision. `personality/dad.py` fuses two jobs in one function: *analysis* (Downloads over 10 GB, free space under 10%, which folders to check) and *voice* (the dad one-liners). The analysis half duplicates what grading already does — both modules apply their own thresholds to the same Downloads/Desktop folders, and the numbers can drift apart silently. Target shape: `scanners/grading.py` is the single place that inspects scan data and emits neutral findings (e.g. `downloads_large` with size and path); a persona module maps each finding to a line in its own voice and never touches thresholds. That makes a second persona (`personality/mom.py`) a table of strings rather than a fork of the logic, and it means tuning a threshold changes the grade and the commentary together. Sequence after the askdad rename lands — the rename's `git mv` to `dad.py` sets up the persona naming this builds on.
- [ ] **Standardize scanner return formats.** Partially done. Storage is modeled in `scanners/models.py`; the CPU scanner's process dicts were deliberately left unmodeled, since converting them reaches into the HTML renderer's process tables for little gain. Worth finishing if the CPU report grows.

## Bugs

- [x] **Instrument every phase with a timer, then report an honest total.** Done Sep 2, 2026. `utils/timing.py` holds the run's wall clock and a per-phase context manager; `askdad.py` times the volume walk, home walk, permission check, Mac libraries, hidden caches, snapshots, CPU scan, grading and HTML render, printing a breakdown under `--timings` or `DIAGNOSTIC_LOGGING=1`. `finish_run()` stamps the whole run's wall clock onto each report, replacing the volume-walk-only figure that read 63s against a 3m 10s stopwatch.

- [x] **The home directory is walked twice, and it is most of the disk.** Done Sep 2, 2026 with option (a). `scan_storage()` takes a `home_path` and, when home sits inside the scan root, fills a second set of `_FolderBuckets` rooted there during the same walk, returned as `result['home_breakdown']` for `run_storage_scan()` to merge and drop. The single-pass `os.scandir` design and the one-`stat()`-per-file rule are unchanged. The separate home walk still runs when home is on another volume or the walk never reached it. Tests pin the folded breakdown against a separate walk of home, and the merged folder list against the old two-walk result.
- [ ] **Scanning `/` descends into every mounted volume.** Found Sep 3, 2026 on a real Mac. `should_exclude()` filters a fixed list of root directory names and has no filesystem-boundary check, and `/Volumes` is not on it, so picking "Macintosh HD (/)" walks attached external and Time Machine drives. With a 2 TB backup drive mounted the same scan passed 678,566 items and 499s without finishing; unplugged it finds ~332,000 in 1m 45s. It also silently counts backup contents toward the startup disk, so the totals and every folder ranking are wrong whenever a volume is mounted. Fix by comparing each entry's `st_dev` against the scan root's — the walk already holds a `stat_result` per entry, so it costs no extra syscall. Do not fix by name-excluding `/Volumes`: that misses other mount points and would break an explicit `--volume /Volumes/BACKUP`. Spec: `docs/roadmap/VOLUME-CROSSING-PLAN.md`. Bug #8.

- [ ] **The home walk reports its item count as a total.** Found Sep 3, 2026. `scanners/storage.py:373` prints `found {n:,} items total` and is reached by every walk, so a pre-PR#13 run printed two different "totals", neither of which was one. PR #13 removed the second walk so the duplicate is gone from `main`, but the wording is still wrong for any subtree scan. Should read `found 292,390 items in home folder, 617,504 items total`. `askdad.py:94` has the same ambiguity while running. Bug #7.

- [ ] **The report card never says what the scan left out.** Found Aug 28, 2026 while splitting `skipped_count`; the terminal's version of this line was deleted the same day for being noise, which makes the report card the only place it can live. The scan distinguishes two kinds of omission — items excluded by policy (dotfiles, `.app` bundles, caches, Mail, Messages, which are each measured by a specialist scanner and reported in their own section) and items the filesystem actually refused — but `renderers/html.py` shows neither, and `utils/llm_prompt.py` doesn't pass them to the LLM either. The HTML report is the one most users actually read, and "why doesn't this add up to my disk size?" is answered nowhere in it. Both counts are already in `scan_data` as `excluded_count` and `denied_count`; this is a rendering gap, not a measurement one.
- [x] **Report footers hardcode "Dad Ware v0.1" while the real version is 0.7.** Done Sep 2, 2026. Both HTML footers and the terminal report-card header read `VERSION`, and the snapshot `scrub()` normalizes the version the way it already normalizes dates, so a release bump no longer churns the fixtures. Still undecided: whether the string should read "Ask Dad for Mac v{VERSION}" to match the terminal banner - left as "Dad Ware" for now.

- [ ] **Launch fails on macOS Tahoe 26.4.1 / Apple Silicon** (Micah Evans, 2026-04-13). `RBSRequestErrorDomain Code=5`, quarantined-binary symptoms. Expected root cause: unsigned binary under Tahoe's tightened Gatekeeper. **Expected fix: Milestone 3 signing** — keep open until verified on a Tahoe machine. Details preserved in git history of this file.

## Future (post-beta)

- [ ] **Duplicate file detection.** By hash; the old v0.2 idea. 20-30 hours.
- [ ] **Native Swift app.** Real UI wrapping the Python scanner — the CleanMyMac competitor. Must keep the bundle ID from Milestone 2 so permission grants carry over. Permission implications already covered in `PERMISSIONS-PLAN.md` future-work.
- [ ] **MCP server.** Expose scans as MCP tools for AI agents. Depends on `--json`.

## Dropped / Superseded

- ~~**Test the security warning flow** (right-click → Open for unsigned builds)~~ — obsolete: the MVP ships signed and notarized, so there is no security warning to test. Replaced by the Milestone 3 clean-machine matrix.
- ~~**Sign and ship as `.app`** (single backlog line)~~ — expanded into `PERMISSIONS-PLAN.md` Phases 1-3 / Milestones 2-3.
- ~~**Test executable on clean Mac** (standalone item)~~ — folded into the Milestone 3 clean-machine matrix.
