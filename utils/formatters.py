"""Shared formatting and display utilities."""


def format_size(size_bytes):
    """Format bytes into human-readable size."""
    size = max(0, size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
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
