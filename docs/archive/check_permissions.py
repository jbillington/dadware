#!/usr/bin/env python3
"""
Standalone script to check macOS Full Disk Access permissions.
Run this before scanning to verify permissions are set up correctly.
"""

import sys
import os

# Add parent directory to path so we can import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.permissions import (
    check_full_disk_access,
    check_messages_access,
    check_mail_access,
    check_photos_access,
    format_permission_status,
    get_permission_instructions
)


def main():
    """Check and display permission status."""
    print("=" * 60)
    print("  macOS Full Disk Access Permission Checker")
    print("=" * 60)
    print()
    
    # Check individual permissions
    print("Checking individual permissions...")
    print()
    
    messages_result = check_messages_access()
    mail_result = check_mail_access()
    photos_result = check_photos_access()
    
    # Display results
    status_icon = "✅" if messages_result['has_access'] else "❌"
    reason = messages_result.get('reason', 'unknown')
    if reason == 'path_not_found':
        print(f"{status_icon} Messages: Not found (may not be installed)")
    elif reason == 'permission_denied':
        print(f"{status_icon} Messages: Permission denied (Full Disk Access required)")
    else:
        print(f"{status_icon} Messages: Access granted")
    
    status_icon = "✅" if mail_result['has_access'] else "❌"
    reason = mail_result.get('reason', 'unknown')
    if reason == 'path_not_found':
        print(f"{status_icon} Mail: Not found (may not be installed)")
    elif reason == 'permission_denied':
        print(f"{status_icon} Mail: Permission denied (Full Disk Access required)")
    else:
        print(f"{status_icon} Mail: Access granted")
    
    status_icon = "✅" if photos_result['has_access'] else "❌"
    reason = photos_result.get('reason', 'unknown')
    if reason == 'path_not_found':
        print(f"{status_icon} Photos: Not found (may not be installed)")
    elif reason == 'permission_denied':
        print(f"{status_icon} Photos: Permission denied (Full Disk Access required)")
    else:
        print(f"{status_icon} Photos: Access granted")
    
    print()
    print("-" * 60)
    print()
    
    # Overall status
    overall_result = check_full_disk_access()
    print(format_permission_status(overall_result))
    print()
    
    if not overall_result['has_access']:
        print("=" * 60)
        print("  Setup Instructions")
        print("=" * 60)
        print(get_permission_instructions())
        print()
        print("After granting permissions, restart Terminal/IDE and run this")
        print("script again to verify the changes took effect.")
        print()
        return 1
    else:
        print("✅ All permissions granted! You're ready to scan.")
        print()
        return 0


if __name__ == '__main__':
    sys.exit(main())

