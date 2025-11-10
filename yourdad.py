#!/usr/bin/env python3
"""
Dad Ware / yourdad - A personality-driven Mac cleanup tool
"""

import argparse
import os
import sys
import datetime
import json
import webbrowser
from utils.volumes import select_volume
from utils.permissions import check_full_disk_access, format_permission_status, get_permission_instructions
from scanners.storage import scan_storage, parse_size
from scanners.cpu import scan_cpu
from scanners.mac_libraries import scan_all_mac_libraries
from personality.yourdad import add_personality
from renderers.terminal import render_terminal
from renderers.html import render_html

VERSION = "0.1-poc"


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


def print_header():
    """Print branded header."""
    print("────────────────────────────────")
    print(f" Dad Ware  |  yourdad v{VERSION}")
    print("────────────────────────────────")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Dad Ware - Your friendly Mac cleanup tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'Dad Ware v{VERSION}'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
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
    
    # scan cpu
    cpu_parser = scan_subparsers.add_parser('cpu', help='Scan CPU and RAM usage')
    cpu_parser.add_argument('--terminal', action='store_true', help='Terminal report only (skip HTML)')
    cpu_parser.add_argument('--no-color', action='store_true', help='Disable ANSI colors in terminal output')
    cpu_parser.add_argument('--test-reports', action='store_true', help='Save reports to test-reports/ folder in project (for development)')
    
    # scan quick
    quick_parser = scan_subparsers.add_parser('quick', help='Quick scan (storage + CPU)')
    quick_parser.add_argument('--volume', type=str, help='Volume path to scan (default: prompt)')
    quick_parser.add_argument('--terminal', action='store_true', help='Terminal report only (skip HTML)')
    quick_parser.add_argument('--no-color', action='store_true', help='Disable ANSI colors in terminal output')
    quick_parser.add_argument('--test-reports', action='store_true', help='Save reports to test-reports/ folder in project (for development)')
    quick_parser.add_argument('--skip-protected', action='store_true', help='Skip scanning protected directories (Photos, Messages, Mail)')
    
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
            volume_path = select_volume(args.volume)
            if not volume_path:
                return 1
            
            min_size_bytes = parse_size(args.min_size) if args.min_size else 0
            
            scan_data = scan_storage(
                volume_path,
                depth=2,
                top_n=args.top,
                min_size_bytes=min_size_bytes
            )
            
            if not scan_data:
                return 1
            
            # Check permissions before scanning Mac libraries
            permission_results = check_full_disk_access()
            scan_data['permission_status'] = permission_results
            
            if not permission_results['has_access'] and not args.skip_protected:
                print(f"\n{format_permission_status(permission_results)}")
                print("\n" + get_permission_instructions())
                print("\nContinuing scan... (protected libraries will show 0 bytes)")
                print("Use --skip-protected to skip scanning protected directories entirely.\n")
            
            # Scan Mac app libraries (unless skipped)
            if not args.skip_protected:
                print("→ scanning Mac app libraries...")
                mac_libraries = scan_all_mac_libraries()
                scan_data['mac_libraries'] = mac_libraries
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
            scan_data = scan_cpu()
            
            if not scan_data:
                print("Error: Could not scan CPU/RAM")
                return 1
            
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
        elif args.scan_type == 'quick':
            volume_path = select_volume(args.volume)
            if not volume_path:
                return 1
            
            print("\nRunning quick scan (storage + CPU)...\n")
            
            # Run storage scan
            scan_data_storage = scan_storage(
                volume_path,
                depth=2,
                top_n=500,
                min_size_bytes=0
            )
            
            if not scan_data_storage:
                print("Error: Storage scan failed")
                return 1
            
            # Check permissions before scanning Mac libraries
            permission_results = check_full_disk_access()
            scan_data_storage['permission_status'] = permission_results
            
            if not permission_results['has_access'] and not args.skip_protected:
                print(f"\n{format_permission_status(permission_results)}")
                print("(Protected libraries will show 0 bytes)\n")
            
            # Scan Mac app libraries (unless skipped)
            if not args.skip_protected:
                print("→ scanning Mac app libraries...")
                mac_libraries = scan_all_mac_libraries()
                scan_data_storage['mac_libraries'] = mac_libraries
            else:
                print("→ skipping protected directories (--skip-protected)")
                scan_data_storage['mac_libraries'] = {}
            
            # Run CPU scan
            scan_data_cpu = scan_cpu()
            
            if not scan_data_cpu:
                print("Warning: CPU scan failed, continuing with storage only")
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
            
            # Generate combined HTML report
            if not args.terminal:
                # Auto-detect development mode if flag not provided
                use_test_reports = getattr(args, 'test_reports', False) or is_development_mode()
                reports_dir = get_reports_dir(use_test_reports=use_test_reports)
                os.makedirs(reports_dir, exist_ok=True)
                
                if use_test_reports:
                    print(f"\n📁 Using test-reports directory: {reports_dir}")
                
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
                report_filename = f"quick_{timestamp}.html"
                report_path = os.path.join(reports_dir, report_filename)
                
                # For combined report, we'll create a special structure
                # For now, just render storage (can enhance later)
                render_html(scan_data_storage, personality_storage, report_path)
                
                # Save manifest
                manifest = {
                    'report_id': f"quick_{timestamp}",
                    'generated_at': datetime.datetime.now().isoformat(),
                    'scan_results': {
                        'storage': scan_data_storage,
                        'cpu': scan_data_cpu
                    } if scan_data_cpu else {'storage': scan_data_storage},
                    'personality_comments': {
                        'storage': personality_storage.get('comments', []),
                        'cpu': personality_cpu.get('comments', []) if scan_data_cpu else []
                    },
                    'report_files': {
                        'html': report_path
                    }
                }
                manifest_path = os.path.join(reports_dir, f"quick_{timestamp}.json")
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)
                
                # Open in browser
                file_url = f"file://{report_path}"
                webbrowser.open(file_url)
                print(f"\n📊 Full report: {file_url}")
                print("   (opened in browser)")
            
            return 0
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

