"""Tests for renderers/terminal.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from renderers.terminal import render_terminal


def _make_scan_data():
    return {
        'scan_type': 'storage',
        'volume': '/',
        'volume_info': {
            'total_human': '500.0 GB',
            'used_human': '250.0 GB',
            'free_human': '250.0 GB',
            'used_percent': 50,
        },
        'top_folders': [],
        'top_files': [],
    }


def _make_personality_data():
    return {
        'status': 'ok',
        'comments': ['Looking good, kiddo.'],
        'tips': [],
    }


class TestRenderTerminalColor:
    def test_no_color_output_has_no_ansi_codes(self):
        output = render_terminal(_make_scan_data(), _make_personality_data(), use_color=False)
        assert '\033[' not in output

    def test_color_survives_a_prior_no_color_call(self):
        # Regression: render_terminal(use_color=False) used to blank the
        # module-level ANSI color constants via `global` and never restore
        # them, permanently losing color for the rest of the process.
        render_terminal(_make_scan_data(), _make_personality_data(), use_color=False)
        output = render_terminal(_make_scan_data(), _make_personality_data(), use_color=True)
        assert '\033[' in output


class TestSkippedItemsCopy:
    """Exclusions and denials are different things and must read differently.

    The old single line called every skipped item a permission problem, so a
    Mac with Full Disk Access granted was told 5,681 items were blocked -
    when nearly all of them were our own exclusion policy (dotfiles, .app
    bundles, caches, Mail, Messages) working exactly as designed.
    """

    def _render(self, **counts):
        scan = _make_scan_data()
        scan.update(counts)
        return render_terminal(scan, _make_personality_data(), use_color=False)

    def test_exclusions_are_not_called_a_permission_problem(self):
        output = self._render(excluded_count=5681, denied_count=0)

        assert '5,681 items not counted' in output
        assert 'on purpose' in output
        assert 'permission' not in output.lower()
        assert "wouldn't let me read" not in output

    def test_denials_are_reported_plainly(self):
        output = self._render(excluded_count=0, denied_count=12)

        assert "12 items your Mac wouldn't let me read" in output

    def test_both_are_reported_separately(self):
        output = self._render(excluded_count=5681, denied_count=12)

        assert '5,681 items not counted' in output
        assert "12 items your Mac wouldn't let me read" in output

    def test_nothing_shown_when_nothing_was_skipped(self):
        output = self._render(excluded_count=0, denied_count=0)

        assert 'not counted' not in output
        assert "wouldn't let me read" not in output

    def test_legacy_report_without_the_split_stays_honest(self):
        # A report saved before the split can't attribute its total, so it
        # must not guess - least of all toward "permissions".
        output = self._render(skipped_count=5681)

        assert '5,681 items not counted' in output
        assert 'permission' not in output.lower()


def _make_hidden_caches():
    return {
        'scan_type': 'hidden_caches',
        'entries': [
            {'app_name': 'Spotify', 'folder_name': 'com.spotify.client',
             'path': '/Users/x/Library/Caches/com.spotify.client',
             'size_bytes': 8 * 1024 ** 3, 'size_human': '8.0 GB', 'category': 'caches'},
            {'app_name': 'Firefox', 'folder_name': 'Firefox',
             'path': '/Users/x/Library/Caches/Firefox',
             'size_bytes': 2 * 1024 ** 3, 'size_human': '2.0 GB', 'category': 'caches'},
        ],
        'roots': [],
        'total_size_bytes': 11 * 1024 ** 3,
        'total_size_human': '11.0 GB',
        'folder_count': 40,
        'scan_status': 'complete',
        'permission_denied': False,
    }


class TestRenderTerminalHiddenCaches:
    """The Hidden App Caches block added by Hidden Storage phase 1a."""

    def test_section_absent_when_scan_has_no_cache_data(self):
        # Scan data predating the cache scanner must render as it always did.
        output = render_terminal(_make_scan_data(), _make_personality_data(), use_color=False)
        assert 'Hidden App Caches' not in output

    def test_section_absent_when_no_entries_cleared_the_floor(self):
        scan = _make_scan_data()
        scan['hidden_caches'] = dict(_make_hidden_caches(), entries=[])
        output = render_terminal(scan, _make_personality_data(), use_color=False)
        assert 'Hidden App Caches' not in output

    def test_entries_are_listed_with_friendly_names_and_total(self):
        scan = _make_scan_data()
        scan['hidden_caches'] = _make_hidden_caches()
        output = render_terminal(scan, _make_personality_data(), use_color=False)

        assert 'Hidden App Caches:' in output
        assert '11.0 GB total' in output
        assert 'Spotify' in output
        assert '8.0 GB' in output
        # The raw bundle ID is report noise in the terminal - the HTML report
        # is where it shows as a secondary line.
        assert 'com.spotify.client' not in output

    def test_only_the_first_ten_entries_are_listed(self):
        scan = _make_scan_data()
        entries = [
            {'app_name': f'App{i}', 'folder_name': f'App{i}', 'path': f'/p/{i}',
             'size_bytes': 1000 - i, 'size_human': '1.0 KB', 'category': 'caches'}
            for i in range(15)
        ]
        scan['hidden_caches'] = dict(_make_hidden_caches(), entries=entries)
        output = render_terminal(scan, _make_personality_data(), use_color=False)

        assert 'App9' in output
        assert 'App10' not in output

    def test_permission_and_partial_caveats_are_shown(self):
        scan = _make_scan_data()
        scan['hidden_caches'] = dict(
            _make_hidden_caches(), permission_denied=True, scan_status='partial'
        )
        output = render_terminal(scan, _make_personality_data(), use_color=False)

        assert 'some cache folders are protected' in output
        assert 'ran out of time' in output
