"""Tests for utils/path_utils.py"""

import sys
import os
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import utils.path_utils as path_utils_mod
from utils.path_utils import (
    is_docker_path, is_sparse_file, should_exclude, should_skip_path,
    get_file_size, get_folder_size_generic, find_folder, basenames_in,
    get_device_id, get_scan_device_ids, is_on_scan_volume,
)


class TestIsDockerPath:
    def test_docker_directory(self):
        assert is_docker_path('/Users/me/Library/Containers/com.docker.docker') is True

    def test_docker_containers(self):
        assert is_docker_path('/var/lib/docker/containers/abc123') is True

    def test_docker_volumes(self):
        assert is_docker_path('/var/lib/docker/volumes/myapp') is True

    def test_docker_qcow2(self):
        assert is_docker_path('/Users/me/.docker/Docker.qcow2') is True

    def test_docker_raw(self):
        assert is_docker_path('/Users/me/Library/Containers/com.docker.docker/Data/vms/0/Docker.raw') is True

    def test_docker_raw_pattern_match(self):
        # Regression: the 'Docker.raw' pattern in DOCKER_PATH_PATTERNS used to
        # be spelled with a capital D, but is compared against a lowercased
        # path, so it could never match. This path avoids every other pattern
        # (no 'com.docker.', no '/docker/', no basename ending in a virtual
        # disk extension) so it only passes via the 'docker.raw' pattern.
        assert is_docker_path('/Users/me/VMs/Docker.raw/disk.img') is True

    def test_normal_path(self):
        assert is_docker_path('/Users/me/Documents/project') is False

    def test_docker_in_name_only(self):
        assert is_docker_path('/Users/me/Documents/my-docker-notes.txt') is False


class TestShouldExclude:
    def test_system_directories(self):
        assert should_exclude('/System/Library/Fonts') is True
        assert should_exclude('/Library/Application Support') is True
        assert should_exclude('/usr/local/bin') is True
        assert should_exclude('/bin/sh') is True
        assert should_exclude('/sbin/mount') is True
        assert should_exclude('/private/var/log') is True

    def test_applications(self):
        assert should_exclude('/Applications') is True

    def test_dot_app(self):
        assert should_exclude('/Users/me/Something.app') is True
        assert should_exclude('/Users/me/.app/subfolder') is True

    def test_photoslibrary(self):
        assert should_exclude('/Users/me/Pictures/Photos Library.photoslibrary') is True

    def test_caches(self):
        assert should_exclude('/Users/me/Library/Caches/com.apple.Safari') is True

    def test_tmp(self):
        assert should_exclude('/tmp/somefile') is True
        assert should_exclude('/Users/me/tmp') is True

    def test_hidden_files(self):
        assert should_exclude('/Users/me/.hidden_folder') is True

    def test_library_mail(self):
        assert should_exclude('/Users/me/Library/Mail/V9') is True

    def test_library_messages(self):
        assert should_exclude('/Users/me/Library/Messages') is True

    def test_normal_user_folder(self):
        assert should_exclude('/Users/me/Documents') is False
        assert should_exclude('/Users/me/Downloads') is False
        assert should_exclude('/Users/me/Movies') is False


class TestShouldSkipPath:
    def test_mobile_documents(self):
        assert should_skip_path('/Users/me/Library/Mobile Documents/com~apple~CloudDocs') is True

    def test_cloud_storage(self):
        assert should_skip_path('/Users/me/Library/CloudStorage/Dropbox') is True

    def test_containers(self):
        assert should_skip_path('/Users/me/Library/Containers/com.apple.mail') is True

    def test_group_containers(self):
        assert should_skip_path('/Users/me/Library/Group Containers/group.com.apple') is True

    def test_normal_path(self):
        assert should_skip_path('/Users/me/Documents/project') is False


class TestGetFolderSizeGeneric:
    """
    Behavioral tests for the shared utils.path_utils.get_folder_size_generic(),
    which backs both scanners.storage.get_folder_size() (depth-aware skip_fn,
    like should_exclude(path, depth)) and scanners.mac_libraries.get_folder_size()
    (non-depth-aware skip_fn, like should_skip_path(path)). Real should_exclude()
    is not used here because it excludes anything under a 'private' path
    segment, which would falsely exclude pytest's tmp_path on macOS.
    """

    def _make_tree(self, base):
        (base / 'a.txt').write_bytes(b'x' * 100)
        (base / 'b.txt').write_bytes(b'x' * 200)
        sub = base / 'sub'
        sub.mkdir()
        (sub / 'c.txt').write_bytes(b'x' * 300)
        deep = sub / 'deep'
        deep.mkdir()
        (deep / 'd.txt').write_bytes(b'x' * 400)
        hidden = base / '.hidden'
        hidden.mkdir()
        (hidden / 'e.txt').write_bytes(b'x' * 500)

    def test_sums_files_recursively_with_depth_aware_skip_fn(self, tmp_path):
        # Mirrors scanners.storage's should_exclude(path, depth) signature.
        self._make_tree(tmp_path)
        size, count = get_folder_size_generic(
            str(tmp_path), size_fn=os.path.getsize,
            skip_fn=lambda path, depth: False, max_depth=10,
        )
        assert size == 100 + 200 + 300 + 400 + 500
        assert count == 5

    def test_sums_files_with_non_depth_aware_skip_fn(self, tmp_path):
        # Mirrors scanners.mac_libraries's should_skip_path(path) signature,
        # adapted via a lambda that ignores the depth argument (as the real
        # scanners.mac_libraries.get_folder_size() wrapper does).
        self._make_tree(tmp_path)
        size, count = get_folder_size_generic(
            str(tmp_path), size_fn=os.path.getsize,
            skip_fn=lambda path, depth: should_skip_path(path), max_depth=10,
        )
        assert size == 100 + 200 + 300 + 400 + 500
        assert count == 5

    def test_respects_max_depth(self, tmp_path):
        self._make_tree(tmp_path)
        # max_depth=1: tmp_path is depth 0; sub/ and .hidden/ are depth 1
        # (descended into); sub/deep/ is depth 2 (not descended into), so
        # d.txt is excluded but a.txt, b.txt, c.txt, and e.txt are counted.
        size, count = get_folder_size_generic(
            str(tmp_path), size_fn=os.path.getsize,
            skip_fn=lambda path, depth: False, max_depth=1,
        )
        assert count == 4
        assert size == 100 + 200 + 300 + 500

    def test_skip_hidden_flag(self, tmp_path):
        self._make_tree(tmp_path)
        size, count = get_folder_size_generic(
            str(tmp_path), size_fn=os.path.getsize,
            skip_fn=lambda path, depth: False, max_depth=10, skip_hidden=True,
        )
        assert count == 4  # .hidden/e.txt excluded

    def test_min_size_bytes_filter(self, tmp_path):
        self._make_tree(tmp_path)
        size, count = get_folder_size_generic(
            str(tmp_path), size_fn=os.path.getsize,
            skip_fn=lambda path, depth: False, max_depth=10, min_size_bytes=250,
        )
        assert count == 3  # c.txt(300), d.txt(400), e.txt(500)
        assert size == 300 + 400 + 500

    def test_skips_symlinks(self, tmp_path):
        self._make_tree(tmp_path)
        link = tmp_path / 'link.txt'
        try:
            link.symlink_to(tmp_path / 'a.txt')
        except OSError:
            pytest.skip("symlinks not supported in this environment")
        size, count = get_folder_size_generic(
            str(tmp_path), size_fn=os.path.getsize,
            skip_fn=lambda path, depth: False, max_depth=10,
        )
        assert count == 5  # symlink not double-counted

    def test_nonexistent_folder_returns_zero(self, tmp_path):
        missing = tmp_path / 'does-not-exist'
        assert get_folder_size_generic(
            str(missing), size_fn=os.path.getsize, skip_fn=lambda path, depth: False,
        ) == (0, 0)

    def test_skip_fn_excludes_folder_entirely(self, tmp_path):
        self._make_tree(tmp_path)
        assert get_folder_size_generic(
            str(tmp_path), size_fn=os.path.getsize, skip_fn=lambda path, depth: True,
        ) == (0, 0)


class TestIsSparseFileWithStatResult:
    def test_matches_no_stat_result_for_normal_file(self, tmp_path):
        f = tmp_path / 'normal.txt'
        f.write_bytes(b'x' * 1024)
        stat_result = os.stat(str(f))
        assert is_sparse_file(str(f)) == is_sparse_file(str(f), stat_result=stat_result) is False

    def test_matches_no_stat_result_for_extension_match(self, tmp_path):
        f = tmp_path / 'disk.qcow2'
        f.write_bytes(b'x' * 10)
        stat_result = os.stat(str(f))
        assert is_sparse_file(str(f)) == is_sparse_file(str(f), stat_result=stat_result) is True

    def test_ratio_based_detection_matches_with_and_without_stat(self, tmp_path):
        f = tmp_path / 'thin.img'  # no matching extension - only the ratio check applies
        with open(f, 'wb') as fh:
            fh.truncate(50 * 1024 * 1024)  # 50MB logical size, ~0 actual disk blocks
        stat_result = os.stat(str(f))
        actual_size = stat_result.st_blocks * 512
        if not (stat_result.st_size > 0 and actual_size > 0 and stat_result.st_size / actual_size > 10):
            pytest.skip("filesystem did not produce a sparse file for this test")
        assert is_sparse_file(str(f)) is True
        assert is_sparse_file(str(f), stat_result=stat_result) is True

    def test_stat_result_avoids_extra_os_stat_call(self, tmp_path, monkeypatch):
        f = tmp_path / 'normal.txt'
        f.write_bytes(b'x' * 1024)
        stat_result = os.stat(str(f))

        def boom(*args, **kwargs):
            raise AssertionError("os.stat should not be called when stat_result is provided")

        monkeypatch.setattr(os, 'stat', boom)
        assert is_sparse_file(str(f), stat_result=stat_result) is False


class TestGetFileSizeWithStatResult:
    def test_normal_file_matches_with_and_without_stat_result(self, tmp_path):
        f = tmp_path / 'plain.dat'
        f.write_bytes(b'x' * 4096)
        stat_result = os.stat(str(f))
        assert get_file_size(str(f)) == get_file_size(str(f), stat_result=stat_result) == 4096

    def test_docker_path_matches_with_and_without_stat_result(self, tmp_path):
        f = tmp_path / 'Docker.qcow2'
        f.write_bytes(b'x' * 4096)
        stat_result = os.stat(str(f))
        expected = stat_result.st_blocks * 512
        assert get_file_size(str(f)) == get_file_size(str(f), stat_result=stat_result) == expected

    def test_stat_result_avoids_extra_os_stat_call(self, tmp_path, monkeypatch):
        f = tmp_path / 'plain.dat'
        f.write_bytes(b'x' * 4096)
        stat_result = os.stat(str(f))

        def boom(*args, **kwargs):
            raise AssertionError("os.stat should not be called when stat_result is provided")

        monkeypatch.setattr(os, 'stat', boom)
        assert get_file_size(str(f), stat_result=stat_result) == 4096


class TestFindFolder:
    def test_matches_exact_basename(self):
        top_folders = [
            {'path': '/Users/me/Downloads', 'size_bytes': 100},
            {'path': '/Users/me/Desktop', 'size_bytes': 200},
        ]
        result = find_folder(top_folders, 'Downloads')
        assert result is not None
        assert result['path'] == '/Users/me/Downloads'

    def test_does_not_match_substring_containing_junk_path(self):
        # Regression: 'Downloads' in path used to match any path merely
        # containing the word, e.g. an archive folder named
        # 'Old-Downloads-Archive'. The real Downloads folder must win, and
        # a similarly-named junk folder must never be picked when the real
        # one is absent.
        top_folders = [
            {'path': '/Users/me/Downloads', 'size_bytes': 111},
            {'path': '/Users/me/Backups/Old-Downloads-Archive', 'size_bytes': 999},
        ]
        result = find_folder(top_folders, 'Downloads')
        assert result['path'] == '/Users/me/Downloads'
        assert result['size_bytes'] == 111

    def test_junk_only_path_does_not_match(self):
        top_folders = [
            {'path': '/Users/me/Backups/Old-Downloads-Archive', 'size_bytes': 999},
        ]
        assert find_folder(top_folders, 'Downloads') is None

    def test_documents_old_does_not_match_documents(self):
        top_folders = [
            {'path': '/Users/me/Documents-old', 'size_bytes': 500},
        ]
        assert find_folder(top_folders, 'Documents') is None

    def test_returns_none_when_absent(self):
        top_folders = [
            {'path': '/Users/me/Desktop', 'size_bytes': 200},
        ]
        assert find_folder(top_folders, 'Downloads') is None

    def test_empty_list_returns_none(self):
        assert find_folder([], 'Downloads') is None

    def test_falls_back_to_path_display_when_path_missing(self):
        top_folders = [
            {'path_display': 'Users/me/Downloads', 'size_bytes': 50},
        ]
        result = find_folder(top_folders, 'Downloads')
        assert result is not None
        assert result['size_bytes'] == 50

    def test_prefers_path_over_path_display(self):
        top_folders = [
            {'path': '/Users/me/Downloads', 'path_display': 'Users/me/SomethingElse', 'size_bytes': 50},
        ]
        result = find_folder(top_folders, 'Downloads')
        assert result is not None

    def test_case_insensitive_fallback(self):
        top_folders = [
            {'path': '/Volumes/case-sensitive/downloads', 'size_bytes': 77},
        ]
        result = find_folder(top_folders, 'Downloads')
        assert result is not None
        assert result['size_bytes'] == 77

    def test_exact_case_preferred_over_case_insensitive(self):
        top_folders = [
            {'path': '/Users/me/downloads', 'size_bytes': 1},
            {'path': '/Users/me/Downloads', 'size_bytes': 2},
        ]
        result = find_folder(top_folders, 'Downloads')
        assert result['size_bytes'] == 2

    def test_missing_path_keys_are_skipped(self):
        top_folders = [
            {'size_bytes': 100},
            {'path': '/Users/me/Downloads', 'size_bytes': 200},
        ]
        result = find_folder(top_folders, 'Downloads')
        assert result['size_bytes'] == 200


class TestBasenamesIn:
    def test_partitions_home_folders_by_basename(self):
        top_folders = [
            {'path': '/Users/me/Downloads', 'size_bytes': 1},
            {'path': '/Users/me/Desktop', 'size_bytes': 2},
            {'path': '/Users/me/Backups/Old-Downloads-Archive', 'size_bytes': 999},
            {'path': '/Users/me/Documents-old', 'size_bytes': 888},
        ]
        names = ['Downloads', 'Desktop', 'Documents']
        result = basenames_in(top_folders, names)
        paths = [f['path'] for f in result]
        assert paths == ['/Users/me/Downloads', '/Users/me/Desktop']

    def test_no_matches_returns_empty_list(self):
        top_folders = [{'path': '/Users/me/Projects', 'size_bytes': 1}]
        assert basenames_in(top_folders, ['Downloads', 'Desktop']) == []

    def test_case_insensitive_fallback(self):
        top_folders = [{'path': '/Volumes/x/downloads', 'size_bytes': 5}]
        result = basenames_in(top_folders, ['Downloads'])
        assert len(result) == 1


class TestGetDeviceId:
    """The device id is what keeps a scan on one filesystem - a scan of `/`
    must not walk into an attached backup drive under /Volumes."""

    def test_returns_the_filesystem_device_of_a_path(self, tmp_path):
        assert get_device_id(str(tmp_path)) == os.stat(tmp_path).st_dev

    def test_a_file_and_its_directory_share_a_device(self, tmp_path):
        target = tmp_path / 'file.bin'
        target.write_bytes(b'x')
        assert get_device_id(str(target)) == get_device_id(str(tmp_path))

    def test_missing_path_returns_none(self, tmp_path):
        assert get_device_id(str(tmp_path / 'nope')) is None


class TestGetScanDeviceIds:
    """What counts as "the scan root's filesystem".

    The macOS startup disk is two volumes - a sealed system volume at / and a
    writable data volume at /System/Volumes/Data, joined by firmlinks - so
    /Users has a different st_dev from /. Treating only the root's own device
    as in-bounds would skip the entire home directory.
    """

    def _devices(self, monkeypatch, mapping, default):
        """Report a fake st_dev per path, so the system/data pair can be
        simulated on any OS."""
        def fake_stat(path):
            class _Stat:
                st_dev = mapping.get(str(path), default)
            return _Stat()
        monkeypatch.setattr(path_utils_mod.os, 'stat', fake_stat)

    def test_includes_the_data_volume_when_scanning_the_system_volume(self, monkeypatch):
        self._devices(monkeypatch, {'/': 1, '/System/Volumes/Data': 2}, default=99)
        assert get_scan_device_ids('/') == {1, 2}

    def test_includes_the_system_volume_when_scanning_from_the_data_side(self, monkeypatch):
        self._devices(monkeypatch,
                      {'/': 1, '/System/Volumes/Data': 2, '/Users/me': 2},
                      default=99)
        assert get_scan_device_ids('/Users/me') == {1, 2}

    def test_an_external_drive_gets_only_its_own_device(self, monkeypatch):
        """`--volume /Volumes/BACKUP` must scan that drive and nothing else -
        the startup disk is not folded in from the other direction."""
        self._devices(monkeypatch,
                      {'/': 1, '/System/Volumes/Data': 2, '/Volumes/BACKUP': 7},
                      default=99)
        assert get_scan_device_ids('/Volumes/BACKUP') == {7}

    def test_unstattable_root_returns_none(self, tmp_path):
        assert get_scan_device_ids(str(tmp_path / 'nope')) is None

    def test_real_root_includes_the_real_home(self):
        """On the machine running the tests, whatever they are, home has to
        be inside a scan of the root that contains it - this is the case the
        firmlink handling exists for."""
        home = os.path.expanduser('~')
        devices = get_scan_device_ids('/')
        assert devices is not None
        assert get_device_id(home) in devices


class TestIsOnScanVolume:
    """Whether the disk being scanned is the one the home folder lives on -
    the difference between a report about a Mac and a report about a thumb
    drive."""

    def _devices(self, monkeypatch, mapping, default):
        def fake_stat(path):
            class _Stat:
                st_dev = mapping.get(str(path), default)
            return _Stat()
        monkeypatch.setattr(path_utils_mod.os, 'stat', fake_stat)

    def test_home_is_on_the_startup_disk(self, monkeypatch):
        self._devices(monkeypatch,
                      {'/': 1, '/System/Volumes/Data': 2, '/Users/me': 2},
                      default=99)
        assert is_on_scan_volume('/', '/Users/me') is True

    def test_home_is_not_on_a_thumb_drive(self, monkeypatch):
        self._devices(monkeypatch,
                      {'/': 1, '/System/Volumes/Data': 2,
                       '/Volumes/THUMB': 7, '/Users/me': 2},
                      default=99)
        assert is_on_scan_volume('/Volumes/THUMB', '/Users/me') is False

    def test_a_folder_inside_home_still_counts_as_home_s_disk(self, monkeypatch):
        """`--volume ~/Downloads` is a subtree of the startup disk, so the
        report keeps its libraries and caches - the scope rule is about which
        disk, not which folder."""
        self._devices(monkeypatch,
                      {'/': 1, '/System/Volumes/Data': 2,
                       '/Users/me/Downloads': 2, '/Users/me': 2},
                      default=99)
        assert is_on_scan_volume('/Users/me/Downloads', '/Users/me') is True

    def test_unreadable_device_falls_back_to_the_full_report(self, tmp_path):
        """Can't tell means give the report people expect, rather than
        silently stripping most of it."""
        assert is_on_scan_volume(str(tmp_path / 'nope'), str(tmp_path)) is True
        assert is_on_scan_volume(str(tmp_path), str(tmp_path / 'nope')) is True
