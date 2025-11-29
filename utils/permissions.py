"""Permission detection and checking for macOS protected directories."""

import os
import subprocess
import sys

# Import diagnostic logging from main module if available
try:
    from yourdad import DIAGNOSTIC_LOGGING
except ImportError:
    DIAGNOSTIC_LOGGING = False

def log_subprocess_call(location, cmd, **kwargs):
    """Log subprocess call for diagnostics."""
    if DIAGNOSTIC_LOGGING:
        print(f"\n[DIAGNOSTIC] {location}: About to call subprocess.run()", file=sys.stderr)
        print(f"[DIAGNOSTIC] Command: {cmd}", file=sys.stderr)
        print(f"[DIAGNOSTIC] Command type: {type(cmd)}", file=sys.stderr)
        if isinstance(cmd, (list, tuple)):
            print(f"[DIAGNOSTIC] Command length: {len(cmd)}", file=sys.stderr)
            for i, arg in enumerate(cmd):
                print(f"[DIAGNOSTIC]   Arg[{i}]: {repr(arg)} (type: {type(arg).__name__})", file=sys.stderr)
        print(f"[DIAGNOSTIC] Additional args: {kwargs}", file=sys.stderr)
        sys.stderr.flush()


def detect_swift_helper():
    """
    Detect if Swift helper app is available.
    
    Returns:
        str or None: Path to helper app bundle, or None if not found
    """
    # Check common locations for bundled helper
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'macos-helper', 'build', 'PermissionHelper.app'),
        os.path.join(os.path.expanduser('~'), '.dadware', 'PermissionHelper.app'),
        '/Applications/DadWare.app/Contents/Resources/PermissionHelper.app',
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            executable = os.path.join(path, 'Contents', 'MacOS', 'PermissionHelper')
            if os.path.exists(executable):
                return path
    
    return None


def try_swift_helper_check():
    """
    Try to use Swift helper to check permissions (if available).
    
    Returns:
        dict or None: Permission results from Swift helper, or None if not available
    """
    helper_path = detect_swift_helper()
    if not helper_path:
        return None
    
    executable = os.path.join(helper_path, 'Contents', 'MacOS', 'PermissionHelper')
    
    # Defensive check: executable must exist
    if not executable or not os.path.exists(executable):
        return None
    
    try:
        # Swift helper would need to output JSON or be called via API
        # For now, this is a placeholder for future integration
        # When Mac app is built, this can call the helper properly
        cmd = [executable, '--check']
        log_subprocess_call("try_swift_helper_check()", cmd)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Parse JSON output (when implemented)
            import json
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError, TypeError):
        pass
    
    return None


def check_messages_access():
    """Check if we can access the Messages library."""
    messages_path = os.path.expanduser('~/Library/Messages')
    
    if not os.path.exists(messages_path):
        return {'has_access': False, 'reason': 'path_not_found'}
    
    try:
        # Try to list directory contents
        os.listdir(messages_path)
        # Try to get a file size (if any files exist)
        try:
            for item in os.listdir(messages_path):
                item_path = os.path.join(messages_path, item)
                if os.path.isfile(item_path):
                    os.path.getsize(item_path)
                    break
        except (OSError, PermissionError):
            pass
        return {'has_access': True, 'reason': 'success'}
    except (OSError, PermissionError):
        return {'has_access': False, 'reason': 'permission_denied'}


def check_mail_access():
    """Check if we can access the Mail library."""
    mail_path = os.path.expanduser('~/Library/Mail')
    
    if not os.path.exists(mail_path):
        return {'has_access': False, 'reason': 'path_not_found'}
    
    try:
        # Try to list directory contents
        os.listdir(mail_path)
        return {'has_access': True, 'reason': 'success'}
    except (OSError, PermissionError):
        return {'has_access': False, 'reason': 'permission_denied'}


def check_photos_access():
    """Check if we can access Photos libraries."""
    home = os.path.expanduser('~')
    photos_path = os.path.join(home, 'Pictures', 'Photos Library.photoslibrary')
    
    if not os.path.exists(photos_path):
        return {'has_access': False, 'reason': 'path_not_found'}
    
    try:
        # Try to list directory contents
        os.listdir(photos_path)
        # Try to access a subdirectory
        for item in os.listdir(photos_path):
            item_path = os.path.join(photos_path, item)
            if os.path.isdir(item_path):
                try:
                    os.listdir(item_path)
                    break
                except (OSError, PermissionError):
                    pass
        return {'has_access': True, 'reason': 'success'}
    except (OSError, PermissionError):
        return {'has_access': False, 'reason': 'permission_denied'}


def check_full_disk_access():
    """
    Check if Full Disk Access is granted by testing protected directories.
    
    Returns:
        dict with:
            - has_access: bool - True if all permissions granted
            - missing_permissions: list - List of missing permission types
            - details: dict - Detailed results for each check
    """
    results = {
        'has_access': True,
        'missing_permissions': [],
        'details': {}
    }
    
    # Check Messages
    messages_result = check_messages_access()
    results['details']['messages'] = messages_result
    if not messages_result['has_access']:
        results['has_access'] = False
        results['missing_permissions'].append('messages')
    
    # Check Mail
    mail_result = check_mail_access()
    results['details']['mail'] = mail_result
    if not mail_result['has_access']:
        results['has_access'] = False
        results['missing_permissions'].append('mail')
    
    # Check Photos
    photos_result = check_photos_access()
    results['details']['photos'] = photos_result
    if not photos_result['has_access']:
        results['has_access'] = False
        results['missing_permissions'].append('photos')
    
    return results


def get_permission_instructions():
    """Get instructions for granting Full Disk Access."""
    return """
To grant Full Disk Access:

1. Open System Settings
   - Click Apple menu → System Settings
   - Or press Cmd+Space and search "System Settings"

2. Go to Privacy & Security
   - Click "Privacy & Security" in the sidebar
   - Scroll down to "Full Disk Access"

3. Add Terminal (or your IDE)
   - Click the lock icon (enter password if needed)
   - Click the + button
   - Navigate to Applications → Utilities
   - Select "Terminal.app"
   - Make sure the checkbox is checked ✅

4. Restart Terminal
   - Close and reopen Terminal for changes to take effect

Note: If you're running from Cursor, VS Code, or another IDE, 
add that application instead of Terminal.
"""


def format_permission_status(permission_results):
    """
    Format permission check results into a user-friendly message.
    
    Args:
        permission_results: Result from check_full_disk_access()
    
    Returns:
        str: Formatted message about permission status
    """
    if permission_results['has_access']:
        return "✅ Full Disk Access granted - all libraries accessible"
    
    missing = permission_results['missing_permissions']
    if len(missing) == 1:
        lib_name = missing[0].title()
        return f"⚠️  Full Disk Access required for {lib_name} library"
    else:
        libs = ", ".join(m.title() for m in missing)
        return f"⚠️  Full Disk Access required for: {libs}"


def try_du_fallback(path):
    """
    Try to get directory size using 'du' command as fallback.
    
    Args:
        path: Path to directory
    
    Returns:
        int: Size in bytes, or 0 if failed
    """
    # Defensive check: path must be valid
    if not path or not isinstance(path, str):
        # Diagnostic: Log invalid path (but don't spam - only in debug mode)
        return 0
    
    try:
        cmd = ['du', '-sk', path]
        log_subprocess_call("try_du_fallback()", cmd, path=path)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # du returns size in KB, convert to bytes
            size_kb = int(result.stdout.split()[0])
            return size_kb * 1024
    except (subprocess.TimeoutExpired, ValueError, IndexError, FileNotFoundError, TypeError) as e:
        # Diagnostic: Log subprocess errors (can be enabled for debugging)
        # print(f"DEBUG: try_du_fallback failed for path={path}: {type(e).__name__}")
        pass
    return 0

