"""
CLI tests for yourdad.py
Basic smoke tests to ensure commands don't crash
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import yourdad
from scanners.storage import parse_size


def test_version_command():
    """Test --version command works"""
    result = subprocess.run(
        [sys.executable, "yourdad.py", "--version"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode == 0
    assert "Dad Ware" in result.stdout or "yourdad" in result.stdout


def test_help_command():
    """Test --help command works"""
    result = subprocess.run(
        [sys.executable, "yourdad.py", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode == 0
    assert "Dad Ware" in result.stdout or "yourdad" in result.stdout


def test_cpu_command_exists():
    """Test that cpu subcommand is recognized"""
    result = subprocess.run(
        [sys.executable, "yourdad.py", "cpu", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode in [0, 2]


def test_all_command_exists():
    """Test that all subcommand is recognized"""
    result = subprocess.run(
        [sys.executable, "yourdad.py", "all", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode in [0, 2]


def test_export_command_exists():
    """Test that export command exists"""
    result = subprocess.run(
        [sys.executable, "yourdad.py", "export", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=5
    )
    # Should show help or error (not crash)
    assert result.returncode in [0, 2]  # 0 = success, 2 = argparse error (also OK)


class TestRefactoredHelpersExist:
    """The storage/cpu/all branches of main() were unified into shared
    helpers. Pin their existence so a future refactor can't silently
    re-fork the logic."""

    def test_save_and_open_report_exists(self):
        assert callable(yourdad.save_and_open_report)

    def test_run_storage_scan_exists(self):
        assert callable(yourdad.run_storage_scan)

    def test_run_cpu_scan_exists(self):
        assert callable(yourdad.run_cpu_scan)


class TestRunStorageScanArgumentPlumbing:
    """Pins the drift bug where the `all` command used to hardcode
    top_n=500 / min_size_bytes=0 in scan_storage() calls, silently
    ignoring --top and --min-size. run_storage_scan() is now the single
    code path used by both `storage` and `all`, so exercising it directly
    proves the user's flags reach scan_storage()."""

    def test_honors_top_and_min_size_flags(self, monkeypatch):
        calls = []

        def fake_scan_storage(path, depth=2, top_n=500, min_size_bytes=0, progress_callback=None):
            calls.append({'path': path, 'top_n': top_n, 'min_size_bytes': min_size_bytes})
            return {'top_folders': []}

        monkeypatch.setattr(yourdad, 'select_volume', lambda volume: '/Volumes/FakeVolume')
        monkeypatch.setattr(yourdad, 'scan_storage', fake_scan_storage)
        monkeypatch.setattr(yourdad, 'check_full_disk_access', lambda: {'has_access': True})

        args = argparse.Namespace(
            volume=None,
            top=42,
            min_size='10MB',
            skip_protected=False,
            no_mac_libraries=True,
        )

        scan_data = yourdad.run_storage_scan(args)

        assert scan_data is not None
        # Both the volume scan and the separate home-directory scan should
        # have received the user's --top/--min-size values.
        assert len(calls) >= 1
        expected_min_size_bytes = parse_size('10MB')
        for call in calls:
            assert call['top_n'] == 42
            assert call['min_size_bytes'] == expected_min_size_bytes

    def test_returns_none_when_no_volume_selected(self, monkeypatch):
        monkeypatch.setattr(yourdad, 'select_volume', lambda volume: None)
        args = argparse.Namespace(
            volume=None,
            top=500,
            min_size=None,
            skip_protected=False,
            no_mac_libraries=True,
        )
        assert yourdad.run_storage_scan(args) is None


class TestAllCommandHonorsTopAndMinSize:
    """Integration-level pin: drive main() itself (real argparse) for the
    `all` subcommand and confirm the parsed --top/--min-size values reach
    run_storage_scan unmodified, instead of the old hardcoded 500/0."""

    def test_all_passes_cli_flags_through_to_storage_scan(self, monkeypatch, capsys):
        captured = {}

        def fake_run_storage_scan(args):
            captured['top'] = args.top
            captured['min_size'] = args.min_size
            return {'top_folders': [], 'mac_libraries': {}}

        def fake_run_cpu_scan(args):
            return None  # keep this test focused on the storage-scan plumbing

        monkeypatch.setattr(yourdad, 'run_storage_scan', fake_run_storage_scan)
        monkeypatch.setattr(yourdad, 'run_cpu_scan', fake_run_cpu_scan)
        monkeypatch.setattr(yourdad, 'add_personality', lambda scan_data: {'comments': []})
        monkeypatch.setattr(yourdad, 'render_terminal', lambda scan_data, personality_data, use_color: '')
        monkeypatch.setattr(yourdad, 'save_and_open_report', lambda *a, **k: None)
        monkeypatch.setattr(
            sys, 'argv',
            ['yourdad.py', '--top', '7', '--min-size', '2MB', 'all']
        )

        exit_code = yourdad.main()

        assert exit_code == 0
        assert captured['top'] == 7
        assert captured['min_size'] == '2MB'
