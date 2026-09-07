"""Tests for scanners/trash.py - the Trash scanner (Phase 2).

Conventions follow tests/test_hidden_storage.py: `unit` marker, real temp
directories for filesystem behavior, and a mocked `subprocess.run` for `du`
so these pass on non-Mac CI.

The load-bearing case here is the denial. A Trash that macOS refuses to show
must come back as 'no_permission' and stay out of the totals - a silent 0 B
for a folder holding 40 GB is the exact failure this scanner exists to
prevent.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import scanners.trash as trash_module
from scanners.trash import (
    find_trash_locations,
    home_trash_path,
    measure_trash_location,
    scan_trash,
    volume_trash_path,
)

KB = 1024
MB = 1024 * KB
GB = 1024 * MB


def fake_du(sizes_by_path_kb, stderr='', returncode=0):
    """A `subprocess.run` stand-in answering `du -skx` from a dict of KB."""
    def _run(cmd, **kwargs):
        path = cmd[-1]
        size_kb = sizes_by_path_kb.get(path, 0)
        return subprocess.CompletedProcess(
            cmd, returncode, stdout=f'{size_kb}\t{path}\n', stderr=stderr
        )
    return _run


def make_trash(root, items):
    """Create a trash folder holding `items` - a list of (name, size_bytes)."""
    root.mkdir(parents=True, exist_ok=True)
    for name, size in items:
        (root / name).write_bytes(b'x' * size)
    return root


@pytest.mark.unit
class TestTrashPaths:
    def test_home_trash_is_the_dot_trash_folder(self):
        assert home_trash_path('/Users/dad') == '/Users/dad/.Trash'

    def test_volume_trash_is_per_user(self):
        # `.Trashes` holds one folder per account; sizing the whole thing
        # would report another user's deleted files as this user's.
        assert volume_trash_path('/Volumes/BACKUP', uid=501) == '/Volumes/BACKUP/.Trashes/501'

    def test_locations_cover_home_and_every_volume(self):
        locations = find_trash_locations(
            home='/Users/dad', volume_paths=['/Volumes/BACKUP'], uid=501)

        assert [path for _label, path in locations] == [
            '/Users/dad/.Trash',
            '/Volumes/BACKUP/.Trashes/501',
        ]
        assert 'BACKUP' in locations[1][0]

    def test_home_can_be_left_out_for_a_drive_report(self):
        # A report about an external drive covers that drive's Trash, not
        # the one in a home folder on a different disk.
        locations = find_trash_locations(
            include_home=False, volume_paths=['/Volumes/BACKUP'], uid=501)

        assert [path for _label, path in locations] == ['/Volumes/BACKUP/.Trashes/501']


@pytest.mark.unit
class TestMeasureTrashLocation:
    def test_a_full_trash_reports_size_count_and_age(self, monkeypatch, tmp_path):
        trash = make_trash(tmp_path / '.Trash', [('old.mov', 10), ('new.pdf', 10)])
        os.utime(trash / 'old.mov', (time.time() - 40 * 86400,) * 2)
        monkeypatch.setattr(subprocess, 'run', fake_du({str(trash): 4 * MB // KB}))

        location = measure_trash_location('Trash', str(trash))

        assert location.status == 'measured'
        assert location.size_bytes == 4 * MB
        assert location.item_count == 2
        assert location.oldest_age_days == 40

    def test_ds_store_is_not_an_item_the_user_threw_away(self, monkeypatch, tmp_path):
        trash = make_trash(tmp_path / '.Trash', [('.DS_Store', 10), ('report.pdf', 10)])
        monkeypatch.setattr(subprocess, 'run', fake_du({str(trash): 1}))

        assert measure_trash_location('Trash', str(trash)).item_count == 1

    def test_missing_folder_is_not_an_error(self, tmp_path):
        # macOS creates .Trash on demand, so its absence means nothing has
        # been deleted here - reportable, not a failure.
        location = measure_trash_location('Trash', str(tmp_path / 'nope'))

        assert location.status == 'missing'
        assert location.size_bytes == 0

    def test_empty_trash_says_empty(self, monkeypatch, tmp_path):
        trash = make_trash(tmp_path / '.Trash', [])
        monkeypatch.setattr(subprocess, 'run', fake_du({}))

        assert measure_trash_location('Trash', str(trash)).status == 'empty'

    def test_a_tcc_denial_is_reported_not_measured(self, monkeypatch, tmp_path):
        trash = make_trash(tmp_path / '.Trash', [('big.mov', 10)])
        monkeypatch.setattr(trash_module, 'check_folder_access',
                            lambda path: {'status': 'denied', 'path': path, 'reason': 'tcc'})
        # `du` would happily print 0 for a folder it cannot read. The probe
        # runs first precisely so that number never reaches the report.
        monkeypatch.setattr(subprocess, 'run', fake_du({}))

        location = measure_trash_location('Trash', str(trash))

        assert location.status == 'no_permission'
        assert location.size_bytes == 0
        assert location.item_count is None
        assert 'Full Disk Access' in location.note

    def test_a_posix_denial_reads_differently(self, monkeypatch, tmp_path):
        trash = make_trash(tmp_path / '.Trash', [])
        monkeypatch.setattr(trash_module, 'check_folder_access',
                            lambda path: {'status': 'denied', 'path': path, 'reason': 'posix'})

        location = measure_trash_location('Trash', str(trash))

        assert location.status == 'no_permission'
        assert 'Full Disk Access' not in location.note


@pytest.mark.unit
class TestScanTrash:
    def test_totals_add_up_across_locations(self, monkeypatch, tmp_path):
        home_trash = make_trash(tmp_path / 'home' / '.Trash', [('a.mov', 10)])
        volume_trash = make_trash(tmp_path / 'vol' / '.Trashes' / '501', [('b.mov', 10)])
        monkeypatch.setattr(subprocess, 'run', fake_du({
            str(home_trash): 2 * GB // KB,
            str(volume_trash): 1 * GB // KB,
        }))

        result = scan_trash(home=str(tmp_path / 'home'),
                            volume_paths=[str(tmp_path / 'vol')], uid=501)

        assert result['status'] == 'complete'
        assert result['total_size_bytes'] == 3 * GB
        assert result['item_count'] == 2
        assert len(result['locations']) == 2

    def test_a_blocked_location_never_lands_in_the_total(self, monkeypatch, tmp_path):
        home_trash = make_trash(tmp_path / 'home' / '.Trash', [('a.mov', 10)])
        monkeypatch.setattr(subprocess, 'run', fake_du({str(home_trash): 2 * GB // KB}))

        real_access = trash_module.check_folder_access

        def blocked_home(path):
            if path == str(home_trash):
                return {'status': 'denied', 'path': path, 'reason': 'tcc'}
            return real_access(path)

        monkeypatch.setattr(trash_module, 'check_folder_access', blocked_home)

        result = scan_trash(home=str(tmp_path / 'home'), volume_paths=[], uid=501)

        assert result['permission_denied'] is True
        assert result['total_size_bytes'] == 0
        assert result['locations'][0]['status'] == 'no_permission'

    def test_oldest_age_is_the_oldest_anywhere(self, monkeypatch, tmp_path):
        home_trash = make_trash(tmp_path / 'home' / '.Trash', [('a.mov', 10)])
        volume_trash = make_trash(tmp_path / 'vol' / '.Trashes' / '501', [('b.mov', 10)])
        os.utime(home_trash / 'a.mov', (time.time() - 5 * 86400,) * 2)
        os.utime(volume_trash / 'b.mov', (time.time() - 90 * 86400,) * 2)
        monkeypatch.setattr(subprocess, 'run', fake_du({}))

        result = scan_trash(home=str(tmp_path / 'home'),
                            volume_paths=[str(tmp_path / 'vol')], uid=501)

        assert result['oldest_age_days'] == 90

    def test_a_missing_trash_scans_clean(self, monkeypatch, tmp_path):
        monkeypatch.setattr(subprocess, 'run', fake_du({}))

        result = scan_trash(home=str(tmp_path), volume_paths=[], uid=501)

        assert result['status'] == 'complete'
        assert result['total_size_bytes'] == 0
        assert result['locations'][0]['status'] == 'missing'

    def test_the_scan_stops_at_its_deadline(self, monkeypatch, tmp_path):
        monkeypatch.setattr(subprocess, 'run', fake_du({}))

        result = scan_trash(home=str(tmp_path), volume_paths=[str(tmp_path)],
                            uid=501, timeout_seconds=0)

        assert result['status'] == 'partial'
        assert result['locations'] == []

    def test_the_dict_shape_survives_a_round_trip(self, monkeypatch, tmp_path):
        from scanners.models import TrashScan

        make_trash(tmp_path / '.Trash', [('a.mov', 10)])
        monkeypatch.setattr(subprocess, 'run', fake_du({}))

        result = scan_trash(home=str(tmp_path), volume_paths=[], uid=501)

        assert TrashScan.from_dict(result).to_dict() == result


@pytest.mark.unit
class TestTrashInTheReport:
    """The scan is only useful if the numbers reach the page."""

    def _scan_data(self, trash):
        return {'scan_type': 'storage', 'trash': trash}

    def test_html_section_shows_the_total(self):
        from renderers.html import render_trash

        html = render_trash(self._scan_data({
            'locations': [{'label': 'Trash (your home folder)',
                           'path': '/Users/dad/.Trash', 'size_bytes': 3 * GB,
                           'size_human': '3.2 GB', 'item_count': 12,
                           'status': 'measured'}],
            'total_size_bytes': 3 * GB, 'total_size_human': '3.2 GB',
            'item_count': 12, 'oldest_age_days': 60, 'status': 'complete',
        }))

        assert '3.2 GB' in html
        assert '12 items' in html
        assert '2 months' in html

    def test_html_section_is_absent_without_trash_data(self):
        from renderers.html import render_trash

        assert render_trash({'scan_type': 'storage'}) == ''

    def test_an_empty_trash_gets_no_section(self):
        from renderers.html import render_trash

        html = render_trash(self._scan_data({
            'locations': [{'label': 'Trash', 'path': '/Users/dad/.Trash',
                           'size_bytes': 0, 'size_human': '0 B',
                           'item_count': 0, 'status': 'empty'}],
            'total_size_bytes': 0, 'total_size_human': '0 B',
            'item_count': 0, 'status': 'complete',
        }))

        assert html == ''

    def test_a_blocked_trash_says_so_instead_of_zero(self):
        from renderers.html import render_trash

        html = render_trash(self._scan_data({
            'locations': [{'label': 'Trash (your home folder)',
                           'path': '/Users/dad/.Trash', 'size_bytes': 0,
                           'size_human': '0 B', 'item_count': None,
                           'status': 'no_permission',
                           'note': 'Needs Full Disk Access to measure'}],
            'total_size_bytes': 0, 'total_size_human': '0 B', 'item_count': 0,
            'permission_denied': True, 'status': 'complete',
        }))

        assert 'not measured' in html
        assert 'Full Disk Access' in html
        assert '0 B' not in html

    def test_dad_tells_you_to_take_the_bag_out(self):
        from personality.dad import add_personality

        result = add_personality({
            'scan_type': 'storage',
            'volume_info': {'free_percent': 50, 'used_percent': 50},
            'trash': {'total_size_bytes': 12 * 1000**3,
                      'total_size_human': '12.0 GB', 'item_count': 40,
                      'oldest_age_days': 200, 'status': 'complete'},
        })

        assert any('trash' in c.lower() for c in result['comments'])
        assert any('Empty the Trash' in tip for tip in result['tips'])

    def test_an_empty_trash_gets_no_lecture(self):
        from personality.dad import add_personality

        result = add_personality({
            'scan_type': 'storage',
            'volume_info': {'free_percent': 50, 'used_percent': 50},
            'trash': {'total_size_bytes': 0, 'total_size_human': '0 B',
                      'item_count': 0, 'status': 'complete'},
        })

        assert not any('Empty the Trash' in tip for tip in result['tips'])
