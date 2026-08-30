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
from utils.path_utils import basenames_in
from utils.subprocess_utils import DIAGNOSTIC_LOGGING
from utils.permissions import (
    CLI_PROMPT_HEADSUP,
    PROMPT_EXPLAINER,
    check_full_disk_access,
    choreograph_permission_prompts,
    format_permission_status,
    get_permission_instructions,
    offer_full_disk_access_settings,
)
from utils.version import VERSION, BUILD
from scanners.storage import scan_storage, parse_size
from scanners.cpu import scan_cpu
from scanners.mac_libraries import scan_all_mac_libraries as scan_all_mac_libraries_func
from scanners.hidden_storage import scan_hidden_storage
from scanners.snapshots import scan_snapshots
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
    """
    Merge home folder breakdown from a separate home scan into the main volume scan data.
    Replaces home-directory folders in scan_data with the detailed breakdown from home_scan_data.
    """
    home_folders = home_scan_data.get('top_folders', [])
    home_folder_names = ['Downloads', 'Desktop', 'Documents', 'Movies', 'Music', 'Pictures', 'Library']

    actual_home_folders = basenames_in(home_folders, home_folder_names)

    volume_folders = scan_data.get('top_folders', [])
    home_dir = os.path.expanduser('~')
    non_home_folders = [f for f in volume_folders if not f.get('path', '').startswith(home_dir)]

    scan_data['top_folders'] = actual_home_folders + non_home_folders
    scan_data['home_folders_total_bytes'] = sum(f.get('size_bytes', 0) for f in actual_home_folders)
    scan_data['home_folders_total_human'] = format_size(scan_data['home_folders_total_bytes'])


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

    Args:
        args: Parsed CLI args (uses args.volume, args.all_volumes, args.top,
              args.min_size, args.skip_protected, args.no_mac_libraries,
              args.library_timeout)

    Returns:
        scan_data dict, or None if the scan could not be started/completed.
    """
    volume_path = select_volume(args.volume, include_all=getattr(args, 'all_volumes', False))
    if not volume_path:
        return None

    min_size_bytes = parse_size(args.min_size) if args.min_size else 0

    # Prompt choreography (PERMISSIONS-PLAN.md Phase 1): explain first, then
    # touch the auto-prompt folders in a fixed order so macOS's permission
    # dialogs all fire up front with context, not scattered through the scan.
    print(f"\n{PROMPT_EXPLAINER}")
    if sys.stdin.isatty():
        print(CLI_PROMPT_HEADSUP)
    folder_access = choreograph_permission_prompts()
    denied_folders = [name for name, info in folder_access.items()
                      if info.get('status') == 'denied']
    if denied_folders:
        print(f"→ no access to: {', '.join(denied_folders)} — skipped and "
              f"labeled in the report, never silently zeroed.\n"
              f"  macOS remembers that choice; change it in System Settings → "
              f"Privacy & Security → Files & Folders.")

    # Always scan the selected volume
    print(f"\n→ scanning volume: {volume_path}")
    scan_data = scan_storage(
        volume_path,
        depth=2,
        top_n=args.top,
        min_size_bytes=min_size_bytes,
        progress_callback=report_scan_progress
    )

    if not scan_data:
        return None

    # Always scan home directory separately to get detailed home folder breakdown
    home_path = os.path.expanduser('~')
    if volume_path != home_path:
        print(f"\n→ scanning home directory for detailed breakdown: {home_path}")
        home_scan_data = scan_storage(
            home_path,
            depth=2,
            top_n=args.top,
            min_size_bytes=min_size_bytes,
            progress_callback=None  # Don't show progress for home scan (already shown for volume)
        )

        if home_scan_data:
            merge_home_folders(scan_data, home_scan_data)

    # Check permissions before scanning Mac libraries
    try:
        if DIAGNOSTIC_LOGGING:
            print("\n[DIAGNOSTIC] About to call check_full_disk_access()", file=sys.stderr)
            sys.stderr.flush()
        permission_results = check_full_disk_access()
        permission_results['folders'] = folder_access
        scan_data['permission_status'] = permission_results

        if not permission_results['has_access'] and not args.skip_protected:
            print(f"\n{format_permission_status(permission_results)}")
            print("\n" + get_permission_instructions())
            offer_full_disk_access_settings()
            print("\nContinuing scan... (areas without access are labeled in the report)")
            print("Use --skip-protected to skip scanning protected directories entirely.\n")
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


def main():
    """Main CLI entry point."""
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

        personality_data = add_personality(scan_data)

        use_color = not args.no_color
        terminal_output = render_terminal(scan_data, personality_data, use_color)
        print(terminal_output)

        save_and_open_report(scan_data, personality_data, 'storage', args)

        return 0

    elif scan_type == 'cpu':
        print(f"Starting CPU scan (Build {BUILD})...\n")
        scan_data = run_cpu_scan(args)

        if not scan_data:
            print("Error: Could not scan CPU/RAM")
            return 1

        personality_data = add_personality(scan_data)

        use_color = not args.no_color
        terminal_output = render_terminal(scan_data, personality_data, use_color)
        print(terminal_output)

        save_and_open_report(scan_data, personality_data, 'cpu', args)

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
        personality_storage = add_personality(scan_data_storage)
        terminal_output = render_terminal(scan_data_storage, personality_storage, use_color)
        print(terminal_output)

        if scan_data_cpu:
            personality_cpu = add_personality(scan_data_cpu)
            print("\n")
            terminal_output_cpu = render_terminal(scan_data_cpu, personality_cpu, use_color)
            print(terminal_output_cpu)

        # Save and open reports
        save_and_open_report(scan_data_storage, personality_storage, 'storage', args,
                             label='Storage report')
        if scan_data_cpu:
            save_and_open_report(scan_data_cpu, personality_cpu, 'cpu', args,
                                 label='CPU report')

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

