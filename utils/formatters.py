"""Shared formatting and display utilities."""


# Disk sizes are formatted in DECIMAL units (1 GB = 1,000,000,000 bytes),
# because that is what macOS shows. Finder, Get Info and Storage Settings have
# used decimal since Snow Leopard, and Apple's own ByteCountFormatter defaults
# to the decimal `.file` style on macOS.
#
# This is not a detail. Formatting 1024-based math with a "GB" label - which
# this function used to do - makes every size in the report read ~7% smaller
# than the same bytes in Finder, and the user's reasonable conclusion is that
# our tool is broken. GrandPerspective documents exactly this trap in its own
# help ("the size reported by GrandPerspective will be smaller").
#
# RAM is deliberately NOT formatted through here; see the note in scanners/cpu.py.
DECIMAL_UNIT = 1000.0


def format_size(size_bytes):
    """Format bytes into a human-readable size, in macOS's decimal units."""
    size = max(0, size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < DECIMAL_UNIT:
            return f"{size:.1f} {unit}"
        size /= DECIMAL_UNIT
    return f"{size:.1f} PB"


def get_status_emoji(status):
    """Get emoji for status."""
    if status == 'critical':
        return '🔴'
    elif status == 'warn':
        return '🟡'
    else:
        return '🟢'


def get_status_text(status):
    """Get status text."""
    if status == 'critical':
        return 'needs attention'
    elif status == 'warn':
        return 'stable but cluttered'
    else:
        return 'all good'
