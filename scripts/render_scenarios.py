#!/usr/bin/env python3
"""Render one saved scan as many different report states, to look at them all.

A real scan only shows the states that Mac happened to be in. Errors, skipped
libraries, missing permissions, a nearly full disk and a thumb-drive report
are the cases most likely to hide a layout or contrast problem, and they are
the ones you rarely see. This takes ONE saved manifest, bends a copy of its
data into each state, renders every one, and writes an index page linking
them all.

Usage:
    ./venv/bin/python scripts/render_scenarios.py test-reports/storage_2026-11-11_10-33.json
    ./venv/bin/python scripts/render_scenarios.py MANIFEST.json --open
    ./venv/bin/python scripts/render_scenarios.py MANIFEST.json --only libraries-errors,other-volume

Output goes to <manifest folder>/scenarios/<manifest name>/ (test-reports/ is
git-ignored, which matters: a real manifest holds real file names and paths).
The scenarios are built from the data, so the numbers are the scan's own. They
are synthetic states, not scans: they check how the report LOOKS, not what a
scan would find. Dev tool only: not part of the build.
"""
import argparse
import copy
import html
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from personality.dad import add_personality  # noqa: E402
from renderers.html import render_html  # noqa: E402


def _human(num_bytes):
    value = float(num_bytes)
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if value < 1000 or unit == 'TB':
            return f"{value:.1f} {unit}"
        value /= 1000


def _is_trash_row(folder):
    path = folder.get('path') or ''
    return path.endswith('/.Trash') or folder.get('path_display') == 'Trash'


def _under_home(path, home):
    return bool(home) and (path == home or path.startswith(home.rstrip('/') + '/'))


def _set_disk(scan, used_percent):
    info = scan.setdefault('volume_info', {})
    total = info.get('total_bytes') or 250 * 1000 ** 3
    used = int(total * used_percent / 100)
    info.update(
        total_bytes=total, used_bytes=used, free_bytes=total - used,
        used_percent=float(used_percent), free_percent=100.0 - used_percent,
        total_human=_human(total), used_human=_human(used), free_human=_human(total - used),
    )


def _libraries(scan):
    return scan.setdefault('mac_libraries', {})


def _library_statuses(scan, statuses, scan_status='partial'):
    libs = _libraries(scan)
    for key, fields in statuses.items():
        entry = libs.setdefault(key, {'type': key})
        entry.update(fields)
    libs['scan_status'] = scan_status


def _drop_trash(scan):
    scan['top_folders'] = [f for f in scan.get('top_folders', []) if not _is_trash_row(f)]


# Each scenario: (name, what it shows, function that edits a copy of the scan).
SCENARIOS = []


def scenario(name, description):
    def register(fn):
        SCENARIOS.append((name, description, fn))
        return fn
    return register


@scenario('as-scanned', 'The scan exactly as saved, for comparison.')
def _as_scanned(scan):
    pass


@scenario('libraries-errors', 'Music and Creative Apps skipped (time-limited), Mail errored: the grey, red '
                              'and amber library badges and the Partial Scan notice.')
def _libraries_errors(scan):
    _library_statuses(scan, {
        'music': {'status': 'skipped', 'reason': 'time-limited'},
        'mail': {'status': 'error', 'error': 'simulated'},
        'creative': {'status': 'skipped', 'reason': 'time-limited'},
    }, 'partial')


@scenario('libraries-interrupted', 'The library scan was interrupted part way.')
def _libraries_interrupted(scan):
    _library_statuses(scan, {
        'music': {'status': 'skipped', 'reason': 'scan-interrupted'},
        'messages': {'status': 'interrupted'},
        'creative': {'status': 'skipped', 'reason': 'scan-interrupted'},
    }, 'interrupted')


@scenario('no-full-disk-access', 'Full Disk Access missing: libraries marked "needs Full Disk Access" and an '
                                 'unmeasured Trash.')
def _no_fda(scan):
    scan['permission_status'] = {
        'has_access': False,
        'missing_permissions': ['messages', 'mail', 'photos'],
        'details': {k: {'has_access': False, 'reason': 'permission denied'}
                    for k in ('messages', 'mail', 'photos')},
        'folders': {},
    }
    trash = scan.setdefault('trash', {'scan_type': 'trash', 'locations': []})
    trash.update(permission_denied=True, status='no_permission', total_size_bytes=0,
                 total_size_human='0 B', item_count=None, oldest_age_days=None)
    _drop_trash(scan)


@scenario('denied-folders', 'The user clicked Don\'t Allow for Desktop and Downloads.')
def _denied_folders(scan):
    perms = scan.setdefault('permission_status', {'has_access': True, 'missing_permissions': []})
    home = scan.get('home_path') or '~'
    perms['folders'] = {
        'Desktop': {'status': 'denied', 'path': f'{home}/Desktop'},
        'Documents': {'status': 'granted', 'path': f'{home}/Documents'},
        'Downloads': {'status': 'denied', 'path': f'{home}/Downloads'},
    }


@scenario('disk-critical', 'Disk 98% full: failing grades and the urgent Dad says lines.')
def _critical(scan):
    _set_disk(scan, 98)


@scenario('disk-healthy', 'Disk 30% full with an empty Trash and no caches: the clean-Mac copy.')
def _healthy(scan):
    _set_disk(scan, 30)
    _drop_trash(scan)
    scan['trash'] = {'scan_type': 'trash', 'locations': [], 'total_size_bytes': 0,
                     'total_size_human': '0 B', 'item_count': 0, 'oldest_age_days': None,
                     'permission_denied': False, 'status': 'complete'}
    scan.pop('hidden_caches', None)


@scenario('huge-trash', 'A 120 GB Trash: the Trash tile, the folder bar and the Dad says line.')
def _huge_trash(scan):
    big = 120 * 1000 ** 3
    trash = scan.setdefault('trash', {'scan_type': 'trash', 'locations': [{}]})
    for loc in trash.get('locations') or [{}]:
        loc.update(size_bytes=big, size_human=_human(big), status='measured')
    trash.update(total_size_bytes=big, total_size_human=_human(big), permission_denied=False,
                 status='complete')
    for folder in scan.get('top_folders', []):
        if _is_trash_row(folder):
            folder.update(size_bytes=big, size_human=_human(big))


@scenario('no-other-folders', 'Only home folders in the scan: the Other Folders bar has nothing to show.')
def _no_other(scan):
    home = scan.get('home_path') or ''
    scan['top_folders'] = [f for f in scan.get('top_folders', [])
                           if _under_home(f.get('path') or '', home)]


@scenario('few-folders', 'Four folders in total, so each bar is far short of ten.')
def _few_folders(scan):
    scan['top_folders'] = scan.get('top_folders', [])[:4]


@scenario('snapshots-fresh', 'One Time Machine snapshot from a few hours ago (nothing stale).')
def _snap_fresh(scan):
    scan['snapshots'] = {'scan_type': 'snapshots', 'status': 'complete', 'source': 'tmutil',
                         'snapshots': [{'name': 'com.apple.TimeMachine.fresh.local',
                                        'created': '2026-01-01T00:00:00', 'age_days': 0,
                                        'is_os_update': False, 'purgeable': True}],
                         'count': 1, 'os_update_count': 0, 'stale_count': 0,
                         'purgeable_count': 1, 'oldest_age_days': 0}


@scenario('snapshots-os-only', 'Only macOS update snapshots, which are not the user\'s to clear.')
def _snap_os(scan):
    scan['snapshots'] = {'scan_type': 'snapshots', 'status': 'complete', 'source': 'tmutil',
                         'snapshots': [{'name': 'com.apple.os.update-ABC', 'created': '2026-01-01T00:00:00',
                                        'age_days': 3, 'is_os_update': True, 'purgeable': False}],
                         'count': 1, 'os_update_count': 1, 'stale_count': 0,
                         'purgeable_count': 0, 'oldest_age_days': 3}


@scenario('no-snapshots-or-caches', 'The scan found no snapshots and no app caches.')
def _no_snap_cache(scan):
    scan.pop('snapshots', None)
    scan.pop('hidden_caches', None)


@scenario('nothing-left-out', 'No excluded and no blocked items, so no "could not see" lines in the AI prompt.')
def _nothing_left_out(scan):
    scan['excluded_count'] = 0
    scan['denied_count'] = 0


@scenario('other-volume', 'A thumb drive or other disk: the drive-only report with no grade.')
def _other_volume(scan):
    home = scan.get('home_path') or ''
    scan['scan_scope'] = 'other_volume'
    scan['volume'] = '/Volumes/BACKUP'
    scan['top_folders'] = [f for f in scan.get('top_folders', [])
                           if not _under_home(f.get('path') or '', home)][:10]
    for key in ('home_path', 'permission_status', 'mac_libraries', 'hidden_caches',
                'snapshots', 'trash', 'home_folders_total_bytes', 'home_folders_total_human'):
        scan.pop(key, None)


def build_scenarios(scan, only=None):
    """Return [(name, description, scan_copy)] for every (or the chosen) scenario."""
    chosen = []
    for name, description, edit in SCENARIOS:
        if only and name not in only:
            continue
        variant = copy.deepcopy(scan)
        edit(variant)
        chosen.append((name, description, variant))
    return chosen


def render_all(manifest_path, out_dir=None, only=None):
    """Render every scenario for `manifest_path`; return (index_path, [(name, path)])."""
    with open(manifest_path, encoding='utf-8') as fh:
        manifest = json.load(fh)
    results = manifest.get('scan_results') or {}
    scan = next(iter(results.values()), None)
    if not scan or scan.get('scan_type') != 'storage':
        raise ValueError(f"{manifest_path} is not a saved storage scan manifest")
    stem = os.path.splitext(os.path.basename(manifest_path))[0]
    out_dir = out_dir or os.path.join(os.path.dirname(os.path.abspath(manifest_path)), 'scenarios', stem)
    os.makedirs(out_dir, exist_ok=True)

    written, rows = [], []
    for name, description, variant in build_scenarios(scan, only):
        path = os.path.join(out_dir, f'{name}.html')
        render_html(variant, add_personality(variant), path)
        written.append((name, path))
        rows.append(f'<li><a href="{html.escape(name)}.html">{html.escape(name)}</a>'
                    f' <span>{html.escape(description)}</span></li>')
    index_path = os.path.join(out_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as fh:
        fh.write(f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Report scenarios: {html.escape(stem)}</title>
<style>body{{font:15px/1.5 -apple-system,Helvetica,sans-serif;margin:30px;max-width:900px}}
li{{margin:8px 0}}li span{{color:#555}}a{{font-weight:600}}</style></head><body>
<h1>Report scenarios</h1><p>Built from <code>{html.escape(stem)}</code>. Synthetic states of one scan:
they show how the report looks, not what a scan would find.</p>
<ul>{''.join(rows)}</ul></body></html>""")
    return index_path, written


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('manifest', help='saved storage scan manifest (.json)')
    parser.add_argument('--out', help='output folder (default: scenarios/<name> beside the manifest)')
    parser.add_argument('--only', help='comma-separated scenario names')
    parser.add_argument('--open', action='store_true', help='open the index page when done')
    args = parser.parse_args(argv)
    only = set(args.only.split(',')) if args.only else None
    try:
        index_path, written = render_all(args.manifest, args.out, only)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Could not render scenarios: {exc}", file=sys.stderr)
        return 1
    print(f"Rendered {len(written)} scenarios. Index: {index_path}")
    if args.open:
        subprocess.run(['open', index_path], check=False)
    return 0


if __name__ == '__main__':
    sys.exit(main())
