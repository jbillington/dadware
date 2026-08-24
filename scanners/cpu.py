"""CPU and RAM scanner."""

import subprocess
import re
import sys
import os
import traceback
from typing import Any, Dict, List, Optional

from utils.subprocess_utils import log_subprocess_call, DIAGNOSTIC_LOGGING

# Ordered table mapping process-name substrings to an app family label, used
# by identify_memory_hogs() to group related processes (e.g. Chrome and its
# helpers) together. Order matters: entries are checked top-to-bottom and the
# first match wins, so more specific families must come before broader ones.
# The 'helper' grouping and the system-process catch-all are handled after
# this table (see identify_memory_hogs) and must stay last.
APP_FAMILIES = [
    (('chrome', 'chromium'), 'Chrome'),
    (('safari', 'webkit', 'webcontent'), 'Safari'),  # WebKit is Safari's rendering engine
    (('messages', 'imessage'), 'Messages'),
    (('mail',), 'Mail'),
    (('firefox',), 'Firefox'),
    (('slack',), 'Slack'),
    (('teams',), 'Teams'),
    (('spotify',), 'Spotify'),
    (('photoshop',), 'Photoshop'),
]

# Substrings that identify a system/background process, used as the final
# catch-all in identify_memory_hogs() after APP_FAMILIES and the helper check.
SYSTEM_PROCESS_SUBSTRINGS = ('kernel', 'launchd', 'windowserver', 'com.apple', 'system')


def get_memory_pressure() -> Optional[Dict[str, Any]]:
    """
    Get memory pressure information from vm_stat.
    Returns dict with memory statistics and pressure level.
    """
    try:
        cmd = ['vm_stat']
        log_subprocess_call("get_memory_pressure()", cmd)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return None

        # Parse vm_stat output
        # Example: "Pages free:                               123456."
        lines = result.stdout.strip().split('\n')

        stats = {}
        for line in lines[1:]:  # Skip first line (header)
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().rstrip('.')
                try:
                    stats[key] = int(value)
                except ValueError:
                    continue

        # Get page size (usually 4096 bytes on modern Macs)
        page_size = 4096
        page_size_match = re.search(r'page size of (\d+) bytes', result.stdout)
        if page_size_match:
            page_size = int(page_size_match.group(1))

        # Calculate memory values in bytes
        pages_free = stats.get('Pages free', 0)
        pages_active = stats.get('Pages active', 0)
        pages_inactive = stats.get('Pages inactive', 0)
        pages_wired = stats.get('Pages wired down', 0)
        pages_compressed = stats.get('Pages occupied by compressor', 0)

        free_bytes = pages_free * page_size
        active_bytes = pages_active * page_size
        inactive_bytes = pages_inactive * page_size
        wired_bytes = pages_wired * page_size
        compressed_bytes = pages_compressed * page_size

        # Calculate memory pressure (simplified)
        # High pressure = low available memory (free + inactive) + high swapping
        pages_swapped_in = stats.get('Swapins', 0)
        pages_swapped_out = stats.get('Swapouts', 0)

        # Calculate available memory (free + inactive pages that can be reclaimed)
        # This is more accurate than just "free" pages
        available_bytes = free_bytes + inactive_bytes
        # RAM stays BINARY (1024-based) on purpose, unlike disk sizes.
        # Apple reports a 16 GiB module as "16 GB" in About This Mac and
        # Activity Monitor, because RAM is manufactured in powers of two.
        # Converting it to decimal here would print "17.2 GB" for the same
        # stick and disagree with every other place the user could check.
        # Disk sizes go the other way - see utils/formatters.format_size.
        available_gb = available_bytes / (1024**3)
        free_gb = free_bytes / (1024**3)
        
        # Determine pressure level based on available memory (not just free)
        # This aligns with how macOS actually manages memory
        pressure = 'low'
        if available_gb < 1.0 or pages_swapped_out > 1000:
            pressure = 'high'
        elif available_gb < 2.0 or pages_swapped_out > 100:
            pressure = 'medium'

        return {
            'free_bytes': free_bytes,
            'active_bytes': active_bytes,
            'inactive_bytes': inactive_bytes,
            'wired_bytes': wired_bytes,
            'compressed_bytes': compressed_bytes,
            'available_bytes': available_bytes,  # free + inactive
            'free_gb': free_gb,
            'available_gb': available_gb,  # free + inactive
            'active_gb': active_bytes / (1024**3),
            'wired_gb': wired_bytes / (1024**3),
            'compressed_gb': compressed_bytes / (1024**3),
            'swapins': pages_swapped_in,
            'swapouts': pages_swapped_out,
            'pressure': pressure,
            'page_size': page_size
        }

    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        print(f"⚠️  Warning: Memory pressure scan failed: {e}", file=sys.stderr)
        if DIAGNOSTIC_LOGGING:
            print("[DIAGNOSTIC] Full traceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        return None


def identify_memory_hogs(processes: List[Dict[str, Any]], threshold_mb: float = 50) -> List[Dict[str, Any]]:
    """
    Identify processes using significant memory.

    Args:
        processes: List of process dicts with memory info
        threshold_mb: Minimum memory usage to be considered a hog (MB)

    Returns:
        List of memory hog processes with categorization
    """
    hogs = []

    # Group processes by app (combine Chrome helpers, etc.)
    app_memory = {}

    for proc in processes:
        name = proc.get('name', '').lower()
        mem_mb = proc.get('memory_mb', 0)
        full_name = proc.get('name', 'Unknown')

        # Categorize by app family, checking the data table in order first
        app_name = None
        for substrings, family_name in APP_FAMILIES:
            if any(substring in name for substring in substrings):
                app_name = family_name
                break

        if app_name is None:
            if 'helper' in name or 'helper' in full_name.lower():
                # Group helper processes
                app_name = 'Helper Processes'
            elif any(sys_name in name for sys_name in SYSTEM_PROCESS_SUBSTRINGS):
                # Group system processes
                app_name = 'System Processes'
            else:
                app_name = full_name  # Keep individual process names for unknown processes

        if app_name in app_memory:
            app_memory[app_name]['total_mb'] += mem_mb
            app_memory[app_name]['process_count'] += 1
        else:
            app_memory[app_name] = {
                'name': app_name,
                'total_mb': mem_mb,
                'process_count': 1
            }

    # Filter apps using significant memory
    for app_name, info in app_memory.items():
        if info['total_mb'] >= threshold_mb:
            hogs.append(info)

    # Sort by memory usage
    hogs.sort(key=lambda x: x['total_mb'], reverse=True)

    return hogs


def scan_cpu() -> Optional[Dict[str, Any]]:
    """Scan CPU and RAM usage, return structured data."""
    try:
        # Run ps aux to get process info
        cmd = ['ps', 'aux']
        log_subprocess_call("scan_cpu() - ps aux", cmd)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return None

        processes = []
        lines = result.stdout.strip().split('\n')

        # Skip header line
        for line in lines[1:]:
            parts = line.split(None, 10)  # Split on whitespace, max 11 parts
            if len(parts) < 11:
                continue

            try:
                # ps aux format: USER PID %CPU %MEM VSZ RSS TT STAT START TIME COMMAND
                cpu_percent = float(parts[2])
                mem_percent = float(parts[3])
                rss_kb = int(parts[5])  # Resident Set Size in KB
                command = parts[10]

                # Extract process name (first part of command)
                process_name = command.split()[0] if command else 'Unknown'
                # Remove path, keep just name
                process_name = process_name.split('/')[-1]

                processes.append({
                    'name': process_name,
                    'cpu_percent': cpu_percent,
                    'memory_percent': mem_percent,
                    'memory_mb': rss_kb / 1024.0,  # Convert KB to MB
                    'command': command
                })
            except (ValueError, IndexError):
                continue

        # Sort by CPU usage for top processes
        processes_by_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)
        top_cpu_processes = processes_by_cpu[:5]  # Top 5 by CPU

        # Sort by memory usage for top memory processes
        processes_by_mem = sorted(processes, key=lambda x: x['memory_mb'], reverse=True)
        top_memory_processes = processes_by_mem[:25]  # Top 25 by memory (increased for better visibility)

        # Get system memory info
        try:
            cmd = ['sysctl', 'hw.memsize']
            log_subprocess_call("scan_cpu() - sysctl hw.memsize", cmd)
            mem_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=2
            )
            total_memory_bytes = 0
            if mem_result.returncode == 0:
                match = re.search(r'(\d+)', mem_result.stdout)
                if match:
                    total_memory_bytes = int(match.group(1))
        except (subprocess.SubprocessError, OSError, ValueError) as e:
            print(f"⚠️  Warning: Could not determine total memory via sysctl: {e}", file=sys.stderr)
            if DIAGNOSTIC_LOGGING:
                print("[DIAGNOSTIC] Full traceback:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
            total_memory_bytes = 0

        # Get memory pressure info
        memory_pressure = get_memory_pressure()

        # Identify memory hogs (apps using >50MB - very low threshold to catch distributed memory)
        memory_hogs = identify_memory_hogs(processes, threshold_mb=50)

        # Calculate total memory used by all processes
        total_used_mb = sum(p['memory_mb'] for p in processes)
        
        # Calculate metrics
        total_processes = len(processes)
        processes_over_100mb = len([p for p in processes if p['memory_mb'] > 100])
        processes_over_500mb = len([p for p in processes if p['memory_mb'] > 500])
        processes_over_1gb = len([p for p in processes if p['memory_mb'] > 1024])
        avg_memory_mb = total_used_mb / total_processes if total_processes > 0 else 0
        
        # Calculate memory distribution - many small processes vs few large ones
        small_processes_mb = sum(p['memory_mb'] for p in processes if p['memory_mb'] < 100)
        medium_processes_mb = sum(p['memory_mb'] for p in processes if 100 <= p['memory_mb'] < 500)
        large_processes_mb = sum(p['memory_mb'] for p in processes if p['memory_mb'] >= 500)
        small_processes_count = len([p for p in processes if p['memory_mb'] < 100])

        return {
            'scan_type': 'cpu',
            'top_processes': top_cpu_processes,
            'top_memory_processes': top_memory_processes,
            'all_processes': processes_by_mem,  # All processes sorted by memory (for export)
            'memory_hogs': memory_hogs,
            'total_memory_bytes': total_memory_bytes,
            'total_memory_gb': total_memory_bytes / (1024**3) if total_memory_bytes > 0 else 0,
            'total_used_mb': total_used_mb,
            'total_used_gb': total_used_mb / 1024.0,
            'memory_pressure': memory_pressure,
            'process_metrics': {
                'total_processes': total_processes,
                'processes_over_100mb': processes_over_100mb,
                'processes_over_500mb': processes_over_500mb,
                'processes_over_1gb': processes_over_1gb,
                'avg_memory_mb': avg_memory_mb,
                'small_processes_mb': small_processes_mb,
                'medium_processes_mb': medium_processes_mb,
                'large_processes_mb': large_processes_mb,
                'small_processes_count': small_processes_count
            }
        }

    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        print(f"⚠️  Warning: CPU/RAM scan failed: {e}", file=sys.stderr)
        if DIAGNOSTIC_LOGGING:
            print("[DIAGNOSTIC] Full traceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        return None

