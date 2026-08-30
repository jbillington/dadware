"""Shared subprocess logging and diagnostic utilities."""

import os
import sys

# Central diagnostic logging flag.
# Avoids circular imports — modules import this instead of from askdad.
DIAGNOSTIC_LOGGING = os.environ.get('DIAGNOSTIC_LOGGING', '').lower() in ('1', 'true', 'yes')


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
