"""Mac app library scanner - finds and measures Mac app data libraries."""

import os
import glob
import subprocess
import time

from utils.formatters import format_size
from utils.path_utils import should_skip_path, get_file_size_disk, get_folder_size_generic


def get_folder_size(folder_path, min_size_bytes=0, max_depth=10, current_depth=0, skip_hidden=False):
    """
    Calculate folder size recursively, respecting depth limit.
    Skips heavy paths like Mobile Documents, CloudStorage, Containers.
    Uses actual disk usage (st_blocks) for all files.

    Thin wrapper around the shared utils.path_utils.get_folder_size_generic(),
    using the library scanner's sizing (get_file_size_disk) and skip
    (should_skip_path, which is not depth-aware) rules.
    """
    return get_folder_size_generic(
        folder_path,
        size_fn=get_file_size_disk,
        skip_fn=lambda path, depth: should_skip_path(path),
        min_size_bytes=min_size_bytes,
        max_depth=max_depth,
        current_depth=current_depth,
        skip_hidden=skip_hidden,
    )


def find_photos_libraries():
    """
    Find Photos libraries using non-recursive search in allowlist paths only.
    Returns list of .photoslibrary bundle paths.
    """
    libraries = []
    home = os.path.expanduser('~')
    
    # Small allowlist of base paths - no recursive glob
    search_paths = [
        os.path.join(home, 'Pictures'),
        os.path.join(home, 'Library', 'Application Support', 'Photos'),
    ]
    
    # Also check for common direct paths
    direct_paths = [
        os.path.join(home, 'Pictures', 'Photos Library.photoslibrary'),
        os.path.join(home, 'Pictures', 'iPhoto Library.photolibrary'),  # Old iPhoto
    ]
    
    # Check direct paths first
    for lib_path in direct_paths:
        if os.path.exists(lib_path) and os.path.isdir(lib_path):
            libraries.append(lib_path)
    
    # Check allowlist paths using non-recursive os.scandir()
    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue
        
        try:
            with os.scandir(search_path) as entries:
                for entry in entries:
                    if entry.is_dir() and entry.name.endswith('.photoslibrary'):
                        lib_path = entry.path
                        if lib_path not in libraries:
                            libraries.append(lib_path)
        except (OSError, PermissionError):
            continue
    
    return libraries


def get_photos_library_size(lib_path):
    """
    Get size of a Photos library using du -skx (treats as leaf, no recursion).
    Returns size in bytes, or 0 if unavailable.
    """
    # Defensive check: lib_path must be valid
    if not lib_path or not isinstance(lib_path, str):
        return 0
    
    try:
        # Use du -skx to get size without recursing into the package
        cmd = ['/usr/bin/du', '-skx', lib_path]
        from utils.subprocess_utils import log_subprocess_call
        log_subprocess_call("get_photos_library_size()", cmd)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # du returns size in KB, convert to bytes
            size_kb = int(result.stdout.split()[0])
            return size_kb * 1024
    except (subprocess.TimeoutExpired, ValueError, IndexError, FileNotFoundError, OSError, PermissionError, TypeError):
        pass
    
    return 0


def scan_photos_library():
    """
    Scan for Photos libraries (.photoslibrary).
    Uses non-recursive search in allowlist paths only.
    Treats each library as a leaf and uses du -skx for size.
    """
    libraries = []
    found_paths = find_photos_libraries()
    
    for lib_path in found_paths:
        try:
            size_bytes = get_photos_library_size(lib_path)
            libraries.append({
                'path': lib_path,
                'name': os.path.basename(lib_path),
                'size_bytes': size_bytes,
                'size_human': format_size(size_bytes),
                'type': 'photos'
            })
        except (OSError, PermissionError):
            # If we can't access it, still add it with 0 size so user knows it exists
            libraries.append({
                'path': lib_path,
                'name': os.path.basename(lib_path),
                'size_bytes': 0,
                'size_human': format_size(0),
                'type': 'photos',
                'note': 'Permission restricted - size unavailable'
            })
    
    # Sort by size
    libraries.sort(key=lambda x: x['size_bytes'], reverse=True)
    
    total_size = sum(lib['size_bytes'] for lib in libraries)
    
    return {
        'type': 'photos',
        'libraries': libraries,
        'total_size_bytes': total_size,
        'total_size_human': format_size(total_size),
        'count': len(libraries)
    }


def scan_music_library():
    """Scan for Music/iTunes libraries."""
    home = os.path.expanduser('~')
    music_paths = [
        os.path.join(home, 'Music', 'Music'),
        os.path.join(home, 'Music', 'iTunes'),
        os.path.join(home, 'Music')
    ]
    
    libraries = []
    total_size = 0
    
    for music_path in music_paths:
        if os.path.exists(music_path) and os.path.isdir(music_path):
            try:
                size, _ = get_folder_size(music_path, min_size_bytes=0, max_depth=10, current_depth=0)
                libraries.append({
                    'path': music_path,
                    'name': os.path.basename(music_path),
                    'size_bytes': size,
                    'size_human': format_size(size),
                    'type': 'music'
                })
                total_size += size
            except (OSError, PermissionError):
                continue
    
    return {
        'type': 'music',
        'libraries': libraries,
        'total_size_bytes': total_size,
        'total_size_human': format_size(total_size),
        'count': len(libraries)
    }


def scan_messages():
    """Scan Messages library."""
    home = os.path.expanduser('~')
    messages_path = os.path.join(home, 'Library', 'Messages')
    
    if not os.path.exists(messages_path):
        return {
            'type': 'messages',
            'path': messages_path,
            'size_bytes': 0,
            'size_human': format_size(0),
            'count': 0
        }
    
    try:
        # Try with deeper depth for Messages as it can have nested structure
        # Don't skip hidden files - Messages uses hidden files
        size, count = get_folder_size(messages_path, min_size_bytes=0, max_depth=15, current_depth=0, skip_hidden=False)
        # If we got 0, try a more aggressive scan
        if size == 0:
            # Check if directory exists and has contents
            try:
                if os.listdir(messages_path):
                    # Directory exists but size is 0 - might be permission issue
                    # Try to get size of individual files
                    size = 0
                    for root, dirs, files in os.walk(messages_path):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                # Use actual disk usage (st_blocks) instead of logical size
                                stat_info = os.stat(file_path)
                                size += stat_info.st_blocks * 512
                            except (OSError, PermissionError):
                                pass
                        # Limit depth manually
                        if root.count(os.sep) - messages_path.count(os.sep) >= 5:
                            dirs[:] = []
            except (OSError, PermissionError):
                pass
        
        return {
            'type': 'messages',
            'path': messages_path,
            'size_bytes': size,
            'size_human': format_size(size),
            'count': count
        }
    except (OSError, PermissionError) as e:
        # Return 0 but don't fail completely
        return {
            'type': 'messages',
            'path': messages_path,
            'size_bytes': 0,
            'size_human': format_size(0),
            'count': 0
        }


def scan_mail():
    """Scan Mail library."""
    home = os.path.expanduser('~')
    mail_path = os.path.join(home, 'Library', 'Mail')
    
    if not os.path.exists(mail_path):
        return {
            'type': 'mail',
            'path': mail_path,
            'size_bytes': 0,
            'size_human': format_size(0),
            'count': 0
        }
    
    try:
        # Don't skip hidden files for Mail
        size, count = get_folder_size(mail_path, min_size_bytes=0, max_depth=10, current_depth=0, skip_hidden=False)
        return {
            'type': 'mail',
            'path': mail_path,
            'size_bytes': size,
            'size_human': format_size(size),
            'count': count
        }
    except (OSError, PermissionError):
        return {
            'type': 'mail',
            'path': mail_path,
            'size_bytes': 0,
            'size_human': format_size(0),
            'count': 0
        }


def scan_time_machine_backups():
    """Scan Time Machine backups."""
    backup_paths = [
        '/Backups.backupdb',
        '/Volumes/*/Backups.backupdb'
    ]
    
    backups = []
    total_size = 0
    
    for pattern in backup_paths:
        for backup_path in glob.glob(pattern):
            if os.path.exists(backup_path) and os.path.isdir(backup_path):
                try:
                    size, _ = get_folder_size(backup_path, min_size_bytes=0, max_depth=5, current_depth=0)
                    backups.append({
                        'path': backup_path,
                        'name': os.path.basename(backup_path),
                        'size_bytes': size,
                        'size_human': format_size(size),
                        'type': 'time_machine'
                    })
                    total_size += size
                except (OSError, PermissionError):
                    continue
    
    return {
        'type': 'time_machine',
        'backups': backups,
        'total_size_bytes': total_size,
        'total_size_human': format_size(total_size),
        'count': len(backups)
    }


def scan_creative_libraries():
    """Scan creative app libraries (GarageBand, Logic Pro, Final Cut, etc.)."""
    home = os.path.expanduser('~')
    
    # Common creative app library locations
    creative_paths = [
        # GarageBand
        os.path.join(home, 'Library', 'Audio', 'Apple Loops'),
        os.path.join(home, 'Music', 'Audio Music Apps'),
        
        # Logic Pro
        os.path.join(home, 'Music', 'Audio Music Apps'),
        
        # Final Cut Pro
        os.path.join(home, 'Movies', 'Motion Templates'),
        os.path.join(home, 'Movies', 'Final Cut Events'),
        os.path.join(home, 'Movies', 'Final Cut Projects'),
        
        # Other creative apps
        os.path.join(home, 'Library', 'Application Support', 'Aperture'),
        os.path.join(home, 'Library', 'Application Support', 'Final Cut Pro'),
    ]
    
    libraries = []
    total_size = 0
    
    for lib_path in creative_paths:
        if os.path.exists(lib_path) and os.path.isdir(lib_path):
            try:
                size, _ = get_folder_size(lib_path, min_size_bytes=0, max_depth=5, current_depth=0)
                if size > 0:  # Only include if it has content
                    libraries.append({
                        'path': lib_path,
                        'name': os.path.basename(lib_path),
                        'size_bytes': size,
                        'size_human': format_size(size),
                        'type': 'creative'
                    })
                    total_size += size
            except (OSError, PermissionError):
                continue
    
    return {
        'type': 'creative',
        'libraries': libraries,
        'total_size_bytes': total_size,
        'total_size_human': format_size(total_size),
        'count': len(libraries)
    }


def scan_all_mac_libraries(timeout_seconds=10):
    """
    Scan all Mac app libraries and return combined results.
    
    Args:
        timeout_seconds: Maximum time budget for the entire scan (default: 10s)
    
    Returns:
        Dictionary with scan results, including 'scan_status' field ('complete', 'partial', or 'interrupted')
    """
    start_time = time.time()
    results = {}
    status = 'complete'
    interrupted_scans = []
    
    # List of scanner functions to run
    scanners = [
        ('photos', scan_photos_library),
        ('music', scan_music_library),
        ('messages', scan_messages),
        ('mail', scan_mail),
        ('time_machine', scan_time_machine_backups),
        ('creative', scan_creative_libraries),
    ]
    
    try:
        for scan_name, scan_func in scanners:
            # Check time budget before each scan
            elapsed = time.time() - start_time
            if elapsed >= timeout_seconds:
                status = 'partial'
                interrupted_scans.append(scan_name)
                # Mark remaining scans as skipped
                for remaining_name, _ in scanners:
                    if remaining_name not in results:
                        results[remaining_name] = {
                            'type': remaining_name,
                            'status': 'skipped',
                            'reason': 'time-limited',
                            'total_size_bytes': 0,
                            'total_size_human': format_size(0),
                            'count': 0
                        }
                break
            
            try:
                result = scan_func()
                result['status'] = 'complete'
                results[scan_name] = result
            except KeyboardInterrupt:
                # User pressed Ctrl-C - re-raise to handle at top level
                raise
            except Exception as e:
                # Other errors - mark as failed but continue
                results[scan_name] = {
                    'type': scan_name,
                    'status': 'error',
                    'error': str(e),
                    'total_size_bytes': 0,
                    'total_size_human': format_size(0),
                    'count': 0
                }
    
    except KeyboardInterrupt:
        # Handle Ctrl-C at top level - return partial results gracefully
        status = 'interrupted'
        # Mark any remaining scans as skipped
        for scan_name, _ in scanners:
            if scan_name not in results:
                results[scan_name] = {
                    'type': scan_name,
                    'status': 'skipped',
                    'reason': 'scan-interrupted',
                    'total_size_bytes': 0,
                    'total_size_human': format_size(0),
                    'count': 0
                }
    
    # Calculate total from completed scans
    total_size = sum(
        result.get('total_size_bytes', result.get('size_bytes', 0))
        for result in results.values()
        if result.get('status') == 'complete'
    )
    
    results['total_size_bytes'] = total_size
    results['total_size_human'] = format_size(total_size)
    results['scan_status'] = status
    if interrupted_scans:
        results['interrupted_scans'] = interrupted_scans
    
    return results

