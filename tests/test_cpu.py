"""Tests for scanners/cpu.py - identify_memory_hogs function."""

import sys
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanners.cpu import identify_memory_hogs, APP_FAMILIES


class TestIdentifyMemoryHogs:
    def test_groups_chrome_processes(self):
        processes = [
            {'name': 'Google Chrome', 'memory_mb': 200},
            {'name': 'Google Chrome Helper', 'memory_mb': 150},
            {'name': 'Google Chrome Helper (Renderer)', 'memory_mb': 300},
        ]
        hogs = identify_memory_hogs(processes, threshold_mb=50)
        chrome_hogs = [h for h in hogs if h['name'] == 'Chrome']
        assert len(chrome_hogs) == 1
        assert chrome_hogs[0]['total_mb'] == 650
        assert chrome_hogs[0]['process_count'] == 3

    def test_groups_safari_with_webkit(self):
        processes = [
            {'name': 'Safari', 'memory_mb': 100},
            {'name': 'com.apple.WebKit.WebContent', 'memory_mb': 250},
            {'name': 'com.apple.WebKit.Networking', 'memory_mb': 50},
        ]
        hogs = identify_memory_hogs(processes, threshold_mb=50)
        safari_hogs = [h for h in hogs if h['name'] == 'Safari']
        assert len(safari_hogs) == 1
        assert safari_hogs[0]['total_mb'] == 400

    def test_filters_by_threshold(self):
        processes = [
            {'name': 'SmallApp', 'memory_mb': 10},
            {'name': 'BigApp', 'memory_mb': 500},
        ]
        hogs = identify_memory_hogs(processes, threshold_mb=50)
        names = [h['name'] for h in hogs]
        assert 'BigApp' in names
        assert 'SmallApp' not in names

    def test_sorted_by_memory_descending(self):
        processes = [
            {'name': 'SmallApp', 'memory_mb': 100},
            {'name': 'BigApp', 'memory_mb': 500},
            {'name': 'MediumApp', 'memory_mb': 250},
        ]
        hogs = identify_memory_hogs(processes, threshold_mb=50)
        memories = [h['total_mb'] for h in hogs]
        assert memories == sorted(memories, reverse=True)

    def test_empty_processes(self):
        assert identify_memory_hogs([], threshold_mb=50) == []

    def test_groups_firefox(self):
        processes = [
            {'name': 'firefox', 'memory_mb': 300},
            {'name': 'firefox-bin', 'memory_mb': 200},
        ]
        hogs = identify_memory_hogs(processes, threshold_mb=50)
        ff = [h for h in hogs if h['name'] == 'Firefox']
        assert len(ff) == 1
        assert ff[0]['total_mb'] == 500


class TestAppFamiliesTable:
    """
    identify_memory_hogs() used to be a 30-line if/elif chain; it's now a
    lookup over the module-level APP_FAMILIES table followed by the
    'helper'/system-process catch-alls. These tests pin the same
    categorization the old chain produced for a representative set of names.
    """

    @pytest.mark.parametrize('process_name,expected_family', [
        ('Google Chrome Helper (Renderer)', 'Chrome'),
        ('com.apple.WebKit.WebContent', 'Safari'),
        ('com.apple.some.system.daemon', 'System Processes'),
        ('Foo Helper', 'Helper Processes'),
        ('SomeUnknownApp', 'SomeUnknownApp'),
    ])
    def test_representative_process_names(self, process_name, expected_family):
        processes = [{'name': process_name, 'memory_mb': 100}]
        hogs = identify_memory_hogs(processes, threshold_mb=50)
        assert len(hogs) == 1
        assert hogs[0]['name'] == expected_family

    def test_specific_app_family_wins_over_helper_catch_all(self):
        # A process name matching both a known app family and containing
        # "helper" must be grouped under the specific app, not lumped into
        # "Helper Processes" - the table is checked before the helper branch.
        processes = [{'name': 'Slack Helper', 'memory_mb': 100}]
        hogs = identify_memory_hogs(processes, threshold_mb=50)
        assert hogs[0]['name'] == 'Slack'

    def test_app_families_table_is_nonempty_and_well_formed(self):
        assert len(APP_FAMILIES) > 0
        for substrings, label in APP_FAMILIES:
            assert isinstance(substrings, tuple)
            assert all(isinstance(s, str) and s == s.lower() for s in substrings)
            assert isinstance(label, str)
