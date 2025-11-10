"""Mac app library scanner - finds and measures Mac app data libraries."""

import os
import glob


def format_size(bytes):
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"


def get_folder_size(folder_path, min_size_bytes=0, max_depth=10, current_depth=0, skip_hidden=False):
    """Calculate folder size recursively, respecting depth limit."""
    total_size = 0
    file_count = 0
    
    if current_depth > max_depth:
        return 0, 0
    
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            
            # Skip hidden files/folders only if requested (for Photos libraries, we need to include them)
            if skip_hidden and os.path.basename(item).startswith('.'):
                continue
            
            try:
                if os.path.islink(item_path):
                    continue
                
                if os.path.isdir(item_path):
                    size, count = get_folder_size(item_path, min_size_bytes, max_depth, current_depth + 1)
                    total_size += size
                    file_count += count
                elif os.path.isfile(item_path):
                    try:
                        size = os.path.getsize(item_path)
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


def scan_photos_library():
    """Scan for Photos libraries (.photoslibrary)."""
    libraries = []
    home = os.path.expanduser('~')
    
    # Check common locations - be more thorough
    search_paths = [
        os.path.join(home, 'Pictures'),
        home,
        os.path.join(home, 'Desktop'),
        '/Users'
    ]
    
    # Also check directly for common names
    direct_paths = [
        os.path.join(home, 'Pictures', 'Photos Library.photoslibrary'),
        os.path.join(home, 'Pictures', 'iPhoto Library.photolibrary'),  # Old iPhoto
    ]
    
    # Check direct paths first
    for lib_path in direct_paths:
        if os.path.exists(lib_path) and os.path.isdir(lib_path):
            try:
                # Don't skip hidden files for Photos libraries
                size, _ = get_folder_size(lib_path, min_size_bytes=0, max_depth=10, current_depth=0, skip_hidden=False)
                libraries.append({
                    'path': lib_path,
                    'name': os.path.basename(lib_path),
                    'size_bytes': size,
                    'size_human': format_size(size),
                    'type': 'photos'
                })
            except (OSError, PermissionError):
                continue
    
    # Then search recursively
    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue
        
        try:
            # Find all .photoslibrary bundles
            pattern = os.path.join(search_path, '**', '*.photoslibrary')
            for lib_path in glob.glob(pattern, recursive=True):
                if os.path.isdir(lib_path):
                    # Skip if we already found this one
                    if any(lib['path'] == lib_path for lib in libraries):
                        continue
                    try:
                        # Don't skip hidden files for Photos libraries - they contain important data
                        size, _ = get_folder_size(lib_path, min_size_bytes=0, max_depth=10, current_depth=0, skip_hidden=False)
                        # If size is 0, try using du command as fallback (Photos libraries may have permission restrictions)
                        if size == 0:
                            try:
                                import subprocess
                                result = subprocess.run(['du', '-sk', lib_path], capture_output=True, text=True, timeout=10)
                                if result.returncode == 0:
                                    # du returns size in KB, convert to bytes
                                    size = int(result.stdout.split()[0]) * 1024
                            except (subprocess.TimeoutExpired, ValueError, IndexError, FileNotFoundError):
                                pass
                        libraries.append({
                            'path': lib_path,
                            'name': os.path.basename(lib_path),
                            'size_bytes': size,
                            'size_human': format_size(size),
                            'type': 'photos'
                        })
                    except (OSError, PermissionError) as e:
                        # If we can't access it, still add it with 0 size so user knows it exists
                        libraries.append({
                            'path': lib_path,
                            'name': os.path.basename(lib_path),
                            'size_bytes': 0,
                            'size_human': format_size(0),
                            'type': 'photos',
                            'note': 'Permission restricted - size unavailable'
                        })
                        continue
        except (OSError, PermissionError):
            continue
    
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
                                size += os.path.getsize(file_path)
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


def scan_all_mac_libraries():
    """Scan all Mac app libraries and return combined results."""
    results = {
        'photos': scan_photos_library(),
        'music': scan_music_library(),
        'messages': scan_messages(),
        'mail': scan_mail(),
        'time_machine': scan_time_machine_backups(),
        'creative': scan_creative_libraries()
    }
    
    # Calculate total
    total_size = sum(
        result.get('total_size_bytes', result.get('size_bytes', 0))
        for result in results.values()
    )
    
    results['total_size_bytes'] = total_size
    results['total_size_human'] = format_size(total_size)
    
    return results

