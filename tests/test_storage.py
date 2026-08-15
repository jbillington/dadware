"""Tests for scanners/storage.py - parse_size and get_folder_size wiring."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import scanners.storage as storage_mod
from scanners.storage import parse_size


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
