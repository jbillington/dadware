"""Volume detection and selection utilities."""

import os
import stat


def format_size(bytes):
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"


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
    
    # Add home directory option
    home = os.path.expanduser('~')
    home_info = get_volume_info(home)
    if home_info:
        volumes.append({
            'index': len(volumes) + 1,
            'name': 'Home directory only',
            'path': home,
            'info': home_info,
            'is_home': True
        })
    
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
    
    # Interactive selection
    volumes = list_volumes()
    
    if not volumes:
        print("Error: No volumes found.")
        return None
    
    print("\nAvailable volumes:")
    for vol in volumes:
        info = vol['info']
        if vol.get('is_home'):
            print(f"{vol['index']}) {vol['name']} (~/) - quickest")
        else:
            print(f"{vol['index']}) {vol['name']} ({vol['path']}) - {info['total_human']}, "
                  f"{info['used_human']} used ({info['used_percent']:.0f}%)")
    
    default = volumes[-1]['index']  # Home directory is last
    print(f"\nPick one [{default}]: ", end='')
    
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

