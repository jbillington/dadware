"""Tests for scanners/mac_libraries.py - get_folder_size wiring."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import scanners.mac_libraries as mac_libraries_mod


class TestGetFolderSizeWiring:
    """
    scanners.mac_libraries.get_folder_size() is now a thin wrapper around
    the shared utils.path_utils.get_folder_size_generic(). These tests pin
    the wiring: the library scanner's disk-based sizing function, its
    default depth, its skip_hidden passthrough, and how its non-depth-aware
    should_skip_path(path) is adapted into skip_fn(path, depth).
    """

    def test_wraps_shared_generic_with_library_semantics(self, monkeypatch):
        captured = {}

        def fake_generic(folder_path, size_fn, skip_fn, min_size_bytes=0,
                          max_depth=2, current_depth=0, skip_hidden=False):
            captured.update(locals())
            return (999, 7)

        monkeypatch.setattr(mac_libraries_mod, 'get_folder_size_generic', fake_generic)
        result = mac_libraries_mod.get_folder_size('/lib/path', skip_hidden=True)

        assert result == (999, 7)
        assert captured['folder_path'] == '/lib/path'
        assert captured['size_fn'] is mac_libraries_mod.get_file_size_disk
        assert captured['max_depth'] == 10  # mac_libraries' default max_depth
        assert captured['skip_hidden'] is True

    def test_skip_fn_delegates_to_should_skip_path_ignoring_depth(self, monkeypatch):
        calls = []

        def fake_should_skip_path(path):
            calls.append(path)
            return path == '/skip/me'

        monkeypatch.setattr(mac_libraries_mod, 'should_skip_path', fake_should_skip_path)

        captured = {}

        def fake_generic(folder_path, size_fn, skip_fn, **kwargs):
            captured['skip_fn'] = skip_fn
            return (0, 0)

        monkeypatch.setattr(mac_libraries_mod, 'get_folder_size_generic', fake_generic)
        mac_libraries_mod.get_folder_size('/root')

        skip_fn = captured['skip_fn']
        assert skip_fn('/keep/me', 5) is False
        assert skip_fn('/skip/me', 0) is True
        # should_skip_path takes only a path - depth must not be forwarded to it.
        assert calls == ['/keep/me', '/skip/me']
