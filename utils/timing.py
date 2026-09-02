"""Per-phase timers for one scan run.

A run is more than the volume walk: it also walks the home directory, reads
the Mac app libraries, sizes the hidden caches, lists snapshots, grades the
result and renders the HTML. Only the volume walk used to be timed, so the
number in the report read as the answer to "how long did that take?" and was
wrong by a factor of three on a real Mac.

Two things live here:

  - `RunTimer.elapsed` - wall clock for the whole run, started in `main()`.
    This is what the report shows.
  - `RunTimer.phase()` - a context manager that records how long each phase
    took. Phases are silent unless timings are switched on (`--timings` or
    `DIAGNOSTIC_LOGGING=1`), so a normal run stays quiet.

The timer is a module-level singleton (`get_timer()`) rather than an argument
threaded through every scanner, because a phase can start deep in a scanner
and the call path to it carries nothing else.
"""

import sys
import time
from contextlib import contextmanager

from utils.subprocess_utils import DIAGNOSTIC_LOGGING


def format_duration(seconds):
    """Human-readable duration: '4.2s', '1m 03s', '3m 10s'."""
    seconds = max(0.0, float(seconds))
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, rest = divmod(int(round(seconds)), 60)
    return f"{minutes}m {rest:02d}s"


class RunTimer:
    """Wall clock for a run, plus a record of each phase within it."""

    def __init__(self, enabled=False):
        self.enabled = enabled
        self._start = time.monotonic()
        # Ordered: phase name -> [total_seconds, call_count]. A phase that
        # runs twice (the `all` command renders two reports) accumulates
        # rather than appearing twice.
        self.phases = {}

    def start(self, enabled=None):
        """Reset the clock and drop any recorded phases."""
        self._start = time.monotonic()
        self.phases = {}
        if enabled is not None:
            self.enabled = enabled

    @property
    def elapsed(self):
        """Seconds since `start()` (or since the timer was created)."""
        return time.monotonic() - self._start

    def record(self, name, seconds):
        """Add `seconds` to phase `name`."""
        entry = self.phases.setdefault(name, [0.0, 0])
        entry[0] += seconds
        entry[1] += 1
        if self.enabled:
            print(f"[timing] {name}: {format_duration(seconds)}", file=sys.stderr)
            sys.stderr.flush()

    @contextmanager
    def phase(self, name):
        """Time a block of work as phase `name`.

        Records on the way out even if the block raises, so a scan that fails
        or is interrupted still says where the time went.
        """
        started = time.monotonic()
        try:
            yield
        finally:
            self.record(name, time.monotonic() - started)

    def summary_lines(self):
        """Lines for the end-of-run breakdown, longest phase first."""
        if not self.phases:
            return []
        total = self.elapsed
        width = max(len(name) for name in self.phases)
        lines = ["[timing] phase breakdown:"]
        for name, (seconds, count) in sorted(self.phases.items(),
                                             key=lambda kv: -kv[1][0]):
            share = (seconds / total * 100) if total > 0 else 0.0
            suffix = f" (x{count})" if count > 1 else ""
            lines.append(f"[timing]   {name:<{width}}  "
                         f"{format_duration(seconds):>8}  {share:5.1f}%{suffix}")
        # Phases don't tile the run - permission prompts, browser launch and
        # the gaps between phases are real time too - so print the total
        # rather than let the reader add the rows up and wonder.
        lines.append(f"[timing]   {'total (wall clock)':<{width}}  "
                     f"{format_duration(total):>8}")
        return lines

    def print_summary(self, stream=None):
        """Print the breakdown to stderr. No-op unless timings are on."""
        if not self.enabled:
            return
        stream = stream or sys.stderr
        for line in self.summary_lines():
            print(line, file=stream)
        stream.flush()


_TIMER = RunTimer(enabled=DIAGNOSTIC_LOGGING)


def get_timer():
    """The run's timer."""
    return _TIMER
