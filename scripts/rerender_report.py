#!/usr/bin/env python3
"""Re-render a saved scan with the current report code, without scanning.

A full scan can take minutes. When you are only changing report copy or CSS,
the saved JSON manifest already holds everything the report needs, so this
renders it again in about a second.

Usage:
    ./venv/bin/python scripts/rerender_report.py test-reports/storage_2026-11-11_10-33.json
    ./venv/bin/python scripts/rerender_report.py MANIFEST.json --open

Writes MANIFEST_rerender.html next to the manifest and leaves the original
report alone. Works for storage and cpu manifests. The "Dad says" comments
and tips are regenerated from the scan data with the current code; the
measurements are the ones in the file. Dev tool only: not part of the build.
"""
import argparse
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from personality.dad import add_personality  # noqa: E402
from renderers.html import render_html  # noqa: E402


def rerender(manifest_path):
    """Render `manifest_path` again and return the path of the new HTML file."""
    with open(manifest_path, encoding='utf-8') as fh:
        manifest = json.load(fh)
    results = manifest.get('scan_results') or {}
    if not results:
        raise ValueError(f"{manifest_path} has no scan_results; is it a saved report manifest?")
    scan_data = next(iter(results.values()))
    personality_data = add_personality(scan_data)
    base, _ = os.path.splitext(manifest_path)
    out_path = f"{base}_rerender.html"
    render_html(scan_data, personality_data, out_path)
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('manifest', help='saved scan manifest (.json) from test-reports/')
    parser.add_argument('--open', action='store_true', help='open the result in the browser')
    args = parser.parse_args(argv)
    try:
        out_path = rerender(args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Could not re-render: {exc}", file=sys.stderr)
        return 1
    print(out_path)
    if args.open:
        subprocess.run(['open', out_path], check=False)
    return 0


if __name__ == '__main__':
    sys.exit(main())
