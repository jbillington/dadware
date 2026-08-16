# Hidden Storage Plan (Caches, Dotfolders, Trash, Purgeable)

**Status:** Proposed
**Effort:** Phase 1: 4-6 hours. Phase 2: 2-3 hours. Phase 3: 2-3 hours.
**Depends on:** Phase 2 requires the Full Disk Access work in `PERMISSIONS-PLAN.md`.
**Motivation:** Micromat article "Why Does My Mac Say the Drive Is Full When It Isn't?" — plus the observation that Dad Ware's own exclusion rules hide some of the largest things on a developer's disk.

---

## Priorities and Assumptions

Phases are ordered by **value to the target user**, not difficulty. Target user: someone who has never really backed up or cleaned up their Mac.

- **Hidden app caches are the priority.** Everybody has them, they're often huge, and the current scan can't see any of them. Phase 1.
- **Trash is the most universal single win** (everyone has one, it's the first thing the article says to check) — but reading it requires Full Disk Access, so it's gated behind the permissions work. Phase 2.
- **APFS snapshots are real but niche for this audience.** Local Time Machine snapshots only exist if TM was ever enabled — likely a minority of never-backed-up users. Still a nice feature; demoted to Phase 3. The *purgeable space* estimate, however, applies to everyone and costs almost nothing, so it stays in Phase 1.
- **iCloud pending-sync is out of scope entirely.** iCloud is generally good at keeping placeholders instead of local copies, and recursing into cloud-backed paths is exactly what caused the hangs the current `should_skip_path()` rules prevent. Not worth the risk.

## The Gap (what the current code can't see)

`should_exclude()` in `utils/path_utils.py` drops any basename starting with `.` and everything under `/Library/Caches/`, `/tmp/`, `/private`, `/var`. Consequences:

- `~/Library/Caches` totals ~0 in every report.
- Hidden dev heavyweights are invisible: `~/.npm`, `~/.cache`, `~/.gradle`, `~/.m2`, `~/.cargo`, `~/.pyenv`, `~/.ollama`.
- **Container runtimes in hidden folders are invisible** even though the codebase has Docker-aware sizing (`is_docker_path`, `st_blocks * 512`): legacy `~/.docker`, Colima (`~/.colima`), OrbStack (`~/.orbstack`), Lima (`~/.lima`). (Docker Desktop's current `~/Library/Containers/com.docker.docker/.../Docker.raw` *is* reachable by the main walk — the blind spot is the hidden-folder variants.)
- `~/.Trash` is invisible — and it's also TCC-protected, see Phase 2.
- Snapshots and purgeable space aren't files at all; no walk can find them.

**Do not fix this by removing the dotfile exclusion from the main walk.** That would drag every scan through `.git` object stores and `.venv` trees — thousands of tiny files, much slower scans, noisy results. The exclusions are load-bearing. Instead, add a targeted scanner that goes directly to hidden locations.

## Design Constraints (unchanged)

- **Read-only.** Detect and advise; never delete. Cleanup commands appear as labeled, copy-pasteable advice.
- **Stdlib only.** `subprocess` + `plistlib` + `os`.
- **Graceful degradation + time budgets.** Same patterns as `scanners/cpu.py` and `scan_all_mac_libraries()`: timeouts, `log_subprocess_call`, partial results.

---

## Phase 1: Hidden files and caches (the priority)

New module: `scanners/hidden_storage.py`. Two parts:

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

### 1c. Purgeable-space estimate

Purgeable ≈ (Finder-reported free) − (`statvfs` free). Sources for the Finder number, in order: `diskutil info -plist /` parsed with `plistlib`, then `system_profiler SPStorageDataType -json` (already shelled out to in `utils/system_info.py`). Clamp negatives to zero. One number plus a one-line explanation — this answers "I deleted files and free space didn't come back" for every user, snapshots or not. No permissions, no scan, minutes of runtime cost.

### Wiring

- `yourdad.py`: attach as `scan_data['hidden_storage']` during the storage scan.
- `scanners/grading.py`: new component grade — thresholds on total hidden-cache GB and purgeable GB.
- `personality/yourdad.py`: "you've got 23GB of caches squirreled away in hidden folders. the Mac equivalent of finding cash in old coat pockets."
- `renderers/terminal.py` + `renderers/html.py`: "Hidden Storage" section; HTML reuses the existing expandable-section pattern. Per-item advice ("DerivedData is safe to delete; Xcode rebuilds it", "caches regenerate — deleting them isn't always a win").
- `utils/llm_prompt.py`: include the new data.

## Phase 2: Trash

`~/.Trash` and `/Volumes/*/.Trashes`. Everybody has a Trash, and "empty the Trash" is the single most actionable tip in the tool — but these paths are TCC-protected (like Mail and Messages): without Full Disk Access, reads fail with "Operation not permitted."

- Blocked on `PERMISSIONS-PLAN.md` landing first, so the failure mode is a guided "grant Full Disk Access to see your Trash" instead of a silent zero.
- Reuse `utils/permissions.py` detection and messaging.
- Grading: Trash > 5 GB is an easy letter-grade ding. Personality writes itself ("you took out the trash but left the bag by the door").

## Phase 3: APFS snapshots

For the Time Machine users in the audience — smaller group, still a nice feature, and cheap:

```
tmutil listlocalsnapshots /          # names embed timestamps
diskutil apfs listSnapshots /        # fallback; also catches update snapshots
```

No root, no FDA, sub-second. Report count + oldest age next to the Phase 1 purgeable number (which is where snapshot space actually shows up). **Honest limitation:** macOS doesn't expose per-snapshot sizes without root/private APIs — report count and age, don't fake a size column. Advice: `tmutil thinlocalsnapshots / 9999999999 4`, "let a backup complete," "a restart often hurries purgeable cleanup along."

Also in this phase: fix `scan_time_machine_backups()` — its `/Backups.backupdb` check is the pre-APFS format only; stop implying it covers local snapshots.

## Testing

`unit` marker, mocked subprocess, following `tests/test_path_utils.py` conventions:

- Allowlist + sweep on a tmpdir with fake dot-directories — verifies hidden dirs get sized even though `should_exclude` would drop them; verifies size floor and depth bound.
- `PermissionError` on a swept dir → routed to permission messaging, scan continues.
- Purgeable math: finder > statvfs, equal, and pathological finder < statvfs (clamp to 0).
- Fixture strings for `tmutil` / `diskutil -plist` / `system_profiler -json` (0, 1, many snapshots; malformed; timeout; `FileNotFoundError` on non-Mac CI).
- New grading thresholds.

## Out of Scope

- iCloud / CloudStorage / Mobile Documents — see Assumptions. The existing skip rules stay.
- Deleting anything. Read-only stays read-only.
- Per-snapshot sizes.
