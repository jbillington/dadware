"""Storage scanner - finds large files and folders."""

import os
import time
from collections import defaultdict


def format_size(bytes):
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"


def parse_size(size_str):
    """Parse size string like '500MB' or '1.5GB' into bytes."""
    if not size_str:
        return 0
    
    size_str = size_str.upper().strip()
    
    # Extract number and unit
    multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
    
    for unit, mult in multipliers.items():
        if size_str.endswith(unit):
            try:
                num = float(size_str[:-len(unit)])
                return int(num * mult)
            except ValueError:
                return 0
    
    # Try to parse as plain number (assume bytes)
    try:
        return int(float(size_str))
    except ValueError:
        return 0


def should_exclude(path, depth=0):
    """Check if path should be excluded from scanning."""
    path_parts = path.split(os.sep)
    
    # Skip system directories at root level
    if len(path_parts) > 1:
        root_part = path_parts[1]
        if root_part in ['System', 'Library', 'Applications', 'usr', 'bin', 'sbin', 'private', 'var']:
            return True
    
    # Skip app bundles
    if path.endswith('.app') or '/.app/' in path:
        return True
    
    # Skip Photos libraries
    if path.endswith('.photoslibrary') or '/.photoslibrary/' in path:
        return True
    
    # Skip caches
    if '/Library/Caches/' in path or '/tmp/' in path or path.endswith('/tmp'):
        return True
    
    # Skip hidden files/folders (starting with .)
    basename = os.path.basename(path)
    if basename.startswith('.'):
        return True
    
    # Skip Mail data
    if '/Library/Mail/' in path:
        return True
    
    return False


def get_folder_size(folder_path, min_size_bytes=0, max_depth=2, current_depth=0):
    """Calculate folder size recursively, respecting depth limit."""
    total_size = 0
    file_count = 0
    
    if should_exclude(folder_path, current_depth):
        return 0, 0
    
    if current_depth > max_depth:
        return 0, 0
    
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            
            if should_exclude(item_path, current_depth):
                continue
            
            try:
                if os.path.islink(item_path):
                    # Skip symlinks to avoid double-counting
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


def scan_folder_contents(folder_path, max_files=100, max_subfolders=10):
    """Scan a specific folder and return its files and subfolders."""
    files = []
    subfolders = []
    
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return files, subfolders
    
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            
            if should_exclude(item_path, 0):
                continue
            
            try:
                if os.path.islink(item_path):
                    continue
                
                if os.path.isdir(item_path):
                    # Calculate subfolder size
                    size, _ = get_folder_size(item_path, min_size_bytes=0, max_depth=1, current_depth=0)
                    subfolders.append({
                        'path': item,
                        'path_display': item,
                        'size_bytes': size,
                        'size_human': format_size(size)
                    })
                elif os.path.isfile(item_path):
                    try:
                        size = os.path.getsize(item_path)
                        files.append({
                            'path': item_path,
                            'size_bytes': size,
                            'size_human': format_size(size)
                        })
                    except (OSError, PermissionError):
                        pass
            except (OSError, PermissionError):
                pass
    except (OSError, PermissionError):
        pass
    
    # Sort and limit
    files.sort(key=lambda x: x['size_bytes'], reverse=True)
    subfolders.sort(key=lambda x: x['size_bytes'], reverse=True)
    
    return files[:max_files], subfolders[:max_subfolders]


def scan_storage(path, depth=2, top_n=500, min_size_bytes=0, timeout=None, progress_callback=None):
    """
    Scan storage and return structured data.
    
    Args:
        path: Path to scan
        depth: Maximum depth to scan (default: 2)
        top_n: Number of top files to return (default: 500)
        min_size_bytes: Minimum file size to include (default: 0)
        timeout: Maximum time to spend scanning in seconds (None = no timeout, user can Ctrl+C)
        progress_callback: Optional function(items_found, elapsed_time) called periodically
    """
    start_time = time.time()
    skipped_count = 0
    
    # Track largest files
    largest_files = []
    
    # Track folder sizes (depth 2) - store both key and actual path
    folder_sizes = defaultdict(int)
    folder_paths = {}  # Map folder_key to actual folder path
    
    print(f"Scanning {path}...")
    print("→ digging through the attic...")
    
    items_found = 0
    last_progress_time = start_time
    progress_interval = 2  # Call callback every 2 seconds (more frequent for slow machines)
    last_heartbeat_time = start_time
    heartbeat_interval = 5  # Force update every 5 seconds even if no new items
    
    try:
        for root, dirs, files in os.walk(path):
            # Check timeout (if specified)
            current_time = time.time()
            if timeout is not None and (current_time - start_time > timeout):
                print(f"\n→ timeout reached ({timeout}s), stopping scan")
                break
            
            # Heartbeat: Update progress even if no new items found
            if progress_callback and (current_time - last_heartbeat_time >= heartbeat_interval):
                elapsed = current_time - start_time
                progress_callback(items_found, elapsed)
                last_heartbeat_time = current_time
                last_progress_time = current_time  # Reset progress time too
            
            # Filter out excluded directories before walking
            dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
            
            # Process files in current directory
            for filename in files:
                file_path = os.path.join(root, filename)
                
                if should_exclude(file_path):
                    skipped_count += 1
                    continue
                
                try:
                    if os.path.islink(file_path):
                        continue
                    
                    file_size = os.path.getsize(file_path)
                    
                    if file_size >= min_size_bytes:
                        items_found += 1
                        
                        # Call progress callback periodically when items are found
                        current_time = time.time()
                        if progress_callback and (current_time - last_progress_time >= progress_interval):
                            elapsed = current_time - start_time
                            progress_callback(items_found, elapsed)
                            last_progress_time = current_time
                            last_heartbeat_time = current_time  # Reset heartbeat too
                        
                        # Track largest files
                        largest_files.append({
                            'path': file_path,
                            'size_bytes': file_size,
                            'size_human': format_size(file_size),
                            'mtime': os.path.getmtime(file_path)
                        })
                        
                        # Track folder sizes (depth 2 from root)
                        rel_path = os.path.relpath(root, path)
                        if rel_path == '.':
                            # Files directly in root - use basename of path
                            folder_key = os.path.basename(path) if path != os.path.expanduser('~') else 'Home'
                            folder_actual_path = path
                        else:
                            parts = rel_path.split(os.sep)
                            # For depth 2, take first 2 parts or just first if only 1
                            if len(parts) >= 2:
                                folder_key = f"{parts[0]}/{parts[1]}"
                                # Get the actual path to the depth-2 folder
                                folder_actual_path = os.path.join(path, parts[0], parts[1])
                            elif len(parts) == 1:
                                folder_key = parts[0]
                                folder_actual_path = os.path.join(path, parts[0])
                            else:
                                folder_key = os.path.basename(root)
                                folder_actual_path = root
                        
                        folder_sizes[folder_key] += file_size
                        # Store the actual path for this folder key (use the first one we encounter)
                        if folder_key not in folder_paths:
                            folder_paths[folder_key] = folder_actual_path
                
                except (OSError, PermissionError):
                    skipped_count += 1
                    continue
        
        # Print final newline after progress updates
        if progress_callback:
            print()  # Newline after the last progress update
        print(f"→ found {items_found:,} items total")
        print("→ calculating sizes...")
        
        # Sort and limit largest files
        largest_files.sort(key=lambda x: x['size_bytes'], reverse=True)
        top_files = largest_files[:top_n]
        
        # Sort folders by size
        folder_list = [
            {
                'path': folder_paths.get(folder_key, folder_key),  # Use actual path if available
                'path_display': folder_key,  # Keep relative path for display
                'size_bytes': size,
                'size_human': format_size(size)
            }
            for folder_key, size in folder_sizes.items()
        ]
        folder_list.sort(key=lambda x: x['size_bytes'], reverse=True)
        top_folders = folder_list[:50]  # Top 50 folders
        
        # Now scan each top folder to get its files and subfolders
        print("→ scanning folder contents...")
        for folder in top_folders:
            folder_path = folder.get('path', '')
            # Ensure path is absolute
            if not os.path.isabs(folder_path):
                folder_path = os.path.join(path, folder_path.lstrip('/'))
                folder_path = os.path.normpath(folder_path)
            
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                files, subfolders = scan_folder_contents(folder_path, max_files=100, max_subfolders=10)
                folder['top_files'] = files
                folder['subfolders'] = subfolders
            else:
                folder['top_files'] = []
                folder['subfolders'] = []
        
        # Get volume info
        try:
            statvfs = os.statvfs(path)
            total_bytes = statvfs.f_frsize * statvfs.f_blocks
            free_bytes = statvfs.f_frsize * statvfs.f_bavail
            used_bytes = total_bytes - (statvfs.f_frsize * statvfs.f_bfree)
            used_percent = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0
            free_percent = (free_bytes / total_bytes * 100) if total_bytes > 0 else 0
        except (OSError, PermissionError):
            total_bytes = used_bytes = free_bytes = used_percent = free_percent = 0
        
        duration = time.time() - start_time
        
        # Calculate home folders total size (sum of all scanned folders)
        home_folders_total_bytes = sum(folder.get('size_bytes', 0) for folder in top_folders)
        
        # Calculate metrics for report card
        sum_top_10_folders = sum(folder.get('size_bytes', 0) for folder in top_folders[:10])
        sum_top_25_files = sum(file.get('size_bytes', 0) for file in top_files[:25])
        reclaimable_percent = (sum_top_25_files / used_bytes * 100) if used_bytes > 0 else 0
        
        return {
            'scan_type': 'storage',
            'volume': path,
            'top_folders': top_folders,
            'top_files': top_files,
            'volume_info': {
                'total_bytes': total_bytes,
                'used_bytes': used_bytes,
                'free_bytes': free_bytes,
                'used_percent': used_percent,
                'free_percent': free_percent,
                'total_human': format_size(total_bytes),
                'used_human': format_size(used_bytes),
                'free_human': format_size(free_bytes)
            },
            'home_folders_total_bytes': home_folders_total_bytes,
            'home_folders_total_human': format_size(home_folders_total_bytes),
            'metrics': {
                'sum_top_10_folders_bytes': sum_top_10_folders,
                'sum_top_10_folders_human': format_size(sum_top_10_folders),
                'sum_top_25_files_bytes': sum_top_25_files,
                'sum_top_25_files_human': format_size(sum_top_25_files),
                'reclaimable_percent': reclaimable_percent
            },
            'skipped_count': skipped_count,
            'duration_seconds': duration
        }
    
    except KeyboardInterrupt:
        print("\n→ scan interrupted by user")
        return None
    except Exception as e:
        print(f"→ error during scan: {e}")
        return None

