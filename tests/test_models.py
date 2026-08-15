"""Tests for scanners/models.py - the typed data model used internally by
scanners/storage.py and scanners/grading.py.

Per the boundary rule (code review section 3), scan_storage() still returns
a plain dict with byte-identical structure to before this refactor - these
tests pin that shape, plus the round-tripping of each dataclass and the
"absent vs False"/"absent vs empty" quirks the legacy dict-building code
had (see scanners/models.py's module docstring for why they matter).
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scanners.models import FileInfo, FolderInfo, VolumeInfo, StorageScan
from scanners.storage import scan_storage

FIXTURES_DIR = Path(__file__).parent / 'fixtures'


@pytest.fixture
def home_scan_dir():
    """A throwaway directory under the real home dir.

    scan_storage() relies on utils.path_utils.should_exclude(), which treats
    any path whose *second* path segment is 'private'/'var'/'System'/etc as
    excluded - that rules out pytest's own tmp_path fixture on macOS (it
    resolves under /private/var/folders/...), so a real end-to-end scan needs
    a directory that lives under $HOME instead.
    """
    path = Path(tempfile.mkdtemp(prefix='dadware_test_models_', dir=os.path.expanduser('~')))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


class TestFileInfo:
    def test_to_dict_minimal(self):
        f = FileInfo(path='/a/b.txt', size_bytes=1024)
        d = f.to_dict()
        assert d == {'path': '/a/b.txt', 'size_bytes': 1024, 'size_human': '1.0 KB'}

    def test_mtime_absent_when_none(self):
        f = FileInfo(path='/a/b.txt', size_bytes=1024, mtime=None)
        assert 'mtime' not in f.to_dict()

    def test_mtime_present_when_set(self):
        f = FileInfo(path='/a/b.txt', size_bytes=1024, mtime=123.5)
        d = f.to_dict()
        assert d['mtime'] == 123.5

    def test_is_docker_absent_when_false(self):
        f = FileInfo(path='/a/b.txt', size_bytes=1024, is_docker=False)
        assert 'is_docker' not in f.to_dict()

    def test_is_docker_present_when_true(self):
        f = FileInfo(path='/a/b.txt', size_bytes=1024, is_docker=True)
        assert f.to_dict()['is_docker'] is True

    def test_is_sparse_absent_when_false(self):
        f = FileInfo(path='/a/b.txt', size_bytes=1024, is_sparse=False)
        assert 'is_sparse' not in f.to_dict()

    def test_is_sparse_present_when_true(self):
        f = FileInfo(path='/a/b.txt', size_bytes=1024, is_sparse=True)
        assert f.to_dict()['is_sparse'] is True

    def test_round_trip(self):
        original = FileInfo(path='/a/b.qcow2', size_bytes=999, mtime=42.0,
                             is_docker=True, is_sparse=True)
        rebuilt = FileInfo.from_dict(original.to_dict())
        assert rebuilt == original

    def test_round_trip_minimal(self):
        original = FileInfo(path='/a/b.txt', size_bytes=0)
        rebuilt = FileInfo.from_dict(original.to_dict())
        assert rebuilt == original

    def test_from_dict_ignores_size_human(self):
        # size_human is derived, not stored - from_dict should not choke on
        # (or trust) a stale/mismatched one.
        d = {'path': '/a/b.txt', 'size_bytes': 5, 'size_human': 'lies'}
        f = FileInfo.from_dict(d)
        assert f.to_dict()['size_human'] == '5.0 B'


class TestFolderInfo:
    def test_to_dict_minimal_omits_optional_keys(self):
        folder = FolderInfo(path='/a', display='a', size_bytes=2048)
        d = folder.to_dict()
        assert d == {'path': '/a', 'path_display': 'a', 'size_bytes': 2048, 'size_human': '2.0 KB'}
        assert 'is_docker' not in d
        assert 'top_files' not in d
        assert 'subfolders' not in d

    def test_is_docker_absent_when_false(self):
        folder = FolderInfo(path='/a', display='a', size_bytes=1, is_docker=False)
        assert 'is_docker' not in folder.to_dict()

    def test_is_docker_present_when_true(self):
        folder = FolderInfo(path='/a', display='a', size_bytes=1, is_docker=True)
        assert folder.to_dict()['is_docker'] is True

    def test_top_files_none_vs_empty_list(self):
        # None ("never scanned", e.g. a nested subfolder entry from
        # scan_folder_contents()) omits the key entirely; [] ("scanned,
        # found nothing", a top-level folder) keeps it as an empty list.
        never_scanned = FolderInfo(path='/a', display='a', size_bytes=1, top_files=None)
        scanned_empty = FolderInfo(path='/a', display='a', size_bytes=1, top_files=[])

        assert 'top_files' not in never_scanned.to_dict()
        assert scanned_empty.to_dict()['top_files'] == []

    def test_subfolders_none_vs_empty_list(self):
        never_scanned = FolderInfo(path='/a', display='a', size_bytes=1, subfolders=None)
        scanned_empty = FolderInfo(path='/a', display='a', size_bytes=1, subfolders=[])

        assert 'subfolders' not in never_scanned.to_dict()
        assert scanned_empty.to_dict()['subfolders'] == []

    def test_round_trip_with_nested_children(self):
        original = FolderInfo(
            path='/home/Downloads',
            display='Downloads',
            size_bytes=5000,
            is_docker=False,
            top_files=[FileInfo(path='/home/Downloads/x.zip', size_bytes=100)],
            subfolders=[FolderInfo(path='old', display='old', size_bytes=200)],
        )
        rebuilt = FolderInfo.from_dict(original.to_dict())
        assert rebuilt == original

    def test_round_trip_leaf_subfolder(self):
        # Mirrors what scan_folder_contents() actually produces for a
        # subfolder entry: no is_docker, no top_files/subfolders.
        original = FolderInfo(path='nested', display='nested', size_bytes=42)
        rebuilt = FolderInfo.from_dict(original.to_dict())
        assert rebuilt == original
        assert rebuilt.top_files is None
        assert rebuilt.subfolders is None


class TestVolumeInfo:
    def test_to_dict_computes_human_fields(self):
        v = VolumeInfo(total_bytes=1024**3, used_bytes=512 * 1024**2,
                        free_bytes=512 * 1024**2, used_percent=50.0, free_percent=50.0)
        d = v.to_dict()
        assert d['total_human'] == '1.0 GB'
        assert d['used_human'] == '512.0 MB'
        assert d['free_human'] == '512.0 MB'

    def test_round_trip(self):
        original = VolumeInfo(total_bytes=100, used_bytes=60, free_bytes=40,
                               used_percent=60.0, free_percent=40.0)
        rebuilt = VolumeInfo.from_dict(original.to_dict())
        assert rebuilt == original

    def test_default_is_all_zero(self):
        v = VolumeInfo()
        d = v.to_dict()
        assert d['total_bytes'] == 0
        assert d['total_human'] == '0.0 B'


class TestStorageScan:
    def test_to_dict_key_set_matches_legacy_shape(self):
        # scan_storage() also adds a 'metrics' key after calling .to_dict()
        # (see scanners/storage.py) - that's the only key StorageScan.to_dict()
        # itself doesn't produce.
        scan = StorageScan(
            scan_type='storage',
            volume='/Users/me',
            top_folders=[],
            top_files=[],
            volume_info=VolumeInfo(),
            home_folders_total_bytes=0,
            skipped_count=0,
            duration_seconds=0.0,
        )
        keys = set(scan.to_dict().keys())
        expected = {
            'scan_type', 'volume', 'top_folders', 'top_files', 'volume_info',
            'home_folders_total_bytes', 'home_folders_total_human',
            'skipped_count', 'duration_seconds',
        }
        assert keys == expected

    def test_round_trip(self):
        original = StorageScan(
            scan_type='storage',
            volume='/Users/me',
            top_folders=[FolderInfo(path='/Users/me/Downloads', display='Downloads',
                                     size_bytes=100, top_files=[], subfolders=[])],
            top_files=[FileInfo(path='/Users/me/big.bin', size_bytes=200, mtime=1.0)],
            volume_info=VolumeInfo(total_bytes=10, used_bytes=5, free_bytes=5,
                                    used_percent=50.0, free_percent=50.0),
            home_folders_total_bytes=100,
            skipped_count=3,
            duration_seconds=1.5,
        )
        rebuilt = StorageScan.from_dict(original.to_dict())
        assert rebuilt == original


class TestScanStorageDictShapeAgainstFixture:
    """scan_storage() must keep returning a plain dict whose key structure
    matches the committed fixture (tests/fixtures/storage_scan.json), which
    represents the real, pre-refactor shape. The fixture's scan_data has two
    extra keys - 'mac_libraries' and 'permission_status' - that yourdad.py
    (not scan_storage()) adds after the fact, so those are excluded here.
    """

    def test_top_level_keys(self, home_scan_dir):
        (home_scan_dir / 'file.bin').write_bytes(b'x' * 2048)

        result = scan_storage(str(home_scan_dir), top_n=10)

        fixture = json.loads((FIXTURES_DIR / 'storage_scan.json').read_text())
        fixture_scan_data_keys = set(fixture['scan_data'].keys()) - {'mac_libraries', 'permission_status'}

        assert set(result.keys()) == fixture_scan_data_keys

    def test_volume_info_keys(self, home_scan_dir):
        (home_scan_dir / 'file.bin').write_bytes(b'x' * 2048)

        result = scan_storage(str(home_scan_dir), top_n=10)

        fixture = json.loads((FIXTURES_DIR / 'storage_scan.json').read_text())
        assert set(result['volume_info'].keys()) == set(fixture['scan_data']['volume_info'].keys())

    def test_top_level_folder_and_file_keys_are_superset_compatible(self, home_scan_dir):
        # A folder with a plain file, and a docker/sparse file, so we exercise
        # both the "always present" keys and the "present only when true" ones.
        (home_scan_dir / 'sub').mkdir()
        (home_scan_dir / 'sub' / 'plain.bin').write_bytes(b'x' * 4096)
        # basename starting with 'docker' and ending in '.qcow2' trips both
        # is_docker_path() and is_sparse_file() (see utils/path_utils.py).
        (home_scan_dir / 'sub' / 'docker.qcow2').write_bytes(b'y' * 4096)

        result = scan_storage(str(home_scan_dir), top_n=10)

        assert len(result['top_folders']) >= 1
        folder = result['top_folders'][0]
        # Base keys always present on a scanned top-level folder.
        assert {'path', 'path_display', 'size_bytes', 'size_human', 'top_files', 'subfolders'} <= set(folder.keys())

        # The qcow2 file must carry is_docker/is_sparse; the plain file must not.
        by_path = {f['path']: f for f in result['top_files']}
        qcow2 = next(f for p, f in by_path.items() if p.endswith('docker.qcow2'))
        plain = next(f for p, f in by_path.items() if p.endswith('plain.bin'))

        assert qcow2['is_docker'] is True
        assert qcow2['is_sparse'] is True
        assert 'is_docker' not in plain
        assert 'is_sparse' not in plain
