"""Tests for utils/formatters.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.formatters import format_size, get_status_emoji, get_status_text


class TestFormatSize:
    def test_bytes(self):
        assert format_size(0) == "0.0 B"
        assert format_size(512) == "512.0 B"

    def test_kilobytes(self):
        assert format_size(1000) == "1.0 KB"
        assert format_size(1500) == "1.5 KB"

    def test_megabytes(self):
        assert format_size(1000**2) == "1.0 MB"
        assert format_size(500 * 1000**2) == "500.0 MB"

    def test_gigabytes(self):
        assert format_size(1000**3) == "1.0 GB"
        assert format_size(1.5 * 1000**3) == "1.5 GB"

    def test_terabytes(self):
        assert format_size(1000**4) == "1.0 TB"

    def test_petabytes(self):
        assert format_size(1000**5) == "1.0 PB"

    def test_units_are_decimal_and_match_finder(self):
        """The whole point of the decimal switch.

        These are real numbers from the Aug 2026 spike: statvfs reported
        50,983,555,072 free bytes on a Mac where Finder said 50.98 GB
        (excluding purgeable). Binary math printed "47.5 GB" for the same
        bytes - a ~7% gap that reads as a broken tool.
        """
        assert format_size(50_983_555_072) == "51.0 GB"
        # A 250 GB disk must not read as 232.8 GB.
        assert format_size(250 * 1000**3) == "250.0 GB"

    def test_negative_clamped_to_zero(self):
        # used_bytes math can go negative on unusual mounts; format_size should
        # never render a leading minus sign.
        assert format_size(-512) == "0.0 B"
        assert format_size(-1) == "0.0 B"

    def test_does_not_shadow_builtin_bytes(self):
        # Regression: the parameter used to be named `bytes`, shadowing the
        # builtin and mutating in place. Passing a plain int must not raise
        # and must not have side effects on the caller's value.
        value = 2000
        result = format_size(value)
        assert result == "2.0 KB"
        assert value == 2000


class TestStatusEmoji:
    def test_critical(self):
        assert get_status_emoji('critical') == '\U0001f534'

    def test_warn(self):
        assert get_status_emoji('warn') == '\U0001f7e1'

    def test_ok(self):
        assert get_status_emoji('ok') == '\U0001f7e2'

    def test_unknown_defaults_to_ok(self):
        assert get_status_emoji('whatever') == '\U0001f7e2'


class TestStatusText:
    def test_critical(self):
        assert get_status_text('critical') == 'needs attention'

    def test_warn(self):
        assert get_status_text('warn') == 'stable but cluttered'

    def test_ok(self):
        assert get_status_text('ok') == 'all good'
