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
