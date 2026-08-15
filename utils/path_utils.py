"""Shared path filtering and folder size utilities."""

import os

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


def is_sparse_file(path):
    """
    Check if a file is a sparse file (virtual disk image).
    Sparse files report huge logical sizes but use little actual space.
    """
    if not os.path.isfile(path):
        return False

    if any(path.lower().endswith(ext) for ext in VIRTUAL_DISK_EXTENSIONS):
        return True

    try:
        logical_size = os.path.getsize(path)
        stat_info = os.stat(path)
        actual_size = stat_info.st_blocks * 512

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


def get_file_size(path):
    """
    Get file size with smart handling for Docker/sparse files.
    Returns actual disk usage for Docker/sparse files, logical size otherwise.
    """
    if is_docker_path(path) or is_sparse_file(path):
        stat_info = os.stat(path)
        return stat_info.st_blocks * 512
    else:
        return os.path.getsize(path)


def get_file_size_disk(path):
    """
    Get actual disk usage (st_blocks * 512) for a file.
    Used by mac_libraries scanner where all files use disk-level sizing.
    """
    stat_info = os.stat(path)
    return stat_info.st_blocks * 512
