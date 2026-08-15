"""Tests for scanners/storage.py - parse_size and get_folder_size wiring."""

import os
import shutil
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

import scanners.storage as storage_mod
from scanners.storage import parse_size, scan_storage


class TestParseSize:
    def test_bytes(self):
        assert parse_size('1024B') == 1024

    def test_kilobytes(self):
        assert parse_size('1KB') == 1024

    def test_megabytes(self):
        assert parse_size('500MB') == 500 * 1024**2

    def test_gigabytes(self):
        assert parse_size('1.5GB') == int(1.5 * 1024**3)

    def test_terabytes(self):
        assert parse_size('1TB') == 1024**4

    def test_case_insensitive(self):
        assert parse_size('500mb') == 500 * 1024**2
        assert parse_size('1gb') == 1024**3

    def test_with_whitespace(self):
        assert parse_size('  500MB  ') == 500 * 1024**2

    def test_plain_number_is_bytes(self):
        assert parse_size('1024') == 1024

    def test_none_returns_zero(self):
        assert parse_size(None) == 0

    def test_empty_string_returns_zero(self):
        assert parse_size('') == 0

    def test_invalid_string_returns_zero(self):
        assert parse_size('notanumber') == 0


class TestGetFolderSizeWiring:
    """
    scanners.storage.get_folder_size() is now a thin wrapper around the
    shared utils.path_utils.get_folder_size_generic(). These tests pin the
    wiring: storage's sizing function, its default depth, and how its
    depth-aware should_exclude(path, depth) is adapted into skip_fn(path, depth).
    """

    def test_wraps_shared_generic_with_storage_semantics(self, monkeypatch):
        captured = {}

        def fake_generic(folder_path, size_fn, skip_fn, min_size_bytes=0,
                          max_depth=2, current_depth=0, skip_hidden=False):
            captured.update(locals())
            return (123, 4)

        monkeypatch.setattr(storage_mod, 'get_folder_size_generic', fake_generic)
        result = storage_mod.get_folder_size('/some/path')

        assert result == (123, 4)
        assert captured['folder_path'] == '/some/path'
        assert captured['size_fn'] is storage_mod.get_file_size
        assert captured['max_depth'] == 2  # storage's default max_depth
        assert captured['skip_hidden'] is False

    def test_skip_fn_delegates_to_should_exclude_with_depth(self, monkeypatch):
        calls = []

        def fake_should_exclude(path, depth):
            calls.append((path, depth))
            return path == '/skip/me'

        monkeypatch.setattr(storage_mod, 'should_exclude', fake_should_exclude)

        captured = {}

        def fake_generic(folder_path, size_fn, skip_fn, **kwargs):
            captured['skip_fn'] = skip_fn
            return (0, 0)

        monkeypatch.setattr(storage_mod, 'get_folder_size_generic', fake_generic)
        storage_mod.get_folder_size('/root')

        skip_fn = captured['skip_fn']
        assert skip_fn('/keep/me', 3) is False
        assert skip_fn('/skip/me', 3) is True
        assert calls == [('/keep/me', 3), ('/skip/me', 3)]


@pytest.fixture
def home_scan_dir():
    """A throwaway directory under the real home dir.

    scan_storage() relies on utils.path_utils.should_exclude(), which treats
    any path whose *second* path segment is 'private'/'var'/'System'/etc as
    excluded - that rules out pytest's own tmp_path fixture on macOS (it
    resolves under /private/var/folders/...), so an end-to-end scan needs a
    directory that lives under $HOME instead.
    """
    path = Path(tempfile.mkdtemp(prefix='dadware_test_storage_', dir=os.path.expanduser('~')))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _make_file(path, size):
    path.write_bytes(b'x' * size)


class TestSingleWalkSymlinksSkipped:
    """The os.scandir()-based walk must skip symlinks outright (files and
    directories alike), exactly like the legacy os.path.islink() check /
    os.walk()'s default followlinks=False - never double-counting a
    symlinked file's target, and never descending into a symlinked dir."""

    def test_symlinked_file_not_counted(self, home_scan_dir):
        target = home_scan_dir / 'real.bin'
        _make_file(target, 5000)
        link = home_scan_dir / 'link.bin'
        os.symlink(target, link)

        result = scan_storage(str(home_scan_dir), top_n=100)

        paths = [f['path'] for f in result['top_files']]
        assert str(target) in paths
        assert str(link) not in paths
        # Only the real file counted - not double-counted via the symlink.
        assert len(paths) == 1

    def test_symlinked_dir_not_descended_into(self, home_scan_dir):
        real_dir = home_scan_dir / 'RealDir'
        real_dir.mkdir()
        _make_file(real_dir / 'inside.bin', 8000)

        link_dir = home_scan_dir / 'LinkDir'
        os.symlink(real_dir, link_dir, target_is_directory=True)

        result = scan_storage(str(home_scan_dir), top_n=100)

        paths = [f['path'] for f in result['top_files']]
        assert str(real_dir / 'inside.bin') in paths
        # Nothing should have been found "through" the symlinked directory.
        assert not any('LinkDir' in p for p in paths)
        folder_names = {f['path_display'] for f in result['top_folders']}
        assert 'LinkDir' not in folder_names


class TestSingleWalkExcludedDirsPruned:
    """Excluded directories must be pruned (never descended into), not just
    filtered from the results afterwards - matching the legacy
    `dirs[:] = [...]` pruning done during os.walk()."""

    def test_excluded_dir_contents_never_appear(self, home_scan_dir):
        # '.hidden' starts with '.' - utils.path_utils.should_exclude()
        # excludes any path whose basename starts with '.'.
        excluded = home_scan_dir / '.hidden'
        excluded.mkdir()
        _make_file(excluded / 'secret.bin', 50000)

        visible = home_scan_dir / 'Visible'
        visible.mkdir()
        _make_file(visible / 'plain.bin', 4000)

        result = scan_storage(str(home_scan_dir), top_n=100)

        paths = [f['path'] for f in result['top_files']]
        assert not any('.hidden' in p for p in paths)
        assert str(visible / 'plain.bin') in paths


class TestSingleWalkPerFolderCaps:
    """Per depth<=2 folder, top_files is capped at 100 (the largest ones)
    and subfolders is capped at 10 (the largest ones) - matching
    scan_folder_contents()'s max_files=100/max_subfolders=10 defaults, which
    the single-pass rewrite must reproduce without calling it."""

    def test_top_files_capped_at_100_largest(self, home_scan_dir):
        folder = home_scan_dir / 'Manyfiles'
        folder.mkdir()
        for i in range(120):
            _make_file(folder / f'f{i:03d}.bin', 1000 + i)  # sizes 1000..1119

        result = scan_storage(str(home_scan_dir), top_n=500)

        entry = next(f for f in result['top_folders'] if f['path_display'] == 'Manyfiles')
        assert len(entry['top_files']) == 100
        sizes = [f['size_bytes'] for f in entry['top_files']]
        assert sizes == sorted(sizes, reverse=True)
        # The 100 largest of 1000..1119 are 1020..1119.
        assert min(sizes) == 1020
        assert max(sizes) == 1119

    def test_subfolders_capped_at_10_largest(self, home_scan_dir):
        folder = home_scan_dir / 'Manysubs'
        folder.mkdir()
        # Manysubs needs at least one *direct* file, or it never gets its
        # own folder_key entry at all (files under Manysubs/subNN roll into
        # the separate "Manysubs/subNN" depth-2 bucket instead) - matches
        # the legacy depth-2 bucketing exactly, not a rewrite artifact.
        _make_file(folder / 'direct.bin', 10)
        for i in range(15):
            sub = folder / f'sub{i:02d}'
            sub.mkdir()
            _make_file(sub / 'data.bin', 1000 * (i + 1))  # sub14 largest

        result = scan_storage(str(home_scan_dir), top_n=500)

        entry = next(f for f in result['top_folders'] if f['path_display'] == 'Manysubs')
        assert len(entry['subfolders']) == 10
        sizes = [sf['size_bytes'] for sf in entry['subfolders']]
        assert sizes == sorted(sizes, reverse=True)
        names = {sf['path'] for sf in entry['subfolders']}
        # The 10 largest subfolders are sub05..sub14 (sizes 6000..15000).
        assert names == {f'sub{i:02d}' for i in range(5, 15)}
        # Subfolder entries use the bare name for both path and path_display.
        for sf in entry['subfolders']:
            assert sf['path'] == sf['path_display']


class TestSingleWalkDeepTreeRecursionSafety:
    """The rewrite uses an explicit stack instead of Python recursion, so a
    pathologically deep directory tree must not raise RecursionError.

    A real directory tree can't actually be made deeper than Python's
    default recursion limit (1000) on disk - macOS's PATH_MAX (1024 bytes)
    caps single-character-named nesting at a few hundred levels well before
    that. So instead this lowers sys.recursionlimit() for the duration of
    the test and builds a tree deeper than *that* - if the walk recursed in
    Python per directory level, it would blow the artificially low limit;
    with an explicit stack, the limit is irrelevant to traversal depth.
    """

    def test_deep_tree_does_not_blow_recursion_limit(self, home_scan_dir):
        original_limit = sys.getrecursionlimit()
        low_limit = 80
        tree_depth = 150  # comfortably deeper than low_limit, well under PATH_MAX

        current = home_scan_dir
        for i in range(tree_depth):
            current = current / 'd'
        current.mkdir(parents=True)
        _make_file(current / 'bottom.bin', 42)

        sys.setrecursionlimit(low_limit)
        try:
            # Must not raise RecursionError even with a tiny Python
            # recursion limit, since the walk itself never recurses.
            result = scan_storage(str(home_scan_dir), top_n=10)
        finally:
            sys.setrecursionlimit(original_limit)

        assert result is not None
        paths = [f['path'] for f in result['top_files']]
        assert str(current / 'bottom.bin') in paths
