"""Shared path filtering and folder size utilities."""

import os


def is_docker_path(path):
    """
    Check if a path is related to Docker.
    Returns True if path is a Docker container, volume, or data directory.
    """
    path_lower = path.lower()

    docker_patterns = [
        '/docker/',
        '/.docker/',
        'docker/containers',
        'docker/volumes',
        'docker/data',
        'com.docker.',
        'docker.qcow2',
        'Docker.raw',
    ]

    for pattern in docker_patterns:
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

    virtual_disk_extensions = ['.qcow2', '.vmdk', '.vdi', '.vhd', '.vhdx', '.raw']
    if any(path.lower().endswith(ext) for ext in virtual_disk_extensions):
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
        if root_part in ['System', 'Library', 'Applications', 'usr', 'bin', 'sbin', 'private', 'var']:
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
    skip_patterns = [
        'Mobile Documents',
        'CloudStorage',
        'Containers',
        'Group Containers',
    ]
    return any(pattern in path_str for pattern in skip_patterns)


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
