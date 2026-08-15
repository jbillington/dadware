"""Tests for scanners/grading.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanners.grading import (
    score_to_letter,
    grade_free_space,
    grade_home_folders_clutter,
    grade_home_folders_ratio,
    grade_library_size,
    calculate_storage_metrics,
    calculate_composite_storage_grade,
)
from scanners.models import FileInfo, FolderInfo, StorageScan, VolumeInfo

GB = 1024**3


class TestScoreToLetter:
    def test_a(self):
        assert score_to_letter(90) == 'A'
        assert score_to_letter(100) == 'A'

    def test_b(self):
        assert score_to_letter(80) == 'B'
        assert score_to_letter(89) == 'B'

    def test_c(self):
        assert score_to_letter(70) == 'C'
        assert score_to_letter(79) == 'C'

    def test_d(self):
        assert score_to_letter(60) == 'D'
        assert score_to_letter(69) == 'D'

    def test_f(self):
        assert score_to_letter(59) == 'F'
        assert score_to_letter(0) == 'F'


class TestGradeFreeSpace:
    def test_plenty_free_is_a(self):
        result = grade_free_space(50)
        assert result['letter'] == 'A'
        assert result['score'] == 100

    def test_40_percent_is_a(self):
        result = grade_free_space(40)
        assert result['letter'] == 'A'

    def test_30_percent_is_b(self):
        result = grade_free_space(30)
        assert result['letter'] == 'B'

    def test_22_percent_is_c(self):
        result = grade_free_space(22)
        assert result['letter'] == 'C'

    def test_15_percent_is_d(self):
        result = grade_free_space(15)
        assert result['letter'] == 'D'

    def test_8_percent_is_f(self):
        result = grade_free_space(8)
        assert result['letter'] == 'F'

    def test_zero_free(self):
        result = grade_free_space(0)
        assert result['letter'] == 'F'
        assert result['score'] == 0

    def test_score_clamped_to_100(self):
        result = grade_free_space(99)
        assert result['score'] <= 100


class TestGradeHomeFoldersClutter:
    def test_clean_folders(self):
        folders = [
            {'path': '/Users/me/Downloads', 'size_bytes': 1 * GB},
            {'path': '/Users/me/Desktop', 'size_bytes': 500 * 1024**2},
        ]
        result = grade_home_folders_clutter(folders)
        assert result['letter'] == 'A'
        assert result['problem_count'] == 0

    def test_large_downloads(self):
        folders = [
            {'path': '/Users/me/Downloads', 'size_bytes': 7 * GB},
        ]
        result = grade_home_folders_clutter(folders)
        assert result['problem_count'] == 1
        assert result['letter'] == 'B'

    def test_huge_downloads(self):
        folders = [
            {'path': '/Users/me/Downloads', 'size_bytes': 15 * GB},
        ]
        result = grade_home_folders_clutter(folders)
        assert result['problem_count'] == 2
        assert result['letter'] == 'D'

    def test_large_desktop(self):
        folders = [
            {'path': '/Users/me/Desktop', 'size_bytes': 8 * GB},
        ]
        result = grade_home_folders_clutter(folders)
        assert result['problem_count'] == 1

    def test_both_cluttered(self):
        folders = [
            {'path': '/Users/me/Downloads', 'size_bytes': 15 * GB},
            {'path': '/Users/me/Desktop', 'size_bytes': 8 * GB},
        ]
        result = grade_home_folders_clutter(folders)
        assert result['problem_count'] == 3
        assert result['letter'] == 'F'

    def test_empty_folders_list(self):
        result = grade_home_folders_clutter([])
        assert result['letter'] == 'A'

    def test_junk_path_does_not_count_as_downloads(self):
        # Regression: a folder whose path merely contains the word
        # 'Downloads' (e.g. an archive folder) must not be mistaken for the
        # real Downloads folder and inflate its reported size / grade.
        folders = [
            {'path': '/Users/me/Downloads', 'size_bytes': 1 * GB},
            {'path': '/Users/me/Backups/Old-Downloads-Archive', 'size_bytes': 20 * GB},
        ]
        result = grade_home_folders_clutter(folders)
        assert result['downloads_size'] == 1 * GB
        assert result['problem_count'] == 0
        assert result['letter'] == 'A'

    def test_junk_path_does_not_count_as_desktop(self):
        folders = [
            {'path': '/Users/me/Documents-old', 'size_bytes': 20 * GB},
        ]
        result = grade_home_folders_clutter(folders)
        assert result['desktop_size'] == 0
        assert result['downloads_size'] == 0
        assert result['problem_count'] == 0


class TestGradeHomeFoldersRatio:
    def test_low_ratio_is_a(self):
        result = grade_home_folders_ratio(20 * GB, 100 * GB)
        assert result['letter'] == 'A'

    def test_high_ratio_is_f(self):
        result = grade_home_folders_ratio(90 * GB, 100 * GB)
        assert result['letter'] == 'F'

    def test_zero_total(self):
        result = grade_home_folders_ratio(0, 0)
        assert result['letter'] == 'N/A'


class TestGradeLibrarySize:
    def test_small_photos_is_a(self):
        result = grade_library_size(10 * GB, 'photos', 500 * GB)
        assert result['letter'] == 'A'

    def test_huge_photos(self):
        result = grade_library_size(350 * GB, 'photos', 500 * GB)
        assert result['letter'] in ['D', 'F']

    def test_small_messages_is_a(self):
        result = grade_library_size(1 * GB, 'messages', 500 * GB)
        assert result['letter'] == 'A'

    def test_large_messages(self):
        result = grade_library_size(25 * GB, 'messages', 500 * GB)
        assert result['letter'] in ['D', 'F']

    def test_library_dominates_disk_gets_penalized(self):
        # Library is 60% of total used space
        small_disk = grade_library_size(30 * GB, 'music', 50 * GB)
        large_disk = grade_library_size(30 * GB, 'music', 500 * GB)
        assert small_disk['score'] < large_disk['score']

    def test_unknown_library_type_uses_music_thresholds(self):
        result = grade_library_size(10 * GB, 'unknown_type', 500 * GB)
        music_result = grade_library_size(10 * GB, 'music', 500 * GB)
        assert result['score'] == music_result['score']


class TestCalculateStorageMetrics:
    def test_basic_metrics(self):
        scan_data = {
            'top_folders': [
                {'size_bytes': 10 * GB},
                {'size_bytes': 5 * GB},
            ],
            'top_files': [
                {'size_bytes': 2 * GB},
                {'size_bytes': 1 * GB},
            ],
            'volume_info': {'used_bytes': 100 * GB},
        }
        result = calculate_storage_metrics(scan_data)
        assert result['sum_top_10_folders_bytes'] == 15 * GB
        assert result['sum_top_25_files_bytes'] == 3 * GB
        assert result['reclaimable_percent'] == 3.0

    def test_empty_scan_data(self):
        result = calculate_storage_metrics({})
        assert result['sum_top_10_folders_bytes'] == 0
        assert result['reclaimable_percent'] == 0

    def test_accepts_typed_storage_scan_and_matches_dict_equivalent(self):
        # calculate_storage_metrics() is called internally by scan_storage()
        # with a scanners.models.StorageScan (typed objects), and externally
        # by renderers/html.py with the plain dict scan_storage() returns.
        # Both must produce identical numbers for equivalent data.
        scan = StorageScan(
            top_folders=[
                FolderInfo(path='/a', display='a', size_bytes=10 * GB),
                FolderInfo(path='/b', display='b', size_bytes=5 * GB),
            ],
            top_files=[
                FileInfo(path='/a/x', size_bytes=2 * GB),
                FileInfo(path='/a/y', size_bytes=1 * GB),
            ],
            volume_info=VolumeInfo(used_bytes=100 * GB),
        )
        typed_result = calculate_storage_metrics(scan)

        dict_equivalent = {
            'top_folders': [{'size_bytes': 10 * GB}, {'size_bytes': 5 * GB}],
            'top_files': [{'size_bytes': 2 * GB}, {'size_bytes': 1 * GB}],
            'volume_info': {'used_bytes': 100 * GB},
        }
        dict_result = calculate_storage_metrics(dict_equivalent)

        assert typed_result == dict_result
        assert typed_result['sum_top_10_folders_bytes'] == 15 * GB
        assert typed_result['sum_top_25_files_bytes'] == 3 * GB
        assert typed_result['reclaimable_percent'] == 3.0


class TestGradeHomeFoldersClutterAcceptsTypedObjects:
    """grade_home_folders_clutter() is only ever called (by renderers/html.py)
    with the plain dicts scan_storage() returns, but per the boundary-rule
    task it should also accept scanners.models.FolderInfo objects without
    special-casing at call sites - it normalizes internally before handing
    folders to utils.path_utils.find_folder() (which only understands dicts).
    """

    def test_typed_folders_match_dict_equivalent(self):
        typed_folders = [
            FolderInfo(path='/Users/me/Downloads', display='Downloads', size_bytes=7 * GB),
        ]
        dict_folders = [
            {'path': '/Users/me/Downloads', 'size_bytes': 7 * GB},
        ]
        assert grade_home_folders_clutter(typed_folders) == grade_home_folders_clutter(dict_folders)

    def test_typed_folders_no_problems(self):
        typed_folders = [
            FolderInfo(path='/Users/me/Downloads', display='Downloads', size_bytes=1 * GB),
            FolderInfo(path='/Users/me/Desktop', display='Desktop', size_bytes=500 * 1024**2),
        ]
        result = grade_home_folders_clutter(typed_folders)
        assert result['letter'] == 'A'
        assert result['problem_count'] == 0


class TestCalculateCompositeGrade:
    def test_all_perfect(self):
        grades = {
            'free_space': {'score': 100},
            'clutter': {'score': 100},
        }
        result = calculate_composite_storage_grade(grades)
        assert result['letter'] == 'A'

    def test_all_failing(self):
        grades = {
            'free_space': {'score': 20},
            'clutter': {'score': 20},
        }
        result = calculate_composite_storage_grade(grades)
        assert result['letter'] == 'F'

    def test_mixed_grades_average(self):
        grades = {
            'free_space': {'score': 100},
            'clutter': {'score': 0},
        }
        result = calculate_composite_storage_grade(grades)
        # Average of 100 and 0 = 50
        assert result['score'] == 50.0

    def test_custom_weights(self):
        grades = {
            'free_space': {'score': 100},
            'clutter': {'score': 0},
        }
        weights = {'free_space': 0.9, 'clutter': 0.1}
        result = calculate_composite_storage_grade(grades, weights)
        assert result['score'] == 90.0
