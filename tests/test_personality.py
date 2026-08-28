"""Tests for personality/dad.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from personality.dad import add_personality

# Decimal GB, matching format_size() and the clutter grade thresholds.
GB = 1000**3


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


class TestCachePersonality:
    """Caches are information, not a grade (docs/GRADING.md). An app filling a
    cache is an app working, and the space comes back on its own - so the dad
    comment must never treat it as a problem the user caused."""

    def _scan(self, cache_bytes, human):
        return {
            'scan_type': 'storage',
            'top_folders': [{'path': '/Users/me/Downloads', 'size_bytes': 1 * GB}],
            'top_files': [],
            'volume_info': {'used_percent': 50},
            'hidden_caches': {'total_size_bytes': cache_bytes, 'total_size_human': human},
        }

    def test_caches_never_escalate_status(self):
        result = add_personality(self._scan(40 * GB, '40.0 GB'))
        # A clean disk with 40 GB of caches is still a clean disk.
        assert result['status'] == 'ok'

    def test_caches_never_produce_a_tip(self):
        """Tips are chores. Clearing a cache is not a chore worth assigning -
        it refills."""
        before = add_personality(self._scan(0, ''))['tips']
        after = add_personality(self._scan(40 * GB, '40.0 GB'))['tips']
        assert before == after

    def test_the_comment_is_additive_not_a_replacement(self):
        """Cache comments come after the default verdict, so a clean scan
        still gets to hear 'looks fine' before being told where the rest went."""
        result = add_personality(self._scan(40 * GB, '40.0 GB'))
        joined = ' '.join(result['comments']).lower()
        assert 'looks fine' in joined
        assert '40.0 gb' in joined

    def test_the_comment_says_it_comes_back(self):
        """The honest half most tools leave out."""
        result = add_personality(self._scan(40 * GB, '40.0 GB'))
        joined = ' '.join(result['comments']).lower()
        assert 'refills' in joined or 'stay gone' in joined

    def test_small_cache_totals_say_nothing(self):
        result = add_personality(self._scan(2 * GB, '2.0 GB'))
        assert not any('cache' in c.lower() for c in result['comments'])

    def test_missing_cache_data_is_harmless(self):
        """Reports from before the cache scanner must read as they always did."""
        scan = self._scan(0, '')
        del scan['hidden_caches']
        result = add_personality(scan)
        assert result['status'] == 'ok'


class TestNotesDoNotCrowdOutTheVerdict:
    """The verdict is capped at two lines. Informational notes are appended
    after that cap, not inside it - otherwise a cache total silently evicts a
    real finding, which is how the snapshot note went missing the first time."""

    def _busy_scan(self):
        return {
            'scan_type': 'storage',
            'top_folders': [{'path': '/Users/me/Downloads', 'size_bytes': 12 * GB}],
            'top_files': [],
            'volume_info': {'used_percent': 85},
            'hidden_caches': {'total_size_bytes': int(20.3 * GB), 'total_size_human': '20.3 GB'},
            'snapshots': {'status': 'complete', 'count': 1,
                          'stale_count': 1, 'oldest_age_days': 168},
        }

    def test_finding_cache_and_snapshot_all_survive(self):
        comments = add_personality(self._busy_scan())['comments']
        joined = ' '.join(comments).lower()
        assert 'downloads' in joined      # the real finding
        assert '20.3 gb' in joined        # the cache note
        assert '168 days' in joined       # the snapshot note

    def test_the_real_finding_comes_first(self):
        comments = add_personality(self._busy_scan())['comments']
        assert 'downloads' in comments[0].lower()

    def test_the_verdict_itself_is_still_capped_at_two(self):
        """Strip the notes away and the old two-line limit must still hold."""
        scan = self._busy_scan()
        scan['top_folders'].append({'path': '/Users/me/Desktop', 'size_bytes': 8 * GB})
        scan['volume_info'] = {'used_percent': 95}   # a third verdict-worthy finding
        del scan['hidden_caches']
        del scan['snapshots']
        assert len(add_personality(scan)['comments']) == 2

    def test_notes_add_at_most_two_lines_of_their_own(self):
        scan = self._busy_scan()
        with_notes = len(add_personality(scan)['comments'])
        scan_bare = self._busy_scan()
        del scan_bare['hidden_caches']
        del scan_bare['snapshots']
        without = len(add_personality(scan_bare)['comments'])
        assert with_notes - without <= 2


class TestSnapshotPersonality:
    def _scan(self, **snapshot):
        base = {'status': 'complete', 'count': 0, 'stale_count': 0, 'oldest_age_days': None}
        base.update(snapshot)
        return {
            'scan_type': 'storage',
            'top_folders': [{'path': '/Users/me/Downloads', 'size_bytes': 1 * GB}],
            'top_files': [],
            'volume_info': {'used_percent': 50},
            'snapshots': base,
        }

    def test_stale_snapshots_are_mentioned_with_their_age(self):
        result = add_personality(self._scan(count=1, stale_count=1, oldest_age_days=168))
        joined = ' '.join(result['comments']).lower()
        assert '168 days' in joined

    def test_a_single_snapshot_reads_as_singular(self):
        result = add_personality(self._scan(count=1, stale_count=1, oldest_age_days=168))
        joined = ' '.join(result['comments']).lower()
        assert '1 copy of itself' in joined

    def test_fresh_snapshots_are_left_alone(self):
        """Time Machine keeps about a day of these. That is the system
        working, not a problem to report."""
        result = add_personality(self._scan(count=3, stale_count=0))
        assert not any('itself' in c.lower() for c in result['comments'])

    def test_snapshots_never_escalate_status(self):
        result = add_personality(self._scan(count=6, stale_count=6, oldest_age_days=200))
        assert result['status'] == 'ok'

    def test_unavailable_snapshot_scan_says_nothing(self):
        result = add_personality(self._scan(status='unavailable', count=0))
        assert not any('itself' in c.lower() for c in result['comments'])


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
