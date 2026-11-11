"""Terminal report renderer with ANSI colors."""

import os
import socket
import datetime

from utils.llm_prompt import describe_coverage
from utils.memory import memory_summary, AVAILABLE_NOTE, APPS_NOTE
from utils.path_utils import folder_label, left_out_note
from utils.timing import format_duration
from utils.version import VERSION
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
    output.append(f"{BOLD} DAD'S REPORT CARD | Ask Dad v{VERSION}{RESET}")
    output.append(f" {hostname}  |  User: {username}")
    output.append(f" Date: {date_str}")
    output.append("─" * 40)
    output.append("")
    
    if scan_type == 'storage':
        volume = scan_data.get('volume', 'Unknown')
        volume_info = scan_data.get('volume_info', {})
        
        output.append(f"📦 {BOLD}STORAGE SCAN{RESET}: {volume}")
        # A drive that is not the one home lives on gets a report about that
        # drive and nothing else. Saying so here stops the missing home
        # folders, libraries and caches from reading as a broken scan.
        if scan_data.get('scan_scope') == 'other_volume':
            output.append("   This drive only. Home folders, app libraries, caches")
            output.append("   and snapshots are on the startup disk.")
        output.append("")
        
        # Top Folders
        top_folders = scan_data.get('top_folders', [])[:10]
        if top_folders:
            output.append(f"{BOLD}Top Folders (depth 2):{RESET}")
            for folder in top_folders:
                path = folder_label(folder, scan_data.get('home_path') or os.path.expanduser('~'))
                size = folder.get('size_human', '0 B')
                # Truncate long paths
                if len(path) > 40:
                    path = '...' + path[-37:]
                output.append(f"  {path:<40} {size:>10}")
                note = left_out_note(folder)
                if note:
                    output.append(f"    {note}")
            coverage = ('' if scan_data.get('scan_scope') == 'other_volume'
                        else describe_coverage(scan_data))
            if coverage:
                output.append(f"  {coverage}")
            output.append("")
        
        # Top Files
        top_files = scan_data.get('top_files', [])[:10]
        if top_files:
            output.append(f"{BOLD}Top 10 Largest Files & Apps:{RESET}")
            for file_info in top_files:
                path = file_info.get('path', '')
                size = file_info.get('size_human', '0 B')
                basename = os.path.basename(path)
                # Truncate long names
                if len(basename) > 40:
                    basename = '...' + basename[-37:]
                output.append(f"  {basename:<40} {size:>10}")
            output.append("")
        
        # Hidden app caches. Absent from older scan data, in which case the
        # section is simply skipped and the report reads as it always did.
        hidden = scan_data.get('hidden_caches') or {}
        cache_entries = hidden.get('entries') or []
        if cache_entries:
            total_caches = hidden.get('total_size_human', '0 B')
            # What a cache is, and why clearing one doesn't stay cleared, is
            # the report card's job - it has the room to say it properly.
            # Here: the number, the list, and any caveat that changes what
            # the number means.
            output.append(f"{BOLD}Hidden App Storage:{RESET} {total_caches} total")
            for entry in cache_entries[:10]:
                name = entry.get('app_name', 'Unknown')
                size = entry.get('size_human', '0 B')
                if len(name) > 40:
                    name = name[:37] + '...'
                output.append(f"  {name:<40} {size:>10}")
            if hidden.get('permission_denied'):
                output.append("  (some cache folders are protected - sizes may be incomplete)")
            if hidden.get('scan_status') == 'partial':
                output.append("  (scan ran out of time - total is a floor, not the whole story)")
            output.append("")

        # Local snapshots. Absent from older scan data, in which case the
        # section is simply skipped.
        snapshot_data = scan_data.get('snapshots') or {}
        if snapshot_data.get('status') == 'complete' and snapshot_data.get('count'):
            count = snapshot_data['count']
            oldest = snapshot_data.get('oldest_age_days')
            stale = snapshot_data.get('stale_count', 0)
            output.append(f"{BOLD}Local Snapshots:{RESET} {count}")
            if oldest is not None:
                output.append(f"  Oldest: {oldest} day{'s' if oldest != 1 else ''} old")
            if stale:
                output.append("  Older than macOS usually keeps. To reclaim now, run yourself:")
                output.append("    tmutil thinlocalsnapshots / 9999999999 4")
            output.append("")

        # Volume Summary
        total = volume_info.get('total_human', '0 B')
        used = volume_info.get('used_human', '0 B')
        free = volume_info.get('free_human', '0 B')
        used_percent = volume_info.get('used_percent', 0)
        
        output.append(f"Total: {total}  |  Used: {used} ({used_percent:.0f}%)  |  Free: {free}")
        output.append("")
        
    
    elif scan_type == 'cpu':
        output.append(f"🔥 {BOLD}CPU & RAM SNAPSHOT{RESET}")
        output.append("")

        # Memory overview - every figure comes from utils.memory, the same
        # numbers the HTML report and the AI prompt print.
        mem = memory_summary(scan_data)

        if mem['total_bytes'] > 0:
            used = mem['used_text']
            if mem['used_percent_text']:
                used += f" ({mem['used_percent_text']})"
            output.append(f"{BOLD}Memory Overview:{RESET}")
            output.append(f"  Total RAM: {mem['total_text']}  |  Used: {used}")

            pressure_level = mem['pressure']
            pressure_color = RED if pressure_level == 'high' else YELLOW if pressure_level == 'medium' else GREEN if pressure_level == 'low' else ''
            pressure_emoji = '🔴' if pressure_level == 'high' else '🟡' if pressure_level == 'medium' else '🟢' if pressure_level == 'low' else '⚪'
            output.append(f"  Free: {mem['free_text']}  |  Available: {mem['available_text']} ({AVAILABLE_NOTE})")
            pressure_line = f"  Pressure: {pressure_color}{pressure_emoji} {pressure_level}{RESET}"
            if mem['swap_used_bytes'] is not None:
                pressure_line += f"  |  Swap in use: {mem['swap_used_text']}"
            output.append(pressure_line)
            output.append(f"  Memory used by apps: {mem['apps_text']} (approx., {APPS_NOTE})")
            output.append("")

        # Memory hogs
        memory_hogs = scan_data.get('memory_hogs', [])
        if memory_hogs:
            output.append(f"{BOLD}Apps Using Most Memory:{RESET} (approx.)")
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
    
    # Permission warnings — honest-denial copy per the tier matrix in
    # PERMISSIONS-PLAN.md: anything the scan couldn't see says so, with the
    # fix path. Never a silent zero.
    if scan_type == 'storage':
        permission_status = scan_data.get('permission_status', {})

        folders = (permission_status or {}).get('folders') or {}
        denied_folders = [name for name, info in folders.items()
                          if isinstance(info, dict) and info.get('status') == 'denied']
        if denied_folders:
            output.append("─" * 40)
            output.append(f"{YELLOW}{BOLD}🚪 Folders I couldn't check:{RESET}")
            output.append(f"  No access to: {', '.join(denied_folders)}")
            output.append("  Left out of the numbers above, not counted as zero.")
            output.append("  Change it: System Settings → Privacy & Security → Files & Folders")
            output.append("")

        if permission_status and not permission_status.get('has_access', True):
            missing = permission_status.get('missing_permissions', [])
            if missing:
                output.append("─" * 40)
                output.append(f"{YELLOW}{BOLD}⚠️  Couldn't measure everything:{RESET}")
                libs = ", ".join(m.title() for m in missing)
                output.append(f"  {libs} need Full Disk Access, so they're")
                output.append(f"  left blank above rather than counted as zero.")
                # How to fix it belongs at the end of the run, after the
                # report - a grant cannot change the run in progress, and
                # printing the steps twice just made the report noisier.
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
        output.append(f"Scan completed in {format_duration(duration)}")
    output.append("─" * 40)
    output.append("")
    
    return "\n".join(output)

