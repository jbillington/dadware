"""Copy for asking testers for feedback. The only place the address lives.

Spec: docs/roadmap/FEEDBACK-AND-CPU-PROMO-PLAN.md. Every renderer imports from
here, so the report and the terminal cannot drift apart.
"""
from urllib.parse import quote

from utils.version import VERSION

FEEDBACK_EMAIL = 'john@dadware.net'

FEEDBACK_HEADLINE = "Ask Dad is in beta, and I'd love to hear from you."
FEEDBACK_BODY = "Was this report useful? Confusing? Wrong? Send me an email."


def feedback_mailto():
    """mailto: link with the version in the subject and nothing else.

    Never put scan data, paths or the report in here: the trust story is that
    nothing leaves the Mac unless the user chooses to send it, and a prefilled
    body is easy to send without reading.
    """
    subject = quote(f'Ask Dad feedback (v{VERSION})')
    return f'mailto:{FEEDBACK_EMAIL}?subject={subject}'
