"""Tests for scanners/snapshots.py - APFS local snapshots (Phase 1c).

Subprocess is mocked throughout, so these pass on non-Mac CI. The diskutil
and tmutil fixtures below are the verbatim output captured from a real Mac
during the Aug 2026 validation spike (2017 MBP, macOS 13.7.8).
"""

import datetime
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import scanners.snapshots as snapshots_mod
from scanners.snapshots import (
    is_os_update_snapshot,
    list_diskutil_snapshots,
    list_tmutil_snapshots,
    parse_snapshot_date,
    scan_snapshots,
)

# Verbatim from the spike Mac.
REAL_TMUTIL = b"""Snapshots for disk /:
com.apple.TimeMachine.2026-03-08-150255.local (dataless)
"""

REAL_DISKUTIL_TEXT = b"""Snapshot for disk1s1 (1 found)
|
+-- ECFF8B6A-3D97-49D0-88A9-557B84AFE48B
    Name:        com.apple.TimeMachine.2026-03-08-150255.local
    XID:         7609039
    Purgeable:   Yes
"""

NOW = datetime.datetime(2026, 8, 24, 12, 0, 0)


def fake_run(responses):
    """subprocess.run stand-in keyed by the executable's basename + verb.

    Keys: 'tmutil' and 'diskutil'. Values are bytes (stdout, rc 0), or an
    Exception instance to raise, or an int return code for failure.
    """
    def _run(cmd, **kwargs):
        key = 'tmutil' if 'tmutil' in cmd[0] else 'diskutil'
        # The plist attempt and the text attempt are distinguishable.
        if key == 'diskutil' and '-plist' in cmd:
            key = 'diskutil_plist'
        value = responses.get(key)
        if isinstance(value, Exception):
            raise value
        if value is None:
            return subprocess.CompletedProcess(cmd, 1, stdout=b'', stderr=b'not found')
        if isinstance(value, int):
            return subprocess.CompletedProcess(cmd, value, stdout=b'', stderr=b'failed')
        return subprocess.CompletedProcess(cmd, 0, stdout=value, stderr=b'')
    return _run


@pytest.mark.unit
class TestSnapshotNameParsing:

    def test_time_machine_name_yields_its_timestamp(self):
        assert parse_snapshot_date('com.apple.TimeMachine.2026-03-08-150255.local') == \
            datetime.datetime(2026, 3, 8, 15, 2, 55)

    def test_name_without_a_timestamp_returns_none(self):
        # No guessing: a name that carries no date has no date.
        assert parse_snapshot_date('com.apple.os.update-ABC123') is None
        assert parse_snapshot_date('') is None
        assert parse_snapshot_date('something-random') is None

    def test_impossible_dates_are_rejected_not_raised(self):
        assert parse_snapshot_date('com.apple.TimeMachine.2026-13-45-999999.local') is None

    def test_os_update_snapshots_are_recognized(self):
        assert is_os_update_snapshot('com.apple.os.update-0F5C9B') is True
        assert is_os_update_snapshot('com.apple.TimeMachine.2026-03-08-150255.local') is False


@pytest.mark.unit
class TestListing:

    def test_tmutil_output_is_parsed_and_annotations_stripped(self, monkeypatch):
        monkeypatch.setattr(subprocess, 'run', fake_run({'tmutil': REAL_TMUTIL}))
        names, err = list_tmutil_snapshots()

        assert err is None
        # The "(dataless)" annotation must not become part of the name.
        assert names == ['com.apple.TimeMachine.2026-03-08-150255.local']

    def test_tmutil_header_only_means_no_snapshots(self, monkeypatch):
        monkeypatch.setattr(subprocess, 'run', fake_run({'tmutil': b'Snapshots for disk /:\n'}))
        assert list_tmutil_snapshots() == ([], None)

    def test_missing_tmutil_is_reported_not_raised(self, monkeypatch):
        monkeypatch.setattr(subprocess, 'run', fake_run({'tmutil': FileNotFoundError('tmutil')}))
        names, err = list_tmutil_snapshots()
        assert names == []
        assert 'not available' in err

    def test_diskutil_text_output_yields_names_and_purgeable(self, monkeypatch):
        # The -plist form fails here, so the text fallback has to carry it.
        monkeypatch.setattr(subprocess, 'run', fake_run({
            'diskutil_plist': 1, 'diskutil': REAL_DISKUTIL_TEXT,
        }))
        entries, err = list_diskutil_snapshots()

        assert err is None
        assert entries == [{
            'name': 'com.apple.TimeMachine.2026-03-08-150255.local',
            'purgeable': True,
        }]

    def test_diskutil_plist_is_preferred_when_it_works(self, monkeypatch):
        import plistlib
        plist = plistlib.dumps({'Snapshots': [
            {'SnapshotName': 'com.apple.TimeMachine.2026-08-24-090000.local', 'Purgeable': False},
        ]})
        monkeypatch.setattr(subprocess, 'run', fake_run({'diskutil_plist': plist}))

        entries, err = list_diskutil_snapshots()
        assert entries == [{
            'name': 'com.apple.TimeMachine.2026-08-24-090000.local',
            'purgeable': False,
        }]

    def test_malformed_plist_falls_back_to_text(self, monkeypatch):
        monkeypatch.setattr(subprocess, 'run', fake_run({
            'diskutil_plist': b'not a plist at all', 'diskutil': REAL_DISKUTIL_TEXT,
        }))
        entries, _err = list_diskutil_snapshots()
        assert len(entries) == 1

    def test_diskutil_targets_the_data_volume(self, monkeypatch):
        # / is the sealed System volume; local snapshots live on Data.
        seen = []

        def _run(cmd, **kwargs):
            seen.append(cmd)
            return subprocess.CompletedProcess(cmd, 1, stdout=b'', stderr=b'')

        monkeypatch.setattr(subprocess, 'run', _run)
        list_diskutil_snapshots()

        assert all(cmd[-1] == '/System/Volumes/Data' for cmd in seen)


@pytest.mark.unit
class TestScanSnapshots:

    def test_real_spike_output_end_to_end(self, monkeypatch):
        monkeypatch.setattr(subprocess, 'run', fake_run({
            'tmutil': REAL_TMUTIL, 'diskutil_plist': 1, 'diskutil': REAL_DISKUTIL_TEXT,
        }))

        result = scan_snapshots(now=NOW)

        assert result['status'] == 'complete'
        assert result['count'] == 1
        assert result['snapshots'][0]['created'] == '2026-03-08T15:02:55'
        # Taken 15:02 on Mar 8, measured at noon on Aug 24: 168 complete
        # 24-hour periods (timedelta.days truncates the partial day). Either
        # way it is far past the 2-day staleness threshold.
        assert result['snapshots'][0]['age_days'] == 168
        assert result['oldest_age_days'] == 168
        assert result['stale_count'] == 1
        assert result['purgeable_count'] == 1

    def test_no_sizes_are_ever_reported(self, monkeypatch):
        # The rule this scanner exists to respect: APFS snapshots share
        # blocks, so a per-snapshot size has no single true value.
        monkeypatch.setattr(subprocess, 'run', fake_run({
            'tmutil': REAL_TMUTIL, 'diskutil_plist': 1, 'diskutil': REAL_DISKUTIL_TEXT,
        }))

        result = scan_snapshots(now=NOW)

        for snapshot in result['snapshots']:
            assert not any('size' in key.lower() for key in snapshot)
        assert not any('size' in key.lower() or 'purgeable_bytes' in key for key in result)

    def test_os_update_snapshots_are_counted_but_not_listed(self, monkeypatch):
        monkeypatch.setattr(subprocess, 'run', fake_run({
            'tmutil': b"""Snapshots for disk /:
com.apple.TimeMachine.2026-08-24-090000.local
com.apple.os.update-8A1F2C3D
""",
            'diskutil_plist': 1, 'diskutil': 1,
        }))

        result = scan_snapshots(now=NOW)

        # Never listed: they belong to macOS, and one may be what the system
        # is currently running from.
        assert result['count'] == 1
        assert result['os_update_count'] == 1
        assert all(not s['is_os_update'] for s in result['snapshots'])

    def test_fresh_snapshots_are_not_counted_as_stale(self, monkeypatch):
        # Time Machine keeps ~24h of hourly snapshots and cleans up after
        # itself. Fresh ones are the system working, not a defect.
        monkeypatch.setattr(subprocess, 'run', fake_run({
            'tmutil': b"""Snapshots for disk /:
com.apple.TimeMachine.2026-08-24-090000.local
com.apple.TimeMachine.2026-08-24-100000.local
""",
            'diskutil_plist': 1, 'diskutil': 1,
        }))

        result = scan_snapshots(now=NOW)

        assert result['count'] == 2
        assert result['stale_count'] == 0
        assert result['oldest_age_days'] == 0

    def test_snapshots_are_ordered_oldest_first(self, monkeypatch):
        monkeypatch.setattr(subprocess, 'run', fake_run({
            'tmutil': b"""Snapshots for disk /:
com.apple.TimeMachine.2026-08-24-100000.local
com.apple.TimeMachine.2026-03-08-150255.local
""",
            'diskutil_plist': 1, 'diskutil': 1,
        }))

        result = scan_snapshots(now=NOW)
        assert [s['age_days'] for s in result['snapshots']] == [168, 0]

    def test_diskutil_only_snapshots_are_still_found(self, monkeypatch):
        # tmutil lists the Data volume's TM snapshots; diskutil can see
        # others. A snapshot only one tool knows about must not vanish.
        import plistlib
        plist = plistlib.dumps({'Snapshots': [
            {'SnapshotName': 'com.apple.TimeMachine.2026-08-01-120000.local', 'Purgeable': True},
        ]})
        monkeypatch.setattr(subprocess, 'run', fake_run({
            'tmutil': b'Snapshots for disk /:\n', 'diskutil_plist': plist,
        }))

        result = scan_snapshots(now=NOW)
        assert result['count'] == 1

    def test_duplicates_across_both_sources_are_merged(self, monkeypatch):
        monkeypatch.setattr(subprocess, 'run', fake_run({
            'tmutil': REAL_TMUTIL, 'diskutil_plist': 1, 'diskutil': REAL_DISKUTIL_TEXT,
        }))
        result = scan_snapshots(now=NOW)
        assert result['count'] == 1

    def test_neither_tool_available_reports_unavailable(self, monkeypatch):
        # The normal outcome on non-Mac CI: reported, never raised.
        monkeypatch.setattr(subprocess, 'run', fake_run({
            'tmutil': FileNotFoundError('tmutil'),
            'diskutil_plist': FileNotFoundError('diskutil'),
            'diskutil': FileNotFoundError('diskutil'),
        }))

        result = scan_snapshots(now=NOW)

        assert result['status'] == 'unavailable'
        assert result['count'] == 0
        assert 'note' in result

    def test_timeout_does_not_raise(self, monkeypatch):
        def _run(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd, 15)

        monkeypatch.setattr(subprocess, 'run', _run)
        result = scan_snapshots(now=NOW)
        assert result['status'] == 'unavailable'

    def test_purgeable_stays_unknown_when_diskutil_is_silent(self, monkeypatch):
        monkeypatch.setattr(subprocess, 'run', fake_run({
            'tmutil': REAL_TMUTIL, 'diskutil_plist': 1, 'diskutil': 1,
        }))

        result = scan_snapshots(now=NOW)

        # Absent, not False - "we don't know" and "macOS says no" differ.
        assert 'purgeable' not in result['snapshots'][0]
        assert result['purgeable_count'] == 0
