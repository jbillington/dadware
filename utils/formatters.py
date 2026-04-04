"""Shared formatting and display utilities."""


def format_size(bytes):
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"


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
