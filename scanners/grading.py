"""Grading system for storage report card."""

from typing import Any, Dict, List, Optional

from utils.formatters import format_size
from utils.path_utils import find_folder


def _field(obj: Any, key: str, default: Any = None) -> Any:
    """Read `key` from `obj`, whether `obj` is a plain dict (the shape every
    grading function is called with today, via yourdad.py/personality/ and
    renderers/html.py) or one of the scanners.models dataclasses (the shape
    scanners.storage now builds internally before converting to a dict on
    the way out). Lets grading functions accept either without callers
    caring which one they have.
    """
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _as_dict(obj: Any) -> Any:
    """Return a plain-dict view of `obj` if it exposes `to_dict()` (a
    scanners.models dataclass), otherwise return `obj` unchanged (already a
    dict, or something dict-like). Used where a helper we can't touch
    (utils.path_utils.find_folder) needs real dicts.
    """
    if isinstance(obj, dict):
        return obj
    to_dict = getattr(obj, 'to_dict', None)
    if callable(to_dict):
        return to_dict()
    return obj


def score_to_letter(score: float) -> str:
    """Convert numeric score (0-100) to letter grade."""
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'


def grade_free_space(free_percent: float) -> Dict[str, Any]:
    """
    Grade based on free space percentage.

    A: >40% free
    B: 25-40% free
    C: 15-25% free
    D: 10-15% free
    F: <10% free
    """
    if free_percent >= 40:
        score = 100
    elif free_percent >= 25:
        score = 80 + (free_percent - 25) * (20 / 15)  # 80-100
    elif free_percent >= 15:
        score = 60 + (free_percent - 15) * 2  # 60-80
    elif free_percent >= 10:
        score = 40 + (free_percent - 10) * 4  # 40-60
    else:
        score = free_percent * 4  # 0-40
    
    return {
        'letter': score_to_letter(score),
        'score': max(0, min(100, score)),
        'max': 100
    }


def grade_home_folders_clutter(top_folders: List[Any]) -> Dict[str, Any]:
    """
    Grade home folders based on clutter in Downloads, Desktop, etc.

    A: No problem folders, well organized
    B: Some clutter but manageable
    C: Downloads/Desktop getting full
    D: Multiple problem areas
    F: Critical clutter issues

    `top_folders` may be a list of plain dicts or scanners.models.FolderInfo
    objects - utils.path_utils.find_folder() only understands dicts, so
    entries are normalized before being handed to it.
    """
    downloads_size = 0
    desktop_size = 0
    problem_count = 0

    normalized_folders = [_as_dict(f) for f in top_folders]

    downloads_folder = find_folder(normalized_folders, 'Downloads')
    if downloads_folder is not None:
        downloads_size = downloads_folder.get('size_bytes', 0)
        if downloads_size > 10 * 1024**3:  # >10GB
            problem_count += 2
        elif downloads_size > 5 * 1024**3:  # >5GB
            problem_count += 1

    desktop_folder = find_folder(normalized_folders, 'Desktop')
    if desktop_folder is not None:
        desktop_size = desktop_folder.get('size_bytes', 0)
        if desktop_size > 5 * 1024**3:  # >5GB
            problem_count += 1
    
    # Calculate score based on problem count
    if problem_count == 0:
        score = 100
    elif problem_count == 1:
        score = 80
    elif problem_count == 2:
        score = 60
    elif problem_count == 3:
        score = 40
    else:
        score = 20
    
    return {
        'letter': score_to_letter(score),
        'score': score,
        'max': 100,
        'downloads_size': downloads_size,
        'desktop_size': desktop_size,
        'problem_count': problem_count
    }


def grade_home_folders_ratio(home_folders_bytes: float, total_used_bytes: float) -> Dict[str, Any]:
    """
    Grade based on ratio of home folder usage to total used storage.
    
    Lower ratio (home folders are small relative to total) = better grade.
    
    A: <30% of used space is in home folders
    B: 30-50%
    C: 50-70%
    D: 70-85%
    F: >85%
    """
    if total_used_bytes == 0:
        return {
            'letter': 'N/A',
            'score': 0,
            'max': 100
        }
    
    ratio_percent = (home_folders_bytes / total_used_bytes) * 100
    
    if ratio_percent < 30:
        score = 100
    elif ratio_percent < 50:
        score = 80 + (50 - ratio_percent) * 1  # 80-100
    elif ratio_percent < 70:
        score = 60 + (70 - ratio_percent) * 1  # 60-80
    elif ratio_percent < 85:
        score = 40 + (85 - ratio_percent) * 1.33  # 40-60
    else:
        score = max(0, 40 - (ratio_percent - 85) * 2.67)  # 0-40
    
    return {
        'letter': score_to_letter(score),
        'score': max(0, min(100, score)),
        'max': 100,
        'ratio_percent': ratio_percent
    }


def grade_library_size(library_size_bytes: float, library_type: str, total_used_bytes: float) -> Dict[str, Any]:
    """
    Grade individual Mac app library size.
    
    Different thresholds for different library types.
    Also considers library size relative to total used space.
    """
    library_size_gb = library_size_bytes / (1024**3)
    library_percent = (library_size_bytes / total_used_bytes * 100) if total_used_bytes > 0 else 0
    
    # Thresholds by library type (in GB)
    thresholds = {
        'photos': {'A': 50, 'B': 100, 'C': 200, 'D': 300},  # Photos can be large
        'music': {'A': 20, 'B': 50, 'C': 100, 'D': 200},
        'messages': {'A': 5, 'B': 10, 'C': 20, 'D': 50},
        'mail': {'A': 5, 'B': 10, 'C': 20, 'D': 50},
        'time_machine': {'A': 100, 'B': 200, 'C': 500, 'D': 1000},  # Time Machine can be huge
        'creative': {'A': 20, 'B': 50, 'C': 100, 'D': 200}
    }
    
    thresh = thresholds.get(library_type, thresholds['music'])
    
    # Grade based on absolute size
    if library_size_gb < thresh['A']:
        size_score = 100
    elif library_size_gb < thresh['B']:
        size_score = 80 + (thresh['B'] - library_size_gb) / (thresh['B'] - thresh['A']) * 20
    elif library_size_gb < thresh['C']:
        size_score = 60 + (thresh['C'] - library_size_gb) / (thresh['C'] - thresh['B']) * 20
    elif library_size_gb < thresh['D']:
        size_score = 40 + (thresh['D'] - library_size_gb) / (thresh['D'] - thresh['C']) * 20
    else:
        size_score = max(0, 40 - (library_size_gb - thresh['D']) / 10)
    
    # Penalize if library is a large percentage of total used space
    if library_percent > 50:
        size_score -= 20
    elif library_percent > 30:
        size_score -= 10
    elif library_percent > 20:
        size_score -= 5
    
    return {
        'letter': score_to_letter(size_score),
        'score': max(0, min(100, size_score)),
        'max': 100,
        'size_gb': library_size_gb,
        'percent_of_used': library_percent
    }


def calculate_storage_metrics(scan_data: Any) -> Dict[str, Any]:
    """
    Calculate key metrics for storage report card.

    Returns:
    - sum_top_10_folders: Sum of top 10 largest folders
    - sum_top_25_files: Sum of top 25 largest files
    - reclaimable_percent: Percentage of used space that could be freed by deleting top 25 files

    `scan_data` may be a plain dict (the shape yourdad.py/personality/ and
    renderers/html.py always use, since scan_storage() returns a dict) or a
    scanners.models.StorageScan (the shape scan_storage() builds internally
    before converting to a dict). Its `top_folders`/`top_files` entries may
    likewise be dicts or FolderInfo/FileInfo objects - `_field()` reads
    either uniformly, so no conversion is needed either way.
    """
    top_folders = _field(scan_data, 'top_folders', []) or []
    top_files = _field(scan_data, 'top_files', []) or []
    volume_info = _field(scan_data, 'volume_info', {}) or {}
    used_bytes = _field(volume_info, 'used_bytes', 0)

    # Sum of top 10 folders
    top_10_folders = top_folders[:10]
    sum_top_10_folders = sum(_field(folder, 'size_bytes', 0) for folder in top_10_folders)

    # Sum of top 25 files
    top_25_files = top_files[:25]
    sum_top_25_files = sum(_field(file, 'size_bytes', 0) for file in top_25_files)

    # Reclaimable percentage
    reclaimable_percent = (sum_top_25_files / used_bytes * 100) if used_bytes > 0 else 0

    return {
        'sum_top_10_folders_bytes': sum_top_10_folders,
        'sum_top_10_folders_human': format_size(sum_top_10_folders),
        'sum_top_25_files_bytes': sum_top_25_files,
        'sum_top_25_files_human': format_size(sum_top_25_files),
        'reclaimable_percent': reclaimable_percent
    }


def calculate_composite_storage_grade(grades: Dict[str, Dict[str, Any]],
                                       weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Calculate composite storage grade from individual component grades.

    Args:
        grades: Dict of grade components with 'score' key
        weights: Dict of weights for each component (default: equal weighting)

    Returns:
        Composite grade with letter and score
    """
    if weights is None:
        # Default equal weighting
        weights = {key: 1.0 for key in grades.keys()}
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
    
    weighted_score = sum(
        grades[key].get('score', 0) * weights.get(key, 0)
        for key in grades.keys()
    )
    
    return {
        'letter': score_to_letter(weighted_score),
        'score': weighted_score,
        'max': 100
    }

