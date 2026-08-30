"""Typed data model for the scanner and grading layers.

Per the code-review boundary decision: typed objects flow through the
*scanners* and *grading* layers only. `scanners.storage.scan_storage()`
builds these dataclasses internally but always returns a plain dict (via
`.to_dict()`) so the HTML renderer and the JSON manifests saved to disk are
completely unaffected. Renderers and manifests keep consuming untyped dicts.

Quirk preserved on purpose: `FileInfo.is_docker` / `FileInfo.is_sparse` and
`FolderInfo.is_docker` are only emitted as dict keys when True (the legacy
code only ever did `file_info['is_docker'] = True`, never `= False`), so
"absent" and "False" are both possible and are NOT the same thing in the
JSON manifest. `to_dict()` reproduces that exactly. Likewise `FileInfo.mtime`
is only emitted when not None, and `FolderInfo.top_files` / `.subfolders`
are only emitted when not None (a top-level scanned folder always has these
set, even to `[]`; a nested subfolder entry - which `scan_folder_contents()`
never recurses into further - never has them at all).

The same rules apply to the hidden-storage model at the bottom of this file
(`CacheEntry` / `CacheRootInfo` / `HiddenCachesScan`, used by
`scanners.hidden_storage`): typed inside the scanner, plain dicts on the way
out, and the optional `note` key emitted only when there is a note.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from utils.formatters import format_size


@dataclass
class FileInfo:
    """A single file entry, as it appears in `top_files` (top-level, with
    `mtime`/`is_docker`/`is_sparse`) or nested inside a folder's `top_files`
    (from `scan_folder_contents()`, which never sets those three fields)."""

    path: str
    size_bytes: int
    mtime: Optional[float] = None
    is_docker: bool = False
    is_sparse: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            'path': self.path,
            'size_bytes': self.size_bytes,
            'size_human': format_size(self.size_bytes),
        }
        # mtime, is_docker, is_sparse: only present when meaningful, matching
        # the legacy dict-building code exactly (see module docstring).
        if self.mtime is not None:
            d['mtime'] = self.mtime
        if self.is_docker:
            d['is_docker'] = True
        if self.is_sparse:
            d['is_sparse'] = True
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'FileInfo':
        return cls(
            path=d.get('path', ''),
            size_bytes=d.get('size_bytes', 0),
            mtime=d.get('mtime'),
            is_docker=bool(d.get('is_docker', False)),
            is_sparse=bool(d.get('is_sparse', False)),
        )


@dataclass
class FolderInfo:
    """A folder entry. Used both for the rich top-level `top_folders` entries
    (which always carry `top_files`/`subfolders`, even as empty lists, once
    `scan_storage()` has scanned their contents) and for the simpler nested
    `subfolders` entries produced by `scan_folder_contents()` (which are leaves
    - no `is_docker` check, no further `top_files`/`subfolders`)."""

    path: str
    display: str
    size_bytes: int
    is_docker: bool = False
    top_files: Optional[List[FileInfo]] = None
    subfolders: Optional[List['FolderInfo']] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            'path': self.path,
            'path_display': self.display,
            'size_bytes': self.size_bytes,
            'size_human': format_size(self.size_bytes),
        }
        if self.is_docker:
            d['is_docker'] = True
        # top_files/subfolders: only present once scanned (see docstring) -
        # None means "not scanned", [] means "scanned, found nothing".
        if self.top_files is not None:
            d['top_files'] = [f.to_dict() for f in self.top_files]
        if self.subfolders is not None:
            d['subfolders'] = [sf.to_dict() for sf in self.subfolders]
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'FolderInfo':
        path = d.get('path') or d.get('path_display', '')
        display = d.get('path_display', path)
        top_files = d.get('top_files')
        subfolders = d.get('subfolders')
        return cls(
            path=path,
            display=display,
            size_bytes=d.get('size_bytes', 0),
            is_docker=bool(d.get('is_docker', False)),
            top_files=[FileInfo.from_dict(f) for f in top_files] if top_files is not None else None,
            subfolders=[FolderInfo.from_dict(sf) for sf in subfolders] if subfolders is not None else None,
        )


@dataclass
class VolumeInfo:
    total_bytes: int = 0
    used_bytes: int = 0
    free_bytes: int = 0
    used_percent: float = 0.0
    free_percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_bytes': self.total_bytes,
            'used_bytes': self.used_bytes,
            'free_bytes': self.free_bytes,
            'used_percent': self.used_percent,
            'free_percent': self.free_percent,
            'total_human': format_size(self.total_bytes),
            'used_human': format_size(self.used_bytes),
            'free_human': format_size(self.free_bytes),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'VolumeInfo':
        return cls(
            total_bytes=d.get('total_bytes', 0),
            used_bytes=d.get('used_bytes', 0),
            free_bytes=d.get('free_bytes', 0),
            used_percent=d.get('used_percent', 0.0),
            free_percent=d.get('free_percent', 0.0),
        )


@dataclass
class StorageScan:
    """The overall result of `scan_storage()`, pre-`metrics`. `metrics` is
    computed separately (via `scanners.grading.calculate_storage_metrics()`)
    and merged into the dict on the way out, exactly as the legacy code did."""

    scan_type: str = 'storage'
    volume: str = ''
    top_folders: List[FolderInfo] = field(default_factory=list)
    top_files: List[FileInfo] = field(default_factory=list)
    volume_info: VolumeInfo = field(default_factory=VolumeInfo)
    home_folders_total_bytes: int = 0
    # Two different reasons a file never made it into the numbers, kept apart
    # because conflating them tells the user they have a permission problem
    # they do not have. `excluded_count` is our own policy - dotfiles, .app
    # bundles, caches, /tmp, Mail and Messages (see utils.path_utils
    # .should_exclude) - and is the large one on any normal Mac.
    # `denied_count` is the honest one: the filesystem refused us.
    # `skipped_count` stays as their sum so existing manifests and readers
    # keep working.
    excluded_count: int = 0
    denied_count: int = 0
    duration_seconds: float = 0.0

    @property
    def skipped_count(self) -> int:
        return self.excluded_count + self.denied_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            'scan_type': self.scan_type,
            'volume': self.volume,
            'top_folders': [f.to_dict() for f in self.top_folders],
            'top_files': [f.to_dict() for f in self.top_files],
            'volume_info': self.volume_info.to_dict(),
            'home_folders_total_bytes': self.home_folders_total_bytes,
            'home_folders_total_human': format_size(self.home_folders_total_bytes),
            'skipped_count': self.skipped_count,
            'excluded_count': self.excluded_count,
            'denied_count': self.denied_count,
            'duration_seconds': self.duration_seconds,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'StorageScan':
        return cls(
            scan_type=d.get('scan_type', 'storage'),
            volume=d.get('volume', ''),
            top_folders=[FolderInfo.from_dict(f) for f in d.get('top_folders', [])],
            top_files=[FileInfo.from_dict(f) for f in d.get('top_files', [])],
            volume_info=VolumeInfo.from_dict(d.get('volume_info', {}) or {}),
            home_folders_total_bytes=d.get('home_folders_total_bytes', 0),
            # A manifest written before the split carries only the total, and
            # nothing records which half it was. Read it as exclusions: that
            # is what nearly all of it always was, and guessing the other way
            # would invent permission trouble the user never had.
            excluded_count=d.get('excluded_count', d.get('skipped_count', 0)),
            denied_count=d.get('denied_count', 0),
            duration_seconds=d.get('duration_seconds', 0.0),
        )


@dataclass
class CacheEntry:
    """One measured cache/log pile - a single top-level subfolder of
    `~/Library/Caches` or `~/Library/Logs` (or the loose files sitting
    directly in one of those roots).

    `folder_name` is the raw on-disk name (`com.spotify.client`); `app_name`
    is what the report shows the user (`Spotify`). `note` carries a
    human-readable caveat (a permission problem, a `du` timeout) and, like
    the storage model's optional keys, is only emitted when set."""

    path: str
    folder_name: str
    app_name: str
    size_bytes: int
    category: str = 'caches'
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            'path': self.path,
            'folder_name': self.folder_name,
            'app_name': self.app_name,
            'size_bytes': self.size_bytes,
            'size_human': format_size(self.size_bytes),
            'category': self.category,
        }
        if self.note:
            d['note'] = self.note
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'CacheEntry':
        return cls(
            path=d.get('path', ''),
            folder_name=d.get('folder_name', ''),
            app_name=d.get('app_name', ''),
            size_bytes=d.get('size_bytes', 0),
            category=d.get('category', 'caches'),
            note=d.get('note'),
        )


@dataclass
class CacheRootInfo:
    """Per-root bookkeeping for one cache location. Totals stay honest even
    when the entry list is trimmed by the reporting floor: `size_bytes` is
    every subfolder plus loose files, not just the entries that made the cut.

    `status` is 'complete', 'missing' (the root isn't on this Mac),
    'partial' (the time budget ran out mid-root) or 'error'."""

    path: str
    category: str
    size_bytes: int = 0
    folder_count: int = 0
    measured_count: int = 0
    status: str = 'complete'
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            'path': self.path,
            'category': self.category,
            'size_bytes': self.size_bytes,
            'size_human': format_size(self.size_bytes),
            'folder_count': self.folder_count,
            'measured_count': self.measured_count,
            'status': self.status,
        }
        if self.note:
            d['note'] = self.note
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'CacheRootInfo':
        return cls(
            path=d.get('path', ''),
            category=d.get('category', 'caches'),
            size_bytes=d.get('size_bytes', 0),
            folder_count=d.get('folder_count', 0),
            measured_count=d.get('measured_count', 0),
            status=d.get('status', 'complete'),
            note=d.get('note'),
        )


@dataclass
class HiddenCachesScan:
    """The result of `scanners.hidden_storage.scan_app_caches()`.

    `entries` is only the reportable slice (above the size floor, capped at
    the top N); `total_size_bytes` is the full measured total across every
    root, so the report can say "and 240 smaller ones" without lying about
    the pile. Follows the same boundary rule as `StorageScan`: typed inside
    the scanner, a plain dict on the way out."""

    scan_type: str = 'hidden_caches'
    entries: List[CacheEntry] = field(default_factory=list)
    roots: List[CacheRootInfo] = field(default_factory=list)
    total_size_bytes: int = 0
    folder_count: int = 0
    scan_status: str = 'complete'
    permission_denied: bool = False
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'scan_type': self.scan_type,
            'entries': [e.to_dict() for e in self.entries],
            'roots': [r.to_dict() for r in self.roots],
            'total_size_bytes': self.total_size_bytes,
            'total_size_human': format_size(self.total_size_bytes),
            'folder_count': self.folder_count,
            'scan_status': self.scan_status,
            'permission_denied': self.permission_denied,
            'duration_seconds': self.duration_seconds,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'HiddenCachesScan':
        return cls(
            scan_type=d.get('scan_type', 'hidden_caches'),
            entries=[CacheEntry.from_dict(e) for e in d.get('entries', [])],
            roots=[CacheRootInfo.from_dict(r) for r in d.get('roots', [])],
            total_size_bytes=d.get('total_size_bytes', 0),
            folder_count=d.get('folder_count', 0),
            scan_status=d.get('scan_status', 'complete'),
            permission_denied=bool(d.get('permission_denied', False)),
            duration_seconds=d.get('duration_seconds', 0.0),
        )


@dataclass
class SnapshotInfo:
    """One APFS local snapshot (`scanners.snapshots`).

    Note what is NOT here: a size. APFS snapshots share blocks via
    copy-on-write, so a per-snapshot size has no single true value - delete
    one and the others appear to grow. `created` comes from the timestamp
    Time Machine encodes in the snapshot's own name, the only unprivileged
    source for it, and is None for snapshots that don't carry one.
    `purgeable` is macOS's own flag, and is None when `diskutil` could not
    be consulted."""

    name: str
    created: Optional[str] = None
    age_days: Optional[int] = None
    is_os_update: bool = False
    purgeable: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            'name': self.name,
            'created': self.created,
            'age_days': self.age_days,
            'is_os_update': self.is_os_update,
        }
        # Only emitted when macOS actually told us, so "unknown" and "no"
        # stay distinguishable in the JSON manifest.
        if self.purgeable is not None:
            d['purgeable'] = self.purgeable
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'SnapshotInfo':
        return cls(
            name=d.get('name', ''),
            created=d.get('created'),
            age_days=d.get('age_days'),
            is_os_update=bool(d.get('is_os_update', False)),
            purgeable=d.get('purgeable'),
        )


@dataclass
class SnapshotScan:
    """The result of `scanners.snapshots.scan_snapshots()`.

    `count` and `snapshots` cover user-reclaimable Time Machine snapshots
    only; OS update snapshots are counted separately in `os_update_count`
    and never listed, because they are not the user's to remove and one of
    them may be what the system is currently running from.

    `status` is 'complete' or 'unavailable' (not a Mac, or the tools could
    not be run) - never a raised exception."""

    scan_type: str = 'snapshots'
    snapshots: List[SnapshotInfo] = field(default_factory=list)
    count: int = 0
    os_update_count: int = 0
    stale_count: int = 0
    purgeable_count: int = 0
    oldest_age_days: Optional[int] = None
    source: str = ''
    status: str = 'complete'
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            'scan_type': self.scan_type,
            'snapshots': [s.to_dict() for s in self.snapshots],
            'count': self.count,
            'os_update_count': self.os_update_count,
            'stale_count': self.stale_count,
            'purgeable_count': self.purgeable_count,
            'oldest_age_days': self.oldest_age_days,
            'source': self.source,
            'status': self.status,
        }
        if self.note:
            d['note'] = self.note
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'SnapshotScan':
        return cls(
            scan_type=d.get('scan_type', 'snapshots'),
            snapshots=[SnapshotInfo.from_dict(s) for s in d.get('snapshots', [])],
            count=d.get('count', 0),
            os_update_count=d.get('os_update_count', 0),
            stale_count=d.get('stale_count', 0),
            purgeable_count=d.get('purgeable_count', 0),
            oldest_age_days=d.get('oldest_age_days'),
            source=d.get('source', ''),
            status=d.get('status', 'complete'),
            note=d.get('note'),
        )
