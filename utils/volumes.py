"""Volume detection and selection utilities.

The volume picker only offers real storage devices. Mounted disk images
(the volume you get while installing a .dmg), network shares, and
read-only mounts are classified and hidden by default — there is nothing
to clean up on them, and offering them next to "Macintosh HD" is
confusing. `--all-volumes` (or an explicit `--volume PATH`) still gets
you to them.
"""

import os
import plistlib
import subprocess
import sys

from utils.formatters import format_size
from utils.subprocess_utils import log_subprocess_call

# Filesystem types that are network shares rather than local storage.
NETWORK_FSTYPES = frozenset({
    'smbfs', 'cifs', 'afpfs', 'nfs', 'webdav', 'ftp', 'fusefs',
})

# Human-readable labels for the volume kinds we hide from the picker.
SKIP_LABELS = {
    'disk_image': 'mounted disk image',
    'network': 'network share',
    'read_only': 'read-only volume',
}


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


def is_read_only(path):
    """Return True if the mount at `path` is mounted read-only."""
    try:
        return bool(os.statvfs(path).f_flag & os.ST_RDONLY)
    except (OSError, AttributeError, ValueError):
        return False


def get_disk_image_mounts():
    """Map mount point -> backing image path for every attached disk image.

    Uses `hdiutil info -plist`, which is authoritative for .dmg and
    .sparsebundle mounts: one subprocess covers every attached image.
    Returns an empty dict if hdiutil is unavailable or unparseable, so a
    failure degrades to "we can't tell" rather than an error.
    """
    cmd = ['hdiutil', 'info', '-plist']
    try:
        log_subprocess_call('volumes.get_disk_image_mounts', cmd)
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        if result.returncode != 0:
            return {}
        info = plistlib.loads(result.stdout)
    except (OSError, ValueError, subprocess.SubprocessError, plistlib.InvalidFileException):
        return {}

    mounts = {}
    if not isinstance(info, dict):
        return mounts
    for image in info.get('images', []) or []:
        if not isinstance(image, dict):
            continue
        image_path = image.get('image-path') or ''
        for entity in image.get('system-entities', []) or []:
            if not isinstance(entity, dict):
                continue
            mount_point = entity.get('mount-point')
            if mount_point:
                mounts[os.path.normpath(mount_point)] = image_path
    return mounts


def get_mount_fstypes():
    """Map mount point -> filesystem type by parsing `mount` output.

    Lines look like:
        /dev/disk3s5 on / (apfs, local, journaled)
        //user@nas/share on /Volumes/share (smbfs, nodev, nosuid)
    Returns an empty dict if `mount` is unavailable.
    """
    cmd = ['/sbin/mount']
    try:
        log_subprocess_call('volumes.get_mount_fstypes', cmd)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return {}
        output = result.stdout
    except (OSError, ValueError, subprocess.SubprocessError):
        return {}

    fstypes = {}
    for line in output.splitlines():
        line = line.strip()
        if ' on ' not in line or not line.endswith(')'):
            continue
        # Options are always the trailing parenthesized group, so split
        # from the right — volume names may contain spaces and parens.
        head, _, options = line.rpartition(' (')
        _, _, mount_point = head.partition(' on ')
        if not mount_point:
            continue
        fstype = options.rstrip(')').split(',')[0].strip().lower()
        if fstype:
            fstypes[os.path.normpath(mount_point)] = fstype
    return fstypes


def classify_volume(path, fstype=None, disk_image_mounts=None):
    """Classify a mount point as a scannable storage device or not.

    Returns a dict with:
        kind        - 'system', 'disk', 'disk_image', 'network', 'read_only'
        scannable   - True if it belongs in the volume picker
        skip_reason - short explanation when scannable is False

    The root volume is always scannable: on modern macOS `/` is the
    sealed, read-only system volume, so the read-only rule must not
    apply to it.
    """
    normalized = os.path.normpath(path)

    if disk_image_mounts and normalized in disk_image_mounts:
        image_path = disk_image_mounts.get(normalized) or ''
        image_name = os.path.basename(image_path)
        reason = SKIP_LABELS['disk_image']
        if image_name:
            reason = '{} ({})'.format(reason, image_name)
        return {'kind': 'disk_image', 'scannable': False, 'skip_reason': reason}

    if fstype and fstype.lower() in NETWORK_FSTYPES:
        return {'kind': 'network', 'scannable': False, 'skip_reason': SKIP_LABELS['network']}

    if normalized == '/':
        return {'kind': 'system', 'scannable': True, 'skip_reason': ''}

    if is_read_only(path):
        # Catches installer images even when hdiutil is unavailable, and
        # read-only mounts have nothing to clean up either way.
        return {'kind': 'read_only', 'scannable': False, 'skip_reason': SKIP_LABELS['read_only']}

    return {'kind': 'disk', 'scannable': True, 'skip_reason': ''}


def list_volumes(include_all=False):
    """List mounted volumes.

    By default only real storage devices are returned. Pass
    include_all=True to also get disk images, network shares, and
    read-only mounts (each carries its own `kind`/`scannable` fields).
    """
    candidates = [('Macintosh HD', '/')]

    # Scan /Volumes for mounted drives
    volumes_dir = '/Volumes'
    if os.path.exists(volumes_dir):
        try:
            for item in sorted(os.listdir(volumes_dir)):
                volume_path = os.path.join(volumes_dir, item)
                # Check if it's a mount point (not a symlink to /)
                if os.path.ismount(volume_path):
                    candidates.append((item, volume_path))
        except (OSError, PermissionError):
            pass

    # One subprocess each, shared across every candidate.
    disk_image_mounts = get_disk_image_mounts()
    fstypes = get_mount_fstypes()

    volumes = []
    for name, path in candidates:
        vol_info = get_volume_info(path)
        if not vol_info:
            continue
        classification = classify_volume(
            path,
            fstypes.get(os.path.normpath(path)),
            disk_image_mounts
        )
        if not include_all and not classification['scannable']:
            continue
        volumes.append({
            'index': len(volumes) + 1,
            'name': name,
            'path': path,
            'info': vol_info,
            'kind': classification['kind'],
            'scannable': classification['scannable'],
            'skip_reason': classification['skip_reason'],
        })

    # Note: Home directory is always scanned separately, so we don't include it as an option
    # This ensures consistent reports with home folder breakdown regardless of selected volume
    
    return volumes


def describe_volume(volume):
    """One-line description of a volume for menus and status messages."""
    info = volume['info']
    return (f"{volume['name']} ({volume['path']}) - {info['total_human']}, "
            f"{info['used_human']} used ({info['used_percent']:.0f}%)")


def _print_hidden_note(hidden):
    """Tell the user what was left out of the picker, and how to get it back."""
    if not hidden:
        return
    print("\nNot shown (not a storage device):")
    for vol in hidden:
        print(f"  - {vol['name']} ({vol['path']}) - {vol['skip_reason']}")
    print("  Use --all-volumes to include them, or --volume PATH to scan one directly.")


def select_volume(volume_path=None, include_all=False):
    """Select a volume, either from argument or interactive prompt."""
    if volume_path:
        # Validate the provided path
        if os.path.exists(volume_path):
            info = get_volume_info(volume_path)
            if info:
                # Explicit path wins, but say so when it isn't a storage device.
                classification = classify_volume(
                    volume_path,
                    get_mount_fstypes().get(os.path.normpath(volume_path)),
                    get_disk_image_mounts()
                )
                if not classification['scannable']:
                    print(f"Note: '{volume_path}' looks like a "
                          f"{classification['skip_reason']}, not a storage device. "
                          f"Scanning it anyway since you asked for it.")
                return volume_path
        print(f"Warning: Volume '{volume_path}' not found or inaccessible. Prompting for selection...")
    
    # Get every volume, then decide here what the picker shows, so the
    # hidden ones can be reported instead of vanishing silently.
    all_volumes = list_volumes(include_all=True)
    volumes = [v for v in all_volumes if include_all or v.get('scannable', True)]
    shown_paths = {v['path'] for v in volumes}
    hidden = [v for v in all_volumes if v['path'] not in shown_paths]

    if not volumes:
        if all_volumes:
            # Everything got filtered out — better to offer them than to bail.
            print("Note: no plain storage volumes found; showing all mounted volumes.")
            volumes, hidden = all_volumes, []
        else:
            print("Error: No volumes found.")
            return None

    # Re-index after filtering so the menu numbers are contiguous.
    for index, vol in enumerate(volumes, start=1):
        vol['index'] = index

    # If only one volume, automatically select it
    if len(volumes) == 1:
        selected_volume = volumes[0]
        print(f"\n→ Using {describe_volume(selected_volume)}")
        _print_hidden_note(hidden)
        print("Note: Home directory will be scanned separately for detailed breakdown.\n")
        return selected_volume['path']
    
    # Multiple volumes - if there's no interactive terminal to prompt
    # (cron, launchd, pipes, CI), auto-select the default volume instead
    # of blocking on input().
    if not _stdin_is_tty():
        default_volume = volumes[0]
        print(f"\n→ Auto-selected {describe_volume(default_volume)} "
              f"[non-interactive session; use --volume PATH to choose a different volume]")
        _print_hidden_note(hidden)
        print("Note: Home directory will be scanned separately for detailed breakdown.\n")
        return default_volume['path']

    # Multiple volumes - show interactive menu
    print("\nAvailable volumes:")
    for vol in volumes:
        suffix = ''
        if not vol.get('scannable', True):
            suffix = f" [{vol['skip_reason']}]"
        print(f"{vol['index']}) {describe_volume(vol)}{suffix}")

    _print_hidden_note(hidden)

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
