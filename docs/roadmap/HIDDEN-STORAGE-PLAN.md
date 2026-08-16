# Hidden Storage PRD

**Status:** Proposed
**Effort:** Phase 1: 7-10 hours. Phase 2: 2-3 hours.
**Depends on:** Phase 2 requires the Full Disk Access work in `PERMISSIONS-PLAN.md`.

---

## The Problem

"My Mac says it's full. I deleted a bunch of stuff. Nothing changed."

This is one of the most common — and most demoralizing — Mac storage experiences, and it hits Dad Ware's core audience (young, non-technical users) hardest, because the space that's missing is invisible on purpose:

- **App caches** pile up in `~/Library/Caches`, a folder most users have never seen. Spotify's streaming cache, Discord, browsers, and game launchers routinely stash 5-30 GB there.
- **Purgeable space and APFS snapshots** hold onto gigabytes after files are deleted. If Time Machine was ever switched on — even if the backup drive has been in a drawer for a year — macOS keeps making hourly local snapshots that quietly retain old data.
- **The Trash** is the first thing anyone tells you to empty, and plenty of users forget it's there.

Finder shows none of this clearly, and today's Dad Ware scan can't see any of it either: caches, hidden folders, and the Trash are all excluded from the scan, and snapshots aren't files at all. The result is a report card that grades a drive as full without being able to say why.

## The Feature

New findings woven into **the existing storage report** — the one HTML report card the storage scan already produces. This is not a separate report or a new mode: the scan gets smarter, and the report the user already knows gains the answers it couldn't give before, explained in plain dad language, without the tool ever touching a file itself.

Four capabilities, built in four pieces (each maps to a phase in the technical plan below):

| Capability | Phase | User benefit |
|---|---|---|
| **App cache finder with real app names** | 1a | "Spotify — 8.2 GB of songs you already streamed." The user learns which app is hoarding and that it's safe to clear, in words they recognize — not `com.spotify.client`. |
| **Developer cache bonus** | 1b | For the minority of users with dev tools: surfaces Docker/Colima VMs, Xcode DerivedData, npm/Gradle caches — often the biggest single files on those machines. Costs nothing for everyone else. |
| **"Where'd my space go?" explainer** | 1c | Answers the deleted-files-but-still-full mystery: shows purgeable space and local Time Machine snapshots, with honest advice on getting the space back. A trust-building "this app actually understands my Mac" moment competitors bury or skip. |
| **Trash size** | 2 | The simplest win in storage cleanup, currently invisible to the scan. "You took out the trash but left the bag by the door." |

Phase 1 (a, b, c) needs no new permissions and ships together as one release; Phase 2 waits on the Full Disk Access work in `PERMISSIONS-PLAN.md`.

**Positioning:** explanatory and safety-first, not a cleaner. Dad Ware stays 100% read-only — it never deletes, moves, or changes anything. Every recommendation is advice the user carries out themselves, which is also the product's core trust promise.

## Target User

Young adults and teenagers who are not computer literate — people who have never backed up or cleaned up a Mac. Developers are a real but secondary segment: developer-specific checks are included only where they add zero cost for everyone else, and marketing copy and report headlines always lead with mainstream apps.

---

## Design Constraints

- **Read-only.** Detect and advise; never delete. Cleanup commands (including Apple's `tmutil thinlocalsnapshots`) appear as labeled, copy-pasteable advice with clear "run this yourself" framing. No delete or thin buttons — this was considered and rejected to protect the read-only trust story, which also underpins the permissions strategy.
- **Stdlib only.** `subprocess` + `plistlib` + `os`. No new dependencies.
- **Graceful degradation and time budgets.** Same patterns as `scanners/cpu.py` and `scan_all_mac_libraries()`: per-call timeouts, `log_subprocess_call`, partial results instead of failures.
- **Python 3.9 compatible** (CI floor).

## Why the Current Scan Can't See Any of This

`should_exclude()` in `utils/path_utils.py` drops any basename starting with `.` and everything under `/Library/Caches/`, `/tmp/`, `/private`, `/var`. Consequences:

- `~/Library/Caches` totals ~0 in every report.
- Hidden dev heavyweights are invisible: `~/.npm`, `~/.cache`, `~/.gradle`, `~/.m2`, `~/.cargo`, `~/.pyenv`, `~/.ollama`.
- Container runtimes in hidden folders are invisible even though the codebase has Docker-aware sizing via `is_docker_path` and `st_blocks * 512`: legacy `~/.docker`, Colima `~/.colima`, OrbStack `~/.orbstack`, Lima `~/.lima`. Docker Desktop's current location under `~/Library/Containers/com.docker.docker/` *is* reachable by the main walk — the blind spot is the hidden-folder variants.
- `~/.Trash` is invisible — and it's also TCC-protected, see Phase 2.
- Snapshots and purgeable space aren't files at all; no directory walk can find them.

**Do not fix this by removing the dotfile exclusion from the main walk.** That would drag every scan through `.git` object stores and `.venv` trees — thousands of tiny files, much slower scans, noisy results. The exclusions are load-bearing. Instead, add targeted scanners that go directly to known hidden locations.

---

## Phase 1a: App Caches

New module: `scanners/hidden_storage.py`.

The core target is `~/Library/Caches` plus `~/Library/Logs` — present on every Mac, invisible in today's reports, and frequently the single biggest recoverable pile on a non-technical user's machine. Size it **per-subfolder** so the report shows *which app* is hoarding, not one opaque total.

**Friendly app names are part of the feature, not a nicety.** Cache folders are named things like `com.spotify.client`, which is meaningless to the target user. Map bundle IDs to app names: match against bundle names in `/Applications` first, else strip the reverse-DNS prefix and title-case the last component. Advice copy leads with mainstream apps ("caches regenerate — Spotify will re-download what you actually listen to"); developer-tool copy exists but never headlines.

Access follows the `mac_libraries.py` philosophy: known paths accessed directly, so the main walk's exclusion rules never apply.

## Phase 1b: Developer Caches and Hidden-Folder Sweep

Near-zero cost for non-developers — an `os.path.exists()` check on a missing path is a stat call — and high value for the developer minority.

| Category | Paths |
|---|---|
| Developer | `~/Library/Developer/Xcode/DerivedData`, `~/Library/Developer/Xcode/iOS DeviceSupport`, `~/Library/Developer/CoreSimulator` |
| Container runtimes | `~/.docker`, `~/.colima`, `~/.orbstack`, `~/.lima` |
| Package managers | `~/.npm`, `~/.cache`, `~/.gradle`, `~/.m2`, `~/.cargo`, `~/Library/Caches/Homebrew` |
| ML/AI | `~/.ollama`, `~/.lmstudio` |

Plus a generic hidden-folder sweep, since no allowlist can know every tool: `os.scandir(home)`, take every directory whose name starts with `.`, size each, and report any over a threshold (default 1 GB). A typical home has 20-60 dot-directories; on a non-technical user's Mac this finds little and costs little. `.Trash` will raise a permission error here — route it to the Phase 2 messaging rather than reporting 0.

**Sizing implementation for 1a and 1b: use `du -skx` per folder, not a Python walk.** The codebase already has this pattern in `get_photos_library_size()` — one subprocess per folder with a timeout, C-speed, full depth, disk-accurate blocks. A bounded-depth Python walk has two problems here: npm/pnpm/Hugging Face cache trees nest deeper than any reasonable depth cap, so a capped walk under-reports exactly the folders this feature exists to expose; and a reporting size floor saves no scan time, because you can't know a folder is small without fully measuring it. Keep a Python-walk fallback for when `du` fails, and treat the per-folder timeout as the real cost bound.

### Wiring for 1a/1b

- `yourdad.py`: attach as `scan_data['hidden_caches']` during the storage scan.
- `scanners/grading.py`: new component grade — thresholds on total hidden-cache GB.
- `personality/yourdad.py`: "spotify's been stashing 8GB of songs you already listened to. it's not a music library, it's a junk drawer." / "you've got 23GB of caches squirreled away in hidden folders. the Mac equivalent of finding cash in old coat pockets."
- `renderers/terminal.py` + `renderers/html.py`: a "Hidden Caches" section added to the existing storage report, with friendly app names; HTML reuses the existing expandable-section pattern. No new report file.
- `utils/llm_prompt.py`: include the new data.

## Phase 1c: Purgeable Space and Local Snapshots

Built as its **own scanner with its own section in the storage report, separate from the caches work** — it answers a different user question ("why didn't deleting things free up space?" vs. "what's secretly taking up space?"), uses different techniques (subprocess parsing vs. directory sizing), and keeping the two independent means either can ship or be tested without blocking the other. Separate code and separate report sections, but the same single storage report. Implement as separate functions in `scanners/hidden_storage.py` or a sibling module such as `scanners/snapshots.py`.

### Snapshot detection

```
tmutil listlocalsnapshots /                        # primary; reports the Data volume's TM snapshots
diskutil apfs listSnapshots /System/Volumes/Data   # fallback; also catches non-TM snapshots
```

No root, no Full Disk Access; `tmutil` and `diskutil` return in well under a second. Parse out: count, per-snapshot timestamps (embedded in the names), oldest snapshot age.

**Volume targeting matters:** on modern macOS, `/` is the sealed System volume — itself mounted from a snapshot — while local Time Machine snapshots live on the Data volume. The `diskutil` fallback must target `/System/Volumes/Data`, not `/`. Filter or separately label `com.apple.os.update-*` snapshots: they are not user-reclaimable, and the report must never suggest thinning the snapshot the OS is running from.

**No per-snapshot sizes.** macOS does not expose per-snapshot size through any unprivileged interface — `tmutil` and `diskutil` return names and dates only. This is not a missing flag: APFS snapshots use copy-on-write with shared blocks, so "how big is snapshot X" isn't a single well-defined number; it depends on what else still references those blocks. Getting a real figure would require mounting each snapshot and running `du` under elevated access — rejected as a new permission/trust cost. Report count and age; the space impact is captured by the aggregate purgeable estimate below. Do not fake a per-snapshot size column.

### Purgeable estimate

Purgeable ≈ (Finder-reported free) − (`statvfs` free). The catch: the number Finder and Storage Settings show (free *including* purgeable) comes from Apple's `NSURLVolumeAvailableCapacityForImportantUsageKey` API, which has **no official CLI**. `diskutil info`'s `APFSContainerFree` very likely reports actually-free space — the same thing `statvfs` reports — in which case the delta is ~0 and the feature silently tells everyone "nothing purgeable here." `system_profiler SPStorageDataType -json` *may* mirror the Finder number, but that's not documented. Note `system_profiler` can take several seconds — standard timeout applies.

**Hard gate before building 1c: a validation spike.** On a Mac with known purgeable space (visible in Storage Settings), compare `statvfs`, `diskutil info -plist`, `system_profiler SPStorageDataType -json`, and Finder's displayed number. Use whichever source actually diverges from `statvfs`. If none does, fall back to shipping snapshot count/age with honest copy ("macOS hides the exact purgeable figure") instead of inventing a number. Clamp negatives to zero either way.

### Presentation

One aggregate story: "N snapshots, oldest from [date], likely holding onto the ~X GB of purgeable space" — not a fake-precise breakdown. Zero snapshots with high purgeable still gets an explanation: purgeable can be iCloud- or cache-driven, and the copy should say so rather than blaming snapshots by default.

### Wiring for 1c

- `yourdad.py`: attach as `scan_data['purgeable_and_snapshots']`.
- `scanners/grading.py`: new component grade, driven **primarily by purgeable GB** (e.g. A < 5 GB; C > 20 GB; F > 15% of disk). Snapshot count and age are modifiers only, and only when abnormal: Time Machine's normal retention is 24 hours of hourly snapshots, auto-deleted after a day, so an actively-backing-up user *always* has several fresh snapshots — that's the system working, not a defect to grade down. Penalize only snapshots older than ~48 hours (macOS isn't cleaning up) combined with high purgeable. Note: adding any new grade component shifts everyone's composite — expect re-baselining questions from existing testers.
- `personality/yourdad.py`: "your mac's been keeping 6 secret copies of itself since Tuesday. sentimental, but expensive." Tips (all advisory text, never executed): the `tmutil thinlocalsnapshots / 9999999999 4` command, "connect your Time Machine drive and let a backup complete," "if you don't use Time Machine anymore, turn off Automatic Backup in System Settings so it stops creating new ones."
- `renderers/terminal.py` + `renderers/html.py`: its own section in the existing storage report — purgeable bar next to the existing free/used bar, snapshot count and age, plain-language explainer.
- `utils/llm_prompt.py`: include this data so the LLM-ready prompt can explain missing-space cases.
- Also fix `scan_time_machine_backups()` in `scanners/mac_libraries.py`: its `/Backups.backupdb` check covers only the pre-APFS backup format and is superseded by this scanner for local snapshots.

## Phase 2: Trash

`~/.Trash` and `/Volumes/*/.Trashes`. Everybody has a Trash, and "empty the Trash" is the single most actionable tip in the tool — but these paths are TCC-protected like Mail and Messages: without Full Disk Access, reads fail with "Operation not permitted."

- Blocked on `PERMISSIONS-PLAN.md` landing first, so the failure mode is a guided "grant Full Disk Access to see your Trash" instead of a silent zero.
- Reuse `utils/permissions.py` detection and messaging.
- Grading: Trash > 5 GB is an easy letter-grade ding.

## Testing

`unit` marker, mocked subprocess, following `tests/test_path_utils.py` conventions:

- **Validation spike for the purgeable source — a manual acceptance test on real hardware, gating the 1c build.** Also verify `tmutil listlocalsnapshots` works without Full Disk Access on macOS Tahoe.
- Allowlist + sweep on a tmpdir with fake dot-directories — verifies hidden dirs get sized even though `should_exclude` would drop them; verifies the reporting floor and the `du` → Python-walk fallback.
- Friendly-name mapping: known bundle IDs (`com.spotify.client` → Spotify), unknown reverse-DNS IDs (heuristic fallback), and non-bundle folder names (pass through unchanged).
- Permission error on a swept dir (mock `du` failure / `PermissionError`) → routed to permission messaging, scan continues.
- Purgeable math: finder > statvfs, equal, and pathological finder < statvfs (clamp to 0).
- Fixture strings for `tmutil` / `diskutil -plist` / `system_profiler -json`: 0, 1, and many snapshots; `com.apple.os.update-*` entries filtered; malformed output; timeout; `FileNotFoundError` on non-Mac CI.
- Zero-snapshots-but-high-purgeable case — verify copy doesn't blame snapshots when there aren't any.
- New grading thresholds for both components, including the "fresh snapshots don't hurt the grade" case.

## Out of Scope

- **iCloud / CloudStorage / Mobile Documents.** iCloud generally keeps placeholders rather than local copies, and recursing into cloud-backed paths is exactly what caused the scan hangs the current `should_skip_path()` rules prevent. The existing skip rules stay.
- **Deleting or thinning anything programmatically.** Read-only stays read-only.
- **Per-snapshot sizes** — see Phase 1c.
- **Managing external Time Machine backup volumes** or offering any backup functionality.
