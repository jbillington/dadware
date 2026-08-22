"""Hidden storage scanner - the app caches the main storage walk can't see.

Phase 1a of `docs/roadmap/HIDDEN-STORAGE-PLAN.md`. `should_exclude()` drops
every dotfile and everything under `/Library/Caches/`, so `~/Library/Caches`
totals ~0 in today's reports even when it holds tens of gigabytes. Rather
than loosening those (load-bearing) exclusions, this module goes straight to
the known cache locations, the same way `scanners/mac_libraries.py` goes
straight to the Photos and Mail libraries.

Two design points worth keeping:

- **Sizing uses `du -skx`, not a Python walk.** Cache trees (npm, pnpm,
  Hugging Face) nest deeper than any sane depth cap, and a capped walk would
  under-report exactly the folders this feature exists to expose. `du` is
  C-speed, full-depth and disk-accurate; the per-folder timeout is the cost
  bound. `_walk_folder_size()` is the fallback for when `du` isn't there.
- **Friendly names are the feature, not a nicety.** A cache folder called
  `com.spotify.client` means nothing to the target user, so bundle IDs are
  resolved against the apps actually installed on this Mac first, then a
  small table of mainstream apps, then a reverse-DNS heuristic.
"""

import os
import plistlib
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

from scanners.models import CacheEntry, CacheRootInfo, HiddenCachesScan
from utils.path_utils import get_file_size_disk, get_folder_size_generic
from utils.subprocess_utils import log_subprocess_call

# The cache roots every Mac has. (category, path relative to home).
CACHE_ROOTS: List[Tuple[str, str]] = [
    ('caches', os.path.join('Library', 'Caches')),
    ('logs', os.path.join('Library', 'Logs')),
]

# Per-folder `du` timeout, and the budget for the whole scan. A single huge
# cache folder can't stall the report, and neither can a slow disk.
DU_TIMEOUT_SECONDS = 10
DEFAULT_SCAN_TIMEOUT_SECONDS = 45

# Piles smaller than this are noise in a report about missing gigabytes.
# They still count toward the totals - only the entry list is trimmed.
MIN_REPORT_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_TOP_N = 25

# Depth cap for the fallback walk only. `du` has no cap; this is a floor
# under a bad situation, not the normal path.
FALLBACK_MAX_DEPTH = 64

# Where installed apps live, searched (non-recursively) to map bundle IDs to
# the app names the user actually recognizes.
APPLICATION_DIRS = [
    '/Applications',
    '/Applications/Utilities',
    '/System/Applications',
    '/System/Applications/Utilities',
    os.path.join('~', 'Applications'),
]

# Mainstream apps whose cache folders are common and whose bundle IDs the
# heuristic below would mangle (or that aren't installed as a .app at all).
# Keys are lowercased bundle IDs.
KNOWN_BUNDLE_NAMES: Dict[str, str] = {
    'com.spotify.client': 'Spotify',
    'com.google.chrome': 'Google Chrome',
    'com.google.chrome.helper': 'Google Chrome',
    'com.google.drivefs': 'Google Drive',
    'com.apple.safari': 'Safari',
    'com.apple.mail': 'Mail',
    'com.apple.music': 'Music',
    'com.apple.photos': 'Photos',
    'com.apple.appstore': 'App Store',
    'com.apple.itunes': 'iTunes',
    'com.microsoft.vscode': 'Visual Studio Code',
    'com.microsoft.edgemac': 'Microsoft Edge',
    'com.microsoft.teams': 'Microsoft Teams',
    'com.microsoft.onedrive': 'OneDrive',
    'com.hnc.discord': 'Discord',
    'com.tinyspeck.slackmacgap': 'Slack',
    'us.zoom.xos': 'Zoom',
    'com.valvesoftware.steam': 'Steam',
    'com.epicgames.launcher': 'Epic Games Launcher',
    'net.whatsapp.whatsapp': 'WhatsApp',
    'org.mozilla.firefox': 'Firefox',
    'com.brave.browser': 'Brave Browser',
    'com.figma.desktop': 'Figma',
    'com.docker.docker': 'Docker Desktop',
    'com.adobe.acc.appmanager': 'Adobe Creative Cloud',
    'com.operasoftware.opera': 'Opera',
    'company.thebrowser.browser': 'Arc',
    'notion.id': 'Notion',
    'com.readdle.smartemail-mac': 'Spark',
    'com.utmapp.utm': 'UTM',
}

# Leading components of a reverse-DNS bundle ID, dropped before naming.
REVERSE_DNS_PREFIXES = {
    'com', 'org', 'net', 'io', 'co', 'uk', 'de', 'fr', 'ca', 'eu', 'us',
    'app', 'dev', 'me', 'ai', 'gg', 'tv', 'xyz', 'cloud', 'sh', 'in', 'it',
    'nl', 'ru', 'jp', 'cn', 'au', 'se', 'no', 'ch', 'at', 'is', 'la', 'ly',
}

# Trailing components that name a *kind* of program rather than the program,
# dropped so `com.spotify.client` reads as "Spotify" and not "Client".
GENERIC_BUNDLE_SUFFIXES = {
    'client', 'app', 'application', 'desktop', 'mac', 'macos', 'osx', 'ios',
    'helper', 'service', 'agent', 'daemon', 'ui', 'gui', 'beta', 'stable',
    'launcher', 'shared', 'framework', 'electron', 'native',
}

# The friendly name given to files sitting loose in a cache root rather than
# inside a per-app subfolder.
LOOSE_FILES_NAME = 'Loose files'


# ---------------------------------------------------------------------------
# Friendly app names
# ---------------------------------------------------------------------------

def read_bundle_id(app_path: str) -> Optional[str]:
    """Read `CFBundleIdentifier` out of an app bundle's `Info.plist`.

    Returns None for anything unreadable or not actually an app bundle -
    a missing plist is the normal case for stray folders, not an error.
    """
    plist_path = os.path.join(app_path, 'Contents', 'Info.plist')
    try:
        with open(plist_path, 'rb') as handle:
            plist = plistlib.load(handle)
    except (OSError, PermissionError, ValueError, plistlib.InvalidFileException):
        return None

    if not isinstance(plist, dict):
        return None
    bundle_id = plist.get('CFBundleIdentifier')
    return bundle_id if isinstance(bundle_id, str) and bundle_id else None


def build_app_name_index(app_dirs: Optional[List[str]] = None) -> Dict[str, str]:
    """Map lowercased bundle ID -> installed app name, from the apps on this Mac.

    One non-recursive `scandir` per application directory; app bundles are
    leaves, so there is nothing to recurse into. Earlier directories win, so
    a user's own `/Applications` copy beats the system one.
    """
    if app_dirs is None:
        app_dirs = APPLICATION_DIRS

    index: Dict[str, str] = {}
    for app_dir in app_dirs:
        expanded = os.path.expanduser(app_dir)
        if not os.path.isdir(expanded):
            continue
        try:
            with os.scandir(expanded) as entries:
                for entry in entries:
                    if not entry.name.endswith('.app'):
                        continue
                    try:
                        if not entry.is_dir():
                            continue
                    except OSError:
                        continue
                    bundle_id = read_bundle_id(entry.path)
                    if bundle_id:
                        index.setdefault(bundle_id.lower(), entry.name[:-len('.app')])
        except (OSError, PermissionError):
            continue

    return index


def looks_like_bundle_id(name: str) -> bool:
    """Is this folder name a reverse-DNS bundle ID rather than a plain name?

    `com.spotify.client` yes; `Firefox`, `Google`, `CloudKit` no. Two dots is
    the usual shape; a known reverse-DNS prefix carries the two-component
    ones (`notion.id` style IDs stay out - they'd read worse mangled).
    """
    if not name or ' ' in name or name.startswith('.'):
        return False
    parts = name.split('.')
    if any(not part for part in parts):
        return False
    if len(parts) >= 3:
        return True
    return len(parts) == 2 and parts[0].lower() in REVERSE_DNS_PREFIXES


def friendly_app_name(folder_name: str, app_index: Optional[Dict[str, str]] = None) -> str:
    """Turn a cache folder name into something a human recognizes.

    Installed apps first (the name in `/Applications` is the name the user
    sees in the Dock), then the mainstream table, then the reverse-DNS
    heuristic. Anything that isn't a bundle ID passes through untouched.
    """
    if not folder_name:
        return folder_name

    key = folder_name.lower()
    if app_index and key in app_index:
        return app_index[key]
    if key in KNOWN_BUNDLE_NAMES:
        return KNOWN_BUNDLE_NAMES[key]
    if not looks_like_bundle_id(folder_name):
        return folder_name

    parts = folder_name.split('.')
    if parts[0].lower() in REVERSE_DNS_PREFIXES and len(parts) > 1:
        parts = parts[1:]
    # Drop trailing "kind of program" words, but never the last thing standing.
    while len(parts) > 1 and parts[-1].lower() in GENERIC_BUNDLE_SUFFIXES:
        parts.pop()

    last = parts[-1]
    # Existing capitalization is a deliberate signal (VSCode, iTerm) - only
    # capitalize names that carry none of their own.
    return last if any(char.isupper() for char in last) else last.capitalize()


# ---------------------------------------------------------------------------
# Sizing
# ---------------------------------------------------------------------------

def _du_folder_size(path: str, timeout: float = DU_TIMEOUT_SECONDS) -> Tuple[Optional[int], Optional[str]]:
    """Size one folder with `du -skx`. Returns (bytes or None, note).

    `-s` summarizes, `-k` reports KB, `-x` stays on one filesystem so a
    mounted disk image inside a cache folder isn't counted as cache. A
    partially-unreadable folder makes `du` exit non-zero while still
    printing a usable total, so the total is taken whenever it parses and
    the permission problem is reported alongside it.
    """
    cmd = ['/usr/bin/du', '-skx', path]
    try:
        log_subprocess_call("_du_folder_size()", cmd)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, 'Timed out measuring this folder'
    except (FileNotFoundError, OSError, PermissionError, ValueError, TypeError):
        return None, None

    note = None
    stderr = (result.stderr or '').lower()
    if 'not permitted' in stderr or 'permission denied' in stderr:
        note = 'Permission restricted - size may be incomplete'

    try:
        size_kb = int((result.stdout or '').split()[0])
    except (ValueError, IndexError):
        if result.returncode != 0 and note is None:
            note = 'Could not measure this folder'
        return None, note

    return size_kb * 1024, note


def _walk_folder_size(path: str) -> int:
    """Fallback sizing when `du` is unavailable, using the shared walker.

    Same disk-accurate `st_blocks * 512` sizing `du` reports, and the same
    symlink handling, so a fallback total is comparable to a `du` total.
    """
    size, _count = get_folder_size_generic(
        path,
        size_fn=get_file_size_disk,
        skip_fn=lambda item_path, depth: False,
        max_depth=FALLBACK_MAX_DEPTH,
    )
    return size


def measure_folder(path: str, timeout: float = DU_TIMEOUT_SECONDS) -> Tuple[int, Optional[str]]:
    """Measure one cache folder, `du` first and a Python walk as backup.

    Returns (size_bytes, note). A note is a caveat worth showing the user
    (permissions, a timeout), not an internal detail.
    """
    size, note = _du_folder_size(path, timeout=timeout)
    if size is not None:
        return size, note

    try:
        return _walk_folder_size(path), note
    except (OSError, PermissionError):
        return 0, note or 'Permission restricted - size unavailable'


def _loose_files_size(root_path: str) -> int:
    """Disk usage of the files sitting directly in a cache root.

    `~/Library/Logs` in particular holds loose `.log` files next to the
    per-app folders; counting them keeps the root total honest.
    """
    total = 0
    try:
        with os.scandir(root_path) as entries:
            for entry in entries:
                try:
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    total += entry.stat(follow_symlinks=False).st_blocks * 512
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        return total
    return total


def _list_cache_folders(root_path: str) -> Tuple[List[Tuple[str, str]], Optional[str]]:
    """Top-level subfolders of a cache root, as (name, path), sorted by name.

    Sorted so a scan that runs out of time truncates reproducibly rather
    than at whatever order the filesystem happened to hand back.
    """
    folders: List[Tuple[str, str]] = []
    try:
        with os.scandir(root_path) as entries:
            for entry in entries:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        folders.append((entry.name, entry.path))
                except OSError:
                    continue
    except PermissionError:
        return [], 'Permission restricted - grant Full Disk Access to see this folder'
    except OSError:
        return [], 'Could not read this folder'

    folders.sort(key=lambda pair: pair[0])
    return folders, None


# ---------------------------------------------------------------------------
# The scan
# ---------------------------------------------------------------------------

def scan_app_caches(home: Optional[str] = None,
                    timeout_seconds: float = DEFAULT_SCAN_TIMEOUT_SECONDS,
                    min_report_bytes: int = MIN_REPORT_BYTES,
                    top_n: int = DEFAULT_TOP_N,
                    app_index: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Scan `~/Library/Caches` and `~/Library/Logs`, sized per app.

    Args:
        home: Home directory to scan (defaults to the current user's).
        timeout_seconds: Budget for the whole scan. Folders past the budget
            are left unmeasured and the scan is reported as 'partial'.
        min_report_bytes: Entries smaller than this stay out of the list
            (they still count toward the totals).
        top_n: Maximum entries to report. 0 or less means no cap.
        app_index: Prebuilt bundle ID -> app name map, for tests and for
            callers that already built one.

    Returns:
        A plain dict (`HiddenCachesScan.to_dict()`), matching the dict
        boundary the renderers and JSON manifests expect.
    """
    start_time = time.time()
    if home is None:
        home = os.path.expanduser('~')
    if app_index is None:
        app_index = build_app_name_index()

    scan = HiddenCachesScan()
    entries: List[CacheEntry] = []
    out_of_time = False

    for category, relative_path in CACHE_ROOTS:
        root_path = os.path.join(home, relative_path)
        root = CacheRootInfo(path=root_path, category=category)

        if out_of_time:
            root.status = 'partial'
            root.note = 'Ran out of time - this folder was not measured'
            scan.roots.append(root)
            continue

        if not os.path.isdir(root_path):
            root.status = 'missing'
            scan.roots.append(root)
            continue

        folders, listing_note = _list_cache_folders(root_path)
        root.folder_count = len(folders)
        if listing_note:
            root.status = 'error'
            root.note = listing_note
            scan.permission_denied = True
            scan.roots.append(root)
            continue

        for folder_name, folder_path in folders:
            if time.time() - start_time >= timeout_seconds:
                out_of_time = True
                root.status = 'partial'
                root.note = 'Ran out of time - some folders were not measured'
                break

            size_bytes, note = measure_folder(folder_path)
            if note and 'Permission' in note:
                scan.permission_denied = True

            root.size_bytes += size_bytes
            root.measured_count += 1
            entries.append(CacheEntry(
                path=folder_path,
                folder_name=folder_name,
                app_name=friendly_app_name(folder_name, app_index),
                size_bytes=size_bytes,
                category=category,
                note=note,
            ))

        loose_bytes = _loose_files_size(root_path)
        if loose_bytes:
            root.size_bytes += loose_bytes
            entries.append(CacheEntry(
                path=root_path,
                folder_name='',
                app_name=LOOSE_FILES_NAME,
                size_bytes=loose_bytes,
                category=category,
            ))

        scan.total_size_bytes += root.size_bytes
        scan.folder_count += root.folder_count
        scan.roots.append(root)

    # Biggest first, ties broken on path so reports are reproducible.
    entries.sort(key=lambda entry: (-entry.size_bytes, entry.path))
    reportable = [entry for entry in entries if entry.size_bytes >= min_report_bytes]
    scan.entries = reportable[:top_n] if top_n and top_n > 0 else reportable

    scan.scan_status = 'partial' if out_of_time else 'complete'
    scan.duration_seconds = round(time.time() - start_time, 2)
    return scan.to_dict()
