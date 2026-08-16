# Hidden Storage Plan (Caches, Dotfolders, Trash, Purgeable/Snapshots)

**Status:** Proposed
**Effort:** Phase 1: 7-10 hours (two independent scanners, see below). Phase 2: 2-3 hours.
**Depends on:** Phase 2 requires the Full Disk Access work in `PERMISSIONS-PLAN.md`.
**Motivation:** Micromat article "Why Does My Mac Say the Drive Is Full When It Isn't?" — plus the observation that Dad Ware's own exclusion rules hide some of the largest things on a developer's disk. Revised after a third-party research PRD on Time Machine local-snapshot prevalence (Aug 2026) — see Decision Log.

---

## Priorities and Assumptions

Phases are ordered by **value to the target user**, not difficulty. Target user: someone who has never really backed up or cleaned up their Mac.

- **Hidden app caches are a priority.** Everybody has them, they're often huge, and the current scan can't see any of them. Phase 1a/1b.
- **Purgeable space + local snapshots are also Phase 1, as one combined "why isn't my space coming back" feature.** Originally snapshots were scoped separately and demoted on the assumption that they mainly matter to current external-drive Time Machine users — a small slice of this audience. A third-party PRD corrected that assumption (see Decision Log): local snapshots persist for anyone who *ever* enabled automatic Time Machine, even after the backup drive is unplugged and put away — a meaningfully bigger population than "people actively using an external disk." Promoted to Phase 1c.
- **Trash is the most universal single win** (everyone has one, it's the first thing the article says to check) — but reading it requires Full Disk Access, so it's gated behind the permissions work. Phase 2.
- **iCloud pending-sync is out of scope entirely.** iCloud is generally good at keeping placeholders instead of local copies, and recursing into cloud-backed paths is exactly what caused the hangs the current `should_skip_path()` rules prevent. Not worth the risk.

## Decision Log

Decisions made while scoping this plan, recorded so the reasoning doesn't get re-litigated later:

1. **Snapshot detection ships as its own scanner and report section, not merged into the hidden-caches feature — but in the same phase/priority tier.** They answer different user questions ("what's secretly taking up space, and can I delete it" vs. "why didn't deleting things free up space") and use different techniques (directory walk with real file bytes vs. subprocess output parsing with a computed estimate). Keeping them independent means either can ship, break, or get tested without blocking the other.
2. **Snapshot size is reported in aggregate only — no per-snapshot byte figure.** macOS does not expose per-snapshot size via any unprivileged API. `tmutil listlocalsnapshots` and `diskutil apfs listSnapshots` return names/dates, not sizes, and this isn't a missing-flag gap — APFS snapshots use copy-on-write with shared blocks, so "how big is snapshot X" isn't a single well-defined number the way a file's size is; it depends on what else still references those blocks. Getting a real per-snapshot number would require mounting each snapshot and running `du`, which needs elevated (admin/root) access — rejected as a new elevation/trust cost the product doesn't want to take on for this feature. Instead: report snapshot count + age range, paired with the purgeable-space delta (which is where the snapshot data actually shows up), with copy that attributes the purgeable total to the snapshots when both are present.
3. **Stays fully read-only. No thinning action.** The PRD recommended a "safe thin" action calling Apple's `tmutil thinlocalsnapshots`. Considered and rejected — it would be the tool's first write action ever, and it undercuts the "Dad Ware never touches your files" trust story that's also load-bearing for the FDA/permissions pitch. The command appears as copy-pasteable advice, same as every other tip in the tool, with a clear "we're not going to run this for you" framing.

## The Gap (what the current code can't see)

`should_exclude()` in `utils/path_utils.py` drops any basename starting with `.` and everything under `/Library/Caches/`, `/tmp/`, `/private`, `/var`. Consequences:

- `~/Library/Caches` totals ~0 in every report.
- Hidden dev heavyweights are invisible: `~/.npm`, `~/.cache`, `~/.gradle`, `~/.m2`, `~/.cargo`, `~/.pyenv`, `~/.ollama`.
- **Container runtimes in hidden folders are invisible** even though the codebase has Docker-aware sizing (`is_docker_path`, `st_blocks * 512`): legacy `~/.docker`, Colima (`~/.colima`), OrbStack (`~/.orbstack`), Lima (`~/.lima`). (Docker Desktop's current `~/Library/Containers/com.docker.docker/.../Docker.raw` *is* reachable by the main walk — the blind spot is the hidden-folder variants.)
- `~/.Trash` is invisible — and it's also TCC-protected, see Phase 2.
- Snapshots and purgeable space aren't files at all; no walk can find them.

**Do not fix this by removing the dotfile exclusion from the main walk.** That would drag every scan through `.git` object stores and `.venv` trees — thousands of tiny files, much slower scans, noisy results. The exclusions are load-bearing. Instead, add a targeted scanner that goes directly to hidden locations.

## Design Constraints (unchanged)

- **Read-only.** Detect and advise; never delete. Cleanup commands appear as labeled, copy-pasteable advice. (Reconfirmed for snapshots specifically — see Decision Log #3.)
- **Stdlib only.** `subprocess` + `plistlib` + `os`.
- **Graceful degradation + time budgets.** Same patterns as `scanners/cpu.py` and `scan_all_mac_libraries()`: timeouts, `log_subprocess_call`, partial results.

---

## Phase 1a/1b: Hidden files and caches

New module: `scanners/hidden_storage.py`.

### 1a. Known-heavyweight allowlist

Same philosophy as `mac_libraries.py` — known paths, direct access (exclusion rules never apply because we never walk to them), bounded-depth sizing via the existing `get_file_size_disk()`:

| Category | Paths |
|---|---|
| User caches | `~/Library/Caches`, `~/Library/Logs` |
| Developer | `~/Library/Developer/Xcode/DerivedData`, `~/Library/Developer/Xcode/iOS DeviceSupport`, `~/Library/Developer/CoreSimulator` |
| Container runtimes | `~/.docker`, `~/.colima`, `~/.orbstack`, `~/.lima` |
| Package managers | `~/.npm`, `~/.cache`, `~/.gradle`, `~/.m2`, `~/.cargo`, `~/Library/Caches/Homebrew` |
| ML/AI | `~/.ollama`, `~/.lmstudio` |

### 1b. Generic hidden-folder sweep

The allowlist can't know every app. So also: `os.scandir(home)`, take every directory whose name starts with `.`, size each with a bounded-depth walk (depth ~6, per-folder timeout), and report any over a threshold (default 1 GB). A typical home has 20-60 dot-directories; with the size floor this is fast and catches caches from apps we've never heard of. `.Trash` will raise `PermissionError` here — route it to the Phase 2 messaging, don't report 0.

### Wiring (1a/1b)

- `yourdad.py`: attach as `scan_data['hidden_caches']` during the storage scan.
- `scanners/grading.py`: new component grade — thresholds on total hidden-cache GB.
- `personality/yourdad.py`: "you've got 23GB of caches squirreled away in hidden folders. the Mac equivalent of finding cash in old coat pockets."
- `renderers/terminal.py` + `renderers/html.py`: "Hidden Caches" section; HTML reuses the existing expandable-section pattern. Per-item advice ("DerivedData is safe to delete; Xcode rebuilds it", "caches regenerate — deleting them isn't always a win").
- `utils/llm_prompt.py`: include the new data.

## Phase 1c: Purgeable space + local snapshots

Separate function(s) in `scanners/hidden_storage.py` (or a sibling module, e.g. `scanners/snapshots.py` — implementation detail, not a priority decision).

### Snapshot detection

```
tmutil listlocalsnapshots /          # names embed timestamps
diskutil apfs listSnapshots /        # fallback; also catches non-TM snapshots (e.g. update snapshots)
```

No root, no FDA, sub-second. Parse: count, per-snapshot timestamps (from the name), oldest snapshot age.

### Purgeable estimate

Purgeable ≈ (Finder-reported free) − (`statvfs` free). Sources for the Finder number, in order: `diskutil info -plist /` parsed with `plistlib`, then `system_profiler SPStorageDataType -json` (already shelled out to in `utils/system_info.py`). Clamp negatives to zero.

### Combined presentation

Per Decision Log #2: no per-snapshot size. The feature is "N snapshots, oldest from [date], and here's the ~X GB of purgeable space they're likely holding onto" — one aggregate number, not a fake-precise breakdown. This is the direct answer to "I deleted files and free space didn't come back," for every user, snapshot count zero or not (zero snapshots + high purgeable still gets an explanation; some purgeable space is iCloud/cache-driven, not snapshot-driven, and the copy should say so rather than blaming snapshots by default).

### Wiring (1c)

- `yourdad.py`: attach as `scan_data['purgeable_and_snapshots']`.
- `scanners/grading.py`: new component grade — e.g. A = 0-1 snapshots and purgeable < 5 GB; C = snapshots older than 3 days or purgeable > 20 GB; F = purgeable > 15% of disk.
- `personality/yourdad.py`: "your mac's been keeping 6 secret copies of itself since Tuesday. sentimental, but expensive." / "you deleted the files. the Mac is just... holding onto the memory. it'll let go eventually, or we can talk to it." Tips: the `tmutil thinlocalsnapshots` command as text (never executed — Decision Log #3), "connect your Time Machine drive and let a backup complete," "if you don't use Time Machine anymore, turn off Automatic Backup in System Settings so it stops creating new ones" (deep-link to the pane, advisory only).
- `renderers/terminal.py` + `renderers/html.py`: its own section, separate from Hidden Caches (Decision Log #1) — purgeable bar next to the existing free/used bar, snapshot count/age, explainer text.
- `utils/llm_prompt.py`: include this data so the "ask an AI" prompt can explain missing-space cases.
- Also fix `scan_time_machine_backups()` in `scanners/mac_libraries.py`: its `/Backups.backupdb` check is the pre-APFS format only; stop implying it covers local snapshots — it's now clearly superseded by this scanner.

## Phase 2: Trash

`~/.Trash` and `/Volumes/*/.Trashes`. Everybody has a Trash, and "empty the Trash" is the single most actionable tip in the tool — but these paths are TCC-protected (like Mail and Messages): without Full Disk Access, reads fail with "Operation not permitted."

- Blocked on `PERMISSIONS-PLAN.md` landing first, so the failure mode is a guided "grant Full Disk Access to see your Trash" instead of a silent zero.
- Reuse `utils/permissions.py` detection and messaging.
- Grading: Trash > 5 GB is an easy letter-grade ding. Personality writes itself ("you took out the trash but left the bag by the door").

## Testing

`unit` marker, mocked subprocess, following `tests/test_path_utils.py` conventions:

- Allowlist + sweep on a tmpdir with fake dot-directories — verifies hidden dirs get sized even though `should_exclude` would drop them; verifies size floor and depth bound.
- `PermissionError` on a swept dir → routed to permission messaging, scan continues.
- Purgeable math: finder > statvfs, equal, and pathological finder < statvfs (clamp to 0).
- Fixture strings for `tmutil` / `diskutil -plist` / `system_profiler -json` (0, 1, many snapshots; malformed; timeout; `FileNotFoundError` on non-Mac CI).
- Zero-snapshots-but-high-purgeable case — verify copy doesn't blame snapshots when there aren't any.
- New grading thresholds (both components).

## Out of Scope

- iCloud / CloudStorage / Mobile Documents — see Assumptions. The existing skip rules stay.
- Deleting or thinning anything programmatically. Read-only stays read-only (Decision Log #3).
- Per-snapshot sizes (Decision Log #2).
