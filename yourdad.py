#!/usr/bin/python3
"""
Dad Ware / yourdad - A personality-driven Mac cleanup tool
"""

import argparse
import os
import sys
import datetime
import json
import csv
import webbrowser
import traceback
from utils.volumes import select_volume, format_size
from utils.permissions import check_full_disk_access, format_permission_status, get_permission_instructions
from scanners.storage import scan_storage, parse_size
from scanners.cpu import scan_cpu
from scanners.mac_libraries import scan_all_mac_libraries as scan_all_mac_libraries_func
from personality.yourdad import add_personality
from renderers.terminal import render_terminal
from renderers.html import render_html

VERSION = "0.1-poc"
BUILD = "2025-11-28-013"  # Fixed Docker container size calculation - now uses actual disk usage (st_blocks) instead of logical file size for sparse files

# Enable diagnostic logging for subprocess calls (set to True for debugging)
DIAGNOSTIC_LOGGING = True


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


def print_header():
    """Print branded header."""
    print("────────────────────────────────")
    print(f" Dad Ware  |  yourdad v{VERSION}")
    print(f" Build: {BUILD}")
    print("────────────────────────────────")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Dad Ware - Your friendly Mac cleanup tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available scan types:
  storage    Scan storage (large files and folders)
  cpu        Scan CPU and RAM usage
  all        Scan both storage and CPU/RAM (opens both reports)

Memory Export (CPU/RAM data only):
  You can export memory/process data in two ways:
  
  1. During scan (live export):
     %(prog)s scan cpu --export-memory memory.csv
     Exports all processes with memory usage to CSV during the scan.
  
  2. From existing JSON report:
     %(prog)s export memory cpu_2025-11-26_16-54.json
     Extracts memory data from a previously saved JSON report file.
  
  Note: Memory export only works with CPU scans, not storage scans.
        The CSV includes all processes with memory usage, CPU %%, and commands.

Examples:
  %(prog)s scan storage
  %(prog)s scan cpu
  %(prog)s scan all
  %(prog)s scan cpu --export-memory memory.csv
  %(prog)s export memory cpu_2025-11-26_16-54.json

For more help, run: %(prog)s scan <type> --help
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'Dad Ware v{VERSION}'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # export subcommand
    export_parser = subparsers.add_parser('export', help='Export data from existing reports')
    export_subparsers = export_parser.add_subparsers(dest='export_type', help='Export type')
    
    memory_export_parser = export_subparsers.add_parser('memory', help='Export memory data from JSON report')
    memory_export_parser.add_argument('json_file', type=str, help='Path to JSON report file (e.g., cpu_2025-11-26_16-54.json)')
    memory_export_parser.add_argument('--output', type=str, help='Output CSV file path (default: memory_export_TIMESTAMP.csv)')
    
    # scan subcommand
    scan_parser = subparsers.add_parser('scan', help='Run a scan')
    scan_subparsers = scan_parser.add_subparsers(dest='scan_type', help='Scan type')
    
    # scan storage
    storage_parser = scan_subparsers.add_parser('storage', help='Scan storage (large files and folders)')
    storage_parser.add_argument('--volume', type=str, help='Volume path to scan (default: prompt)')
    storage_parser.add_argument('--top', type=int, default=500, help='Number of top files to show (default: 500)')
    storage_parser.add_argument('--min-size', type=str, help='Minimum file size (e.g., 500MB)')
    storage_parser.add_argument('--terminal', action='store_true', help='Terminal report only (skip HTML)')
    storage_parser.add_argument('--no-color', action='store_true', help='Disable ANSI colors in terminal output')
    storage_parser.add_argument('--test-reports', action='store_true', help='Save reports to test-reports/ folder in project (for development)')
    storage_parser.add_argument('--skip-protected', action='store_true', help='Skip scanning protected directories (Photos, Messages, Mail)')
    storage_parser.add_argument('--no-mac-libraries', action='store_true', help='Skip scanning Mac app libraries entirely (faster scan)')
    
    # scan cpu
    cpu_parser = scan_subparsers.add_parser('cpu', help='Scan CPU and RAM usage')
    cpu_parser.add_argument('--terminal', action='store_true', help='Terminal report only (skip HTML)')
    cpu_parser.add_argument('--no-color', action='store_true', help='Disable ANSI colors in terminal output')
    cpu_parser.add_argument('--test-reports', action='store_true', help='Save reports to test-reports/ folder in project (for development)')
    cpu_parser.add_argument('--export-memory', type=str, help='Export all memory processes to CSV file (e.g., --export-memory memory_export.csv)')
    
    # scan all
    all_parser = scan_subparsers.add_parser('all', help='Scan both storage and CPU/RAM')
    all_parser.add_argument('--volume', type=str, help='Volume path to scan (default: prompt)')
    all_parser.add_argument('--terminal', action='store_true', help='Terminal report only (skip HTML)')
    all_parser.add_argument('--no-color', action='store_true', help='Disable ANSI colors in terminal output')
    all_parser.add_argument('--test-reports', action='store_true', help='Save reports to test-reports/ folder in project (for development)')
    all_parser.add_argument('--skip-protected', action='store_true', help='Skip scanning protected directories (Photos, Messages, Mail)')
    all_parser.add_argument('--no-mac-libraries', action='store_true', help='Skip scanning Mac app libraries entirely (faster scan)')
    
    args = parser.parse_args()
    
    if not args.command:
        print_header()
        parser.print_help()
        return 0
    
    if args.command == 'scan':
        if not args.scan_type:
            scan_parser.print_help()
            return 1
        
        print_header()
        
        if args.scan_type == 'storage':
            print(f"Starting storage scan (Build {BUILD})...\n")
            volume_path = select_volume(args.volume)
            if not volume_path:
                return 1
            
            min_size_bytes = parse_size(args.min_size) if args.min_size else 0
            
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
                return 1
            
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
                    # Extract home folders from home scan
                    home_folders = home_scan_data.get('top_folders', [])
                    
                    # Identify home folder names
                    home_folder_names = ['Downloads', 'Desktop', 'Documents', 'Movies', 'Music', 'Pictures', 'Library']
                    
                    # Filter to get only actual home folders
                    actual_home_folders = []
                    for folder in home_folders:
                        path_display = folder.get('path_display', '') or folder.get('path', '')
                        folder_name = os.path.basename(path_display)
                        raw_path = folder.get('path', '')
                        
                        # Check if this is a home folder
                        is_home_folder = False
                        for home_name in home_folder_names:
                            if folder_name == home_name:
                                is_home_folder = True
                                break
                            if home_name.lower() in path_display.lower() or home_name.lower() in raw_path.lower():
                                is_home_folder = True
                                break
                        
                        if is_home_folder:
                            actual_home_folders.append(folder)
                    
                    # Get non-home folders from volume scan
                    volume_folders = scan_data.get('top_folders', [])
                    non_home_folders = []
                    home_dir = os.path.expanduser('~')
                    
                    for folder in volume_folders:
                        folder_path = folder.get('path', '')
                        # Skip if this folder is in the home directory
                        if not folder_path.startswith(home_dir):
                            non_home_folders.append(folder)
                    
                    # Merge: home folders first, then other folders
                    scan_data['top_folders'] = actual_home_folders + non_home_folders
                    
                    # Update home_folders_total_bytes to use actual home folders
                    scan_data['home_folders_total_bytes'] = sum(f.get('size_bytes', 0) for f in actual_home_folders)
                    scan_data['home_folders_total_human'] = format_size(scan_data['home_folders_total_bytes'])
            
            # Check permissions before scanning Mac libraries
            permission_results = check_full_disk_access()
            scan_data['permission_status'] = permission_results
            
            if not permission_results['has_access'] and not args.skip_protected:
                print(f"\n{format_permission_status(permission_results)}")
                print("\n" + get_permission_instructions())
                print("\nContinuing scan... (protected libraries will show 0 bytes)")
                print("Use --skip-protected to skip scanning protected directories entirely.\n")
            
            # Scan Mac app libraries (unless skipped)
            if args.no_mac_libraries:
                print("→ skipping Mac app libraries (--no-mac-libraries)")
                scan_data['mac_libraries'] = {}
            elif not args.skip_protected:
                print("→ scanning Mac app libraries...")
                try:
                    mac_libraries = scan_all_mac_libraries_func()
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
            else:
                print("→ skipping protected directories (--skip-protected)")
                scan_data['mac_libraries'] = {}
            
            # Add personality
            personality_data = add_personality(scan_data)
            
            # Render terminal report
            use_color = not args.no_color
            terminal_output = render_terminal(scan_data, personality_data, use_color)
            print(terminal_output)
            
            # Generate HTML report
            if not args.terminal:
                # Auto-detect development mode if flag not provided
                use_test_reports = getattr(args, 'test_reports', False) or is_development_mode()
                reports_dir = get_reports_dir(use_test_reports=use_test_reports)
                os.makedirs(reports_dir, exist_ok=True)
                
                if use_test_reports:
                    print(f"\n📁 Using test-reports directory: {reports_dir}")
                
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
                report_filename = f"storage_{timestamp}.html"
                report_path = os.path.join(reports_dir, report_filename)
                
                render_html(scan_data, personality_data, report_path)
                
                # Save manifest
                manifest = {
                    'report_id': f"storage_{timestamp}",
                    'generated_at': datetime.datetime.now().isoformat(),
                    'scan_results': {'storage': scan_data},
                    'personality_comments': personality_data.get('comments', []),
                    'report_files': {
                        'html': report_path
                    }
                }
                manifest_path = os.path.join(reports_dir, f"storage_{timestamp}.json")
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)
                
                # Open in browser
                file_url = f"file://{report_path}"
                webbrowser.open(file_url)
                print(f"\n📊 Full report: {file_url}")
                print("   (opened in browser)")
            
            return 0
        elif args.scan_type == 'cpu':
            print(f"Starting CPU scan (Build {BUILD})...\n")
            scan_data = scan_cpu()
            
            if not scan_data:
                print("Error: Could not scan CPU/RAM")
                return 1
            
            # Export memory data if requested
            if args.export_memory:
                export_memory_to_csv(scan_data, args.export_memory)
            
            # Add personality
            personality_data = add_personality(scan_data)
            
            # Render terminal report
            use_color = not args.no_color
            terminal_output = render_terminal(scan_data, personality_data, use_color)
            print(terminal_output)
            
            # Generate HTML report
            if not args.terminal:
                # Auto-detect development mode if flag not provided
                use_test_reports = getattr(args, 'test_reports', False) or is_development_mode()
                reports_dir = get_reports_dir(use_test_reports=use_test_reports)
                os.makedirs(reports_dir, exist_ok=True)
                
                if use_test_reports:
                    print(f"\n📁 Using test-reports directory: {reports_dir}")
                
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
                report_filename = f"cpu_{timestamp}.html"
                report_path = os.path.join(reports_dir, report_filename)
                
                render_html(scan_data, personality_data, report_path)
                
                # Save manifest
                manifest = {
                    'report_id': f"cpu_{timestamp}",
                    'generated_at': datetime.datetime.now().isoformat(),
                    'scan_results': {'cpu': scan_data},
                    'personality_comments': personality_data.get('comments', []),
                    'report_files': {
                        'html': report_path
                    }
                }
                manifest_path = os.path.join(reports_dir, f"cpu_{timestamp}.json")
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)
                
                # Open in browser
                file_url = f"file://{report_path}"
                webbrowser.open(file_url)
                print(f"\n📊 Full report: {file_url}")
                print("   (opened in browser)")
            
            return 0
        elif args.scan_type == 'all':
            volume_path = select_volume(args.volume)
            if not volume_path:
                return 1
            
            print(f"\nRunning full scan (storage + CPU) - Build {BUILD}...\n")
            
            # Run storage scan
            print(f"→ scanning volume: {volume_path}")
            scan_data_storage = scan_storage(
                volume_path,
                depth=2,
                top_n=500,
                min_size_bytes=0,
                progress_callback=report_scan_progress
            )
            
            if not scan_data_storage:
                print("Error: Storage scan failed")
                return 1
            
            # Always scan home directory separately to get detailed home folder breakdown
            home_path = os.path.expanduser('~')
            if volume_path != home_path:
                print(f"\n→ scanning home directory for detailed breakdown: {home_path}")
                home_scan_data = scan_storage(
                    home_path,
                    depth=2,
                    top_n=500,
                    min_size_bytes=0,
                    progress_callback=None  # Don't show progress for home scan
                )
                
                if home_scan_data:
                    # Extract home folders from home scan
                    home_folders = home_scan_data.get('top_folders', [])
                    
                    # Identify home folder names
                    home_folder_names = ['Downloads', 'Desktop', 'Documents', 'Movies', 'Music', 'Pictures', 'Library']
                    
                    # Filter to get only actual home folders
                    actual_home_folders = []
                    for folder in home_folders:
                        path_display = folder.get('path_display', '') or folder.get('path', '')
                        folder_name = os.path.basename(path_display)
                        raw_path = folder.get('path', '')
                        
                        # Check if this is a home folder
                        is_home_folder = False
                        for home_name in home_folder_names:
                            if folder_name == home_name:
                                is_home_folder = True
                                break
                            if home_name.lower() in path_display.lower() or home_name.lower() in raw_path.lower():
                                is_home_folder = True
                                break
                        
                        if is_home_folder:
                            actual_home_folders.append(folder)
                    
                    # Get non-home folders from volume scan
                    volume_folders = scan_data_storage.get('top_folders', [])
                    non_home_folders = []
                    home_dir = os.path.expanduser('~')
                    
                    for folder in volume_folders:
                        folder_path = folder.get('path', '')
                        # Skip if this folder is in the home directory
                        if not folder_path.startswith(home_dir):
                            non_home_folders.append(folder)
                    
                    # Merge: home folders first, then other folders
                    scan_data_storage['top_folders'] = actual_home_folders + non_home_folders
                    
                    # Update home_folders_total_bytes to use actual home folders
                    scan_data_storage['home_folders_total_bytes'] = sum(f.get('size_bytes', 0) for f in actual_home_folders)
                    scan_data_storage['home_folders_total_human'] = format_size(scan_data_storage['home_folders_total_bytes'])
            
            # Check permissions before scanning Mac libraries
            try:
                if DIAGNOSTIC_LOGGING:
                    print("\n[DIAGNOSTIC] About to call check_full_disk_access()", file=sys.stderr)
                    sys.stderr.flush()
                permission_results = check_full_disk_access()
                scan_data_storage['permission_status'] = permission_results
                
                if not permission_results['has_access'] and not args.skip_protected:
                    print(f"\n{format_permission_status(permission_results)}")
                    print("(Protected libraries will show 0 bytes)\n")
            except Exception as e:
                print(f"⚠️  Warning: Permission check failed: {e}", file=sys.stderr)
                if DIAGNOSTIC_LOGGING:
                    print(f"[DIAGNOSTIC] Full traceback:", file=sys.stderr)
                    traceback.print_exc(file=sys.stderr)
                scan_data_storage['permission_status'] = {'has_access': False, 'error': str(e)}
            
            # Scan Mac app libraries (unless skipped)
            if args.no_mac_libraries:
                print("→ skipping Mac app libraries (--no-mac-libraries)")
                scan_data_storage['mac_libraries'] = {}
            elif not args.skip_protected:
                print("→ scanning Mac app libraries...")
                try:
                    if DIAGNOSTIC_LOGGING:
                        print("[DIAGNOSTIC] About to call scan_all_mac_libraries_func()", file=sys.stderr)
                        sys.stderr.flush()
                    mac_libraries = scan_all_mac_libraries_func()
                    scan_data_storage['mac_libraries'] = mac_libraries
                    # Show status if partial or interrupted
                    if mac_libraries.get('scan_status') != 'complete':
                        status = mac_libraries.get('scan_status', 'unknown')
                        print(f"   ⚠️  Mac library scan: {status}")
                except KeyboardInterrupt:
                    print("\n⚠️  Mac library scan interrupted by user")
                    scan_data_storage['mac_libraries'] = {
                        'scan_status': 'interrupted',
                        'total_size_bytes': 0,
                        'total_size_human': '0 B'
                    }
                except Exception as e:
                    print(f"\n⚠️  Mac library scan failed: {e}", file=sys.stderr)
                    if DIAGNOSTIC_LOGGING:
                        print(f"[DIAGNOSTIC] Full traceback:", file=sys.stderr)
                        traceback.print_exc(file=sys.stderr)
                    scan_data_storage['mac_libraries'] = {
                        'scan_status': 'error',
                        'error': str(e),
                        'total_size_bytes': 0,
                        'total_size_human': '0 B'
                    }
            else:
                print("→ skipping protected directories (--skip-protected)")
                scan_data_storage['mac_libraries'] = {}
            
            # Run CPU scan
            try:
                if DIAGNOSTIC_LOGGING:
                    print("\n[DIAGNOSTIC] About to call scan_cpu()", file=sys.stderr)
                    sys.stderr.flush()
                scan_data_cpu = scan_cpu()
                
                if not scan_data_cpu:
                    print("Warning: CPU scan failed, continuing with storage only")
                    scan_data_cpu = None
            except Exception as e:
                print(f"⚠️  Warning: CPU scan failed with error: {e}", file=sys.stderr)
                if DIAGNOSTIC_LOGGING:
                    print(f"[DIAGNOSTIC] Full traceback:", file=sys.stderr)
                    traceback.print_exc(file=sys.stderr)
                print("   Continuing with storage scan only...")
                scan_data_cpu = None
            
            # Combine results
            use_color = not args.no_color
            if scan_data_cpu:
                # Render both
                personality_storage = add_personality(scan_data_storage)
                personality_cpu = add_personality(scan_data_cpu)
                
                # Terminal output for storage
                terminal_output = render_terminal(scan_data_storage, personality_storage, use_color)
                print(terminal_output)
                
                # Terminal output for CPU
                print("\n")
                terminal_output_cpu = render_terminal(scan_data_cpu, personality_cpu, use_color)
                print(terminal_output_cpu)
            else:
                personality_storage = add_personality(scan_data_storage)
                terminal_output = render_terminal(scan_data_storage, personality_storage, use_color)
                print(terminal_output)
            
            # Generate separate HTML reports for both scans
            if not args.terminal:
                # Auto-detect development mode if flag not provided
                use_test_reports = getattr(args, 'test_reports', False) or is_development_mode()
                reports_dir = get_reports_dir(use_test_reports=use_test_reports)
                os.makedirs(reports_dir, exist_ok=True)
                
                if use_test_reports:
                    print(f"\n📁 Using test-reports directory: {reports_dir}")
                
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
                
                # Generate storage report
                storage_report_filename = f"storage_{timestamp}.html"
                storage_report_path = os.path.join(reports_dir, storage_report_filename)
                render_html(scan_data_storage, personality_storage, storage_report_path)
                
                # Save storage manifest
                storage_manifest = {
                    'report_id': f"storage_{timestamp}",
                    'generated_at': datetime.datetime.now().isoformat(),
                    'scan_results': {'storage': scan_data_storage},
                    'personality_comments': personality_storage.get('comments', []),
                    'report_files': {
                        'html': storage_report_path
                    }
                }
                storage_manifest_path = os.path.join(reports_dir, f"storage_{timestamp}.json")
                with open(storage_manifest_path, 'w') as f:
                    json.dump(storage_manifest, f, indent=2)
                
                # Generate CPU report if available
                if scan_data_cpu:
                    cpu_report_filename = f"cpu_{timestamp}.html"
                    cpu_report_path = os.path.join(reports_dir, cpu_report_filename)
                    render_html(scan_data_cpu, personality_cpu, cpu_report_path)
                    
                    # Save CPU manifest
                    cpu_manifest = {
                        'report_id': f"cpu_{timestamp}",
                        'generated_at': datetime.datetime.now().isoformat(),
                        'scan_results': {'cpu': scan_data_cpu},
                        'personality_comments': personality_cpu.get('comments', []),
                        'report_files': {
                            'html': cpu_report_path
                        }
                    }
                    cpu_manifest_path = os.path.join(reports_dir, f"cpu_{timestamp}.json")
                    with open(cpu_manifest_path, 'w') as f:
                        json.dump(cpu_manifest, f, indent=2)
                
                # Open both reports in browser
                storage_url = f"file://{storage_report_path}"
                webbrowser.open(storage_url)
                print(f"\n📊 Storage report: {storage_url}")
                print("   (opened in browser)")
                
                if scan_data_cpu:
                    cpu_url = f"file://{cpu_report_path}"
                    webbrowser.open(cpu_url)
                    print(f"📊 CPU report: {cpu_url}")
                    print("   (opened in browser)")
            
            return 0
    
    elif args.command == 'export':
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
    sys.exit(main())

