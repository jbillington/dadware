#!/usr/bin/env python3
"""
Dad Ware / askdad - A personality-driven Mac cleanup tool
"""

import argparse
import os
import sys
import datetime
import json
import csv
import webbrowser
import traceback
from utils.volumes import select_volume
from utils.formatters import format_size
from utils.path_utils import is_on_scan_volume, is_under
from utils.subprocess_utils import DIAGNOSTIC_LOGGING
from utils.permissions import (
    ALL_GRANTED_LINE,
    CLI_PROMPT_HEADSUP,
    PROMPT_EXPLAINER,
    FDA_UPGRADE_BODY,
    FDA_UPGRADE_HEADER,
    FDA_UPGRADE_STEPS,
    check_full_disk_access,
    choreograph_permission_prompts,
    format_permission_status,
    mark_permissions_introduced,
    offer_full_disk_access_settings,
    permissions_introduced,
)
from utils.timing import get_timer
from utils.version import VERSION, BUILD
from scanners.storage import scan_storage, parse_size
from scanners.cpu import scan_cpu
from scanners.mac_libraries import scan_all_mac_libraries as scan_all_mac_libraries_func
from scanners.hidden_storage import scan_hidden_storage
from scanners.snapshots import scan_snapshots
from scanners.trash import scan_trash
from personality.dad import add_personality
from renderers.terminal import render_terminal
from renderers.html import render_html

# Reports dirs already announced on stdout, so `all` (which saves two reports)
# doesn't repeat the notice for each one.
_announced_reports_dirs = set()


def get_reports_dir(use_test_reports=False):
    """
    Get the directory for saving reports.
    
    Args:
        use_test_reports: If True, use project test-reports folder. 
                         If False, use default ~/.dadware/reports
    
    Returns:
        Path to reports directory
    """
    if use_test_reports:
        # Use test-reports folder in project root
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up to project root (assuming script is in project root)
        project_root = script_dir
        reports_dir = os.path.join(project_root, 'test-reports')
    else:
        # Default: use hidden folder in home directory
        reports_dir = os.path.expanduser('~/.dadware/reports')
    
    return reports_dir


def is_development_mode():
    """
    Detect if we're running in development mode.
    Checks if we're in a git repository (common in development).
    
    Returns:
        True if likely in development mode, False otherwise
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    git_dir = os.path.join(script_dir, '.git')
    return os.path.exists(git_dir)


def report_scan_progress(items_found, elapsed_time):
    """
    Report progress during storage scan.
    
    Args:
        items_found: Number of items found so far
        elapsed_time: Time elapsed in seconds
    """
    rate = items_found / elapsed_time if elapsed_time > 0 else 0
    print(f"→ found {items_found:,} items... ({elapsed_time:.0f}s elapsed)", end='\r', flush=True)


def export_memory_to_csv(scan_data, output_path):
    """
    Export all memory processes to CSV for analysis.
    
    Args:
        scan_data: CPU scan data dict
        output_path: Path to save CSV file
    """
    all_processes = scan_data.get('all_processes', [])
    
    if not all_processes:
        print("Warning: No process data available to export")
        return False
    
    # Get memory pressure info for header
    memory_pressure = scan_data.get('memory_pressure', {})
    total_mem_gb = scan_data.get('total_memory_gb', 0)
    total_used_gb = scan_data.get('total_used_gb', 0)
    used_percent = (total_used_gb / total_mem_gb * 100) if total_mem_gb > 0 else 0
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header with system info
            writer.writerow(['# Memory Export from Dadware'])
            writer.writerow(['# Generated:', datetime.datetime.now().isoformat()])
            writer.writerow(['# Total RAM:', f'{total_mem_gb:.2f} GB'])
            writer.writerow(['# Used RAM:', f'{total_used_gb:.2f} GB ({used_percent:.1f}%)'])
            writer.writerow(['# Memory Pressure:', memory_pressure.get('pressure', 'unknown')])
            writer.writerow(['# Free Memory:', f"{memory_pressure.get('free_gb', 0):.2f} GB"])
            writer.writerow([''])
            
            # Write CSV header
            writer.writerow(['Process Name', 'Memory (MB)', 'Memory (GB)', 'Memory %', 'CPU %', 'Command'])
            
            # Write all processes
            for proc in all_processes:
                name = proc.get('name', 'Unknown')
                mem_mb = proc.get('memory_mb', 0)
                mem_gb = mem_mb / 1024.0
                mem_percent = proc.get('memory_percent', 0)
                cpu_percent = proc.get('cpu_percent', 0)
                command = proc.get('command', '')
                
                # Truncate very long commands
                if len(command) > 200:
                    command = command[:197] + '...'
                
                writer.writerow([name, f'{mem_mb:.2f}', f'{mem_gb:.3f}', f'{mem_percent:.2f}', f'{cpu_percent:.2f}', command])
        
        print(f"\n✅ Exported {len(all_processes)} processes to: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return False


def merge_home_folders(scan_data, home_scan_data):
    """Swap the volume walk's one `Users/<you>` row for the breakdown of it.

    Every folder in home is kept. There used to be an allowlist here -
    Downloads, Desktop, Documents, Movies, Music, Pictures, Library - and
    anything else was discarded: a 40 GB `~/Projects`, `~/code`, a folder of
    video work, gone from the report entirely, whatever its size. An
    allowlist cannot know what a person keeps in their own home folder, and
    a storage tool that hides the biggest folder on the disk has failed at
    the only job it has. Size decides now; the renderer takes the top 10.

    The names still matter elsewhere - `grade_home_folders_clutter()` looks
    up Downloads and Desktop by name - and those rows are still here, now
    carrying their full recursive size rather than their loose files alone.
    """
    home_folders = home_scan_data.get('top_folders', [])

    volume_folders = scan_data.get('top_folders', [])
    # The home this scan actually walked, not this process's `~`. They are
    # the same on a normal run and different everywhere else that matters.
    home_dir = scan_data.get('home_path') or os.path.expanduser('~')
    non_home_folders = [f for f in volume_folders
                        if not is_under(f.get('path', ''), home_dir)]

    scan_data['top_folders'] = home_folders + non_home_folders
    scan_data['home_folders_total_bytes'] = sum(f.get('size_bytes', 0) for f in home_folders)
    scan_data['home_folders_total_human'] = format_size(scan_data['home_folders_total_bytes'])


def merge_trash_folders(scan_data):
    """Put the Trash in the folder list, where a folder its size belongs.

    On a real Mac `~/.Trash` held 14.3 GB - larger than Downloads, the
    biggest thing in the report - and it appeared in no folder list at all,
    because `should_exclude()` drops every dotfile before the walk ever sees
    it. The Trash is a folder. The folder chart is where people look for big
    folders. So it becomes an ordinary row that sorts on size with
    everything else, rather than a section of its own further down the page.

    Nothing is double-counted: the walk never reached these paths, which is
    the whole bug. A location the scan could not read adds no row - a folder
    bar cannot say "unknown", so `render_permission_warning()` says it in
    words instead.
    """
    trash = scan_data.get('trash') or {}
    rows = [loc for loc in (trash.get('locations') or []) if loc.get('size_bytes')]
    if not rows:
        return

    folders = list(scan_data.get('top_folders') or [])
    home_dir = scan_data.get('home_path') or os.path.expanduser('~')
    home_bytes_added = 0

    for location in rows:
        path = location.get('path', '')
        folders.append({
            'path': path,
            # The folder on disk is `.Trash`; "Trash" is what the reader
            # calls it, and the expanded panel still prints the real path.
            'path_display': 'Trash',
            'size_bytes': location.get('size_bytes', 0),
            'size_human': location.get('size_human', format_size(0)),
        })
        if is_under(path, home_dir):
            home_bytes_added += location.get('size_bytes', 0)

    # Same ordering rule as the walk: size descending, ties broken on path
    # so a report is reproducible.
    folders.sort(key=lambda f: (-f.get('size_bytes', 0), f.get('path', '')))
    scan_data['top_folders'] = folders

    if home_bytes_added:
        # The home total feeds the Home Folders Ratio grade, and the bar it
        # now appears in. Leaving it out would print a chart whose segments
        # do not add up to the total beside them.
        scan_data['home_folders_total_bytes'] = (
            scan_data.get('home_folders_total_bytes', 0) + home_bytes_added)
        scan_data['home_folders_total_human'] = format_size(
            scan_data['home_folders_total_bytes'])


def offer_permission_upgrade(scan_data, args):
    """End-of-run Full Disk Access hand-off.

    Deliberately the last thing that happens. macOS applies a Full Disk
    Access grant to a process when it *starts*, so nothing the user toggles
    can change the report they are currently reading - offering it mid-scan
    (as this used to) invited them to fix something and then showed them a
    scan that carried on regardless, looking like the click did nothing.
    Here the report is already written and opened, so "this takes effect
    next time" is simply true.
    """
    if args.skip_protected:
        return
    status = (scan_data or {}).get('permission_status') or {}
    if status.get('has_access', True) or not status.get('missing_permissions'):
        return

    print(f"\n{FDA_UPGRADE_HEADER}")
    print(f"  {FDA_UPGRADE_BODY}")
    print()
    print(FDA_UPGRADE_STEPS)
    print()
    offer_full_disk_access_settings()


def print_header():
    """Print branded header."""
    print("────────────────────────────────")
    print(f" Ask Dad for Mac v{VERSION}")
    print(f" Build: {BUILD}")
    print("────────────────────────────────")


def save_and_open_report(scan_data, personality_data, prefix, args, label='Full report'):
    """
    Render the HTML report, write the JSON manifest, and open the report in
    a browser. No-op when args.terminal is set.

    Args:
        scan_data: Scan result dict (storage or cpu scan data)
        personality_data: Output of add_personality(scan_data)
        prefix: 'storage' or 'cpu' - used for filenames and the
                scan_results key in the manifest
        args: Parsed CLI args (uses args.terminal, args.test_reports)
        label: How to describe this report on stdout. The 'all' command
               saves two reports, so it labels them individually.
    """
    if args.terminal:
        return

    # Auto-detect development mode if flag not provided
    use_test_reports = args.test_reports or is_development_mode()
    reports_dir = get_reports_dir(use_test_reports=use_test_reports)
    os.makedirs(reports_dir, exist_ok=True)

    # Announce the directory once per run, not once per report saved.
    if use_test_reports and reports_dir not in _announced_reports_dirs:
        _announced_reports_dirs.add(reports_dir)
        print(f"\n📁 Using test-reports directory: {reports_dir}")

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    report_filename = f"{prefix}_{timestamp}.html"
    report_path = os.path.join(reports_dir, report_filename)

    with get_timer().phase('html render'):
        render_html(scan_data, personality_data, report_path)

    # Save manifest
    manifest = {
        'report_id': f"{prefix}_{timestamp}",
        'generated_at': datetime.datetime.now().isoformat(),
        'scan_results': {prefix: scan_data},
        'personality_comments': personality_data.get('comments', []),
        'report_files': {
            'html': report_path
        }
    }
    manifest_path = os.path.join(reports_dir, f"{prefix}_{timestamp}.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Open in browser
    file_url = f"file://{report_path}"
    webbrowser.open(file_url)
    print(f"\n📊 {label}: {file_url}")
    print("   (opened in browser)")


def run_storage_scan(args):
    """
    Run a full storage scan: select volume, scan it, scan the home
    directory separately for a detailed folder breakdown, check Full Disk
    Access permissions, and scan Mac app libraries.

    Everything after the walk - the home breakdown, the permission
    choreography, Mac app libraries, hidden caches and snapshots - describes
    the disk the home folder lives on. When the user picks another volume (a
    thumb drive, an external disk) none of it belongs in the report: it would
    answer a question about a different disk than the one they asked about.
    So those phases run only when the chosen volume is home's, and the report
    is marked `scan_scope` so the renderers can say what a volume report does
    and does not cover.

    Args:
        args: Parsed CLI args (uses args.volume, args.all_volumes, args.top,
              args.min_size, args.skip_protected, args.no_mac_libraries,
              args.library_timeout)

    Returns:
        scan_data dict, or None if the scan could not be started/completed.
    """
    timer = get_timer()
    volume_path = select_volume(args.volume, include_all=getattr(args, 'all_volumes', False))
    if not volume_path:
        return None

    min_size_bytes = parse_size(args.min_size) if args.min_size else 0

    # Is this the disk the home folder lives on? Everything below that talks
    # about home, app libraries, caches or snapshots is only true for that
    # disk. Scanning a thumb drive and being shown the state of the startup
    # disk is the bug this answers.
    home_path = os.path.expanduser('~')
    scans_home_volume = is_on_scan_volume(volume_path, home_path)

    if not scans_home_volume:
        print(f"\n→ {volume_path} is not the disk your home folder is on, so this "
              f"report covers that drive only.\n"
              f"  No home folders, app libraries, caches or snapshots - those "
              f"live on the startup disk.")

    # Prompt choreography (PERMISSIONS-PLAN.md Phase 1): explain first, then
    # touch the auto-prompt folders in a fixed order so macOS's permission
    # dialogs all fire up front with context, not scattered through the scan.
    #
    # The explainer only runs the first time. macOS asks once and remembers,
    # so on later runs there are no dialogs to warn about, and promising them
    # makes a working scan look broken.
    # Desktop/Documents/Downloads are on the startup disk, so asking for them
    # to scan a thumb drive would be prompting for access this run will never
    # use - and the first-run explainer would be introducing permissions the
    # user did not trigger. Left for the first scan that needs them.
    folder_access = {}
    if scans_home_volume:
        first_introduction = not permissions_introduced()
        if first_introduction:
            print(f"\n{PROMPT_EXPLAINER}")
            if sys.stdin.isatty():
                print(CLI_PROMPT_HEADSUP)

        folder_access = choreograph_permission_prompts()
        mark_permissions_introduced()

        denied_folders = [name for name, info in folder_access.items()
                          if info.get('status') == 'denied']
        if denied_folders:
            print(f"\n→ no access to: {', '.join(denied_folders)} — skipped and "
                  f"labeled in the report, never silently zeroed.\n"
                  f"  macOS remembers that choice; change it in System Settings → "
                  f"Privacy & Security → Files & Folders.")
        elif first_introduction:
            # Close the loop we opened above; on later runs, silence is the
            # honest answer - nothing happened worth saying.
            print(ALL_GRANTED_LINE)

    print(f"\n→ scanning volume: {volume_path}")
    with timer.phase('volume walk'):
        scan_data = scan_storage(
            volume_path,
            depth=2,
            top_n=args.top,
            min_size_bytes=min_size_bytes,
            progress_callback=report_scan_progress,
            # When home is inside the volume, the same walk collects its
            # folder breakdown - no second pass over the same files. On any
            # other volume there is no home to break down.
            home_path=home_path if scans_home_volume else None,
        )

    if not scan_data:
        return None

    # What this report is about. The renderers use it to say what a volume
    # report covers, and to grade only what was actually measured.
    scan_data['scan_scope'] = 'home_volume' if scans_home_volume else 'other_volume'
    # Recorded so the renderers can tell a home folder from any other folder
    # by where it lives. Reading the *current* user's home instead would
    # misfile every row of a saved manifest opened on another Mac.
    scan_data['home_path'] = home_path

    # Detailed home folder breakdown. It normally rides along with the volume
    # walk; a home directory outside the scanned volume still needs its own
    # walk, and so does one the walk never reached (a denied or excluded
    # parent) - scan_storage() omits the key in that case rather than hand
    # back an empty breakdown that would blank the home rows.
    home_breakdown = scan_data.pop('home_breakdown', None)
    if home_breakdown is not None:
        merge_home_folders(scan_data, home_breakdown)
    elif scans_home_volume and volume_path != home_path:
        print(f"\n→ scanning home directory for detailed breakdown: {home_path}")
        with timer.phase('home walk'):
            home_scan_data = scan_storage(
                home_path,
                depth=2,
                top_n=args.top,
                min_size_bytes=min_size_bytes,
                # Same shape as the folded breakdown: one row per folder in
                # home, carrying everything inside it.
                rollup=True,
                progress_callback=None  # Don't show progress for home scan (already shown for volume)
            )

        if home_scan_data:
            merge_home_folders(scan_data, home_scan_data)

    # The Trash, which the main walk cannot see: `should_exclude()` drops
    # every dotfile, so `~/.Trash` and `<volume>/.Trashes` are missing from
    # the numbers above. Deleting a file in Finder only moves it, so this is
    # often the difference between what the report accounts for and what the
    # drive says is used. Runs on both report shapes - a drive report covers
    # that drive's own Trash, and only that one.
    print("→ measuring the Trash...")
    try:
        with timer.phase('trash'):
            # One report, one disk - the rule the whole scan follows. The
            # startup disk's report measures `~/.Trash`; a drive's report
            # measures that drive's `.Trashes`. Another disk's Trash belongs
            # in that disk's report, not as a stray row in this one.
            if scans_home_volume:
                scan_data['trash'] = scan_trash(volume_paths=[])
            else:
                scan_data['trash'] = scan_trash(include_home=False,
                                                volume_paths=[volume_path])
        merge_trash_folders(scan_data)
    except KeyboardInterrupt:
        print("\n⚠️  Trash scan interrupted by user")
        scan_data['trash'] = {'scan_type': 'trash', 'locations': [],
                              'total_size_bytes': 0,
                              'total_size_human': format_size(0),
                              'item_count': 0, 'status': 'partial'}
    except Exception as e:
        print(f"\n⚠️  Trash scan failed: {e}", file=sys.stderr)
        if DIAGNOSTIC_LOGGING:
            print("[DIAGNOSTIC] Full traceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        scan_data['trash'] = {'scan_type': 'trash', 'locations': [],
                              'total_size_bytes': 0,
                              'total_size_human': format_size(0),
                              'item_count': 0, 'status': 'partial',
                              'error': str(e)}

    # Everything from here to the end of the function reads the startup
    # disk - Full Disk Access covers Apple's libraries, the caches live in
    # ~/Library, and the snapshots are the boot volume's. On another volume
    # they would describe a disk the user did not ask about, so the report
    # leaves the keys out entirely and every section renderer already omits
    # a section whose data is absent.
    if not scans_home_volume:
        return scan_data

    # Check permissions before scanning Mac libraries
    try:
        if DIAGNOSTIC_LOGGING:
            print("\n[DIAGNOSTIC] About to call check_full_disk_access()", file=sys.stderr)
            sys.stderr.flush()
        with timer.phase('permission check'):
            permission_results = check_full_disk_access()
        permission_results['folders'] = folder_access
        scan_data['permission_status'] = permission_results

        if not permission_results['has_access'] and not args.skip_protected:
            # Note it and move on. The fix cannot apply to a process that is
            # already running, so the offer to open System Settings waits
            # until the report is done - see offer_permission_upgrade().
            print(f"\n{format_permission_status(permission_results)}")
            print("   Carrying on — those areas are labeled in the report, not "
                  "counted as zero.\n")
    except Exception as e:
        print(f"⚠️  Warning: Permission check failed: {e}", file=sys.stderr)
        if DIAGNOSTIC_LOGGING:
            print(f"[DIAGNOSTIC] Full traceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        scan_data['permission_status'] = {'has_access': False, 'error': str(e),
                                          'folders': folder_access}

    # Scan Mac app libraries (unless skipped)
    if args.no_mac_libraries:
        print("→ skipping Mac app libraries (--no-mac-libraries)")
        scan_data['mac_libraries'] = {}
    elif not args.skip_protected:
        print("→ scanning Mac app libraries...")
        try:
            if DIAGNOSTIC_LOGGING:
                print("[DIAGNOSTIC] About to call scan_all_mac_libraries_func()", file=sys.stderr)
                sys.stderr.flush()
            with timer.phase('mac libraries'):
                mac_libraries = scan_all_mac_libraries_func(
                    timeout_seconds=getattr(args, 'library_timeout', 60.0))
            scan_data['mac_libraries'] = mac_libraries
            # Show status if partial or interrupted
            if mac_libraries.get('scan_status') != 'complete':
                status = mac_libraries.get('scan_status', 'unknown')
                print(f"   ⚠️  Mac library scan: {status}")
        except KeyboardInterrupt:
            print("\n⚠️  Mac library scan interrupted by user")
            scan_data['mac_libraries'] = {
                'scan_status': 'interrupted',
                'total_size_bytes': 0,
                'total_size_human': '0 B'
            }
        except Exception as e:
            print(f"\n⚠️  Mac library scan failed: {e}", file=sys.stderr)
            if DIAGNOSTIC_LOGGING:
                print(f"[DIAGNOSTIC] Full traceback:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
            scan_data['mac_libraries'] = {
                'scan_status': 'error',
                'error': str(e),
                'total_size_bytes': 0,
                'total_size_human': '0 B'
            }
    else:
        print("→ skipping protected directories (--skip-protected)")
        scan_data['mac_libraries'] = {}

    # Scan the app caches the main walk can't see. Runs regardless of
    # --skip-protected: ~/Library/Caches is not TCC-protected, and the
    # scanner already degrades to a permission note on the folders that are.
    print("→ scanning hidden app caches...")
    try:
        with timer.phase('hidden caches'):
            hidden_caches = scan_hidden_storage()
        scan_data['hidden_caches'] = hidden_caches
        if hidden_caches.get('scan_status') != 'complete':
            print(f"   ⚠️  Hidden cache scan: {hidden_caches.get('scan_status', 'unknown')}")
    except KeyboardInterrupt:
        print("\n⚠️  Hidden cache scan interrupted by user")
        scan_data['hidden_caches'] = {
            'scan_status': 'interrupted',
            'entries': [],
            'total_size_bytes': 0,
            'total_size_human': format_size(0),
        }
    except Exception as e:
        print(f"\n⚠️  Hidden cache scan failed: {e}", file=sys.stderr)
        if DIAGNOSTIC_LOGGING:
            print("[DIAGNOSTIC] Full traceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        scan_data['hidden_caches'] = {
            'scan_status': 'error',
            'error': str(e),
            'entries': [],
            'total_size_bytes': 0,
            'total_size_human': format_size(0),
        }

    # Local APFS snapshots - the other half of "where did my space go?".
    # Cheap (two subprocess calls) and needs no special permissions.
    print("→ checking local snapshots...")
    try:
        with timer.phase('snapshots'):
            scan_data['snapshots'] = scan_snapshots()
    except KeyboardInterrupt:
        print("\n⚠️  Snapshot check interrupted by user")
        scan_data['snapshots'] = {'scan_type': 'snapshots', 'snapshots': [],
                                  'count': 0, 'status': 'unavailable'}
    except Exception as e:
        print(f"\n⚠️  Snapshot check failed: {e}", file=sys.stderr)
        if DIAGNOSTIC_LOGGING:
            print("[DIAGNOSTIC] Full traceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        scan_data['snapshots'] = {'scan_type': 'snapshots', 'snapshots': [],
                                  'count': 0, 'status': 'unavailable', 'note': str(e)}

    return scan_data


def run_cpu_scan(args):
    """
    Run the CPU/RAM scan and handle --export-memory CSV export.

    Args:
        args: Parsed CLI args (uses args.export_memory)

    Returns:
        scan_data dict, or None if the scan failed.
    """
    try:
        if DIAGNOSTIC_LOGGING:
            print("\n[DIAGNOSTIC] About to call scan_cpu()", file=sys.stderr)
            sys.stderr.flush()
        with get_timer().phase('cpu scan'):
            scan_data = scan_cpu()
    except Exception as e:
        print(f"⚠️  Warning: CPU scan failed with error: {e}", file=sys.stderr)
        if DIAGNOSTIC_LOGGING:
            print(f"[DIAGNOSTIC] Full traceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        return None

    if not scan_data:
        return None

    # Export memory data if requested
    if args.export_memory:
        export_memory_to_csv(scan_data, args.export_memory)

    return scan_data


def finish_run(scan_data):
    """Stamp the run's wall clock onto `scan_data` and hand it back.

    The reported figure is the whole run - every walk, every library, the
    grading and the render - not just the volume walk. Called once per report
    at the point the report is written, so the number matches what a stopwatch
    on the terminal would read.
    """
    if scan_data is not None:
        scan_data['duration_seconds'] = get_timer().elapsed
    return scan_data


def main():
    """Main CLI entry point."""
    timer = get_timer()
    timer.start()

    parser = argparse.ArgumentParser(
        description="Dad Ware - Your friendly Mac cleanup tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  (default)  Scan storage (large files and folders)
  cpu        Scan CPU and RAM usage
  all        Scan both storage and CPU/RAM
  export     Export data from existing reports

Examples:
  %(prog)s                              Scan storage
  %(prog)s cpu                          Scan CPU and RAM
  %(prog)s all                          Scan everything
  %(prog)s --volume /Volumes/External   Scan a specific volume
  %(prog)s --all-volumes                Also offer disk images/network shares
  %(prog)s cpu --export-memory mem.csv  Export process data to CSV
  %(prog)s export memory report.json    Export from saved report
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'Dad Ware v{VERSION}'
    )

    # Top-level shared flags
    parser.add_argument('--volume', type=str, help='Volume path to scan (default: prompt)')
    parser.add_argument('--all-volumes', action='store_true',
                        help='Include disk images, network shares, and read-only mounts in the volume picker')
    parser.add_argument('--top', type=int, default=500, help='Number of top files to show (default: 500)')
    parser.add_argument('--min-size', type=str, help='Minimum file size (e.g., 500MB)')
    parser.add_argument('--terminal', action='store_true', help='Terminal report only (skip HTML)')
    parser.add_argument('--no-color', action='store_true', help='Disable ANSI colors in terminal output')
    parser.add_argument('--test-reports', action='store_true', help='Save reports to test-reports/ folder in project (for development)')
    parser.add_argument('--skip-protected', action='store_true', help='Skip scanning protected directories (Photos, Messages, Mail)')
    parser.add_argument('--no-mac-libraries', action='store_true', help='Skip scanning Mac app libraries entirely (faster scan)')
    parser.add_argument('--library-timeout', type=float, default=60.0,
                        help='Time budget in seconds for the Mac app library scan (default: 60). '
                             'Libraries not reached in time are reported as skipped and are not graded.')
    parser.add_argument('--export-memory', type=str, help='Export all memory processes to CSV file (cpu scan only)')
    parser.add_argument('--timings', action='store_true',
                        help='Print how long each phase of the scan took (also on with DIAGNOSTIC_LOGGING=1)')

    subparsers = parser.add_subparsers(dest='command')

    # cpu subcommand
    subparsers.add_parser('cpu', help='Scan CPU and RAM usage')

    # all subcommand
    subparsers.add_parser('all', help='Scan both storage and CPU/RAM')

    # export subcommand
    export_parser = subparsers.add_parser('export', help='Export data from existing reports')
    export_subparsers = export_parser.add_subparsers(dest='export_type', help='Export type')

    memory_export_parser = export_subparsers.add_parser('memory', help='Export memory data from JSON report')
    memory_export_parser.add_argument('json_file', type=str, help='Path to JSON report file (e.g., cpu_2025-11-26_16-54.json)')
    memory_export_parser.add_argument('--output', type=str, help='Output CSV file path (default: memory_export_TIMESTAMP.csv)')

    args = parser.parse_args()
    timer.enabled = DIAGNOSTIC_LOGGING or getattr(args, 'timings', False)

    # Default to storage scan when no command given
    scan_type = args.command if args.command else 'storage'

    if scan_type == 'export':
        # Handle export command separately
        pass
    else:
        print_header()

    if scan_type == 'storage':
        print(f"Starting storage scan (Build {BUILD})...\n")
        scan_data = run_storage_scan(args)
        if not scan_data:
            return 1

        with timer.phase('grading'):
            personality_data = add_personality(scan_data)

        finish_run(scan_data)
        use_color = not args.no_color
        terminal_output = render_terminal(scan_data, personality_data, use_color)
        print(terminal_output)

        save_and_open_report(scan_data, personality_data, 'storage', args)
        offer_permission_upgrade(scan_data, args)
        timer.print_summary()

        return 0

    elif scan_type == 'cpu':
        print(f"Starting CPU scan (Build {BUILD})...\n")
        scan_data = run_cpu_scan(args)

        if not scan_data:
            print("Error: Could not scan CPU/RAM")
            return 1

        with timer.phase('grading'):
            personality_data = add_personality(scan_data)

        finish_run(scan_data)
        use_color = not args.no_color
        terminal_output = render_terminal(scan_data, personality_data, use_color)
        print(terminal_output)

        save_and_open_report(scan_data, personality_data, 'cpu', args)
        timer.print_summary()

        return 0

    elif scan_type == 'all':
        print(f"\nRunning full scan (storage + CPU) - Build {BUILD}...\n")

        scan_data_storage = run_storage_scan(args)
        if not scan_data_storage:
            print("Error: Storage scan failed")
            return 1

        scan_data_cpu = run_cpu_scan(args)
        if not scan_data_cpu:
            print("Warning: CPU scan failed, continuing with storage only")

        # Render terminal output
        use_color = not args.no_color
        with timer.phase('grading'):
            personality_storage = add_personality(scan_data_storage)
            if scan_data_cpu:
                personality_cpu = add_personality(scan_data_cpu)

        finish_run(scan_data_storage)
        finish_run(scan_data_cpu)
        terminal_output = render_terminal(scan_data_storage, personality_storage, use_color)
        print(terminal_output)

        if scan_data_cpu:
            print("\n")
            terminal_output_cpu = render_terminal(scan_data_cpu, personality_cpu, use_color)
            print(terminal_output_cpu)

        # Save and open reports
        save_and_open_report(scan_data_storage, personality_storage, 'storage', args,
                             label='Storage report')
        if scan_data_cpu:
            save_and_open_report(scan_data_cpu, personality_cpu, 'cpu', args,
                                 label='CPU report')
        offer_permission_upgrade(scan_data_storage, args)
        timer.print_summary()

        return 0

    elif scan_type == 'export':
        if not args.export_type:
            export_parser.print_help()
            return 1

        print_header()

        if args.export_type == 'memory':
            json_file = args.json_file

            if not os.path.exists(json_file):
                print(f"Error: File not found: {json_file}")
                return 1

            try:
                with open(json_file, 'r') as f:
                    manifest = json.load(f)

                # Extract CPU scan data
                scan_results = manifest.get('scan_results', {})
                scan_data = scan_results.get('cpu')

                if not scan_data:
                    print("Error: No CPU scan data found in JSON file")
                    print("Available scan types:", list(scan_results.keys()))
                    return 1

                # Determine output path
                if args.output:
                    output_path = args.output
                else:
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
                    output_path = f"memory_export_{timestamp}.csv"

                # Export to CSV
                if export_memory_to_csv(scan_data, output_path):
                    print(f"\n📊 Memory data exported successfully!")
                    print(f"   You can now analyze this CSV file on any computer.")
                    return 0
                else:
                    return 1

            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON file: {e}")
                return 1
            except Exception as e:
                print(f"Error: {e}")
                return 1

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nScan cancelled.")
        sys.exit(1)

