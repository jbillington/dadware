"""Storage scanner - finds large files and folders."""

import heapq
import itertools
import os
import time
from collections import defaultdict, deque
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
    
    # Decimal units, matching format_size() and macOS itself - `--min-size 1GB`
    # has to mean the same GB the report prints back, or the flag silently
    # filters at a different threshold than the user asked for.
    # Longest suffixes first, so 'B' can't match the tail of 'MB'.
    multipliers = [('TB', 1000**4), ('GB', 1000**3), ('MB', 1000**2), ('KB', 1000), ('B', 1)]

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
    # Sort by size, then path, so entries of identical size keep a stable,
    # traversal-order-independent order in the report.
    files.sort(key=lambda f: (-f.size_bytes, f.path))
    subfolders.sort(key=lambda f: (-f.size_bytes, f.path))

    return files[:max_files], subfolders[:max_subfolders]


def _folder_key_for(path: str, parts: List[str]) -> Tuple[str, str]:
    """Depth<=2 folder bucket for a directory given its path components
    relative to the scan root `path` (`parts == []` means the directory
    IS `path`). Mirrors the legacy inline logic exactly: only the first two
    relative components are ever used, however deep `parts` actually goes.

    Returns (folder_key, folder_actual_path).
    """
    if not parts:
        folder_key = os.path.basename(path) if path != os.path.expanduser('~') else 'Home'
        return folder_key, path
    elif len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}", os.path.join(path, parts[0], parts[1])
    else:
        return parts[0], os.path.join(path, parts[0])


# Historical max_depth used by get_folder_size()/scan_folder_contents() when
# sizing a top folder's immediate subfolders - preserved here so the folded
# single-pass subfolder totals cut off at the same relative depth.
_SUBFOLDER_MAX_DEPTH = 10

# Bound on how many of a folder's direct-child files are retained (per
# folder_key) while scanning, matching scan_folder_contents()'s max_files=100.
_MAX_FOLDER_TOP_FILES = 100

# How many folders the report breaks down.
_TOP_FOLDER_COUNT = 50


def _home_prefix_parts(root: str, home_path: Optional[str]) -> Optional[List[str]]:
    """`home_path`'s path components relative to `root`, or None if home is
    not strictly inside `root` (nothing to fold in that case - either home is
    the scan root itself, or it is on another volume entirely)."""
    if not home_path:
        return None
    root_norm = os.path.normpath(root)
    home_norm = os.path.normpath(home_path)
    if root_norm == home_norm:
        return None
    rel = os.path.relpath(home_norm, root_norm)
    if rel == os.curdir or rel == os.pardir or rel.startswith(os.pardir + os.sep):
        return None
    return rel.split(os.sep)


class _FolderBuckets:
    """The depth<=2 folder breakdown for one root, accumulated during the walk.

    A scan of `/` buckets everything under `/Users/<you>` into a single row,
    which loses the Downloads/Desktop/Documents breakdown that is the most
    useful part of the report. That used to be fixed by walking the home
    directory a second time from scratch - on a real Mac, 244,324 items
    re-read out of the 276,353 the first walk had already stat'd.

    So the walk keeps a second set of buckets rooted at the home directory
    instead. Same walk, same os.scandir(), same one stat() per file - only
    the bucket key differs.

    Per folder_key this holds:
      - the bucket's total size (files at or above the scan's min_size_bytes)
      - a bounded (<=100) min-heap of that folder's own *direct* child files
      - the set of that folder's immediate child directory names
      - each such child directory's recursive size (capped at the same
        max_depth=10 relative to the child that get_folder_size() used to
        enforce)
    which is exactly what scan_folder_contents()/get_folder_size() used to
    compute for each top folder in a separate walk - including their (legacy)
    quirk of ignoring min_size_bytes entirely, preserved here by tracking the
    per-folder structures unconditionally in add_file(), before count_file()
    applies the filter.
    """

    def __init__(self, root: str):
        self.root = root
        # Whether the walk ever reached this root. A root that was never
        # visited (denied, excluded, or on another volume) has no breakdown -
        # which is not the same as one whose files all fell below
        # min_size_bytes and left every bucket empty.
        self.entered = False
        self.folder_sizes = defaultdict(int)
        self.folder_paths: Dict[str, str] = {}   # folder_key -> actual path
        self.top_files_heap: Dict[str, list] = defaultdict(list)  # folder_key -> [(size, seq, FileInfo), ...]
        self.subfolder_names: Dict[str, set] = defaultdict(set)   # folder_key -> {child_name, ...}
        self.subfolder_sizes: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # Tie-breaker so heap items never compare FileInfo objects.
        self._heap_seq = itertools.count()

    def enter_dir(self, parts: List[str]) -> Tuple[str, str, List[Tuple[str, str]]]:
        """Register a directory and return the context its files need.

        Precomputes (once per directory, not per file) which of the up-to-3
        ancestor buckets (scan-root/Home, depth-1, depth-2) this directory
        rolls up into as a *subfolder*, and under what child name - mirroring
        get_folder_size()'s max_depth=10 cutoff.
        """
        self.entered = True
        own_key, own_actual = _folder_key_for(self.root, parts)
        depth_here = len(parts)
        subfolder_targets = []  # [(ancestor_key, child_name), ...]
        for d in (0, 1, 2):
            if depth_here > d and (depth_here - d - 1) <= _SUBFOLDER_MAX_DEPTH:
                ancestor_key, _ = _folder_key_for(self.root, parts[:d])
                subfolder_targets.append((ancestor_key, parts[d]))
            # Register this directory itself as a known immediate child (even
            # if it ends up contributing 0 bytes, e.g. empty or fully
            # excluded) - matches scan_folder_contents(), which lists every
            # immediate subdirectory via os.listdir() regardless of size.
            if depth_here == d + 1:
                ancestor_key, _ = _folder_key_for(self.root, parts[:d])
                self.subfolder_names[ancestor_key].add(parts[d])
        return own_key, own_actual, subfolder_targets

    def add_file(self, ctx, dir_path: str, entry_path: str, file_size: int) -> None:
        """Record a file against its folder's top_files and its ancestors'
        subfolder totals. Unfiltered - see the class docstring."""
        own_key, own_actual, subfolder_targets = ctx
        if dir_path == own_actual:
            heap = self.top_files_heap[own_key]
            candidate = (file_size, next(self._heap_seq),
                         FileInfo(path=entry_path, size_bytes=file_size))
            if len(heap) < _MAX_FOLDER_TOP_FILES:
                heapq.heappush(heap, candidate)
            elif file_size > heap[0][0]:
                heapq.heappushpop(heap, candidate)

        for ancestor_key, child_name in subfolder_targets:
            self.subfolder_sizes[ancestor_key][child_name] += file_size

    def count_file(self, ctx, file_size: int) -> None:
        """Add a file that passed the scan's min_size_bytes filter to its
        folder's reported total."""
        own_key, own_actual, _ = ctx
        self.folder_sizes[own_key] += file_size
        # Store the actual path for this folder key (use the first one we encounter)
        if own_key not in self.folder_paths:
            self.folder_paths[own_key] = own_actual

    def top_folders(self, limit: int = _TOP_FOLDER_COUNT) -> List[FolderInfo]:
        """The biggest `limit` folders, each with its top_files and
        subfolders filled in from what the walk already collected - no second
        disk pass."""
        folder_list: List[Tuple[str, FolderInfo]] = []
        for folder_key, size in self.folder_sizes.items():
            folder_path = self.folder_paths.get(folder_key, folder_key)
            folder_list.append((folder_key, FolderInfo(
                path=folder_path,       # Use actual path if available
                display=folder_key,     # Keep relative path for display
                size_bytes=size,
                # Mark Docker folders
                is_docker=is_docker_path(folder_path),
            )))
        folder_list.sort(key=lambda kv: (-kv[1].size_bytes, kv[1].path))

        for folder_key, folder in folder_list[:limit]:
            heap = self.top_files_heap.get(folder_key, [])
            folder.top_files = sorted((item[2] for item in heap),
                                      key=lambda f: (-f.size_bytes, f.path))
            names = self.subfolder_names.get(folder_key, ())
            sizes = self.subfolder_sizes.get(folder_key, {})
            subfolders = [
                FolderInfo(path=name, display=name, size_bytes=sizes.get(name, 0))
                for name in names
            ]
            subfolders.sort(key=lambda f: (-f.size_bytes, f.path))
            folder.subfolders = subfolders[:10]

        return [f for _, f in folder_list[:limit]]


def scan_storage(path: str, depth: int = 2, top_n: int = 500, min_size_bytes: int = 0,
                  timeout: Optional[float] = None,
                  progress_callback: Optional[Callable[[int, float], None]] = None,
                  home_path: Optional[str] = None) -> Optional[Dict]:
    """
    Scan storage and return structured data.

    Args:
        path: Path to scan
        depth: Maximum depth to scan (default: 2)
        top_n: Number of top files to return (default: 500)
        min_size_bytes: Minimum file size to include (default: 0)
        timeout: Maximum time to spend scanning in seconds (None = no timeout, user can Ctrl+C)
        progress_callback: Optional function(items_found, elapsed_time) called periodically
        home_path: Home directory to break down separately. When it sits
                   inside `path`, the same walk fills a second set of folder
                   buckets rooted there and returns them as
                   result['home_breakdown'] - so Downloads/Desktop/Documents
                   get their own rows without walking home a second time.
                   Ignored when home is the scan root or lives elsewhere.

    Implementation note: this walks the tree exactly once, using os.scandir()
    directly (an explicit stack, not recursion, so a pathological directory
    tree can't blow the Python recursion limit) instead of os.walk(). Each
    file is stat()'d at most once - that single os.stat_result is reused for
    sizing (get_file_size), sparse-file detection (is_sparse_file) and mtime.

    Folder bucketing (and the per-folder top_files/subfolders that used to
    need a second disk pass) lives in _FolderBuckets - see that class for
    what it accumulates and why. One walk fills one bucket set per root: the
    scan root always, plus the home directory when `home_path` sits inside it.

    Memory ceiling for the bookkeeping: O(distinct depth<=2 folders x 100)
    FileInfo records for top_files, plus O(distinct depth<=2 folders x
    distinct immediate child dirs) size counters for subfolders - it scales
    with directory count, not file count, and is bounded per folder
    regardless of how many files that folder recursively contains.
    """
    start_time = time.time()
    # Kept apart deliberately: excluded is our own policy (dotfiles, .app
    # bundles, caches, Mail, Messages...), denied is the filesystem refusing
    # us. Reporting the sum as "skipped due to permissions" told users with
    # full access that they had a permission problem.
    excluded_count = 0
    denied_count = 0

    # Track largest files
    largest_files: List[FileInfo] = []

    # Folder buckets for the scan root, and - when home lives inside it - a
    # second set rooted at home, filled by the same walk.
    buckets = _FolderBuckets(path)
    home_prefix = _home_prefix_parts(path, home_path)
    home_buckets = _FolderBuckets(home_path) if home_prefix is not None else None
    home_depth = len(home_prefix) if home_prefix is not None else 0

    print(f"Scanning {path}...")
    print("→ digging through the attic...")

    items_found = 0
    last_progress_time = start_time
    progress_interval = 2  # Call callback every 2 seconds (more frequent for slow machines)
    last_heartbeat_time = start_time
    heartbeat_interval = 5  # Force update every 5 seconds even if no new items

    try:
        # Explicit stack for iterative DFS: (dir_path, parts), where `parts`
        # is dir_path's path components relative to `path` (empty for `path`
        # itself). Order doesn't matter - results are sorted afterwards.
        stack = deque()
        stack.append((path, []))

        while stack:
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

            root, parts = stack.pop()
            ctx = buckets.enter_dir(parts)
            # The same directory, bucketed a second time relative to home.
            home_ctx = None
            if home_buckets is not None and parts[:home_depth] == home_prefix:
                home_ctx = home_buckets.enter_dir(parts[home_depth:])

            try:
                entries = os.scandir(root)
            except PermissionError:
                # A folder we were refused outright. Everything inside it is
                # invisible to the scan, so this is exactly the case the
                # report should be honest about rather than pass over in
                # silence, as os.walk()'s default onerror=None would.
                denied_count += 1
                continue
            except OSError:
                # Not permission: vanished mid-scan, bad mount, I/O error.
                continue

            with entries:
                for entry in entries:
                    entry_path = entry.path

                    try:
                        is_symlink = entry.is_symlink()
                    except OSError:
                        continue

                    if is_symlink:
                        # Skip symlinks outright (files and dirs alike) to
                        # avoid double-counting - matches the legacy
                        # os.path.islink() check on files, and os.walk()'s
                        # default followlinks=False (never descending into
                        # symlinked directories) for dirs.
                        continue

                    try:
                        is_dir = entry.is_dir()
                    except OSError:
                        continue

                    if is_dir:
                        if should_exclude(entry_path):
                            continue
                        stack.append((entry_path, parts + [entry.name]))
                        continue

                    # Not a dir, not a symlink: treat as a "file" for
                    # accounting purposes (matches os.walk()'s nondirs
                    # bucket, which is everything that isn't a directory -
                    # regular files as well as any special files whose
                    # size/stat still succeeds).
                    if should_exclude(entry_path):
                        excluded_count += 1
                        continue

                    try:
                        st = entry.stat()
                        file_size = get_file_size(entry_path, stat_result=st)
                    except PermissionError:
                        denied_count += 1
                        continue
                    except OSError:
                        # Not a permission problem - a broken symlink target,
                        # a file that vanished mid-scan, an I/O error. Counted
                        # with the exclusions rather than reported as denial.
                        excluded_count += 1
                        continue

                    buckets.add_file(ctx, root, entry_path, file_size)
                    if home_ctx is not None:
                        home_buckets.add_file(home_ctx, root, entry_path, file_size)

                    if file_size < min_size_bytes:
                        continue

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
                        path=entry_path,
                        size_bytes=file_size,
                        mtime=st.st_mtime,
                        # Mark Docker containers and sparse files
                        is_docker=is_docker_path(entry_path),
                        is_sparse=is_sparse_file(entry_path, stat_result=st),
                    )
                    largest_files.append(file_info)

                    buckets.count_file(ctx, file_size)
                    if home_ctx is not None:
                        home_buckets.count_file(home_ctx, file_size)

        # Print final newline after progress updates
        if progress_callback:
            print()  # Newline after the last progress update
        print(f"→ found {items_found:,} items total")
        print("→ calculating sizes...")

        # Sort and limit largest files
        largest_files.sort(key=lambda f: (-f.size_bytes, f.path))
        top_files: List[FileInfo] = largest_files[:top_n]

        # Sort folders by size and fill in each one's top_files/subfolders
        # from what the walk already collected - no second disk pass.
        print("→ scanning folder contents...")
        top_folders: List[FolderInfo] = buckets.top_folders()

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
            excluded_count=excluded_count,
            denied_count=denied_count,
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

        # The home-rooted breakdown, when this walk covered home. Kept out of
        # the scan proper: run_storage_scan() merges it into top_folders and
        # drops the key, so the manifest keeps its existing shape.
        if home_buckets is not None and home_buckets.entered:
            result['home_breakdown'] = {
                'top_folders': [f.to_dict() for f in home_buckets.top_folders()],
            }

        return result
    
    except KeyboardInterrupt:
        print("\n→ scan interrupted by user")
        return None
    except Exception as e:
        print(f"→ error during scan: {e}")
        return None

