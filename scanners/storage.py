"""Storage scanner - finds large files and folders."""

import os
import time
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple

from utils.path_utils import (
    is_docker_path, is_sparse_file, should_exclude, get_file_size,
    get_folder_size_generic,
)
from utils.volumes import get_volume_info

# scanners.grading has no dependency on scanners.storage, so this is safe as
# a top-level import (no circular import).
from scanners.grading import calculate_storage_metrics
from scanners.models import FileInfo, FolderInfo, StorageScan, VolumeInfo


def parse_size(size_str: Optional[str]) -> int:
    """Parse size string like '500MB' or '1.5GB' into bytes."""
    if not size_str:
        return 0
    
    size_str = size_str.upper().strip()
    
    # Extract number and unit (check longest suffixes first to avoid 'B' matching 'MB')
    multipliers = [('TB', 1024**4), ('GB', 1024**3), ('MB', 1024**2), ('KB', 1024), ('B', 1)]

    for unit, mult in multipliers:
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


def get_folder_size(folder_path: str, min_size_bytes: int = 0, max_depth: int = 2,
                     current_depth: int = 0) -> Tuple[int, int]:
    """Calculate folder size recursively, respecting depth limit.

    Thin wrapper around the shared utils.path_utils.get_folder_size_generic(),
    using the storage scanner's sizing (get_file_size) and exclusion
    (should_exclude, which is depth-aware) rules.
    """
    return get_folder_size_generic(
        folder_path,
        size_fn=get_file_size,
        skip_fn=lambda path, depth: should_exclude(path, depth),
        min_size_bytes=min_size_bytes,
        max_depth=max_depth,
        current_depth=current_depth,
    )


def scan_folder_contents(folder_path: str, max_files: int = 100,
                          max_subfolders: int = 10) -> Tuple[List[FileInfo], List[FolderInfo]]:
    """Scan a specific folder and return its files and subfolders.

    Returns typed FileInfo/FolderInfo objects (not dicts) - these are leaf
    entries: files here never carry mtime/is_docker/is_sparse and subfolders
    never carry is_docker/top_files/subfolders, matching what the legacy
    dict-building code produced (see scanners/models.py docstring).
    """
    files: List[FileInfo] = []
    subfolders: List[FolderInfo] = []

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
                    # Calculate subfolder size - use deeper depth to get full recursive size
                    # This matches what the main scan sees, so sizes are consistent
                    size, _ = get_folder_size(item_path, min_size_bytes=0, max_depth=10, current_depth=0)
                    subfolders.append(FolderInfo(path=item, display=item, size_bytes=size))
                elif os.path.isfile(item_path):
                    try:
                        size = get_file_size(item_path)
                        files.append(FileInfo(path=item_path, size_bytes=size))
                    except (OSError, PermissionError):
                        pass
            except (OSError, PermissionError):
                pass
    except (OSError, PermissionError):
        pass

    # Sort and limit
    files.sort(key=lambda f: f.size_bytes, reverse=True)
    subfolders.sort(key=lambda f: f.size_bytes, reverse=True)

    return files[:max_files], subfolders[:max_subfolders]


def scan_storage(path: str, depth: int = 2, top_n: int = 500, min_size_bytes: int = 0,
                  timeout: Optional[float] = None,
                  progress_callback: Optional[Callable[[int, float], None]] = None) -> Optional[Dict]:
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
    largest_files: List[FileInfo] = []

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
                    
                    file_size = get_file_size(file_path)
                    
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
                        file_info = FileInfo(
                            path=file_path,
                            size_bytes=file_size,
                            mtime=os.path.getmtime(file_path),
                            # Mark Docker containers and sparse files
                            is_docker=is_docker_path(file_path),
                            is_sparse=is_sparse_file(file_path),
                        )
                        largest_files.append(file_info)
                        
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
        largest_files.sort(key=lambda f: f.size_bytes, reverse=True)
        top_files: List[FileInfo] = largest_files[:top_n]

        # Sort folders by size
        folder_list: List[FolderInfo] = []
        for folder_key, size in folder_sizes.items():
            folder_path = folder_paths.get(folder_key, folder_key)
            folder_list.append(FolderInfo(
                path=folder_path,       # Use actual path if available
                display=folder_key,     # Keep relative path for display
                size_bytes=size,
                # Mark Docker folders
                is_docker=is_docker_path(folder_path),
            ))
        folder_list.sort(key=lambda f: f.size_bytes, reverse=True)
        top_folders: List[FolderInfo] = folder_list[:50]  # Top 50 folders

        # Now scan each top folder to get its files and subfolders
        print("→ scanning folder contents...")
        for folder in top_folders:
            folder_path = folder.path
            # Ensure path is absolute
            if not os.path.isabs(folder_path):
                folder_path = os.path.join(path, folder_path.lstrip('/'))
                folder_path = os.path.normpath(folder_path)

            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                files, subfolders = scan_folder_contents(folder_path, max_files=100, max_subfolders=10)
                folder.top_files = files
                folder.subfolders = subfolders
            else:
                folder.top_files = []
                folder.subfolders = []

        # Get volume info (shared with utils.volumes.list_volumes()/select_volume())
        vol_info = get_volume_info(path)
        if vol_info:
            total_bytes = vol_info['total_bytes']
            used_bytes = vol_info['used_bytes']
            free_bytes = vol_info['free_bytes']
            used_percent = vol_info['used_percent']
            free_percent = (free_bytes / total_bytes * 100) if total_bytes > 0 else 0
            volume_info = VolumeInfo(
                total_bytes=total_bytes,
                used_bytes=used_bytes,
                free_bytes=free_bytes,
                used_percent=used_percent,
                free_percent=free_percent,
            )
        else:
            volume_info = VolumeInfo()

        duration = time.time() - start_time

        # Calculate home folders total size (sum of all scanned folders)
        home_folders_total_bytes = sum(folder.size_bytes for folder in top_folders)

        scan = StorageScan(
            scan_type='storage',
            volume=path,
            top_folders=top_folders,
            top_files=top_files,
            volume_info=volume_info,
            home_folders_total_bytes=home_folders_total_bytes,
            skipped_count=skipped_count,
            duration_seconds=duration,
        )

        # Build the plain dict that renderers/manifests consume - the typed
        # objects above stay internal to the scanner/grading layers.
        result = scan.to_dict()

        # Compute report-card metrics from the typed scan - single source of
        # truth shared with grading.calculate_composite_storage_grade().
        # calculate_storage_metrics() accepts either the StorageScan object
        # or a plain dict, so this works whether or not `scan` is typed.
        result['metrics'] = calculate_storage_metrics(scan)

        return result
    
    except KeyboardInterrupt:
        print("\n→ scan interrupted by user")
        return None
    except Exception as e:
        print(f"→ error during scan: {e}")
        return None

