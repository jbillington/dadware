#!/usr/bin/env python3
"""Validation spike for the purgeable-space data source (HIDDEN-STORAGE-PLAN 1c).

Run this on a Mac that has visible purgeable space, then compare the numbers
below against what Finder and Storage Settings show.

WHY THIS EXISTS
---------------
Purgeable space is roughly (what Finder calls free) - (what statvfs calls
free). The catch is that Finder's number comes from Apple's
NSURLVolumeAvailableCapacityForImportantUsageKey API, which has no
documented CLI equivalent. `diskutil info`'s APFSContainerFree very likely
reports actually-free space - the same thing statvfs reports - in which case
the delta is ~0 and the feature would silently tell every user "nothing
purgeable here". `system_profiler SPStorageDataType` *may* mirror Finder's
number, but that is not documented either.

So 1c is gated on this: whichever source actually diverges from statvfs is
the one to build on. If none of them diverge, the honest move is to ship
snapshot count and age with copy that says macOS hides the exact figure,
rather than inventing a number.

This script is read-only. It runs statvfs, diskutil, system_profiler and
tmutil, and changes nothing.

    python3 scripts/purgeable_spike.py
"""

import json
import os
import plistlib
import subprocess
import sys

# On modern macOS `/` is the sealed, read-only System volume (itself mounted
# from a snapshot); the user's data and its local Time Machine snapshots live
# on the Data volume. Both are checked because they answer differently.
VOLUMES = ['/', '/System/Volumes/Data']

TIMEOUT = 30  # system_profiler can genuinely take several seconds


def human(num_bytes):
    if num_bytes is None:
        return 'n/a'
    size = float(num_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size) < 1024.0:
            return f'{size:.2f} {unit}'
        size /= 1024.0
    return f'{size:.2f} PB'


def run(cmd):
    """Run a command, returning (stdout_bytes, error_string)."""
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=TIMEOUT)
    except FileNotFoundError:
        return None, f'{cmd[0]} not found (are you on macOS?)'
    except subprocess.TimeoutExpired:
        return None, f'timed out after {TIMEOUT}s'
    except OSError as exc:
        return None, str(exc)

    if result.returncode != 0:
        err = (result.stderr or b'').decode('utf-8', 'replace').strip()
        return None, err or f'exit code {result.returncode}'
    return result.stdout, None


def statvfs_free(path):
    """What the POSIX API thinks is free: the conservative number."""
    try:
        st = os.statvfs(path)
    except OSError as exc:
        return None, str(exc)
    return st.f_bavail * st.f_frsize, None


def diskutil_numbers(path):
    """Every byte-count key diskutil reports, so nothing is missed."""
    stdout, err = run(['/usr/sbin/diskutil', 'info', '-plist', path])
    if err:
        return {}, err
    try:
        info = plistlib.loads(stdout)
    except Exception as exc:  # noqa: BLE001 - spike script, report and move on
        return {}, f'could not parse plist: {exc}'

    interesting = {}
    for key, value in info.items():
        if isinstance(value, int) and ('Free' in key or 'Available' in key or 'Size' in key):
            interesting[key] = value
    return interesting, None


def system_profiler_numbers():
    """SPStorageDataType - the candidate most likely to mirror Finder."""
    stdout, err = run(['/usr/sbin/system_profiler', 'SPStorageDataType', '-json'])
    if err:
        return [], err
    try:
        data = json.loads(stdout)
    except ValueError as exc:
        return [], f'could not parse JSON: {exc}'

    volumes = []
    for entry in data.get('SPStorageDataType', []):
        volumes.append({
            'name': entry.get('_name', '?'),
            'mount_point': entry.get('mount_point', '?'),
            'free_space_in_bytes': entry.get('free_space_in_bytes'),
            'size_in_bytes': entry.get('size_in_bytes'),
        })
    return volumes, None


def snapshots():
    """Both listing paths, since they can disagree."""
    results = {}

    stdout, err = run(['/usr/bin/tmutil', 'listlocalsnapshots', '/'])
    if err:
        results['tmutil listlocalsnapshots /'] = f'ERROR: {err}'
    else:
        lines = [ln.strip() for ln in stdout.decode('utf-8', 'replace').splitlines() if ln.strip()]
        results['tmutil listlocalsnapshots /'] = lines

    stdout, err = run(['/usr/sbin/diskutil', 'apfs', 'listSnapshots', '/System/Volumes/Data'])
    if err:
        results['diskutil apfs listSnapshots /System/Volumes/Data'] = f'ERROR: {err}'
    else:
        lines = [ln.strip() for ln in stdout.decode('utf-8', 'replace').splitlines() if ln.strip()]
        results['diskutil apfs listSnapshots /System/Volumes/Data'] = lines

    return results


def main():
    if sys.platform != 'darwin':
        print(f'NOTE: this is {sys.platform}, not macOS - only statvfs will mean anything.\n')

    print('=' * 72)
    print('PURGEABLE SPACE VALIDATION SPIKE')
    print('=' * 72)

    for volume in VOLUMES:
        print(f'\n--- {volume} ---')

        free, err = statvfs_free(volume)
        if err:
            print(f'  statvfs: ERROR: {err}')
            continue
        print(f'  statvfs free (the conservative number):  {human(free)}  [{free}]')

        numbers, err = diskutil_numbers(volume)
        if err:
            print(f'  diskutil: ERROR: {err}')
        else:
            for key in sorted(numbers):
                delta = numbers[key] - free
                marker = '  <-- DIVERGES' if abs(delta) > 100 * 1024 * 1024 else ''
                print(f'    diskutil {key:<28} {human(numbers[key]):>12}  '
                      f'(statvfs delta {human(delta):>12}){marker}')

    print('\n--- system_profiler SPStorageDataType ---')
    volumes, err = system_profiler_numbers()
    if err:
        print(f'  ERROR: {err}')
    else:
        for entry in volumes:
            print(f'  {entry["name"]} at {entry["mount_point"]}')
            print(f'    free_space_in_bytes: {human(entry["free_space_in_bytes"])}  '
                  f'[{entry["free_space_in_bytes"]}]')
            print(f'    size_in_bytes:       {human(entry["size_in_bytes"])}')
            root_free, _ = statvfs_free(entry.get('mount_point') or '/')
            if root_free and entry['free_space_in_bytes']:
                delta = entry['free_space_in_bytes'] - root_free
                print(f'    statvfs delta:       {human(delta)}'
                      f'{"  <-- DIVERGES" if abs(delta) > 100 * 1024 * 1024 else ""}')

    print('\n--- snapshots ---')
    for label, value in snapshots().items():
        print(f'  {label}')
        if isinstance(value, str):
            print(f'    {value}')
        elif not value:
            print('    (none)')
        else:
            for line in value:
                print(f'    {line}')

    print('\n' + '=' * 72)
    print('NOW COMPARE BY HAND')
    print('=' * 72)
    print('  Finder:            open a window, ⌘I on Macintosh HD -> "available"')
    print('  Storage Settings:  Apple menu -> System Settings -> General -> Storage')
    print()
    print('  Any source whose number matches Finder rather than statvfs is the')
    print('  one 1c should use. If none of them do, ship snapshot count/age with')
    print('  honest copy instead of inventing a purgeable figure.')
    print()
    print('  Also worth noting: whether tmutil worked without Full Disk Access.')


if __name__ == '__main__':
    main()
