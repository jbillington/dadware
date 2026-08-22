"""Tests for scanners/hidden_storage.py - the app cache scanner (Phase 1a).

Conventions follow tests/test_path_utils.py: `unit` marker, real temp
directories for the filesystem behavior, and mocked subprocess for anything
that shells out. `du` is mocked everywhere it matters so these tests pass on
non-Mac CI too, with one integration-style test that exercises the Python
walk fallback against real files.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import scanners.hidden_storage as hidden_storage
from scanners.hidden_storage import (
    build_app_name_index,
    friendly_app_name,
    looks_like_bundle_id,
    measure_folder,
    read_bundle_id,
    scan_app_caches,
)

MB = 1024 * 1024
GB = 1024 * MB


def make_cache_tree(home, layout):
    """Build `Library/Caches` and `Library/Logs` under `home`.

    `layout` maps a relative root ('Library/Caches') to a dict of folder
    name -> list of (filename, size_bytes). A folder mapped to None is
    created empty.
    """
    for relative_root, folders in layout.items():
        root = Path(home) / relative_root
        root.mkdir(parents=True, exist_ok=True)
        for folder_name, files in folders.items():
            folder = root / folder_name
            folder.mkdir(exist_ok=True)
            for filename, size in (files or []):
                (folder / filename).write_bytes(b'x' * size)


def fake_du(sizes_by_path, stderr='', returncode=0):
    """A `subprocess.run` stand-in that answers `du -skx` from a dict.

    Keyed by path; unknown paths report 0 KB, which is what `du` does for an
    empty folder.
    """
    def _run(cmd, **kwargs):
        path = cmd[-1]
        size_kb = sizes_by_path.get(path, 0)
        return subprocess.CompletedProcess(
            cmd, returncode, stdout=f'{size_kb}\t{path}\n', stderr=stderr
        )
    return _run


@pytest.mark.unit
class TestFriendlyAppName:
    """Bundle ID -> the name the user actually recognizes."""

    def test_installed_app_wins_over_everything(self):
        index = {'com.spotify.client': 'Spotify Premium Edition'}
        # The installed name beats the built-in table, because it's the name
        # in the user's own Dock.
        assert friendly_app_name('com.spotify.client', index) == 'Spotify Premium Edition'

    def test_known_bundle_id_maps_to_mainstream_name(self):
        assert friendly_app_name('com.spotify.client') == 'Spotify'
        assert friendly_app_name('com.microsoft.VSCode') == 'Visual Studio Code'
        assert friendly_app_name('us.zoom.xos') == 'Zoom'

    def test_known_lookup_is_case_insensitive(self):
        assert friendly_app_name('COM.Spotify.Client') == 'Spotify'
        assert friendly_app_name('com.spotify.client', {'com.spotify.client': 'Spotify'}) == 'Spotify'

    def test_unknown_bundle_id_falls_back_to_heuristic(self):
        assert friendly_app_name('com.acme.widgetron') == 'Widgetron'
        # The generic trailing component names a kind of program, not the
        # program - drop it and use what's left.
        assert friendly_app_name('com.obscureco.client') == 'Obscureco'
        assert friendly_app_name('org.videolan.helper') == 'Videolan'

    def test_heuristic_keeps_existing_capitalization(self):
        assert friendly_app_name('com.googlecode.iTerm2') == 'iTerm2'
        assert friendly_app_name('com.acme.MyApp2') == 'MyApp2'

    def test_heuristic_never_strips_the_last_component(self):
        # Every component is generic; something has to survive.
        assert friendly_app_name('com.app.client') == 'App'

    def test_non_bundle_names_pass_through_unchanged(self):
        for name in ('Firefox', 'Google', 'CloudKit', 'Homebrew', 'My Cache Folder'):
            assert friendly_app_name(name) == name

    def test_two_component_names_without_dns_prefix_pass_through(self):
        # 'notion.id' reads worse mangled than left alone.
        assert friendly_app_name('storekit.cache') == 'storekit.cache'

    def test_empty_name_is_returned_unchanged(self):
        assert friendly_app_name('') == ''

    def test_looks_like_bundle_id(self):
        assert looks_like_bundle_id('com.spotify.client') is True
        assert looks_like_bundle_id('org.mozilla.firefox') is True
        assert looks_like_bundle_id('com.spotify') is True  # known DNS prefix
        assert looks_like_bundle_id('Firefox') is False
        assert looks_like_bundle_id('storekit.cache') is False
        assert looks_like_bundle_id('com..client') is False
        assert looks_like_bundle_id('.hidden.thing.here') is False
        assert looks_like_bundle_id('com.my app.client') is False
        assert looks_like_bundle_id('') is False


@pytest.mark.unit
class TestAppNameIndex:
    """Reading bundle IDs out of the apps installed on this Mac."""

    def _make_app(self, apps_dir, app_name, bundle_id):
        contents = Path(apps_dir) / f'{app_name}.app' / 'Contents'
        contents.mkdir(parents=True)
        import plistlib
        with open(contents / 'Info.plist', 'wb') as handle:
            plistlib.dump({'CFBundleIdentifier': bundle_id}, handle)
        return contents.parent

    def test_index_maps_bundle_ids_to_app_names(self, tmp_path):
        apps = tmp_path / 'Applications'
        apps.mkdir()
        self._make_app(apps, 'Spotify', 'com.spotify.client')
        self._make_app(apps, 'Cool Editor', 'com.acme.editor')

        index = build_app_name_index([str(apps)])

        assert index == {
            'com.spotify.client': 'Spotify',
            'com.acme.editor': 'Cool Editor',
        }

    def test_index_skips_non_apps_and_unreadable_plists(self, tmp_path):
        apps = tmp_path / 'Applications'
        apps.mkdir()
        self._make_app(apps, 'Real', 'com.acme.real')
        (apps / 'NotAnApp').mkdir()
        (apps / 'Broken.app' / 'Contents').mkdir(parents=True)
        (apps / 'Broken.app' / 'Contents' / 'Info.plist').write_text('not a plist')

        assert build_app_name_index([str(apps)]) == {'com.acme.real': 'Real'}

    def test_index_skips_missing_directories(self, tmp_path):
        assert build_app_name_index([str(tmp_path / 'nope')]) == {}

    def test_earlier_directories_win(self, tmp_path):
        first = tmp_path / 'Applications'
        second = tmp_path / 'System Applications'
        first.mkdir()
        second.mkdir()
        self._make_app(first, 'User Copy', 'com.acme.thing')
        self._make_app(second, 'System Copy', 'com.acme.thing')

        index = build_app_name_index([str(first), str(second)])
        assert index['com.acme.thing'] == 'User Copy'

    def test_read_bundle_id_returns_none_without_a_plist(self, tmp_path):
        assert read_bundle_id(str(tmp_path / 'Missing.app')) is None


@pytest.mark.unit
class TestMeasureFolder:
    """`du -skx` first, Python walk as backup, notes for the caveats."""

    def test_du_kilobytes_become_bytes(self, monkeypatch, tmp_path):
        monkeypatch.setattr(subprocess, 'run', fake_du({str(tmp_path): 2048}))
        assert measure_folder(str(tmp_path)) == (2048 * 1024, None)

    def test_du_command_uses_skx(self, monkeypatch, tmp_path):
        captured = {}

        def _run(cmd, **kwargs):
            captured['cmd'] = cmd
            captured['timeout'] = kwargs.get('timeout')
            return subprocess.CompletedProcess(cmd, 0, stdout='4\t/x\n', stderr='')

        monkeypatch.setattr(subprocess, 'run', _run)
        measure_folder(str(tmp_path), timeout=3)

        assert captured['cmd'] == ['/usr/bin/du', '-skx', str(tmp_path)]
        assert captured['timeout'] == 3

    def test_permission_error_keeps_the_partial_total_and_notes_it(self, monkeypatch, tmp_path):
        monkeypatch.setattr(subprocess, 'run', fake_du(
            {str(tmp_path): 100}, stderr='du: fts_read: Operation not permitted\n', returncode=1
        ))
        size, note = measure_folder(str(tmp_path))
        assert size == 100 * 1024
        assert 'Permission restricted' in note

    def test_unparseable_output_falls_back_to_the_walk(self, monkeypatch, tmp_path):
        (tmp_path / 'a.bin').write_bytes(b'x' * 4096)

        def _run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 1, stdout='', stderr='du: something odd\n')

        monkeypatch.setattr(subprocess, 'run', _run)
        size, note = measure_folder(str(tmp_path))

        assert size > 0  # measured by the Python walk instead
        assert note == 'Could not measure this folder'

    def test_missing_du_falls_back_to_the_walk(self, monkeypatch, tmp_path):
        # Non-Mac CI, or a stripped-down system: no /usr/bin/du at all.
        nested = tmp_path / 'a' / 'b' / 'c'
        nested.mkdir(parents=True)
        (nested / 'deep.bin').write_bytes(b'x' * 8192)

        def _run(cmd, **kwargs):
            raise FileNotFoundError('/usr/bin/du')

        monkeypatch.setattr(subprocess, 'run', _run)
        size, note = measure_folder(str(tmp_path))

        assert size >= 8192  # the walk goes full depth, not a capped two levels
        assert note is None

    def test_timeout_is_reported_and_does_not_raise(self, monkeypatch, tmp_path):
        def _run(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd, 10)

        monkeypatch.setattr(subprocess, 'run', _run)
        size, note = measure_folder(str(tmp_path))

        assert size == 0
        assert 'Timed out' in note


@pytest.mark.unit
class TestScanAppCaches:
    """The scan itself: totals, the reporting floor, ordering, degradation."""

    def _home_with_caches(self, tmp_path):
        make_cache_tree(tmp_path, {
            'Library/Caches': {
                'com.spotify.client': [],
                'com.acme.tiny': [],
                'Firefox': [],
            },
            'Library/Logs': {
                'DiagnosticReports': [],
            },
        })
        return {
            str(tmp_path / 'Library/Caches/com.spotify.client'): 8 * 1024 * 1024,  # 8 GB in KB
            str(tmp_path / 'Library/Caches/com.acme.tiny'): 4,                     # 4 KB
            str(tmp_path / 'Library/Caches/Firefox'): 2 * 1024 * 1024,             # 2 GB
            str(tmp_path / 'Library/Logs/DiagnosticReports'): 512 * 1024,          # 512 MB
        }

    def test_entries_are_named_sized_and_sorted(self, monkeypatch, tmp_path):
        monkeypatch.setattr(subprocess, 'run', fake_du(self._home_with_caches(tmp_path)))

        result = scan_app_caches(home=str(tmp_path), app_index={})

        names = [entry['app_name'] for entry in result['entries']]
        assert names == ['Spotify', 'Firefox', 'DiagnosticReports']
        assert result['entries'][0]['size_bytes'] == 8 * GB
        assert result['entries'][0]['size_human'] == '8.0 GB'
        assert result['entries'][0]['folder_name'] == 'com.spotify.client'
        assert result['entries'][0]['category'] == 'caches'
        assert result['entries'][-1]['category'] == 'logs'

    def test_total_counts_folders_below_the_reporting_floor(self, monkeypatch, tmp_path):
        monkeypatch.setattr(subprocess, 'run', fake_du(self._home_with_caches(tmp_path)))

        result = scan_app_caches(home=str(tmp_path), app_index={})

        # The 4 KB folder is too small to list but still part of the pile.
        assert 'com.acme.tiny' not in [entry['folder_name'] for entry in result['entries']]
        assert result['total_size_bytes'] == 8 * GB + 2 * GB + 512 * MB + 4 * 1024
        assert result['folder_count'] == 4
        assert result['scan_status'] == 'complete'
        assert result['permission_denied'] is False

    def test_reporting_floor_and_top_n_are_configurable(self, monkeypatch, tmp_path):
        monkeypatch.setattr(subprocess, 'run', fake_du(self._home_with_caches(tmp_path)))

        everything = scan_app_caches(home=str(tmp_path), app_index={}, min_report_bytes=0)
        assert len(everything['entries']) == 4

        capped = scan_app_caches(home=str(tmp_path), app_index={}, min_report_bytes=0, top_n=2)
        assert [entry['app_name'] for entry in capped['entries']] == ['Spotify', 'Firefox']
        # The cap trims the list, never the total.
        assert capped['total_size_bytes'] == everything['total_size_bytes']

    def test_equal_sizes_break_ties_on_path(self, monkeypatch, tmp_path):
        make_cache_tree(tmp_path, {'Library/Caches': {'zeta': [], 'alpha': []}})
        monkeypatch.setattr(subprocess, 'run', fake_du({
            str(tmp_path / 'Library/Caches/zeta'): 100 * 1024,
            str(tmp_path / 'Library/Caches/alpha'): 100 * 1024,
        }))

        result = scan_app_caches(home=str(tmp_path), app_index={})
        assert [entry['folder_name'] for entry in result['entries']] == ['alpha', 'zeta']

    def test_loose_files_in_a_root_are_counted(self, monkeypatch, tmp_path):
        make_cache_tree(tmp_path, {'Library/Logs': {'App': []}})
        (tmp_path / 'Library/Logs/stray.log').write_bytes(b'x' * (20 * MB))
        monkeypatch.setattr(subprocess, 'run', fake_du({}))

        result = scan_app_caches(home=str(tmp_path), app_index={})

        loose = [e for e in result['entries'] if e['app_name'] == 'Loose files']
        assert len(loose) == 1
        assert loose[0]['size_bytes'] >= 20 * MB
        assert result['total_size_bytes'] >= 20 * MB

    def test_missing_roots_are_reported_not_fatal(self, monkeypatch, tmp_path):
        monkeypatch.setattr(subprocess, 'run', fake_du({}))

        result = scan_app_caches(home=str(tmp_path / 'no-such-home'), app_index={})

        assert result['entries'] == []
        assert result['total_size_bytes'] == 0
        assert [root['status'] for root in result['roots']] == ['missing', 'missing']
        assert result['scan_status'] == 'complete'

    def test_unreadable_root_sets_permission_denied(self, monkeypatch, tmp_path):
        make_cache_tree(tmp_path, {'Library/Caches': {'App': []}})
        real_scandir = os.scandir

        def deny_caches(path, *args, **kwargs):
            if str(path).endswith('Library/Caches'):
                raise PermissionError('Operation not permitted')
            return real_scandir(path, *args, **kwargs)

        monkeypatch.setattr(subprocess, 'run', fake_du({}))
        monkeypatch.setattr(os, 'scandir', deny_caches)

        result = scan_app_caches(home=str(tmp_path), app_index={})

        caches_root = [root for root in result['roots'] if root['category'] == 'caches'][0]
        assert caches_root['status'] == 'error'
        assert 'Full Disk Access' in caches_root['note']
        assert result['permission_denied'] is True

    def test_permission_note_on_a_folder_surfaces_on_the_scan(self, monkeypatch, tmp_path):
        make_cache_tree(tmp_path, {'Library/Caches': {'com.apple.locked': []}})
        monkeypatch.setattr(subprocess, 'run', fake_du(
            {str(tmp_path / 'Library/Caches/com.apple.locked'): 50 * 1024},
            stderr='du: fts_read: Operation not permitted\n', returncode=1,
        ))

        result = scan_app_caches(home=str(tmp_path), app_index={})

        assert result['permission_denied'] is True
        assert 'Permission restricted' in result['entries'][0]['note']

    def test_time_budget_stops_the_scan_and_marks_it_partial(self, monkeypatch, tmp_path):
        make_cache_tree(tmp_path, {
            'Library/Caches': {'a-app': [], 'b-app': [], 'c-app': []},
            'Library/Logs': {'d-app': []},
        })
        monkeypatch.setattr(subprocess, 'run', fake_du({
            str(tmp_path / 'Library/Caches/a-app'): 100 * 1024,
            str(tmp_path / 'Library/Caches/b-app'): 100 * 1024,
            str(tmp_path / 'Library/Caches/c-app'): 100 * 1024,
            str(tmp_path / 'Library/Logs/d-app'): 100 * 1024,
        }))
        # A clock that jumps past the budget once the first folder has been
        # measured: two looks at 0 (the start time and the first check), then
        # well past the deadline for every look after that.
        looks = []

        def creeping_clock():
            looks.append(1)
            return 0 if len(looks) <= 2 else 99

        monkeypatch.setattr(hidden_storage.time, 'time', creeping_clock)

        result = scan_app_caches(home=str(tmp_path), app_index={}, timeout_seconds=2)

        assert result['scan_status'] == 'partial'
        assert len(result['entries']) == 1
        caches_root, logs_root = result['roots']
        assert caches_root['status'] == 'partial'
        assert caches_root['measured_count'] == 1
        assert caches_root['folder_count'] == 3
        # The second root is not even listed once the budget is gone.
        assert logs_root['status'] == 'partial'
        assert 'Ran out of time' in logs_root['note']

    def test_files_directly_under_caches_are_not_treated_as_apps(self, monkeypatch, tmp_path):
        make_cache_tree(tmp_path, {'Library/Caches': {'App': []}})
        (tmp_path / 'Library/Caches/loose.dat').write_bytes(b'x' * 1024)
        monkeypatch.setattr(subprocess, 'run', fake_du(
            {str(tmp_path / 'Library/Caches/App'): 100 * 1024}
        ))

        result = scan_app_caches(home=str(tmp_path), app_index={}, min_report_bytes=0)

        folder_names = [entry['folder_name'] for entry in result['entries']]
        assert 'loose.dat' not in folder_names

    def test_app_index_is_built_once_when_not_supplied(self, monkeypatch, tmp_path):
        make_cache_tree(tmp_path, {'Library/Caches': {'com.acme.one': [], 'com.acme.two': []}})
        monkeypatch.setattr(subprocess, 'run', fake_du({}))
        calls = []
        monkeypatch.setattr(hidden_storage, 'build_app_name_index',
                            lambda *args, **kwargs: calls.append(1) or {})

        scan_app_caches(home=str(tmp_path))
        assert len(calls) == 1

    def test_real_files_without_du(self, monkeypatch, tmp_path):
        """End to end on real files with `du` unavailable - the fallback path
        a non-Mac or stripped-down system takes."""
        make_cache_tree(tmp_path, {
            'Library/Caches': {'com.spotify.client': [('song.bin', 12 * MB)]},
        })

        def _run(cmd, **kwargs):
            raise FileNotFoundError('/usr/bin/du')

        monkeypatch.setattr(subprocess, 'run', _run)
        result = scan_app_caches(home=str(tmp_path), app_index={})

        assert len(result['entries']) == 1
        assert result['entries'][0]['app_name'] == 'Spotify'
        assert result['entries'][0]['size_bytes'] >= 12 * MB
