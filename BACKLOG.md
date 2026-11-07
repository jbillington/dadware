# Backlog & Roadmap

**Last Updated:** November 7, 2026

This file holds **only unshipped work, in the order it should be done**. Shipped work moves to `CHANGELOG.md`, which is also the day-by-day session record — look there for what was done and why. Detailed specs live in `docs/roadmap/`.

---

## Next — the road to a signed beta

**The Apple Developer Program subscription is bought (Sep 2026).** Signing is now unblocked, and it is the next thing to do.

### 1. Sign and notarize the binary, on the 2017 Intel Mac — in progress

Do it there, not on the M1 (Stacey's laptop, not signed into the developer account) and not on the M4 (a work machine — a personal signing key on employer-managed hardware is a policy question you do not need). Signing does not care about architecture: an Intel Mac signs a universal2 binary perfectly well. The certificate's private key then lives on your own machine, where the repo already is.

**Status, Nov 7, 2026.** Done: a–b. Next: confirm the identity is valid, then c. Not started: d–e.

**a. Get the binary there — done Nov 1.** The universal2 binary came over on the `johnnyb` thumb drive, not AirDrop, and is now `dist/askdad` on the Intel Mac. `lipo -info` reads `x86_64 arm64`; SHA-256 before signing is `16f984d994eea46060c20b0519fd73b1f761e28894d8d9c06bc60495d191bf2e`. The old Intel-only build is kept beside it as `dist/askdad.intel-build.bak` (`820e46fc…`). **Still open:** compare that hash with `shasum -a 256 dist/askdad` on the M1, to prove it is the same artifact. Do it before signing — `codesign` writes into the file and changes the hash.

Watch for two traps here. `./askdad` in the repo root is the Python menu launcher, not the binary: always type `./dist/askdad`. And a `cp` from a thumb drive sets no quarantine flag, so a run on this Mac never tests Gatekeeper.

**This binary is not the release binary.** It is the Sep 7 M1 build, which predates all of PR #17 (merged Sep 14–15): the Trash row, whole-folder roll-up, the end of the seven-name home allowlist, `/Applications` and `/Library` in the walk, and apps sized as one item. The Nov 1 scan showed it: no Trash row, `Music` and `Music/Music` as two rows, no `/Applications`. PR #15 (volume crossing, Sep 7) is probably in it; the `Starting storage scan (Build …)` line says for sure. Use this binary to prove the signing flow, then build again from `main` — see step 2.

**b. Create the certificate on this machine — done Nov 1.** `Developer ID Application: JOHN N BILLINGTON (3HM5J8RJX6)`, SHA-1 `87A9CC14511B43A15F0DB08A4B7B0DFC7B39463C`. Two snags, both fixed or being fixed:

- **The upload window did not show the request file.** The CSR had to be made first (Keychain Access → Certificate Assistant → *Request a Certificate From a Certificate Authority*, *Saved to disk*), on this Mac. Make the CSR and download the `.cer` on the same Mac: the private key stays with the Mac that made the request.
- **The `.cer` went into the iCloud keychain.** Double-clicking it offers iCloud as the default. It must go into `login`, where the private key is — and iCloud would sync it to the M4. It was imported again into `login` with `security import ~/Downloads/developerID_application.cer -k ~/Library/Keychains/login.keychain-db`, which said it was already there.
- **`find-identity` then listed the identity under "Matching" but showed `0 valid identities`.** The key was paired, so the cause is trust: the **Developer ID G2** intermediate was missing. Fix:

```bash
curl -fsSLo ~/Downloads/DeveloperIDG2CA.cer https://www.apple.com/certificateauthority/DeveloperIDG2CA.cer
security import ~/Downloads/DeveloperIDG2CA.cer -k ~/Library/Keychains/login.keychain-db
security find-identity -v -p codesigning     # want: 1 valid identities found
```

**Not yet confirmed:** that this now reads `1 valid identities found`. If it does not, `security verify-cert -c ~/Downloads/developerID_application.cer -p codeSign` names the reason. After it does, delete the iCloud copy: Keychain Access → iCloud → Certificates → right-click the Developer ID certificate → Delete. Delete nothing in the **Keys** tab and nothing in `login`.

**c. Get a notary credential — not started.** App Store Connect → Users and Access → Integrations → App Store Connect API → Team Keys → **+**, role **Developer**. Note the **Issuer ID** (top of the page) and the **Key ID** (the row). The `.p8` downloads **once**: keep it outside the repo and back it up in a password manager.

```bash
mkdir -p ~/.appstoreconnect/private_keys
mv ~/Downloads/AuthKey_*.p8 ~/.appstoreconnect/private_keys/ && chmod 600 ~/.appstoreconnect/private_keys/AuthKey_*.p8
```

Test the key before the slow upload — this should print an empty history, not a 401:

```bash
xcrun notarytool history --key "$APPLE_API_KEY_PATH" --key-id "$APPLE_API_KEY_ID" --issuer "$APPLE_API_ISSUER"
```

**d. Sign and notarize — not started.** Never commit any of these values. Exports last only for one Terminal window. Use `$HOME`, not `~`, inside the quotes.

```bash
export DADWARE_CODESIGN_IDENTITY="Developer ID Application: JOHN N BILLINGTON (3HM5J8RJX6)"
export APPLE_API_KEY_ID="…" APPLE_API_ISSUER="…" APPLE_API_KEY_PATH="$HOME/.appstoreconnect/private_keys/AuthKey_….p8"
./sign_and_notarize.sh 2>&1 | tee ~/Desktop/sign-run.log
```

**`sign_and_notarize.sh` has never run.** Expect to iterate. On a rejection, `xcrun notarytool log <id> …` (the script prints the command) names the file and rule that failed. macOS may ask to let `codesign` use the key: **Always Allow**.

**e. Verify — not started.** Two of the checks this step used to list fail on a bare Mach-O even when the binary is fine, and the script says so: `xcrun stapler validate` (a ticket staples only to a `.app`, `.dmg` or `.pkg` — this check belongs to step 4), and `spctl -a -t install` (may say "rejected" for a loose binary). Use these instead:

```bash
codesign --verify --deep --strict --verbose=2 dist/askdad
codesign -dvv dist/askdad 2>&1 | grep -E "Authority|TeamIdentifier|Timestamp|flags"   # want: Developer ID first, a Timestamp, flags=0x10000(runtime)
xcrun notarytool history --key "$APPLE_API_KEY_PATH" --key-id "$APPLE_API_KEY_ID" --issuer "$APPLE_API_ISSUER"   # want: Accepted
./dist/askdad --timings 2>&1 | tee ~/Desktop/askdad-signed-run.log
```

macOS may ask for folder access again after signing: TCC records grants against the signature, and signing gives the binary a new identity. The real Gatekeeper test is the signed binary AirDropped to another Mac (AirDrop sets quarantine) — the M1 is the obvious one, and that run also covers the arm64 slice.

### 2. Run the universal2 binary on the Intel Mac — done; one release build still needed

**Done on the M1, Sep 7, 2026**, and **on the 2017 Intel Mac, Nov 1, 2026**: the same Sep 7 binary ran a full scan of `/` in **1m 53s** on the Intel slice. See `CHANGELOG.md`. Optional, if the M4 is to hand: run it there too and check `sysctl -n sysctl.proc_translated` reads `0`. Spec: `docs/roadmap/ARCH-COVERAGE-PLAN.md`.

**What is left: the release binary, built from current `main`.** After step 1 proves the signing flow on the old binary, build again — PR #17 is missing from it. **Build on the Intel Mac**, not the M1. A universal2 binary needs a universal2 *Python*, not an Apple Silicon Mac: the old Intel build failed only because its venv was x86_64-only. Building where the certificate and the repo already live removes the copy step and the stale-binary risk, and the M1 run that tests the arm64 slice doubles as the Gatekeeper test. This route is **untried**; if it fails, fall back to the proven M1 build.

```bash
mv venv venv.intel-only.bak
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -m venv venv   # python.org 3.13 installer
lipo -info venv/bin/python3                                                   # want: x86_64 arm64
./venv/bin/pip install -r requirements-dev.txt
./venv/bin/python -m pytest tests/ -q
git pull origin main && DADWARE_TARGET_ARCH=universal2 ./build_executable.sh
lipo -info dist/askdad                                                        # want: x86_64 arm64
```

Then sign it (step 1d), scan on the Intel Mac, AirDrop it to the M1 and scan there. In the new build, a Trash row and the `→ sized N apps in X.Xs` line should appear — the second shows what app sizing costs on the slowest Mac here.

### 3. Check a mounted backup drive on a real Mac

The last unverified piece of the volume-crossing fix (Bug #8). With an external or Time Machine drive attached, a scan of `/` should finish, and its item count should match the unplugged run (~332k, not ~678k). Everything else about that fix is confirmed on the M1: a scan of `/` still shows the home folder breakdown, and a thumb drive scan reports on the drive alone. Spec: `docs/roadmap/VOLUME-CROSSING-PLAN.md`.

### 4. Package the DMG and the Homebrew CLI

Step 1 signs the *binary*. Beta testers get a **stapled drag-to-Applications DMG**, which has to be built, signed and stapled in its own right — `package_for_distribution.sh` produces a zip today and needs extending. The Homebrew CLI package is the other half. Spec: `docs/roadmap/PERMISSIONS-PLAN.md` Phase 2.

### 5. Tag `v0.7` and cut the release

`VERSION` reads 0.7 and nothing has ever been tagged at it. Tagging triggers the universal2 CI job, which has never run — **and it will not run as written: it is on `runs-on: macos-13`, an image GitHub has retired** (the test job hit the same wall in Aug and sat queued for 24 hours). Move it to `macos-15` in `.github/workflows/test-and-build.yml` before tagging, and check its python.org universal2 install still works there. steps 1-2 prove that build and its signature by hand first. Once the flow is known to work, the same six secrets can go into the repo's Actions secrets and tagged releases sign themselves — `docs/BUILDING.md` lists them. Upload both packages and capture report-card, terminal and breakdown screenshots for the landing page.

### 6. Retest on Tahoe

Launch fails on macOS Tahoe 26.4.1 / Apple Silicon (Micah Evans, 2026-04-13): `RBSRequestErrorDomain Code=5`, quarantined-binary symptoms. Expected cause is the unsigned binary under Tahoe's tightened Gatekeeper, so steps 1 and 4 are the expected fix. No machine here runs Tahoe — Micah retests once the `.app` is signed. Keep open until verified.

---

## Milestone 3 — Signed Beta Packages

Everything above is this milestone, plus:

- [ ] **Homebrew formula + tap.** `Formula/askdad.rb` has a placeholder URL and stale syntax; needs the real release URL and a `homebrew-tap` repo. Follows step 4's CLI package and step 5's release.
- [ ] **Clean-machine test matrix.** Intel + Apple Silicon; Sonoma/Sequoia/Tahoe. No Gatekeeper warnings, prompts attribute to the app.
- [ ] **`.app` bundle + app mode.** PyInstaller onedir `.app`, `Info.plist` usage strings, browser progress page via meta-refresh. Spec: `docs/roadmap/PERMISSIONS-PLAN.md` Phase 2.
- [ ] **Verify the permission UX on real hardware.** Phase 1 is unit-tested with mocked errno, but TCC only exists on macOS. Run the `PERMISSIONS-PLAN.md` matrix — `tccutil reset All`, then all-denied, partially-granted, and FDA-revoked-after-grant. Fits into the next real-Mac run.

## Milestone 4 — Full-Report Experience

- [ ] **First-run onboarding.** HTML welcome page: read-only promise, what macOS will ask, with-vs-without-FDA comparison, guided FDA walkthrough. Spec: `PERMISSIONS-PLAN.md` Phase 3.

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

## Scan Speed and Chart Design (opened Sep 15, 2026)

Raised by the real-Mac run that added `/Applications` and `/Library` to the scan. Measured on an M4: total **34s → 53s**, with the volume walk going **16s → 34s**. Batching app bundles into one `du -skx` per folder did not move it much, which points at the walk itself rather than at the apps.

- [ ] **Find out where the 34 seconds goes before optimizing it.** The walk is one phase and one number, so every theory about it is a guess — `/Library`, `/Applications`, or home as it always was. Cheapest instrument: accumulate wall-clock and item counts per top-level folder during the walk and print them under `--timings`. Decide with the numbers.
- [ ] **Overlap the phases.** `hidden caches` (11.5s) and `mac libraries` (5.6s) run after the walk (34s) and are almost entirely `du` subprocesses and file stats — IO, not Python. Running them in threads alongside the walk could take ~17s off the wall clock without touching the walk at all, and it is the largest single win available. Watch two things: the progress output would need serializing, and `hidden caches` re-measures parts of `~/Library` the walk has already stat'd.
- [ ] **Consider parallelizing the walk by top-level folder.** `/Applications`, `/Library`, `/Users`, `/opt` are independent subtrees, and `scandir`/`stat` release the GIL, so a small thread pool may scale on IO. Only worth trying once the per-folder timings say which subtree dominates. Keep the single-pass, one-stat-per-file rule intact.
- [ ] **Decide whether a shallower `/Library` is honest.** It is system-wide app support — real space, but not space a non-technical user should be clearing by hand. If it turns out to be most of the added time, a depth cap or a single `du` total for it (no per-file rows) buys the time back. `/Library/Caches` is already excluded.

- [ ] **`Library` now appears twice in the report.** It is a folder row carrying Messages and app support, and the Mac App Libraries section reports Messages separately — on the test Mac, a 92.3 GB row above a 30.1 GB library. The same gigabytes in two places, with nothing saying so. Either subtract what the libraries section already covers, or say plainly what the row contains.
- [ ] **Revisit the two-bar folder chart.** With `/Applications` and `/Library` included, "Other Folders" on a normal Mac is those two plus `/opt` and little else. The home/other split earned its keep when the home bar was an allowlist of seven names; now it may just be two short bars where one ranked list would do. Raised by the user as a design question, not a bug.

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

- [ ] **Downloads cleanup harness — the scan proposes, a rule engine executes.** The scan tells a user their Downloads folder is 40 GB. It does not help them do anything about it, and the read-only constraint means it never will on its own. A separate companion tool can: take the scan as input, hand the ambiguous files to a cheap LLM, and let the user act. It stays a companion, not a feature — the scanner's promise is that it never touches a file, and merging the two breaks that promise.

  **The design: the model writes rules, not filesystem calls.**

  1. The scan emits its JSON manifest (needs `--json`).
  2. A deterministic pass kills the easy 80% with no tokens spent — stale `.dmg`/`.pkg` installers, `Screenshot *.png`, `(1).pdf` duplicates, partial downloads, anything over 1 GB untouched for 90 days.
  3. One batched prompt classifies only what is left: name, extension, size, age and the scan's context in, `{path, action, destination, confidence, reason}` out. One call for a few hundred files costs cents on a small model.
  4. The model's answers become a generated rule file, applied by the same engine as step 2. That keeps one code path, and the dry-run, the audit log and the undo come free.
  5. Nothing is deleted. Files move to a dated staging folder (`~/Downloads/_review/<date>/`) with an `undo.sh` beside them — the same trust constraint the scanner keeps.

  The point of step 4 is that the rules outlive the model. When the model changes or goes away, the rules a user has accumulated still work.

  **Prior art, researched Sep 15, 2026.** [`tfeldmann/organize`](https://github.com/tfeldmann/organize) is the obvious engine: MIT, 3.1k stars, `pip install organize-tool`, YAML rules, an `organize sim` dry-run, and inline Python and shell as both filters and actions — so the whole harness can be two YAML files and a prompt. [Hazel](https://www.noodlesoft.com/) ($42, Mac-only) is what non-technical Mac users already trust for this, and it can run a script as a rule action, which makes it a delivery channel rather than a competitor. On the AI side, [`hyperfield/ai-file-sorter`](https://github.com/hyperfield/ai-file-sorter) (~1k stars, local or remote LLM, preview before move) and [`QiuYannnn/Local-File-Organizer`](https://github.com/QiuYannnn/Local-File-Organizer) (fully local) are the credible ones; [LlamaFS](https://github.com/iyaja/llama-fs) is a well-known hackathon demo and not a foundation. [`MatheusKindrazki/downloads-organizer`](https://github.com/MatheusKindrazki/downloads-organizer) has no users but has already written down this exact architecture — shell plus LaunchAgent plus a batched LLM call — and is worth reading before starting.

  **Be skeptical of the search results.** File Arbor, Sortio, VaultSort, Zush, Neatify and Files Magic AI each publish their own "best file organizer of 2026" roundups. That is SEO, not adoption. The tools with real history are Hazel, `organize`, DaisyDisk, CleanMyMac and Gemini 2.

  Depends on `--json`. Pairs with **Duplicate file detection** (the harness wants a duplicate list) and with the errand-based scoring idea above — "Downloads" is the first errand on that list, and this is what makes it actionable.
