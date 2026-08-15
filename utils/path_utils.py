"""Shared path filtering and folder size utilities."""

import os
import stat as stat_module

# Substrings (matched against a lowercased path) that indicate a Docker-related
# file or directory. Hoisted to module level since is_docker_path() runs once
# per file during scans.
DOCKER_PATH_PATTERNS = [
    '/docker/',
    '/.docker/',
    'docker/containers',
    'docker/volumes',
    'docker/data',
    'com.docker.',
    'docker.qcow2',
    'docker.raw',
]

# File extensions associated with virtual disk images (sparse files).
VIRTUAL_DISK_EXTENSIONS = ['.qcow2', '.vmdk', '.vdi', '.vhd', '.vhdx', '.raw']

# Top-level root directories to exclude from storage scanning.
EXCLUDED_ROOT_DIRS = ['System', 'Library', 'Applications', 'usr', 'bin', 'sbin', 'private', 'var']

# Substrings that mark a path as heavy/noisy and safe to skip during library
# scanning (can cause hangs, e.g. iCloud/CloudStorage paths).
LIBRARY_SKIP_PATTERNS = [
    'Mobile Documents',
    'CloudStorage',
    'Containers',
    'Group Containers',
]


def is_docker_path(path):
    """
    Check if a path is related to Docker.
    Returns True if path is a Docker container, volume, or data directory.
    """
    path_lower = path.lower()

    for pattern in DOCKER_PATH_PATTERNS:
        if pattern in path_lower:
            return True

    basename = os.path.basename(path_lower)
    if basename.startswith('docker') and any(basename.endswith(ext) for ext in ['.qcow2', '.raw', '.vmdk']):
        return True

    return False


def is_sparse_file(path, stat_result=None):
    """
    Check if a file is a sparse file (virtual disk image).
    Sparse files report huge logical sizes but use little actual space.

    If `stat_result` (an os.stat_result, e.g. from a prior os.stat() or
    DirEntry.stat() call) is provided, it is used instead of re-statting
    the path.
    """
    if stat_result is None:
        if not os.path.isfile(path):
            return False
    else:
        if not stat_module.S_ISREG(stat_result.st_mode):
            return False

    if any(path.lower().endswith(ext) for ext in VIRTUAL_DISK_EXTENSIONS):
        return True

    try:
        if stat_result is None:
            stat_result = os.stat(path)
        logical_size = stat_result.st_size
        actual_size = stat_result.st_blocks * 512

        if logical_size > 0 and actual_size > 0:
            ratio = logical_size / actual_size
            if ratio > 10:
                return True
    except (OSError, PermissionError):
        pass

    return False


def should_exclude(path, depth=0):
    """Check if path should be excluded from storage scanning."""
    path_parts = path.split(os.sep)

    if len(path_parts) > 1:
        root_part = path_parts[1]
        if root_part in EXCLUDED_ROOT_DIRS:
            return True

    if path.endswith('.app') or '/.app/' in path:
        return True

    if path.endswith('.photoslibrary') or '/.photoslibrary/' in path:
        return True

    if '/Library/Caches/' in path or '/tmp/' in path or path.endswith('/tmp'):
        return True

    basename = os.path.basename(path)
    if basename.startswith('.'):
        return True

    if '/Library/Mail/' in path:
        return True

    if '/Library/Messages/' in path or path.endswith('/Library/Messages'):
        return True

    if is_docker_path(path) and os.path.isdir(path):
        if any(x in path.lower() for x in ['/containers/', '/volumes/', '/data/']):
            return True

    return False


def should_skip_path(path):
    """
    Check if a path should be skipped during library scanning.
    Skips heavy/noisy paths that can cause hangs.
    """
    path_str = str(path)
    return any(pattern in path_str for pattern in LIBRARY_SKIP_PATTERNS)


def _folder_basename(folder):
    """
    Return the basename to match a top_folders entry against, preferring
    the absolute 'path' and falling back to the relative 'path_display'.
    Either key may be missing or empty.
    """
    path = folder.get('path') or folder.get('path_display') or ''
    return os.path.basename(path) if path else ''


def find_folder(top_folders, name):
    """
    Return the first folder dict in `top_folders` whose basename matches
    `name`, or None if there is no match.

    Matches on os.path.basename(path) == name (checking 'path' first, then
    falling back to 'path_display' if 'path' is missing/empty), so a folder
    like '/Users/me/Backups/Old-Downloads-Archive' does NOT match 'Downloads'
    - only an actual '.../Downloads' path does. Falls back to a
    case-insensitive basename comparison (macOS volumes are usually
    case-insensitive) but never falls back to substring matching.
    """
    name_lower = name.lower()
    fallback = None
    for folder in top_folders:
        basename = _folder_basename(folder)
        if not basename:
            continue
        if basename == name:
            return folder
        if fallback is None and basename.lower() == name_lower:
            fallback = folder
    return fallback


def basenames_in(top_folders, names):
    """
    Return the subset of `top_folders` whose basename (per the same rules as
    find_folder) matches one of `names`, preserving order. `names` is
    matched exactly first; a case-insensitive match is accepted as a
    fallback (never substring matching).
    """
    name_set = set(names)
    name_set_lower = {n.lower() for n in names}
    matches = []
    for folder in top_folders:
        basename = _folder_basename(folder)
        if not basename:
            continue
        if basename in name_set or basename.lower() in name_set_lower:
            matches.append(folder)
    return matches


def get_file_size(path, stat_result=None):
    """
    Get file size with smart handling for Docker/sparse files.
    Returns actual disk usage for Docker/sparse files, logical size otherwise.

    If `stat_result` is provided, it is reused instead of re-statting the
    path. Otherwise a single os.stat() call is made and passed down to
    is_sparse_file(), so this function does at most one stat syscall.
    """
    if stat_result is None:
        stat_result = os.stat(path)

    if is_docker_path(path) or is_sparse_file(path, stat_result=stat_result):
        return stat_result.st_blocks * 512
    else:
        return stat_result.st_size


def get_file_size_disk(path):
    """
    Get actual disk usage (st_blocks * 512) for a file.
    Used by mac_libraries scanner where all files use disk-level sizing.
    """
    stat_info = os.stat(path)
    return stat_info.st_blocks * 512


def get_folder_size_generic(folder_path, size_fn, skip_fn, min_size_bytes=0,
                             max_depth=2, current_depth=0, skip_hidden=False):
    """
    Shared recursive folder-size calculation, used by both the storage and
    mac_libraries scanners.

    Args:
        folder_path: Folder to measure.
        size_fn: Callable(path) -> int, returns a file's size in bytes.
        skip_fn: Callable(path, depth) -> bool, decides whether a path
            (folder or item) should be skipped.
        min_size_bytes: Minimum file size to count toward the total.
        max_depth: Maximum recursion depth.
        current_depth: Current recursion depth (used internally).
        skip_hidden: If True, skip items whose basename starts with '.'.

    Returns:
        (total_size_bytes, file_count) tuple.
    """
    total_size = 0
    file_count = 0

    if skip_fn(folder_path, current_depth):
        return 0, 0

    if current_depth > max_depth:
        return 0, 0

    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)

            if skip_hidden and os.path.basename(item).startswith('.'):
                continue

            if skip_fn(item_path, current_depth):
                continue

            try:
                if os.path.islink(item_path):
                    # Skip symlinks to avoid double-counting
                    continue

                if os.path.isdir(item_path):
                    size, count = get_folder_size_generic(
                        item_path, size_fn, skip_fn, min_size_bytes,
                        max_depth, current_depth + 1, skip_hidden
                    )
                    total_size += size
                    file_count += count
                elif os.path.isfile(item_path):
                    try:
                        size = size_fn(item_path)
                        if size >= min_size_bytes:
                            total_size += size
                            file_count += 1
                    except (OSError, PermissionError):
                        pass
            except (OSError, PermissionError):
                pass
    except (OSError, PermissionError):
        pass

    return total_size, file_count
