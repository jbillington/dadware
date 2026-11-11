"""
The feedback invitation and the storage/CPU cross-promo, in one place.

Both the terminal and the HTML report take their wording from here, so the two
cannot drift. Plan: docs/roadmap/FEEDBACK-AND-CPU-PROMO-PLAN.md.

Nothing here sends anything anywhere. The mailto link carries the version in
its subject and nothing else: no scan data, no paths, no report. The tool's
trust story is that nothing leaves the Mac unless the user chooses to send it.
"""

import os
from urllib.parse import quote

from utils.version import VERSION

# The only place the address lives.
FEEDBACK_EMAIL = "john@dadware.net"

# Set by the signed .app's launcher (make_app.sh, AskDad.command). That window
# has the bundled binary on its PATH, but a fresh Terminal window does not, so
# the wording points at "this Terminal window".
CHANNEL_ENV = "ASKDAD_CHANNEL"

FEEDBACK_INVITE = ("Send me an email.  I would love to hear if Ask Dad was useful "
                   "or could be better.")

CPU_PROMPT = "Want me to check your memory and CPU too? [y/N] "


def is_app_channel():
    """True when the run was started by the signed .app's launcher."""
    return os.environ.get(CHANNEL_ENV) == "app"


def feedback_line():
    """Plain-text feedback invitation, address on its own line."""
    return f"{FEEDBACK_INVITE}\n{FEEDBACK_EMAIL}"


def feedback_mailto():
    """mailto: href for the report footer. Subject carries the version only."""
    subject = quote(f"Ask Dad feedback (v{VERSION})")
    return f"mailto:{FEEDBACK_EMAIL}?subject={subject}"


def promo_command(scan_type):
    """The command that runs the *other* scan, or None.

    A storage report points at `askdad cpu`, a CPU report at `askdad`.
    """
    if scan_type == "storage":
        return "askdad cpu"
    if scan_type == "cpu":
        return "askdad"
    return None


def cpu_promo_line(scan_type):
    """Plain-text pointer to the other scan, or None for anything else."""
    command = promo_command(scan_type)
    if command is None:
        return None
    where = ("Type in this Terminal window:" if is_app_channel() else "Run:")
    if scan_type == "storage":
        return f"Next - Ask Dad to scan your memory and CPU.  {where}  {command}"
    return f"Curious about your storage?  {where}  {command}"
