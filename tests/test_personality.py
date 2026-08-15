"""Tests for personality/yourdad.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from personality.yourdad import add_personality

GB = 1024**3


class TestStoragePersonality:
    def test_clean_system_is_ok(self):
        scan_data = {
            'scan_type': 'storage',
            'top_folders': [
                {'path': '/Users/me/Downloads', 'size_bytes': 1 * GB},
            ],
            'top_files': [],
            'volume_info': {'used_percent': 50},
        }
        result = add_personality(scan_data)
        assert result['status'] == 'ok'
        assert len(result['comments']) >= 1

    def test_large_downloads_triggers_warn(self):
        scan_data = {
            'scan_type': 'storage',
            'top_folders': [
                {'path': '/Users/me/Downloads', 'size_bytes': 12 * GB},
            ],
            'top_files': [],
            'volume_info': {'used_percent': 50},
        }
        result = add_personality(scan_data)
        assert result['status'] == 'warn'
        assert any('downloads' in c.lower() for c in result['comments'])

    def test_large_desktop_triggers_warn(self):
        scan_data = {
            'scan_type': 'storage',
            'top_folders': [
                {'path': '/Users/me/Desktop', 'size_bytes': 8 * GB},
            ],
            'top_files': [],
            'volume_info': {'used_percent': 50},
        }
        result = add_personality(scan_data)
        assert result['status'] == 'warn'
        assert any('desktop' in c.lower() for c in result['comments'])

    def test_low_free_space_is_critical(self):
        scan_data = {
            'scan_type': 'storage',
            'top_folders': [],
            'top_files': [],
            'volume_info': {'used_percent': 95},
        }
        result = add_personality(scan_data)
        assert result['status'] == 'critical'

    def test_comments_limited_to_two(self):
        scan_data = {
            'scan_type': 'storage',
            'top_folders': [
                {'path': '/Users/me/Downloads', 'size_bytes': 12 * GB},
                {'path': '/Users/me/Desktop', 'size_bytes': 8 * GB},
            ],
            'top_files': [],
            'volume_info': {'used_percent': 95},
        }
        result = add_personality(scan_data)
        assert len(result['comments']) <= 2

    def test_tips_limited_to_five(self):
        scan_data = {
            'scan_type': 'storage',
            'top_folders': [
                {'path': '/Users/me/Downloads', 'size_bytes': 12 * GB},
                {'path': '/Users/me/Desktop', 'size_bytes': 8 * GB},
            ],
            'top_files': [],
            'volume_info': {'used_percent': 95},
        }
        result = add_personality(scan_data)
        assert len(result['tips']) <= 5

    def test_junk_path_does_not_trigger_downloads_warning(self):
        # Regression: a folder whose path merely contains the word
        # 'Downloads' (e.g. an archive folder) must not be mistaken for the
        # real Downloads folder, which is small here.
        scan_data = {
            'scan_type': 'storage',
            'top_folders': [
                {'path': '/Users/me/Downloads', 'size_bytes': 1 * GB},
                {'path': '/Users/me/Backups/Old-Downloads-Archive', 'size_bytes': 20 * GB},
            ],
            'top_files': [],
            'volume_info': {'used_percent': 50},
        }
        result = add_personality(scan_data)
        assert result['status'] == 'ok'
        assert not any('downloads' in c.lower() for c in result['comments'])

    def test_junk_path_does_not_trigger_desktop_warning(self):
        scan_data = {
            'scan_type': 'storage',
            'top_folders': [
                {'path': '/Users/me/Documents-old', 'size_bytes': 20 * GB},
            ],
            'top_files': [],
            'volume_info': {'used_percent': 50},
        }
        result = add_personality(scan_data)
        assert result['status'] == 'ok'
        assert not any('desktop' in c.lower() for c in result['comments'])


class TestCpuPersonality:
    def test_healthy_system_is_ok(self):
        scan_data = {
            'scan_type': 'cpu',
            'top_processes': [],
            'memory_hogs': [],
            'memory_pressure': {'pressure': 'low', 'free_gb': 4.0},
            'total_memory_gb': 16,
            'total_used_gb': 8,
            'process_metrics': {},
        }
        result = add_personality(scan_data)
        assert result['status'] == 'ok'

    def test_high_memory_pressure_is_critical(self):
        scan_data = {
            'scan_type': 'cpu',
            'top_processes': [],
            'memory_hogs': [
                {'name': 'Chrome', 'total_mb': 4096, 'process_count': 20},
            ],
            'memory_pressure': {'pressure': 'high', 'free_gb': 0.5},
            'total_memory_gb': 16,
            'total_used_gb': 15.5,
            'process_metrics': {},
        }
        result = add_personality(scan_data)
        assert result['status'] == 'critical'

    def test_chrome_hog_triggers_comment(self):
        scan_data = {
            'scan_type': 'cpu',
            'top_processes': [],
            'memory_hogs': [
                {'name': 'Chrome', 'total_mb': 4096, 'process_count': 30},
            ],
            'memory_pressure': {'pressure': 'low', 'free_gb': 4.0},
            'total_memory_gb': 16,
            'total_used_gb': 8,
            'process_metrics': {},
        }
        result = add_personality(scan_data)
        assert any('chrome' in c.lower() for c in result['comments'])

    def test_unknown_scan_type(self):
        scan_data = {'scan_type': 'unknown'}
        result = add_personality(scan_data)
        assert result['status'] == 'ok'
        assert len(result['comments']) >= 1
