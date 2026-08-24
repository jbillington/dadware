# Volume Picker Offers Mounted Disk Images

**Date:** August 24, 2026
**Issue:** [#3](https://github.com/jbillington/dadware/issues/3)
**Status:** ✅ Fixed on branch `claude/storage-scan-volume-filter-9hfet6` (`93de21e`) — not merged, not yet run on a real Mac
**Reported by:** Jeff, while a package `.dmg` was mounted mid-install

---

## Problem

With a `.dmg` installer mounted, the storage scan's volume menu offered the installer's volume as a scan target, sitting next to the real drives:

```
Available volumes:
1) Macintosh HD (/) - 494.4 GB, 312.1 GB used (63%)
2) Install SomeApp (/Volumes/Install SomeApp) - 1.2 GB, 1.2 GB used (100%)

Note: Home directory will be scanned separately for detailed breakdown.
Pick one [1]:
```

Nobody wants a cleanup report on an installer image. It is read-only, it vanishes on eject, and there is nothing on it to delete.

---

## Root Cause

`utils/volumes.py::list_volumes()` offered anything under `/Volumes` that passed `os.path.ismount()`:

```python
for item in os.listdir(volumes_dir):
    volume_path = os.path.join(volumes_dir, item)
    if os.path.ismount(volume_path):
        ...
```

To the OS, a mounted disk image *is* a mount point — indistinguishable from an attached drive by that test alone. The same hole let in two other non-targets:

| Mount kind | Why it isn't a scan target |
|---|---|
| Mounted `.dmg` / `.sparsebundle` | Read-only, temporary, nothing to clean up |
| Network share (SMB/AFP/NFS/WebDAV) | Not local storage; scanning it is slow over the wire |
| Any read-only mount | Can't be cleaned up either way |

The picker should only offer real storage devices — internal and external drives.

---

## Solution

Classify every mount before offering it. Three independent signals, all available without adding a runtime dependency:

| Signal | Detects | Cost |
|---|---|---|
| `hdiutil info -plist` | Mount points backed by disk images | One subprocess covers *every* attached image; authoritative for `.dmg`/`.sparsebundle` |
| `mount` output | Filesystem type → network mounts | One subprocess for all mounts |
| `statvfs` `ST_RDONLY` | Read-only mounts | Free — no subprocess |

Read-only is deliberately the third check, not the only one: it doubles as the backstop that still catches installer images if `hdiutil` is unavailable.

### Two details that matter

1. **`/` is exempt from the read-only rule.** On Big Sur and later the macOS system volume is sealed read-only, so a naive `ST_RDONLY` check would hide the user's main drive. `classify_volume()` returns `system`/scannable for `/` before that rule runs.
2. **Every detection degrades to "can't tell → still offer it."** A missing or failing `hdiutil`/`mount` returns an empty mapping rather than raising, so the worst case is the old behavior (an extra entry in the menu), never an empty picker.

### Behavior

- Non-storage volumes are **hidden from the menu but listed** under a "Not shown (not a storage device)" note with the reason. Silently dropping a drive someone expected to see would be a worse bug than the one being fixed.
- `--all-volumes` puts them all back in the picker.
- An explicit `--volume PATH` still scans anything, with a one-line note when the target isn't a storage device.
- If classification somehow filters out *everything*, `select_volume()` falls back to showing all mounts rather than erroring.

```
→ Using Macintosh HD (/) - 494.4 GB, 312.1 GB used (63%)

Not shown (not a storage device):
  - Install SomeApp (/Volumes/Install SomeApp) - mounted disk image (SomeApp.dmg)
  Use --all-volumes to include them, or --volume PATH to scan one directly.
Note: Home directory will be scanned separately for detailed breakdown.
```

---

## Implementation

**`utils/volumes.py`** — new public helpers, all covered by tests:

| Function | Role |
|---|---|
| `get_disk_image_mounts()` | `hdiutil info -plist` → `{mount_point: backing_image_path}` |
| `get_mount_fstypes()` | `mount` output → `{mount_point: fstype}` |
| `is_read_only(path)` | `statvfs().f_flag & ST_RDONLY` |
| `classify_volume(path, fstype, disk_image_mounts)` | → `{kind, scannable, skip_reason}`, `kind` ∈ `system` / `disk` / `disk_image` / `network` / `read_only` |
| `describe_volume(volume)` | Shared one-line format for menu and status lines |

`list_volumes(include_all=False)` runs the two subprocesses once and classifies every candidate. `select_volume(volume_path=None, include_all=False)` asks for the full list, splits it into offered vs. hidden, re-indexes the menu so numbers stay contiguous, and reports what it left out.

**`yourdad.py`** — adds `--all-volumes`, passes it through `run_storage_scan()`.

**Docs** — README options list, USER-GUIDE options section, CLAUDE.md design-decisions list.

---

## Testing

`tests/test_volumes.py` grew from 8 to 27 tests; full suite passes (246 passed, 1 skipped). Coverage:

- **Classification** — root stays scannable while read-only; disk image excluded with its backing filename in the reason; disk image with no backing path still gets a reason; each network fstype excluded; read-only excluded; writable external kept.
- **Parsing** — `mount` output parsed into fstypes (including a volume name with spaces and a garbage line); missing `hdiutil`/`mount` binaries return `{}` instead of raising.
- **Filtering** — disk image excluded by default, kept and labeled under `include_all=True`.
- **Picker** — hidden volumes are reported rather than dropped; menu indexes stay contiguous after filtering (picking "2" gets the second *offered* volume, not the third entry); explicit path to a disk image scans with a note; everything-filtered falls back to showing all.

### Still needs a real Mac

The tests stub `hdiutil` and `mount`, so **the detection logic has never run against a real mounted image.** Before merging:

1. Mount any `.dmg`, run `python yourdad.py` → the image must be under "Not shown", the real drives still listed.
2. Same state, `python yourdad.py --all-volumes` → the image is back in the menu, labeled.
3. `python yourdad.py --volume "/Volumes/<image>"` → scans, with the "Scanning it anyway" note.
4. Plain run with no image mounted → menu unchanged from today.
5. If a network share is handy, connect one and confirm it lands under "Not shown" as a network share.
6. Sanity check the plist parse against the current OS: `hdiutil info -plist | head -40` should show `images` → `system-entities` → `mount-point`.

---

## Merge Notes

Measured against `claude/backlog-review-next-steps-4vro4i` (the hidden-storage work) on Aug 24, 2026:

- **Textual conflicts: none.** `git merge` of this branch into that one auto-merges `CLAUDE.md`, `yourdad.py`, and `tests/test_cli.py` cleanly.
- **One semantic break, one line to fix.** `select_volume()` gained an `include_all` keyword, so any test stub written as `lambda volume: ...` raises `TypeError`. The hidden-storage branch adds one such stub (`tests/test_cli.py`, `TestRunStorageScanAttachesHiddenCaches._patch_scan`); changing it to `lambda volume, include_all=False: ...` takes the merged suite to green (307 passed, 1 skipped, verified).

Merge order doesn't matter — whichever lands second needs that one-line stub update.

---

**Files Modified:**
- `utils/volumes.py` — classification, filtering, hidden-volume reporting
- `yourdad.py` — `--all-volumes` flag and plumbing
- `tests/test_volumes.py` — 19 new tests
- `tests/test_cli.py` — `select_volume` stubs updated for the new signature
- `README.md`, `docs/USER-GUIDE.md`, `CLAUDE.md` — flag and design-decision docs
