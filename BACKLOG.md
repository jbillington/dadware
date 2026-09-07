# Backlog & Roadmap

**Last Updated:** September 7, 2026

This file holds **only unshipped work, in the order it should be done**. Shipped work moves to `CHANGELOG.md`, which is also the day-by-day session record — look there for what was done and why. Detailed specs live in `docs/roadmap/`.

---

## Next — the road to a signed beta

Do these in order. Items 1 and 2 can run at the same time.

### 1. Enroll in the Apple Developer Program

$99/yr, then request a **Developer ID Application** certificate. Approval takes days, so start it now — nothing else waits on it, and signing, notarization, the DMG and the Tahoe retest all wait on it.

### 2. Run the universal2 binary on the Intel Mac

**Done on the M1, Sep 7, 2026:** built with python.org's universal2 Python 3.13, `lipo` confirmed both slices, the scan ran and the full suite passed — the first time any of this has happened on Apple Silicon. See `CHANGELOG.md`.

What is left is the other half of the same evidence: copy **that same binary** to the Intel Mac and run a scan. One artifact proven on both machines is what the clean-machine matrix needs; two separate builds are not.

Optional, if the M4 is to hand: run it there too and check `sysctl -n sysctl.proc_translated` reads `0`. Spec: `docs/roadmap/ARCH-COVERAGE-PLAN.md`.

### 3. Check a mounted backup drive on a real Mac

The last unverified piece of the volume-crossing fix (Bug #8). With an external or Time Machine drive attached, a scan of `/` should finish, and its item count should match the unplugged run (~332k, not ~678k). Everything else about that fix is confirmed on the M1: a scan of `/` still shows the home folder breakdown, and a thumb drive scan reports on the drive alone. Spec: `docs/roadmap/VOLUME-CROSSING-PLAN.md`.

### 4. Sign, notarize, package

`sign_and_notarize.sh` and `entitlements.plist` script the flow but have never run. Extend them and `package_for_distribution.sh` to produce the stapled drag-to-Applications DMG and the Homebrew CLI package. Required secrets are listed in `docs/BUILDING.md`.

### 5. Tag `v0.7` and cut the release

`VERSION` reads 0.7 and nothing has ever been tagged at it. Tagging triggers the universal2 CI job, which has never run; step 2 proves that build by hand first. Upload both packages and capture report-card, terminal and breakdown screenshots for the landing page.

### 6. Retest on Tahoe

Launch fails on macOS Tahoe 26.4.1 / Apple Silicon (Micah Evans, 2026-04-13): `RBSRequestErrorDomain Code=5`, quarantined-binary symptoms. Expected cause is the unsigned binary under Tahoe's tightened Gatekeeper, so step 4 is the expected fix. No machine here runs Tahoe — Micah retests once the `.app` is signed. Keep open until verified.

---

## Milestone 3 — Signed Beta Packages

Everything above is this milestone, plus:

- [ ] **Homebrew formula + tap.** `Formula/askdad.rb` has a placeholder URL and stale syntax; needs the real release URL and a `homebrew-tap` repo.
- [ ] **Clean-machine test matrix.** Intel + Apple Silicon; Sonoma/Sequoia/Tahoe. No Gatekeeper warnings, prompts attribute to the app.
- [ ] **`.app` bundle + app mode.** PyInstaller onedir `.app`, `Info.plist` usage strings, browser progress page via meta-refresh. Spec: `docs/roadmap/PERMISSIONS-PLAN.md` Phase 2.
- [ ] **Verify the permission UX on real hardware.** Phase 1 is unit-tested with mocked errno, but TCC only exists on macOS. Run the `PERMISSIONS-PLAN.md` matrix — `tccutil reset All`, then all-denied, partially-granted, and FDA-revoked-after-grant. Fits into the next real-Mac run.

## Milestone 4 — Full-Report Experience

- [ ] **First-run onboarding.** HTML welcome page: read-only promise, what macOS will ask, with-vs-without-FDA comparison, guided FDA walkthrough. Spec: `PERMISSIONS-PLAN.md` Phase 3.
- [ ] **Trash scanner.** `~/.Trash` + `/Volumes/*/.Trashes`, FDA-gated, so it follows the onboarding flow. Spec: `HIDDEN-STORAGE-PLAN.md` Phase 2.

## Milestone 5 — Beta Launch

Family first, then friends on unseen Macs, then Reddit (r/macapps). Waits on Milestone 3 — the signed DMG removes the security-warning friction. Plan: `docs/TESTING-AND-LAUNCH.md`.

---

## Bugs

- [ ] **The home walk reports its item count as a total.** `scanners/storage.py:373` prints `found {n:,} items total` on every walk, so a subtree scan calls its own count the total. Should read `found 292,390 items in home folder, 617,504 items total`. `askdad.py:94` has the same ambiguity. Bug #7, 30 minutes.
- [ ] **The report card never says what the scan left out.** The scan already separates items excluded by policy (dotfiles, `.app` bundles, caches, Mail, Messages — each measured by its own scanner) from items the filesystem refused, and holds both as `excluded_count` and `denied_count`. `renderers/html.py` shows neither and `utils/llm_prompt.py` does not pass them to the LLM, so "why doesn't this add up to my disk size?" is answered nowhere in the report most people read. A rendering gap, not a measurement one.

## Report content — deferred, not blocking

- [ ] **No next step for a bad library grade.** Messages graded **F at 29.9 GB** with nothing telling the user what to do. A grade without an action is a scolding. Needs per-library advice (Messages: attachment management and "Keep Messages" retention; Photos: iCloud optimization; Mail: rebuild and attachment cleanup) in the same read-only advisory framing as the snapshot section. Graded libraries only — caches are not graded.
- [ ] **Nothing measures the big third-party stores.** The Mac App Libraries grade covers Apple's five, so on a developer's or gamer's Mac the largest pile on the disk can be missing from the graded section: **Steam** (`~/Library/Application Support/Steam/steamapps`, routinely 100 GB+), **Xcode** (`DerivedData`, `iOS DeviceSupport`, archives), **iOS Simulator runtimes** (`~/Library/Developer/CoreSimulator/Devices`), possibly Adobe. Two questions first: graded or reported like caches (a big Steam folder is not clutter if the games are played), and how much `scanners/hidden_storage.py::scan_developer_caches()` already picks up. **Leave the Docker handling alone** — `utils/path_utils.py` deliberately sizes sparse images by `st_blocks * 512`; a new scanner sits alongside it.
- [ ] **Orphaned caches: cross-reference cache folders against installed apps.** `build_app_name_index()` already knows what is installed, so flagging caches for apps you no longer have is nearly free — and it is the one cache category worth clearing for good.
- [ ] **Remember the permission *state*, not just a flag.** `~/.dadware/.permissions-introduced` is a bare boolean, so the explainer never runs again — wrong in both directions. After a `tccutil reset`, a migration, or revoked grants the dialogs come back unexplained; and when someone takes the advice and switches Full Disk Access on, nothing acknowledges it. Store `{introduced, fda, folders: {Desktop: granted, ...}, last_run}` — every value is already computed each run, so it is a write, not new work. The rules then become transitions: explain when there is no record or a folder went back to denied; say one line when FDA flipped off→on; stay silent otherwise. **Two constraints or it becomes noise:** speak only on a transition, and only when the news is good or actionable — never announce "you turned FDA off", the report already shows the blanks. Migration is trivial: the existing plain-text file means "introduced, state unknown".
- [ ] **Snapshot size.** `scanners/snapshots.py::_parse_diskutil_plist()` reads only `SnapshotName` and `Purgeable`. Run `diskutil apfs listSnapshots -plist /System/Volumes/Data` on a Mac and dump every key. If a size key exists, ship single-snapshot sizing — with exactly one snapshot, "what would I get back" is a well-formed question. If it does not, point the user at Finder → Get Info, which shows a purgeable total.
- [ ] **Optimize the LLM prompt for the storage scan.** `generate_storage_prompt()` grew organically and still ends with a fixed six-question tail written before volumes, libraries, caches and snapshots existed. The questions should match the current sections, and the prompt should state what the scan could *not* see so the model does not reason from a total it assumes is complete.
- [ ] **Research how CleanMyMac / DaisyDisk / Sweep handle units, purgeable and cache-safety copy.** Prompt ready at `docs/research/COMPETITOR-UX-RESEARCH-PROMPT.md`. Much narrower than when written — units, purgeable and the cache-safety message are all decided. Nothing live depends on it. Would extend `docs/COMPETITIVE-COMPARISON.md`.

## Feature Pool (unscheduled)

- [ ] **`--json` flag.** Scan results to stdout. Low effort, and the prerequisite for the MCP server.
- [ ] **`--prompt` flag.** The LLM-ready prompt to stdout for agents.
- [ ] **Redesign report card layout.** Component grades first, overall grade last, one line of explanation each.
- [ ] **Explore a scoring system a normal person can read (and want to beat).** A real run shows **Free Space D (69/100)** beside three components pinned at **A (100/100)**, so the top-line grade is just the free-space number and the rest is decoration. The names ("Home Folders Ratio", "Home Folders Clutter") describe how we compute, not what the user has, and a component can score A on almost no evidence. Explore metrics a dad would actually check and that pay off in ten minutes — Downloads, Trash, Desktop clutter, screenshots, big apps never opened, duplicates, stale installers. The current components are ratios; these are errands, each with a visible before-and-after. Ratios can't be gamified; errands can. Pairs with the layout redesign.
- [ ] **CPU/RAM grading thresholds have never gotten the scrutiny storage got.** Storage was re-baselined in Aug 2026; memory kept its original thresholds.
- [ ] **Expand personality comments.** The current set repeats quickly.
- [ ] **Report history.** `askdad history` — past reports with dates and grades.
- [ ] **Lightweight TUI.** Curses menu, progress and summary for the CLI channel. Deprioritized: the `.app` plus browser progress now serves non-technical users. Plan: `docs/roadmap/LIGHTWEIGHT-TUI-PLAN.md`.

## Code Quality

- [ ] **Move the analysis out of `personality/` into `scanners/grading.py`; personas become pure voice.** `personality/dad.py` fuses analysis (Downloads over 10 GB, free space under 10%) with voice (the one-liners), and the analysis half duplicates thresholds that grading already applies to the same folders — so the two can drift apart silently. Target: `grading.py` emits neutral findings (`downloads_large`, with size and path); a persona maps each finding to a line and never touches a threshold. That makes `personality/mom.py` a table of strings, and tuning a threshold moves the grade and the commentary together.
- [ ] **Standardize scanner return formats.** Partially done. Storage is modeled in `scanners/models.py`; the CPU scanner's process dicts were left unmodeled because converting them reaches into the HTML renderer's process tables for little gain. Worth finishing if the CPU report grows.

## Future (post-beta)

- [ ] **Duplicate file detection.** By hash. 20-30 hours.
- [ ] **Native Swift app.** Real UI wrapping the Python scanner. Must keep the bundle ID so permission grants carry over. Never the Mac App Store — sandboxing is incompatible with Full Disk Access.
- [ ] **MCP server.** Scans as MCP tools for AI agents. Depends on `--json`.
