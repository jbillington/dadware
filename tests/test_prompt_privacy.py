"""The AI prompt: new plan-focused intro, ~ paths, and the file-names checkbox."""
import json
import os

import pytest

from renderers import html as html_module
from utils.llm_prompt import generate_storage_prompt

pytestmark = pytest.mark.unit

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def _scan():
    with open(os.path.join(FIXTURES, 'storage_scan.json'), encoding='utf-8') as fh:
        data = json.load(fh)
    return data.get('scan_data', data)


def _scan_with_home(home='/Users/dadtest'):
    scan = _scan()
    scan['home_path'] = home
    scan['top_files'] = [{'path': f'{home}/Movies/trip.mov', 'size_human': '4.0 GB'}]
    scan['top_folders'] = [{'path': f'{home}/Movies', 'path_display': 'Movies', 'size_human': '4.0 GB'}]
    scan['hidden_caches'] = {
        'total_size_human': '1.0 GB', 'folder_count': 1,
        'entries': [{'app_name': 'Arc', 'size_human': '1.0 GB',
                     'path': f'{home}/Library/Caches/Arc'}],
    }
    return scan


def test_intro_asks_for_a_plan_and_never_a_permanent_delete():
    prompt = generate_storage_prompt(_scan(), {}, {})
    assert prompt.startswith('Make a cleanup plan')
    assert 'STEP 1' in prompt and 'STEP 2' in prompt
    assert 'Never permanently delete' in prompt
    assert 'Move to Trash' in prompt
    assert prompt.rstrip().endswith('Start with Step 1 now.')
    assert 'MY QUESTIONS' not in prompt


def test_the_home_folder_never_appears_as_a_path_prefix():
    prompt = generate_storage_prompt(_scan_with_home(), {}, {})
    assert '/Users/dadtest' not in prompt
    assert '~/Movies/trip.mov: 4.0 GB' in prompt
    assert '(~/Library/Caches/Arc)' in prompt


def test_largest_files_can_be_left_out():
    scan = _scan_with_home()
    assert 'trip.mov' in generate_storage_prompt(scan, {}, {})
    without = generate_storage_prompt(scan, {}, {}, include_file_names=False)
    assert 'trip.mov' not in without
    assert 'LARGEST FILES' not in without
    assert 'LARGEST FOLDERS' in without


def test_quick_win_tips_that_name_files_are_not_in_the_prompt():
    prompt = generate_storage_prompt(
        _scan(), {'tips': ['Review large file: secret-taxes.pdf (1 GB)']}, {})
    assert 'secret-taxes.pdf' not in prompt


def test_unseen_section_lists_what_the_scan_missed():
    scan = _scan()
    scan.update(excluded_count=6153, denied_count=9, scan_scope='home_volume')
    prompt = generate_storage_prompt(scan, {}, {})
    assert 'WHAT THIS SCAN COULD NOT SEE' in prompt
    assert '6,153 items were left out on purpose' in prompt
    assert '9 items macOS would not let the scan read' in prompt


def _render(tmp_path, monkeypatch):
    monkeypatch.setattr(html_module, 'get_system_info', lambda: {})
    out = tmp_path / 'r.html'
    html_module.render_html(_scan_with_home(), {'comments': [], 'tips': []}, str(out))
    return out.read_text(encoding='utf-8')


def test_report_has_an_unchecked_file_names_checkbox(tmp_path, monkeypatch):
    html = _render(tmp_path, monkeypatch)
    assert 'id="includeFileNames"' in html
    assert 'id="includeFileNames" checked' not in html
    # Private by default: the visible prompt is the no-file-names version
    visible = html.split('id="llmPrompt" readonly')[1].split('</textarea>')[0]
    assert 'trip.mov' not in visible
    assert 'Include my largest file names' in html
    assert 'syncPromptFileNames' in html


def test_the_two_prompt_versions_differ_only_by_the_files_list(tmp_path, monkeypatch):
    html = _render(tmp_path, monkeypatch)
    full = html.split('id="llmPromptFull" hidden>')[1].split('</textarea>')[0]
    short = html.split('id="llmPromptNoFiles" hidden>')[1].split('</textarea>')[0]
    assert 'trip.mov' in full
    assert 'trip.mov' not in short
