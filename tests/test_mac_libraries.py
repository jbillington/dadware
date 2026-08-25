"""Tests for scanners/mac_libraries.py - get_folder_size wiring and scan budgeting."""

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


class TestTimeBudgetReporting:
    """The Partial Scan banner reads interrupted_scans, so it has to name
    everything that was skipped - not just the scanner whose turn it was when
    the budget ran out."""

    def _stub_scanners(self, monkeypatch, slow_first=True):
        """Replace the real scanners with fakes; the first one burns the budget."""
        def make(name, size, slow=False):
            def scan():
                if slow:
                    # Push elapsed past any budget the test sets.
                    mac_libraries_mod.time.sleep(0.05)
                return {'type': name, 'total_size_bytes': size,
                        'total_size_human': f'{size}', 'count': 1}
            return scan

        monkeypatch.setattr(mac_libraries_mod, 'scan_photos_library', make('photos', 10, slow=slow_first))
        monkeypatch.setattr(mac_libraries_mod, 'scan_music_library', make('music', 20))
        monkeypatch.setattr(mac_libraries_mod, 'scan_messages', make('messages', 30))
        monkeypatch.setattr(mac_libraries_mod, 'scan_mail', make('mail', 40))
        monkeypatch.setattr(mac_libraries_mod, 'scan_time_machine_backups', make('time_machine', 50))
        monkeypatch.setattr(mac_libraries_mod, 'scan_creative_libraries', make('creative', 60))

    def test_every_skipped_library_is_named_not_just_the_first(self, monkeypatch):
        self._stub_scanners(monkeypatch)
        result = mac_libraries_mod.scan_all_mac_libraries(timeout_seconds=0.01)

        assert result['scan_status'] == 'partial'
        skipped = [name for name in
                   ('photos', 'music', 'messages', 'mail', 'time_machine', 'creative')
                   if result[name].get('status') == 'skipped']
        # The banner list and the actual skipped set must agree. Before this
        # fix, interrupted_scans held one name while several were skipped.
        assert sorted(result['interrupted_scans']) == sorted(skipped)
        assert len(skipped) > 1

    def test_a_complete_scan_reports_no_interrupted_list(self, monkeypatch):
        self._stub_scanners(monkeypatch, slow_first=False)
        result = mac_libraries_mod.scan_all_mac_libraries(timeout_seconds=30)

        assert result['scan_status'] == 'complete'
        assert 'interrupted_scans' not in result

    def test_default_budget_is_generous_enough_for_six_scanners(self):
        import inspect
        default = inspect.signature(
            mac_libraries_mod.scan_all_mac_libraries).parameters['timeout_seconds'].default
        # 10s could not finish six scanners on a real Mac, which left the
        # library grade computed from whatever fitted.
        assert default >= 60

