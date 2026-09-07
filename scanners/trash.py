"""Trash scanner - the folder everyone forgets and every cleanup guide names first.

Phase 2 of `docs/roadmap/HIDDEN-STORAGE-PLAN.md`. Deleting a file in Finder
moves it; it does not remove it. Until the Trash is emptied the bytes are
still on the disk, and the main storage walk cannot see them: `should_exclude()`
drops every dotfile, so `~/.Trash` and every `/Volumes/*/.Trashes` are missing
from today's reports. A drive can be 40 GB short of what the report accounts
for and the Trash is the whole answer.

Three design points worth keeping:

- **A denial is reported, never a zero.** `~/.Trash` is TCC-protected like
  Mail and Messages. Without Full Disk Access, listing it raises EPERM, and a
  scanner that swallowed that would print "Trash: 0 B" to a user with 40 GB
  in it - the exact failure `PERMISSIONS-PLAN.md` exists to stop. Every
  location carries its own `status`, and 'no_permission' is a first-class
  answer that the report shows as a blank with a fix, not as empty.
- **Every volume has its own Trash.** Drag a file to the Trash from an
  external drive and macOS puts it in `/Volumes/<drive>/.Trashes/<uid>` - on
  that drive, not in your home folder. Emptying the Trash empties all of
  them, but until then the space is missing from whichever disk the file came
  from, which is why each location is reported separately.
- **Sizing is `du -skx`, shared with `hidden_storage`.** Same reasons: full
  depth, C-speed, disk-accurate, timeout-bounded. The item count and the age
  of the oldest item come from one `scandir` of the top level, because "142
  items, oldest 8 months old" is the line that makes someone act.

Read-only, like everything else here: the report says how much is in there
and how to empty it. It never empties anything.
"""

import os
import time
from typing import Any, Dict, List, Optional, Tuple

from scanners.hidden_storage import measure_folder
from scanners.models import TrashLocation, TrashScan
from utils.permissions import check_folder_access

# Per-location `du` timeout and the budget for the whole scan. A Trash on a
# slow external drive can't stall the report.
TRASH_DU_TIMEOUT_SECONDS = 20
DEFAULT_SCAN_TIMEOUT_SECONDS = 45

# Bookkeeping macOS keeps in a Trash folder. Counted in the size (it is real
# disk usage) but not as items the user put there.
NON_ITEM_NAMES = {'.DS_Store'}


def home_trash_path(home: Optional[str] = None) -> str:
    """`~/.Trash` - where Finder puts files deleted from the startup disk."""
    if home is None:
        home = os.path.expanduser('~')
    return os.path.join(home, '.Trash')


def volume_trash_path(volume_path: str, uid: Optional[int] = None) -> str:
    """`<volume>/.Trashes/<uid>` - one drive's Trash, for this user.

    `.Trashes` holds a numbered folder per user account, so the path has to
    be the current user's; sizing `.Trashes` whole would report another
    account's deleted files as this user's.
    """
    if uid is None:
        uid = os.getuid()
    return os.path.join(volume_path, '.Trashes', str(uid))


def _count_items(path: str) -> Tuple[Optional[int], Optional[float]]:
    """Top-level item count and the oldest item's mtime, in one scandir.

    Returns (count, oldest_mtime); either is None when the folder could not
    be listed. The count is of things the user threw away - a folder dragged
    to the Trash is one item, however many files are inside it.
    """
    count = 0
    oldest: Optional[float] = None
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.name in NON_ITEM_NAMES:
                    continue
                count += 1
                try:
                    mtime = entry.stat(follow_symlinks=False).st_mtime
                except (OSError, PermissionError):
                    continue
                if oldest is None or mtime < oldest:
                    oldest = mtime
    except (OSError, PermissionError):
        return None, None
    return count, oldest


def _age_days(mtime: Optional[float], now: Optional[float] = None) -> Optional[int]:
    """Whole days between `mtime` and now, floored at 0. None stays None."""
    if mtime is None:
        return None
    if now is None:
        now = time.time()
    return max(0, int((now - mtime) // 86400))


def measure_trash_location(label: str, path: str,
                           timeout: float = TRASH_DU_TIMEOUT_SECONDS,
                           now: Optional[float] = None) -> TrashLocation:
    """Measure one Trash folder, classifying what came back.

    The access probe runs first and its answer is the answer: a TCC denial
    means this location's size is unknown, and reporting the 0 bytes `du`
    would hand back for an unreadable folder is the bug this check exists to
    prevent.
    """
    access = check_folder_access(path)

    if access['status'] == 'not_found':
        # No Trash folder means nothing has been deleted here (macOS creates
        # it on demand), which is a real and reportable "empty", not an error.
        return TrashLocation(label=label, path=path, status='missing')

    if access['status'] == 'denied':
        note = ('Needs Full Disk Access to measure'
                if access.get('reason') == 'tcc'
                else 'Locked by file permissions')
        return TrashLocation(label=label, path=path, status='no_permission', note=note)

    if access['status'] == 'error':
        return TrashLocation(label=label, path=path, status='error',
                             note=access.get('reason'))

    item_count, oldest_mtime = _count_items(path)
    size_bytes, note = measure_folder(path, timeout=timeout)

    return TrashLocation(
        label=label,
        path=path,
        size_bytes=size_bytes,
        item_count=item_count,
        oldest_age_days=_age_days(oldest_mtime, now),
        status='empty' if not item_count and not size_bytes else 'measured',
        note=note,
    )


def find_trash_locations(home: Optional[str] = None,
                         include_home: bool = True,
                         volume_paths: Optional[List[str]] = None,
                         uid: Optional[int] = None) -> List[Tuple[str, str]]:
    """The Trash folders to measure, as (label, path).

    `volume_paths` defaults to every mounted volume Dad Ware considers
    scannable - the same classification the volume picker uses, so a network
    share or a mounted installer .dmg is not probed for a Trash it has no
    business having.
    """
    locations: List[Tuple[str, str]] = []

    if include_home:
        locations.append(('Trash (your home folder)', home_trash_path(home)))

    if volume_paths is None:
        # Imported here rather than at module scope: this is the only path
        # that needs it, and it costs two subprocess calls.
        from utils.volumes import list_volumes
        try:
            # `/` is dropped: on the startup disk Finder puts deleted files in
            # `~/.Trash`, which is already the first location above, and the
            # root `/.Trashes` is the same Trash counted twice.
            volume_paths = [
                volume['path'] for volume in list_volumes()
                if os.path.normpath(volume['path']) != '/'
            ]
        except Exception:  # noqa: BLE001 - a volume listing failure is not a scan failure
            volume_paths = []

    for volume_path in volume_paths:
        name = os.path.basename(os.path.normpath(volume_path)) or volume_path
        locations.append((f'Trash on {name}', volume_trash_path(volume_path, uid)))

    return locations


def scan_trash(home: Optional[str] = None,
               include_home: bool = True,
               volume_paths: Optional[List[str]] = None,
               timeout_seconds: float = DEFAULT_SCAN_TIMEOUT_SECONDS,
               uid: Optional[int] = None,
               now: Optional[float] = None) -> Dict[str, Any]:
    """Measure the Trash, everywhere it lives on this Mac.

    Totals cover the locations that could actually be read. A location the
    scan could not measure is listed with its own status and never folded
    into the total as a zero, so "1.2 GB" is never really "1.2 GB plus
    whatever is behind that locked door".

    Returns a plain dict (`TrashScan.to_dict()`), matching the dict boundary
    the renderers and JSON manifests expect.
    """
    start_time = time.time()
    deadline = start_time + timeout_seconds
    scan = TrashScan()

    for label, path in find_trash_locations(home=home, include_home=include_home,
                                            volume_paths=volume_paths, uid=uid):
        if time.time() >= deadline:
            scan.status = 'partial'
            break

        location = measure_trash_location(label, path, now=now)
        scan.locations.append(location)

        if location.status == 'no_permission':
            scan.permission_denied = True
            continue
        if location.status in ('missing', 'error'):
            continue

        scan.total_size_bytes += location.size_bytes
        scan.item_count += location.item_count or 0
        if location.oldest_age_days is not None:
            scan.oldest_age_days = max(scan.oldest_age_days or 0,
                                       location.oldest_age_days)

    if scan.status != 'partial':
        scan.status = 'complete'
    scan.duration_seconds = round(time.time() - start_time, 2)
    return scan.to_dict()
