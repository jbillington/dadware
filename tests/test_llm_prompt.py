"""Tests for utils/llm_prompt.py - the hidden-caches block.

The prompt is embedded in the HTML report, so the golden snapshots in
tests/test_html_render.py already pin its output for scans that carry no
cache data. These tests cover the block this feature added.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.llm_prompt import generate_llm_prompt

SYSTEM_INFO = {
    'model': {'model_name': 'MacBook Pro', 'model_identifier': 'Mac14,9', 'year': '2023'},
    'cpu': {'brand': 'Apple M2 Pro', 'total_cores': '12'},
    'memory': {'total_gb': '16'},
    'os': {'name': 'macOS', 'version': '14.0'},
}

PERSONALITY = {'comments': ['tidy up, kiddo'], 'tips': [], 'status': 'ok'}


def _storage_scan(hidden=None):
    scan = {
        'scan_type': 'storage',
        'volume': '/',
        'volume_info': {'total_human': '500.0 GB', 'used_human': '250.0 GB',
                        'free_human': '250.0 GB', 'used_percent': 50},
        'top_folders': [],
        'top_files': [],
    }
    if hidden is not None:
        scan['hidden_caches'] = hidden
    return scan


def _hidden(**overrides):
    data = {
        'entries': [
            {'app_name': 'Spotify', 'folder_name': 'com.spotify.client',
             'path': '/Users/x/Library/Caches/com.spotify.client',
             'size_bytes': 8 * 1024 ** 3, 'size_human': '8.0 GB'},
        ],
        'total_size_bytes': 11 * 1024 ** 3,
        'total_size_human': '11.0 GB',
        'folder_count': 40,
        'scan_status': 'complete',
    }
    data.update(overrides)
    return data


@pytest.mark.unit
class TestHiddenCachesInPrompt:

    def test_block_absent_without_cache_data(self):
        prompt = generate_llm_prompt(_storage_scan(), PERSONALITY, SYSTEM_INFO)
        assert 'HIDDEN APP CACHES' not in prompt

    def test_block_absent_when_no_entries(self):
        prompt = generate_llm_prompt(_storage_scan(_hidden(entries=[])), PERSONALITY, SYSTEM_INFO)
        assert 'HIDDEN APP CACHES' not in prompt

    def test_block_lists_apps_sizes_and_the_true_total(self):
        prompt = generate_llm_prompt(_storage_scan(_hidden()), PERSONALITY, SYSTEM_INFO)

        assert 'HIDDEN APP CACHES' in prompt
        assert '- Spotify: 8.0 GB' in prompt
        # The total is the measured pile, not the sum of the listed entries,
        # so the model isn't misled about how much is actually there.
        assert '11.0 GB across 40 folders' in prompt

    def test_block_explains_why_these_are_not_in_the_main_listing(self):
        # Without this, the numbers look like they contradict the folder
        # totals above them in the same prompt.
        prompt = generate_llm_prompt(_storage_scan(_hidden()), PERSONALITY, SYSTEM_INFO)
        assert 'the main scan above excludes' in prompt

    def test_at_most_fifteen_entries_are_included(self):
        entries = [
            {'app_name': f'App{i}', 'folder_name': f'App{i}', 'path': f'/p/{i}',
             'size_bytes': 1, 'size_human': '1.0 KB'}
            for i in range(20)
        ]
        prompt = generate_llm_prompt(_storage_scan(_hidden(entries=entries)), PERSONALITY, SYSTEM_INFO)

        assert '- App14: ' in prompt
        assert '- App15: ' not in prompt

    def test_cpu_prompt_is_unaffected(self):
        cpu_scan = {'scan_type': 'cpu', 'total_memory_gb': 16, 'total_used_gb': 8,
                    'memory_pressure': {}, 'memory_hogs': [], 'top_processes': []}
        prompt = generate_llm_prompt(cpu_scan, PERSONALITY, SYSTEM_INFO)
        assert 'HIDDEN APP CACHES' not in prompt
