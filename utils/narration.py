"""Dad narrating what he's doing, one short line at a time.

The opening lines of a run come from three places (the CLI, the volume
picker, the scanner). Printing them through one helper keeps their look the
same and lets a short pause between lines say "I'm working on it".
"""
import sys
import time

# Seconds between narrated lines. Short enough to add about a second to a run.
PAUSE_SECONDS = 0.2


def say(text, arrow=True, pause=PAUSE_SECONDS):
    """Print one narrated line, then pause briefly if a person is watching.

    The pause happens only when stdout is a terminal, so scheduled runs,
    pipes and the test suite never slow down where nobody can see it.
    `arrow=False` prints an indented follow-on line without the marker.
    """
    print(f"→ {text}" if arrow else f"     {text}", flush=True)
    stdout = sys.stdout
    if pause and getattr(stdout, 'isatty', lambda: False)():
        time.sleep(pause)
