"""Bug #10 (Library rows) and the report-card coverage gap."""

import pytest

from renderers import html as html_renderer
from scanners.hidden_storage import friendly_app_name
from utils.llm_prompt import describe_coverage, generate_storage_prompt
from utils.path_utils import folder_label, left_out_note

pytestmark = pytest.mark.unit

HOME = '/Users/dad'


def test_home_and_system_library_get_different_labels():
    home_lib = {'path': '/Users/dad/Library', 'path_display': 'Library'}
    sys_lib = {'path': '/Library', 'path_display': 'Library'}
    assert folder_label(home_lib, HOME) == '~/Library'
    assert folder_label(sys_lib, HOME) == '/Library'


def test_label_leaves_volume_rows_alone():
    row = {'path': '/Volumes/X/opt', 'path_display': 'opt'}
    assert folder_label(row, HOME) == 'opt'


def test_library_rows_say_what_they_leave_out():
    note = left_out_note({'path': '/Users/dad/Library'})
    assert 'Messages' in note and 'Mail' in note and 'Caches' in note
    assert left_out_note({'path': '/Users/dad/Downloads'}) is None


def test_prompt_lists_the_exclusion_under_library():
    scan = {'top_folders': [{'path': '/Users/dad/Library', 'size_human': '36 GB'}],
            'home_path': HOME, 'volume_info': {}}
    prompt = generate_storage_prompt(scan, {}, {})
    assert '~/Library: 36 GB' in prompt
    assert 'Not included: Messages, Mail and Caches' in prompt


def test_messages_cache_is_not_called_messages():
    assert friendly_app_name('com.apple.mobilesms') == 'Messages cache'


def test_coverage_names_excluded_and_denied_items():
    text = describe_coverage({'excluded_count': 6137, 'denied_count': 9})
    assert '6,137' in text and '9 items macOS would not' in text
    assert describe_coverage({'excluded_count': 0, 'denied_count': 0}) == ''


def test_html_report_shows_coverage_and_library_note():
    assert 'left out on purpose' in html_renderer.render_scan_coverage(
        {'excluded_count': 5, 'denied_count': 0})
    assert html_renderer.render_scan_coverage({}) == ''
    assert 'Not included' in html_renderer.render_left_out_note({'path': '/Library'})
