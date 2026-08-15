"""Typed data model for the storage scanner and grading layer.

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
    skipped_count: int = 0
    duration_seconds: float = 0.0

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
            skipped_count=d.get('skipped_count', 0),
            duration_seconds=d.get('duration_seconds', 0.0),
        )
