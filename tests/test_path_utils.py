"""Tests for utils/path_utils.py"""

import sys
import os
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.path_utils import (
    is_docker_path, is_sparse_file, should_exclude, should_skip_path,
    get_file_size, get_folder_size_generic,
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
