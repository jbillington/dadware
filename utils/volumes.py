"""Volume detection and selection utilities."""

import os
import stat
import sys

from utils.formatters import format_size


def _stdin_is_tty():
    """Return True if stdin is an interactive terminal.

    Treat any failure to determine this (stdin is None, lacks isatty,
    or isatty() raises) as "not a TTY" so non-interactive launch
    contexts (cron, launchd, pipes, CI) never block on input().
    """
    try:
        return bool(sys.stdin and sys.stdin.isatty())
    except (AttributeError, ValueError, OSError):
        return False


def get_volume_info(path):
    """Get volume information using statvfs."""
    try:
        statvfs = os.statvfs(path)
        # Calculate sizes
        total_bytes = statvfs.f_frsize * statvfs.f_blocks
        free_bytes = statvfs.f_frsize * statvfs.f_bavail
        used_bytes = total_bytes - (statvfs.f_frsize * statvfs.f_bfree)
        used_percent = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0
        
        return {
            'path': path,
            'total_bytes': total_bytes,
            'used_bytes': used_bytes,
            'free_bytes': free_bytes,
            'used_percent': used_percent,
            'total_human': format_size(total_bytes),
            'used_human': format_size(used_bytes),
            'free_human': format_size(free_bytes)
        }
    except (OSError, PermissionError):
        return None


def list_volumes():
    """List all mounted volumes."""
    volumes = []
    
    # Add root volume
    root_info = get_volume_info('/')
    if root_info:
        volumes.append({
            'index': len(volumes) + 1,
            'name': 'Macintosh HD',
            'path': '/',
            'info': root_info
        })
    
    # Scan /Volumes for mounted drives
    volumes_dir = '/Volumes'
    if os.path.exists(volumes_dir):
        try:
            for item in os.listdir(volumes_dir):
                volume_path = os.path.join(volumes_dir, item)
                # Check if it's a mount point (not a symlink to /)
                if os.path.ismount(volume_path):
                    vol_info = get_volume_info(volume_path)
                    if vol_info:
                        volumes.append({
                            'index': len(volumes) + 1,
                            'name': item,
                            'path': volume_path,
                            'info': vol_info
                        })
        except (OSError, PermissionError):
            pass
    
    # Note: Home directory is always scanned separately, so we don't include it as an option
    # This ensures consistent reports with home folder breakdown regardless of selected volume
    
    return volumes


def select_volume(volume_path=None):
    """Select a volume, either from argument or interactive prompt."""
    if volume_path:
        # Validate the provided path
        if os.path.exists(volume_path):
            info = get_volume_info(volume_path)
            if info:
                return volume_path
        print(f"Warning: Volume '{volume_path}' not found or inaccessible. Prompting for selection...")
    
    # Get list of volumes
    volumes = list_volumes()
    
    if not volumes:
        print("Error: No volumes found.")
        return None
    
    # If only one volume, automatically select it
    if len(volumes) == 1:
        selected_volume = volumes[0]
        info = selected_volume['info']
        print(f"\n→ Using {selected_volume['name']} ({selected_volume['path']}) - "
              f"{info['total_human']}, {info['used_human']} used ({info['used_percent']:.0f}%)")
        print("Note: Home directory will be scanned separately for detailed breakdown.\n")
        return selected_volume['path']
    
    # Multiple volumes - if there's no interactive terminal to prompt
    # (cron, launchd, pipes, CI), auto-select the default volume instead
    # of blocking on input().
    if not _stdin_is_tty():
        default_volume = volumes[0]
        info = default_volume['info']
        print(f"\n→ Auto-selected {default_volume['name']} ({default_volume['path']}) - "
              f"{info['total_human']}, {info['used_human']} used ({info['used_percent']:.0f}%) "
              f"[non-interactive session; use --volume PATH to choose a different volume]")
        print("Note: Home directory will be scanned separately for detailed breakdown.\n")
        return default_volume['path']

    # Multiple volumes - show interactive menu
    print("\nAvailable volumes:")
    for vol in volumes:
        info = vol['info']
        print(f"{vol['index']}) {vol['name']} ({vol['path']}) - {info['total_human']}, "
              f"{info['used_human']} used ({info['used_percent']:.0f}%)")
    
    default = volumes[0]['index']  # Default to first volume (usually root)
    print(f"\nNote: Home directory will be scanned separately for detailed breakdown.")
    print(f"Pick one [{default}]: ", end='')
    
    try:
        choice = input().strip()
        if not choice:
            choice = str(default)
        
        choice_num = int(choice)
        selected = next((v for v in volumes if v['index'] == choice_num), None)
        
        if selected:
            return selected['path']
        else:
            print(f"Invalid choice: {choice}")
            return None
    except (ValueError, KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return None

