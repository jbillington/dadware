"""Feedback ask and the storage/CPU cross-promo. The only place the address lives.

Spec: docs/roadmap/FEEDBACK-AND-CPU-PROMO-PLAN.md. Every renderer imports from
here, so the report and the terminal cannot drift apart. The report shows the
feedback banner; the terminal gets the closing lines and the CPU offer.
"""
import os
from urllib.parse import quote

from utils.version import VERSION

FEEDBACK_EMAIL = 'john@dadware.net'

FEEDBACK_HEADLINE = "Ask Dad is in beta, and I'd love to hear from you."
FEEDBACK_BODY = "Was this report useful? Confusing? Wrong? Send me an email."

# Terminal wording.
FEEDBACK_INVITE = ("Send me an email.  I would love to hear if Ask Dad was useful "
                   "or could be better.")
CPU_PROMPT = "Want me to check your memory and CPU too? [y/N] "

# Set by the signed .app's launcher (make_app.sh, AskDad.command). That window
# has the bundled binary on its PATH, but a fresh Terminal window does not, so
# the wording points at "this Terminal window".
CHANNEL_ENV = 'ASKDAD_CHANNEL'


def feedback_mailto():
    """mailto: link with the version in the subject and nothing else.

    Never put scan data, paths or the report in here: the trust story is that
    nothing leaves the Mac unless the user chooses to send it, and a prefilled
    body is easy to send without reading.
    """
    subject = quote(f'Ask Dad feedback (v{VERSION})')
    return f'mailto:{FEEDBACK_EMAIL}?subject={subject}'


def is_app_channel():
    """True when the run was started by the signed .app's launcher."""
    return os.environ.get(CHANNEL_ENV) == 'app'


def feedback_line():
    """Plain-text feedback invitation, address on its own line."""
    return f"{FEEDBACK_INVITE}\n{FEEDBACK_EMAIL}"


def promo_command(scan_type):
    """The command that runs the *other* scan, or None.

    After a storage scan that is `askdad cpu`; after a CPU scan, `askdad`.
    """
    if scan_type == 'storage':
        return 'askdad cpu'
    if scan_type == 'cpu':
        return 'askdad'
    return None


def cpu_promo_line(scan_type):
    """Plain-text pointer to the other scan, or None for anything else."""
    command = promo_command(scan_type)
    if command is None:
        return None
    where = "Type in this Terminal window:" if is_app_channel() else "Run:"
    if scan_type == 'storage':
        return f"Next - Ask Dad to scan your memory and CPU.  {where}  {command}"
    return f"Curious about your storage?  {where}  {command}"
