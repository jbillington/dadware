#!/usr/bin/env python3
"""Build the website's sample report from the sanitized sample scan.

Usage:
    ./venv/bin/python scripts/build_sample_report.py
    ./venv/bin/python scripts/build_sample_report.py --open

Renders assets/dadware/sample-scan.json with the current report code and
writes site/sample-report.html (pass --out to
write it elsewhere). Run it again after any report change.

Two things in a report come from the Mac that renders it, not from the scan:
the system specs in the "Ask an AI" prompt, and the date. The specs are
replaced here with a generic Mac, so the published page never describes the
machine that built it. The script then refuses to write the page if it finds
the current user's name, home folder or computer name in it.

sample-scan.json is already sanitized; never replace it with a raw scan.
Dev tool only: not part of the build.
"""
import argparse
import getpass
import json
import os
import re
import socket
import subprocess
import sys
from unittest import mock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import renderers.html as report_html  # noqa: E402
from personality.dad import add_personality  # noqa: E402

SCAN = os.path.join(REPO_ROOT, 'assets', 'dadware', 'sample-scan.json')
OUT = os.path.join(REPO_ROOT, 'site', 'sample-report.html')

# A generic Mac for the AI prompt's spec block. The drive size matches the scan.
SAMPLE_SYSTEM = {
    'model': {'model_name': 'MacBook Air', 'model_identifier': 'Mac14,2', 'year': 'Unknown'},
    'cpu': {'brand': 'Apple M2', 'total_cores': '8', 'physical_cores': '8', 'architecture': 'arm64'},
    'memory': {'total_gb': '8', 'type': 'LPDDR5', 'speed': 'Unknown'},
    'storage': {'drives': ['250.69 GB (250,685,575,168 bytes)']},
    'os': {'version': '14.6', 'version_name': 'Sonoma', 'build': '23G80'},
    'hostname': 'Dads-MacBook-Air',
    'username': 'dad',
}


def leaks(html):
    """Return the identifying strings from this Mac that appear in `html`."""
    home = os.path.expanduser('~')
    found = []
    for needle in {getpass.getuser(), home, socket.gethostname().split('.')[0]}:
        if needle and needle not in ('dad', '/Users/dad') and re.search(re.escape(needle), html, re.I):
            found.append(needle)
    # Any home folder other than the sample's /Users/dad (and /Users/Shared).
    found += sorted(set(re.findall(r'/Users/(?!dad\b|Shared\b)[A-Za-z0-9._-]+', html)))
    return found


def build(scan_path, out_path):
    with open(scan_path, encoding='utf-8') as fh:
        manifest = json.load(fh)
    scan_data = next(iter(manifest['scan_results'].values()))
    personality_data = add_personality(scan_data)
    tmp = out_path + '.tmp'
    with mock.patch.object(report_html, 'get_system_info', return_value=SAMPLE_SYSTEM):
        report_html.render_html(scan_data, personality_data, tmp)
    with open(tmp, encoding='utf-8') as fh:
        html = fh.read()
    found = leaks(html)
    if found:
        os.remove(tmp)
        raise SystemExit(f"Not written: the report contains {len(found)} identifying string(s) from this Mac. "
                         "Fix sample-scan.json or this script.")
    os.replace(tmp, out_path)
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--scan', default=SCAN, help='sanitized scan manifest (default: %(default)s)')
    parser.add_argument('--out', default=OUT, help='where to write the page (default: %(default)s)')
    parser.add_argument('--open', action='store_true', help='open the result in the browser')
    args = parser.parse_args(argv)
    out_path = build(args.scan, args.out)
    print(out_path)
    if args.open:
        subprocess.run(['open', out_path], check=False)
    return 0


if __name__ == '__main__':
    sys.exit(main())
