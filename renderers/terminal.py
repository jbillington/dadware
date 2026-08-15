"""Terminal report renderer with ANSI colors."""

import os
import socket
import datetime

from utils.formatters import format_size, get_status_emoji, get_status_text

# ANSI color codes
RESET = '\033[0m'
BOLD = '\033[1m'
RED = '\033[31m'
YELLOW = '\033[33m'
GREEN = '\033[32m'
BLUE = '\033[34m'
CYAN = '\033[36m'

# Palettes used by render_terminal(). Built from the module-level constants
# above but never mutate them, so colors aren't lost across calls.
_COLOR_PALETTE = {
    'RESET': RESET, 'BOLD': BOLD, 'RED': RED,
    'YELLOW': YELLOW, 'GREEN': GREEN, 'BLUE': BLUE, 'CYAN': CYAN,
}
_NO_COLOR_PALETTE = {key: '' for key in _COLOR_PALETTE}


def render_terminal(scan_data, personality_data, use_color=True):
    """Render terminal report."""
    output = []

    # Color control — build a local palette instead of mutating module globals,
    # so a use_color=False call doesn't permanently blank colors for the process.
    if use_color:
        palette = _COLOR_PALETTE
    else:
        palette = _NO_COLOR_PALETTE
    RESET = palette['RESET']
    BOLD = palette['BOLD']
    RED = palette['RED']
    YELLOW = palette['YELLOW']
    GREEN = palette['GREEN']
    BLUE = palette['BLUE']
    CYAN = palette['CYAN']

    # Get metadata
    hostname = socket.gethostname()
    username = os.getenv('USER', 'Unknown')
    now = datetime.datetime.now()
    date_str = now.strftime('%B %d, %Y %H:%M')
    
    scan_type = scan_data.get('scan_type', 'unknown')
    status = personality_data.get('status', 'ok')
    comments = personality_data.get('comments', [])
    tips = personality_data.get('tips', [])
    
    # Header
    output.append("")
    output.append("─" * 40)
    output.append(f"{BOLD} DAD'S REPORT CARD — Dad Ware v0.1{RESET}")
    output.append(f" {hostname}  |  User: {username}")
    output.append(f" Date: {date_str}")
    output.append("─" * 40)
    output.append("")
    
    if scan_type == 'storage':
        volume = scan_data.get('volume', 'Unknown')
        volume_info = scan_data.get('volume_info', {})
        
        output.append(f"📦 {BOLD}STORAGE SCAN{RESET} — {volume}")
        output.append("")
        
        # Top Folders
        top_folders = scan_data.get('top_folders', [])[:10]
        if top_folders:
            output.append(f"{BOLD}Top Folders (depth 2):{RESET}")
            for folder in top_folders:
                path = folder.get('path', '')
                size = folder.get('size_human', '0 B')
                # Truncate long paths
                if len(path) > 40:
                    path = '...' + path[-37:]
                output.append(f"  {path:<40} {size:>10}")
            output.append("")
        
        # Top Files
        top_files = scan_data.get('top_files', [])[:10]
        if top_files:
            output.append(f"{BOLD}Top 10 Largest Files:{RESET}")
            for file_info in top_files:
                path = file_info.get('path', '')
                size = file_info.get('size_human', '0 B')
                basename = os.path.basename(path)
                # Truncate long names
                if len(basename) > 40:
                    basename = '...' + basename[-37:]
                output.append(f"  {basename:<40} {size:>10}")
            output.append("")
        
        # Volume Summary
        total = volume_info.get('total_human', '0 B')
        used = volume_info.get('used_human', '0 B')
        free = volume_info.get('free_human', '0 B')
        used_percent = volume_info.get('used_percent', 0)
        
        output.append(f"Total: {total}  |  Used: {used} ({used_percent:.0f}%)  |  Free: {free}")
        output.append("")
        
        # Skipped count
        skipped = scan_data.get('skipped_count', 0)
        if skipped > 0:
            output.append(f"({skipped} items skipped due to permissions)")
            output.append("")
    
    elif scan_type == 'cpu':
        output.append(f"🔥 {BOLD}CPU & RAM SNAPSHOT{RESET}")
        output.append("")

        # Memory overview
        total_mem_gb = scan_data.get('total_memory_gb', 0)
        total_used_gb = scan_data.get('total_used_gb', 0)
        memory_pressure = scan_data.get('memory_pressure', {})

        if total_mem_gb > 0:
            used_percent = (total_used_gb / total_mem_gb) * 100 if total_mem_gb > 0 else 0
            output.append(f"{BOLD}Memory Overview:{RESET}")
            output.append(f"  Total RAM: {total_mem_gb:.1f} GB  |  Used: {total_used_gb:.1f} GB ({used_percent:.0f}%)")

            if memory_pressure:
                pressure_level = memory_pressure.get('pressure', 'low')
                # Calculate free memory as total - used (more accurate than vm_stat)
                total_mem_gb = scan_data.get('total_memory_gb', 0)
                total_used_gb = scan_data.get('total_used_gb', 0)
                free_gb = max(0, total_mem_gb - total_used_gb) if total_mem_gb > 0 else memory_pressure.get('free_gb', 0)
                pressure_color = RED if pressure_level == 'high' else YELLOW if pressure_level == 'medium' else GREEN
                pressure_emoji = '🔴' if pressure_level == 'high' else '🟡' if pressure_level == 'medium' else '🟢'
                output.append(f"  Free RAM: {free_gb:.1f} GB  |  Pressure: {pressure_color}{pressure_emoji} {pressure_level}{RESET}")
            output.append("")

        # Memory hogs
        memory_hogs = scan_data.get('memory_hogs', [])
        if memory_hogs:
            output.append(f"{BOLD}Apps Using Most Memory:{RESET}")
            for hog in memory_hogs[:5]:  # Top 5 memory hogs
                name = hog.get('name', 'Unknown')
                mem_mb = hog.get('total_mb', 0)
                mem_gb = mem_mb / 1024.0
                process_count = hog.get('process_count', 1)
                mem_str = f"{mem_gb:.1f} GB" if mem_gb >= 1 else f"{mem_mb:.0f} MB"
                process_str = f"({process_count} processes)" if process_count > 1 else ""
                # Truncate long names
                if len(name) > 25:
                    name = name[:22] + '...'
                output.append(f"  {name:<25} {mem_str:>10} {process_str}")
            output.append("")

        # Top CPU processes
        top_processes = scan_data.get('top_processes', [])
        if top_processes:
            output.append(f"{BOLD}Top CPU Usage:{RESET}")
            for proc in top_processes:
                name = proc.get('name', 'Unknown')
                cpu = proc.get('cpu_percent', 0)
                mem = proc.get('memory_mb', 0)
                mem_str = f"{mem:.1f} MB" if mem < 1024 else f"{mem/1024:.1f} GB"
                # Truncate long names
                if len(name) > 25:
                    name = name[:22] + '...'
                output.append(f"  {name:<25} {cpu:>6.1f}% CPU    {mem_str:>10} RAM")
            output.append("")
    
    # Personality comments
    if comments:
        output.append(f"💬 {BOLD}Dad says:{RESET}")
        for comment in comments:
            output.append(f'   "{comment}"')
        output.append("")
    
    # Status
    emoji = get_status_emoji(status)
    status_text = get_status_text(status)
    status_color = RED if status == 'critical' else YELLOW if status == 'warn' else GREEN
    output.append(f"Status: {status_color}{emoji} {status_text}{RESET}")
    output.append("")
    
    # Permission warnings
    if scan_type == 'storage':
        permission_status = scan_data.get('permission_status', {})
        if permission_status and not permission_status.get('has_access', True):
            missing = permission_status.get('missing_permissions', [])
            if missing:
                output.append("─" * 40)
                output.append(f"{YELLOW}{BOLD}⚠️  Permission Notice:{RESET}")
                libs = ", ".join(m.title() for m in missing)
                output.append(f"  Full Disk Access required for: {libs}")
                output.append(f"  Protected libraries show 0 bytes without permission")
                output.append(f"  See GRANT-PERMISSIONS.md for setup instructions")
                output.append("")
    
    # Tips
    if tips:
        output.append("─" * 40)
        output.append(f"{BOLD}💡 Quick Wins:{RESET}")
        for tip in tips:
            output.append(f"  • {tip}")
        output.append("")
    
    # Footer
    duration = scan_data.get('duration_seconds', 0)
    output.append("─" * 40)
    if duration > 0:
        output.append(f"Scan completed in {duration:.1f} seconds")
    output.append("─" * 40)
    output.append("")
    
    return "\n".join(output)

