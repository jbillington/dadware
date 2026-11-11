# Backlog & Roadmap

**Last Updated:** November 11, 2026

This file holds **only unshipped work, in the order it should be done**. Shipped work moves to `CHANGELOG.md`, which is also the day-by-day session record — look there for what was done and why. Detailed specs live in `docs/roadmap/`.

---

## What to do next (as of Nov 11, 2026)

Everything from the Nov 11 session is **merged to `main`** (PRs #29, #31, #32, #33, #34; record in `CHANGELOG.md`, "November 11, 2026 session"). The beta is now blocked on real-Mac checks and a clean build, not on code. In order:

1. **Run a fresh scan from `main` on the Intel Mac and read it.** The checklist under "Fix first" below says what to look at. Also open the scenario gallery (`scripts/render_scenarios.py`, see `CLAUDE.md`) and look at all 15 states once.
2. **Try the new AI prompt in a real AI** (Claude and ChatGPT): it should ask what to keep first and wait, sort the plan into Move to Trash / Keep / Back up first, and the file-names checkbox should drop the largest-files list. Fix wording from what the AI actually does.
3. **Decide whether the CPU report's AI prompt gets the same rebuild** (item under "Bugs"). Not needed for the beta.
4. **Clean release build and signing** (step 2 below). It was waiting on the copy edits; they are merged, so it is unblocked.
5. **Backup-drive check** (step 3), **CI image fix and tag `v1.0-beta`** (step 5), **Tahoe retest with Micah** (step 6).

`docs/roadmap/README.md` lists every plan with its status and next step.

---

## Fix first — found Nov 5, 2026

Bug #10 is fixed and merged (PR #27) and still needs a real-Mac check. Nothing else is open here besides the QA list.

- [ ] **QA the Nov 7, 2026 copy rewrite (PR #29) on a real Mac.** The tests pin the strings; they do not show how it reads on screen, or whether the flow still makes sense. Copy inventory: `docs/COPY-REVIEW-STORAGE.md` (Current copy = what ships; item numbers below match it). Run in a real Terminal on the Intel Mac, then once from the signed `.app`.

  **Terminal flow: run each, read every line**
  - [ ] **Launch (1.2).** First line after the banner. Fits one screen width? It no longer shows the build number (the banner still does).
  - [ ] **Several drives, press Enter (2.1, 2.2, 2.5).** Menu header, one row per drive, hidden-drives note, then `Your choice? (Enter for 1):`. Confirm Enter picks drive 1.
  - [ ] **Hidden drives note (2.3).** Mount a `.dmg`. Check the two-line note, and that it says to run `askdad`, which does not exist on a `.app` user's PATH.
  - [ ] **Prompt inputs (2.6, 2.7).** Try `7` (out of range), `abc`, an empty line, Ctrl+C and Ctrl+D. Numbers and words give the "isn't a number from the list" line; only Ctrl+C and Ctrl+D give "Ouch! You canceled me." Nothing should scan afterwards.
  - [ ] **One drive only (2.8).** Unplug everything. Check for "Only one drive here…", and that 1.2 and 4.1 around it do not read as a stutter.
  - [ ] **Non-interactive (2.9).** `echo | python askdad.py`. Auto-select line unchanged, no stray blank line where the home-scan note was.
  - [ ] **`--volume` cases (2.12, 2.13).** A bad path gives "Heads up… Choose again…". A `.dmg` mount gives the unchanged "Scanning it anyway" note.
  - [ ] **Thumb drive (4.1, 4.14).** Scan one. There is no "isn't the disk your home folder is on" notice any more. Check that the report is still the drive-only report with no grade.
  - [ ] **Permissions, first run (3.1, 3.2, 3.3).** Reset with `tccutil reset All` for Terminal. Check the explainer, the Terminal heads-up, and the dialogs. Allow all, then deny one folder, and read the matching line each time.
  - [ ] **Full Disk Access off, then on (5.1, 5.2).** Off gives the two-line warning and "I'm getting back to my scan now." On gives the single "Because you granted…" line.
  - [ ] **Report card (6.1).** `Ask Dad v1.0-beta` appears once in the header, and the date is on its own line.
  - [ ] **`askdad --version` and `--help`.** Both say "Ask Dad".

  **HTML report: open one and read it**
  - [ ] **Header and footer (9.2, 14.7).** "Ask Dad v1.0-beta | date"; footer "Ask Dad v1.0-beta, a DadWare joint. Happy cleaning".
  - [ ] **Dad says (8.x).** Trigger each: Downloads over 10 GB and over 5 GB, Desktop over 5 GB, and a clean Mac (8.6). Caches over 20 GB give "Separately, … a pretty large cache" and over 5 GB the shorter line. Snapshots older than a day give the 8.10 line.
  - [ ] **Hidden App Caches (12.2 to 12.7).** Three bullets now (the "leave them alone" one is gone). (The closing "Ask Dad never deletes anything for you." was removed Nov 11; the Next Steps box says it.)
  - [ ] **Local Snapshots (13.2 to 13.8).** Check a fresh case and a stale case. Stale shows the paragraph ending "yet." and the `tmutil` command with a one-line lead-in (the "Ask Dad won't run it for you" sentence was cut Nov 11). Macs with OS snapshots get 13.7.
  - [ ] **Permission notice (10.2) and next-steps callout (14.4).** Read both.

  **Added Nov 11, 2026: check on a real scan**
  - [ ] **Terminal intro.** Opening lines print one at a time (0.2 s apart) with `→`, no blank-line gaps, nothing wraps in an 80-column Terminal. Try one drive and several drives. Piped output (`echo | python askdad.py`) must not pause.
  - [ ] **Grade Breakdown.** Titles carry the weights ("Free Space (50% of grade)" ... "Mac Apps: Photos, Music, iMessages, & Mail (15% of grade)") with the new subtitles. With Full Disk Access off the Mac Apps title says "(not counted in grade)".
  - [ ] **Folder bars.** "Top 10 Home Folders" / "Top 10 Other Folders", the info icon and "Click each folder to view its top items" sit on the title's line, and clicking a bar still opens its items.
  - [ ] **Dad says.** Quick Wins bullets end the section; "View next steps" jumps to the Next Steps block. The old yellow Quick Wins box is gone.
  - [ ] **Removed copy stays gone.** No Trash blurb or caches aside under the report card, no "Folder totals do not include everything" note, no "Ask Dad won't run it for you", no em dashes anywhere in the report or Terminal.
  - [ ] **Scenario gallery.** Open all 15 states from `scripts/render_scenarios.py`. Look especially at `libraries-errors` (badges legible), `no-other-folders`, `few-folders`, `other-volume` (drive report), `disk-critical`.
  - [ ] **AI prompt, in a real AI.** Paste into Claude and ChatGPT. Step 1 should ask what to keep and wait. The plan should use Move to Trash, never permanent deletion, and end with "check, then empty the Trash". Untick "Include my largest file names" and confirm the copied text has no LARGEST FILES section. Search the prompt for your username (there should be none).

  **Open copy questions to settle while reviewing**
  - [ ] **"terminal" wording for `.app` users.** 3.2 and 5.1 say "this terminal" and "Terminal wants access". The `.app` build has no Terminal in the dialog.
  - [ ] **Voice mix.** The new verdict lines are sentence case; 8.4, 8.5, 8.10's second variant and the snapshot lines are still lowercase dad-casual. Pick one.
  - [ ] **Snapshot line, no oldest age.** 8.10 has a second variant ("holding on to {n} old copies of itself") that was not reworded to match.
  - [ ] **Dropped explanations.** 12.2 lost "none of it counts against your grade"; 13.2 lost why free space does not budge after deleting files. Intended?
  - [ ] **Delete advice.** 8.8 ("storage that you can delete") and 13.8 (a command that removes snapshots) lean toward advice. The rule is now "hold opinions lightly, never delete automatically" (CLAUDE.md); check they read that way.
  - [ ] **Long lines wrap badly.** 3.1, 3.3, 5.1 and 2.3 are long. Check in an 80-column Terminal.
  - [ ] **Old names elsewhere.** `site/index.html`, `README.md` and `USER-GUIDE` may still say "Dad Ware". Not checked. `docs/COMPETITIVE-COMPARISON.md` says "100% read-only", and the global `~/.claude/CLAUDE.md` says it "never deletes files". Both predate the softened rule.

  **Automated: what changed in the tests**
  - Changed to the new wording: `test_cli.py` (`--version`), `test_terminal.py` (report-card header), `test_permissions.py` (the FDA notice now checks "needs Full Disk Access" instead of "never counted as zero"; the granted line checks "granted"), `test_personality.py` (cache comment), `test_volumes.py` (hidden-drives note).
  - Snapshots regenerated: `tests/fixtures/storage_scan.snapshot.html` and `cpu_scan.snapshot.html`; the diff is copy only. `test_html_render.py` now scrubs "Ask Dad v…" and asserts it appears in the header and footer.
  - Full run: 522 passed, 1 skipped, after merging `main` (the `personality/dad.py` conflict kept main's "Separately," fix).


---

## Next — the road to a signed beta

**Signing is done (Nov 7, 2026):** a stapled DMG holding a notarized `Ask Dad.app` passed Gatekeeper on an Apple Silicon Mac. What is left to ship the beta is below, in order.

### 1. Sign and notarize — done Nov 7, 2026

Shipped; the record, the snags and the evidence are in `CHANGELOG.md` ("The first signed beta"). Kept here because it is the release procedure, and the setup has to be repeated on a new Mac. **Never commit any of these values; exports last one Terminal window.**

```bash
export DADWARE_CODESIGN_IDENTITY="Developer ID Application: JOHN N BILLINGTON (3HM5J8RJX6)"
export APPLE_API_KEY_ID="…" APPLE_API_ISSUER="…" APPLE_API_KEY_PATH="$HOME/.appstoreconnect/private_keys/AuthKey_….p8"
./build_executable.sh        # DADWARE_TARGET_ARCH=universal2, from a clean commit
./sign_and_notarize.sh       # signs + notarizes the bare binary
./make_app.sh                # wraps it in Ask Dad.app; signs, notarizes, staples
./make_dmg.sh                # DMG with the app and an Applications shortcut; signs, notarizes, staples
```

Setup that lives outside the repo: the Developer ID Application certificate and its private key in the `login` keychain on the 2017 Intel Mac (plus the Developer ID G2 intermediate), and the App Store Connect API key (`.p8`, downloads once, backed up Nov 7). **Still open:** a clean-machine run on an Intel Mac that is not this one, and one with no network, both under Milestone 3.

### 2. The release build, from a clean commit

The universal2 build now works **on the Intel Mac itself**, with the python.org 3.13 universal2 Python (the Homebrew Pythons are x86_64 only) — `lipo -info dist/askdad` reads `x86_64 arm64`, and it ran on the Intel slice here and the arm64 slice on an M1 (macOS 15.7.3). What is left is to build it again **from a committed `main`** (the copy edits merged Nov 11, `main` at `1a9a556`, so this is unblocked), so the `Build:` banner names a real commit instead of `…-dirty`, then run the procedure in step 1. Spec: `docs/roadmap/ARCH-COVERAGE-PLAN.md`.

### 3. Check a mounted backup drive on a real Mac

The last unverified piece of the volume-crossing fix (Bug #8). With an external or Time Machine drive attached, a scan of `/` should finish, and its item count should match the unplugged run (~332k, not ~678k). Everything else about that fix is confirmed on the M1: a scan of `/` still shows the home folder breakdown, and a thumb drive scan reports on the drive alone. Spec: `docs/roadmap/VOLUME-CROSSING-PLAN.md`.

### 4. Native app mode — later

The beta package is a **stapled DMG holding `Ask Dad.app`**, built by `make_app.sh` and `make_dmg.sh`; it passed Gatekeeper on an M1 (AirDrop, macOS 15.7.3). That app is a thin launcher: it opens Terminal running the bundled scanner, so **Terminal, not Ask Dad, owns every permission prompt and the Full Disk Access grant**. What is not built: a real app that runs without Terminal, the `Info.plist` usage strings that put Dad's voice in the system dialogs, and the browser progress page. Spec: `docs/roadmap/PERMISSIONS-PLAN.md` Phase 2. The Homebrew CLI package is **not part of this beta** — testers get the link on the website.

### 5. Tag `v1.0-beta` and cut the release

`VERSION` is `1.0-beta` and nothing has been tagged. Tagging triggers the universal2 CI job, which has never run — **and it will not run as written: it is on `runs-on: macos-13`, an image GitHub has retired** (the test job hit the same wall in Aug and sat queued for 24 hours). Move it to `macos-15` in `.github/workflows/test-and-build.yml` before tagging, and check its python.org universal2 install still works there. Signing is proven by hand; once the clean rebuild is done, the six secrets can go into the repo's Actions secrets so tagged releases sign themselves (`docs/BUILDING.md` lists them — the DMG step needs `make_app.sh` and `make_dmg.sh` added to the workflow). Upload the DMG, and capture report-card, terminal and breakdown screenshots for the landing page **from `tests/fixtures/storage_scan.snapshot.html`, not a real scan** — a real report lists filenames (licenses, tax and medical papers) and the home path. Put one line on the landing page: macOS asks "are you sure?" for any downloaded app, and that is normal.

### 6. Retest on Tahoe

Launch fails on macOS Tahoe 26.4.1 / Apple Silicon (Micah Evans, 2026-04-13): `RBSRequestErrorDomain Code=5`, quarantined-binary symptoms. Expected cause is the unsigned binary under Tahoe's tightened Gatekeeper, so the signed, stapled `.app` in the DMG is the expected fix. The only other Apple Silicon test so far was macOS 15.7.3, not Tahoe. No machine here runs Tahoe — Micah retests with the beta DMG. Keep open until verified.

---

## Milestone 3 — Signed Beta Packages

Everything above is this milestone, plus:

- [ ] **Homebrew formula + tap.** *(Not needed for the beta — testers get a website link.)* `Formula/askdad.rb` has a placeholder URL and stale syntax; needs the real release URL and a `homebrew-tap` repo. Follows step 4's CLI package and step 5's release.
- [ ] **Clean-machine test matrix.** Intel + Apple Silicon; Sonoma/Sequoia/Tahoe. Done so far: Apple Silicon, macOS 15.7.3, AirDrop — the normal "are you sure" prompt with Apple's no-malware line; that Mac's Terminal already had Full Disk Access. Still to run: an Intel Mac that is not the signing Mac, Tahoe, a Mac with no network (checks the staple), and a Mac whose Terminal has no access.
- [ ] **App mode.** The interim `Ask Dad.app` launcher shipped (it opens Terminal). Still to do: a Terminal-free app (PyInstaller onedir or the Swift wrapper), `Info.plist` usage strings, browser progress page via meta-refresh. Spec: `docs/roadmap/PERMISSIONS-PLAN.md` Phase 2.
- [ ] **Verify the permission UX on real hardware.** Phase 1 is unit-tested with mocked errno, but TCC only exists on macOS. Run the `PERMISSIONS-PLAN.md` matrix — `tccutil reset All`, then all-denied, partially-granted, and FDA-revoked-after-grant. Fits into the next real-Mac run.

## Milestone 4 — Full-Report Experience

- [ ] **First-run onboarding.** HTML welcome page: read-only promise, what macOS will ask, with-vs-without-FDA comparison, guided FDA walkthrough. Spec: `PERMISSIONS-PLAN.md` Phase 3.

## Milestone 5 — Beta Launch

Family first, then friends on unseen Macs, then Reddit (r/macapps). Waits on Milestone 3 — the signed DMG removes the security-warning friction. Plan: `docs/TESTING-AND-LAUNCH.md`.

- [ ] **Feedback invitation and CPU-scan cross-promo.** Terminal ending and report footer invite beta testers to email John; the storage run and report point to the CPU scan (`askdad cpu`), and the CPU report points back. Needs the feedback address chosen first. `.app` users get the CPU scan two ways (decided Nov 11): an end-of-scan "Check memory and CPU too? [y/N]" prompt (B), and `make_app.sh` putting the bundled `askdad` on the PATH of the Terminal window it leaves open (A; needs an app rebuild and re-sign). **Ship only after the CPU report fixes** (the "CPU report calls memory pressure high" bug below). Spec: `docs/roadmap/FEEDBACK-AND-CPU-PROMO-PLAN.md`. Do before the beta goes out to testers.

---

## Bugs

- [ ] **CPU report calls memory pressure "high" on almost any Mac, and shows free RAM four ways.** Verified Nov 11, 2026: `scanners/cpu.py:107` triggers on `Swapouts > 1000`, a since-boot counter, while the kernel (`kern.memorystatus_vm_pressure_level`) says normal. Do this **before** the CPU cross-promo ships. Items A1-A8 in `docs/roadmap/CPU-REPORT-FIXES-PLAN.md` (pressure source, wording, one definition of free, command lines out of the AI prompt).

Reviewed Nov 7, 2026 against PRs #24 (merged) and #26 (open, copy review only). Fixed and merged (PR #27): the "of that" wording, the Messages "most of this" claim, and the home-walk item count (now `found N items in <path>`). Also merged, awaiting a real-Mac check: Bug #10 (`~/Library` vs `/Library` labels, "Not included" note, "Messages cache") and the report-card coverage line. Open: chart labels, backslash names. PR #26 revises copy in `docs/COPY-REVIEW-STORAGE.md`; re-check `personality/dad.py` wording against it before merging.

- [ ] **Add a "What the scan couldn't read" section at the bottom of the report.** Plain reasons with counts: items left out on purpose, and items macOS blocked. It replaces the "Folder totals do not include everything on the disk" note, which was removed from the HTML report on Nov 11, 2026 because it named Mail and Messages as left out while the report shows their sizes right above it, which reads as a contradiction. `describe_coverage()` in `utils/llm_prompt.py` and `left_out_note()` in `utils/path_utils.py` still carry the data.
- [ ] **CPU and generic AI prompts still use the old format.** Only the storage prompt was rebuilt Nov 11 (plan request, `~` paths, privacy checkbox). `generate_cpu_prompt()` and `generate_generic_prompt()` keep the old intro, "ADVISOR'S ASSESSMENT" heading and question tail. (The CPU prompt's command lines, which carried absolute paths, were removed Nov 11; see CHANGELOG.) Bring them in line, or leave them until the CPU report is next in line.
- [ ] **Contrast is only guarded for the library badges.** `tests/test_scenarios.py` fails any badge under 4.5:1; nothing checks the rest of the report. A whole-report check needs a real browser (or an axe-style audit) in the test run.
- [ ] **Chart labels clip and tiny segments go unlabeled.** `Downloads` shows as `Downloa` in the Home Folders bar. Fold into the two-bar chart redesign under Scan Speed and Chart Design.
- [ ] **Files with backslashes in their names appear as folder rows** (`Library\CherryAudio\DCO-106`, 8.7 MB). Handled safely, harmless noise from a Windows or Wine copy.


## Report content — deferred, not blocking

- [ ] **No next step for a bad library grade.** Messages graded **F at 29.9 GB** with nothing telling the user what to do. A grade without an action is a scolding. Needs per-library advice (Messages: attachment management and "Keep Messages" retention; Photos: iCloud optimization; Mail: rebuild and attachment cleanup) in the same read-only advisory framing as the snapshot section. Graded libraries only — caches are not graded.
- [ ] **Nothing measures the big third-party stores.** The Mac App Libraries grade covers Apple's five, so on a developer's or gamer's Mac the largest pile on the disk can be missing from the graded section: **Steam** (`~/Library/Application Support/Steam/steamapps`, routinely 100 GB+), **Xcode** (`DerivedData`, `iOS DeviceSupport`, archives), **iOS Simulator runtimes** (`~/Library/Developer/CoreSimulator/Devices`), possibly Adobe. Two questions first: graded or reported like caches (a big Steam folder is not clutter if the games are played), and how much `scanners/hidden_storage.py::scan_developer_caches()` already picks up. **Leave the Docker handling alone** — `utils/path_utils.py` deliberately sizes sparse images by `st_blocks * 512`; a new scanner sits alongside it.
- [ ] **Orphaned caches: cross-reference cache folders against installed apps.** `build_app_name_index()` already knows what is installed, so flagging caches for apps you no longer have is nearly free — and it is the one cache category worth clearing for good.
- [ ] **Remember the permission *state*, not just a flag.** `~/.dadware/.permissions-introduced` is a bare boolean, so the explainer never runs again — wrong in both directions. After a `tccutil reset`, a migration, or revoked grants the dialogs come back unexplained; and when someone takes the advice and switches Full Disk Access on, nothing acknowledges it. Store `{introduced, fda, folders: {Desktop: granted, ...}, last_run}` — every value is already computed each run, so it is a write, not new work. The rules then become transitions: explain when there is no record or a folder went back to denied; say one line when FDA flipped off→on; stay silent otherwise. **Two constraints or it becomes noise:** speak only on a transition, and only when the news is good or actionable — never announce "you turned FDA off", the report already shows the blanks. Migration is trivial: the existing plain-text file means "introduced, state unknown".
- [ ] **Snapshot size.** `scanners/snapshots.py::_parse_diskutil_plist()` reads only `SnapshotName` and `Purgeable`. Run `diskutil apfs listSnapshots -plist /System/Volumes/Data` on a Mac and dump every key. If a size key exists, ship single-snapshot sizing — with exactly one snapshot, "what would I get back" is a well-formed question. If it does not, point the user at Finder → Get Info, which shows a purgeable total.
- [ ] **Research how CleanMyMac / DaisyDisk / Sweep handle units, purgeable and cache-safety copy.** Prompt ready at `docs/research/COMPETITOR-UX-RESEARCH-PROMPT.md`. Much narrower than when written — units, purgeable and the cache-safety message are all decided. Nothing live depends on it. Would extend `docs/COMPETITIVE-COMPARISON.md`.

## Report review — insight, voice, and views (opened Nov 6, 2026)

From a read of `tests/fixtures/storage_scan.snapshot.html` rendered in a browser. The page is built for one reader — a parent fixing the Mac — and serves the kid who wants a verdict and the LLM that wants data less well. Three groups: what would make the report say more, what would make it more fun to read, and whether it should have more than one view.

### More insightful

- [ ] **Show where all 420 GB went.** The sample says 420 GB used, then shows 48 GB of folders and 54 GB of libraries, and nothing says where the other 300 GB is. Add one stacked bar at the top of the card: Photos, apps, your folders, caches, Trash, snapshots, system, and "not measured". The "not measured" segment is the rendering fix for the `excluded_count` / `denied_count` bug under Bugs. This is the question Apple's Storage panel answers with a "System Data" blob and the report answers not at all.
- [ ] **Fix the "Reclaimable 7.4%" stat.** It sums the top 25 files. In the sample that includes `Xcode.app` and the Docker disk, which nobody should delete, so the number is wrong in the direction that gets a user hurt. Replace it with "easy wins": Trash + installers + caches + screenshots — bytes a person can act on in ten minutes. Pairs with the errands item in the Feature Pool.
- [ ] **Explain the big files.** The product's thesis is interpretation, but the sample does not say what `docker-desktop-data.qcow2` is. A small table keyed on extension does it: "Docker's virtual disk — shrinks from Docker's settings, not Finder." Same for `.dmg` (an installer you probably already ran), `.key`, `.sql`, `.app`, `.ipa`, `.iso`. One line per type, shown under the file name in the table. Cheap, and exactly on thesis.
- [ ] **Group files that are alike.** The table shows `installer-01` through `installer-10` and thirteen `build-artifact` zips as 23 rows. Show one row — "12 installers in Downloads, 2.9 GB, oldest 14 months" — and expand on click. Group on folder + extension. The walk already keeps a `stat_result` per file, so the age costs nothing.
- [ ] **Add time: the delta since the last scan.** "Since your last scan, Downloads grew 3 GB" is more useful than any ratio in the grade breakdown. Depends on **Report history** in the Feature Pool; the delta is that feature's payoff, so build them together.
- [ ] **Shrink the permission notice.** It is the largest block above the fold, and the grade card already marks the gaps as "needs Full Disk Access". Collapse it to one line with a link to the settings pane; expand on click.

### More fun to read

- [ ] **Put Dad at the top, not in a grey box.** Two one-liners sit below the permission warning. Lead the card with a one-sentence verdict, like the comment line on a school report. Then give each section its own line of Dad — the folder chart, the Trash row, the snapshot section each get a remark. The voice is the product; today it is the smallest box on the page.
- [ ] **Translate bytes into things.** "14 GB in the Trash" means little to a kid. "That is 3,000 songs" or "seven movies" does. One helper in `utils/formatters.py` covers the whole report; use it beside the big numbers, not instead of them.
- [ ] **Errands with checkboxes.** Extends the scoring item in the Feature Pool. Each errand (Empty the Trash, clear old installers, move the screenshots) gets a checkbox that remembers its state in `localStorage`. A user who comes back to three ticks and a better grade has a reason to run the scan again. Still read-only: the box records that *they* did it.
- [ ] **Finish the report-card metaphor.** Teacher comments, a gold star for an A, "signed, Dad" at the bottom. Keep it gentle — a kid with an F should feel coached, not scolded.
- [ ] **Add voices.** The Code Quality section already plans `personality/mom.py` as a table of strings. Make the persona a flag — Dad, Mom, Grandpa, Coach — once the analysis has moved out of `personality/`. Only the strings change.
- [ ] **Grow the comment pool.** Already in the Feature Pool; listed here because the sample makes the problem visible: two lines, and they repeat.

### Different views — yes, two pages in one file

- [ ] **Fridge view.** One screen: grade, verdict, the storage bar, three errands. Printable. This is the default.
- [ ] **Full view.** Everything the report shows today, plus snapshots and caches, behind a "show me everything" toggle.
- [ ] **Agent view** is the planned `--json` and `--prompt` flags, not a page.
- [ ] **Both page views live in the same HTML file** with a tab toggle in `REPORT_JS`, so the report stays self-contained. The precedent exists: `render_html()` already assembles a different report for an external volume. Simple and full are the same idea with a switch instead of a scan scope, and both call the same section functions.

## Grading fixes (opened Nov 6, 2026)

From a read of `docs/GRADING.md` against the sample report. The proposal is written up as §9 of that document; these are the pieces, in build order. The principle: grade only what slows the Mac and what the user can fix in ten minutes. Everything else is a fact with context, not a letter.

- [ ] **Health grade: free space with a kinder, two-part ladder.** Today F begins under 15% free, so a 500 GB disk with 70 GB free fails, and the ladder ignores absolute size (10% of a 4 TB disk is 400 GB). New rule: a letter passes on percentage *or* absolute amount, whichever is kinder — A at 20% or 100 GB, B at 15% or 50 GB, C at 10% or 25 GB, D at 5% or 10 GB, F below both. Table in `docs/GRADING.md` §9. Re-baselines every tester's grade, so ship with the layout redesign, not alone.
- [ ] **Drop Home Folders Ratio.** It punishes a person for having files: 300 GB of photos on a 2 TB drive scores F on it with 85% free. It tells the user to do nothing, because there is nothing to do. Remove the component, its weight, and its tests.
- [ ] **Mac App Libraries become facts, not a grade.** The same 60 GB photo library gets an A, B or C depending on the disk it sits on (the share penalty), and a letter on a library is a scolding with no action. Keep the per-type thresholds only to say "normal for a family library"; drop the share penalty and the letter; fold in the per-library advice from "No next step for a bad library grade" above.
- [ ] **Remove the composite.** Free Space is half the weighted average and the other three components are pinned at A on most Macs, so the top letter is free space with decoration. Show two letters side by side, each with one sentence. Where one screen needs one letter (the fridge view), use Health, with "A after chores" and the projected free space beside it.
- [ ] **CPU Health thresholds.** The storage Health grade needs a sibling: memory pressure and swap in use. Pairs with the existing "CPU/RAM grading thresholds have never gotten the scrutiny storage got" item in the Feature Pool; do both at once.
- [ ] **Chores grade — under consideration, not decided.** Start at 100; each chore costs 5 points plus 1 point per 1% of the disk it holds, capped at 25; do every chore and the score is 100. Candidates: Trash, installers in Downloads older than 30 days, screenshots and screen recordings, orphan caches, stale snapshots, old device backups, developer piles, Downloads or Desktop over 5 GB. Would replace Home Folders Clutter and absorb the errands item in the Feature Pool, and it is the honest "Reclaimable" number for the card. Decide it before building; the four items above do not depend on it.
- [ ] **One source of findings.** Once Health (and the chores, if adopted) are computed in `scanners/grading.py`, Dad's remark, the letters and the next steps read the same list, and §7–8 of `docs/GRADING.md` (why the grade and the comment disagree) can go. This is the Code Quality item "Move the analysis out of `personality/`" with a reason to do it now.
- [ ] **Rewrite `docs/GRADING.md` §1–8 when the above ships.** The document describes the code as it runs; §9 is the only section that describes a plan. Once the plan is code, §9 becomes the body and the old sections move to `CHANGELOG.md`.

## Metrics worth adding (opened Nov 6, 2026)

A brainstorm from the same report review, kept whole so nothing is lost. Most come from data the scan already holds: the walk keeps a `stat_result` per file, so ages and types are free. The rest cost one cheap subprocess each. "Already measured" means the number exists in the manifest and only needs a place on the report. Order within each group is rough value for effort.

### Where the space is

- [ ] **Storage budget.** Apps, Photos, your files, caches, Trash, snapshots, system, not measured. One bar that adds up to the disk. Same item as the first one under "Report review" above; listed here so the metric list is complete.
- [ ] **Free space after chores.** Free space today plus every byte the chores would return. The number the user actually wants. Depends on the chores decision under "Grading fixes".
- [ ] **Growth since the last scan,** and days until full at that rate. Depends on **Report history** in the Feature Pool.
- [ ] **Largest app you never open.** App bundle sizes (already measured) beside last-opened dates: one `mdls -name kMDItemLastUsedDate` per app, or the bundle's access time as the no-subprocess fallback.

### Dust: what has not been touched

- [ ] **Dormant bytes.** Files not opened in one, three and five years, as a share of your files. Access time from the stat the walk already holds.
- [ ] **Your oldest file.** Birth time from the same stat. A time capsule, and it teaches what a file date is.
- [ ] **Installers you already ran.** `.dmg`, `.pkg` and `.zip` in Downloads older than 30 days, with count, size and oldest.
- [ ] **Screenshots and screen recordings.** Count, size and oldest. Finder names them ("Screenshot ", "Screen Recording "), so the match is a filename test.
- [ ] **Trash: size, item count, age of the oldest item.** Already measured; only the count and age are missing from the report.

### Things that hide

- [ ] **iPhone and iPad backups.** Each folder under `~/Library/Application Support/MobileSync/Backup` has an `Info.plist` with the device name and the last backup date. "A 23 GB backup of Dad's iPhone 11 from 2022" is the best line the report could print. Forum research names this folder more than any other.
- [ ] **Orphan caches.** Cache folders for apps no longer installed. Same as the Report content item above; `build_app_name_index()` already knows what is installed.
- [ ] **Developer piles.** Xcode DerivedData, simulator runtimes and archives are already measured; add the count and total size of every `node_modules` folder the walk passes.
- [ ] **Docker and VM disks.** Space used on disk beside the provisioned size. Both numbers already exist (`st_blocks` vs logical size); show them together.
- [ ] **Snapshots: count and age of the oldest.** Already measured and shown; keep.
- [ ] **iCloud placeholders.** Files whose data lives only in iCloud, counted by the dataless flag in `st_flags`. Shows whether Optimize Storage is doing anything, and why a folder looks big in Finder but small on disk.
- [ ] **Other user accounts.** The size of each folder under `/Users`. Parents forget the old account.

### File mix

- [ ] **Bytes by kind.** Video, photos, archives, installers, disk images, build output, documents. Keyed on extension; the same table drives the file-type explanations under "Report review".
- [ ] **Duplicate candidates.** Same name and same size, no hashing. Catches "report (1).pdf". The hashed version stays in Future.
- [ ] **Counts by size band.** Files over 1 GB, and between 100 MB and 1 GB.

### Memory and CPU scan

- [ ] **Swap in use and compressed memory.** `vm_stat` already supplies both; memory pressure is shown, these two are not. Together they say whether the Mac is coping or hiding it.
- [ ] **Browser tab tax.** Browser RAM total and process count, as one line per browser. The grouping exists in `personality/dad.py`; make it a metric on the card, not only a remark.
- [ ] **Days since restart.** `sysctl kern.boottime`. The dad classic, and often the fix.
- [ ] **Login items and background agents.** Count of what starts with the Mac, from `launchctl list` filtered to user agents. Startup load the user never sees.
- [ ] **Sustained CPU hogs.** Processes over 50% CPU across the sample window, not one instant. The scan samples once today; a second sample a few seconds later tells steady from spike.
- [ ] **Disk SMART status.** One `diskutil info` call. Usually "Verified", and worth a reassuring line.
- [ ] **Health grade for memory.** Memory pressure and swap, as the sibling of storage Health. Tracked under "Grading fixes".

### Translated for the reader

- [ ] **Bytes as things.** Songs, movies, photos. Same item as under "Report review"; every big number above gets the translation beside it.

## Scan Speed and Chart Design (opened Sep 15, 2026)

Raised by the real-Mac run that added `/Applications` and `/Library` to the scan. Measured on an M4: total **34s → 53s**, with the volume walk going **16s → 34s**. Batching app bundles into one `du -skx` per folder did not move it much, which points at the walk itself rather than at the apps.

- [ ] **Find out where the 34 seconds goes before optimizing it.** The walk is one phase and one number, so every theory about it is a guess — `/Library`, `/Applications`, or home as it always was. Cheapest instrument: accumulate wall-clock and item counts per top-level folder during the walk and print them under `--timings`. Decide with the numbers.
- [ ] **Overlap the phases.** `hidden caches` (11.5s) and `mac libraries` (5.6s) run after the walk (34s) and are almost entirely `du` subprocesses and file stats — IO, not Python. Running them in threads alongside the walk could take ~17s off the wall clock without touching the walk at all, and it is the largest single win available. Watch two things: the progress output would need serializing, and `hidden caches` re-measures parts of `~/Library` the walk has already stat'd.
- [ ] **Consider parallelizing the walk by top-level folder.** `/Applications`, `/Library`, `/Users`, `/opt` are independent subtrees, and `scandir`/`stat` release the GIL, so a small thread pool may scale on IO. Only worth trying once the per-folder timings say which subtree dominates. Keep the single-pass, one-stat-per-file rule intact.
- [ ] **Data point from the 2017 Intel Mac (Nov 5, 2026).** MacBookPro14,2 (i7-7567U, 2 cores, 16 GB, macOS 13.7.8, 91% full): the whole run took **203.9 s** and `hidden caches` took **36.7 s** of it. The report saves no other per-phase timings, so the rest (~165 s) is the walk plus Mac libraries, split unknown. **Guess, not profiled:** 60-90 s is reachable here, and 45-60 s with more work. Run `--timings` on this Mac first to confirm. The ideas below are on top of "Overlap the phases" and "parallelizing the walk" above.
- [ ] **Measure Messages and Caches concurrently, or reuse the walk's results.** A bare `du -sk` over just `~/Library/Messages` and `~/Library/Caches` took **22 s** on this Mac, a large share of the work for two folders. They are sized separately from the walk (they are excluded from it on purpose), so they are independent and safe to run in parallel with it. If the Mac libraries scan and the hidden caches scan each size them, check that nothing is measured twice.
- [ ] **Thread the walk to the hardware.** This Mac is 2 cores / 4 threads. Disk waits release the GIL, so 3-4 workers over the top-level folders might give around 2x on the walk. Unverified; the per-folder timings above decide whether it is worth the complexity. Keep the one-stat-per-file rule.
- [ ] **Cache folder sizes between runs.** Key a saved size on the directory's mtime, so an unchanged subtree is not re-walked. A second scan might drop to 10-20 s. Unverified, and invalidation needs care: a directory's mtime does not change when a file deep inside it grows, so this likely needs a depth limit or a short expiry. Never trust a cache for a delete decision (the tool never deletes, but its numbers drive advice).
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
- [ ] **Persona: "Dad's guess at who you are."** Infer developer / designer / photographer / musician / gamer / student and a dozen more from installed apps, the Dock, file extensions by count and bytes, developer caches and library sizes — names and sizes only, never content. The persona changes four things: the noun in "normal for a family library", which chores apply, one Dad line, and the first sentence of the LLM prompt. On-device, occupations and hobbies only, never age, never a sensitive category, opt-out with one flag. Full signal table and privacy rules: `docs/roadmap/PERSONA-PLAN.md`. The first two steps (an extension tally in the walk, reading `com.apple.dock.plist`) are useful metrics on their own.
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
