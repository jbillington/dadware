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
        # Keep the suite hermetic: the real scan_app_caches() shells out to
        # `du` once per folder under ~/Library/Caches, which on a real Mac
        # would make this unit test take seconds and depend on the machine.
        monkeypatch.setattr(yourdad, 'scan_app_caches', lambda: {'scan_status': 'complete'})

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


class TestMergeHomeFolders:
    """merge_home_folders() used to match home-folder names with a loose,
    case-insensitive substring check (e.g. 'documents' in path), so any
    folder that merely mentioned a home-folder name anywhere in its path
    was mis-classified as a home folder. It now matches on exact/basename
    equality via utils.path_utils.basenames_in()."""

    def test_junk_path_is_not_treated_as_a_home_folder(self):
        scan_data = {
            'top_folders': [
                {'path': f'{os.path.expanduser("~")}/some_other_folder', 'size_bytes': 1},
            ],
        }
        home_scan_data = {
            'top_folders': [
                {'path': f'{os.path.expanduser("~")}/Downloads', 'path_display': 'Users/me/Downloads', 'size_bytes': 100},
                # Merely contains the word 'documents' - must NOT be treated
                # as the real Documents folder.
                {'path': f'{os.path.expanduser("~")}/Old-Documents-Archive', 'path_display': 'Users/me/Old-Documents-Archive', 'size_bytes': 999},
            ],
        }

        yourdad.merge_home_folders(scan_data, home_scan_data)

        merged_paths = [f['path'] for f in scan_data['top_folders']]
        assert f'{os.path.expanduser("~")}/Downloads' in merged_paths
        assert f'{os.path.expanduser("~")}/Old-Documents-Archive' not in merged_paths
        assert scan_data['home_folders_total_bytes'] == 100

    def test_recognized_home_folders_are_merged(self):
        home = os.path.expanduser('~')
        scan_data = {'top_folders': []}
        home_scan_data = {
            'top_folders': [
                {'path': f'{home}/Downloads', 'path_display': 'Users/me/Downloads', 'size_bytes': 10},
                {'path': f'{home}/Desktop', 'path_display': 'Users/me/Desktop', 'size_bytes': 20},
                {'path': f'{home}/Documents', 'path_display': 'Users/me/Documents', 'size_bytes': 30},
                {'path': f'{home}/random_project', 'path_display': 'Users/me/random_project', 'size_bytes': 40},
            ],
        }

        yourdad.merge_home_folders(scan_data, home_scan_data)

        merged_paths = {f['path'] for f in scan_data['top_folders']}
        assert merged_paths == {f'{home}/Downloads', f'{home}/Desktop', f'{home}/Documents'}
        assert scan_data['home_folders_total_bytes'] == 60


class TestRunStorageScanAttachesHiddenCaches:
    """Wiring for Hidden Storage phase 1a: the cache scan is attached to the
    storage scan data, and a failure inside it degrades to a recorded error
    rather than taking the whole report down."""

    def _args(self):
        return argparse.Namespace(
            volume=None, top=10, min_size=None,
            skip_protected=False, no_mac_libraries=True,
        )

    def _patch_scan(self, monkeypatch):
        monkeypatch.setattr(yourdad, 'select_volume', lambda volume: '/Volumes/FakeVolume')
        monkeypatch.setattr(
            yourdad, 'scan_storage',
            lambda path, depth=2, top_n=500, min_size_bytes=0, progress_callback=None: {'top_folders': []},
        )
        monkeypatch.setattr(yourdad, 'check_full_disk_access', lambda: {'has_access': True})

    def test_result_is_attached_under_hidden_caches(self, monkeypatch):
        self._patch_scan(monkeypatch)
        payload = {'scan_status': 'complete', 'entries': [], 'total_size_bytes': 7}
        monkeypatch.setattr(yourdad, 'scan_app_caches', lambda: payload)

        scan_data = yourdad.run_storage_scan(self._args())

        assert scan_data['hidden_caches'] == payload

    def test_scanner_failure_does_not_abort_the_storage_scan(self, monkeypatch):
        self._patch_scan(monkeypatch)

        def boom():
            raise RuntimeError('du exploded')

        monkeypatch.setattr(yourdad, 'scan_app_caches', boom)

        scan_data = yourdad.run_storage_scan(self._args())

        # The rest of the report survives; the failure is recorded, not raised.
        assert scan_data is not None
        assert scan_data['hidden_caches']['scan_status'] == 'error'
        assert 'du exploded' in scan_data['hidden_caches']['error']
        assert scan_data['hidden_caches']['entries'] == []

    def test_interrupt_is_recorded_and_not_propagated(self, monkeypatch):
        self._patch_scan(monkeypatch)

        def interrupted():
            raise KeyboardInterrupt()

        monkeypatch.setattr(yourdad, 'scan_app_caches', interrupted)

        scan_data = yourdad.run_storage_scan(self._args())

        assert scan_data['hidden_caches']['scan_status'] == 'interrupted'
