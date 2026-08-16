# Hidden Storage Plan (Snapshots, Purgeable, Caches, Trash)

**Status:** Proposed
**Effort:** Phase 1: 4-6 hours. Phase 2: 3-4 hours. Phase 3: optional.
**Motivation:** Micromat article "Why Does My Mac Say the Drive Is Full When It Isn't?" — the classic support case where a user deletes files and free space doesn't come back. Dad Ware currently cannot answer this question, and it's exactly the question a "dad" tool should answer.

---

## The Gap

The article lists five reasons a Mac reports "disk full" when Finder shows nothing big:

1. APFS snapshots (Time Machine / system updates)
2. Purgeable storage macOS hasn't reclaimed yet
3. Large caches and temporary files
4. Hidden system data
5. Files waiting to sync with cloud services

**The current implementation finds none of these.** This is not an accident — most of them are deliberately excluded, and the two biggest ones (snapshots, purgeable) are not files at all, so no directory walk will ever find them. Here's the audit:

### 1. APFS snapshots — NOT FOUND, cannot be found by the current design

Snapshots are filesystem metadata, not files. `os.walk()` in `scanners/storage.py` can never see them. The closest thing we have, `scan_time_machine_backups()` in `scanners/mac_libraries.py`, only looks at `/Backups.backupdb` and `/Volumes/*/Backups.backupdb` — the **pre-APFS (HFS+) Time Machine format**. On any Mac running 10.13+ with APFS backups, local snapshots live inside the APFS container and that scanner returns nothing. This is the single biggest blind spot relative to the article. **Requires a new feature.**

### 2. Purgeable storage — NOT REPORTED, partially measurable today

`os.statvfs()` (used in `utils/volumes.py` and `scanners/storage.py`) reports *actually-free* blocks. Finder and Storage Settings report free + purgeable. Dad Ware currently shows the statvfs number and never surfaces the discrepancy — which is precisely the "why don't these numbers match" confusion the article describes. **Requires a new feature** (a delta calculation, not a scan).

### 3. Caches and temporary files — DELIBERATELY EXCLUDED

`should_exclude()` in `utils/path_utils.py` skips:
- anything under `/Library/Caches/` (which also matches `~/Library/Caches/...` contents, so the user cache folder totals ~0)
- `/tmp/` and anything ending in `/tmp`
- root-level `Library`, `private`, `var`, `System`, `usr` — so `/private/var/folders` (per-user temp/cache), `/private/var/vm` (swap + sleepimage), and system caches are all invisible

These exclusions are correct for the main walk (speed, permission noise), but it means the tool literally cannot explain cache bloat. **Requires a new targeted scanner; do not relax the main-walk exclusions.**

### 4. Hidden system data / dotfiles — DELIBERATELY EXCLUDED

`should_exclude()` drops any basename starting with `.`. That hides some of the worst offenders on developer Macs:
- `~/.Trash` — the article's first check is "empty the Trash," and Dad Ware can't even see it
- `~/.docker` (Docker.raw lives here on modern Docker Desktop), `~/.npm`, `~/.cache`, `~/.gradle`, `~/.m2`, `~/.cargo`, `~/.pyenv`, `~/.ollama`
- `/Volumes/*/.Trashes` on external drives

Ironic given the codebase already has Docker-aware sizing (`is_docker_path`, `st_blocks * 512`) — the sizing logic exists but the walk never reaches the files. **Requires an allowlist scanner** (same pattern as `mac_libraries.py`: known paths, non-recursive discovery, bounded depth).

### 5. Cloud files pending sync — DELIBERATELY SKIPPED

`should_skip_path()` skips `Mobile Documents` and `CloudStorage` to prevent iCloud-triggered hangs (a good decision — keep it). We can report *that* they exist and their on-disk (not logical) size without recursing into cloud-backed content. **Low priority; advice-level.**

---

## Design Constraints (unchanged)

- **Read-only.** We detect and advise; we never run `tmutil deletelocalsnapshots`, never empty the Trash. Cleanup commands appear as copy-pasteable advice in the report, clearly labeled.
- **Stdlib only.** Everything below uses `subprocess` + `plistlib` + `os`. No new dependencies.
- **Graceful degradation.** Every probe has a timeout and a "couldn't check" fallback, following the existing `log_subprocess_call` + try/except pattern from `scanners/cpu.py` and `mac_libraries.py`.
- **Time-budgeted.** New scanners plug into the same budget pattern as `scan_all_mac_libraries()`.

---

## Phase 1: Snapshots + Purgeable ("the missing space report")

New module: `scanners/hidden_storage.py`.

### Snapshot detection

```
tmutil listlocalsnapshots /          # names like com.apple.TimeMachine.2026-08-16-093012.local
diskutil apfs listSnapshots /        # fallback; also catches non-TM snapshots (e.g. update snapshots)
```

Both run without root and return in well under a second. Parse out: count, per-snapshot timestamps (embedded in the name), oldest snapshot age.

**Honest limitation to encode in the report:** macOS does not expose per-snapshot size without private APIs or root. We report count + age and pair it with the purgeable estimate below, which is where snapshot space shows up anyway. Don't fake a per-snapshot size column.

### Purgeable estimate

Purgeable ≈ (Finder-reported free) − (statvfs free). Two sources for the Finder number, in order:

1. `diskutil info -plist /` parsed with `plistlib` — `APFSContainerFree` / volume fields
2. `system_profiler SPStorageDataType -json` — `free_space_in_bytes` matches Storage Settings (we already shell out to `system_profiler` in `utils/system_info.py`)

Report: `free_bytes_statvfs`, `free_bytes_finder`, `purgeable_estimate_bytes`, and a one-line explanation. This single number is the answer to the article's headline question.

### Data shape

```python
{
  'type': 'hidden_storage',
  'snapshots': {'count': 4, 'oldest': '2026-08-14T09:30:12', 'names': [...], 'source': 'tmutil'},
  'purgeable': {'estimate_bytes': ..., 'finder_free_bytes': ..., 'statvfs_free_bytes': ...},
  'status': 'complete' | 'error',
}
```

### Wiring (follows the existing pipeline exactly)

- `yourdad.py`: call it during the storage scan, attach as `scan_data['hidden_storage']`.
- `scanners/grading.py`: new component grade. Suggested thresholds: A = 0-1 snapshots and purgeable < 5 GB; C = snapshots older than 3 days or purgeable > 20 GB; F = purgeable > 15% of disk. Add to the composite with a modest weight.
- `personality/yourdad.py`: this is prime dad material.
  - "your mac's been keeping 6 secret copies of itself since Tuesday. sentimental, but expensive."
  - "you deleted the files. the Mac is just... holding onto the memory. it'll let go eventually. or we can talk to it."
  - Tips: `tmutil thinlocalsnapshots / 9999999999 4` (safe, asks TM to thin), "connect your Time Machine drive and let a backup complete," "purgeable space frees itself when the disk gets tight — but a restart often hurries it along."
- `renderers/terminal.py` + `renderers/html.py`: a "Hidden Storage" section — snapshot count/ages, purgeable bar next to the existing free/used bar, explainer text. The HTML report already has expandable sections; reuse that.
- `utils/llm_prompt.py`: include snapshot + purgeable data so the "ask an AI" prompt can explain missing-space cases.

### Also in Phase 1

Fix/replace `scan_time_machine_backups()`: keep the `Backups.backupdb` check for old external drives, but stop implying it covers local snapshots. Its APFS successor is the snapshot probe above.

## Phase 2: Trash + hidden heavyweights allowlist

Extend `scanners/hidden_storage.py` (or sibling `scanners/hidden_folders.py`) with an **allowlist** scanner — same philosophy as `mac_libraries.py`: known paths only, no discovery walk, disk-accurate sizing via the existing `get_file_size_disk()`.

Targets, each with a bounded-depth `get_folder_size`:

| Category | Paths |
|---|---|
| Trash | `~/.Trash`, `/Volumes/*/.Trashes` |
| User caches | `~/Library/Caches`, `~/Library/Logs` |
| Developer | `~/Library/Developer/Xcode/DerivedData`, `~/Library/Developer/Xcode/iOS DeviceSupport`, `~/Library/Developer/CoreSimulator` |
| Dev dotfolders | `~/.docker`, `~/.npm`, `~/.cache`, `~/.gradle`, `~/.m2`, `~/.cargo`, `~/.ollama`, `~/Library/Caches/Homebrew` |
| System (report-only) | `/private/var/vm` (swap/sleepimage — explains "System Data"), `/Library/Caches` |

Notes:
- **Do not touch `should_exclude()`** for the main walk — the exclusions are load-bearing for speed. The allowlist scanner reaches these paths directly, so the exclusion rules never apply.
- `~/Library/Caches` needs a small carve-out in the shared `get_folder_size` path-skipping only when called from this scanner (pass-through flag), since `should_skip_path` doesn't block it but `should_exclude` semantics must not leak in.
- System paths will often be permission-denied without Full Disk Access — reuse `utils/permissions.py` messaging, show "needs Full Disk Access" instead of 0 bytes.
- Grading: Trash > 5 GB is an easy letter-grade ding and the single most actionable tip in the whole tool. Caches graded gently (they regenerate; deleting them isn't always a win — dad says so).

## Phase 3 (optional): Cloud sync + deeper system data

- iCloud/CloudStorage: report on-disk size of `~/Library/Mobile Documents` and `~/Library/CloudStorage` using `st_blocks` sizing at shallow depth with a hard timeout (dataless files stat fine; do NOT open/read them or macOS may download). Possibly `brctl quota` for iCloud numbers.
- Per-user temp: top-level sizing of `$TMPDIR`'s parent under `/private/var/folders` (FDA required).
- A "System Data explained" panel in the HTML report tying all of the above together.

## Testing

Follows `tests/test_path_utils.py` conventions, `unit` marker, mocked subprocess:

- Fixture strings for `tmutil listlocalsnapshots` (0, 1, many snapshots; malformed), `diskutil info -plist` (real plist blobs), `system_profiler -json`.
- Purgeable math: finder_free > statvfs_free, equal, and the pathological finder_free < statvfs_free (clamp to 0, don't report negative purgeable).
- Timeout / `FileNotFoundError` (non-Mac CI) → `status: 'error'`, scan continues.
- Allowlist scanner on a tmpdir with fake `.Trash` — verifies hidden-dir sizing works even though `should_exclude` would drop dotfiles.
- Grading thresholds for the new components.

## Out of Scope

- Deleting snapshots, emptying Trash, purging caches — read-only stays read-only.
- Per-snapshot sizes (not available without root/private APIs — see Phase 1 note).
- Watching/daemon behavior; this stays a point-in-time scan.
