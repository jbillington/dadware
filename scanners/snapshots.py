"""APFS local snapshot scanner - the other half of "where did my space go?".

Phase 1c of `docs/roadmap/HIDDEN-STORAGE-PLAN.md`. Deliberately a sibling of
`hidden_storage.py` rather than part of it: this answers a different user
question ("why didn't deleting things free up space?" rather than "what is
secretly taking up space?"), uses subprocess parsing rather than directory
sizing, and either can ship or break without the other.

**No sizes, and no purgeable figure.** Two hard rules, both load-bearing:

1. *Per-snapshot sizes are not reported.* APFS snapshots share blocks via
   copy-on-write, so "how big is snapshot X" has no single answer - delete one
   and the others appear to grow. DaisyDisk is the only tool that shows the
   number at all, and its own manual disclaims it as "displayed only for
   reference". Inventing it here would be fake precision.
2. *No purgeable total is computed.* The Aug 2026 validation spike confirmed
   that no CLI source exposes the figure Finder shows: `diskutil`'s
   `APFSContainerFree` and `system_profiler`'s `free_space_in_bytes` both
   return exactly the `statvfs` number. Reaching Finder's number needs
   `NSURLVolumeAvailableCapacityForImportantUsageKey`, which needs PyObjC -
   an external runtime dependency this project does not take. So the report
   says what it knows (count, dates, ages) and says plainly that macOS does
   not expose the rest.

What it does report is honest and useful: how many snapshots exist, how old
the oldest is, and whether macOS considers them purgeable. Time Machine keeps
roughly 24 hours of hourly snapshots and cleans up after itself, so fresh
snapshots are the system working correctly - only genuinely stale ones (past
`STALE_AFTER_DAYS`) suggest macOS has not been able to reclaim them.
"""

import datetime
import plistlib
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from scanners.models import SnapshotInfo, SnapshotScan
from utils.subprocess_utils import log_subprocess_call

# `/` is the sealed System volume on modern macOS - itself mounted from a
# snapshot - while local Time Machine snapshots live on the Data volume. The
# diskutil fallback must target the Data volume or it reports the wrong thing.
DATA_VOLUME = '/System/Volumes/Data'

SNAPSHOT_TIMEOUT_SECONDS = 15

# Time Machine's normal retention is ~24 hours of hourly snapshots, auto-
# deleted after a day. An actively-backing-up Mac therefore always has several
# fresh ones: that is the system working, not a defect. Only past this does
# "macOS hasn't cleaned up" become the better explanation.
STALE_AFTER_DAYS = 2

# com.apple.TimeMachine.2026-03-08-150255.local
SNAPSHOT_DATE_RE = re.compile(r'(\d{4})-(\d{2})-(\d{2})-(\d{2})(\d{2})(\d{2})')

# Snapshots the OS makes around system updates. These are not user-
# reclaimable, and the report must never suggest thinning the snapshot the
# running system was booted from.
OS_UPDATE_MARKER = 'com.apple.os.update'


def _run(cmd: List[str], location: str) -> Tuple[Optional[bytes], Optional[str]]:
    """Run a command, returning (stdout, error). Never raises."""
    try:
        log_subprocess_call(location, cmd)
        result = subprocess.run(cmd, capture_output=True, timeout=SNAPSHOT_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return None, 'timed out'
    except FileNotFoundError:
        return None, 'not available on this system'
    except (OSError, PermissionError, ValueError) as exc:
        return None, str(exc)

    if result.returncode != 0:
        stderr = (result.stderr or b'').decode('utf-8', 'replace').strip()
        return None, stderr or f'exit code {result.returncode}'
    return result.stdout, None


def parse_snapshot_date(name: str) -> Optional[datetime.datetime]:
    """Pull the creation time out of a snapshot name.

    Time Machine encodes it in the name itself, which is the only unprivileged
    source for it. Names that don't carry one (OS update snapshots, anything
    hand-made) return None rather than a guess.
    """
    match = SNAPSHOT_DATE_RE.search(name or '')
    if not match:
        return None
    try:
        return datetime.datetime(*(int(part) for part in match.groups()))
    except ValueError:
        return None


def is_os_update_snapshot(name: str) -> bool:
    """Is this a system-update snapshot rather than a Time Machine one?"""
    return OS_UPDATE_MARKER in (name or '').lower()


def _build_snapshot(name: str, now: datetime.datetime,
                    purgeable: Optional[bool] = None) -> SnapshotInfo:
    created = parse_snapshot_date(name)
    age_days = None
    if created is not None:
        age_days = max(0, (now - created).days)
    return SnapshotInfo(
        name=name,
        created=created.isoformat() if created else None,
        age_days=age_days,
        is_os_update=is_os_update_snapshot(name),
        purgeable=purgeable,
    )


def list_tmutil_snapshots(volume: str = '/') -> Tuple[List[str], Optional[str]]:
    """Snapshot names via `tmutil listlocalsnapshots`.

    Confirmed working without Full Disk Access (Aug 2026 spike). Output is a
    header line followed by one name per line; some names carry a trailing
    annotation such as "(dataless)" which is stripped.
    """
    stdout, err = _run(['/usr/bin/tmutil', 'listlocalsnapshots', volume],
                       'list_tmutil_snapshots()')
    if err:
        return [], err

    names = []
    for line in stdout.decode('utf-8', 'replace').splitlines():
        line = line.strip()
        # Skip the "Snapshots for disk /:" header and any blank lines.
        if not line or line.lower().startswith('snapshots for'):
            continue
        # "com.apple.TimeMachine.2026-03-08-150255.local (dataless)"
        names.append(line.split(' ')[0].strip())
    return names, None


def list_diskutil_snapshots(volume: str = DATA_VOLUME) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Snapshots via `diskutil apfs listSnapshots`, which also reports Purgeable.

    Tries the plist form first and falls back to parsing the human-readable
    output, since the `-plist` flag's availability varies across macOS
    versions and the text form is what was actually observed on the spike Mac.
    Returns dicts of {'name', 'purgeable'}.
    """
    stdout, err = _run(['/usr/sbin/diskutil', 'apfs', 'listSnapshots', '-plist', volume],
                       'list_diskutil_snapshots()')
    if not err and stdout:
        parsed = _parse_diskutil_plist(stdout)
        if parsed is not None:
            return parsed, None

    stdout, err = _run(['/usr/sbin/diskutil', 'apfs', 'listSnapshots', volume],
                       'list_diskutil_snapshots() [text]')
    if err:
        return [], err
    return _parse_diskutil_text(stdout.decode('utf-8', 'replace')), None


def _parse_diskutil_plist(stdout: bytes) -> Optional[List[Dict[str, Any]]]:
    """Parse `diskutil ... -plist` output. None means "not a usable plist"."""
    try:
        data = plistlib.loads(stdout)
    except Exception:  # noqa: BLE001 - any malformed output means fall back
        return None
    if not isinstance(data, dict):
        return None

    snapshots = data.get('Snapshots')
    if not isinstance(snapshots, list):
        return None

    parsed = []
    for entry in snapshots:
        if not isinstance(entry, dict):
            continue
        name = entry.get('SnapshotName')
        if not name:
            continue
        purgeable = entry.get('Purgeable')
        parsed.append({
            'name': name,
            'purgeable': bool(purgeable) if isinstance(purgeable, bool) else None,
        })
    return parsed


def _parse_diskutil_text(text: str) -> List[Dict[str, Any]]:
    """Parse the human-readable `diskutil apfs listSnapshots` output.

    The observed shape is a tree: a "+-- <UUID>" line per snapshot followed by
    indented "Name:" / "XID:" / "Purgeable:" lines.
    """
    snapshots: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('+--'):
            current = {'name': None, 'purgeable': None}
            snapshots.append(current)
            continue
        if current is None:
            continue
        if stripped.startswith('Name:'):
            current['name'] = stripped.split(':', 1)[1].strip()
        elif stripped.startswith('Purgeable:'):
            value = stripped.split(':', 1)[1].strip().lower()
            if value in ('yes', 'no'):
                current['purgeable'] = value == 'yes'

    return [snap for snap in snapshots if snap.get('name')]


def scan_snapshots(now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """Scan for APFS local snapshots.

    `tmutil` is the primary source (no Full Disk Access needed); `diskutil` is
    consulted for the per-snapshot Purgeable flag and to catch snapshots
    `tmutil` doesn't list. Neither being available is a normal outcome on a
    non-Mac and is reported, not raised.

    Returns a plain dict (`SnapshotScan.to_dict()`), matching the dict
    boundary the renderers and manifests expect.
    """
    if now is None:
        now = datetime.datetime.now()

    scan = SnapshotScan()

    tm_names, tm_error = list_tmutil_snapshots()
    du_entries, du_error = list_diskutil_snapshots()

    purgeable_by_name = {
        entry['name']: entry.get('purgeable')
        for entry in du_entries if entry.get('name')
    }

    # tmutil first (it is the unprivileged, documented source), then anything
    # only diskutil could see.
    names: List[str] = list(tm_names)
    for name in purgeable_by_name:
        if name not in names:
            names.append(name)

    if tm_error and du_error:
        scan.status = 'unavailable'
        scan.note = f'Could not list snapshots ({tm_error})'
        return scan.to_dict()

    scan.source = 'tmutil' if not tm_error else 'diskutil'

    for name in sorted(set(names)):
        snapshot = _build_snapshot(name, now, purgeable=purgeable_by_name.get(name))
        if snapshot.is_os_update:
            # Counted but never listed as reclaimable: these belong to the OS,
            # and one of them may be what the system is running from.
            scan.os_update_count += 1
            continue
        scan.snapshots.append(snapshot)

    # Oldest first is the order that matters here - the report leads with age.
    scan.snapshots.sort(key=lambda snap: (snap.created or '', snap.name))

    ages = [snap.age_days for snap in scan.snapshots if snap.age_days is not None]
    scan.oldest_age_days = max(ages) if ages else None
    scan.stale_count = sum(1 for age in ages if age >= STALE_AFTER_DAYS)
    scan.purgeable_count = sum(1 for snap in scan.snapshots if snap.purgeable)
    scan.count = len(scan.snapshots)
    scan.status = 'complete'

    return scan.to_dict()
