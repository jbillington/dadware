"""scripts/rerender_report.py turns a saved manifest back into a report."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts'))
import rerender_report  # noqa: E402

pytestmark = pytest.mark.unit

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def _manifest(tmp_path, fixture, key):
    with open(os.path.join(FIXTURES, fixture), encoding='utf-8') as fh:
        scan_data = json.load(fh)
    scan_data = scan_data.get('scan_data', scan_data)
    path = tmp_path / f'{key}_2026-01-01_00-00.json'
    path.write_text(json.dumps({'scan_results': {key: scan_data}}), encoding='utf-8')
    return str(path)


def test_writes_a_rerender_file_next_to_the_manifest(tmp_path):
    manifest = _manifest(tmp_path, 'storage_scan.json', 'storage')
    out = rerender_report.rerender(manifest)
    assert out == manifest[:-5] + '_rerender.html'
    html = open(out, encoding='utf-8').read()
    assert 'Top 10 Home Folders' in html


def test_a_manifest_without_results_is_an_error(tmp_path):
    bad = tmp_path / 'empty.json'
    bad.write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError):
        rerender_report.rerender(str(bad))
    assert rerender_report.main([str(bad)]) == 1
