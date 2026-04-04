"""Tests for scanners/storage.py - parse_size function."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanners.storage import parse_size


class TestParseSize:
    def test_bytes(self):
        assert parse_size('1024B') == 1024

    def test_kilobytes(self):
        assert parse_size('1KB') == 1024

    def test_megabytes(self):
        assert parse_size('500MB') == 500 * 1024**2

    def test_gigabytes(self):
        assert parse_size('1.5GB') == int(1.5 * 1024**3)

    def test_terabytes(self):
        assert parse_size('1TB') == 1024**4

    def test_case_insensitive(self):
        assert parse_size('500mb') == 500 * 1024**2
        assert parse_size('1gb') == 1024**3

    def test_with_whitespace(self):
        assert parse_size('  500MB  ') == 500 * 1024**2

    def test_plain_number_is_bytes(self):
        assert parse_size('1024') == 1024

    def test_none_returns_zero(self):
        assert parse_size(None) == 0

    def test_empty_string_returns_zero(self):
        assert parse_size('') == 0

    def test_invalid_string_returns_zero(self):
        assert parse_size('notanumber') == 0
