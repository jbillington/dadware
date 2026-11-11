"""scripts/render_scenarios.py: every report state renders, and badges stay legible."""
import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts'))
import render_scenarios  # noqa: E402
from personality.dad import add_personality  # noqa: E402
from renderers import html as html_module  # noqa: E402

pytestmark = pytest.mark.unit

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')
NAMES = [name for name, _, _ in render_scenarios.SCENARIOS]


def _fixture_scan():
    with open(os.path.join(FIXTURES, 'storage_scan.json'), encoding='utf-8') as fh:
        data = json.load(fh)
    return data.get('scan_data', data)


def _render(name, tmp_path, monkeypatch):
    monkeypatch.setattr(html_module, 'get_system_info', lambda: {})
    (_, _, variant), = render_scenarios.build_scenarios(_fixture_scan(), only={name})
    out = tmp_path / f'{name}.html'
    html_module.render_html(variant, add_personality(variant), str(out))
    return out.read_text(encoding='utf-8')


@pytest.mark.parametrize('name', NAMES)
def test_every_scenario_renders(name, tmp_path, monkeypatch):
    page = _render(name, tmp_path, monkeypatch)
    assert '<html' in page and '</html>' in page


def test_scenarios_show_the_states_they_claim(tmp_path, monkeypatch):
    errors = _render('libraries-errors', tmp_path, monkeypatch)
    assert '(error)' in errors and '(skipped: time-limited)' in errors
    assert 'needs Full Disk Access' in _render('no-full-disk-access', tmp_path, monkeypatch)
    drive = _render('other-volume', tmp_path, monkeypatch)
    assert 'Grade Breakdown' not in drive
    assert 'Grade Breakdown' in _render('as-scanned', tmp_path, monkeypatch)


def test_scenarios_do_not_change_the_scan_they_start_from():
    scan = _fixture_scan()
    before = json.dumps(scan, sort_keys=True, default=str)
    render_scenarios.build_scenarios(scan)
    assert json.dumps(scan, sort_keys=True, default=str) == before


def _luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contrast(fg, bg):
    hi, lo = sorted((_luminance(fg), _luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize('name', ['libraries-errors', 'libraries-interrupted', 'no-full-disk-access'])
def test_library_status_badges_are_legible(name, tmp_path, monkeypatch):
    """The badges once drew grey and red text straight onto the purple card
    (contrast about 1.1 to 1.6). They are pills with their own background now;
    this holds them to the 4.5:1 minimum."""
    page = _render(name, tmp_path, monkeypatch)
    badges = re.findall(r'<span style="([^"]*border-radius: 10px[^"]*)">', page)
    assert badges, f'{name} rendered no status badges'
    for style in badges:
        fg = re.search(r'(?<!-)color: (#[0-9a-fA-F]{6})', style).group(1)
        bg = re.search(r'background: (#[0-9a-fA-F]{6})', style).group(1)
        assert _contrast(fg, bg) >= 4.5, f'{style} is only {_contrast(fg, bg):.1f}:1'


def test_only_keeps_the_other_scenarios_in_the_index(tmp_path):
    scan = _fixture_scan()
    manifest = tmp_path / 'storage_x.json'
    manifest.write_text(json.dumps({'scan_results': {'storage': scan}}), encoding='utf-8')
    out = tmp_path / 'out'
    render_scenarios.render_all(str(manifest), str(out))
    index_path, written = render_scenarios.render_all(str(manifest), str(out), only={'other-volume'})
    assert len(written) == 1
    index = open(index_path, encoding='utf-8').read()
    assert 'other-volume.html' in index and 'as-scanned.html' in index
