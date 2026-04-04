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
        assert format_size(1024) == "1.0 KB"
        assert format_size(1536) == "1.5 KB"

    def test_megabytes(self):
        assert format_size(1024**2) == "1.0 MB"
        assert format_size(500 * 1024**2) == "500.0 MB"

    def test_gigabytes(self):
        assert format_size(1024**3) == "1.0 GB"
        assert format_size(1.5 * 1024**3) == "1.5 GB"

    def test_terabytes(self):
        assert format_size(1024**4) == "1.0 TB"

    def test_petabytes(self):
        assert format_size(1024**5) == "1.0 PB"


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
