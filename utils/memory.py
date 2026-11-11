"""The one definition of the RAM figures every CPU report prints.

The HTML report, the terminal and the AI prompt all read memory numbers
from memory_summary(), so "free" and "available" mean the same thing,
and print the same text, in all three.

RAM stays binary (1024-based); see the comment in scanners/cpu.py.
"""

GIB = 1024 ** 3


def _gb_text(num_bytes):
    return f"{num_bytes / GIB:.1f} GB" if num_bytes is not None else "unknown"


def memory_summary(scan_data):
    """
    RAM figures for a CPU scan, in one dict.

    - free: pages nobody is using at all (vm_stat "Pages free"). Usually
      small on a healthy Mac, because macOS puts spare RAM to work.
    - available: free + inactive + purgeable, an approximation of what
      macOS could hand out quickly.
    - used: active + wired + compressed, as Activity Monitor counts it.
    - apps: the sum of every process's resident memory. Shared memory is
      counted once per process, so it overstates; use it only to rank apps.
    - pressure: the kernel's own reading, or 'unknown'.

    Byte values are None when vm_stat could not be read. Every *_text key
    is ready to print, so all reports show identical strings.
    """
    mp = scan_data.get('memory_pressure') or {}
    total_bytes = scan_data.get('total_memory_bytes') or int(
        (scan_data.get('total_memory_gb') or 0) * GIB)

    free_bytes = mp.get('free_bytes') if mp else None
    available_bytes = mp.get('available_bytes') if mp else None
    used_bytes = mp.get('used_bytes') if mp else None
    if mp and used_bytes is None:
        # Manifests saved before used_bytes existed carry its parts.
        used_bytes = (mp.get('active_bytes', 0) + mp.get('wired_bytes', 0)
                      + mp.get('compressed_bytes', 0))
    swap_used_bytes = mp.get('swap_used_bytes') if mp else None
    apps_bytes = int((scan_data.get('total_used_mb') or 0) * 1024 ** 2)

    used_percent = None
    if used_bytes is not None and total_bytes:
        used_percent = min(100.0, used_bytes / total_bytes * 100)

    return {
        'total_bytes': total_bytes,
        'free_bytes': free_bytes,
        'available_bytes': available_bytes,
        'used_bytes': used_bytes,
        'used_percent': used_percent,
        'apps_bytes': apps_bytes,
        'swap_used_bytes': swap_used_bytes,
        'pressure': mp.get('pressure', 'unknown') if mp else 'unknown',
        'pressure_source': mp.get('pressure_source') if mp else None,
        'total_text': _gb_text(total_bytes),
        'free_text': _gb_text(free_bytes),
        'available_text': _gb_text(available_bytes),
        'used_text': _gb_text(used_bytes),
        'used_percent_text': f"{used_percent:.0f}%" if used_percent is not None else "",
        'apps_text': _gb_text(apps_bytes),
        'swap_used_text': _gb_text(swap_used_bytes),
    }


AVAILABLE_NOTE = "approx.: free + inactive + purgeable"
APPS_NOTE = "shared memory is counted more than once"
