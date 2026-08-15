"""Characterization ("golden output") tests for renderers/html.py::render_html.

These tests exist to let renderers/html.py be refactored (it's ~2000 lines of
f-string HTML assembly) with confidence that observable behavior hasn't
changed. They intentionally do NOT assert on exact byte-for-byte HTML output
via a plain hash, because render_html() embeds a wall-clock timestamp and
calls utils.system_info.get_system_info() (which shells out to sysctl /
system_profiler / sw_vers and therefore varies by machine). Instead:

  * get_system_info() is monkeypatched to a fixed dict so the "Ask AI About
    This Report" section (which embeds system specs) is deterministic.
  * The one remaining volatile element - the generation date/time printed in
    the page <title> and header - is scrubbed via regex before the
    normalized-snapshot comparison.

What this DOES pin down:
  - The overall HTML skeleton (doctype, balanced html/head/body/style/script)
  - That every folder, subfolder, file and process name from the input data
    makes it into the rendered output somewhere
  - That the report stays fully self-contained (no external http(s) src/href)
  - A full normalized-snapshot diff against tests/fixtures/*.snapshot.html,
    which will catch ANY change to markup, structure, copy, or ordering.

What this does NOT pin down:
  - Exact byte-for-byte output (timestamps and system specs are scrubbed/faked)
  - CSS/visual rendering correctness
  - JS behavior (only that script blocks are balanced/present)
  - Whether the HTML is *safe* - see test_xss_folder_path_is_not_escaped
    below, which documents a known-open injection hole (xfail).
"""
import json
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from renderers.html import render_html

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Fixed stand-in for utils.system_info.get_system_info() so the "Ask AI About
# This Report" section (which embeds Mac model / CPU / OS specs) is identical
# no matter which machine runs the test.
FIXED_SYSTEM_INFO = {
    "model": {
        "model_name": "MacBook Pro",
        "model_identifier": "Mac14,9",
        "year": "2023",
    },
    "cpu": {
        "brand": "Apple M2 Pro",
        "total_cores": "12",
        "physical_cores": "12",
        "architecture": "arm",
    },
    "memory": {"total_gb": "16", "type": "LPDDR5", "speed": "Unknown"},
    "storage": {"drives": ["500.28 GB"]},
    "os": {"version": "14.5", "version_name": "Sonoma", "build": "23F79"},
    "hostname": "test-host",
    "username": "testuser",
}

# Matches things like "August 15, 2026 14:32" or "Aug 15, 2026" - the only
# volatile content render_html() emits once get_system_info() is patched.
DATE_RE = re.compile(r"\b[A-Z][a-z]{2,8} \d{1,2}, \d{4}(?: \d{2}:\d{2})?\b")

EXTERNAL_URL_RE = re.compile(r'(?:href|src)\s*=\s*"(https?://[^"]*)"', re.IGNORECASE)


def scrub(html_text):
    """Replace volatile generation-timestamp text with a fixed placeholder."""
    return DATE_RE.sub("{{DATE}}", html_text)


def _load_fixture(name):
    with open(FIXTURES_DIR / name, encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload["scan_data"], payload["personality_data"]


def _render(monkeypatch, tmp_path, scan_data, personality_data, out_name="report.html"):
    monkeypatch.setattr("renderers.html.get_system_info", lambda: FIXED_SYSTEM_INFO)
    report_path = str(tmp_path / out_name)
    render_html(scan_data, personality_data, report_path)
    with open(report_path, encoding="utf-8") as fh:
        return fh.read()


def regenerate_snapshot(fixture_name, snapshot_name):
    """Render `fixture_name` with the fixed system-info stub, scrub the
    volatile timestamp, and overwrite tests/fixtures/`snapshot_name`.

    Not run automatically. Use this only after confirming a change to
    render_html()'s output is intentional, then inspect the diff (`git diff
    tests/fixtures/`) before committing. Usage:

        ./venv/bin/python -c \\
          "from tests.test_html_render import regenerate_snapshot as r; \\
           r('storage_scan.json', 'storage_scan.snapshot.html')"
    """
    import renderers.html as html_module

    scan_data, personality_data = _load_fixture(fixture_name)
    original_get_system_info = html_module.get_system_info
    html_module.get_system_info = lambda: FIXED_SYSTEM_INFO
    try:
        out_path = FIXTURES_DIR / "_tmp_regenerate.html"
        render_html(scan_data, personality_data, str(out_path))
        rendered = scrub(out_path.read_text(encoding="utf-8"))
        out_path.unlink()
    finally:
        html_module.get_system_info = original_get_system_info

    (FIXTURES_DIR / snapshot_name).write_text(rendered, encoding="utf-8")


def _iter_paths_and_names(scan_data):
    """Yield every folder path/path_display and file basename embedded in a
    storage or cpu scan_data fixture, for "did it make it into the HTML"
    checks."""
    names = []
    if scan_data.get("scan_type") == "storage":
        for folder in scan_data.get("top_folders", []):
            names.append(folder.get("path_display", ""))
            names.append(folder.get("path", ""))
            for sub in folder.get("subfolders", []):
                names.append(sub.get("path_display", ""))
            for file_info in folder.get("top_files", []):
                names.append(os.path.basename(file_info.get("path", "")))
        for file_info in scan_data.get("top_files", []):
            names.append(os.path.basename(file_info.get("path", "")))
    if scan_data.get("scan_type") == "cpu":
        for proc in scan_data.get("top_processes", []):
            names.append(proc.get("name", ""))
        for proc in scan_data.get("top_memory_processes", []):
            names.append(proc.get("name", ""))
        for hog in scan_data.get("memory_hogs", []):
            names.append(hog.get("name", ""))
    return [n for n in names if n]


# ---------------------------------------------------------------------------
# Structural assertions, run against both fixtures
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fixture_name", ["storage_scan.json", "cpu_scan.json"])
class TestStructuralProperties:
    def test_output_is_nonempty_and_well_formed_skeleton(self, monkeypatch, tmp_path, fixture_name):
        scan_data, personality_data = _load_fixture(fixture_name)
        html = _render(monkeypatch, tmp_path, scan_data, personality_data)

        assert html.strip() != ""
        assert html.startswith("<!DOCTYPE html>")

        for open_tag, close_tag in [
            ("<html", "</html>"),
            ("<head>", "</head>"),
            ("<body>", "</body>"),
            ("<style>", "</style>"),
            ("<script>", "</script>"),
        ]:
            assert html.count(open_tag) == html.count(close_tag) == 1, (
                f"{fixture_name}: unbalanced {open_tag}/{close_tag} "
                f"({html.count(open_tag)} open, {html.count(close_tag)} close)"
            )

    def test_all_fixture_names_and_paths_appear_in_output(self, monkeypatch, tmp_path, fixture_name):
        scan_data, personality_data = _load_fixture(fixture_name)
        html = _render(monkeypatch, tmp_path, scan_data, personality_data)

        for name in _iter_paths_and_names(scan_data):
            assert name in html, f"{fixture_name}: expected {name!r} to appear in rendered HTML"

    def test_report_is_self_contained_no_external_hosts(self, monkeypatch, tmp_path, fixture_name):
        scan_data, personality_data = _load_fixture(fixture_name)
        html = _render(monkeypatch, tmp_path, scan_data, personality_data)

        external = EXTERNAL_URL_RE.findall(html)
        assert external == [], f"{fixture_name}: found external http(s) references: {external}"

    def test_key_section_headings_present(self, monkeypatch, tmp_path, fixture_name):
        scan_data, personality_data = _load_fixture(fixture_name)
        html = _render(monkeypatch, tmp_path, scan_data, personality_data)

        assert "DAD'S REPORT CARD" in html
        assert "NEXT STEPS" in html
        assert "Ask AI About This Report" in html
        if scan_data.get("scan_type") == "storage":
            assert "Storage Report Card" in html
            assert "Home Folders" in html
            assert "Top Largest Files" in html
            assert "Permission Notice" in html  # fixture has has_access: False
        if scan_data.get("scan_type") == "cpu":
            assert "CPU & RAM Snapshot" in html
            assert "Apps Using Most Memory" in html
            assert "Top CPU Usage" in html


# ---------------------------------------------------------------------------
# Permission branch: with vs without Full Disk Access
# ---------------------------------------------------------------------------

def test_permission_warning_absent_when_access_granted(monkeypatch, tmp_path):
    scan_data, personality_data = _load_fixture("storage_scan.json")
    # The committed fixture exercises the "no access" branch; flip it here to
    # exercise the "has access" branch without needing a second fixture file.
    scan_data = json.loads(json.dumps(scan_data))  # cheap deep copy
    scan_data["permission_status"] = {"has_access": True, "missing_permissions": []}

    html = _render(monkeypatch, tmp_path, scan_data, personality_data)
    assert "Permission Notice" not in html


def test_permission_warning_present_when_access_denied(monkeypatch, tmp_path):
    scan_data, personality_data = _load_fixture("storage_scan.json")
    html = _render(monkeypatch, tmp_path, scan_data, personality_data)
    assert "Permission Notice" in html
    assert "Messages" in html and "Mail" in html  # titled missing_permissions


# ---------------------------------------------------------------------------
# Normalized-snapshot comparison
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "fixture_name,snapshot_name",
    [
        ("storage_scan.json", "storage_scan.snapshot.html"),
        ("cpu_scan.json", "cpu_scan.snapshot.html"),
    ],
)
def test_normalized_snapshot_matches(monkeypatch, tmp_path, fixture_name, snapshot_name):
    scan_data, personality_data = _load_fixture(fixture_name)
    html = scrub(_render(monkeypatch, tmp_path, scan_data, personality_data))

    regen_cmd = (
        "./venv/bin/python -c \"from tests.test_html_render import "
        f"regenerate_snapshot as r; r('{fixture_name}', '{snapshot_name}')\""
    )

    snapshot_path = FIXTURES_DIR / snapshot_name
    if not snapshot_path.exists():
        pytest.fail(
            f"Snapshot {snapshot_path} does not exist. To create it (only do "
            f"this after confirming the current output is intentional and "
            f"inspecting it by eye), run:\n\n    {regen_cmd}\n\n"
            f"then review the new file with `git diff` / `git status` before "
            f"relying on it."
        )

    expected = snapshot_path.read_text(encoding="utf-8")
    assert html == expected, (
        f"Rendered HTML for {fixture_name} no longer matches the stored "
        f"snapshot at {snapshot_path}. If this change is INTENTIONAL "
        f"(e.g. part of the planned refactor and you've manually verified "
        f"the new output is equivalent), regenerate the snapshot with:\n\n"
        f"    {regen_cmd}\n\n"
        f"then review the diff carefully before committing the updated "
        f"snapshot - it is the source of truth for 'did the refactor change "
        f"behavior?'."
    )


# ---------------------------------------------------------------------------
# Known-open XSS hole (expected to fail until html.escape() is added)
# ---------------------------------------------------------------------------

def _minimal_storage_scan_with_path(malicious_path_display, malicious_file_path):
    """Build the smallest storage scan_data that exercises both the folder
    bar (title/segment-label attributes+text) and the top files table
    (link text + JS onclick strings), using an attacker-controlled path."""
    size_bytes = 1234
    return {
        "scan_type": "storage",
        "volume": "/Users/testuser",
        "top_folders": [
            {
                "path": f"/Users/testuser/{malicious_path_display}",
                "path_display": malicious_path_display,
                "size_bytes": size_bytes,
                "size_human": "1.2 KB",
                "subfolders": [],
                "top_files": [
                    {
                        "path": malicious_file_path,
                        "size_bytes": size_bytes,
                        "size_human": "1.2 KB",
                    }
                ],
            }
        ],
        "top_files": [
            {
                "path": malicious_file_path,
                "size_bytes": size_bytes,
                "size_human": "1.2 KB",
            }
        ],
        "volume_info": {
            "total_bytes": 100 * 1024 ** 3,
            "used_bytes": 50 * 1024 ** 3,
            "free_bytes": 50 * 1024 ** 3,
            "used_percent": 50.0,
            "free_percent": 50.0,
            "total_human": "100.0 GB",
            "used_human": "50.0 GB",
            "free_human": "50.0 GB",
        },
        "home_folders_total_bytes": size_bytes,
        "metrics": {
            "sum_top_10_folders_human": "1.2 KB",
            "sum_top_25_files_human": "1.2 KB",
            "reclaimable_percent": 0.1,
        },
        "mac_libraries": {},
        "permission_status": {"has_access": True, "missing_permissions": []},
    }


def test_dangerous_paths_are_escaped(monkeypatch, tmp_path):
    """render_html() must html.escape() folder/file paths before interpolating
    them into HTML text and attributes. A folder (or file) whose name
    contains markup must not be emitted verbatim - this used to be an
    injection hole for anyone who can influence a scanned filename (e.g. a
    downloaded file named to look like a script tag).

    This was previously an xfail (see docs/CODE-REVIEW.md section 4); now
    that renderers/html.py routes dynamic path/name values through
    html.escape(), it's a plain regression test.
    """
    payload = '<script>alert(1)</script>"'
    scan_data = _minimal_storage_scan_with_path(payload, f"/Users/testuser/evil/{payload}.txt")
    personality_data = {"status": "ok", "comments": [], "tips": []}

    html = _render(monkeypatch, tmp_path, scan_data, personality_data)

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html

    # Attribute-context payload: an unescaped double-quote would close the
    # HTML attribute it's sitting in early, letting the text that follows
    # become a live (unquoted) event-handler attribute of its own.
    attr_payload = 'evil" onmouseover="alert(1)'
    attr_scan_data = _minimal_storage_scan_with_path(
        attr_payload, f"/Users/testuser/{attr_payload}.txt"
    )
    attr_html = _render(
        monkeypatch, tmp_path, attr_scan_data, personality_data, out_name="attr_report.html"
    )

    assert 'evil" onmouseover="alert(1)' not in attr_html
    assert "&quot;" in attr_html
